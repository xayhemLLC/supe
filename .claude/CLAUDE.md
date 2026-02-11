# Supe Project

> Audit layer for AI agents: validation gates, proof-of-work logs, persistent memory.

## Quick Start

```bash
# Install
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Test
pytest tests/ -v

# Lint
ruff check .
```

## Architecture

```
supe/
├── ab/                    # AB Memory Engine (36 modules)
│   ├── abdb.py            # SQLite storage layer
│   ├── models.py          # Card, Buffer, Moment, CardStats
│   ├── recall.py          # Connection traversal
│   ├── search.py          # Keyword search
│   ├── neural_memory.py   # Spreading activation recall
│   ├── vector_search.py   # Embedding-based search
│   ├── embeddings.py      # Embedding generation
│   ├── decay.py           # Memory decay algorithms
│   ├── checkpoint.py      # State snapshots
│   └── ...
├── tasc/                  # Task Management (23 modules)
│   ├── atom.py            # Atomic work units
│   ├── tasc.py            # Task containers
│   ├── relations.py       # Card relationships
│   ├── evidence.py        # Evidence-based validation
│   ├── reasoning_engine.py # Logical reasoning
│   ├── cli.py             # CLI interface
│   ├── tui.py             # Terminal UI
│   └── ...
├── tascer/                # Validation Framework (67 modules)
│   ├── sdk_wrapper.py     # TascerAgent (MAIN ENTRY POINT)
│   ├── contracts.py       # GateResult, ValidationRecord
│   ├── llm_proof.py       # Proof-of-work generation
│   ├── gates/             # Validation gates (pre/post)
│   │   ├── exit_code.py   # Exit code validation
│   │   ├── patterns.py    # Pattern matching
│   │   └── file_gate.py   # File operation gates
│   ├── proofs/            # Proof generators
│   │   ├── tests_passing.py
│   │   ├── lint_passing.py
│   │   └── learning_proof.py
│   ├── primitives/        # Low-level operations
│   │   ├── git.py, git_mutations.py
│   │   ├── file_ops.py, file_mutations.py
│   │   ├── terminal.py, process.py
│   │   └── browser.py, http.py
│   ├── overlord/          # Decision loop
│   ├── ledgers/           # Execution history
│   └── actions/           # Action executors
├── supe/                  # Unified Interface (6 modules)
│   ├── cli.py             # Main CLI entry point
│   ├── supe.py            # Core Supe class
│   └── mcp_server.py      # MCP integration
├── scripts/               # Build & demo scripts
├── tests/                 # Test suite (20 test files)
└── docs/                  # Documentation
```

## Main APIs

### TascerAgent (Primary Entry Point)
```python
from ab import ABMemory
from tascer.sdk_wrapper import TascerAgent, TascerAgentOptions, ToolValidationConfig
from tascer.contracts import GateResult

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

@agent.register_gate("safe_commands")
def safe_commands(record, phase) -> GateResult:
    cmd = record.tool_input.get("command", "")
    if "rm -rf" in cmd:
        return GateResult("safe_commands", False, f"BLOCKED: {cmd}")
    return GateResult("safe_commands", True, f"Allowed: {cmd}")
```

### ABMemory
```python
from ab import ABMemory

ab = ABMemory("memory.sqlite")
card = ab.store("user_query", {"content": "What is X?"})
results = ab.recall("X", top_k=5)
```

## Key Concepts

### Validation Gates
Functions that run pre/post tool execution:
- Return `GateResult(name, passed: bool, message)`
- Pre-gates block execution before it happens
- Post-gates validate results after execution

### Proof-of-Work
SHA256 hashes for tamper-evident audit trails:
- Every tool execution generates a proof
- Proofs chain together for integrity verification
- Export with `agent.export_report("audit.json")`

### AB Memory
SQLite-backed cognitive memory:
- **Cards**: Information containers with typed buffers
- **Moments**: Points in time for temporal queries
- **Recall**: Keyword search + spreading activation

## CLI Commands

All commands are accessed through the unified `supe` CLI:

```bash
# Core commands
supe status              # Show system status
supe prove <cmd>         # Execute with proof generation
supe verify <proof-id>   # Verify an existing proof
supe run <cmd>           # Safe command execution
supe check <cmd>         # Dry-run safety check
supe checkpoint [name]   # Create checkpoint for rollback
supe rollback            # Rollback to last checkpoint
supe capture <url>       # Browser screenshot
supe plugins             # List available plugins
supe metrics             # Show metrics
supe benchmark           # Run benchmarks
supe audit <run_id>      # Export audit report

# Memory queries (supe memory)
supe memory search <query>   # Keyword search
supe memory semantic <query> # Vector similarity search
supe memory recall <query>   # Neural spreading activation
supe memory timeline         # Time range queries
supe memory card <id>        # Show card details
supe memory context <tool>   # Preview auto-context

# Task management (supe tasc)
supe tasc save [name]    # Save current work
supe tasc list           # List all tascs
supe tasc recall <query> # Search past work
supe tasc evolve <target> # Genetic evolution
supe tasc hook commit    # Install git hooks
supe tasc ui             # Launch TUI

# Plan management (supe plan)
supe plan create <file>  # Create plan from file
supe plan list           # List plans
supe plan generate <goal> # Claude-powered generation

# Sandbox mode (supe sandbox)
supe sandbox enter       # Enter sandbox mode
supe sandbox exit        # Exit (discard changes)
supe sandbox exit --commit # Exit (apply changes)

# Approval workflow (supe approve)
supe approve list        # List pending approvals
supe approve yes <id>    # Approve request
supe approve no <id>     # Reject request
supe approve show <id>   # Show details

# Human input for automation (supe input)
supe input list          # List pending inputs
supe input respond <id>  # Respond to input request

# Other
supe install             # Show installation info
supe mcp-server          # Start MCP server
```

## Code Style

- **Line length**: 100 chars (ruff config)
- **Python**: 3.10+
- **Async**: Use `pytest-asyncio` for async tests
- **Types**: Type hints encouraged but not enforced

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/test_tascer_contracts.py -v

# Run with coverage
pytest tests/ --cov=ab --cov=tasc --cov=tascer
```

Test files follow pattern: `tests/test_<module>.py`

## Common Tasks

### Adding a new validation gate
1. Create gate function returning `GateResult`
2. Register with `@agent.register_gate("name")`
3. Add to tool config: `ToolValidationConfig(pre_gates=["name"])`

### Adding a new proof type
1. Create module in `tascer/proofs/`
2. Implement proof generation logic
3. Register in proof registry

### Extending AB Memory
1. Models go in `ab/models.py`
2. Storage operations in `ab/abdb.py`
3. Search extensions in `ab/search.py` or `ab/neural_memory.py`

## Links

- **PyPI**: https://pypi.org/project/supe/
- **GitHub**: https://github.com/xayhemLLC/supe
- **Issues**: https://github.com/xayhemLLC/supe/issues
