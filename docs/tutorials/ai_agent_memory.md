# Tutorial: AI Agent Memory System

Build a persistent memory system for AI agents that remembers conversations,
retrieves relevant context, and learns from interactions.

## Overview

AI agents often struggle with:

- **Limited context windows** - Can't see entire conversation history
- **No long-term memory** - Forget previous interactions
- **Context relevance** - Hard to find relevant past information

AB solves these problems by providing a structured memory system with
strength-based recall and semantic search.

## Use Case

We'll build a memory system for a coding assistant that:

1. Stores conversation turns
2. Remembers code snippets and explanations
3. Recalls relevant context for new questions
4. Strengthens useful memories over time

## Implementation

### Step 1: Set Up Memory

```python
from ab import ABMemory, Buffer
from ab.debug import DebugPrinter

# Create persistent memory
memory = ABMemory("ai_agent_memory.sqlite")
printer = DebugPrinter()
```

### Step 2: Store Conversations

```python
def store_conversation_turn(
    memory: ABMemory,
    user_message: str,
    ai_response: str,
    topic: str = "general",
    code_snippets: list[str] = None
) -> int:
    """Store a conversation turn as a card."""
    
    buffers = [
        Buffer(
            name="user_message",
            payload=user_message.encode(),
            headers={"role": "user"}
        ),
        Buffer(
            name="ai_response",
            payload=ai_response.encode(),
            headers={"role": "assistant"}
        ),
        Buffer(
            name="topic",
            payload=topic.encode(),
            headers={}
        ),
    ]
    
    # Store code snippets if any
    if code_snippets:
        for i, snippet in enumerate(code_snippets):
            buffers.append(Buffer(
                name=f"code_{i}",
                payload=snippet.encode(),
                headers={"type": "code"}
            ))
    
    card = memory.store_card(label="conversation", buffers=buffers)
    return card.id

# Example usage
turn_id = store_conversation_turn(
    memory,
    user_message="How do I read a file in Python?",
    ai_response="Use the open() function with a context manager...",
    topic="python",
    code_snippets=[
        'with open("file.txt", "r") as f:\n    content = f.read()'
    ]
)
```

### Step 3: Recall Relevant Context

```python
from ab import semantic_search, recall_cards

def get_relevant_context(
    memory: ABMemory,
    current_question: str,
    max_results: int = 5
) -> list[dict]:
    """Find relevant past conversations for context."""
    
    # Semantic search for similar conversations
    results = semantic_search(
        memory,
        current_question,
        top_k=max_results,
        label_filter="conversation"
    )
    
    context = []
    for card, score in results:
        # Strengthen memories we're recalling
        memory.recall_card(card.id)
        
        # Extract conversation data
        turn = {"score": score, "card_id": card.id}
        for buf in card.buffers:
            if buf.name in ["user_message", "ai_response", "topic"]:
                turn[buf.name] = buf.payload.decode()
            elif buf.name.startswith("code_"):
                turn.setdefault("code_snippets", []).append(buf.payload.decode())
        
        context.append(turn)
    
    return context

# Example: Get context for a new question
question = "How do I write to a file in Python?"
context = get_relevant_context(memory, question)

for turn in context:
    print(f"Score: {turn['score']:.3f}")
    print(f"User: {turn['user_message'][:50]}...")
    print(f"Topic: {turn.get('topic', 'unknown')}")
    print()
```

### Step 4: Build Context Window

```python
def build_context_prompt(
    memory: ABMemory,
    current_question: str,
    max_context_turns: int = 3
) -> str:
    """Build a context-aware prompt for the AI."""
    
    context = get_relevant_context(memory, current_question, max_context_turns)
    
    prompt_parts = ["Here are some relevant past conversations:\n"]
    
    for turn in context:
        prompt_parts.append(f"---")
        prompt_parts.append(f"User: {turn['user_message']}")
        prompt_parts.append(f"Assistant: {turn['ai_response']}")
        if turn.get('code_snippets'):
            prompt_parts.append(f"Code: {turn['code_snippets'][0]}")
    
    prompt_parts.append(f"\n---\nNow answer this question: {current_question}")
    
    return "\n".join(prompt_parts)
```

### Step 5: Connect Related Conversations

```python
def link_related_conversations(
    memory: ABMemory,
    card_id: int,
    related_card_id: int,
    relation: str = "relates_to"
) -> None:
    """Create a connection between related conversations."""
    memory.create_connection(
        source_card_id=card_id,
        target_card_id=related_card_id,
        relation=relation,
        strength=1.5
    )

# Link follow-up questions
link_related_conversations(memory, turn_id, previous_turn_id, "follows_up")
```

### Step 6: Navigate Conversation Chains

```python
from ab import rfs_recall

def get_conversation_chain(
    memory: ABMemory,
    start_card_id: int,
    max_depth: int = 5
) -> list[dict]:
    """Get a chain of related conversations."""
    
    results = rfs_recall(
        memory,
        start_card_id,
        max_hops=max_depth,
        max_results=10,
        strengthen_path=True  # Strengthen as we traverse
    )
    
    chain = []
    for card, score, path in results:
        if card.label == "conversation":
            chain.append({
                "card_id": card.id,
                "score": score,
                "path": path,
                "preview": card.buffers[0].payload.decode()[:50] + "..."
            })
    
    return chain
```

## Debugging

Use the debug tools to inspect memory state:

```python
from ab.debug import MemoryInspector, visualize_card

inspector = MemoryInspector(memory)
inspector.summary()

# Visualize a specific card
card = memory.get_card(turn_id)
print(visualize_card(card))
```

Output:
```
┌────────────────────────────────────────────────────────┐
│ Card #1: conversation                                  │
├────────────────────────────────────────────────────────┤
│ ◀ INPUTS                                               │
│ ├── user_message (35B)                                 │
│ ├── ai_response (52B)                                  │
│ ├── topic (6B)                                         │
│ └── code_0 (48B)                                       │
├────────────────────────────────────────────────────────┤
│ master_input: (none)                                   │
│ master_output: (none)                                  │
└────────────────────────────────────────────────────────┘
```

## Memory Decay

Over time, unused memories fade. Keep important memories strong:

```python
from ab import decay_formula, apply_decay_to_all

# Simulate decay (run periodically)
memory.apply_decay(decay_factor=0.95)

# Check which memories are getting weak
stale_cards = get_stale_cards(memory, threshold=0.5)
for stats in stale_cards:
    print(f"Card {stats.card_id} strength: {stats.strength:.2f}")
```

## Full Example

See the complete implementation in:
`drivers/demo_ai_agent_memory.py`

## Next Steps

- [Image Recall Tutorial](image_recall.md) - Store and search images
- [Knowledge Graph Tutorial](knowledge_graph.md) - Build connected knowledge
