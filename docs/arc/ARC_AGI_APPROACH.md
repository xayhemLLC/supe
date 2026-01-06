# Tackling ARC-AGI: Architecture and Implementation Plan

## What is ARC-AGI?

**ARC (Abstraction and Reasoning Corpus)** is François Chollet's benchmark for measuring AI systems' ability to efficiently acquire new skills. It's specifically designed to resist brute-force and memorization approaches.

### Key Characteristics

**Format**:
- Grid-based visual puzzles (typically 30x30 or smaller)
- Colors: 0-9 (10 colors including background)
- Each task has 2-3 training examples
- 1-3 test examples to solve

**Challenge**:
- Must infer transformation rule from few examples
- Apply rule to novel test input
- No training on similar tasks (true few-shot)
- Requires core knowledge priors

**Core Knowledge Priors** (built-in human assumptions):
1. **Objectness** - grids contain discrete objects
2. **Cohesion** - object parts stick together
3. **Persistence** - objects continue to exist
4. **Contact** - objects can touch/overlap
5. **Symmetry** - mirroring, rotation patterns
6. **Containment** - objects can contain others
7. **Counting** - ability to count objects
8. **Basic geometry** - lines, rectangles, shapes

---

## Why ARC-AGI is Hard

### 1. Requires True Abstraction
- Not pattern matching over large datasets
- Must extract rule from 2-3 examples
- Rule must generalize to new inputs

### 2. Compositional Complexity
- Rules can involve multiple operations
- Operations can be nested/sequential
- Context-dependent transformations

### 3. No Memorization
- 800 training tasks, 400 eval tasks
- Each task is unique
- Can't learn by seeing similar examples

### 4. Diverse Transformations
Examples of transformation types:
- Fill patterns
- Rotate/flip objects
- Count and replicate
- Complete symmetry
- Identify and extract
- Apply color logic
- Stack/layer objects
- Boundary detection

---

## Supe's Approach to ARC-AGI

### Phase 1: Core Infrastructure (Weeks 1-2)

#### 1.1 Grid Representation & Parsing
```python
@dataclass
class ARCGrid:
    """Represents an ARC grid."""
    data: np.ndarray  # 2D array of colors (0-9)
    height: int
    width: int

    def get_objects(self) -> List[ARCObject]:
        """Extract discrete objects via connected components."""
        pass

    def get_background(self) -> int:
        """Identify most common color (usually 0)."""
        pass

@dataclass
class ARCObject:
    """Represents a discrete object in grid."""
    pixels: Set[Tuple[int, int]]  # Coordinates
    color: int
    bounding_box: Tuple[int, int, int, int]  # x, y, w, h

    def mass(self) -> int:
        """Number of pixels."""
        return len(self.pixels)

    def shape(self) -> np.ndarray:
        """Normalized shape representation."""
        pass
```

#### 1.2 Object Detection
**Approach**: Connected component analysis
- 4-connectivity (orthogonal neighbors)
- 8-connectivity (diagonal neighbors)
- Color-based grouping
- Size filtering (ignore noise)

```python
class ObjectDetector:
    """Detect objects in ARC grids."""

    def detect_objects(self, grid: ARCGrid) -> List[ARCObject]:
        """Find all objects via connected components."""
        # 1. Identify background color
        # 2. Run connected components on non-background
        # 3. Create ARCObject for each component
        pass

    def detect_shapes(self, grid: ARCGrid) -> List[Shape]:
        """Detect geometric shapes (lines, rectangles, etc.)."""
        pass
```

---

### Phase 2: Core Knowledge Priors (Weeks 3-4)

#### 2.1 Spatial Reasoning Primitives

```python
class SpatialReasoner:
    """Core spatial reasoning operations."""

    def translate(self, obj: ARCObject, dx: int, dy: int) -> ARCObject:
        """Move object by offset."""
        pass

    def rotate(self, obj: ARCObject, degrees: int) -> ARCObject:
        """Rotate object (90, 180, 270 degrees)."""
        pass

    def flip(self, obj: ARCObject, axis: str) -> ARCObject:
        """Flip object (horizontal, vertical, diagonal)."""
        pass

    def scale(self, obj: ARCObject, factor: int) -> ARCObject:
        """Scale object size."""
        pass

    def detect_symmetry(self, obj: ARCObject) -> Dict[str, bool]:
        """Check for reflection/rotation symmetry."""
        return {
            "horizontal": ...,
            "vertical": ...,
            "diagonal": ...,
            "rotational": ...,
        }

    def compute_relative_position(
        self, obj1: ARCObject, obj2: ARCObject
    ) -> Dict[str, Any]:
        """Relative positioning (left, right, above, below, inside)."""
        pass
```

