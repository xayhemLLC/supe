---
description: How to debug issues systematically
---

# Debug Mode Workflow

Systematic approach to debugging when something goes wrong.

---

## Phase 1: Identify the Error

1. **Reproduce the error**
```bash
# Run the failing command/test
pytest tests/test_failing.py -v
```

2. **Capture the error**
- Stack trace
- Error message
- Exit code
- Relevant logs

3. **Classify the error type**
| Type | Indicators |
|------|------------|
| Syntax | `SyntaxError`, parse failure |
| Import | `ModuleNotFoundError`, `ImportError` |
| Runtime | `TypeError`, `ValueError`, `AttributeError` |
| Logic | Wrong output, assertion failure |
| Integration | API errors, connection failures |

---

## Phase 2: Locate the Source

4. **Parse the stack trace**
- Identify the file and line number
- Note the call chain

5. **Read the source file**
```python
# READ_FILE action
path: "src/module.py"
range: { startLine: 40, endLine: 60 }
```

6. **Read related files**
- Imports
- Called functions
- Test file

---

## Phase 3: Form Hypothesis

7. **State your hypothesis clearly**
```
Hypothesis: The error occurs because X is None when it should be a list,
which happens when the API returns an empty response.
```

8. **Identify what to verify**
- Check if X is indeed None
- Check API response format
- Check error handling

---

## Phase 4: Add Debug Instrumentation

9. **Option A: Add logging**
```python
import logging
logging.debug(f"Value of X: {X}")
```

10. **Option B: Write a minimal test**
```python
def test_debug_hypothesis():
    result = function_under_test(edge_case_input)
    assert result is not None
```

11. **Option C: Interactive debugging**
```python
import pdb; pdb.set_trace()
```

---

## Phase 5: Execute and Observe

// turbo
12. Run with debug instrumentation:
```bash
pytest tests/test_debug.py -v -s
```

13. **Compare observation to hypothesis**
- Confirmed? → Proceed to fix
- Refuted? → Form new hypothesis, go to Phase 3

---

## Phase 6: Fix the Bug

14. **Apply minimal fix**
```python
# EDIT_FILE action
- Use diff format
- Change only what's necessary
- Add appropriate error handling
```

15. **Verify the fix**
```bash
pytest tests/ -v
```

---

## Phase 7: Clean Up

16. **Remove debug code**
- Remove print statements
- Remove pdb traces
- Keep useful tests

17. **Run full test suite**
```bash
pytest tests/ -v
```

18. **FINISH with summary**
```json
{
  "type": "FINISH",
  "summary": "Fixed null pointer in login handler by adding None check",
  "risks": ["Edge case for empty response still needs more tests"],
  "followUps": ["Add integration test for empty API response"]
}
```

---

## Debug Checklist

- [ ] Error reproduced
- [ ] Stack trace captured
- [ ] Source file located
- [ ] Hypothesis formed
- [ ] Debug instrumentation added
- [ ] Observation matches hypothesis
- [ ] Minimal fix applied
- [ ] Tests pass
- [ ] Debug code removed
- [ ] Full suite green

---

## Common Patterns

| Error | Likely Cause | First Check |
|-------|--------------|-------------|
| `None` errors | Missing return, empty response | Check function returns |
| Import errors | Missing dependency, circular import | Check imports, requirements |
| Type errors | Wrong argument type | Check function signatures |
| Key errors | Missing dict key | Check data structure |
| Assertion errors | Logic bug | Check test expectations vs implementation |
