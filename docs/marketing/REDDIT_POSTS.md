# Reddit Posts

---

## r/MachineLearning

### Title
[P] Supe: Cognitive memory for AI agents - neural learning, validation gates, and proof-of-work audit trails

### Body

I've been working on a library to solve a practical problem with AI agents: how do you give them a brain, not just memory?

**Supe** adds five things to AI agent workflows:

1. **Neural Memory** - Not flat storage. Hebbian learning where "cells that fire together wire together." Spreading activation for recall. Connections strengthen with use. Hubs emerge. Like a real brain.

2. **Validation gates** - Python functions that run before/after tool executions. Block dangerous commands, enforce read-only mode, whitelist operations - all with simple functions that return `GateResult(name, passed, message)`.

3. **Proof-of-work** - SHA256 hashes of every execution for tamper-evident audit trails. If anyone modifies execution records, the proofs won't verify.

4. **Cognitive hierarchy** - Moments (sessions) → Cards (knowledge units) → Buffers (raw data). Not flat key-value storage.

5. **Semantic relations** - 7 typed relations (CAUSES, IMPLIES, CONTRADICTS, SUPPORTS, DEPENDS_ON, EQUALS, TRANSFORMS) that capture how knowledge connects.

**Key design decisions:**

Gates are code, not configuration:
```python
@agent.register_gate("safe_commands")
def safe_commands(record, phase) -> GateResult:
    if "rm -rf" in record.tool_input.get("command", ""):
        return GateResult("safe_commands", False, "BLOCKED")
    return GateResult("safe_commands", True, "OK")
```

Neural memory with biological dynamics:
```python
neural = NeuralMemory()
neural.add_card(1, {"title": "OAuth"})
neural.add_card(2, {"title": "Login"})
neural.connect(1, 2)  # Hebbian learning
results = neural.recall("authentication")  # Spreading activation
```

343 tests, MIT license, pip installable.

GitHub: https://github.com/xayhemLLC/supe

Would appreciate feedback on the approach, especially from anyone working on cognitive architectures or agent tooling.

---

## r/LocalLLaMA

### Title
Supe: Give your AI agent a brain, not just memory (neural learning + validation gates + proofs)

### Body

Built this for a reverse engineering workflow where I wanted Claude to analyze game binaries but NOT modify anything. Ended up building something more general.

**Supe** wraps AI agent SDKs with:

- **Neural Memory** - Hebbian learning. Cards connected by synaptic links that strengthen with co-activation. Spreading activation for recall. Hubs emerge for frequently accessed concepts.
- **Gates** - Block dangerous operations before they happen (Python functions, not config)
- **Proofs** - SHA256 audit trail for every execution
- **Recall** - Query past executions ("show me all Bash commands")
- **Relations** - 7 semantic types (CAUSES, SUPPORTS, CONTRADICTS, etc.)

**Example:** Read-only mode for RE

```python
@agent.register_gate("command_whitelist")
def command_whitelist(record, phase) -> GateResult:
    allowed = ["ghidra", "radare2", "strings", "objdump"]
    cmd = record.tool_input.get("command", "")
    if any(cmd.startswith(a) for a in allowed):
        return GateResult("command_whitelist", True, "OK")
    return GateResult("command_whitelist", False, f"BLOCKED: {cmd}")
```

**Neural memory in action:**
```python
neural = NeuralMemory()
neural.add_card(1, {"title": "Player Struct", "fields": ["health", "mana"]})
neural.add_card(2, {"title": "Network Protocol", "packets": ["MOVE", "ATTACK"]})
neural.connect(1, 2)  # Used together = wired together

# Later...
results = neural.recall("game structures")
# Spreading activation finds connected cards
```

Works with Claude SDK, planning OpenAI support.

- 343 tests
- MIT license
- `pip install supe`

GitHub: https://github.com/xayhemLLC/supe

---

## r/Python

### Title
Supe: Cognitive framework for AI agents with neural memory, validation gates, and proof-of-work

### Body

Sharing an open source library I built for giving AI agents a proper cognitive architecture.

**Problem:** AI agents (Claude, GPT, etc.) can execute tools, but there's no standard way to:
1. Block dangerous operations before they happen
2. Create audit trails of what was executed
3. Query past executions intelligently
4. Understand relationships between knowledge
5. Store memories with biological-like dynamics

**Solution:** Supe adds five cognitive capabilities:

**1. Neural Memory (Hebbian Learning)**
```python
from ab.neural_memory import NeuralMemory

neural = NeuralMemory()
neural.add_card(1, {"title": "OAuth Auth"})
neural.add_card(2, {"title": "Login Page"})

# Co-activation strengthens connections
neural.connect(1, 2)
neural.connect(1, 2)  # Repeated = stronger

# Query spreads activation through network
results = neural.recall("authentication login", top_k=5)
```

