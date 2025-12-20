# Supe System Overview for AI Agents

Welcome! This document provides everything you need to understand and work with the Supe system.

## Quick Reference

| Module | Purpose | Key File |
|--------|---------|----------|
| **supe** | Unified CLI | `supe/cli.py` |
| **ab** | AB Memory (persistent storage) | `ab/abdb.py` |
| **tasc** | Task management (Tasc objects) | `tasc/tasc.py` |
| **tascer** | Validation & proof-of-work | `tascer/llm_proof.py` |

---

## Core Concepts

### 1. Tasc
A **Tasc** is a structured task with:
- `id`, `title`, `status`
- `testing_instructions` — command to validate
- `desired_outcome` — expected result
- `dependencies` — list of tasc IDs

```python
from tasc.tasc import Tasc

tasc = Tasc(
    id="tasc_1",
    status="pending",
    title="Run tests",
    testing_instructions="pytest tests/",
    desired_outcome="All tests pass",
    dependencies=[],
)
```

### 2. TascValidation
Validation result for a single Tasc:
- `tasc_id`, `validated`, `proof_hash`
- `gate_results` — list of GateResult
- `command_executed`, `exit_code`, `duration_ms`

```python
from tascer.contracts import TascValidation
```

### 3. TascPlan
Container for multiple Tascs with dependency ordering:
- `tascs` — List[Tasc]
- `validations` — Dict[str, TascValidation]

```python
from tascer.llm_proof import create_plan, execute_plan

plan = create_plan(
    title="My Plan",
    tascs=[
        {"id": "t1", "title": "Step 1", "testing_instructions": "echo hello"},
        {"id": "t2", "title": "Step 2", "testing_instructions": "echo done", "dependencies": ["t1"]},
    ]
)
report = execute_plan(plan)
print(report.verified)  # True if all validated
```

---

## Key Functions

### Proof-of-Work

```python
from tascer import validate_tasc, prove_task, create_plan, execute_plan

# Validate a single Tasc
validation = validate_tasc(tasc, plan)

# Execute entire plan in dependency order
report = execute_plan(plan)
```

### AB Memory

```python
from ab.abdb import ABMemory
from ab.models import Buffer

mem = ABMemory("tasc.sqlite")

# Create a moment (timeline tick)
moment = mem.create_moment(master_input="User action", master_output="Result")

# Store a card with buffers
card = mem.store_card(
    label="tasc",
    buffers=[Buffer(name="title", payload="My work")],
    owner_self="Agent",
    moment_id=moment.id,
)

# Recall cards
cards = mem.recall(query="work", limit=10)
```

---

## CLI Commands

```bash
# System status
supe status

# Execute with proof
supe prove pytest tests/

# Save work
supe tasc save "auth fix" --type bug

# Create plan from markdown
supe plan create design.md --name "Feature"

# Run with safety checks
supe run "npm test"
```

---

## Project Structure

```
supe/
├── ab/           # AB Memory Engine
│   ├── abdb.py        # Main ABMemory class
│   └── models.py      # Buffer, Card, Moment
├── tasc/         # Task management
│   ├── tasc.py        # Tasc class
│   └── cli.py         # tasc CLI
├── tascer/       # Validation framework
│   ├── llm_proof.py   # TascPlan, create_plan, execute_plan
│   ├── contracts.py   # TascValidation, GateResult
│   ├── proofs/        # prove_llm_task, prove_script_success
│   ├── gates/         # ExitCodeGate, PatternGate
│   └── primitives/    # run_and_observe, capture_context
├── supe/         # Unified CLI
│   ├── cli.py         # Main CLI
│   └── mcp_server.py  # MCP server for AI assistants
├── tests/        # Test suite
└── docs/         # Documentation
```

---

## MCP Server (for Cursor/Claude)

The MCP server exposes supe tools to AI assistants:

```bash
supe mcp-server
```

Available tools:
- `supe_prove` — execute with proof
- `supe_verify` — verify a proof
- `supe_plan_create` — create a plan
- `supe_plan_execute` — execute a plan
- `supe_tasc_save` — save work to memory
- `supe_run_safe` — run with safety checks

---

## Important Files

| File | Description |
|------|-------------|
| `tascer/llm_proof.py` | TascPlan, validate_tasc, execute_plan |
| `tascer/contracts.py` | TascValidation, GateResult, Context |
| `tasc/tasc.py` | Base Tasc class |
| `ab/abdb.py` | ABMemory storage engine |
| `supe/cli.py` | Unified supe CLI |
| `supe/mcp_server.py` | MCP server for AI integration |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run tascer tests only
pytest tests/test_tascer*.py -v

# Quick import test
python -c "from tascer import create_plan, execute_plan; print('OK')"
```
