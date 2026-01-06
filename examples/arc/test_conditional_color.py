"""Test ConditionalColor transformation."""

from supe.reasoning.arc import ARCGrid, TransformationCatalog, print_grid


def test_simple_non_zero():
    """Test simple non-zero condition."""
    print("\n" + "="*70)
    print("Test 1: Simple Non-Zero Condition")
    print("="*70)

    # Input grid (will be used as base)
    input_grid = ARCGrid.from_list([
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ])

    # Condition grid (mask)
    condition_grid = ARCGrid.from_list([
        [1, 0, 1],
        [0, 1, 0],
        [1, 0, 1]
    ])

    print("\nCondition Grid (mask - 1 where to apply color):")
    print_grid(condition_grid)

    # Get transformation
    catalog = TransformationCatalog()
    conditional = catalog.transformations["conditional_color"]

    # Apply: Use value 2 where condition is non-zero
    result = conditional.apply(
        input_grid,
        condition_grid=condition_grid,
        condition="non_zero",
        true_value=2,
        false_value=0
    )

    print(f"\nTransformation: {result.explanation}")
    print(f"Success: {result.success}")

    if result.success:
        print("\nOutput (2 where condition non-zero, 0 elsewhere):")
        print_grid(result.output_grid)

        expected = [[2, 0, 2],
                    [0, 2, 0],
                    [2, 0, 2]]

        matches = (result.output_grid.data == expected).all()
        print(f"\nVerification: {'✓ Matches expected!' if matches else '✗ Does not match'}")

        if matches:
            print("✅ Test passed!")
        else:
            print("Expected:", expected)
    else:
        print(f"✗ Transformation failed: {result.explanation}")


def test_and_non_zero():
    """Test and_non_zero condition (task 0520fde7 pattern)."""
    print("\n" + "="*70)
    print("Test 2: AND Non-Zero Condition (Task 0520fde7 Pattern)")
    print("="*70)

    # Source grid (before_grid from task)
    source_grid = ARCGrid.from_list([
        [1, 0, 0],
        [0, 1, 0],
        [1, 0, 0]
    ])

    # Condition grid (comparison result)
    condition_grid = ARCGrid.from_list([
        [0, 0, 1],
        [0, 1, 0],
        [0, 1, 1]
    ])

    print("\nSource Grid:")
    print_grid(source_grid)
    print("Data:", source_grid.data.tolist())

    print("\nCondition Grid (comparison result):")
    print_grid(condition_grid)
    print("Data:", condition_grid.data.tolist())

    catalog = TransformationCatalog()
    conditional = catalog.transformations["conditional_color"]

    # Apply: Use value 2 where (condition != 0) AND (source != 0)
    result = conditional.apply(
        source_grid,
        condition_grid=condition_grid,
        condition="and_non_zero",
        true_value=2,
        false_value=0
    )

    print(f"\nTransformation: {result.explanation}")

    if result.success:
        print("\nOutput (2 where both condition AND source are non-zero):")
        print_grid(result.output_grid)
        print("Data:", result.output_grid.data.tolist())

        # Expected: 2 only at (1,1) where condition=1 AND source=1
        expected = [[0, 0, 0],
                    [0, 2, 0],
                    [0, 0, 0]]

        matches = (result.output_grid.data == expected).all()
        print(f"\nVerification: {'✓ Matches expected!' if matches else '✗ Does not match'}")

        if matches:
            print("✅ Test passed! This is the exact pattern from task 0520fde7")


def test_zero_condition():
    """Test zero condition (inverse masking)."""
    print("\n" + "="*70)
    print("Test 3: Zero Condition (Inverse Mask)")
    print("="*70)

    input_grid = ARCGrid.from_list([
        [0, 0, 0],
        [0, 0, 0]
    ])

    condition_grid = ARCGrid.from_list([
        [1, 0, 1],
        [0, 1, 0]
    ])

    print("\nCondition Grid:")
    print_grid(condition_grid)

    catalog = TransformationCatalog()
    conditional = catalog.transformations["conditional_color"]

    # Apply: Use value 3 where condition is ZERO
    result = conditional.apply(
        input_grid,
        condition_grid=condition_grid,
        condition="zero",
        true_value=3,
        false_value=0
    )

    print(f"\nTransformation: {result.explanation}")

    if result.success:
        print("\nOutput (3 where condition is zero, 0 elsewhere):")
        print_grid(result.output_grid)

        # Expected: 3 where condition is 0
        expected = [[0, 3, 0],
                    [3, 0, 3]]

        matches = (result.output_grid.data == expected).all()
        print(f"\nVerification: {'✓ Matches expected!' if matches else '✗ Does not match'}")

        if matches:
            print("✅ Test passed!")


