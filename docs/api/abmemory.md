# ABMemory API Reference

The `ABMemory` class is the primary interface for all storage operations.

## Class: ABMemory

```python
from ab import ABMemory

memory = ABMemory("my_database.sqlite")
# or in-memory:
memory = ABMemory(":memory:")
```

### Constructor

```python
ABMemory(db_path: str = ":memory:")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `db_path` | `str` | Path to SQLite database file, or `:memory:` for in-memory |

---

## Moments

### create_moment

Create a new moment (a point in time).

```python
moment = memory.create_moment(
    master_input="User asked a question",
    master_output="AI responded with answer"
)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `master_input` | `str` | No | Input text for this moment |
| `master_output` | `str` | No | Output text for this moment |

**Returns:** `Moment` object

### get_moment

```python
moment = memory.get_moment(moment_id=1)
```

---

## Cards

### store_card

Store a new card with buffers.

```python
from ab import Buffer

card = memory.store_card(
    label="conversation",
    buffers=[
        Buffer(name="input", payload=b"Hello", headers={"type": "text"}),
        Buffer(name="output", payload=b"Hi there!", headers={}),
    ],
    moment_id=1,
    owner_self="planner"
)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `label` | `str` | Yes | Classification label for the card |
| `buffers` | `List[Buffer]` | Yes | List of Buffer objects |
| `moment_id` | `int` | No | Associated moment ID |
| `owner_self` | `str` | No | Owner self identifier |
| `master_input` | `str` | No | Master input text |
| `master_output` | `str` | No | Master output text |

**Returns:** `Card` object with populated `id`

### get_card

```python
card = memory.get_card(card_id=1)
```

**Returns:** `Card` object with buffers populated

### update_card_buffers

Replace all buffers on a card.

```python
memory.update_card_buffers(card_id=1, buffers=[...])
```

---

## Card Stats (Memory Physics)

### get_card_stats

Get or initialize statistics for a card.

```python
stats = memory.get_card_stats(card_id=1)
print(stats.strength)      # 1.0
print(stats.recall_count)  # 0
```

**Returns:** `CardStats` object

### recall_card

Record a recall event, strengthening the memory.

```python
stats = memory.recall_card(card_id=1)
print(stats.strength)      # 1.9 (increased)
print(stats.recall_count)  # 1
```

**Returns:** Updated `CardStats` object

### apply_decay

Reduce strength of all cards by a decay factor.

```python
memory.apply_decay(decay_factor=0.95)
```

### list_cards_by_strength

Get cards ordered by memory strength.

```python
top_memories = memory.list_cards_by_strength(limit=10)
```

**Returns:** List of `CardStats` objects, sorted by strength descending

---

## Connections

### create_connection

Create a relationship between two cards.

```python
memory.create_connection(
    source_card_id=1,
    target_card_id=2,
    relation="references",
    strength=1.5
)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_card_id` | `int` | Yes | ID of source card |
| `target_card_id` | `int` | Yes | ID of target card |
| `relation` | `str` | Yes | Relationship type label |
| `strength` | `float` | No | Connection strength (default: 1.0) |

### list_connections

Get connections for a card.

```python
connections = memory.list_connections(card_id=1)
for conn in connections:
    print(f"{conn['source_card_id']} -> {conn['target_card_id']}: {conn['relation']}")
```

**Returns:** List of connection dictionaries

---

## Selves (Agents)

### create_self

Create a new self (agent).

```python
self_id = memory.create_self(
    name="planner",
    role="planning",
    subscribed_buffers=["prompt", "context"]
)
```

### get_self

```python
self_data = memory.get_self(self_id=1)
```

**Returns:** Dictionary with self properties

### list_selves

```python
selves = memory.list_selves()
```

---

## Subscriptions

### create_subscription

Subscribe a card to updates from another card's buffer.

```python
sub_id = memory.create_subscription(
    subscriber_card_id=1,
    source_card_id=2,
    buffer_name="output"
)
```

---

## Utility Methods

### close

Close the database connection.

```python
memory.close()
```

---

## Example: Complete Workflow

```python
from ab import ABMemory, Buffer

# Initialize
memory = ABMemory("example.sqlite")

# Create a moment
moment = memory.create_moment(master_input="User query")

# Store a card
card = memory.store_card(
    label="qa",
    buffers=[
        Buffer(name="question", payload=b"What is Python?", headers={}),
        Buffer(name="answer", payload=b"A programming language", headers={}),
    ],
    moment_id=moment.id
)

# Recall it (strengthens memory)
stats = memory.recall_card(card.id)
print(f"Card {card.id} strength: {stats.strength}")

# Create connections
card2 = memory.store_card(label="related", buffers=[...])
memory.create_connection(card.id, card2.id, "relates_to")

# Clean up
memory.close()
```
