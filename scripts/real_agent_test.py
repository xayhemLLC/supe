#!/usr/bin/env python3
"""Real Claude API Integration Test with TascerAgent.

This script demonstrates TascerAgent validation with the real Anthropic API:
1. Define tools for Claude to use
2. Intercept tool calls through TascerAgent validation
3. Store execution records to AB Memory
4. Query recall after execution

Requires: ANTHROPIC_API_KEY environment variable

Run: python scripts/real_agent_test.py
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic

from ab import ABMemory
from tascer.sdk_wrapper import (
    TascerAgent,
    TascerAgentOptions,
    ToolValidationConfig,
    RecallConfig,
)
from tascer.contracts import GateResult


# =============================================================================
# Tool Definitions for Claude
# =============================================================================

TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_directory",
        "description": "List files in a directory",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the directory"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "calculate",
        "description": "Perform a mathematical calculation",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2')"
                }
            },
            "required": ["expression"]
        }
    },
]


# =============================================================================
# Tool Implementations (with validation)
# =============================================================================

def execute_read_file(path: str) -> str:
    """Read a file's contents."""
    try:
        # Only allow reading from current directory for safety
        if ".." in path or path.startswith("/"):
            return f"Error: Access denied - only relative paths allowed"

        with open(path, "r") as f:
            content = f.read()
            # Truncate long files
            if len(content) > 2000:
                return content[:2000] + "\n... (truncated)"
            return content
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error reading file: {e}"


def execute_list_directory(path: str) -> str:
    """List directory contents."""
    try:
        if ".." in path:
            return "Error: Access denied"

        entries = os.listdir(path or ".")
        return "\n".join(sorted(entries)[:50])  # Limit to 50 entries
    except Exception as e:
        return f"Error: {e}"


def safe_math_eval(expression: str) -> str:
    """Safely evaluate a simple math expression using regex parsing."""
    # Remove whitespace
    expr = expression.replace(" ", "")

    # Only allow numbers, basic operators, parentheses, decimal points
    if not re.match(r'^[\d\+\-\*\/\(\)\.]+$', expr):
        return "Error: Invalid characters in expression"

    try:
        # Use Python's compile with restricted mode
        code = compile(expr, "<string>", "eval")

        # Check that only safe operations are used
        allowed_names = set()
        for name in code.co_names:
            if name not in allowed_names:
                return f"Error: Invalid operation: {name}"

        # Evaluate with empty namespace (no builtins)
        result = eval(code, {"__builtins__": {}}, {})  # noqa: S307
        return str(result)
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error: {e}"


TOOL_EXECUTORS = {
    "read_file": lambda args: execute_read_file(args["path"]),
    "list_directory": lambda args: execute_list_directory(args["path"]),
    "calculate": lambda args: safe_math_eval(args["expression"]),
}


# =============================================================================
# Custom Gate
# =============================================================================

def gate_safe_path(record, phase) -> GateResult:
    """Ensure file operations use safe paths."""
    if phase != "pre":
        return GateResult("safe_path", True, "Post-check skipped")

    tool_input = record.tool_input
    path = tool_input.get("path", "")

    # Block parent directory traversal
    if ".." in path:
        return GateResult("safe_path", False, f"Blocked: path traversal not allowed")

    # Block absolute paths
    if path.startswith("/"):
        return GateResult("safe_path", False, f"Blocked: absolute paths not allowed")

    return GateResult("safe_path", True, f"Path allowed: {path}")


# =============================================================================
# Main Agent Loop
# =============================================================================

async def run_agent_with_tascer(prompt: str, agent: TascerAgent, max_turns: int = 5):
    """Run Claude with TascerAgent validation on tool calls."""

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": prompt}]

    print(f"\n{'='*60}")
    print(f"User: {prompt}")
    print(f"{'='*60}\n")

    for turn in range(max_turns):
        # Call Claude
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        # Check stop reason
        if response.stop_reason == "end_turn":
            # Extract final text
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"Claude: {block.text}")
            break

        # Process tool uses
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                tool_id = block.id

                print(f"[Tool Call] {tool_name}: {json.dumps(tool_input)}")

                # Run through TascerAgent validation
                import uuid
                tool_use_id = f"tu_{uuid.uuid4().hex[:8]}"

                # Pre-hook validation
                input_data = {"tool_name": tool_name, "tool_input": tool_input}
                pre_result = await agent._pre_tool_hook(input_data, tool_use_id, None)

                if pre_result.get("block"):
                    # Tool blocked by gate
                    result = f"BLOCKED: {pre_result.get('message')}"
                    print(f"[Validation] {result}")
                else:
                    # Execute the tool
                    if tool_name in TOOL_EXECUTORS:
                        result = TOOL_EXECUTORS[tool_name](tool_input)
                    else:
                        result = f"Unknown tool: {tool_name}"

                    # Post-hook (capture result, generate proof)
                    result_data = {"tool_result": result}
                    await agent._post_tool_hook(result_data, tool_use_id, None)

                    print(f"[Result] {result[:100]}{'...' if len(result) > 100 else ''}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result,
                })
            elif hasattr(block, "text") and block.text:
                print(f"Claude: {block.text}")

        # Add assistant message and tool results
        messages.append({"role": "assistant", "content": response.content})
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    return agent


