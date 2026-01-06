# Task 0520fde7 Analysis: Extract + Compare Pattern

**Date**: January 6, 2026
**Finding**: Task requires compositional reasoning (extract + compare + transform)

## The Pattern

### Input Structure (3x7):
```
[1 0 0 | 5 | 0 1 0]
[0 1 0 | 5 | 1 1 1]
[1 0 0 | 5 | 0 0 0]
         ↑
      Marker column (color 5)
```

### Transformation Steps:
1. **Find marker**: Column where all cells = 5 (column 3)
2. **Extract before**: Columns [0:3] = [[1,0,0], [0,1,0], [1,0,0]]
3. **Extract after**: Columns [4:7] = [[0,1,0], [1,1,1], [0,0,0]]
4. **Compare + Transform**:
   - For each position (r,c):
   - If before[r,c] == after[r,c] AND both != 0: output[r,c] = 2
   - Else: output[r,c] = 0

### Result (3x3):
```
[[0 0 0]    ← No matches
 [0 2 0]    ← Position (1,1): before=1, after=1 → output=2
 [0 0 0]]   ← No matches
```

## Why This Is Complex

**Appears to be**: Simple column extraction by marker

**Actually is**: Extract + Element-wise comparison + Conditional coloring

**Components needed**:
1. ✅ Find marker column (simple search)
2. ✅ Extract columns (array slicing)
3. ❌ Element-wise comparison (requires comparison operator)
4. ❌ Conditional coloring (requires conditional logic)

## Implementation Strategy

### Option 1: Full Compositional (Complex)
```python
# Pseudocode
def solve_0520fde7(input_grid):
    marker_col = find_marker_column(input_grid, marker_color=5)
    before = extract_columns(input_grid, 0, marker_col)
    after = extract_columns(input_grid, marker_col+1, input_grid.width)
    output = compare_and_color(before, after, match_color=2, no_match_color=0)
    return output
```

### Option 2: Single Transformation (Simpler)
```python
class ExtractByMarkerWithCompare(Transformation):
    """Extract columns around marker and compare."""
    def apply(self, input_grid, marker_color=5, match_color=2):
        # Find marker, extract, compare - all in one
        ...
```

### Option 3: Primitive Extraction Only
```python
class ExtractByMarker(Transformation):
    """Extract columns based on marker position."""
    def apply(self, input_grid, marker_color=5, mode="before"):
        # Only handles extraction part
        # Comparison would be separate transformation
        ...
```

## Decision: Option 3 (Primitive Extraction)

**Rationale**:
- ExtractByMarker is useful across many tasks
- Comparison logic is task-specific
- Can combine with other transformations in DSL
- Follows single-responsibility principle

**Implementation**:
```python
class ExtractByMarker(Transformation):
    def apply(self, grid, marker_color, mode="before", width=None):
        marker_col = find_marker_column(grid, marker_color)
        if mode == "before":
            return grid[:, :marker_col]
        elif mode == "after":
            return grid[:, marker_col+1:]
        elif mode == "around":
            # Extract both sides, excluding marker
            ...
```

## What We Learn

Similar to the tiling task (007bbfb7), task 0520fde7 demonstrates that:

1. **Visual patterns deceive**: Looks like extraction, but requires comparison
2. **Composition is key**: Real ARC combines multiple operations
3. **Primitives are valuable**: Even if they don't solve the full task, they're essential building blocks
4. **Need comparison operators**: Many tasks require element-wise comparisons

## Value of ExtractByMarker

Even though it won't solve 0520fde7 alone, ExtractByMarker will:
- ✅ Enable marker-based extraction tasks
- ✅ Serve as primitive for compositional programs
- ✅ Handle simpler extraction scenarios
- ✅ Combine with comparison/conditional transformations

## Other Task Applications

ExtractByMarker could help with:
- Grid splitting/sectioning tasks
- Extracting regions bounded by markers
- Column/row selection based on special values
- Spatial referencing patterns

## Conclusion

Like TileTransformation, ExtractByMarker is a valuable primitive even if it doesn't solve the specific task alone. We're building a **library of composable primitives** rather than task-specific solutions.

**Status**: Pattern fully understood ✓
**Implementation decision**: Primitive extraction transformation
**Expected value**: High (fundamental operation)
**Task 0520fde7 solvable**: No (requires comparison logic)
