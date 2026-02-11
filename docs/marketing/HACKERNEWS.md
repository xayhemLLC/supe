# Hacker News

## Show HN: Supe - Cognitive architecture for AI agents (neural memory, validation gates, proofs)

### Link
https://github.com/xayhemLLC/supe

### Text (for Show HN)

I built Supe because I wanted Claude to analyze game binaries but not modify them. The constraints grew into something more general: a cognitive architecture for AI agents.

**The problem:** Most agent frameworks treat memory as flat storage. Store a key, get a value. That's not how useful memory works.

**What Supe provides:**

1. **Neural Memory** - Hebbian learning ("fire together, wire together"). Cards connected by synaptic links that strengthen with co-activation and decay with disuse. Spreading activation for recall. Hubs emerge naturally.

2. **Validation Gates** - Python functions that run before/after tool executions. Block `rm -rf`, enforce read-only mode, whitelist commands. Code, not configuration.

3. **Proof-of-Work** - SHA256 hashes chain every execution. Tamper with logs and proofs won't verify.

4. **Cognitive Hierarchy** - Moments (sessions) → Cards (knowledge units) → Buffers (raw data). Not flat.

5. **Semantic Relations** - 7 typed connections: CAUSES, IMPLIES, CONTRADICTS, SUPPORTS, DEPENDS_ON, EQUALS, TRANSFORMS.

**Example gate:**
```python
@agent.register_gate("safe")
def safe(record, phase) -> GateResult:
    if "rm -rf" in record.tool_input.get("command", ""):
        return GateResult("safe", False, "BLOCKED")
    return GateResult("safe", True, "OK")
```

**Example neural recall:**
```python
neural.add_card(1, {"title": "OAuth"})
neural.add_card(2, {"title": "Login"})
neural.connect(1, 2)  # Hebbian learning
results = neural.recall("authentication")  # Spreading activation
```

343 tests. MIT license. Works with Claude SDK.

`pip install supe`

---

## Alternative Title Options

- Show HN: Supe - Give your AI agent a brain, not just memory
- Show HN: Supe - Neural memory + validation gates for AI agents (343 tests)
- Show HN: Supe - Cognitive architecture for Claude and other AI agents

---

## Timing

Best times to post on HN:
- Weekday mornings 9-11am EST (6-8am PST)
- Tuesday, Wednesday, Thursday are best
- Avoid weekends and Monday mornings

---

## Anticipated HN Questions & Answers

**Q: How is this different from LangChain memory?**

A: LangChain memory is flat key-value or vector storage. Supe has:
- Neural dynamics (Hebbian learning, spreading activation, decay)
- Validation gates (code, not config)
- Cryptographic proof chains
- 7 typed semantic relations
- Cognitive hierarchy (moments → cards → buffers)

LangChain is "store and retrieve." Supe is "learn and recall."

**Q: Why Python functions for gates instead of YAML/JSON config?**

A: Validation logic is often conditional and complex. "Block rm -rf unless the user is admin and the path matches /tmp/*" doesn't fit well in declarative config. Python functions give you full expressivity.

**Q: Is the neural memory actually useful or just a gimmick?**

A: It solves a real problem: finding relevant memories when you don't know the exact keywords. Traditional search requires knowing what to search for. Spreading activation finds conceptually related memories through learned associations.

Example: You query "authentication" and it finds cards about "login", "sessions", "OAuth" - not because they contain that word, but because they were co-activated during past work.

**Q: What's the performance overhead?**

A: Minimal. SQLite storage, in-memory neural graph. The bottleneck in any AI agent system is the LLM API call, not local memory operations.

**Q: Why SHA256 proofs instead of actual blockchain?**

A: Practicality. SHA256 chains are enough to detect tampering, simple to implement, and don't require external infrastructure. We're not solving Byzantine consensus - we're creating audit logs that can't be quietly modified.

**Q: How does this compare to MemGPT?**

A: Different focus. MemGPT handles context window management (moving things in/out of context). Supe handles:
- Validation (blocking dangerous operations)
- Audit trails (proving what happened)
- Cognitive storage (learning associations)
- Semantic relations (understanding connections)

They could potentially complement each other.

**Q: Does it work with OpenAI/Anthropic/local models?**

A: Currently wraps Claude SDK. OpenAI wrapper planned. The core components (AB Memory, Neural Memory, Relations) are model-agnostic.

---

## Technical Details to Mention if Asked

- SQLite for persistence (no external deps)
- NumPy for vector operations (semantic search)
- 343 tests with pytest
- Async support throughout
- Type hints on everything
- Python 3.10+

---

## Comparison Table (if useful)

| Feature | LangChain | AutoGPT | MemGPT | Supe |
|---------|-----------|---------|--------|------|
| Pre-validation | No | No | No | Yes |
| Post-validation | No | No | No | Yes |
| Proof-of-work | No | No | No | Yes |
| Neural recall | No | No | No | Yes |
| Hebbian learning | No | No | No | Yes |
| Semantic relations | No | No | No | Yes (7 types) |
| Cognitive hierarchy | No | No | Partial | Yes |
| Custom gates | No | No | No | Yes (code) |
