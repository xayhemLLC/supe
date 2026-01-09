# Supe

> **Your AI agent just mass-deleted files. Can you prove it wasn't supposed to?**

**Supe** is the missing audit layer for AI agents. Validation gates block dangerous operations, proof-of-work creates tamper-evident logs, and persistent memory lets you query what your agent actually did.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-343%20passing-brightgreen.svg)]()
[![PyPI](https://img.shields.io/pypi/v/supe.svg)](https://pypi.org/project/supe/)

<!-- Demo GIF placeholder - record with: python scripts/demo_recording.py -->
<!-- ![Demo](docs/demo.gif) -->

## Why Supe?

| Feature | LangChain | AutoGPT | CrewAI | **Supe** |
|---------|:---------:|:-------:|:------:|:--------:|
| Pre-execution validation | - | - | - | **Yes** |
| Post-execution validation | - | - | - | **Yes** |
| Proof-of-work audit trail | - | - | - | **Yes** |
| Query past executions | - | Partial | - | **Yes** |
| Custom validation gates | - | - | - | **Yes** |
| Session memory persistence | - | Partial | Partial | **Yes** |
| Neural recall (spreading activation) | - | - | - | **Yes** |

## Install

```bash
pip install supe

# With Claude SDK integration
pip install supe[anthropic]
```

## 60-Second Example

```python
from ab import ABMemory
from tascer.sdk_wrapper import TascerAgent, TascerAgentOptions, ToolValidationConfig
from tascer.contracts import GateResult

# 1. Create agent with memory
ab = ABMemory(".tascer/memory.sqlite")
agent = TascerAgent(
    tascer_options=TascerAgentOptions(
        tool_configs={
            "Bash": ToolValidationConfig(tool_name="Bash", pre_gates=["safe_commands"]),
        },
        store_to_ab=True,
    ),
    ab_memory=ab,
)

# 2. Add a custom gate (just a Python function)
@agent.register_gate("safe_commands")
def safe_commands(record, phase) -> GateResult:
    cmd = record.tool_input.get("command", "")
    dangerous = ["rm -rf", "DROP TABLE", "format", "> /dev/sda"]

    if any(d in cmd for d in dangerous):
        return GateResult("safe_commands", False, f"BLOCKED: {cmd}")
    return GateResult("safe_commands", True, f"Allowed: {cmd}")

# 3. Every execution generates a proof
for record in agent.get_validation_report():
    print(f"{record.tool_name}: {record.proof_hash[:16]}...")

# 4. Query what happened
results = agent.recall("database operations", top_k=5)
```

## Core Concepts

### Validation Gates

Gates run before (pre) and after (post) every tool execution:

```python
@agent.register_gate("read_only_mode")
def read_only_mode(record, phase) -> GateResult:
    """Block all write operations."""
    if phase != "pre":
        return GateResult("read_only_mode", True, "Post-check skipped")

    write_tools = ["Write", "Edit", "Bash"]
    if record.tool_name in write_tools:
        cmd = record.tool_input.get("command", "")
        if any(w in cmd for w in [">", ">>", "rm", "mv", "cp"]):
            return GateResult("read_only_mode", False, "Write operation blocked")

    return GateResult("read_only_mode", True, "Read operation allowed")
```

### Proof-of-Work

Every execution gets a SHA256 proof that's tamper-evident:

```python
# Verify all proofs in a session
assert agent.verify_proofs()  # Returns False if anything was tampered

# Export audit report
agent.export_report("audit_trail.json")
```

### Recall System

Query past executions with keyword search and neural spreading activation:

```python
# Keyword search
results = agent.recall("player struct", top_k=5)

# Filter by tool
bash_history = agent.recall_tool("Bash")

# Get full session history
history = agent.recall_session()

# Find similar past executions
similar = agent.recall_similar({"file_path": "/app/config.py"})

# Auto-context for upcoming calls
context = agent.get_context_for("Read", {"file_path": "/app/auth.py"})
```

## Real-World Use Cases

### Reverse Engineering (Read-Only Mode)
```python
# Agent can analyze binaries but can't modify game files
agent = TascerAgent(
    tascer_options=TascerAgentOptions(
        tool_configs={
            "Bash": ToolValidationConfig(pre_gates=["command_whitelist"]),
            "Write": ToolValidationConfig(pre_gates=["block_game_files"]),
        },
    ),
)

# Whitelist only RE tools
@agent.register_gate("command_whitelist")
def command_whitelist(record, phase) -> GateResult:
    allowed = ["ghidra", "radare2", "strings", "objdump", "hexdump"]
    cmd = record.tool_input.get("command", "")
    if any(cmd.startswith(a) for a in allowed):
        return GateResult("command_whitelist", True, "Allowed")
    return GateResult("command_whitelist", False, f"Blocked: {cmd}")
```

### Code Review Bot (No Push to Main)
```python
@agent.register_gate("no_push_main")
def no_push_main(record, phase) -> GateResult:
    cmd = record.tool_input.get("command", "")
    if "git push" in cmd and ("main" in cmd or "master" in cmd):
        return GateResult("no_push_main", False, "Cannot push to main/master")
    return GateResult("no_push_main", True, "Allowed")
```

### Compliance/Audit Requirements
```python
# Every action has a verifiable proof
for record in agent.get_validation_report():
    print(f"""
    Tool: {record.tool_name}
    Input: {record.tool_input}
    Output: {record.tool_output[:100]}...
    Proof: {record.proof_hash}
    Status: {record.status}
    Timestamp: {record.timestamp}
    """)

# Export for compliance
agent.export_report("compliance_audit.json")
```

## Demo

```bash
# Clone and run the reverse engineering demo
git clone https://github.com/xayhemLLC/supe.git
cd supe && pip install -e .
python scripts/demo_tascer_re_workflow.py
```

Output:
```
PHASE 1: Initial Binary Analysis
[1.1] Reading binary header...
[1.2] Running Ghidra headless analysis...
      Result: Found 12,847 functions, 8,234 strings

PHASE 3: Security Gates Demo
[3.1] Attempting to patch game binary (should be BLOCKED)...
      BLOCKED: Write blocked: RE mode is read-only for game files

PHASE 4: Recall - Querying Past Analysis
[4.3] Recall Tool: All Bash commands
      - strings -n 10 game_client.exe | grep -i player
      - radare2 -c 'px 0x100 @ 0x7FF600004A80' memdump.bin
      - ghidra_headless /analysis game_client.exe --analyze

PHASE 5: Audit Trail
      Total: 9 executions
      Validated: 7 | Blocked: 2 | Failed: 0
      All proofs valid: True
```

## Architecture

```
supe/
├── ab/                  # AB Memory Engine
│   ├── abdb.py          # SQLite storage layer
│   ├── models.py        # Card, Buffer, Moment
│   ├── recall.py        # Connection traversal
│   ├── search.py        # Keyword search
│   └── neural_memory.py # Spreading activation
├── tascer/              # Validation Framework
│   ├── sdk_wrapper.py   # TascerAgent
│   ├── contracts.py     # GateResult, ValidationRecord
│   ├── gates/           # Built-in gates
│   └── proofs/          # Proof generators
└── tests/               # 343 tests
```

## Development

```bash
git clone https://github.com/xayhemLLC/supe.git
cd supe

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check .
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Areas we'd love help with:
- More validation gates (rate limiting, cost tracking)
- Integrations (LangChain, LlamaIndex, OpenAI)
- Documentation and tutorials

## License

MIT - see [LICENSE](LICENSE)

---

**Links:** [PyPI](https://pypi.org/project/supe/) · [GitHub](https://github.com/xayhemLLC/supe) · [Issues](https://github.com/xayhemLLC/supe/issues)
