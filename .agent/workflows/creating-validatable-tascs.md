---
description: How to create automatically validatable Tascs for experiments, coding problems, and workflows
---

# Creating Validatable Tascs

The key to automatic validation: `testing_instructions` must be a command that **exits 0 on success, non-zero on failure**.

---

## The Golden Rule

```python
{
    "id": "task_1",
    "title": "What you're doing",
    "testing_instructions": "command that exits 0 on success",
}
```

---

## Validation Patterns

| Goal | testing_instructions |
|------|---------------------|
| File exists | `test -f output.txt` |
| File contains text | `grep -q "SUCCESS" output.txt` |
| Python assertion | `python -c "assert condition"` |
| JSON value check | `python -c "import json; exit(0 if json.load(open('f.json'))['key'] > val else 1)"` |
| Compare outputs | `diff output.txt expected.txt` |
| Test suite passes | `pytest tests/` |
| Lint passes | `ruff check .` |
| Build succeeds | `docker build -t app .` |
| Script runs | `python script.py && echo done` |

---

## Example: Coding Problem

```python
from tascer import create_plan, execute_plan

plan = create_plan(
    title="Solve FizzBuzz",
    tascs=[
        {
            "id": "implement",
            "title": "Implement FizzBuzz",
            "testing_instructions": "python -c \"from solution import fizzbuzz; assert fizzbuzz(15) == 'FizzBuzz'\"",
            "desired_outcome": "Function returns correct values",
        },
        {
            "id": "full_test",
            "title": "Run test suite",
            "testing_instructions": "pytest tests/test_fizzbuzz.py -v",
            "dependencies": ["implement"],
        },
    ]
)

# Agent writes solution.py, then validates:
report = execute_plan(plan)
print(f"Verified: {report.verified}")
```

---

## Example: ML Experiment

```python
plan = create_plan(
    title="Train and Evaluate Model",
    tascs=[
        {
            "id": "train",
            "title": "Train model",
            "testing_instructions": "python train.py --output model.pkl && test -f model.pkl",
        },
        {
            "id": "accuracy",
            "title": "Check accuracy > 90%",
            "testing_instructions": "python -c \"import json; acc = json.load(open('results.json'))['accuracy']; exit(0 if acc > 0.9 else 1)\"",
            "dependencies": ["train"],
        },
    ]
)
```

---

## Example: Build Pipeline

```python
plan = create_plan(
    title="CI Pipeline",
    tascs=[
        {"id": "lint", "title": "Lint", "testing_instructions": "ruff check ."},
        {"id": "test", "title": "Test", "testing_instructions": "pytest", "dependencies": ["lint"]},
        {"id": "build", "title": "Build", "testing_instructions": "docker build -t app .", "dependencies": ["test"]},
    ]
)
```

---

## Example: Advent of Code

```python
plan = create_plan(
    title="AoC Day 1",
    tascs=[
        {
            "id": "part1",
            "title": "Solve Part 1",
            "testing_instructions": "python solution.py < input.txt | head -1 | diff - <(echo '12345')",
        },
        {
            "id": "part2", 
            "title": "Solve Part 2",
            "testing_instructions": "python solution.py < input.txt | tail -1 | diff - <(echo '67890')",
            "dependencies": ["part1"],
        },
    ]
)
```

---

## Headless Agent Workflow

For Claude Code or other AI agents operating autonomously:

```python
from tascer import create_plan, execute_plan, save_plan

# 1. Define the task with validation
plan = create_plan(
    title="Agent Task",
    tascs=[
        {
            "id": "implement",
            "title": "Write solution",
            "testing_instructions": "pytest tests/ -v",
        },
    ]
)

# 2. Agent does its work (writes code, etc.)
# ... 

# 3. Self-validate
report = execute_plan(plan)

if report.verified:
    print(f"✅ Validated! Proof: {report.overall_proof_hash}")
else:
    # Inspect failures
    for tasc in plan.tascs:
        val = plan.validations.get(tasc.id)
        if val and not val.validated:
            print(f"❌ {tasc.id}: exit_code={val.exit_code}")
            for gate in val.gate_results:
                if not gate.passed:
                    print(f"   Failed gate: {gate.gate_name}: {gate.message}")
```

---

## Advanced: Custom Proof Types

```python
{
    "id": "task",
    "title": "Run tests",
    "testing_instructions": "pytest tests/ -v",
    "proof_required": {
        "proof_type": "test",      # "script", "test", "lint"
        "criteria": {
            "expected_exit_codes": [0],
        },
        "timeout_seconds": 300,
        "max_retries": 3,
    },
}
```

---

## Tips for Agents

1. **Be specific**: `pytest tests/test_foo.py::test_bar` not just `pytest`
2. **Check outputs**: Use `&& test -f output.txt` to verify files created
3. **Use assertions**: `python -c "assert ..."` for quick checks
4. **Chain commands**: `cmd1 && cmd2` ensures both succeed
5. **Diff for comparison**: `diff actual.txt expected.txt` for exact matching
6. **Capture errors**: Check `validation.error_message` on failure

---

## Quick Start Template

```python
from tascer import create_plan, execute_plan

plan = create_plan(
    title="YOUR_TASK_TITLE",
    tascs=[
        {
            "id": "step_1",
            "title": "First step",
            "testing_instructions": "YOUR_VALIDATION_COMMAND",
        },
        {
            "id": "step_2",
            "title": "Second step", 
            "testing_instructions": "YOUR_VALIDATION_COMMAND",
            "dependencies": ["step_1"],
        },
    ]
)

report = execute_plan(plan)
assert report.verified, f"Failed: {report.failed_tasks} tasks"
print(f"Proof hash: {report.overall_proof_hash}")
```
