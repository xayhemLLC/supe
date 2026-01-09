# Supe Project

## Project Overview

Supe is infrastructure for extending AI agent capabilities through:
- **AB Memory**: Structured storage with moments, cards, and buffers
- **Tasc**: Task management with atoms, plans, and tracking
- **Tascer**: Safe command execution with proof-of-work validation

## Architecture

```
supe/
├── ab/              # AB Memory Engine
│   ├── abdb.py      # SQLite database layer
│   ├── models.py    # Moment, Card, Buffer, CardStats
│   ├── search.py    # Semantic search
│   └── ...
├── tasc/            # Task Management
│   ├── atom.py      # Atomic work units
│   ├── tasc.py      # Task containers
│   ├── cli.py       # Command-line interface
│   └── tui.py       # Terminal UI
├── tascer/          # Validation Framework
│   ├── contracts.py # Context, ActionSpec, ActionResult
│   ├── llm_proof.py # Proof-of-work generation
│   ├── gates/       # Validation gates
│   ├── proofs/      # Proof generators
│   └── overlord/    # Decision loop
├── supe/            # Unified CLI
│   ├── cli.py       # Main entry point
│   └── mcp_server.py # MCP integration
├── scripts/         # Install/uninstall
└── tests/           # Test suite
```

## Development

```bash
# Install
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Test
pytest

# Lint
ruff check .
```

## CLI Commands

```bash
# Supe - Unified interface
supe status
supe prove "pytest"
supe verify <proof-id>

# Tasc - Task management
tasc save "description"
tasc list
tasc recall "search"
tasc ui

# Tascer - Validation
tascer run "command"
tascer check "command"
tascer checkpoint
tascer rollback
```

## Key Concepts

### AB Memory
SQLite-backed cognitive memory with:
- **Moments**: Discrete points in time
- **Cards**: Information containers with typed buffers
- **Buffers**: Payload storage (text, code, embeddings)
- **CardStats**: Decay and retrieval metrics

### Tasc
Task management with:
- **Atoms**: Smallest units of work
- **Tascs**: Task containers grouping atoms
- **Plans**: Multi-tasc orchestration

### Tascer
Validation layer providing:
- **Context**: Environment snapshots (git state, toolchain, etc.)
- **Proof generation**: Cryptographic validation of actions
- **Gates**: Pre/post validation checks

## Future Direction

Integration with Claude Agent SDK to replace custom tool implementations with SDK-native tools while preserving tascer's validation layer.
