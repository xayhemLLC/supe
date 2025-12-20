# Supe 🚀

**Super simple, super powerful.** A cognitive memory system for AI agents with task management and proof-of-work validation.

[![CI](https://github.com/your-repo/supe/workflows/CI/badge.svg)](https://github.com/your-repo/supe/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Features

- 🧠 **AB Memory** - Structured storage with moments, cards, and buffers
- 📋 **Tasc** - Task management with plans and tracking
- 🔒 **Tascer** - Safe command execution with proof generation
- ✅ **LLM Proof-of-Work** - Validate AI agent actions through structured proofs
- 🐳 **Cross-Platform** - Docker, Linux, macOS, and cloud ready

## Quick Install

```bash
# Clone and install
git clone https://github.com/your-repo/supe.git
cd supe

# Option 1: With uv (recommended)
uv venv && source .venv/bin/activate
uv pip install -e .

# Option 2: With pip
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Option 3: One-liner script
./scripts/install.sh
```

## CLI Commands

Supe provides three main CLIs:

### `supe` - Unified Interface
```bash
supe status              # System status
supe prove "pytest"      # Execute with proof
supe verify <proof-id>   # Verify a proof
supe run "npm test"      # Safe command execution
supe tasc save "work"    # Save current work
supe plan create file.md # Create a plan
```

### `tasc` / `t` - Task Management
```bash
tasc save "auth fix"     # Save work as a tasc
tasc list                # List all tascs
tasc recall "login"      # Find past work
tasc plan design.md      # Track a plan
tasc ui                  # Launch interactive TUI
```

### `tascer` - Safety & Validation
```bash
tascer run "command"     # Run with safety checks
tascer check "rm -rf"    # Check if command is safe
tascer checkpoint        # Create checkpoint
tascer rollback          # Rollback changes
tascer sandbox enter     # Enter sandbox mode
tascer benchmark         # Run capability benchmarks
```

## LLM Proof-of-Work

Enforce structured execution for AI agents:

```python
from tascer import create_plan, execute_plan, verify_plan_completion

# Create a structured plan
plan = create_plan(
    title="Implement Auth",
    tasks=[
        {
            "id": "task_1",
            "title": "Create auth module",
            "subtasks": [
                {"action": "write_code", "command": "touch auth.py"},
                {"action": "test", "command": "pytest tests/test_auth.py"},
            ],
        },
        {
            "id": "task_2", 
            "title": "Add API endpoints",
            "dependencies": ["task_1"],
        },
    ],
)

# Execute with proof generation
report = execute_plan(plan)

# Verify completion
verification = verify_plan_completion(plan)
print(f"Plan verified: {verification.verified}")
print(f"Proof hash: {verification.overall_proof_hash}")
```

## Docker Deployment

```bash
# Build
docker build -t supe .

# Run
docker run -it supe status
docker run -v $(pwd):/workspace -w /workspace supe prove "pytest"

# With Docker Compose
docker-compose up -d
docker exec -it supe supe prove "echo hello"
```

## Project Structure

```
supe/
├── ab/           # AB Memory Engine (storage, search, agents)
├── tasc/         # Task management (CLI, TUI, atoms)
├── tascer/       # Validation framework
│   ├── llm_proof.py      # LLM proof-of-work system
│   ├── proofs/           # Proof generators
│   ├── gates/            # Validation gates
│   ├── primitives/       # Observation primitives
│   └── overlord/         # Decision loop
├── supe/         # Unified CLI
├── scripts/      # Install/uninstall scripts
├── tests/        # Test suite
└── docs/         # Documentation
```

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Build docs
uv pip install -e ".[docs]"
mkdocs serve
```

## Cloud Deployment

See [docs/cloud-deployment.md](docs/cloud-deployment.md) for:
- Docker and Kubernetes configs
- Claude agent integration
- MCP server setup

## License

MIT
