"""Demonstrate compositional solution using CompareGrids.

This shows how task 0520fde7 can be solved using real transformations:
1. ExtractByMarker (before) - ✅ IMPLEMENTED
2. ExtractByMarker (after)  - ✅ IMPLEMENTED
3. CompareGrids             - ✅ IMPLEMENTED
4. ConditionalColor         - ❌ NOT YET (next priority)

We can now execute steps 1-3 with real transformations!
"""

import json
import numpy as np
from supe.reasoning.arc import ARCGrid, TransformationCatalog, print_grid


def demonstrate_with_compare():
    """Show compositional solution using CompareGrids."""
    print("\n" + "="*70)
    print("Compositional Solution for Task 0520fde7")
    print("Using Real Transformations: ExtractByMarker + CompareGrids")
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
    compare = catalog.transformations["compare_grids"]

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

    # Step 3: Compare grids (NOW IMPLEMENTED!)
    print("\n" + "="*70)
    print("Step 3: CompareGrids - ✅ NOW IMPLEMENTED!")
    print("="*70)
    print("Performing: compare(before, after, operation='equal')")

    result_compare = compare.apply(
        before_grid,
        second_grid=after_grid,
        operation="equal",
        true_value=1,
        false_value=0
    )

    if result_compare.success:
        print(f"✓ {result_compare.explanation}")
        print("\nComparison Grid (1 where equal, 0 where different):")
        print_grid(result_compare.output_grid)
        comparison_grid = result_compare.output_grid

    # Step 4: Conditional color (STILL NOT IMPLEMENTED - need to do manually)
    print("\n" + "="*70)
    print("Step 4: ConditionalColor - ❌ STILL NOT YET (next implementation)")
    print("="*70)
    print("Would perform: conditional_color(comparison, before, condition='AND non-zero')")
    print("\nManual implementation:")
    print("if (comparison[i,j] == 1 AND before[i,j] != 0) then 2 else 0")

    manual_output = np.where(
        (comparison_grid.data == 1) & (before_grid.data != 0),
        2,
        0
    )
    output_grid = ARCGrid(manual_output)
    print_grid(output_grid)

    # Verify against expected
    print("\n" + "="*70)
    print("Verification")
    print("="*70)

    print("\nExpected Output:")
    print_grid(expected_output)

    matches = (output_grid.data == expected_output.data).all()
    print(f"\nComposition matches expected: {matches}")

    if matches:
        print("\n✅ SUCCESS: Compositional solution works!")
        print("\n🎯 Progress Update:")
        print("  ✅ ExtractByMarker (before/after) - Working")
        print("  ✅ CompareGrids - Working")
        print("  ❌ ConditionalColor - Still needed")
        print("\n📊 Completion: 3/4 steps (75%)")
        print("\n💡 With ConditionalColor, we can solve this task entirely with")
        print("   primitive transformations - no manual code needed!")

    print("\n" + "="*70)
    print("What We've Achieved")
    print("="*70)
    print("✅ Can extract regions by marker")
    print("✅ Can compare two grids element-wise")
    print("✅ 75% of compositional pipeline implemented")
    print("\n❌ Still need:")
    print("   - ConditionalColor: Apply colors based on conditions")
    print("\n📋 Next Step:")
    print("   Implement ConditionalColor to complete compositional pipeline")
    print("="*70)


def test_all_examples():
    """Test compositional approach on all training examples."""
    print("\n" + "="*70)
    print("Testing Compositional Approach on All Examples")
    print("="*70)

    with open("data/arc_tasks/training/0520fde7.json", 'r') as f:
        data = json.load(f)

    catalog = TransformationCatalog()
    extract = catalog.transformations["extract_by_marker"]
    compare = catalog.transformations["compare_grids"]

    all_pass = True

    for i, example in enumerate(data['train'], 1):
        print(f"\n{'='*70}")
        print(f"Example {i}/3")
        print(f"{'='*70}")

        input_grid = ARCGrid.from_list(example['input'])
        expected_output = ARCGrid.from_list(example['output'])

        # Step 1-2: Extract
        before = extract.apply(input_grid, marker_color=5, mode="before", axis="vertical").output_grid
        after = extract.apply(input_grid, marker_color=5, mode="after", axis="vertical").output_grid

        # Step 3: Compare
        comparison = compare.apply(before, second_grid=after, operation="equal").output_grid

        # Step 4: Manual conditional
        output_data = np.where(
            (comparison.data == 1) & (before.data != 0),
            2,
            0
        )
        output_grid = ARCGrid(output_data)

        matches = (output_grid.data == expected_output.data).all()
        print(f"Result: {'✅ PASS' if matches else '✗ FAIL'}")

        if not matches:
            all_pass = False

    print("\n" + "="*70)
    if all_pass:
        print("✅ ALL 3 EXAMPLES PASS")
        print("\nCompositional approach validated across all training data!")
    else:
        print("✗ Some examples failed")
    print("="*70)


if __name__ == "__main__":
    demonstrate_with_compare()
    test_all_examples()
