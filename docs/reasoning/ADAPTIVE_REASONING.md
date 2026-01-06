human # Adaptive Reasoning System - Layer 8: Meta-Cognition

## Overview

Supe's adaptive reasoning system enables it to **extend its own cognitive capabilities** as it encounters new problem types. This is Layer 8 of the cognitive architecture - a meta-cognitive system that reasons about reasoning itself.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 8: META-COGNITION                   │
│                                                               │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐         │
│  │  Problem   │→ │ Capability  │→ │   Strategy   │         │
│  │ Classifier │  │  Registry   │  │  Synthesizer │         │
│  └────────────┘  └─────────────┘  └──────────────┘         │
│        ↓                ↓                  ↓                 │
│  ┌────────────────────────────────────────────────┐         │
│  │           Meta-Solver (Orchestrator)           │         │
│  │  • Analyze problems                            │         │
│  │  • Check capabilities                          │         │
│  │  • Synthesize strategies                       │         │
│  │  • Execute solutions                           │         │
│  │  • Learn from experience                       │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              LAYER 7: REASONING ENGINE                       │
│  Transitive closure, causal analysis, logical inference...   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              LAYERS 1-6: FOUNDATION                          │
│  Evidence, validation, relations, AB Memory...               │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Problem Classifier (`problem_types.py`)

Analyzes problems to determine:
- **Domain**: Algebra, geometry, logic, pattern recognition, etc.
- **Required Patterns**: What types of reasoning are needed
- **Structure**: Specific problem format (factorization, system of equations, etc.)
- **Complexity**: Difficulty level (1-10 scale)

**Reasoning Patterns** (15 types):
- Logical: deductive, inductive, abductive
- Mathematical: algebraic, geometric, numeric, optimization
- Search: systematic_search, constraint_satisfaction, backtracking
- Pattern: pattern_matching, analogy, decomposition
- Meta: hypothesis_generation, hypothesis_testing, elimination

### 2. Capability Registry (`capability_registry.py`)

Tracks what the system **can do**:
- **Registered Capabilities**: Available reasoning methods
- **Domains**: What problem types each can handle
- **Confidence**: How well each works (learned from experience)
- **Prerequisites**: What other capabilities are needed
- **Statistics**: Usage count, success rate

**Base Capabilities**:
```python
algebraic_manipulation     # Solve equations
exhaustive_search          # Try all possibilities
hypothesis_testing         # Test candidate solutions
constraint_solver          # Satisfy constraints
pattern_matcher           # Recognize patterns
deductive_reasoner        # Apply logic rules
optimizer                 # Find min/max
geometric_reasoner        # Spatial reasoning
```

### 3. Meta-Solver (`meta_solver.py`)

The orchestrator that:

**Analyzes Problems**:
```python
analysis = solver.analyze_problem(problem_text)
# Returns: signature, available_capabilities, missing_capabilities, strategy
```

**Checks Capabilities**:
- Compares required patterns against available capabilities
- Identifies gaps (missing reasoning methods)

**Synthesizes Strategies**:
- If no existing strategy fits, creates a new one
- Combines available capabilities into solving steps
- Stores the new strategy for future use

**Executes Solutions**:
- Runs the selected/synthesized strategy
- Tracks which steps succeed/fail

**Learns from Experience**:
- Updates strategy confidence based on success/failure
- Adjusts capability success rates
- Improves future problem-solving

**Extends Itself**:
```python
solver.extend_capability(
    name="new_reasoner",
    pattern=ReasoningPattern.SOME_NEW_TYPE,
    domains={ProblemDomain.SOME_DOMAIN},
    description="What this does",
    implementation=actual_function,
)
```

## Problem-Solving Flow

```
1. User provides problem
        ↓
2. Classifier identifies: domain + required patterns
        ↓
3. Registry checks: Do we have these capabilities?
        ↓
4a. YES → Find or synthesize strategy
        ↓
4b. NO → Report missing capabilities
        ↓
5. Execute strategy
        ↓
6. Learn from result (update confidence, success rates)
        ↓
7. Store knowledge for future problems
```

## Key Features

### Self-Awareness

The system **knows what it knows**:
```python
analysis = solver.analyze_problem("Factor x² + 5x + 6")

print(analysis.can_solve)  # True or False
print(analysis.available_capabilities)  # List of usable methods
print(analysis.missing_capabilities)  # What it lacks
print(analysis.reasoning)  # Explanation of analysis
```

### Self-Extension

The system can **learn new reasoning methods**:
```python
# Before: Can't solve combinatorics problems
analysis = solver.analyze_problem("How many permutations of 5 items?")
# → missing_capabilities: [ReasoningPattern.COMBINATORIAL]

# Learn the new capability
solver.extend_capability("combinatorial_reasoner", ...)

# After: Can now solve combinatorics
analysis = solver.analyze_problem("How many permutations of 5 items?")
# → can_solve: True
```

