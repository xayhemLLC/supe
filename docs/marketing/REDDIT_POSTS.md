# Reddit Posts

---

## r/MachineLearning

### Title
[P] Supe: Validation gates and proof-of-work audit trails for AI agents

### Body

I've been working on a library to solve a practical problem with AI agents: how do you validate what they're doing and audit what they did?

**Supe** adds three things to AI agent workflows:

1. **Validation gates** - Functions that run before/after tool executions. Block dangerous commands, enforce read-only mode, whitelist operations - all with simple Python functions.

2. **Proof-of-work** - SHA256 hashes of every execution for tamper-evident audit trails. If anyone modifies execution records, the proofs won't verify.

3. **Neural recall** - Executions stored with spreading activation for semantic search. Query "player struct analysis" and get relevant past executions.

**Not about alignment** - This is practical validation for specific use cases (RE workflows, compliance requirements), not general AI safety.

**Key design decision:** Gates are just Python functions returning `GateResult(name, passed, message)`. No DSL, no config files, just code.

```python
@agent.register_gate("safe_commands")
def safe_commands(record, phase) -> GateResult:
    if "rm -rf" in record.tool_input.get("command", ""):
        return GateResult("safe_commands", False, "BLOCKED")
    return GateResult("safe_commands", True, "OK")
```

343 tests, MIT license, pip installable.

GitHub: https://github.com/xayhemLLC/supe

Would appreciate feedback on the approach, especially from anyone working on agent tooling or compliance.

---

## r/LocalLLaMA

### Title
Supe: Add validation gates and audit trails to your AI agents (open source)

### Body

Built this for a reverse engineering workflow where I wanted Claude to analyze game binaries but NOT modify anything.

**Supe** wraps AI agent SDKs with:

- **Gates** - Block dangerous operations before they happen
- **Proofs** - SHA256 audit trail for every execution
- **Recall** - Query past executions ("show me all Bash commands")

**Example:** Read-only mode for RE

```python
@agent.register_gate("command_whitelist")
def command_whitelist(record, phase) -> GateResult:
    allowed = ["ghidra", "radare2", "strings", "objdump"]
    cmd = record.tool_input.get("command", "")
    if any(cmd.startswith(a) for a in allowed):
        return GateResult("command_whitelist", True, "OK")
    return GateResult("command_whitelist", False, f"BLOCKED: {cmd}")
```

Works with Claude SDK, planning OpenAI support.

- 343 tests
- MIT license
- `pip install supe`

GitHub: https://github.com/xayhemLLC/supe

---

## r/Python

### Title
Supe: Validation framework for AI agents with proof-of-work audit trails

### Body

Sharing an open source library I built for validating AI agent actions.

**Problem:** AI agents (Claude, GPT, etc.) can execute tools, but there's no standard way to:
1. Block dangerous operations before they happen
2. Create audit trails of what was executed
3. Query past executions

**Solution:** Supe adds validation "gates" that are just Python functions:

```python
from tascer.contracts import GateResult

@agent.register_gate("safe_commands")
def safe_commands(record, phase) -> GateResult:
    """Block dangerous shell commands."""
    cmd = record.tool_input.get("command", "")
    dangerous = ["rm -rf", "DROP TABLE", "> /dev/sda"]

    if any(d in cmd for d in dangerous):
        return GateResult("safe_commands", False, f"BLOCKED: {cmd}")
    return GateResult("safe_commands", True, "OK")
```

**Features:**
- Pre and post-execution gates
- SHA256 proof-of-work for each execution
- Persistent memory with semantic search (neural spreading activation)
- Export audit reports for compliance

**Tech:**
- Pure Python, minimal dependencies (click, rich, numpy)
- SQLite storage (via custom AB Memory engine)
- 343 tests, type hints throughout
- Python 3.10+

`pip install supe`

GitHub: https://github.com/xayhemLLC/supe

Would love feedback on the API design!

---

## r/ClaudeAI

### Title
Built a validation layer for Claude agents - gates, proofs, and recall

### Body

I use Claude for reverse engineering workflows but needed guardrails. Built **Supe** to add:

**1. Validation gates** - Block operations before Claude executes them

```python
@agent.register_gate("no_writes")
def no_writes(record, phase) -> GateResult:
    if record.tool_name == "Write" and "/game/" in record.tool_input.get("file_path", ""):
        return GateResult("no_writes", False, "Cannot modify game files")
    return GateResult("no_writes", True, "OK")
```

**2. Proof-of-work** - Every tool execution gets a SHA256 proof

```python
agent.verify_proofs()  # Returns False if audit log was tampered
agent.export_report("audit.json")  # For compliance
```

**3. Recall** - Query past executions

```python
results = agent.recall("player struct", top_k=5)
bash_history = agent.recall_tool("Bash")
```

Works as a wrapper around Claude Agent SDK.

GitHub: https://github.com/xayhemLLC/supe
`pip install supe[anthropic]`
