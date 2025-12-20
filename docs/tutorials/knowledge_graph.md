# Tutorial: Knowledge Graph Building

Build a connected knowledge base that stores entities, relationships,
and enables traversal to find related concepts.

## Overview

Knowledge graphs power many AI systems:

- **Entity relationships** - Connect concepts together
- **Path finding** - Discover indirect connections
- **Context building** - Gather related information

AB's connection system provides the foundation for knowledge graphs.

## Use Case

We'll build a knowledge graph for a programming documentation system:

1. Store concepts (languages, frameworks, patterns)
2. Define relationships (uses, implements, extends)
3. Traverse to find related concepts
4. Build context from connected knowledge

## Implementation

### Step 1: Define Entity Types

```python
from ab import ABMemory, Buffer
from typing import Optional, List, Dict, Any

memory = ABMemory("knowledge_graph.sqlite")

def create_entity(
    memory: ABMemory,
    entity_type: str,
    name: str,
    description: str,
    properties: Dict[str, Any] = None
) -> int:
    """Create an entity in the knowledge graph."""
    
    import json
    
    buffers = [
        Buffer(name="name", payload=name.encode(), headers={}),
        Buffer(name="type", payload=entity_type.encode(), headers={}),
        Buffer(name="description", payload=description.encode(), headers={"type": "text"}),
    ]
    
    if properties:
        buffers.append(Buffer(
            name="properties",
            payload=json.dumps(properties).encode(),
            headers={"type": "json"}
        ))
    
    card = memory.store_card(label=f"entity:{entity_type}", buffers=buffers)
    return card.id

# Create programming concepts
python_id = create_entity(
    memory,
    "language",
    "Python",
    "High-level, interpreted programming language known for readability",
    {"paradigms": ["oop", "functional", "procedural"], "year": 1991}
)

django_id = create_entity(
    memory,
    "framework",
    "Django",
    "High-level Python web framework for rapid development",
    {"type": "web", "language": "python"}
)

flask_id = create_entity(
    memory,
    "framework",
    "Flask",
    "Lightweight WSGI web application framework",
    {"type": "web", "language": "python"}
)

ml_id = create_entity(
    memory,
    "concept",
    "Machine Learning",
    "Field of computer science using statistical techniques to learn from data",
    {"domains": ["ai", "data_science"]}
)
```

### Step 2: Create Relationships

```python
# Relationship types
RELATIONS = {
    "implements": "implements",
    "extends": "extends",
    "uses": "uses",
    "part_of": "part_of",
    "alternative_to": "alternative_to",
    "related_to": "related_to",
}

def create_relationship(
    memory: ABMemory,
    source_id: int,
    target_id: int,
    relation: str,
    strength: float = 1.0,
    bidirectional: bool = False
) -> None:
    """Create a relationship between entities."""
    
    memory.create_connection(source_id, target_id, relation, strength)
    
    if bidirectional:
        # Create reverse relationship
        reverse_relation = f"inverse_{relation}"
        memory.create_connection(target_id, source_id, reverse_relation, strength)

# Build relationships
create_relationship(memory, django_id, python_id, "uses", strength=2.0)
create_relationship(memory, flask_id, python_id, "uses", strength=2.0)
create_relationship(memory, flask_id, django_id, "alternative_to", bidirectional=True)
create_relationship(memory, python_id, ml_id, "used_for", strength=1.5)
```

### Step 3: Query the Graph

```python
def get_entity(memory: ABMemory, card_id: int) -> Dict[str, Any]:
    """Get entity details."""
    import json
    
    card = memory.get_card(card_id)
    entity = {"card_id": card_id}
    
    for buf in card.buffers:
        if buf.name == "properties":
            entity["properties"] = json.loads(buf.payload.decode())
        else:
            entity[buf.name] = buf.payload.decode()
    
    return entity

def find_entities_by_type(memory: ABMemory, entity_type: str) -> List[int]:
    """Find all entities of a given type."""
    from ab import search_cards
    
    results = search_cards(memory, label=f"entity:{entity_type}")
    return [card.id for card in results]

# Find all frameworks
frameworks = find_entities_by_type(memory, "framework")
for fw_id in frameworks:
    entity = get_entity(memory, fw_id)
    print(f"{entity['name']}: {entity['description'][:50]}...")
```

### Step 4: Traverse Relationships

```python
from ab import rfs_recall, attention_jump

def get_related_entities(
    memory: ABMemory,
    entity_id: int,
    relation: Optional[str] = None,
    direction: str = "both"
) -> List[Dict[str, Any]]:
    """Get directly connected entities."""
    
    connections = memory.list_connections(card_id=entity_id)
    
    related = []
    for conn in connections:
        # Filter by relation if specified
        if relation and conn["relation"] != relation:
            continue
        
        # Determine which end is the related entity
        if conn["source_card_id"] == entity_id and direction in ["both", "outgoing"]:
            other_id = conn["target_card_id"]
        elif conn["target_card_id"] == entity_id and direction in ["both", "incoming"]:
            other_id = conn["source_card_id"]
        else:
            continue
        
        related.append({
            "entity_id": other_id,
            "relation": conn["relation"],
            "strength": conn["strength"],
            **get_entity(memory, other_id)
        })
    
    return related

# Get entities that Python uses
uses = get_related_entities(memory, python_id, relation="used_for")
for entity in uses:
    print(f"Python is used for: {entity['name']}")
```

