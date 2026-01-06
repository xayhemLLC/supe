# Supe Learning System

A unified learning system for AI agents that supports both document-based learning (INGEST mode) and experimental validation (EXPLORE mode).

## Overview

The learning system uses a state machine architecture to process questions and build validated knowledge. It supports:

- **INGEST Mode**: Learn from documents, APIs, and existing knowledge
- **EXPLORE Mode**: Discover properties through experimentation and proof
- **Spaced Repetition**: Automatic review scheduling based on confidence
- **Proof of Work**: Cryptographic validation via Tascer integration
- **Evidence-Based**: All beliefs require citations and validation

## Quick Start

```python
import asyncio
from supe import Supe

async def main():
    # Initialize Supe
    supe = Supe(db_path="memory.db")

    # Learn from documentation (INGEST mode)
    result = await supe.learn(
        "How do Python decorators work?",
        mode="ingest"
    )

    print(f"Learned {result['beliefs_count']} beliefs")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Validated: {result['validated']}")

    # Discover mathematical properties (EXPLORE mode)
    result = await supe.learn(
        "Is addition commutative?",
        mode="explore"
    )

    print(f"Theorem proven: {result['validated']}")
    print(f"Proof hash: {result['proof_hash']}")

asyncio.run(main())
```

## Architecture

### State Machine Flow

```
INIT
  ↓
SELECT_FOCUS_QUESTION
  ↓
PLAN_EVIDENCE_STRATEGY
  ↓
┌─────────────────┬─────────────────┐
│   INGEST_DOC    │   EXPLORE_ENV   │
│ (documentation) │ (experiments)   │
└─────────────────┴─────────────────┘
  ↓
INTEGRATE_KNOWLEDGE
  ↓
SELF_TEST
  ↓
EVALUATE_AND_UPDATE_CONFIDENCE
  ↓
GENERATE_FOLLOWUP_QUESTIONS
  ↓
SCHEDULE_REVIEW
  ↓
IDLE_OR_TERMINATE
```

### Core Components

- **LearningStateMachine**: Orchestrates the learning workflow
- **Question**: Learning queries with types (CORE_CONCEPT, OPERATIONAL, etc.)
- **Evidence**: Citations with validation status
- **Belief**: Knowledge representation (CornellNote or Theorem)
- **LearningContext**: Session state and accumulated knowledge

## INGEST Mode

Learn from existing documentation and knowledge sources.

### Features

- Concept extraction from text and code
- Question generation (4 types: core, operational, constraint, impact)
- Cornell note synthesis (cue/notes/examples/summary)
- Evidence collection with citations

### Example: Learning from Documentation

```python
async def learn_from_docs():
    supe = Supe()

    # Store documentation in memory first
    supe.memory.store_card(
        label="documentation",
        master_input="React Hooks Documentation",
        master_output="""
        Hooks are functions that let you use state and other React features
        without writing a class. The most common hooks are useState and useEffect.

        useState returns a pair: the current state value and a function to update it.
        useEffect lets you perform side effects in function components.
        """,
        track="awareness",
    )

    # Learn from the documentation
    result = await supe.learn(
        "How do React hooks work?",
        mode="ingest"
    )

    # Examine beliefs
    for belief in result['beliefs']:
        if 'content' in belief:
            note = belief['content']
            print(f"Cue: {note.get('cue', 'N/A')}")
            print(f"Notes: {note.get('notes', 'N/A')}")
            print(f"Summary: {note.get('conceptual_summary', 'N/A')}")
            print(f"Confidence: {belief['confidence']:.2f}")
```

### Cornell Note Structure

```python
{
    "cue": "The question or prompt",
    "notes": "Detailed notes from sources",
    "examples": ["Code example 1", "Code example 2"],
    "conceptual_summary": "High-level understanding",
    "operational_summary": "How to use it"
}
```

## EXPLORE Mode

Discover properties through experimentation and formal proof.

### Features

- Mathematical claim parsing
- Experiment plan generation
- Property validation (commutative, associative, distributive, identity)
- Theorem synthesis with formal proofs
- Counterexample identification

