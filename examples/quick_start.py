#!/usr/bin/env python3
"""Quick Start: Minimal Supe Integration.

Copy this to your project and customize the gates.

Usage:
    from quick_start import get_agent, validate_tool_call

    agent = get_agent("my_project")
    result = await validate_tool_call(agent, "Bash", {"command": "ls"})
"""

import os
from ab import ABMemory
from tascer.sdk_wrapper import (
    TascerAgent,
    TascerAgentOptions,
    ToolValidationConfig,
    RecallConfig,
)
from tascer.contracts import GateResult


# =============================================================================
# CUSTOMIZE THESE GATES FOR YOUR PROJECT
# =============================================================================

def gate_block_dangerous(record, phase) -> GateResult:
    """Block dangerous operations. Customize for your needs."""
    if phase != "pre":
        return GateResult("block_dangerous", True, "OK")

    cmd = record.tool_input.get("command", "")
    path = record.tool_input.get("file_path", "")

    # Add your blocked patterns here
    blocked_patterns = [
        "rm -rf /",
        "sudo",
        "/etc/passwd",
        "DROP TABLE",
        "DELETE FROM",
    ]

    for pattern in blocked_patterns:
        if pattern in cmd or pattern in path:
            return GateResult("block_dangerous", False, f"BLOCKED: {pattern}")

    return GateResult("block_dangerous", True, "OK")


# =============================================================================
# AGENT FACTORY
# =============================================================================

_agents = {}


def get_agent(project: str = "default") -> TascerAgent:
    """Get or create a validated agent for a project."""
    if project not in _agents:
        db_path = os.path.expanduser("~/.supe/memory.sqlite")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        agent = TascerAgent(
            tascer_options=TascerAgentOptions(
                tool_configs={
                    "Bash": ToolValidationConfig(
                        tool_name="Bash",
                        pre_gates=["block_dangerous"],
                        post_gates=["exit_code_zero"],
                    ),
                },
                default_pre_gates=["block_dangerous"],
                recall_config=RecallConfig(
                    enabled=True,
                    auto_context=True,
                    auto_context_limit=3,
                ),
                generate_proofs=True,
                store_to_ab=True,
            ),
            ab_memory=ABMemory(db_path),
        )

        agent.register_gate("block_dangerous", gate_block_dangerous)
        _agents[project] = agent

    return _agents[project]


# =============================================================================
# VALIDATION HELPER
# =============================================================================

async def validate_tool_call(
    agent: TascerAgent,
    tool_name: str,
    tool_input: dict,
    tool_output: any = None,
) -> dict:
    """Validate a tool call through supe.

    Args:
        agent: TascerAgent instance
        tool_name: Name of the tool (Bash, Read, Write, etc.)
        tool_input: Tool input parameters
        tool_output: Tool output (for post-validation)

    Returns:
        {
            "allowed": bool,
            "proof_hash": str or None,
            "context": str or None,  # Injected context from memory
            "message": str,
        }
    """
    import uuid
    tool_use_id = f"tu_{uuid.uuid4().hex[:8]}"

    # Pre-validation
    pre_result = await agent._pre_tool_hook(
        {"tool_name": tool_name, "tool_input": tool_input},
        tool_use_id,
        None,
    )

    if pre_result.get("block"):
        return {
            "allowed": False,
            "proof_hash": None,
            "context": None,
            "message": pre_result.get("message", "Blocked"),
        }

    # Post-validation (if output provided)
    if tool_output is not None:
        await agent._post_tool_hook(
            {"tool_result": tool_output},
            tool_use_id,
            None,
        )

    record = agent._find_record(tool_use_id)

    return {
        "allowed": True,
        "proof_hash": record.proof_hash if record else None,
        "context": pre_result.get("context"),
        "message": "Validated",
    }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def check_bash(command: str, project: str = "default") -> bool:
    """Quick check if a bash command is allowed."""
    agent = get_agent(project)
    result = await validate_tool_call(agent, "Bash", {"command": command})
    return result["allowed"]


async def check_file(file_path: str, project: str = "default") -> bool:
    """Quick check if a file path is allowed."""
    agent = get_agent(project)
    result = await validate_tool_call(agent, "Read", {"file_path": file_path})
    return result["allowed"]


def recall_similar(query: str, project: str = "default", top_k: int = 5) -> list:
    """Recall similar past executions."""
    agent = get_agent(project)
    return agent.recall(query, top_k=top_k)


# =============================================================================
# EXAMPLE
# =============================================================================

if __name__ == "__main__":
    import asyncio

    async def main():
        agent = get_agent("test")

        # Test some commands
        tests = [
            ("ls -la", True),
            ("rm -rf /", False),
            ("git status", True),
            ("sudo rm", False),
        ]

        print("Quick validation tests:")
        for cmd, expected in tests:
            allowed = await check_bash(cmd)
            icon = "✅" if allowed == expected else "❌"
            print(f"  {icon} '{cmd}' -> allowed={allowed}")

    asyncio.run(main())
