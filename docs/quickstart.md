# Quick Start

Learn the basics of AB in 5 minutes!

## 1. Create a Memory Instance

```python
from ab import ABMemory, Buffer

# Persistent storage
memory = ABMemory("my_project.sqlite")

# Or in-memory for testing
memory = ABMemory(":memory:")
```

## 2. Store Cards with Buffers

Cards are the basic unit of storage. Each card has a label and multiple buffers.

```python
# Store a conversation
card = memory.store_card(
    label="conversation",
    buffers=[
        Buffer(name="user_input", payload=b"What is Python?", headers={"role": "user"}),
        Buffer(name="ai_response", payload=b"Python is a programming language.", headers={"role": "assistant"}),
    ]
)
print(f"Stored as card #{card.id}")
```

## 3. Recall and Strengthen Memories

Each recall strengthens the memory, making it more likely to be found later.

```python
# Recall a card (strengthens it)
stats = memory.recall_card(card.id)
print(f"Strength: {stats.strength:.2f}, Recalls: {stats.recall_count}")
```

## 4. Search for Information

```python
from ab import search_cards, semantic_search

# Keyword search
results = search_cards(memory, keyword="Python")
for card in results:
    print(f"Found: {card.label} (id={card.id})")

# Semantic search (by meaning)
results = semantic_search(memory, "programming languages", top_k=5)
for card, score in results:
    print(f"Score {score:.3f}: {card.label}")
```

## 5. Connect Related Cards

```python
# Create connections between cards
memory.create_connection(
    source_card_id=card1.id,
    target_card_id=card2.id,
    relation="relates_to",
    strength=1.5
)

# Traverse connections
from ab import rfs_recall
results = rfs_recall(memory, start_card_id=card1.id, max_hops=3)
```

## 6. Use Transforms

Process buffer payloads before use:

```python
from ab import apply_transform

text = b"  HELLO WORLD  "
result = apply_transform("strip|lower_text", text)
print(result)  # b'hello world'
```

## 7. Debug and Inspect

```python
from ab.debug import DebugPrinter, MemoryInspector

# Pretty print cards
printer = DebugPrinter()
printer.card(card)

# Inspect memory state
inspector = MemoryInspector(memory)
inspector.summary()
```

## Next Steps

- [Core Concepts](concepts/moments_cards.md) - Deep dive into the data model
- [Tutorials](tutorials/index.md) - Real-world use cases
- [API Reference](api/abmemory.md) - Complete API documentation
