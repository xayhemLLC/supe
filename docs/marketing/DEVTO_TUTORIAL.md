# Building Auditable AI Agents with Python: A Practical Guide

> Your AI agent just deleted the production database. Now what?

AI agents are powerful, but they're also black boxes. When something goes wrong, you're left digging through logs trying to piece together what happened. And for regulated industries? Good luck explaining to auditors that your AI "just does things."

I built **Supe** to solve this problem. It's an open-source Python library that wraps AI agent SDKs (like Claude's) with:

- **Validation gates** that block dangerous operations before they happen
- **Proof-of-work** that creates tamper-evident audit trails
- **Recall** that lets you query past executions

Let me show you how it works.

## The Problem

Here's a typical AI agent flow:

```
User: "Clean up old log files"
Agent: *runs rm -rf /*
User: "Wait, what?"
```

Most agent frameworks have no concept of:
1. **Pre-execution validation** - Can I stop this before it happens?
2. **Audit trails** - What exactly did the agent do?
3. **Session memory** - What has this agent done before?

## The Solution: Validation Gates

Supe introduces "gates" - simple Python functions that run before and after every tool execution:

```python
from tascer.contracts import GateResult

def safe_commands(record, phase) -> GateResult:
    """Block dangerous shell commands."""
    if phase != "pre":
        return GateResult("safe_commands", True, "Post-check skipped")

    cmd = record.tool_input.get("command", "")
    dangerous = ["rm -rf", "DROP TABLE", "> /dev/sda", "format"]

    for pattern in dangerous:
        if pattern in cmd:
            return GateResult(
                gate_name="safe_commands",
                passed=False,
                message=f"BLOCKED: dangerous pattern '{pattern}'"
            )

    return GateResult("safe_commands", True, f"Allowed: {cmd}")
```

That's it. A gate is just a function that returns `GateResult(name, passed, message)`.

## Setting Up TascerAgent

TascerAgent wraps any Claude SDK agent with validation:

```python
from ab import ABMemory
from tascer.sdk_wrapper import (
    TascerAgent,
    TascerAgentOptions,
    ToolValidationConfig,
)

# Persistent memory storage
ab = ABMemory(".tascer/memory.sqlite")

# Create the agent
agent = TascerAgent(
    tascer_options=TascerAgentOptions(
        tool_configs={
            "Bash": ToolValidationConfig(
                tool_name="Bash",
                pre_gates=["safe_commands"],  # Run before execution
                post_gates=["exit_code_ok"],  # Run after execution
            ),
            "Write": ToolValidationConfig(
                tool_name="Write",
                pre_gates=["no_system_files"],
            ),
        },
        store_to_ab=True,  # Enable persistent storage
    ),
    ab_memory=ab,
)

# Register your custom gate
agent.register_gate("safe_commands", safe_commands)
```

Now every Bash command goes through your `safe_commands` gate before executing.

## Real Example: Read-Only Reverse Engineering Mode

Here's a practical use case. You want an AI agent to analyze game binaries, but it should NEVER modify game files:

```python
@agent.register_gate("read_only_mode")
def read_only_mode(record, phase) -> GateResult:
    """Block writes to game directories."""
    if phase != "pre":
        return GateResult("read_only_mode", True, "Post-check")

    if record.tool_name == "Write":
        path = record.tool_input.get("file_path", "")
        if "/game/" in path or "/binary/" in path:
            return GateResult(
                "read_only_mode",
                False,
                f"BLOCKED: Cannot write to game files"
            )

    return GateResult("read_only_mode", True, "Allowed")

@agent.register_gate("command_whitelist")
def command_whitelist(record, phase) -> GateResult:
    """Only allow specific RE tools."""
    if phase != "pre":
        return GateResult("command_whitelist", True, "Post-check")

    cmd = record.tool_input.get("command", "")
    allowed = ["ghidra", "radare2", "strings", "objdump", "hexdump", "file"]

    if any(cmd.startswith(tool) for tool in allowed):
        return GateResult("command_whitelist", True, f"Allowed: {cmd}")

    return GateResult("command_whitelist", False, f"BLOCKED: {cmd}")
```

