# Hacker News Post

## Title
Show HN: Supe – Proof-of-work audit trails for AI agents

## URL
https://github.com/xayhemLLC/supe

## Text (for Show HN)

I built Supe because I kept running into the same problem: AI agents do things, but there's no good way to validate what they're doing or audit what they did.

**The core idea:**

1. **Validation gates** - Python functions that run before/after every tool execution. Want to block `rm -rf`? Write a 10-line function. Want read-only mode? Another 10 lines.

2. **Proof-of-work** - Every execution gets a SHA256 hash of (tool + input + output + timestamp). Tamper with the audit log? The proofs won't verify.

3. **Recall** - All executions are stored with neural spreading activation for semantic search. Query "what did the agent do with player structs?" and get relevant results.

**Example gate:**

```python
@agent.register_gate("safe_commands")
def safe_commands(record, phase) -> GateResult:
    cmd = record.tool_input.get("command", "")
    if "rm -rf" in cmd:
        return GateResult("safe_commands", False, "BLOCKED")
    return GateResult("safe_commands", True, "OK")
```

**Real use case:** I use this for reverse engineering workflows where an AI agent can analyze game binaries with Ghidra/radare2 but can't modify game files.

**What it's not:** This isn't about making agents "safe" in the alignment sense. It's about practical validation for specific use cases and audit trails for compliance.

343 tests, MIT licensed, works with Claude SDK (OpenAI wrapper coming).

Would love feedback on the gate pattern design and the recall API.

---

# Alternative Titles (pick based on what resonates)

1. Show HN: Supe – Proof-of-work audit trails for AI agents
2. Show HN: Supe – Validation gates and audit trails for AI agents
3. Show HN: The missing audit layer for AI agents
4. Show HN: Supe – Make your AI agent prove what it did

# Timing

Best times to post on HN:
- Weekday mornings 9-11am EST (6-8am PST)
- Tuesday, Wednesday, Thursday are best
- Avoid weekends and Monday mornings
