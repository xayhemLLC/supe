# Supe

**Cognitive memory for AI agents.** Structured storage, task management, and proof-of-work validation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-54%20passing-brightgreen.svg)]()

## Core Components

| Component | Purpose |
|-----------|---------|
| **AB Memory** | Structured storage with moments, cards, and buffers |
| **Tasc** | Task management with plans and tracking |
| **Tascer** | Validation framework with proof generation |
| **TascerAgent** | Claude Agent SDK wrapper with validation hooks |

## Quick Start

```bash
git clone https://github.com/xayhemLLC/supe.git
cd supe

# Install with uv (recommended)
uv venv && source .venv/bin/activate
uv pip install -e .

# Or with pip
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## TascerAgent - Validated AI Agent Execution

Wrap Claude Agent SDK with validation gates and audit trails:

```python
from ab import ABMemory
from tascer.sdk_wrapper import TascerAgent, TascerAgentOptions, ToolValidationConfig

# Create agent with AB Memory for persistent storage
ab = ABMemory(".tascer/memory.sqlite")
agent = TascerAgent(
    tascer_options=TascerAgentOptions(
        tool_configs={
            "Bash": ToolValidationConfig(
                tool_name="Bash",
                pre_gates=["command_allowed"],
                post_gates=["exit_code_zero"],
            ),
            "Write": ToolValidationConfig(
                tool_name="Write",
                pre_gates=["read_only_mode"],  # Block writes in RE mode
            ),
        },
        store_to_ab=True,
    ),
    ab_memory=ab,
)

# Execute with validation
async for msg in agent.query("Analyze the binary"):
    print(msg)

# Verify all proofs
assert agent.verify_proofs()
```

### Custom Validation Gates

```python
from tascer.contracts import GateResult

@agent.register_gate("command_whitelist")
def command_whitelist(record, phase) -> GateResult:
    """Only allow specific commands."""
    if phase != "pre":
        return GateResult("command_whitelist", True, "Post-check skipped")

    cmd = record.tool_input.get("command", "")
    allowed = ["ghidra", "radare2", "strings", "objdump"]

    if any(cmd.startswith(a) for a in allowed):
        return GateResult("command_whitelist", True, f"Allowed: {cmd}")

    return GateResult("command_whitelist", False, f"Blocked: {cmd}")
```

## Recall - Query Past Executions

TascerAgent stores all executions as Cards in AB Memory, enabling powerful recall:

```python
# Keyword search with neural spreading activation
results = agent.recall("struct player", top_k=5)
for r in results:
    print(f"[{r.score:.2f}] {r.tool_name}: {r.tool_input}")

# Filter by tool
bash_history = agent.recall_tool("Bash", top_k=10)

# Find similar executions
similar = agent.recall_similar({"file_path": "/app/auth.py"})

# Get session history
history = agent.recall_session()

# Auto-context for upcoming tool calls
context = agent.get_context_for("Read", {"file_path": "/app/config.py"})
```

## Demo: Reverse Engineering Workflow

See the full capabilities in action:

```bash
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

## AB Memory - Structured Storage

Cards with Buffers for structured data:

```python
from ab import ABMemory, Card, Buffer

ab = ABMemory("memory.sqlite")

# Create a moment (container for cards)
moment = ab.create_moment(master_input="Analysis session")

# Store a card with multiple buffers
card = ab.store_card(
    label="analysis:player_struct",
    buffers=[
        Buffer(name="definition", payload=struct_bytes),
        Buffer(name="offsets", payload=json.dumps(offsets).encode()),
    ],
    moment_id=moment.id,
    track="structs",
)

# Recall with keyword search
from ab.recall import recall_cards
results = recall_cards(ab, query="player health", top_k=5)
```

## CLI Commands

### `supe` - Unified Interface
```bash
supe status              # System status
supe prove "pytest"      # Execute with proof
supe verify <proof-id>   # Verify a proof
```

### `tasc` - Task Management
```bash
tasc save "auth fix"     # Save work as a tasc
tasc list                # List all tascs
tasc recall "login"      # Find past work
tasc ui                  # Launch interactive TUI
```

### `tascer` - Safety & Validation
```bash
tascer run "command"     # Run with safety checks
tascer checkpoint        # Create checkpoint
tascer rollback          # Rollback changes
```

## Project Structure

```
supe/
├── ab/              # AB Memory Engine
│   ├── abdb.py      # Database layer
│   ├── models.py    # Card, Buffer, Moment models
│   ├── recall.py    # Recall with connection traversal
│   ├── search.py    # Keyword and filter search
│   └── neural_memory.py  # Spreading activation
├── tasc/            # Task management
├── tascer/          # Validation framework
│   ├── sdk_wrapper.py    # TascerAgent (Claude SDK wrapper)
│   ├── contracts.py      # GateResult, Context, etc.
│   ├── gates/            # Validation gates
│   └── proofs/           # Proof generators
├── supe/            # Unified CLI
├── scripts/         # Demo and install scripts
│   ├── demo_tascer_re_workflow.py  # RE demo
│   └── test_tascer_agent.py        # Integration test
└── tests/           # 54 tests
```

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests (54 passing)
pytest tests/test_sdk_wrapper.py -v

# Run linter
ruff check .
```

## License

MIT