### Step 5: Multi-Hop Traversal

```python
def find_connected_knowledge(
    memory: ABMemory,
    start_id: int,
    max_hops: int = 3,
    max_results: int = 20
) -> List[Dict[str, Any]]:
    """Find all entities connected within N hops."""
    
    results = rfs_recall(
        memory,
        start_id,
        max_hops=max_hops,
        max_results=max_results,
        strengthen_path=True  # Strengthen paths we traverse
    )
    
    entities = []
    for card, score, path in results:
        if card.label.startswith("entity:"):
            entity = get_entity(memory, card.id)
            entity["score"] = score
            entity["path"] = path
            entities.append(entity)
    
    return entities

# Find everything connected to Python within 3 hops
connected = find_connected_knowledge(memory, python_id, max_hops=3)
for entity in connected:
    path_str = " -> ".join(map(str, entity["path"]))
    print(f"{entity['name']} (score: {entity['score']:.3f}) via {path_str}")
```

### Step 6: Build Context

```python
def build_knowledge_context(
    memory: ABMemory,
    query_entities: List[int],
    max_context_size: int = 10
) -> str:
    """Build a context string from knowledge graph entities."""
    
    all_related = []
    for entity_id in query_entities:
        # Get entity itself
        entity = get_entity(memory, entity_id)
        all_related.append(entity)
        
        # Get related entities
        related = find_connected_knowledge(memory, entity_id, max_hops=2)
        all_related.extend(related)
    
    # Deduplicate and sort by score
    seen = set()
    unique = []
    for e in all_related:
        if e["card_id"] not in seen:
            seen.add(e["card_id"])
            unique.append(e)
    
    # Sort by relevance
    unique.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    # Build context string
    context_parts = []
    for entity in unique[:max_context_size]:
        context_parts.append(f"- {entity['name']}: {entity['description']}")
    
    return "\n".join(context_parts)

# Build context about Python web development
context = build_knowledge_context(memory, [python_id, django_id])
print(context)
```

## Visualization

```python
from ab.debug import DebugPrinter, MemoryInspector

printer = DebugPrinter()
inspector = MemoryInspector(memory)

# View the graph around Python
inspector.graph(memory, python_id, depth=2)
```

Output:
```
─── Connection Graph (center=1, depth=2) ───
  ● Card #1 (entity:language)
      └─uses─▶ #4
      └─used_for─▶ #3
  ○ Card #2 (entity:framework)
      └─uses─▶ #1
      └─alternative_to─▶ #3
  ○ Card #3 (entity:framework)
      └─uses─▶ #1
```

## Advanced: Schema Validation

```python
# Define allowed relationships per entity type
SCHEMA = {
    "language": {
        "outgoing": ["used_for", "implements"],
        "incoming": ["uses"],
    },
    "framework": {
        "outgoing": ["uses", "extends", "alternative_to"],
        "incoming": ["alternative_to"],
    },
    "concept": {
        "outgoing": ["related_to", "part_of"],
        "incoming": ["used_for", "related_to"],
    },
}

def validate_relationship(
    memory: ABMemory,
    source_id: int,
    target_id: int,
    relation: str
) -> bool:
    """Check if a relationship is valid per schema."""
    
    source = get_entity(memory, source_id)
    target = get_entity(memory, target_id)
    
    source_type = source["type"]
    target_type = target["type"]
    
    if source_type in SCHEMA:
        allowed = SCHEMA[source_type].get("outgoing", [])
        if relation not in allowed:
            return False
    
    return True
```

## Full Example

```python
# Complete knowledge graph workflow
from ab import ABMemory, Buffer

memory = ABMemory("tech_knowledge.sqlite")

# 1. Create entities
entities = {}
entities["python"] = create_entity(memory, "language", "Python", "...")
entities["javascript"] = create_entity(memory, "language", "JavaScript", "...")
entities["react"] = create_entity(memory, "framework", "React", "...")
entities["django"] = create_entity(memory, "framework", "Django", "...")

# 2. Create relationships
create_relationship(memory, entities["react"], entities["javascript"], "uses")
create_relationship(memory, entities["django"], entities["python"], "uses")

# 3. Query
related = get_related_entities(memory, entities["python"])
context = build_knowledge_context(memory, [entities["python"]])

# 4. Visualize
inspector = MemoryInspector(memory)
inspector.summary()
```

## Next Steps

- [AI Agent Memory](ai_agent_memory.md) - Apply to AI systems
- [Image Recall](image_recall.md) - Handle binary data