### Example: Mathematical Discovery

```python
async def discover_math():
    supe = Supe()

    # Discover commutativity
    result = await supe.learn(
        "Is addition commutative?",
        mode="explore"
    )

    belief = result['beliefs'][0]
    theorem = belief['content']

    print(f"Statement: {theorem['statement']}")
    print(f"Status: {theorem['status']}")  # PROVEN, DISPROVEN, or CONJECTURE
    print(f"Proof: {theorem['proof']}")
    print(f"Properties: {theorem['properties_validated']}")
    print(f"Confidence: {belief['confidence']:.2f}")

asyncio.run(discover_math())
```

### Theorem Structure

```python
{
    "statement": "Addition is commutative",
    "proof": "Validated through 5/5 experiments...",
    "status": "PROVEN",  # or DISPROVEN, CONJECTURE
    "properties_validated": ["commutative"],
    "counterexample": None,  # or {"a": 5, "b": 3} if disproven
}
```

### Supported Properties

- **Commutative**: `a op b == b op a`
- **Associative**: `(a op b) op c == a op (b op c)`
- **Distributive**: `a op (b + c) == (a op b) + (a op c)`
- **Identity**: `a op e == a` (finds identity element)
- **Inverse**: `a op inv(a) == e` (finds inverse)

## Learning from First Principles

Starting from minimal axioms and building up knowledge.

### Example: Mathematical Discovery from Zero

```python
async def learn_math_from_scratch():
    """Learn mathematics starting from zero and nonzero."""
    supe = Supe()

    # Phase 1: Understand zero
    r1 = await supe.learn(
        "What happens when you add zero to a number?",
        mode="explore"
    )
    print(f"Zero property: {r1['beliefs'][0]['content']['statement']}")

    # Phase 2: Understand nonzero
    r2 = await supe.learn(
        "What happens when you add two nonzero numbers?",
        mode="explore"
    )

    # Phase 3: Discover commutativity
    r3 = await supe.learn(
        "Does the order of addition matter?",
        mode="explore"
    )

    # Phase 4: Discover associativity
    r4 = await supe.learn(
        "When adding three numbers, does grouping matter?",
        mode="explore"
    )

    # Phase 5: Build on discovered properties
    r5 = await supe.learn(
        "Is subtraction commutative?",
        mode="explore"
    )

    # Should discover that subtraction is NOT commutative
    theorem = r5['beliefs'][0]['content']
    print(f"Subtraction commutative: {theorem['status']}")  # DISPROVEN
    print(f"Counterexample: {theorem['counterexample']}")

asyncio.run(learn_math_from_scratch())
```

## Confidence Scoring

Beliefs receive confidence scores (0.0-1.0) based on:

- **Evidence Quality**:
  - Number of evidence items (1-5 optimal)
  - Source diversity (multiple sources better)
  - Validation status (validated evidence preferred)
  - Citation quality

- **Self-Test Performance**:
  - Recall quality without referring to sources
  - Applied as adjustment factor (0.7-1.1)

- **Gap Impact**:
  - Fewer gaps = higher confidence
  - Many gaps (>5) reduce confidence by 20%

- **Experiment Results** (EXPLORE mode):
  - All tests pass = 0.95 confidence (PROVEN)
  - Mixed results = proportional confidence (CONJECTURE)
  - Tests fail = 0.0 confidence (DISPROVEN)

## Spaced Repetition

Beliefs are automatically scheduled for review based on confidence:

| Confidence | Interval | Use Case |
|------------|----------|----------|
| < 0.5 | 1 day | Very low - immediate review |
| 0.5-0.6 | 2 days | Low - needs reinforcement |
| 0.6-0.7 | 3 days | Medium-low - regular review |
| 0.7-0.8 | 5 days | Medium - established knowledge |
| 0.8-0.9 | 7 days | High - well understood |
| 0.9-0.95 | 14 days | Very high - strong retention |
| > 0.95 | 30 days | Excellent - long-term memory |

