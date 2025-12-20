---
description: How to use AB Memory for storing and recalling cards
---

# AB Memory Workflow

## 1. Initialize Memory

```python
from ab.abdb import ABMemory
from ab.models import Buffer

mem = ABMemory("tasc.sqlite")  # or any .sqlite path
```

## 2. Create a Moment

Moments are timeline ticks that group cards together:

```python
moment = mem.create_moment(
    master_input="User asked about authentication",
    master_output="Explained JWT tokens"
)
```

## 3. Store Cards

Cards are memory units with buffers:

```python
card = mem.store_card(
    label="conversation",
    buffers=[
        Buffer(name="topic", payload="authentication"),
        Buffer(name="summary", payload="Discussed JWT implementation"),
    ],
    owner_self="Agent",
    moment_id=moment.id
)
```

## 4. Recall Cards

```python
# Search by query
results = mem.recall(query="authentication", limit=10)

for card in results:
    print(f"Card {card.id}: {card.label}")
    for buf in card.buffers:
        print(f"  {buf.name}: {buf.payload[:50]}...")
```

## 5. Memory Strength

Cards have strength that increases with recall:

```python
# Get card stats
stats = mem.get_card_stats(card.id)
print(f"Strength: {stats.strength}, Recalls: {stats.recall_count}")

# Apply decay to old memories
mem.apply_decay(decay_factor=0.95)
```

## CLI Usage

```bash
# Save current work
supe tasc save "auth module" --type feature

# List recent tascs
supe tasc list

# Search past work
supe tasc recall "login"
```
