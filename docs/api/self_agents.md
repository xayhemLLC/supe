# Self Agents API Reference

Cognitive agents with specialized behaviors.

## Core Classes

### Self (Abstract Base)

Base class for all self agents.

```python
from ab import Self, Proposal

class MySelf(Self):
    name = "my_agent"
    role = "custom"
    
    def think(self, card):
        # Analyze card and return proposal
        return Proposal(
            suggestion="My recommendation",
            strength=1.5,
            metadata={"analyzed": True}
        )
```

### Proposal

Result of a self's think() method.

```python
from ab import Proposal

proposal = Proposal(
    suggestion="Take this action",
    strength=2.5,
    metadata={"confidence": "high", "steps": 3}
)
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `suggestion` | `str` | The proposed action/response |
| `strength` | `float` | Priority/confidence score |
| `metadata` | `Dict` | Additional context |

---

## Built-in Selves

### PlannerSelf

Strategic planning and task breakdown.

```python
from ab import PlannerSelf, Buffer

planner = PlannerSelf()

card = memory.store_card(
    label="awareness",
    buffers=[
        Buffer(name="prompt", payload=b"Plan user authentication", headers={}),
        Buffer(name="context", payload=b"Web app using React", headers={})
    ]
)

proposal = planner.think(card)
print(proposal.suggestion)  # Planning recommendations
print(proposal.strength)    # Priority score
```

### ArchitectSelf

System design and patterns.

```python
from ab import ArchitectSelf

architect = ArchitectSelf()
proposal = architect.think(card)
# Focuses on design patterns, architecture considerations
```

### ExecutorSelf

Action execution and task completion.

```python
from ab import ExecutorSelf

executor = ExecutorSelf()
proposal = executor.think(card)
# Detects action keywords, prioritizes execution
```

---

## Self Methods

### think(card) → Proposal

Analyze a card and produce a proposal.

```python
proposal = self.think(card)
```

### filter_buffers(card) → List[Buffer]

Get only subscribed buffers from a card.

```python
planner = PlannerSelf(subscribed_buffers=["prompt", "context"])

# Card has 4 buffers, but planner only sees 2
filtered = planner.filter_buffers(card)
```

### bind_memory(memory)

Bind a memory instance for recursive calls.

```python
planner = PlannerSelf()
planner.bind_memory(memory)
```

### call_subself(other_self, card) → Proposal

Delegate to another self.

```python
planner.bind_memory(memory)
executor = ExecutorSelf()

# Planner delegates to executor
result = planner.call_subself(executor, card)
```

---

## Self Registry

Manage multiple self agents.

```python
from ab import self_registry, PlannerSelf, ExecutorSelf

# Register selves
self_registry.register(PlannerSelf())
self_registry.register(ExecutorSelf())

# Get by name
planner = self_registry.get("planner")

# List all
names = self_registry.list_names()
```

---

## Database Integration

Selves can be stored in the database.

```python
# Create a self record
self_id = memory.create_self(
    name="planner",
    role="planning",
    subscribed_buffers=["prompt", "context", "files"]
)

# Retrieve
self_data = memory.get_self(self_id)
print(self_data["subscribed_buffers"])  # ['prompt', 'context', 'files']

# List all
selves = memory.list_selves()
```

---

## Custom Self Example

```python
from ab import Self, Proposal, Card

class ReviewerSelf(Self):
    """Reviews code and provides feedback."""
    
    name = "reviewer"
    role = "code_review"
    subscribed_buffers = ["code", "diff"]
    
    def think(self, card: Card) -> Proposal:
        # Get code buffer
        code_buf = None
        for buf in self.filter_buffers(card):
            if buf.name == "code":
                code_buf = buf
                break
        
        if not code_buf:
            return Proposal(
                suggestion="No code to review",
                strength=0.0
            )
        
        code = code_buf.payload.decode()
        
        # Simple analysis
        issues = []
        if "TODO" in code:
            issues.append("Contains TODO comments")
        if len(code) > 1000:
            issues.append("Consider splitting large file")
        
        return Proposal(
            suggestion=f"Found {len(issues)} issues: " + ", ".join(issues),
            strength=len(issues) * 0.5,
            metadata={"issues": issues, "code_length": len(code)}
        )

# Use it
reviewer = ReviewerSelf()
proposal = reviewer.think(card)
```

---

## Overlord Integration

Selves submit proposals to the Overlord for decision-making.

```python
from ab import Overlord, PlannerSelf, ExecutorSelf

overlord = Overlord(memory)

# Selves propose actions
for self_agent in [PlannerSelf(), ExecutorSelf()]:
    proposal = self_agent.think(card)
    overlord.add_proposal({
        "subself_id": self_agent.name,
        "action": proposal.suggestion,
        "priority": proposal.strength
    })

# Overlord decides
winner = overlord.decide()
print(f"Winner: {winner['subself_id']}")
```