## Proof of Work

Learning sessions generate cryptographic proofs via Tascer:

```python
result = await supe.learn("Question", mode="explore")

print(f"Validated: {result['validated']}")  # True if all gates passed
print(f"Proof hash: {result['proof_hash']}")  # SHA-256 hash

# Validation includes:
# - ConfidenceGate: confidence >= threshold
# - GapGate: gaps <= max allowed
# - ExperimentGate: pass rate >= threshold (EXPLORE mode)
```

## Advanced Usage

### Question Types

```python
from supe.learning.types import QuestionType

# CORE_CONCEPT: "What is X?"
# OPERATIONAL: "How do you use X?"
# CONSTRAINT: "When should you NOT use X?"
# IMPACT: "What happens if you change X?"
# MATH_STRUCTURE: "Does X have property Y?"
```

### Custom Learning Sessions

```python
from supe.learning import LearningStateMachine, Mode

async def custom_learning():
    memory = ABMemory("memory.db")
    sm = LearningStateMachine(memory, mode=Mode.EXPLORE, debug=True)

    # Initialize with question
    await sm.initialize("Is multiplication distributive over addition?")

    # Run state machine
    await sm.run(max_steps=50)

    # Get results
    beliefs = sm.get_beliefs()
    evidence = sm.get_evidence()
    summary = sm.get_summary()

    return {
        "beliefs": beliefs,
        "evidence": evidence,
        "summary": summary,
    }
```

### Accessing Stored Knowledge

```python
# Search for learned beliefs
cards = supe.memory.find_cards_by_label("learning_belief")

# Recall related knowledge
result = await supe.recall("React hooks")

# Get beliefs for a topic
from supe.learning.storage import load_beliefs
belief_ids = ["belief_id_1", "belief_id_2"]
beliefs = load_beliefs(supe.memory, belief_ids)
```

## Storage Schema

Learning artifacts are stored in AB Memory:

- **learning_context**: Session metadata and state
- **learning_question**: Questions with status tracking
- **learning_evidence**: Evidence with citations
- **learning_belief**: Beliefs (CornellNote or Theorem)
- **tasc_execution**: Validation proofs

All learning data persists across sessions and supports:
- Cross-session question queues
- Knowledge graph connections
- Spaced repetition scheduling
- Audit trails with proof hashes

## Testing

```bash
# Run all learning tests
pytest tests/test_learning*.py tests/test_supe_learning_integration.py -v

# Test INGEST mode only
pytest tests/test_learning_modes.py::test_process_ingest_content -v

# Test EXPLORE mode only
pytest tests/test_learning_modes.py::test_process_explore_question -v

# Test full state machine
pytest tests/test_learning_state_machine.py -v
```

## Performance

- **INGEST mode**: ~50-100ms per question (depends on memory search)
- **EXPLORE mode**: ~100-200ms per question (includes experiments)
- **State machine**: ~10-20 state transitions per learning session
- **Memory footprint**: ~1-5KB per belief (with evidence)

## Troubleshooting

### No beliefs created

```python
# Check if evidence was collected
result = await supe.learn("Question", mode="ingest")
print(f"Evidence: {result['evidence_count']}")

# If evidence_count is 0, no relevant content in memory
# Solution: Store source material first
```

### Low confidence scores

```python
# Check evidence quality and gaps
result = await supe.learn("Question")
print(f"Gaps: {result['gaps_count']}")

# Many gaps reduce confidence
# Solution: Learn prerequisite concepts first
```

### EXPLORE mode not finding properties

```python
# Check question phrasing
# Good: "Is addition commutative?"
# Bad: "Tell me about addition"

# Must be testable property question
```

## Examples Directory

See `examples/` for complete working examples:

- `examples/learn_react.py` - INGEST mode with documentation
- `examples/discover_math.py` - EXPLORE mode from first principles
- `examples/learn_curriculum.py` - Multi-topic learning sequence
- `examples/review_schedule.py` - Spaced repetition implementation
