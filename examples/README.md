# Supe Learning System Examples

Practical examples demonstrating the unified learning system.

## Quick Start

All examples can be run directly:

```bash
# Learn mathematics from first principles
python examples/discover_math_from_zero.py

# Learn React Hooks from documentation
python examples/learn_react_hooks.py

# Compare both modes
python examples/compare_modes.py
```

## Examples

### 1. Mathematical Discovery (EXPLORE Mode)

**File**: `discover_math_from_zero.py`

Demonstrates learning from first principles by starting with just two concepts:
- Zero (additive identity)
- Nonzero (everything else)

The system discovers:
- ✅ Addition is commutative (PROVEN with experiments)
- ✅ Addition is associative (PROVEN)
- ❌ Subtraction is NOT commutative (DISPROVEN with counterexample)
- ✅ Multiplication is associative (PROVEN)

**Output**: Complete proofs with confidence scores and cryptographic validation.

### 2. Documentation Learning (INGEST Mode)

**File**: `learn_react_hooks.py`

Demonstrates learning from documentation:
1. Stores React documentation in memory
2. Extracts key concepts
3. Creates Cornell-style notes
4. Identifies knowledge gaps
5. Schedules spaced repetition

**Output**: Structured notes with conceptual and operational summaries.

### 3. Mode Comparison

**File**: `compare_modes.py`

Side-by-side comparison of INGEST and EXPLORE modes showing:
- Different use cases
- Evidence types
- Confidence scoring
- Output formats

## Key Concepts Demonstrated

### EXPLORE Mode

- **Purpose**: Discover properties through experimentation
- **Input**: Testable questions ("Is X commutative?")
- **Process**: Generate experiments, run tests, synthesize theorems
- **Output**: Formal proofs with PROVEN/DISPROVEN/CONJECTURE status
- **Confidence**: Based on experiment pass rate
- **Use Cases**:
  - Mathematical property discovery
  - Algorithm behavior validation
  - System property testing
  - API contract verification

### INGEST Mode

- **Purpose**: Learn from existing documentation
- **Input**: General questions ("How does X work?")
- **Process**: Search memory, extract concepts, synthesize notes
- **Output**: Cornell notes with cue/notes/examples/summaries
- **Confidence**: Based on evidence quality and self-test
- **Use Cases**:
  - Learning from documentation
  - Understanding codebases
  - API usage patterns
  - Conceptual knowledge

## Running Examples

### Prerequisites

```bash
# Install Supe
pip install -e .

# Or use uv
uv pip install -e .
```

### Execute Examples

```bash
# Make executable (Unix/Mac)
chmod +x examples/*.py

# Run directly
./examples/discover_math_from_zero.py

# Or with python
python examples/discover_math_from_zero.py
```

### Custom Examples

Create your own:

```python
#!/usr/bin/env python3
import asyncio
from supe import Supe

async def main():
    supe = Supe(db_path=":memory:")

    # INGEST: Learn from docs
    result = await supe.learn(
        "What is Python's GIL?",
        mode="ingest"
    )
    print(f"Learned {result['beliefs_count']} beliefs")

    # EXPLORE: Test properties
    result = await supe.learn(
        "Is Python dict lookup O(1)?",
        mode="explore"
    )
    print(f"Proven: {result['validated']}")

asyncio.run(main())
```

## Output Interpretation

### Belief Structure

```python
{
    "id": "belief_abc123",
    "question_id": "question_xyz789",
    "confidence": 0.85,  # 0.0-1.0
    "mode": "INGEST",    # or "EXPLORE"
    "content": {
        # INGEST mode: CornellNote
        "cue": "Question prompt",
        "notes": "Detailed notes",
        "examples": ["Example 1", "Example 2"],
        "conceptual_summary": "High-level understanding",
        "operational_summary": "How to use it"

        # EXPLORE mode: Theorem
        "statement": "Property description",
        "proof": "Formal proof",
        "status": "PROVEN",  # or DISPROVEN, CONJECTURE
        "properties_validated": ["commutative"],
        "counterexample": None  # or dict if disproven
    }
}
```

### Confidence Scores

| Range | Meaning | Action |
|-------|---------|--------|
| 0.9-1.0 | Proven/Excellent | Review in 14-30 days |
| 0.8-0.9 | High confidence | Review in 7 days |
| 0.6-0.8 | Medium confidence | Review in 3-5 days |
| 0.4-0.6 | Low confidence | Review in 2 days |
| 0.0-0.4 | Very low/Disproven | Review tomorrow |

### Validation Status

- **validated: true**: All gates passed (confidence, gaps, experiments)
- **validated: false**: One or more gates failed
- **proof_hash**: Cryptographic proof (SHA-256)

## Advanced Usage

### Storing Source Material

```python
# Store documentation
supe.memory.store_card(
    label="documentation",
    master_input="React Hooks",
    master_output="Documentation text...",
    track="awareness",
)

# Store code examples
supe.memory.store_card(
    label="code_example",
    master_input="useState example",
    master_output="const [state, setState] = useState(0)",
    track="awareness",
)
```

### Accessing Results

```python
result = await supe.learn("Question", mode="ingest")

# Get beliefs
for belief in result['beliefs']:
    print(f"Confidence: {belief['confidence']}")
    print(f"Content: {belief['content']}")

# Get metadata
print(f"Session: {result['session_id']}")
print(f"Proof: {result['proof_hash']}")
print(f"Gaps: {result['gaps_count']}")
```

### Building Curricula

```python
# Sequential learning
topics = [
    ("What is a React component?", "ingest"),
    ("What are props?", "ingest"),
    ("What are hooks?", "ingest"),
    ("Is useState synchronous?", "explore"),
]

for question, mode in topics:
    result = await supe.learn(question, mode=mode)
    print(f"✓ {question}: {result['confidence']:.2f}")
```

## Troubleshooting

### No beliefs created

```python
# Check evidence collection
result = await supe.learn("Question", mode="ingest")
if result['evidence_count'] == 0:
    print("No relevant content found in memory")
    # Solution: Store source material first
```

### Low confidence

```python
# Check gaps
if result['gaps_count'] > 5:
    print("Many knowledge gaps identified")
    # Solution: Learn prerequisites first
```

### EXPLORE mode not finding properties

```python
# Ensure question is testable
# Good: "Is addition commutative?"
# Bad: "Tell me about addition"
```

## Next Steps

1. **Read the docs**: `docs/learning_system.md`
2. **Run the tests**: `pytest tests/test_learning*.py -v`
3. **Create your own examples**: Use these as templates
4. **Build a curriculum**: Chain learning sessions
5. **Integrate with your app**: Use `supe.learn()` API

## Contributing

Found a bug or have an idea? Open an issue or PR!