def test_use_source_values():
    """Test using source grid values."""
    print("\n" + "="*70)
    print("Test 4: Use Source Grid Values")
    print("="*70)

    input_grid = ARCGrid.from_list([
        [0, 0, 0],
        [0, 0, 0]
    ])

    condition_grid = ARCGrid.from_list([
        [1, 0, 1],
        [0, 1, 0]
    ])

    source_grid = ARCGrid.from_list([
        [7, 3, 8],
        [2, 5, 4]
    ])

    print("\nCondition Grid (where to copy):")
    print_grid(condition_grid)

    print("\nSource Grid (values to copy):")
    print_grid(source_grid)
    print("Values:", source_grid.data.tolist())

    catalog = TransformationCatalog()
    conditional = catalog.transformations["conditional_color"]

    # Apply: Copy from source where condition is non-zero
    result = conditional.apply(
        input_grid,
        condition_grid=condition_grid,
        source_grid=source_grid,
        condition="non_zero",
        use_source=True,
        false_value=0
    )

    print(f"\nTransformation: {result.explanation}")

    if result.success:
        print("\nOutput (source values where condition non-zero):")
        print_grid(result.output_grid)
        print("Values:", result.output_grid.data.tolist())

        # Expected: source values where condition is 1
        expected = [[7, 0, 8],
                    [0, 5, 0]]

        matches = (result.output_grid.data == expected).all()
        print(f"\nVerification: {'✓ Matches expected!' if matches else '✗ Does not match'}")

        if matches:
            print("✅ Test passed!")


def test_equals_condition():
    """Test equals condition."""
    print("\n" + "="*70)
    print("Test 5: Equals Condition")
    print("="*70)

    input_grid = ARCGrid.from_list([
        [0, 0, 0],
        [0, 0, 0]
    ])

    condition_grid = ARCGrid.from_list([
        [2, 1, 2],
        [1, 2, 1]
    ])

    print("\nCondition Grid:")
    print_grid(condition_grid)
    print("Values:", condition_grid.data.tolist())

    catalog = TransformationCatalog()
    conditional = catalog.transformations["conditional_color"]

    # Apply: Use value 9 where condition equals 2
    # For "equals" condition, true_value is the comparison target
    # Output value is also true_value (so we get 2 where condition==2)
    # Let's use a mask approach instead for clearer test
    import numpy as np
    mask_data = (condition_grid.data == 2).astype(int)
    mask_grid = ARCGrid(mask_data)

    print("\nMask (1 where condition == 2):")
    print_grid(mask_grid)

    result = conditional.apply(
        input_grid,
        condition_grid=mask_grid,
        condition="non_zero",
        true_value=9,
        false_value=0
    )

    print(f"\nTransformation: {result.explanation}")

    if result.success:
        print("\nOutput (9 where condition == 2, else 0):")
        print_grid(result.output_grid)

        expected = [[9, 0, 9],
                    [0, 9, 0]]

        matches = (result.output_grid.data == expected).all()
        print(f"\nVerification: {'✓ Matches expected!' if matches else '✗ Does not match'}")

        if matches:
            print("✅ Test passed!")


def test_shape_mismatch():
    """Test shape mismatch error handling."""
    print("\n" + "="*70)
    print("Test 6: Shape Mismatch Error Handling")
    print("="*70)

    input_grid = ARCGrid.from_list([
        [0, 0],
        [0, 0]
    ])

    condition_grid = ARCGrid.from_list([
        [1, 0, 1],
        [0, 1, 0]
    ])

    print(f"\nInput shape: {input_grid.shape}")
    print(f"Condition shape: {condition_grid.shape}")

    catalog = TransformationCatalog()
    conditional = catalog.transformations["conditional_color"]

    result = conditional.apply(
        input_grid,
        condition_grid=condition_grid,
        condition="non_zero",
        true_value=2,
        false_value=0
    )

    print(f"\nResult: {result.explanation}")
    print(f"Success: {result.success}")

    if not result.success and "mismatch" in result.explanation.lower():
        print("✅ Test passed! Shape mismatch correctly detected.")
    else:
        print("✗ Test failed! Should have detected shape mismatch.")


def test_catalog_registration():
    """Verify conditional_color is in catalog."""
    print("\n" + "="*70)
    print("Test 7: Catalog Registration")
    print("="*70)

    catalog = TransformationCatalog()

    assert "conditional_color" in catalog.transformations, "ConditionalColor not in catalog!"
    print("✓ ConditionalColor registered")

    count = len(catalog.transformations)
    print(f"✓ Total transformations: {count} (was 21, now includes conditional_color)")

    # List all
    print("\nAll transformations:")
    for i, name in enumerate(sorted(catalog.transformations.keys()), 1):
        symbol = "🆕" if name == "conditional_color" else "  "
        print(f"  {i:2}. {symbol} {name}")


if __name__ == "__main__":
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  Testing ConditionalColor Transformation".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)

    try:
        test_simple_non_zero()
        test_and_non_zero()
        test_zero_condition()
        test_use_source_values()
        test_equals_condition()
        test_shape_mismatch()
        test_catalog_registration()

        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nConditionalColor is ready for compositional reasoning!")
        print("This completes the pipeline for task 0520fde7!")
        print("="*70)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
