---
description: How to run tests for the supe project
---

# Running Tests

// turbo-all

1. Activate the virtual environment:
```bash
source .venv/bin/activate
```

2. Run all tests:
```bash
pytest tests/ -v
```

3. Run specific test modules:
```bash
# Tascer tests only
pytest tests/test_tascer*.py -v

# Tasc roundtrip test
pytest tests/test_tasc_roundtrip.py -v

# AB Memory tests
pytest tests/test_ab_features.py -v
```

4. Run with coverage:
```bash
pytest tests/ --cov=tascer --cov=tasc --cov=ab -v
```
