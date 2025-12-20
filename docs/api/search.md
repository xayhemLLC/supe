# Search & Recall API Reference

Functions for finding and retrieving cards from memory.

## Keyword Search

### search_cards

Search cards by keyword or label.

```python
from ab import search_cards

# Search by keyword (searches buffer payloads)
results = search_cards(memory, keyword="Python")

# Search by label
results = search_cards(memory, label="conversation")

# Combined
results = search_cards(memory, keyword="hello", label="greeting")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `memory` | `ABMemory` | Memory instance |
| `keyword` | `str` | Text to search in payloads |
| `label` | `str` | Filter by card label |
| `owner_self` | `str` | Filter by owner |
| `limit` | `int` | Max results (default: 100) |

**Returns:** List of `Card` objects

---

## Semantic Search

### semantic_search

Find cards by semantic similarity to a query.

```python
from ab import semantic_search

results = semantic_search(
    memory,
    query="artificial intelligence and machine learning",
    top_k=10,
    label_filter="document"
)

for card, score in results:
    print(f"Score {score:.3f}: {card.label}")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `memory` | `ABMemory` | Memory instance |
| `query` | `str` | Search query text |
| `top_k` | `int` | Number of results (default: 10) |
| `label_filter` | `str` | Optional label filter |
| `buffer_name` | `str` | Specific buffer to search |

**Returns:** List of `(Card, score)` tuples, sorted by similarity

### embed_text

Create a bag-of-words embedding for text.

```python
from ab import embed_text

embedding = embed_text("hello world hello")
# {'hello': 0.894, 'world': 0.447}
```

### cosine_similarity

Calculate similarity between two embeddings.

```python
from ab import cosine_similarity, embed_text

vec1 = embed_text("machine learning")
vec2 = embed_text("artificial intelligence")
score = cosine_similarity(vec1, vec2)
```

---

## Recall with Memory Physics

### recall_cards

Search with memory strength integration.

```python
from ab.recall import recall_cards

results = recall_cards(
    memory,
    query="Python",
    top_k=5,
    use_card_stats=True  # Factor in memory strength
)
```

When `use_card_stats=True`:
- Stronger memories rank higher
- Each recalled card has its strength increased

---

## RFS Recall (Multi-Hop Traversal)

### rfs_recall

Traverse connections to find related cards.

```python
from ab import rfs_recall

results = rfs_recall(
    memory,
    start_card_id=1,
    max_hops=3,
    max_results=20,
    strengthen_path=True
)

for card, score, path in results:
    print(f"Card {card.id}: score={score:.3f}, path={path}")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `memory` | `ABMemory` | Memory instance |
| `start_card_id` | `int` | Starting card |
| `max_hops` | `int` | Maximum traversal depth |
| `max_results` | `int` | Limit results |
| `strengthen_path` | `bool` | Strengthen connections on path |

**Returns:** List of `(Card, score, path)` tuples

### attention_jump

Find directly connected cards.

```python
from ab import attention_jump

# Outgoing connections
connections = attention_jump(memory, card_id=1, direction="outgoing")

for target_id, relation, strength in connections:
    print(f"-> {target_id} ({relation})")
```

### get_connection_graph

Build a connection graph around a card.

```python
from ab import get_connection_graph

graph = get_connection_graph(memory, center_id=1, depth=2)
# {1: [(2, 'refs'), (3, 'uses')], 2: [(4, 'extends')], ...}
```

---

## Example: Finding Related Context

```python
from ab import ABMemory, semantic_search, rfs_recall

memory = ABMemory("knowledge.sqlite")

# Start with semantic search
results = semantic_search(memory, "web frameworks", top_k=3)

# For top result, find connected knowledge
if results:
    top_card, score = results[0]
    
    # Traverse connections
    related = rfs_recall(
        memory,
        start_card_id=top_card.id,
        max_hops=2,
        strengthen_path=True
    )
    
    print(f"Found {len(related)} related cards")
```
