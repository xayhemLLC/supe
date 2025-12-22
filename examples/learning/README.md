# Learning System Examples

Examples demonstrating Supe's unified learning system with **INGEST** and **EXPLORE** modes.

## Directory Structure

```
learning/
├── ingest/                        # INGEST mode examples (learn from docs)
├── explore/mathematical/          # EXPLORE mode mathematical discovery
│   ├── foundations/               # Building from first principles
│   ├── arithmetic/                # Number theory, primes, modular arithmetic
│   ├── algebra/                   # Abstract, linear, complex numbers
│   ├── geometry/                  # Euclidean, trigonometry, topology
│   ├── analysis/                  # Calculus, fractals
│   ├── discrete/                  # Sets, graphs, information theory
│   ├── probability/               # Probability and statistics
│   └── advanced/                  # Higher-order patterns
└── tools/                         # Learning system utilities
```

## Quick Start

### INGEST Mode - Learn from Documentation

```bash
cd examples/learning/ingest
python learn_react_hooks.py
```

### EXPLORE Mode - Discover Mathematical Properties

```bash
cd examples/learning/explore/mathematical/foundations
python discover_from_zero.py
```

## INGEST Mode Examples

| File | Description |
|------|-------------|
| `ingest/learn_react_hooks.py` | Learn React hooks from documentation |
| `ingest/compare_modes.py` | Side-by-side comparison of INGEST vs EXPLORE |

### Features
- Cornell-style notes with cue/notes/examples/summary
- Concept extraction from text
- Question generation (core, operational, constraint, impact)
- Evidence collection with citations
- Self-testing for validation

## EXPLORE Mode - Mathematical Discovery

### `/foundations` - Building from First Principles

| File | Discovers |
|------|-----------|
| `discover_from_zero.py` | Commutativity, associativity from Peano axioms |
| `discover_math_from_zero.py` | Original mathematical discovery demo |
| `discover_ordering.py` | Greater than, less than, equality properties |
| `discover_identity_and_inverses.py` | Identity elements, inverse operations |

### `/arithmetic` - Number Theory

| File | Discovers |
|------|-----------|
| `discover_modular_arithmetic.py` | Modular addition, multiplication, patterns |
| `discover_primes.py` | Prime numbers, divisibility, factorization |
| `discover_number_theory.py` | GCD, LCM, Euclidean algorithm |

### `/algebra` - Algebraic Structures

| File | Discovers |
|------|-----------|
| `discover_abstract_algebra.py` | Groups, rings, fields, isomorphisms |
| `discover_linear_algebra.py` | Vectors, matrices, transformations |
| `discover_complex_numbers.py` | Complex plane, operations, properties |

### `/geometry` - Spatial Mathematics

| File | Discovers |
|------|-----------|
| `discover_geometry.py` | Euclidean geometry, triangles, circles |
| `discover_trigonometry.py` | Sine, cosine, identities, unit circle |
| `discover_topology.py` | Continuity, open/closed sets, homeomorphisms |

### `/analysis` - Continuous Mathematics

| File | Discovers |
|------|-----------|
| `discover_calculus.py` | Derivatives, integrals, limits |
| `discover_fractals.py` | Self-similarity, iteration, dimension |

### `/discrete` - Discrete Structures

| File | Discovers |
|------|-----------|
| `discover_set_theory.py` | Sets, unions, intersections, power sets |
| `discover_graph_theory.py` | Paths, cycles, connectivity, trees |
| `discover_information_theory.py` | Entropy, compression, channel capacity |

### `/probability` - Randomness & Statistics

| File | Discovers |
|------|-----------|
| `discover_probability.py` | Probability axioms, distributions, expectation |

### `/advanced` - Higher-Order Patterns

| File | Discovers |
|------|-----------|
| `discover_deeper_patterns.py` | Cross-domain connections, emergent properties |

## Learning System Tools

| File | Description |
|------|-------------|
| `tools/debug_learning_process.py` | Debug learning state machine |
| `tools/visualize_state_machine.py` | Visualize learning workflow |

## How It Works

### EXPLORE Mode Process

1. **Parse** - Extract testable claims from questions
2. **Generate** - Create experiments to validate properties
3. **Execute** - Run experiments with concrete examples
4. **Validate** - Check results for patterns/counterexamples
5. **Synthesize** - Generate formal theorems with proofs
6. **Store** - Save to AB Memory with cryptographic validation

### Result Types

- **PROVEN** - Property holds with high confidence (0.8-1.0)
- **CONJECTURE** - Likely true but needs more evidence (0.5-0.8)
- **DISPROVEN** - Counterexample found
- **UNKNOWN** - Insufficient evidence

## Documentation

- **System docs**: [docs/learning_system.md](../../docs/learning_system.md)
- **Mathematical journey**: [docs/guides/mathematical_journey.md](../../docs/guides/mathematical_journey.md)
- **Geometry guide**: [docs/guides/geometry_guide.md](../../docs/guides/geometry_guide.md)
- **Modular arithmetic**: [docs/guides/modular_arithmetic_guide.md](../../docs/guides/modular_arithmetic_guide.md)

## Example Output

```python
from supe import Supe

supe = Supe()
result = await supe.learn("Is addition commutative?", mode="explore")

# Returns: Theorem(
#   status=PROVEN,
#   confidence=1.0,
#   proof="For all tested pairs (a,b): a+b = b+a",
#   experiments=50,
#   counterexamples=0
# )
```

## Running All Examples

```bash
# Run a specific category
cd explore/mathematical/foundations
for f in *.py; do python "$f"; done

# Or run with pytest to validate
pytest examples/learning/ -v
```

## Key Features

- ✅ **Evidence-based** - All beliefs require validation
- ✅ **Cryptographic proof** - Tascer integration validates work
- ✅ **Spaced repetition** - SM-2 algorithm for review scheduling
- ✅ **Cross-session** - Persistent knowledge graphs in AB Memory
- ✅ **Confidence scoring** - Multi-factor confidence (0.0-1.0)
- ✅ **Formal proofs** - Generated with proper mathematical notation