async def main():
    print("=" * 60)
    print("  Real Claude API + TascerAgent Integration Test")
    print("=" * 60)

    # Setup
    db_path = ".tascer/real_agent_test.sqlite"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    ab = ABMemory(db_path)

    # Create TascerAgent
    agent = TascerAgent(
        tascer_options=TascerAgentOptions(
            tool_configs={
                "read_file": ToolValidationConfig(
                    tool_name="read_file",
                    pre_gates=["safe_path"],
                ),
                "list_directory": ToolValidationConfig(
                    tool_name="list_directory",
                    pre_gates=["safe_path"],
                ),
                "calculate": ToolValidationConfig(
                    tool_name="calculate",
                ),
            },
            capture_git_state=False,
            capture_env=False,
            store_to_ab=True,
            recall_config=RecallConfig(enabled=True, index_on_store=True),
        ),
        ab_memory=ab,
    )
    agent._session_id = f"real_test_{datetime.now().strftime('%H%M%S')}"

    # Register custom gate
    agent.register_gate("safe_path", gate_safe_path)

    print(f"\n[Setup] Session: {agent._session_id}")
    print(f"[Setup] Database: {db_path}")

    # ==========================================================================
    # Test 1: Simple calculation
    # ==========================================================================
    print("\n" + "=" * 60)
    print("TEST 1: Mathematical Calculation")
    print("=" * 60)

    agent = await run_agent_with_tascer(
        "What is 42 * 17 + 123? Use the calculate tool.",
        agent
    )

    # ==========================================================================
    # Test 2: File listing
    # ==========================================================================
    print("\n" + "=" * 60)
    print("TEST 2: Directory Listing")
    print("=" * 60)

    agent = await run_agent_with_tascer(
        "List the Python files in the current directory. Use list_directory with path '.'",
        agent
    )

    # ==========================================================================
    # Test 3: Read a file
    # ==========================================================================
    print("\n" + "=" * 60)
    print("TEST 3: Read File")
    print("=" * 60)

    agent = await run_agent_with_tascer(
        "Read the README.md file and tell me what this project is about.",
        agent
    )

    # ==========================================================================
    # Results
    # ==========================================================================
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)

    records = agent.get_validation_report()
    print(f"\nTotal tool calls: {len(records)}")

    validated = sum(1 for r in records if r.status == "validated")
    blocked = sum(1 for r in records if r.status == "blocked")
    print(f"Validated: {validated} | Blocked: {blocked}")

    print("\nExecution log:")
    for r in records:
        status = "✓" if r.status == "validated" else "✗"
        print(f"  {status} {r.tool_name:15} | {r.proof_hash[:12]}... | {r.status}")

    # Proof verification
    print(f"\nAll proofs valid: {agent.verify_proofs()}")

    # ==========================================================================
    # Recall Demo
    # ==========================================================================
    print("\n" + "=" * 60)
    print("RECALL DEMO")
    print("=" * 60)

    print("\nRecalling 'calculate' operations:")
    results = agent.recall("calculate", top_k=3)
    for r in results:
        print(f"  [{r.score:.2f}] {r.tool_name}: {r.tool_input}")

    print("\nRecalling 'file' operations:")
    results = agent.recall("file read", top_k=3)
    for r in results:
        print(f"  [{r.score:.2f}] {r.tool_name}: {r.tool_input}")

    print("\nAll tool calls this session:")
    for r in agent.recall_tool("read_file"):
        print(f"  - read_file: {r.tool_input.get('path', 'N/A')}")
    for r in agent.recall_tool("list_directory"):
        print(f"  - list_directory: {r.tool_input.get('path', 'N/A')}")
    for r in agent.recall_tool("calculate"):
        print(f"  - calculate: {r.tool_input.get('expression', 'N/A')}")

    # Export
    report_path = ".tascer/real_agent_report.json"
    agent.export_report(report_path)
    print(f"\nExported report to: {report_path}")

    print("\n" + "=" * 60)
    print("  Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