## Proof-of-Work: Tamper-Evident Audit Trails

Every execution generates a SHA256 proof:

```python
# After running some operations...
for record in agent.get_validation_report():
    print(f"""
    Tool: {record.tool_name}
    Input: {record.tool_input}
    Status: {record.status}
    Proof: {record.proof_hash}
    Timestamp: {record.timestamp}
    """)

# Verify nothing was tampered with
assert agent.verify_proofs()  # Returns False if any proof is invalid

# Export for compliance
agent.export_report("audit_trail.json")
```

The proof hash is computed from the tool name, input, output, and timestamp. If anyone modifies the records, the proofs won't verify.

## Recall: Query Past Executions

Every execution is stored as a Card in AB Memory, enabling powerful queries:

```python
# Keyword search with neural spreading activation
results = agent.recall("player struct", top_k=5)
for r in results:
    print(f"[{r.score:.2f}] {r.tool_name}: {r.tool_input}")

# Filter by tool type
bash_history = agent.recall_tool("Bash")

# Get full session history
history = agent.recall_session()

# Find similar past executions
similar = agent.recall_similar({"file_path": "/app/config.py"})
```

This is incredibly useful for:
- **Debugging**: "What commands led to this state?"
- **Context**: "What has the agent learned about this file?"
- **Compliance**: "Show me everything the agent did on Tuesday"

## Putting It All Together

Here's a complete example:

```python
import asyncio
from ab import ABMemory
from tascer.sdk_wrapper import (
    TascerAgent,
    TascerAgentOptions,
    ToolValidationConfig,
    RecallConfig,
)
from tascer.contracts import GateResult

# Setup
ab = ABMemory(".tascer/agent_memory.sqlite")

agent = TascerAgent(
    tascer_options=TascerAgentOptions(
        tool_configs={
            "Bash": ToolValidationConfig(
                tool_name="Bash",
                pre_gates=["safe_commands", "command_whitelist"],
            ),
            "Write": ToolValidationConfig(
                tool_name="Write",
                pre_gates=["read_only_mode"],
            ),
            "Read": ToolValidationConfig(tool_name="Read"),
        },
        store_to_ab=True,
        recall_config=RecallConfig(
            enabled=True,
            index_on_store=True,
            auto_context=True,  # Auto-retrieve relevant past executions
        ),
    ),
    ab_memory=ab,
)

# Register gates
@agent.register_gate("safe_commands")
def safe_commands(record, phase) -> GateResult:
    if phase != "pre":
        return GateResult("safe_commands", True, "OK")
    cmd = record.tool_input.get("command", "")
    if any(d in cmd for d in ["rm -rf", "DROP", "> /dev"]):
        return GateResult("safe_commands", False, f"BLOCKED: {cmd}")
    return GateResult("safe_commands", True, "OK")

# ... add more gates as needed

# Use the agent
async def main():
    # Your agent logic here...

    # Check audit trail
    records = agent.get_validation_report()
    print(f"Total executions: {len(records)}")
    print(f"Blocked: {sum(1 for r in records if r.status == 'blocked')}")
    print(f"All proofs valid: {agent.verify_proofs()}")

    # Query history
    results = agent.recall("database query", top_k=3)
    for r in results:
        print(f"Found: {r.tool_name} - {r.tool_input}")

asyncio.run(main())
```

## Installation

```bash
pip install supe

# With Claude SDK integration
pip install supe[anthropic]
```

## What's Next?

Supe is open source and we'd love contributions:

- **More gates**: Rate limiting, cost tracking, API quotas
- **Integrations**: LangChain, LlamaIndex, OpenAI
- **Visualization**: Audit trail dashboard

Check out the repo: [github.com/xayhemLLC/supe](https://github.com/xayhemLLC/supe)

---

*Have questions? Open an issue or drop a comment below!*
