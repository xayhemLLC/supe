# Twitter/X Thread

---

## Tweet 1 (Hook)

Your AI agent just mass-deleted files.

Can you prove it wasn't supposed to?

I built Supe - a cognitive brain for AI agents.

Not just memory. Neural learning + validation gates + cryptographic proofs.

343 tests, pip installable, MIT license.

Here's what makes it different:

---

## Tweet 2 (Problem)

The problem with AI agents:

- No pre-execution validation
- No audit trails
- No persistent memory
- No way to prove what happened
- No understanding of relationships

Most frameworks just... let agents do things. Then hope for the best.

---

## Tweet 3 (Neural Memory)

Supe has *neural* memory, not flat storage.

"Cells that fire together wire together"

```python
neural = NeuralMemory()
neural.add_card(1, {"title": "OAuth"})
neural.add_card(2, {"title": "Login"})
neural.connect(1, 2)  # Hebbian learning

results = neural.recall("authentication")
# Spreading activation through network
```

Connections strengthen with use. Hubs emerge. Like a brain.

---

## Tweet 4 (Validation Gates)

Gates = Python functions that validate tool execution.

```python
@agent.register_gate("safe")
def safe(record, phase):
    if "rm -rf" in record.tool_input["command"]:
        return GateResult("safe", False, "BLOCKED")
    return GateResult("safe", True, "OK")
```

10 lines. No DSL. No config files.

Block dangerous commands. Enforce read-only. Whitelist operations.

---

## Tweet 5 (Proofs)

Every execution gets a SHA256 proof.

Tool + Input + Output + Timestamp to Hash

Tamper with the logs? Proofs won't verify.

```python
assert agent.verify_proofs()
agent.export_report("audit.json")
```

Compliance teams love this.

---

## Tweet 6 (Cognitive Hierarchy)

Not flat key-value storage. A cognitive hierarchy:

Moments to Sessions
  Cards to Knowledge units
    Buffers to Raw data

```python
moment = ab.create_moment(master_input="Analysis session")
card = ab.store_card(
    label="analysis:player_struct",
    buffers=[Buffer(name="def", payload=b"struct Player")],
)
```

---

## Tweet 7 (Relations)

Knowledge has relationships. Supe captures them:

7 relation types:
- CAUSES
- IMPLIES
- CONTRADICTS
- SUPPORTS
- DEPENDS_ON
- EQUALS
- TRANSFORMS

```python
Relation.create("r1", RelationType.SUPPORTS, card1.id, card2.id)
```

---

## Tweet 8 (Task Management)

Task management with 14 evidence types:
- TEST
- PEER_REVIEW
- SECURITY_SCAN
- ...

7 domain categories auto-inferred:
- DEBUGGING
- SECURITY
- REFACTORING
- ...

```python
domain = infer_domain_from_title("Fix security vulnerability")
# TaskDomain.SECURITY
```

---

## Tweet 9 (Use Case)

Real use case: Reverse engineering workflow

Agent analyzes game binaries with Ghidra/radare2.
Agent can NOT modify game files.

```python
@agent.register_gate("whitelist")
def whitelist(record, phase):
    allowed = ["ghidra", "strings", "objdump"]
    cmd = record.tool_input["command"]
    if any(cmd.startswith(a) for a in allowed):
        return GateResult("whitelist", True, "OK")
    return GateResult("whitelist", False, "BLOCKED")
```

---

## Tweet 10 (CTA)

pip install supe

GitHub: github.com/xayhemLLC/supe

What you get:
- 343 tests passing
- MIT license
- Neural memory with Hebbian learning
- Validation gates (code, not config)
- Cryptographic proof chains
- 7 semantic relation types
- 14 evidence types
- Claude SDK integration

---

## Shorter Thread (5 tweets)

### Tweet 1
AI agents are powerful but terrifying.

No validation. No audit trails. No understanding of relationships.

I built Supe - a cognitive brain for AI agents.

Not just memory. Neural learning + validation + cryptographic proofs.

### Tweet 2
**Neural Memory**: Hebbian learning. "Fire together, wire together."

Connections strengthen with use. Hubs emerge. Spreading activation for recall.

```python
neural.connect(card1, card2)  # Repeated use = stronger link
results = neural.recall("authentication")  # Spreads through network
```

### Tweet 3
**Validation Gates**: Python functions, not config files.

Block rm -rf? 10 lines.
Whitelist commands? 10 lines.
Read-only mode? 10 lines.

**Proofs**: SHA256 of every execution. Tamper = invalid chain.

### Tweet 4
**7 Relation Types**: CAUSES, IMPLIES, CONTRADICTS, SUPPORTS, DEPENDS_ON, EQUALS, TRANSFORMS

**Cognitive Hierarchy**: Moments to Cards to Buffers

**14 Evidence Types**: TEST, PEER_REVIEW, SECURITY_SCAN...

### Tweet 5
pip install supe

343 tests | MIT license | Claude SDK integration

GitHub: github.com/xayhemLLC/supe

---

## Hashtags (use sparingly)

#AI #AIAgents #Python #OpenSource #MachineLearning #Claude #Anthropic #CognitiveAI
