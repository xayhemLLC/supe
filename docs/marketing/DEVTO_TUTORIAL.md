# Building AI Agents with a Brain: Neural Memory, Validation, and Proofs

> Your AI agent just deleted the production database. Now what?

AI agents are powerful, but they're also black boxes. When something goes wrong, you're left digging through logs trying to piece together what happened. And for regulated industries? Good luck explaining to auditors that your AI "just does things."

I built **Supe** to solve this problem. It's an open-source Python library that gives AI agents a proper cognitive architecture:

- **Neural Memory** with Hebbian learning and spreading activation
- **Validation Gates** that block dangerous operations before they happen
- **Proof-of-Work** that creates tamper-evident audit trails
- **Cognitive Hierarchy** with moments, cards, and buffers
- **Semantic Relations** with 7 typed connections

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
3. **Neural memory** - How do related concepts connect?
4. **Session memory** - What has this agent done before?

## Solution 1: Neural Memory

Supe doesn't just store data - it learns associations like a brain.

```python
from ab.neural_memory import NeuralMemory

neural = NeuralMemory()

# Add knowledge as cards
neural.add_card(1, {"title": "OAuth Authentication", "type": "feature"})
neural.add_card(2, {"title": "Login Page", "type": "feature"})
neural.add_card(3, {"title": "Session Management", "type": "feature"})

# Hebbian learning: "cells that fire together wire together"
neural.connect(1, 2)  # OAuth often used with Login
neural.connect(1, 3)  # OAuth often used with Sessions
neural.connect(1, 2)  # Repeated use = stronger connection

# Query with spreading activation
results = neural.recall("authentication login", top_k=5)
# Returns cards ranked by activation level, not just keyword match
```

**Key features:**
- **Long-term potentiation**: Frequently used paths strengthen
- **Synaptic depression**: Unused links decay over time
- **Hub formation**: Central concepts emerge naturally
- **Spreading activation**: Queries propagate through the network

## Solution 2: Validation Gates

Supe introduces "gates" - simple Python functions that run before and after every tool execution:

```python
from tascer.contracts import GateResult

@agent.register_gate("safe_commands")
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

## Solution 3: Cognitive Hierarchy

Not flat key-value storage. A real hierarchy:

```python
from ab import ABMemory, Buffer

ab = ABMemory(".tascer/memory.sqlite")

# Moments = work sessions
moment = ab.create_moment(master_input="RE analysis session")

# Cards = units of knowledge
card = ab.store_card(
    label="analysis:player_struct",
    buffers=[
        Buffer(name="definition", payload=b"struct Player { int health; int mana; }"),
        Buffer(name="offsets", payload=b'{"health": "0x10", "mana": "0x14"}'),
    ],
    moment_id=moment.id,
)
```

**Hierarchy:**
- **Moments** → Sessions of work
  - **Cards** → Units of knowledge
    - **Buffers** → Raw data payloads

## Solution 4: Semantic Relations

Knowledge has relationships. Capture them:

```python
from tasc.relations import Relation, RelationType, RelationCollection

# 7 relation types
relations = [
    Relation.create("r1", RelationType.SUPPORTS, evidence_id, hypothesis_id, 0.9),
    Relation.create("r2", RelationType.CONTRADICTS, old_id, new_id, 0.8),
    Relation.create("r3", RelationType.DEPENDS_ON, feature_id, library_id, 1.0),
]

# Organize in collections
collection = RelationCollection(id="audit-findings", description="Security audit")
for rel in relations:
    collection.add_relation(rel)
```

**7 Types:**
- CAUSES, IMPLIES, CONTRADICTS
- SUPPORTS, DEPENDS_ON
- EQUALS, TRANSFORMS

## Setting Up TascerAgent

TascerAgent wraps any Claude SDK agent with validation:

```python
from ab import ABMemory
from tascer.sdk_wrapper import (
    TascerAgent,
    TascerAgentOptions,
    ToolValidationConfig,
    RecallConfig,
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
        recall_config=RecallConfig(
            enabled=True,
            index_on_store=True,
        ),
    ),
    ab_memory=ab,
)

# Register your custom gate
@agent.register_gate("safe_commands")
def safe_commands(record, phase) -> GateResult:
    if phase != "pre":
        return GateResult("safe_commands", True, "OK")
    cmd = record.tool_input.get("command", "")
    if "rm -rf" in cmd:
        return GateResult("safe_commands", False, "BLOCKED")
    return GateResult("safe_commands", True, "OK")
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

## Task Management with Evidence

14 evidence types for task completion:

```python
from tasc.tasc import Tasc
from tasc.evidence import Evidence, EvidenceSource
from tasc.domains import infer_domain_from_title

# Create a task
task = Tasc(
    id="task-001",
    status="pending",
    title="Fix security vulnerability in auth",
)

# Auto-infer domain (7 categories)
domain = infer_domain_from_title(task.title)
# Returns: TaskDomain.SECURITY

# Attach evidence
evidence = [
    Evidence.create("Tests pass", EvidenceSource.TEST, ["pytest: 42 passed"]),
    Evidence.create("Code reviewed", EvidenceSource.PEER_REVIEW, ["PR #123"]),
    Evidence.create("Scan clean", EvidenceSource.SECURITY_SCAN, ["snyk: 0 vulns"]),
]
```

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

## Complete Example

```python
import asyncio
from ab import ABMemory
from ab.neural_memory import NeuralMemory
from tascer.sdk_wrapper import (
    TascerAgent,
    TascerAgentOptions,
    ToolValidationConfig,
    RecallConfig,
)
from tascer.contracts import GateResult

# Setup cognitive memory
ab = ABMemory(".tascer/agent_memory.sqlite")
neural = NeuralMemory()

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
            auto_context=True,
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

# Add more gates as needed...

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

## Run the Demo

```bash
python scripts/demo_full_capabilities.py
```

## What's Included

| Component | Features |
|-----------|----------|
| **AB Memory** | Moments, cards, buffers - cognitive hierarchy |
| **Neural Memory** | Hebbian learning, spreading activation, hub formation |
| **Tascer** | Validation gates, proof chains, recall |
| **Tasc** | Task management, 14 evidence types, 7 domains |
| **Relations** | 7 semantic types (CAUSES, SUPPORTS, etc.) |

- 343 tests passing
- MIT license
- Python 3.10+
- Full type hints
- Async support

## What's Next?

Supe is open source and we'd love contributions:

- **More gates**: Rate limiting, cost tracking, API quotas
- **Integrations**: LangChain, LlamaIndex, OpenAI
- **Visualization**: Audit trail dashboard

Check out the repo: [github.com/xayhemLLC/supe](https://github.com/xayhemLLC/supe)

---

*Have questions? Open an issue or drop a comment below!*