### Strategy Synthesis

When encountering a **new problem structure**:
1. Check required reasoning patterns
2. Find available capabilities for each pattern
3. Combine them into a multi-step strategy
4. Mark as "synthesized" (lower initial confidence)
5. Learn from usage to improve confidence

Example:
```
Problem: Circle geometry constraint
Required: [geometric, algebraic, deductive]

System synthesizes:
  Step 1: Apply geometric_reasoner
  Step 2: Apply algebraic_manipulation
  Step 3: Apply deductive_reasoner

Strategy saved as: "synthesized_geometric_constraint_3"
```

### Learning from Experience

Every time a strategy is used:
```python
# Before solving
strategy.confidence = 0.60
strategy.success_count = 0

# After successful solve
strategy.confidence = 0.65  # Increased
strategy.success_count = 1

# After failure
strategy.confidence = 0.50  # Decreased
strategy.failure_count = 1
```

Statistics tracked:
- Capability usage counts
- Success rates (exponential moving average)
- Strategy effectiveness
- Problem type difficulty

## Current Capabilities (Demo)

**8 Base Capabilities**:
1. algebraic_manipulation (confidence: 90%)
2. exhaustive_search (confidence: 100%)
3. hypothesis_testing (confidence: 85%)
4. constraint_solver (confidence: 90%)
5. pattern_matcher (confidence: 75%)
6. deductive_reasoner (confidence: 95%)
7. optimizer (confidence: 80%)
8. geometric_reasoner (confidence: 85%)

**4 Strategies**:
1. grid_pattern_solver (confidence: 90%)
2. polynomial_factorization_solver (confidence: 95%)
3. logic_puzzle_solver (confidence: 85%)
4. synthesized_geometric_constraint_3 (confidence: 60%)

## Future Enhancements

### 1. Automatic Capability Synthesis

Not just strategies, but **new reasoning methods**:
- Observe human solving patterns
- Abstract common steps into new capability
- Register and reuse

### 2. Transfer Learning

Apply capabilities learned in one domain to another:
- "Constraint satisfaction" works in algebra AND logic
- "Pattern matching" works in sequences AND visual puzzles

### 3. Meta-Learning

Learn **how to learn**:
- Which synthesis approaches work best?
- When to try new strategies vs. refine existing?
- Optimal confidence update rates?

### 4. Collaborative Extension

Multiple agents share capabilities:
- Agent A learns "graph reasoning"
- Agent B can now use it too
- Capability registry becomes shared knowledge

### 5. Reflection & Debugging

When solutions fail, system reflects:
- Which step failed?
- Was the strategy wrong?
- Was a capability incorrectly applied?
- What should be learned from this?

## Integration with Existing Layers

**Layer 7 (Reasoning Engine)**:
- Meta-solver calls reasoning engine for logic tasks
- Reasoning engine provides capabilities like "transitive_closure"

**Layer 6 (Relations)**:
- Problem analysis stored as relations
- Strategy→Capability links tracked
- Learning creates IMPROVES_ON relations

**Layer 5 (AB Memory)**:
- All analysis, strategies, capabilities persisted
- Cross-session learning
- Knowledge accumulation

**Layers 1-4 (Evidence + Validation)**:
- Problem solutions validated
- Evidence supports/invalidates strategies
- Confidence based on validation results

## Usage Example

```python
from ab.abdb import ABMemory
from supe.reasoning.meta_solver import MetaSolver

# Initialize
memory = ABMemory("~/.supe/memory.db")
solver = MetaSolver(memory)

# Analyze a problem
analysis = solver.analyze_problem(
    "54x⁴ + 219x² + 105 = k(ax² + b)(cx² + d), find smallest ab"
)

print(f"Domain: {analysis.signature.domain}")
print(f"Can solve: {analysis.can_solve}")
print(f"Strategy: {analysis.suggested_strategy.name}")

# Solve it
result = solver.solve(
    "54x⁴ + 219x² + 105 = k(ax² + b)(cx² + d), find smallest ab"
)

print(f"Success: {result['success']}")
print(f"Answer: {result.get('answer')}")

# Extend with new capability
solver.extend_capability(
    name="my_custom_reasoner",
    pattern=ReasoningPattern.SOME_NEW_TYPE,
    domains={ProblemDomain.ALGEBRA},
    description="Special reasoning for my domain",
    implementation=my_function,
)

# System has learned and improved!
```

## Significance

This is **meta-cognition** - the system:
- **Knows what it knows** (capability awareness)
- **Knows what it doesn't know** (gap detection)
- **Can learn what it needs** (self-extension)
- **Improves from experience** (adaptation)
- **Creates new strategies** (synthesis)

