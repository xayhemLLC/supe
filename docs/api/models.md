# Models API Reference

Data classes representing core AB entities.

## Buffer

A named data buffer attached to a card.

```python
from ab import Buffer

buffer = Buffer(
    name="content",
    payload=b"Hello, world!",
    headers={"type": "text", "encoding": "utf-8"},
    exe="strip|lower_text"  # Optional transform chain
)
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Buffer identifier |
| `payload` | `bytes` | Raw binary data |
| `headers` | `Dict[str, Any]` | Metadata key-value pairs |
| `exe` | `Optional[str]` | Transform chain to apply |

---

## Card

A collection of buffers with a label.

```python
from ab import Card, Buffer

card = Card(
    id=1,
    label="conversation",
    buffers=[Buffer(name="data", payload=b"...", headers={})],
    moment_id=1,
    owner_self="planner",
    master_input="User said hello",
    master_output="AI responded"
)
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `Optional[int]` | Database ID (set after storage) |
| `label` | `str` | Classification label |
| `buffers` | `List[Buffer]` | Attached buffers |
| `moment_id` | `Optional[int]` | Associated moment |
| `owner_self` | `Optional[str]` | Owner agent name |
| `master_input` | `Optional[str]` | Input summary |
| `master_output` | `Optional[str]` | Output summary |

---

## Moment

A point in time in the memory timeline.

```python
from ab import Moment

moment = Moment(
    id=1,
    timestamp="2024-01-15T10:30:00.000000",
    master_input="User query",
    master_output="AI response"
)
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `Optional[int]` | Database ID |
| `timestamp` | `str` | ISO format timestamp |
| `master_input` | `Optional[str]` | Input for this moment |
| `master_output` | `Optional[str]` | Output for this moment |

---

## CardStats

Memory physics statistics for a card.

```python
from ab import CardStats

stats = CardStats(
    card_id=1,
    strength=2.5,
    recall_count=3,
    last_recalled="2024-01-15T10:30:00.000000"
)
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `card_id` | `int` | Associated card ID |
| `strength` | `float` | Current memory strength (default: 1.0) |
| `recall_count` | `int` | Number of times recalled |
| `last_recalled` | `Optional[str]` | Timestamp of last recall |

### Memory Physics Formula

When a card is recalled:
```
new_strength = old_strength * 0.9 + 1.0
recall_count += 1
```

When decay is applied:
```
new_strength = old_strength * decay_factor
```

---

## Usage Examples

### Creating a Conversation Card

```python
from ab import ABMemory, Buffer

memory = ABMemory(":memory:")

card = memory.store_card(
    label="conversation",
    buffers=[
        Buffer(
            name="user_message",
            payload=b"Hello, how are you?",
            headers={"role": "user"}
        ),
        Buffer(
            name="ai_response",
            payload=b"I'm doing well, thank you!",
            headers={"role": "assistant"}
        ),
    ]
)
```

### Accessing Buffer Data

```python
card = memory.get_card(1)

for buffer in card.buffers:
    print(f"Buffer: {buffer.name}")
    print(f"  Payload: {buffer.payload.decode()}")
    print(f"  Headers: {buffer.headers}")
```

### Checking Memory Strength

```python
stats = memory.get_card_stats(card.id)

if stats.strength < 0.5:
    print("Memory is fading!")
elif stats.strength > 3.0:
    print("Strong memory!")
```
