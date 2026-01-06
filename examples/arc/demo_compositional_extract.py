"""Demonstrate compositional solution using ExtractByMarker primitive.

This shows how task 0520fde7 would be solved using composition:
1. ExtractByMarker (before) - ✅ IMPLEMENTED
2. ExtractByMarker (after)  - ✅ IMPLEMENTED
3. CompareGrids             - ❌ NOT YET (Phase 6)
4. ConditionalColor         - ❌ NOT YET (Phase 6)

The fact that we can execute steps 1-2 demonstrates primitive value.
"""

import json
import numpy as np
from supe.reasoning.arc import ARCGrid, TransformationCatalog, print_grid


def demonstrate_compositional_pattern():
    """Show how ExtractByMarker enables compositional reasoning."""
    print("\n" + "="*70)
    print("Compositional Solution for Task 0520fde7")
    print("="*70)

    # Load the task
    with open("data/arc_tasks/training/0520fde7.json", 'r') as f:
        data = json.load(f)

    example = data['train'][0]
    input_grid = ARCGrid.from_list(example['input'])
    expected_output = ARCGrid.from_list(example['output'])

    print("\n" + "="*70)
    print("Step 0: Input Grid (3x7)")
    print("="*70)
    print_grid(input_grid)
    print("\nNote: Column 3 (color 5) is the marker dividing the grid")

    # Get catalog
    catalog = TransformationCatalog()
    extract = catalog.transformations["extract_by_marker"]

    # Step 1: Extract before marker
    print("\n" + "="*70)
    print("Step 1: ExtractByMarker (before) - ✅ IMPLEMENTED")
    print("="*70)
    result_before = extract.apply(input_grid, marker_color=5, mode="before", axis="vertical")

    if result_before.success:
        print(f"✓ {result_before.explanation}")
        print("\nBefore Grid (3x3):")
        print_grid(result_before.output_grid)
        before_grid = result_before.output_grid

    # Step 2: Extract after marker
    print("\n" + "="*70)
    print("Step 2: ExtractByMarker (after) - ✅ IMPLEMENTED")
    print("="*70)
    result_after = extract.apply(input_grid, marker_color=5, mode="after", axis="vertical")

    if result_after.success:
        print(f"✓ {result_after.explanation}")
        print("\nAfter Grid (3x3):")
        print_grid(result_after.output_grid)
        after_grid = result_after.output_grid

    # Step 3: Compare grids (NOT YET IMPLEMENTED)
    print("\n" + "="*70)
    print("Step 3: CompareGrids - ❌ NOT YET IMPLEMENTED (Phase 6)")
    print("="*70)
    print("Would perform: compare(before, after, mode='element_wise')")
    print("Output: boolean mask where before[i,j] == after[i,j]")
    print("\nManual comparison:")
    comparison = (before_grid.data == after_grid.data)
    print(comparison.astype(int))

    # Step 4: Conditional color (NOT YET IMPLEMENTED)
    print("\n" + "="*70)
    print("Step 4: ConditionalColor - ❌ NOT YET IMPLEMENTED (Phase 6)")
    print("="*70)
    print("Would perform: if (mask[i,j] AND before[i,j] != 0) then 2 else 0")
    print("\nManual implementation:")
    manual_output = np.where(
        (before_grid.data == after_grid.data) & (before_grid.data != 0),
        2,
        0
    )
    output_grid = ARCGrid(manual_output)
    print_grid(output_grid)

    # Verify against expected
    print("\n" + "="*70)
    print("Verification")
    print("="*70)
    matches = (output_grid.data == expected_output.data).all()
    print(f"Manual composition matches expected: {matches}")

    if matches:
        print("\n✅ SUCCESS: Compositional solution works!")
        print("\nThis demonstrates:")
        print("  1. ExtractByMarker primitives work correctly")
        print("  2. We understand the full compositional pattern")
        print("  3. We need CompareGrids and ConditionalColor for Phase 6")
        print("  4. The primitives enable future compositional reasoning")

    print("\n" + "="*70)
    print("Value of Primitives")
    print("="*70)
    print("✅ ExtractByMarker solves:")
    print("   - Marker-based region extraction (many ARC tasks)")
    print("   - Grid sectioning by special colors")
    print("   - Spatial reference patterns")
    print("\n❌ But task 0520fde7 additionally requires:")
    print("   - Element-wise comparison operators")
    print("   - Conditional coloring logic")
    print("\n📋 Phase 6 Priorities:")
    print("   1. CompareGrids transformation")
    print("   2. ConditionalColor transformation")
    print("   3. Compositional DSL enhancements")
    print("="*70)


if __name__ == "__main__":
    demonstrate_compositional_pattern()