#### 2.2 Pattern Recognition

```python
class ARCPatternMatcher:
    """Pattern detection for ARC grids."""

    def detect_repeating_pattern(self, grid: ARCGrid) -> Optional[Pattern]:
        """Find repeating tile patterns."""
        pass

    def detect_symmetry(self, grid: ARCGrid) -> Dict[str, bool]:
        """Grid-level symmetry detection."""
        pass

    def detect_color_patterns(self, grid: ARCGrid) -> List[ColorPattern]:
        """Find color-based rules (alternating, gradients, etc.)."""
        pass

    def detect_size_progression(self, objects: List[ARCObject]) -> Optional[str]:
        """Detect size patterns (growing, shrinking)."""
        pass
```

---

### Phase 3: Transformation Inference (Weeks 5-6)

#### 3.1 Transformation Catalog

**Categories**:

1. **Geometric Transformations**
   - Rotate (90°, 180°, 270°)
   - Flip (horizontal, vertical, diagonal)
   - Scale
   - Translate

2. **Color Transformations**
   - Recolor (change all X to Y)
   - Color by property (size, position)
   - Color propagation

3. **Structural Transformations**
   - Fill regions
   - Complete patterns
   - Extend lines
   - Connect objects

4. **Logical Transformations**
   - Count and replicate
   - Conditional application
   - Boolean operations (union, intersection)

5. **Compositional Transformations**
   - Sequential application
   - Conditional chains
   - Nested operations

#### 3.2 Transformation Detection

```python
@dataclass
class Transformation:
    """Represents an ARC transformation."""
    name: str
    operation: Callable
    parameters: Dict[str, Any]
    confidence: float

class TransformationInference:
    """Infer transformation from input-output pairs."""

    def infer_transformation(
        self,
        examples: List[Tuple[ARCGrid, ARCGrid]]  # (input, output) pairs
    ) -> List[Transformation]:
        """Generate candidate transformations."""

        candidates = []

        # For each transformation type
        for transform_type in self.transformation_catalog:
            # Try to fit parameters
            params = self._fit_parameters(transform_type, examples)

            if params and self._verify_on_examples(transform_type, params, examples):
                candidates.append(Transformation(
                    name=transform_type.name,
                    operation=transform_type.operation,
                    parameters=params,
                    confidence=self._compute_confidence(examples),
                ))

        return sorted(candidates, key=lambda t: t.confidence, reverse=True)

    def _fit_parameters(
        self,
        transform_type: TransformationType,
        examples: List[Tuple[ARCGrid, ARCGrid]]
    ) -> Optional[Dict[str, Any]]:
        """Fit transformation parameters to examples."""
        pass

    def _verify_on_examples(
        self,
        transform_type: TransformationType,
        params: Dict[str, Any],
        examples: List[Tuple[ARCGrid, ARCGrid]]
    ) -> bool:
        """Check if transformation produces correct outputs."""
        pass
```

---

### Phase 4: Program Synthesis (Weeks 7-8)

#### 4.1 Domain-Specific Language (DSL)

**Design a minimal DSL for ARC transformations**:

```python
# Example DSL
class ARCProgram:
    """Represents an ARC transformation program."""

    def __init__(self):
        self.operations = []

    def add_operation(self, op: Operation):
        self.operations.append(op)

    def execute(self, input_grid: ARCGrid) -> ARCGrid:
        grid = input_grid
        for op in self.operations:
            grid = op.apply(grid)
        return grid

# Example operations
class Operation:
    pass

class DetectObjects(Operation):
    """Extract objects from grid."""
    def apply(self, grid: ARCGrid) -> List[ARCObject]:
        pass

class FilterBySize(Operation):
    """Keep only objects of certain size."""
    def __init__(self, min_size: int, max_size: int):
        pass

class Rotate(Operation):
    """Rotate objects."""
    def __init__(self, degrees: int):
        self.degrees = degrees

class FillPattern(Operation):
    """Fill with repeating pattern."""
    pass

class Compose(Operation):
    """Combine multiple operations."""
    def __init__(self, *operations):
        self.operations = operations
```

