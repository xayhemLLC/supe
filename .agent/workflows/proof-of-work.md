---
description: How to use the proof-of-work system for task validation
---

# Proof-of-Work Workflow

## 1. Create a Plan

```python
from tascer import create_plan, execute_plan

plan = create_plan(
    title="Your Plan Title",
    tascs=[
        {
            "id": "tasc_1",
            "title": "First step",
            "testing_instructions": "echo 'step 1 done'",
            "desired_outcome": "Prints step 1 done",
        },
        {
            "id": "tasc_2",
            "title": "Second step",
            "testing_instructions": "echo 'step 2 done'",
            "dependencies": ["tasc_1"],
        },
    ]
)
```

## 2. Execute the Plan

```python
report = execute_plan(plan)

print(f"Verified: {report.verified}")
print(f"Proven: {report.proven_tasks}/{report.total_tasks}")
print(f"Proof hash: {report.overall_proof_hash}")
```

## 3. Access Validations

```python
for tasc in plan.tascs:
    validation = plan.validations.get(tasc.id)
    if validation:
        print(f"{tasc.id}: validated={validation.validated}, hash={validation.proof_hash}")
```

## 4. Save/Load Plans

```python
from tascer import save_plan, load_plan

# Save
save_plan(plan, ".tascer/plans/my_plan.json")

# Load
loaded_plan = load_plan(".tascer/plans/my_plan.json")
```

## CLI Usage

```bash
# Execute single command with proof
supe prove "pytest tests/"

# Verify existing proof
supe verify 20231219_120000_proof

# Check system status
supe status
```
