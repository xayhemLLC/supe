# ARC Visual Reasoning - User Guide

**A Complete Tutorial for Using ARC with Supe**

This guide shows you how to use the integrated ARC visual reasoning system to solve grid transformation problems. Whether you're working with pattern recognition, visual transformations, or abstract reasoning tasks, this guide will help you get started.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Basic Usage](#basic-usage)
3. [Understanding ARC Tasks](#understanding-arc-tasks)
4. [Working with the Integrated System](#working-with-the-integrated-system)
5. [Advanced Features](#advanced-features)
6. [Real-World Examples](#real-world-examples)
7. [Troubleshooting](#troubleshooting)
8. [API Reference](#api-reference)

---

## Quick Start

### Installation

The ARC system is integrated into supe. No additional installation needed if you have supe installed:

```bash
# Ensure you're in the supe directory
cd supe

# Activate virtual environment
source .venv/bin/activate

# Verify installation
python -c "from supe.reasoning.arc import ARCCapability; print('✓ ARC ready!')"
```

### Your First ARC Task (30 seconds)

```python
from supe.reasoning.arc import ARCGrid, ARCTask, ARCCapability

# Create capability
arc = ARCCapability()

# Define a simple rotation task
task = ARCTask(
    train=[
        (ARCGrid.from_list([[1, 0], [1, 0]]),  # Input: vertical line
         ARCGrid.from_list([[1, 1], [0, 0]])),  # Output: horizontal line
    ],
    test_inputs=[ARCGrid.from_list([[0, 1], [0, 1]])],  # Another vertical line
)

# Solve it!
result = arc(task)

if result.success:
    print(f"✓ Solved! Program: {result.explanation}")
    print(f"Prediction:\n{result.predictions[0].data}")
else:
    print(f"✗ Failed: {result.explanation}")
```

**Output:**
```
✓ Solved! Program: Synthesized program: rotate(angle=90)
Prediction:
[[0 0]
 [1 1]]
```

---

## Basic Usage

### 1. Creating Grids

ARC works with 2D grids where each cell has a color (0-9).

```python
from supe.reasoning.arc import ARCGrid

# Method 1: From Python list
grid = ARCGrid.from_list([
    [0, 1, 0],
    [1, 1, 1],
    [0, 1, 0],
])

# Method 2: From numpy array
import numpy as np
grid = ARCGrid(np.array([[0, 1], [1, 0]]))

# Method 3: Create empty grid
grid = ARCGrid.empty(height=5, width=5, background=0)

# Access grid properties
print(f"Shape: {grid.shape}")  # (rows, cols)
print(f"Colors: {grid.get_unique_colors()}")
print(f"Size: {grid.width}x{grid.height}")
```

### 2. Visualizing Grids

Grids display with colored terminal output:

```python
from supe.reasoning.arc import print_grid

# Print with title
print_grid(grid, title="My Grid")

# Visual output shows colors:
# ■ = colored cell
# □ = background (0)
```

### 3. Creating Tasks

ARC tasks consist of training examples and test inputs:

```python
from supe.reasoning.arc import ARCTask

task = ARCTask(
    # Training examples (input-output pairs)
    train=[
        (input_grid_1, output_grid_1),
        (input_grid_2, output_grid_2),
    ],

    # Test inputs (what we want to predict)
    test_inputs=[test_grid_1, test_grid_2],

    # Optional: Ground truth for evaluation
    test_outputs=[expected_output_1, expected_output_2],

    # Optional: Task identifier
    task_id="my_task_001",
)
```

### 4. Solving Tasks

```python
from supe.reasoning.arc import ARCCapability

# Create capability
arc = ARCCapability(
    max_depth=3,      # Max transformation steps
    beam_width=5,     # Search width
    enable_learning=True,  # Learn from solutions
)

# Solve task
result = arc(task)

# Check result
if result.success:
    print(f"✓ Solved!")
    print(f"Program: {result.explanation}")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Time: {result.synthesis_time:.3f}s")

    # Access predictions
    for i, pred in enumerate(result.predictions):
        print(f"\nPrediction {i+1}:")
        print_grid(pred)
else:
    print(f"✗ Failed: {result.explanation}")
```

---

## Understanding ARC Tasks

### Task Structure

An ARC task teaches by example:

```
Training Example 1:
  Input:  ■□□    Output: □□■
          ■□□            □□■
          ■□□            □□■

Training Example 2:
  Input:  □■□    Output: □■□
          □■□            □■□
          □■□            □■□

Pattern: Flip horizontally

Test Input:
  Input:  ■■□    Output: ?
          □□■
```

The system learns the transformation from training examples and applies it to test inputs.

### Common Transformation Types

1. **Geometric**
   - Rotation (90°, 180°, 270°)
   - Flipping (horizontal, vertical)
   - Scaling (enlarge, shrink)
   - Translation (move objects)

2. **Color**
   - Color swapping
   - Color mapping
   - Recoloring objects
   - Background changes

3. **Structural**
   - Duplication
   - Pattern extension
   - Flood filling
   - Adding borders

### Example: Rotation Task

```python
# Training: Show that we rotate 90° clockwise
train = [
    # Example 1: Vertical line → Horizontal line
    (ARCGrid.from_list([[1, 0], [1, 0], [1, 0]]),
     ARCGrid.from_list([[1, 1, 1], [0, 0, 0]])),

    # Example 2: L-shape rotation
    (ARCGrid.from_list([[1, 0], [1, 1]]),
     ARCGrid.from_list([[1, 1], [1, 0]])),
]

# Test: Apply same rotation
test_input = ARCGrid.from_list([[0, 1], [0, 1]])

task = ARCTask(train=train, test_inputs=[test_input])
result = arc(task)

# Result: [[0, 0], [1, 1]] (rotated 90°)
```

---

## Working with the Integrated System

### Using Supe's Capability Registry

The ARC system integrates with supe's reasoning framework:

```python
from supe.reasoning.arc import setup_arc_integration
from supe.reasoning.capability_registry import CapabilityRegistry
from supe.reasoning.problem_types import ProblemClassifier

# Initialize supe components
registry = CapabilityRegistry()
classifier = ProblemClassifier()

# Integrate ARC
arc_capability = setup_arc_integration(
    registry=registry,
    classifier=classifier,
    max_depth=3,
    beam_width=5,
    enable_learning=True,
)

# Now ARC is available as a registered capability!
```

### Automatic Problem Classification

Let supe classify your problem:

```python
# Describe your problem
problem = "Given grid transformation examples, predict the next output"

# Classify it
signature = classifier.classify(problem)

print(f"Domain: {signature.domain.value}")
print(f"Patterns: {[p.value for p in signature.required_patterns]}")
print(f"Complexity: {signature.complexity}/10")

# Find appropriate capability
from supe.reasoning.problem_types import ProblemDomain, ReasoningPattern

capabilities = registry.find_capabilities(
    domain=ProblemDomain.VISUAL_REASONING,
    pattern=ReasoningPattern.PROGRAM_SYNTHESIS,
)

# Use the best one
best = capabilities[0]
result = best.invoke(task)
```

### Capability Discovery

Find the right tool for your problem:

```python
# Search by domain
visual_caps = registry.find_capabilities(
    domain=ProblemDomain.VISUAL_REASONING,
    pattern=ReasoningPattern.TRANSFORMATION_INFERENCE,
)

print(f"Found {len(visual_caps)} visual reasoning capabilities:")
for cap in visual_caps:
    print(f"  - {cap.name} (confidence: {cap.confidence})")

# Capabilities are sorted by confidence (best first)
best_cap = visual_caps[0]
```

---

## Advanced Features

### 1. Solution Library & Learning

ARC learns from successful solutions:

```python
# Enable learning
arc = ARCCapability(enable_learning=True)

# Solve Task 1
task1 = ARCTask(train=[...], test_inputs=[...])
result1 = arc(task1)
# → Adds learned program to library

# Solve Task 2 (similar pattern)
task2 = ARCTask(train=[...], test_inputs=[...])
result2 = arc(task2)
# → May reuse learned program (faster!)

# Check library
stats = arc.get_statistics()
print(f"Library size: {stats['solution_library_size']}")
print(f"Solve rate: {stats['solve_rate']:.0%}")
```

### 2. Benchmark Evaluation

Evaluate performance on multiple tasks:

```python
from supe.reasoning.arc import ARCEvaluator

# Create evaluator
evaluator = ARCEvaluator(arc)

# Evaluate on task list
tasks = [task1, task2, task3, ...]
results = evaluator.evaluate_tasks(tasks, print_progress=True)

# View summary
evaluator.print_summary(results)

# Output:
# ============================================================
# ARC EVALUATION SUMMARY
# ============================================================
#
# Task Performance:
#   Total tasks: 10
#   Solved tasks: 8
#   Solve rate: 80.0%
# ...
```

### 3. Loading ARC JSON Files

Work with official ARC benchmark format:

```python
from supe.reasoning.arc import load_arc_task

# Load from JSON file
task = load_arc_task("arc-agi/data/training/12345.json")

# Solve it
result = arc(task)

# Check correctness (if ground truth available)
if task.test_outputs:
    correct = [
        pred.equals(truth)
        for pred, truth in zip(result.predictions, task.test_outputs)
    ]
    accuracy = sum(correct) / len(correct)
    print(f"Accuracy: {accuracy:.0%}")
```

### 4. Custom Transformations

You can check what transformations are available:

```python
from supe.reasoning.arc import get_catalog

catalog = get_catalog()

# List all transformations
print("Available transformations:")
for name in catalog.list_transformations():
    transform = catalog.get(name)
    print(f"  - {name}: {transform.description}")

# Get transformation details
rotate = catalog.get("rotate")
print(f"\nRotate transformation:")
print(f"  Type: {rotate.transform_type.value}")
print(f"  Parameters: {rotate.parameter_space}")
```

### 5. Tuning Parameters

Optimize for your use case:

```python
# Fast but less accurate
arc_fast = ARCCapability(
    max_depth=2,      # Fewer transformation steps
    beam_width=3,     # Narrower search
)

# Slow but more accurate
arc_accurate = ARCCapability(
    max_depth=4,      # More transformation steps
    beam_width=10,    # Wider search
)

# Balanced (default)
arc_balanced = ARCCapability(
    max_depth=3,
    beam_width=5,
)
```

---

## Real-World Examples

### Example 1: Pattern Completion

**Problem**: Complete a repeating pattern

```python
from supe.reasoning.arc import ARCGrid, ARCTask, ARCCapability, print_grid

# Training: Show the pattern
train_in = ARCGrid.from_list([
    [1, 0, 1, 0, 1, 0],
    [0, 1, 0, 1, 0, 1],
])

train_out = ARCGrid.from_list([
    [1, 0, 1, 0, 1, 0, 1, 0],  # Extended by 2 columns
    [0, 1, 0, 1, 0, 1, 0, 1],
])

# Test: Apply same extension
test_in = ARCGrid.from_list([
    [2, 2, 0, 0, 2, 2],
    [0, 0, 2, 2, 0, 0],
])

task = ARCTask(
    train=[(train_in, train_out)],
    test_inputs=[test_in],
)

arc = ARCCapability()
result = arc(task)

if result.success:
    print("✓ Pattern extended!")
    print_grid(result.predictions[0])
```

### Example 2: Object Transformation

**Problem**: Rotate all colored objects

```python
# Training: Show rotation of colored objects
train_in = ARCGrid.from_list([
    [0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0],
    [0, 1, 0, 0, 0],
    [0, 0, 0, 2, 0],
    [0, 0, 0, 2, 0],
])

train_out = ARCGrid.from_list([
    [0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0],
    [0, 1, 1, 0, 0],
    [0, 0, 2, 2, 0],
    [0, 0, 0, 0, 0],
])

task = ARCTask(
    train=[(train_in, train_out)],
    test_inputs=[test_in],
)

result = arc(task)
```

### Example 3: Color Transformation

**Problem**: Swap two colors

```python
# Training: Show color swap (1 ↔ 2)
train_in = ARCGrid.from_list([
    [1, 0, 2],
    [2, 1, 0],
    [0, 2, 1],
])

train_out = ARCGrid.from_list([
    [2, 0, 1],  # 1s become 2s, 2s become 1s
    [1, 2, 0],
    [0, 1, 2],
])

task = ARCTask(
    train=[(train_in, train_out)],
    test_inputs=[test_in],
)

result = arc(task)
```

### Example 4: Multi-Step Transformation

**Problem**: Rotate then scale

```python
# Training: Show rotation + scaling
train_in = ARCGrid.from_list([[1, 0], [1, 0]])

train_out = ARCGrid.from_list([
    [1, 1, 1, 1],  # Rotated 90° then scaled 2x
    [1, 1, 1, 1],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
])

task = ARCTask(
    train=[(train_in, train_out)],
    test_inputs=[test_in],
)

# System will synthesize: rotate(90) → scale(2)
result = arc(task)
print(f"Program: {result.explanation}")
```

---

## Troubleshooting

### Problem: Task Not Solving

**Symptoms**: `result.success == False`

**Solutions**:

1. **Add more training examples**
   ```python
   # Not enough information
   train = [(input1, output1)]  # Only 1 example

   # Better
   train = [(input1, output1), (input2, output2)]  # 2+ examples
   ```

2. **Increase search parameters**
   ```python
   arc = ARCCapability(
       max_depth=4,   # More steps
       beam_width=10, # Wider search
   )
   ```

3. **Check if transformation is supported**
   ```python
   from supe.reasoning.arc import get_catalog
   catalog = get_catalog()
   transformations = catalog.list_transformations()
   print(f"Available: {transformations}")
   ```

### Problem: Slow Performance

**Symptoms**: Takes >1 second per task

**Solutions**:

1. **Reduce search space**
   ```python
   arc = ARCCapability(
       max_depth=2,   # Fewer steps
       beam_width=3,  # Narrower search
   )
   ```

2. **Enable learning** (speeds up similar tasks)
   ```python
   arc = ARCCapability(enable_learning=True)
   ```

3. **Check grid size**
   ```python
   # Large grids are slower
   if grid.height * grid.width > 900:  # 30x30
       print("Consider downsampling")
   ```

### Problem: Wrong Predictions

**Symptoms**: `result.success == True` but wrong output

**Solutions**:

1. **Add diverse training examples**
   ```python
   # Show multiple cases
   train = [
       (small_input, small_output),
       (large_input, large_output),
       (edge_case_input, edge_case_output),
   ]
   ```

2. **Verify training examples are correct**
   ```python
   for inp, out in task.train:
       print_grid(inp, title="Input")
       print_grid(out, title="Expected Output")
       # Manually verify these are correct!
   ```

3. **Check program explanation**
   ```python
   print(f"Program: {result.explanation}")
   # Does this match your intent?
   ```

---

## API Reference

### Core Classes

#### `ARCGrid`
```python
class ARCGrid:
    """2D grid with colored cells (0-9)."""

    @classmethod
    def from_list(cls, data: List[List[int]]) -> ARCGrid

    @classmethod
    def empty(cls, height: int, width: int, background: int = 0) -> ARCGrid

    def copy(self) -> ARCGrid
    def equals(self, other: ARCGrid) -> bool
    def to_list(self) -> List[List[int]]

    @property
    def shape(self) -> Tuple[int, int]  # (height, width)
    @property
    def height(self) -> int
    @property
    def width(self) -> int

    def get_unique_colors(self) -> Set[int]
```

#### `ARCTask`
```python
@dataclass
class ARCTask:
    """ARC task with training and test examples."""

    train: List[Tuple[ARCGrid, ARCGrid]]  # Training (input, output) pairs
    test_inputs: List[ARCGrid]             # Test inputs to predict
    test_outputs: Optional[List[ARCGrid]]  # Ground truth (optional)
    task_id: str = ""                      # Task identifier

    @classmethod
    def from_dict(cls, data: Dict) -> ARCTask  # Load from JSON

    def to_dict(self) -> Dict  # Save to JSON
```

#### `ARCCapability`
```python
class ARCCapability:
    """ARC visual reasoning capability."""

    def __init__(
        self,
        max_depth: int = 3,        # Max transformation steps
        beam_width: int = 5,       # Beam search width
        enable_learning: bool = True,  # Learn from solutions
    )

    def __call__(self, task: ARCTask) -> ARCResult  # Solve task

    def get_statistics(self) -> Dict[str, Any]  # Usage stats
    def reset_statistics(self)  # Reset counters
    def clear_library(self)  # Clear learned solutions
```

#### `ARCResult`
```python
@dataclass
class ARCResult:
    """Result from solving an ARC task."""

    success: bool                          # Whether task was solved
    predictions: List[Optional[ARCGrid]]   # Predicted outputs
    program: Optional[ProgramCandidate]    # Synthesized program
    explanation: str                       # Human-readable description
    confidence: float                      # Score (0.0 to 1.0)
    synthesis_time: float                  # Time taken (seconds)
```

### Functions

#### Visualization
```python
def print_grid(
    grid: ARCGrid,
    title: Optional[str] = None,
) -> None:
    """Print grid with colored terminal output."""

def visualize_task(
    task: ARCTask,
    show_test_outputs: bool = True,
) -> None:
    """Visualize complete ARC task."""
```

#### File I/O
```python
def load_arc_task(filepath: str) -> ARCTask:
    """Load ARC task from JSON file."""

def save_arc_task(task: ARCTask, filepath: str) -> None:
    """Save ARC task to JSON file."""
```

#### Integration
```python
def setup_arc_integration(
    registry: CapabilityRegistry,
    classifier: ProblemClassifier,
    max_depth: int = 3,
    beam_width: int = 5,
    enable_learning: bool = True,
) -> ARCCapability:
    """Complete ARC integration setup."""
```

#### Evaluation
```python
class ARCEvaluator:
    """Evaluator for ARC benchmark."""

    def __init__(self, capability: ARCCapability)

    def evaluate_task(self, task: ARCTask) -> TaskResult

    def evaluate_tasks(
        self,
        tasks: List[ARCTask],
        print_progress: bool = True,
    ) -> EvaluationResults

    def print_summary(self, results: EvaluationResults)

    def save_results(self, results: EvaluationResults, filepath: Path)
```

---

## Tips & Best Practices

### 1. Start Simple

Begin with simple, clear examples:
```python
# Good: Clear pattern
train = [
    (ARCGrid.from_list([[1, 0]]), ARCGrid.from_list([[0, 1]])),
    (ARCGrid.from_list([[0, 1]]), ARCGrid.from_list([[1, 0]])),
]

# Avoid: Ambiguous or complex first attempt
```

### 2. Provide Multiple Examples

More examples = better understanding:
```python
# Minimum: 1 example (may be ambiguous)
# Good: 2-3 examples (usually sufficient)
# Better: 4+ examples (handles edge cases)
```

### 3. Keep Grids Small

Smaller grids solve faster:
```python
# Fast: 2x2 to 10x10
# OK: 10x10 to 20x20
# Slow: 20x20 to 30x30
# Very slow: >30x30
```

### 4. Use Descriptive Task IDs

```python
task = ARCTask(
    ...,
    task_id="rotation_90_clockwise_v1",  # Descriptive
)
```

### 5. Check Statistics

Monitor performance:
```python
stats = arc.get_statistics()
if stats['solve_rate'] < 0.5:
    print("Consider tuning parameters")
```

---

## Next Steps

- **Run the demo**: `python examples/arc_integration_demo.py`
- **Try examples**: Check `examples/test_arc_phase*.py`
- **Read docs**: See `docs/ARC_PHASE*_COMPLETE.md`
- **Evaluate**: Use `ARCEvaluator` on your own tasks
- **Contribute**: Add custom transformations or improve synthesis

## Support

- **Documentation**: See `docs/` directory
- **Examples**: See `examples/` directory
- **Source**: `supe/reasoning/arc/`

---

**🎉 You're ready to use ARC visual reasoning!**

Start with the Quick Start example and explore from there. The system learns as you use it, so it gets better over time.