This moves beyond "hardcoded problem solvers" to a system that **programs itself** with new reasoning capabilities as it encounters new challenges.

## Continuous Learning Loop

The system **improves with every problem solved** through the learning loop:

### Components

**ProblemLibrary**:
- Stores every problem + solution
- Enables similarity search by problem signature
- Tracks success rates by structure and domain

**PatternExtractor**:
- Groups problems by structure
- Extracts common solving patterns
- Suggests new capabilities from patterns
- Requires minimum occurrences (default 3)

**LearningLoop**:
- Records each solution attempt
- Creates beliefs about solving strategies
- Links solutions with DEPENDS_ON relations
- Enables reasoning by analogy

### How It Works

**1. Record Every Solution**:
```python
problem_solution = learning_loop.record_solution(
    problem_text="Factor x² + 5x + 6",
    signature=signature,
    solution="(x + 2)(x + 3)",
    success=True,
    strategy_used="polynomial_factorization_solver",
    steps_taken=[...],
    capabilities_used={"algebraic_manipulation", "exhaustive_search"},
)
```

**2. Reason by Analogy**:
```python
analogy = learning_loop.reason_by_analogy(new_problem_signature)
# Returns: {
#   "similar_problem": "Factor x² + 7x + 12",
#   "similarity": 1.00,
#   "strategy_used": "polynomial_factorization_solver",
#   "steps": [...],
#   "confidence": 0.85
# }
```

**3. Extract Patterns**:
```python
learnings = learning_loop.learn_from_experience(min_pattern_occurrences=3)
# After solving 3+ similar problems, extracts:
# - Common solving patterns
# - Capability suggestions
# - Success rate statistics
```

**4. Automatic Improvement**:
- Strategy confidence increases with success
- Capability success rates tracked
- Similar problems solved faster
- Patterns emerge from examples

### Integration with MetaSolver

The MetaSolver automatically uses the learning loop:

```python
solver = MetaSolver(memory)

# First problem - no prior experience
result1 = solver.solve("Factor x² + 5x + 6")
# → Uses base strategy, records solution

# Second similar problem - uses analogy
result2 = solver.solve("Factor x² + 7x + 12")
# → Finds similar past problem
# → Uses same strategy with higher confidence
# → Solves faster

# Third similar problem - even better
result3 = solver.solve("Factor x² + 9x + 20")
# → Strong analogy match
# → Refined strategy
# → Performance improved

# Extract learnings
learnings = solver.learn_from_experience()
# → Patterns extracted
# → New capabilities suggested
# → Statistics available
```

### Learning Metrics

The system tracks:
- **Total problems solved**
- **Success rate** (overall and by domain)
- **Patterns learned** (extracted from examples)
- **Similarity matches** (analogy success)
- **Performance improvements** (time reduction)
- **Confidence trends** (strategy refinement)

**Example Results**:
```
Problems Solved: 25
Success Rate: 92%
Patterns Learned: 4
Best Domain: algebra (100% success)
Performance Improvement: 35% faster on similar problems
```

### Demonstration

See `examples/demo_continuous_learning.py` for complete demonstration showing:
- First problem solved from scratch
- Analogy detected on second problem
- Pattern extraction after multiple examples
- Automatic capability suggestions
- Measurable performance improvements

## Files

- `supe/reasoning/problem_types.py` - Problem classification
- `supe/reasoning/capability_registry.py` - Capability tracking
- `supe/reasoning/meta_solver.py` - Meta-cognitive orchestrator
- `supe/reasoning/learning_loop.py` - Continuous learning system
- `examples/demo_adaptive_solver.py` - Basic meta-solver demonstration
- `examples/demo_continuous_learning.py` - Continuous learning demonstration

## Status

✅ **IMPLEMENTED** - Layer 8 complete with continuous learning
- Problem classification (15 reasoning patterns)
- Capability registry (track what system can do)
- Strategy synthesis (create new solving methods)
- Self-extension API (add new capabilities dynamically)
- **Continuous learning loop** (improve from every problem)
- **Problem library** (store all solutions)
- **Reasoning by analogy** (find similar past problems)
- **Pattern extraction** (abstract common patterns)
- **Automatic capability suggestions** (learn new methods)

🚧 **IN PROGRESS**:
- Full capability implementations (actual reasoning code)
- Strategy execution engine (dispatch to reasoning modules)
- Advanced synthesis algorithms (better strategy creation)

📋 **PLANNED**:
- Automatic capability abstraction (extract from successful patterns)
- Collaborative capability sharing (multi-agent learning)
- Meta-learning optimization (learn how to learn better)
- Transfer learning across domains (apply patterns to new areas)
