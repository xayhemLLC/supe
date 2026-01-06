"""Complete compositional solution for task 0520fde7.

This demonstrates solving a real ARC task using ONLY primitive transformations:
1. ExtractByMarker (before) - ✅ IMPLEMENTED
2. ExtractByMarker (after)  - ✅ IMPLEMENTED
3. CompareGrids             - ✅ IMPLEMENTED
4. ConditionalColor         - ✅ IMPLEMENTED

100% compositional - no manual numpy operations!
"""

import json
from supe.reasoning.arc import ARCGrid, TransformationCatalog, print_grid


def solve_with_primitives():
    """Solve task 0520fde7 using only primitive transformations."""
    print("\n" + "="*70)
    print("COMPLETE COMPOSITIONAL SOLUTION FOR TASK 0520fde7")
    print("Using 100% Primitive Transformations - No Manual Code!")
    print("="*70)

    # Load the task
    with open("data/arc_tasks/training/0520fde7.json", 'r') as f:
        data = json.load(f)

    # Get catalog
    catalog = TransformationCatalog()
    extract = catalog.transformations["extract_by_marker"]
    compare = catalog.transformations["compare_grids"]
    conditional = catalog.transformations["conditional_color"]

    print(f"\n📊 Transformations used:")
    print(f"  1. ExtractByMarker (catalog position: {list(catalog.transformations.keys()).index('extract_by_marker') + 1}/22)")
    print(f"  2. CompareGrids (catalog position: {list(catalog.transformations.keys()).index('compare_grids') + 1}/22)")
    print(f"  3. ConditionalColor (catalog position: {list(catalog.transformations.keys()).index('conditional_color') + 1}/22)")

    all_pass = True

    for i, example in enumerate(data['train'], 1):
        print(f"\n{'='*70}")
        print(f"Example {i}/3")
        print(f"{'='*70}")

        input_grid = ARCGrid.from_list(example['input'])
        expected_output = ARCGrid.from_list(example['output'])

        print("\nInput Grid (3x7):")
        print_grid(input_grid)

        # STEP 1: Extract before marker
        print(f"\n{'-'*70}")
        print("STEP 1: ExtractByMarker (before)")
        print(f"{'-'*70}")
        result_before = extract.apply(
            input_grid,
            marker_color=5,
            mode="before",
            axis="vertical"
        )
        print(f"✓ {result_before.explanation}")
        print("\nBefore Grid (3x3):")
        print_grid(result_before.output_grid)
        before_grid = result_before.output_grid

        # STEP 2: Extract after marker
        print(f"\n{'-'*70}")
        print("STEP 2: ExtractByMarker (after)")
        print(f"{'-'*70}")
        result_after = extract.apply(
            input_grid,
            marker_color=5,
            mode="after",
            axis="vertical"
        )
        print(f"✓ {result_after.explanation}")
        print("\nAfter Grid (3x3):")
        print_grid(result_after.output_grid)
        after_grid = result_after.output_grid

        # STEP 3: Compare grids
        print(f"\n{'-'*70}")
        print("STEP 3: CompareGrids (equal)")
        print(f"{'-'*70}")
        result_compare = compare.apply(
            before_grid,
            second_grid=after_grid,
            operation="equal"
        )
        print(f"✓ {result_compare.explanation}")
        print("\nComparison Grid (1 where equal, 0 where different):")
        print_grid(result_compare.output_grid)
        comparison_grid = result_compare.output_grid

        # STEP 4: Conditional color
        print(f"\n{'-'*70}")
        print("STEP 4: ConditionalColor (and_non_zero)")
        print(f"{'-'*70}")
        result_conditional = conditional.apply(
            before_grid,
            condition_grid=comparison_grid,
            condition="and_non_zero",
            true_value=2,
            false_value=0
        )
        print(f"✓ {result_conditional.explanation}")
        print("\nFinal Output (2 where comparison AND before are non-zero):")
        print_grid(result_conditional.output_grid)
        output_grid = result_conditional.output_grid

        # Verify
        print(f"\n{'-'*70}")
        print("VERIFICATION")
        print(f"{'-'*70}")
        print("\nExpected Output:")
        print_grid(expected_output)

        matches = (output_grid.data == expected_output.data).all()

        if matches:
            print("\n✅ PERFECT MATCH!")
            print("Compositional solution produces correct output!")
        else:
            print("\n✗ Mismatch detected")
            all_pass = False

    print("\n" + "="*70)
    if all_pass:
        print("✅ ALL 3 EXAMPLES SOLVED CORRECTLY")
        print("\n🎯 MILESTONE ACHIEVED:")
        print("  • 100% compositional solution")
        print("  • Zero manual numpy operations")
        print("  • All transformations from catalog")
        print("  • Fully declarative pipeline")
    else:
        print("✗ Some examples failed")
    print("="*70)

    return all_pass


def show_transformation_pipeline():
    """Display the complete transformation pipeline."""
    print("\n" + "="*70)
    print("TRANSFORMATION PIPELINE SUMMARY")
    print("="*70)

    print("\nComputational Graph:")
    print("""
    Input (3x7)
        │
        ├─────────────────┬─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
    ExtractByMarker   [marker]   ExtractByMarker
    (before)                     (after)
        │                             │
        │ (3x3)                       │ (3x3)
        │                             │
        └──────────┬──────────────────┘
                   │
                   ▼
              CompareGrids
              (equal)
                   │
                   │ (3x3 comparison mask)
                   │
                   ├─────────────┐
                   │             │
                   ▼             ▼
            ConditionalColor ← before_grid
            (and_non_zero)
                   │
                   ▼
              Output (3x3)
    """)

    print("\nTransformation Details:")
    print("  1. ExtractByMarker(mode='before', axis='vertical', marker_color=5)")
    print("     → Extracts columns [0:marker_col]")
    print("")
    print("  2. ExtractByMarker(mode='after', axis='vertical', marker_color=5)")
    print("     → Extracts columns [marker_col+1:]")
    print("")
    print("  3. CompareGrids(operation='equal')")
    print("     → Produces 1 where grids match, 0 where different")
    print("")
    print("  4. ConditionalColor(condition='and_non_zero', true_value=2)")
    print("     → Applies color 2 where (comparison==1 AND before!=0)")

    print("\n" + "="*70)
    print("KEY INNOVATIONS")
    print("="*70)
    print("\n✅ No manual numpy operations")
    print("   Every step uses a cataloged transformation")
    print("\n✅ Fully declarative")
    print("   Solution describes WHAT, not HOW")
    print("\n✅ Discoverable")
    print("   Each transformation can be found via catalog search")
    print("\n✅ Composable")
    print("   Primitives chain together naturally")
    print("\n✅ Reusable")
    print("   Each primitive solves many tasks, not just this one")

    print("\n" + "="*70)


if __name__ == "__main__":
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  Task 0520fde7: Complete Compositional Solution".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)

    success = solve_with_primitives()

    if success:
        show_transformation_pipeline()

        print("\n" + "█"*70)
        print("█" + " "*68 + "█")
        print("█" + "  🎉 COMPOSITIONAL REASONING MILESTONE 🎉".center(68) + "█")
        print("█" + " "*68 + "█")
        print("█" + "  Real ARC task solved with primitive transformations".center(68) + "█")
        print("█" + " "*68 + "█")
        print("█"*70 + "\n")
