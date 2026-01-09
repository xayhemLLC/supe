# Supe Launch Checklist

## Pre-Launch (Done)

- [x] LICENSE file (MIT)
- [x] CONTRIBUTING.md
- [x] README with examples
- [x] pyproject.toml with URLs
- [x] .gitignore covers .tascer/, *.sqlite
- [x] No hardcoded secrets
- [x] Tests passing (54 tests)
- [x] Working demos
  - `scripts/demo_tascer_re_workflow.py` - RE workflow
  - `scripts/real_agent_test.py` - Real Claude API
  - `scripts/test_tascer_agent.py` - Integration test

## Launch Day

### 1. GitHub Repo Settings
- [ ] Add description: "Cognitive memory for AI agents with validation and proof-of-work"
- [ ] Add topics: `ai`, `agents`, `memory`, `validation`, `claude`, `anthropic`, `proof-of-work`
- [ ] Enable Issues
- [ ] Enable Discussions (optional)

### 2. Announce

**Twitter/X:**
```
Releasing Supe - cognitive memory for AI agents

TascerAgent wraps Claude SDK with:
- Validation gates (block dangerous ops)
- Proof-of-work (audit trails)
- Recall (query past executions)
- AB Memory (persistent storage)

54 tests, real Claude API integration tested

github.com/xayhemLLC/supe
```

**Hacker News (Show HN):**
```
Title: Show HN: Supe – Validation layer and memory for AI agents

Body:
I built Supe to solve a problem I kept running into: AI agents that can't remember what they did, and no way to validate their actions.

Key features:
- TascerAgent: Wraps Claude SDK with pre/post validation gates
- Custom gates: Block dangerous commands, enforce read-only mode, whitelist operations
- Proof-of-work: SHA256 hashes of every execution for audit trails
- Recall: Query past executions ("what structs did I find?", "show all Bash commands")
- AB Memory: Persistent storage with cards, buffers, and neural recall

Real-world use case: Reverse engineering workflow where the agent analyzes binaries but can't modify game files.

Demo: python scripts/demo_tascer_re_workflow.py

Would love feedback on the gate pattern and recall API design.
```

**Reddit (r/MachineLearning, r/LocalLLaMA):**
```
Title: Supe: Validation layer and cognitive memory for AI agents

[Same as HN body]
```

### 3. Optional Enhancements (Post-Launch)

- [ ] PyPI publish (`uv build && uv publish`)
- [ ] GitHub Actions CI
- [ ] Badges (CI status, coverage)
- [ ] Documentation site (mkdocs)
- [ ] Example integrations (LangChain, LlamaIndex)

## Key Selling Points

1. **Novel**: Proof-of-work for AI agent actions
2. **Practical**: Real Claude API integration tested and working
3. **Flexible**: Custom gates are just Python functions
4. **Auditable**: Every action has a verifiable proof hash
5. **Memorable**: Agents can query their own history

## Quick Stats for Launch

```
- 54 tests passing
- 4 core components (AB Memory, Tasc, Tascer, TascerAgent)
- 6 recall methods
- 3 built-in gates
- 3 demo scripts
- Real Claude API integration
```