#### 4.2 Program Search

**Approach**: Enumerate programs in DSL, verify on examples

```python
class ProgramSynthesizer:
    """Synthesize ARC programs from examples."""

    def synthesize(
        self,
        examples: List[Tuple[ARCGrid, ARCGrid]],
        max_depth: int = 5,
        beam_width: int = 10
    ) -> Optional[ARCProgram]:
        """Search for program matching examples."""

        # Beam search over program space
        beam = [ARCProgram()]  # Empty program

        for depth in range(max_depth):
            new_beam = []

            for program in beam:
                # Enumerate possible next operations
                for op in self._get_candidate_operations(program, examples):
                    candidate = program.copy()
                    candidate.add_operation(op)

                    # Score by match to examples
                    score = self._score_program(candidate, examples)

                    if score == 1.0:
                        # Perfect match!
                        return candidate

                    new_beam.append((candidate, score))

            # Keep top beam_width programs
            beam = [p for p, s in sorted(new_beam, key=lambda x: x[1], reverse=True)[:beam_width]]

        return beam[0] if beam else None
```

---

### Phase 5: Integration with Supe (Weeks 9-10)

#### 5.1 New Reasoning Capabilities

Add ARC-specific capabilities to `supe/reasoning/capabilities/`:

```python
# arc_visual.py
class ARCVisualReasoner:
    """Visual reasoning for ARC grids."""

    def execute(self, problem_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Parse ARC task from context
        # Detect objects
        # Infer transformation
        # Apply to test input
        pass

# arc_spatial.py
class ARCSpatialReasoner:
    """Spatial transformations for ARC."""
    pass

# arc_synthesis.py
class ARCProgramSynthesizer:
    """Program synthesis for ARC."""
    pass
```

#### 5.2 ARC-Specific Strategy

```python
# In meta_solver.py
self.strategies["arc_task"] = SolvingStrategy(
    name="arc_visual_puzzle_solver",
    problem_signature=self.classifier.get_signature("arc_puzzle"),
    steps=[
        {"action": "parse_arc_task", "pattern": ReasoningPattern.VISUAL, "capability": "arc_visual"},
        {"action": "detect_objects", "pattern": ReasoningPattern.PATTERN_MATCHING, "capability": "arc_visual"},
        {"action": "infer_transformation", "pattern": ReasoningPattern.INDUCTIVE, "capability": "arc_synthesis"},
        {"action": "apply_transformation", "pattern": ReasoningPattern.PROGRAM_SYNTHESIS, "capability": "arc_synthesis"},
    ],
    required_capabilities={"arc_visual", "arc_synthesis"},
    confidence=0.5,  # Start low, will learn
)
```

---

## Implementation Roadmap

### Week 1-2: Foundation
- [ ] Grid data structures (ARCGrid, ARCObject)
- [ ] Object detection (connected components)
- [ ] Basic spatial operations (translate, rotate, flip)
- [ ] Visualization tools

### Week 3-4: Core Primitives
- [ ] Symmetry detection
- [ ] Shape recognition (lines, rectangles)
- [ ] Relative positioning
- [ ] Pattern detection (repetition, progression)

### Week 5-6: Transformation Catalog
- [ ] Implement 20+ basic transformations
- [ ] Transformation verification
- [ ] Parameter fitting
- [ ] Confidence scoring

### Week 7-8: Program Synthesis
- [ ] Design DSL for ARC operations
- [ ] Implement program search (beam search)
- [ ] Compositional operations
- [ ] Test on simple ARC tasks

### Week 9-10: Integration
- [ ] Wire into supe capability registry
- [ ] Create ARC-specific strategies
- [ ] Add to meta-solver
- [ ] Learning from failed attempts

