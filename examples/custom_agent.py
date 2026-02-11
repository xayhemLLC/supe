#!/usr/bin/env python3
"""Example: Building a Custom Agent with Supe Validation.

This demonstrates how to wrap any LLM/agent with supe's:
- Validation gates (pre/post execution checks)
- Proof-of-work generation (audit trails)
- Memory recall (context from past executions)
- Auto-context injection (relevant history in prompts)

Usage:
    export ANTHROPIC_API_KEYY="your-key"
    python examples/custom_agent.py
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

from ab import ABMemory
from tascer.sdk_wrapper import (
    TascerAgent,
    TascerAgentOptions,
    ToolValidationConfig,
    RecallConfig,
)
from tascer.contracts import GateResult


# =============================================================================
# 1. CUSTOM VALIDATION GATES
# =============================================================================

def gate_no_secrets_in_output(record, phase) -> GateResult:
    """Block if output contains potential secrets."""
    if phase != "post":
        return GateResult("no_secrets", True, "Pre-check skipped")

    output = str(record.tool_output or "").lower()

    # Check for common secret patterns
    secret_patterns = [
        "api_key=",
        "password=",
        "secret=",
        "token=",
        "aws_access_key",
        "private_key",
    ]

    for pattern in secret_patterns:
        if pattern in output:
            return GateResult(
                "no_secrets",
                False,
                f"BLOCKED: Output may contain secrets ({pattern})"
            )

    return GateResult("no_secrets", True, "No secrets detected")


def gate_safe_file_paths(record, phase) -> GateResult:
    """Block dangerous file operations."""
    if phase != "pre":
        return GateResult("safe_paths", True, "Post-check skipped")

    tool_input = record.tool_input or {}

    # Check file paths
    dangerous_paths = ["/etc/", "/usr/", "/bin/", "/root/", "~/.ssh/"]

    for key in ["file_path", "path", "target"]:
        path = tool_input.get(key, "")
        for dangerous in dangerous_paths:
            if dangerous in path:
                return GateResult(
                    "safe_paths",
                    False,
                    f"BLOCKED: Dangerous path ({path})"
                )

    return GateResult("safe_paths", True, "Path is safe")


def gate_command_allowlist(record, phase) -> GateResult:
    """Only allow specific commands."""
    if phase != "pre":
        return GateResult("command_allowlist", True, "Post-check skipped")

    command = record.tool_input.get("command", "")

    # Allowed command prefixes
    allowed = [
        "ls", "cat", "grep", "find", "echo",
        "python", "pytest", "pip",
        "git status", "git diff", "git log",
        "npm", "yarn", "node",
    ]

    # Check if command starts with allowed prefix
    cmd_lower = command.lower().strip()
    for prefix in allowed:
        if cmd_lower.startswith(prefix):
            return GateResult("command_allowlist", True, f"Allowed: {prefix}")

    # Block dangerous commands
    dangerous = ["rm -rf", "sudo", "chmod 777", "curl | bash", "wget | sh"]
    for danger in dangerous:
        if danger in cmd_lower:
            return GateResult(
                "command_allowlist",
                False,
                f"BLOCKED: Dangerous command ({danger})"
            )

    # Allow by default but warn
    return GateResult(
        "command_allowlist",
        True,
        f"Warning: Unlisted command ({command[:30]})"
    )


# =============================================================================
# 2. AGENT CONFIGURATION
# =============================================================================

def create_validated_agent(
    project: str = "default",
    db_path: Optional[str] = None,
    auto_context: bool = True,
) -> TascerAgent:
    """Create a TascerAgent with custom validation gates.

    Args:
        project: Project name for memory isolation
        db_path: Path to memory database
        auto_context: Enable automatic context injection

    Returns:
        Configured TascerAgent instance
    """
    # Use global supe database
    db_path = db_path or os.path.expanduser("~/.supe/memory.sqlite")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Initialize memory
    ab = ABMemory(db_path)

    # Configure agent
    agent = TascerAgent(
        tascer_options=TascerAgentOptions(
            # Tool-specific validation
            tool_configs={
                "Bash": ToolValidationConfig(
                    tool_name="Bash",
                    pre_gates=["command_allowlist", "safe_paths"],
                    post_gates=["no_secrets", "exit_code_zero"],
                ),
                "Read": ToolValidationConfig(
                    tool_name="Read",
                    pre_gates=["safe_paths"],
                    post_gates=["no_secrets"],
                ),
                "Write": ToolValidationConfig(
                    tool_name="Write",
                    pre_gates=["safe_paths"],
                    post_gates=[],
                ),
                "Edit": ToolValidationConfig(
                    tool_name="Edit",
                    pre_gates=["safe_paths"],
                    post_gates=[],
                ),
            },
            # Default gates for unlisted tools
            default_pre_gates=["safe_paths"],
            default_post_gates=["no_secrets"],
            # Memory settings
            recall_config=RecallConfig(
                enabled=True,
                auto_context=auto_context,
                auto_context_limit=3,
                default_top_k=5,
            ),
            # Proof generation
            generate_proofs=True,
            store_to_ab=True,
        ),
        ab_memory=ab,
    )

    # Register custom gates
    agent.register_gate("no_secrets", gate_no_secrets_in_output)
    agent.register_gate("safe_paths", gate_safe_file_paths)
    agent.register_gate("command_allowlist", gate_command_allowlist)

    return agent


# =============================================================================
# 3. SIMULATED TOOL EXECUTION (for demo)
# =============================================================================

async def simulate_tool_execution(
    agent: TascerAgent,
    tool_name: str,
    tool_input: Dict[str, Any],
) -> Dict[str, Any]:
    """Simulate a tool execution through the agent's validation.

    In a real integration, this would call the actual tool.
    Here we simulate to demonstrate the validation flow.
    """
    import uuid

    tool_use_id = f"tu_{uuid.uuid4().hex[:8]}"

    # Pre-hook: validation gates run here
    pre_result = await agent._pre_tool_hook(
        {"tool_name": tool_name, "tool_input": tool_input},
        tool_use_id,
        None,
    )

    if pre_result.get("block"):
        return {
            "status": "blocked",
            "reason": pre_result.get("message"),
            "tool_use_id": tool_use_id,
        }

    # Check if context was injected
    context = pre_result.get("context")

    # Simulate tool execution
    if tool_name == "Bash":
        # Simulate command output
        tool_output = {
            "exit_code": 0,
            "stdout": f"Executed: {tool_input.get('command', '')}",
            "stderr": "",
        }
    elif tool_name == "Read":
        tool_output = f"Contents of {tool_input.get('file_path', 'unknown')}"
    else:
        tool_output = {"result": "success"}

    # Post-hook: more validation, proof generation
    await agent._post_tool_hook(
        {"tool_result": tool_output},
        tool_use_id,
        None,
    )

    # Get the execution record
    record = agent._find_record(tool_use_id)

    return {
        "status": record.status if record else "unknown",
        "tool_use_id": tool_use_id,
        "proof_hash": record.proof_hash if record else None,
        "context_injected": context is not None,
        "output": tool_output,
    }


# =============================================================================
# 4. EXAMPLE USAGE
# =============================================================================

async def demo():
    """Demonstrate the validated agent."""

    print("=" * 60)
    print("SUPE VALIDATED AGENT DEMO")
    print("=" * 60)

    # Create agent
    agent = create_validated_agent(
        project="demo",
        auto_context=True,
    )

    # Test cases
    test_cases = [
        # Safe command - should pass
        ("Bash", {"command": "ls -la"}),

        # Safe file read - should pass
        ("Read", {"file_path": "/tmp/test.txt"}),

        # Dangerous path - should block
        ("Read", {"file_path": "/etc/passwd"}),

        # Dangerous command - should block
        ("Bash", {"command": "rm -rf /"}),

        # Git command - should pass
        ("Bash", {"command": "git status"}),

        # Python test - should pass
        ("Bash", {"command": "pytest tests/ -v"}),
    ]

    for tool_name, tool_input in test_cases:
        print(f"\n{'─' * 40}")
        print(f"Tool: {tool_name}")
        print(f"Input: {json.dumps(tool_input)}")

        result = await simulate_tool_execution(agent, tool_name, tool_input)

        status_icon = "✅" if result["status"] == "validated" else "🚫"
        print(f"Status: {status_icon} {result['status']}")

        if result.get("proof_hash"):
            print(f"Proof: {result['proof_hash']}")

        if result.get("context_injected"):
            print("Context: Injected from past executions")

        if result["status"] == "blocked":
            print(f"Reason: {result.get('reason', 'Unknown')}")

    # Show execution report
    print(f"\n{'=' * 60}")
    print("EXECUTION REPORT")
    print("=" * 60)

    report = agent.get_validation_report()

    validated = sum(1 for r in report if r.status == "validated")
    blocked = sum(1 for r in report if r.status == "blocked")

    print(f"Total executions: {len(report)}")
    print(f"Validated: {validated}")
    print(f"Blocked: {blocked}")
    print(f"Proofs valid: {agent.verify_proofs()}")

    # Export report
    report_path = ".supe/demo_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    agent.export_report(report_path)
    print(f"\nReport saved: {report_path}")

    # Show memory recall
    print(f"\n{'=' * 60}")
    print("MEMORY RECALL")
    print("=" * 60)

    results = agent.recall("git", top_k=3)
    if results:
        for r in results:
            print(f"  [{r.tool_name}] {json.dumps(r.tool_input)[:50]}...")
    else:
        print("  No relevant memories found")


# =============================================================================
# 5. REAL CLAUDE INTEGRATION EXAMPLE
# =============================================================================

async def claude_integration_example():
    """Example of integrating with Claude API.

    This shows how you would wrap actual Claude API calls
    with supe validation.
    """
    try:
        import anthropic
    except ImportError:
        print("Install anthropic: pip install anthropic")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEYY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEYY environment variable")
        return

    # Create validated agent
    agent = create_validated_agent(project="claude_demo")

    # Initialize Claude client
    client = anthropic.Anthropic(api_key=api_key)

    # Define tools for Claude
    tools = [
        {
            "name": "bash",
            "description": "Execute a bash command",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to run"}
                },
                "required": ["command"]
            }
        },
        {
            "name": "read_file",
            "description": "Read a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to file"}
                },
                "required": ["file_path"]
            }
        }
    ]

    # Example conversation
    messages = [
        {"role": "user", "content": "List the files in the current directory"}
    ]

    print("\n" + "=" * 60)
    print("CLAUDE INTEGRATION EXAMPLE")
    print("=" * 60)

    # Call Claude
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )

    # Process tool calls through supe validation
    for block in response.content:
        if block.type == "tool_use":
            tool_name = "Bash" if block.name == "bash" else "Read"
            tool_input = block.input

            print(f"\nClaude wants to use: {block.name}")
            print(f"Input: {json.dumps(tool_input)}")

            # Validate through supe
            result = await simulate_tool_execution(agent, tool_name, tool_input)

            if result["status"] == "blocked":
                print(f"🚫 BLOCKED by supe: {result.get('reason')}")
            else:
                print(f"✅ VALIDATED with proof: {result.get('proof_hash')}")


if __name__ == "__main__":
    print("\n🚀 Running Supe Validated Agent Demo\n")
    asyncio.run(demo())

    # Uncomment to run Claude integration
    # asyncio.run(claude_integration_example())
