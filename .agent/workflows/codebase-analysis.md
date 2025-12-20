---
description: How an agent should analyze a new codebase from scratch
---

# Codebase Analysis Workflow

When encountering a new or unfamiliar codebase, follow this workflow to build understanding.

---

## Phase 1: Structure Discovery

// turbo
1. Get project structure:
```bash
find . -type f -name "*.py" -o -name "*.ts" -o -name "*.js" | head -50
```

// turbo
2. List top-level directories:
```bash
ls -la
```

3. Read key configuration files:
- `README.md`
- `package.json` / `pyproject.toml` / `Cargo.toml`
- `.gitignore`
- `Dockerfile` / `docker-compose.yml`

---

## Phase 2: Entry Point Identification

4. Identify main entry points:
- Look for `main.py`, `index.ts`, `app.py`, `server.py`
- Check `scripts` section in package.json
- Look for CLI definitions

5. Map the module structure:
- Core business logic
- API/routes
- Models/data
- Utils/helpers
- Tests

---

## Phase 3: Dependency Understanding

6. Analyze imports/dependencies:
```bash
# Python
grep -r "^from\|^import" --include="*.py" | head -30

# TypeScript/JS
grep -r "^import\|require(" --include="*.ts" --include="*.js" | head -30
```

7. Identify external dependencies:
- Check requirements.txt / package.json
- Note major frameworks (FastAPI, React, etc.)

---

## Phase 4: Test Structure

8. Locate tests:
```bash
find . -name "test_*.py" -o -name "*.test.ts" -o -name "*.spec.js"
```

9. Understand test patterns:
- Unit tests
- Integration tests
- E2E tests

---

## Phase 5: Store in Memory

10. Save findings to AB Memory:
```python
from ab.abdb import ABMemory
from ab.models import Buffer

mem = ABMemory("tasc.sqlite")
moment = mem.create_moment(
    master_input="Codebase analysis",
    master_output="Structure understood"
)

mem.store_card(
    label="codebase_structure",
    buffers=[
        Buffer(name="project", payload="project_name"),
        Buffer(name="language", payload="python"),
        Buffer(name="framework", payload="FastAPI"),
        Buffer(name="entry_points", payload="supe/cli.py, supe/mcp_server.py"),
        Buffer(name="test_pattern", payload="pytest tests/"),
    ],
    owner_self="CodeAnalyzer",
    moment_id=moment.id
)
```

---

## Quick Reference

| Question | How to Find |
|----------|-------------|
| What language? | Check file extensions, config files |
| What framework? | Check dependencies |
| Where's main? | Look for entry points in config |
| How to run? | Check README, scripts |
| How to test? | Look for test directories |
| What's the architecture? | Map directory structure |

---

## Output

After analysis, you should know:
- [ ] Primary language(s)
- [ ] Framework(s) used
- [ ] Entry point(s)
- [ ] How to run/build
- [ ] How to test
- [ ] Key modules and their purpose