### Week 11-12: Evaluation & Refinement
- [ ] Test on ARC training set (800 tasks)
- [ ] Analyze failure modes
- [ ] Add missing primitives
- [ ] Optimize search

---

## Key Challenges

### 1. Compositional Complexity
**Challenge**: Rules can be sequences of operations
**Solution**:
- DSL with composition primitives
- Hierarchical program search
- Abstraction learning

### 2. Ambiguity in Few-Shot
**Challenge**: 2-3 examples can admit multiple interpretations
**Solution**:
- Rank by simplicity (Occam's razor)
- Use core knowledge priors to break ties
- Confidence scoring

### 3. Novel Transformations
**Challenge**: Test tasks may need new operation types
**Solution**:
- Extensible transformation catalog
- Learn new primitives from successful solves
- Meta-learning: learn what transformations are learnable

### 4. Search Space Explosion
**Challenge**: Combinatorially many possible programs
**Solution**:
- Pruning based on core priors
- Beam search with learned heuristics
- Type-directed synthesis

---

## Success Metrics

### Short-term (Weeks 1-6)
- ✓ Correctly detect objects in 90%+ of training grids
- ✓ Correctly identify symmetry in symmetrical examples
- ✓ Implement 30+ transformation primitives

### Medium-term (Weeks 7-12)
- ✓ Solve 10% of ARC training tasks
- ✓ Perfect accuracy on "easy" category tasks
- ✓ Working program synthesis pipeline

### Long-term (Months 3-6)
- ✓ Solve 30%+ of ARC training tasks
- ✓ Solve 20%+ of ARC eval tasks
- ✓ Learn new primitives from experience
- ✓ State-of-the-art performance

---

## Why Supe is Well-Positioned

### 1. Meta-Cognitive Architecture
- Already has strategy synthesis
- Can learn new capabilities
- Self-extending system

### 2. Learning Loop
- Records successful transformations
- Builds library of solutions
- Reasoning by analogy

### 3. Modular Capabilities
- Easy to add ARC-specific reasoners
- Compositional by design
- Clear separation of concerns

### 4. Evidence-Based Validation
- Can verify transformations on examples
- Confidence scoring built-in
- Proof-of-work validation

---

## Getting Started

### Immediate Next Steps

1. **Create ARC data loader**:
   ```python
   # arc_loader.py
   def load_arc_task(task_id: str) -> ARCTask:
       """Load task from JSON."""
       pass
   ```

2. **Implement grid visualization**:
   ```python
   def visualize_grid(grid: ARCGrid):
       """Display grid with colors."""
       pass
   ```

3. **Basic object detection**:
   ```python
   def detect_objects_simple(grid: ARCGrid) -> List[ARCObject]:
       """Connected components on non-background."""
       pass
   ```

4. **First transformation**:
   ```python
   class HorizontalFlip:
       """Flip grid horizontally."""
       def apply(self, grid: ARCGrid) -> ARCGrid:
           pass
   ```

5. **Test on simplest ARC tasks**:
   - Tasks with single transformation
   - No object detection needed
   - Direct grid manipulation

### Initial Test Tasks

Start with these task types:
1. **Horizontal/vertical flip** - simplest transformations
2. **Color substitution** - change all X to Y
3. **Pattern repetition** - tile a small pattern
4. **Crop/extract** - take subregion

Once these work, progressively add complexity.

---

## Resources

- **ARC Dataset**: https://github.com/fchollet/ARC-AGI
- **Papers**:
  - "On the Measure of Intelligence" (Chollet, 2019)
  - "Abstraction and Reasoning Corpus" paper
- **Existing Approaches**:
  - DSL-based (DreamCoder, etc.)
  - Neural (various attempts, poor results)
  - Hybrid (most promising)

---

## Conclusion

ARC-AGI represents the frontier of AI reasoning. Success requires:
- True abstraction (not memorization)
- Compositional reasoning
- Core knowledge priors
- Program synthesis

Supe's architecture is well-suited because:
- Already has meta-cognitive capabilities
- Modular and extensible
- Learning-oriented
- Evidence-based

**Timeline**: 3-6 months to competitive performance
**Effort**: Significant but achievable
**Impact**: Would demonstrate genuine AGI progress
