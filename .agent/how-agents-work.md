# How AI Agent Systems Work Internally

Reference document for understanding agent decision-making, action selection, and validation.

---

## Core Loop

1. **Understand** the goal/user intent
2. **Plan** an approach
3. **Choose** the next best step
4. **Execute** the action
5. **Observe** the new state
6. **Re-plan** if needed
7. **Stop** when success criteria satisfied

---

## Action Categories

| Action | Purpose |
|--------|---------|
| `READ_FILE` | Read file content |
| `SEARCH` | Search codebase for symbols/patterns |
| `EDIT_FILE` | Apply diff patch |
| `RUN_TESTS` | Run test suite |
| `RUN_CMD` | Run shell command |
| `ASK_USER` | Request clarification |
| `FINISH` | Complete task |

---

## How Agents Choose Actions

### 1. Intent Parsing
Convert vague instructions into structured tasks:
- Problem classification (bug, feature, refactor)
- Affected subsystem
- Required actions
- Success definition

### 2. World-State Modeling
Maintain internal model:
- File tree
- Dependency graph
- Test map
- Error logs
- Hypothesis candidates

### 3. Planning Strategies

**ReAct (Reasoning + Acting):**
```
Thought: To solve X, I must do Y
Action: READ_FILE src/auth.py
Observation: [file contents]
Thought: The bug is in line 42
Action: EDIT_FILE src/auth.py
```

**Scoring:**
Each action gets scored on:
- Relevance (does this help?)
- Impact (how much progress?)
- Confidence
- Risk (chance of breaking things)
- Cost (time/tokens)

Pick maximum-utility action.

---

## Multi-Agent Pattern (Planner → Executor → Critic)

### Planner
- Converts goal to concrete plan
- Chooses files to touch
- Defines success conditions

### Executor
- Does actual editing/commands
- Sticks to planned steps
- Runs validations after edits

### Critic
- Reviews diffs and test results
- Checks invariants
- Verdicts: `ACCEPT`, `REVISE`, `ROLLBACK`, `ASK_USER`

---

## Surgical Coding Principles

1. **Shrink action surface** — restricted, explicit toolbox
2. **Always plan before acting** — no blind tool calls
3. **Diffs only** — never wholesale rewrites
4. **Validation first-class** — post-conditions on every action
5. **Sandbox the world** — git branch per run, container execution
6. **Teach to ask** — reward uncertainty over hallucination
7. **Narrow context** — curated views, not brain-dump
8. **Multi-eye workflow** — planner/executor/critic separation
9. **Domain checklists** — invariants per domain
10. **Explicit stop** — clear stopping conditions

---

## Knowing When to Stop

Agents stop when:
- Success criteria satisfied
- No progress being made
- Uncertainty too high
- Error loops detected
- User approval required
- Max step threshold reached

---

## Example Agent Run

**Goal:** "Fix the login bug"

```
1. READ_FILE → recent commits
2. READ_FILE → login component
3. RUN_CMD → run app to reproduce
4. Observe → stack trace
5. SEARCH → trace dependency
6. Form hypothesis
7. EDIT_FILE → patch code
8. RUN_TESTS → validate
9. Confirm success
10. FINISH
```

Every step: proposed → evaluated → chosen deliberately.

---

## Key Insight

AI agents don't "guess what to do."

They:
- **plan**
- **reason**
- **simulate**
- **score actions**
- **execute**
- **observe**
- **adapt**
- **validate**
- **stop**

They operate like **junior engineers trained on billions of examples**, not autocomplete engines.
