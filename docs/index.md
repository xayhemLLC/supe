# AB / TASC Documentation

Welcome to the AB Memory Engine documentation!

## Overview

AB is a cognitive memory system that provides:

- **Structured Storage**: Moments, cards, and buffers for organized data
- **Memory Physics**: Strength-based recall with natural decay
- **Transforms**: Text processing pipelines for buffer payloads
- **Self Agents**: Cognitive agents with specialized behaviors
- **Semantic Search**: Find related information by meaning
- **Knowledge Graphs**: Connect and traverse related concepts

## Quick Start

```python
from ab import ABMemory, Buffer

# Create memory instance
memory = ABMemory("my_memory.sqlite")

# Store a card with buffers
card = memory.store_card(
    label="note",
    buffers=[
        Buffer(name="content", payload=b"Hello, world!", headers={})
    ]
)

# Recall strengthens the memory
memory.recall_card(card.id)
```

## Table of Contents

- [Installation](installation.md)
- [Core Concepts](concepts.md)
- [API Reference](api.md)
- [Tutorials](tutorials/index.md)
- [Benchmarks](benchmarks.md)
