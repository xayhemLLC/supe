---
description: How LLMs generate validatable TascPlans from natural language goals
---

# LLM Plan Generation Workflow

How AI agents generate executable, validatable plans using Claude (Anthropic API).

**Claude is the recommended LLM for plan generation** due to its strong reasoning capabilities and long context window.

---

## The Process

```
Goal (natural language) → Analyze Context → Decompose → Create TascPlan → Request Approval → Execute
```

---

## Quick Start with Claude

The simplest way to generate a plan:

```python
from tascer import generate_plan

# Set ANTHROPIC_API_KEY environment variable
plan_result = generate_plan(
    goal="Fix the 500 error on the login endpoint",
    context="FastAPI app with JWT authentication",
    constraints=["Must maintain backwards compatibility"],
)

print(f"Plan: {plan_result.plan.title}")
print(f"Confidence: {plan_result.confidence:.0%}")

for tasc in plan_result.plan.tascs:
    print(f"  - {tasc.title}")
```

**Requirements:**
- Install: `pip install anthropic`
- Set `ANTHROPIC_API_KEY` environment variable
- Claude handles all the prompt engineering and parsing automatically

---

## Step 1: Receive Goal

The agent receives a natural language goal:
```
"Fix the 500 error on the login endpoint"
"Add dark mode to the settings page"
"Refactor the auth module to use JWT"
```

---

## Step 2: Analyze Context

Before planning, gather context:

```python
from tascer.actions import ActionExecutor, ActionType

executor = ActionExecutor(session_id="plan_001", tasc_id="analyze")

# Read relevant files
result = executor.execute(ActionType.READ_FILE, {"path": "src/auth.py"})

# Search for related code
result = executor.execute(ActionType.SEARCH_CODEBASE, {"query": "login endpoint"})

# Check test structure
result = executor.execute(ActionType.SEARCH_CODEBASE, {"query": "def test_login"})
```

---

## Step 3: Decompose into Tascs

Break the goal into validatable steps. Each Tasc needs:

| Field | Description |
|-------|-------------|
| `id` | Unique identifier |
| `title` | Human-readable description |
| `testing_instructions` | Command that exits 0 on success |
| `dependencies` | List of prerequisite tasc IDs |

**Key Rule**: Every `testing_instructions` must be executable and deterministic.

---

## Step 4: Create TascPlan

```python
from tascer import create_plan, ProofType

plan = create_plan(
    title="Fix Login 500 Error",
    tascs=[
        {
            "id": "locate",
            "title": "Locate the error source",
            "testing_instructions": "grep -q 'login' src/auth.py && echo found",
            "desired_outcome": "Identify file and line causing 500",
        },
        {
            "id": "fix",
            "title": "Apply fix",
            "testing_instructions": "python -c 'import src.auth'",  # Syntax check
            "dependencies": ["locate"],
        },
        {
            "id": "review",
            "title": "Human review of changes",
            "testing_instructions": "",
            "proof_required": {"proof_type": "manual"},  # Human approval gate
            "dependencies": ["fix"],
        },
        {
            "id": "test",
            "title": "Run test suite",
            "testing_instructions": "pytest tests/test_auth.py -v",
            "dependencies": ["review"],
        },
    ]
)
```

---

## Step 5: Request Plan Approval

Before executing, request human approval on the plan:

```python
from tascer import request_approval

approval = request_approval(
    tasc_id="plan_approval",
    title=f"Approve plan: {plan.title}",
    description=f"Plan has {len(plan.tascs)} tascs: {[t.title for t in plan.tascs]}",
    action_type="plan_approval",
    context={"plan_id": plan.id, "tascs": [t.id for t in plan.tascs]},
)

# Wait for approval via CLI: supe approve yes <id>
```

---

## Step 6: Execute with Validation

```python
from tascer import execute_plan

report = execute_plan(plan)

if report.verified:
    print(f"✅ All tascs validated! Proof: {report.overall_proof_hash}")
else:
    print(f"❌ {report.failed_tasks} tascs failed")
    for tasc in plan.tascs:
        val = plan.validations.get(tasc.id)
        if val and not val.validated:
            print(f"  - {tasc.id}: exit_code={val.exit_code}")
```

---

## Prompt Template for LLMs

When generating plans, LLMs should use this prompt pattern:

```
You are creating a TascPlan for the following goal:

Goal: {goal}

Codebase Context:
{context_summary}

Requirements:
1. Each tasc must have executable testing_instructions
2. testing_instructions must exit 0 on success, non-zero on failure
3. Use dependencies to enforce order
4. Add proof_type: "manual" for risky operations

Output JSON:
{
  "title": "...",
  "tascs": [
    {
      "id": "tasc_1",
      "title": "...",
      "testing_instructions": "command that validates this step",
      "dependencies": []
    }
  ]
}
```

---

## Validation Patterns Reference

| Goal | testing_instructions |
|------|---------------------|
| File exists | `test -f path/to/file` |
| Module imports | `python -c "import module"` |
| Tests pass | `pytest tests/` |
| Type check | `mypy src/` |
| Lint passes | `ruff check .` |
| Output matches | `command \| diff - expected.txt` |
| JSON field check | `python -c "import json; assert json.load(...)['key'] == value"` |

---

## Example: Complete Flow

```python
# 1. Goal arrives
goal = "Add pagination to the API list endpoint"

# 2. Analyze
# (agent reads files, searches, understands current implementation)

# 3. Generate plan
plan = create_plan(
    title=goal,
    tascs=[
        {"id": "model", "title": "Add pagination params", 
         "testing_instructions": "python -c 'from api.models import PaginationParams'"},
        {"id": "endpoint", "title": "Update endpoint",
         "testing_instructions": "python -c 'from api.routes import list_items'",
         "dependencies": ["model"]},
        {"id": "test", "title": "Test pagination",
         "testing_instructions": "pytest tests/test_pagination.py -v",
         "dependencies": ["endpoint"]},
    ]
)

# 4. Request approval
# (via supe approve CLI)

# 5. Execute
report = execute_plan(plan)

# 6. Report
print(f"Proof hash: {report.overall_proof_hash}")
```