**2. Validation Gates (Code, Not Config)**
```python
from tascer.contracts import GateResult

@agent.register_gate("safe_commands")
def safe_commands(record, phase) -> GateResult:
    cmd = record.tool_input.get("command", "")
    dangerous = ["rm -rf", "DROP TABLE", "> /dev/sda"]

    if any(d in cmd for d in dangerous):
        return GateResult("safe_commands", False, f"BLOCKED: {cmd}")
    return GateResult("safe_commands", True, "OK")
```

**3. Cognitive Hierarchy**
```python
from ab import ABMemory, Buffer

ab = ABMemory(".tascer/memory.sqlite")
moment = ab.create_moment(master_input="RE session")
card = ab.store_card(
    label="analysis:player_struct",
    buffers=[
        Buffer(name="definition", payload=b"struct Player { int health; }"),
        Buffer(name="offsets", payload=b'{"health": "0x10"}'),
    ],
)
```

**4. Semantic Relations**
```python
from tasc.relations import Relation, RelationType

# 7 types: CAUSES, IMPLIES, CONTRADICTS, SUPPORTS, DEPENDS_ON, EQUALS, TRANSFORMS
Relation.create("r1", RelationType.SUPPORTS, card1.id, card2.id, confidence=0.9)
```

**5. Proof-of-Work Audit Trails**
```python
assert agent.verify_proofs()  # False if tampered
agent.export_report("audit.json")
```

**Tech:**
- Pure Python, minimal dependencies (click, rich, numpy)
- SQLite storage (via AB Memory engine)
- 343 tests, type hints throughout
- Python 3.10+

`pip install supe`

GitHub: https://github.com/xayhemLLC/supe

Would love feedback on the API design!

---

## r/ClaudeAI

### Title
Built a cognitive brain for Claude agents - neural memory, validation gates, proofs, semantic relations

### Body

I use Claude for reverse engineering workflows but needed more than guardrails. I needed Claude to have something like a brain.

**Supe** adds five capabilities:

**1. Neural Memory (not flat storage)**

Hebbian learning - "cells that fire together wire together"

```python
neural = NeuralMemory()
neural.add_card(1, {"title": "OAuth", "type": "feature"})
neural.add_card(2, {"title": "Login", "type": "feature"})
neural.connect(1, 2)  # Strengthens with each use

results = neural.recall("authentication")  # Spreading activation
```

Connections strengthen with use, weaken with disuse. Hubs emerge. Fundamental branches form.

**2. Validation gates** - Block operations before Claude executes them

```python
@agent.register_gate("no_writes")
def no_writes(record, phase) -> GateResult:
    if record.tool_name == "Write" and "/game/" in record.tool_input.get("file_path", ""):
        return GateResult("no_writes", False, "Cannot modify game files")
    return GateResult("no_writes", True, "OK")
```

**3. Proof-of-work** - Every tool execution gets a SHA256 proof

```python
agent.verify_proofs()  # Returns False if audit log was tampered
agent.export_report("audit.json")  # For compliance
```

**4. Semantic relations** - 7 typed connections

CAUSES, IMPLIES, CONTRADICTS, SUPPORTS, DEPENDS_ON, EQUALS, TRANSFORMS

```python
Relation.create("r1", RelationType.SUPPORTS, evidence_card.id, hypothesis_card.id)
```

**5. Task management** - 14 evidence types, 7 domain categories, auto-inference

```python
domain = infer_domain_from_title("Fix security vulnerability")
# TaskDomain.SECURITY
```

Works as a wrapper around Claude Agent SDK.

GitHub: https://github.com/xayhemLLC/supe
`pip install supe[anthropic]`

---

## r/artificial

### Title
Supe: A cognitive architecture for AI agents (neural memory, validation, proofs)

### Body

Most AI agent frameworks treat memory as flat storage. Store a string, retrieve a string. That's not how brains work.

I built **Supe** to give AI agents something closer to cognitive architecture:

**Neural Memory with Biological Dynamics**

- Hebbian learning: connections strengthen when co-activated
- Spreading activation: queries propagate through the network
- Long-term potentiation: frequently used paths become highways
- Synaptic depression: unused links decay over time
- Hub formation: central concepts emerge naturally

```python
neural = NeuralMemory()
# Add knowledge
neural.add_card(1, {"concept": "authentication"})
neural.add_card(2, {"concept": "login"})
neural.add_card(3, {"concept": "security"})

# Wire through use
neural.connect(1, 2)  # Auth often used with login
neural.connect(1, 3)  # Auth often used with security

# Recall spreads activation
results = neural.recall("login security")
# Returns cards ranked by activation level
```

**Plus practical features:**

- **Validation gates**: Python functions that approve/block operations
- **Proof-of-work**: SHA256 chains for tamper-evident audit logs
- **Semantic relations**: 7 typed connections (CAUSES, SUPPORTS, CONTRADICTS, etc.)
- **Cognitive hierarchy**: Moments → Cards → Buffers

343 tests. MIT license. pip installable.

GitHub: https://github.com/xayhemLLC/supe

Interested in feedback from anyone working on cognitive architectures or neurosymbolic systems.
