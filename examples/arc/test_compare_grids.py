"""Test CompareGrids transformation."""

from supe.reasoning.arc import ARCGrid, TransformationCatalog, print_grid


def test_equal_comparison():
    """Test basic equality comparison."""
    print("\n" + "="*70)
    print("Test 1: Equal Comparison (==)")
    print("="*70)

    # Create two grids
    grid1 = ARCGrid.from_list([
        [1, 0, 1],
        [0, 1, 0],
        [1, 0, 1]
    ])

    grid2 = ARCGrid.from_list([
        [1, 1, 0],
        [0, 1, 1],
        [1, 0, 1]
    ])

    print("\nGrid 1:")
    print_grid(grid1)
    print("Data:")
    print(grid1.data)

    print("\nGrid 2:")
    print_grid(grid2)
    print("Data:")
    print(grid2.data)

    # Get transformation
    catalog = TransformationCatalog()
    compare = catalog.transformations["compare_grids"]

    # Compare
    result = compare.apply(grid1, second_grid=grid2, operation="equal")

    print(f"\nTransformation: {result.explanation}")
    print(f"Success: {result.success}")

    if result.success:
        print("\nComparison Result (1 where equal, 0 where different):")
        print_grid(result.output_grid)
        print("Data:")
        print(result.output_grid.data)

        # Verify
        expected = [[1, 0, 0],
                    [1, 1, 0],
                    [1, 1, 1]]

        matches = (result.output_grid.data == expected).all()
        print(f"\nVerification: {'✓ Matches expected!' if matches else '✗ Does not match'}")

        if matches:
            print("✅ Test passed!")
        else:
            print("Expected:")
            print(expected)
            print("✗ Test failed!")
    else:
        print(f"✗ Transformation failed: {result.explanation}")


def test_not_equal_comparison():
    """Test inequality comparison."""
    print("\n" + "="*70)
    print("Test 2: Not Equal Comparison (!=)")
    print("="*70)

    grid1 = ARCGrid.from_list([
        [1, 0, 1],
        [0, 1, 0]
    ])

    grid2 = ARCGrid.from_list([
        [1, 1, 0],
        [0, 1, 1]
    ])

    print("\nGrid 1:")
    print_grid(grid1)

    print("\nGrid 2:")
    print_grid(grid2)

    catalog = TransformationCatalog()
    compare = catalog.transformations["compare_grids"]

    result = compare.apply(grid1, second_grid=grid2, operation="not_equal")

    print(f"\nTransformation: {result.explanation}")

    if result.success:
        print("\nComparison Result (1 where different, 0 where equal):")
        print_grid(result.output_grid)

        expected = [[0, 1, 1],
                    [0, 0, 1]]

        matches = (result.output_grid.data == expected).all()
        print(f"\nVerification: {'✓ Matches expected!' if matches else '✗ Does not match'}")

        if matches:
            print("✅ Test passed!")


def test_greater_comparison():
    """Test greater-than comparison."""
    print("\n" + "="*70)
    print("Test 3: Greater Than Comparison (>)")
    print("="*70)

    grid1 = ARCGrid.from_list([
        [2, 1, 3],
        [0, 5, 1]
    ])

    grid2 = ARCGrid.from_list([
        [1, 2, 3],
        [0, 4, 2]
    ])

    print("\nGrid 1:")
    print_grid(grid1)
    print("Values:", grid1.data.tolist())

    print("\nGrid 2:")
    print_grid(grid2)
    print("Values:", grid2.data.tolist())

    catalog = TransformationCatalog()
    compare = catalog.transformations["compare_grids"]

    result = compare.apply(grid1, second_grid=grid2, operation="greater")

    print(f"\nTransformation: {result.explanation}")

    if result.success:
        print("\nComparison Result (1 where grid1 > grid2, 0 otherwise):")
        print_grid(result.output_grid)
        print("Data:", result.output_grid.data.tolist())

        # grid1 > grid2: [2>1, 1>2, 3>3] = [T, F, F]
        #                [0>0, 5>4, 1>2] = [F, T, F]
        expected = [[1, 0, 0],
                    [0, 1, 0]]

        matches = (result.output_grid.data == expected).all()
        print(f"\nVerification: {'✓ Matches expected!' if matches else '✗ Does not match'}")

        if matches:
            print("✅ Test passed!")


def test_custom_output_values():
    """Test comparison with custom true/false values."""
    print("\n" + "="*70)
    print("Test 4: Custom Output Values")
    print("="*70)

    grid1 = ARCGrid.from_list([
        [1, 0, 1],
        [0, 1, 0]
    ])

    grid2 = ARCGrid.from_list([
        [1, 1, 0],
        [0, 1, 1]
    ])

    print("\nGrid 1:")
    print_grid(grid1)

    print("\nGrid 2:")
    print_grid(grid2)

    catalog = TransformationCatalog()
    compare = catalog.transformations["compare_grids"]

    # Use true_value=2, false_value=0 (like task 0520fde7)
    result = compare.apply(
        grid1,
        second_grid=grid2,
        operation="equal",
        true_value=2,
        false_value=0
    )

    print(f"\nTransformation: {result.explanation}")
    print("Parameters: true_value=2, false_value=0")

    if result.success:
        print("\nComparison Result (2 where equal, 0 where different):")
        print_grid(result.output_grid)

        expected = [[2, 0, 0],
                    [2, 2, 0]]

        matches = (result.output_grid.data == expected).all()
        print(f"\nVerification: {'✓ Matches expected!' if matches else '✗ Does not match'}")

        if matches:
            print("✅ Test passed!")


def test_ignore_color():
    """Test comparison with ignored color (like background)."""
    print("\n" + "="*70)
    print("Test 5: Ignore Color (Treat 0 as Always Matching)")
    print("="*70)

    grid1 = ARCGrid.from_list([
        [1, 0, 1],
        [0, 2, 0]
    ])

    grid2 = ARCGrid.from_list([
        [1, 0, 3],
        [0, 3, 0]
    ])

    print("\nGrid 1:")
    print_grid(grid1)

    print("\nGrid 2:")
    print_grid(grid2)

    catalog = TransformationCatalog()
    compare = catalog.transformations["compare_grids"]

    # Compare, ignoring color 0 (background)
    result = compare.apply(
        grid1,
        second_grid=grid2,
        operation="equal",
        ignore_color=0
    )

    print(f"\nTransformation: {result.explanation}")
    print("Parameters: ignore_color=0 (background always matches)")

    if result.success:
        print("\nComparison Result:")
        print_grid(result.output_grid)
        print("Data:")
        print(result.output_grid.data)

        # Expected: [1==1, 0==0 (ignored, treated as match), 1!=3]
        #           [0==0 (ignored), 2!=3, 0==0 (ignored)]
        expected = [[1, 1, 0],
                    [1, 0, 1]]

        matches = (result.output_grid.data == expected).all()
        print(f"\nVerification: {'✓ Matches expected!' if matches else '✗ Does not match'}")

        if matches:
            print("✅ Test passed!")


def test_shape_mismatch():
    """Test that mismatched shapes are rejected."""
    print("\n" + "="*70)
    print("Test 6: Shape Mismatch Error Handling")
    print("="*70)

    grid1 = ARCGrid.from_list([
        [1, 0],
        [0, 1]
    ])

    grid2 = ARCGrid.from_list([
        [1, 0, 1],
        [0, 1, 0]
    ])

    print(f"\nGrid 1 shape: {grid1.shape}")
    print(f"Grid 2 shape: {grid2.shape}")

    catalog = TransformationCatalog()
    compare = catalog.transformations["compare_grids"]

    result = compare.apply(grid1, second_grid=grid2, operation="equal")

    print(f"\nResult: {result.explanation}")
    print(f"Success: {result.success}")

    if not result.success and "don't match" in result.explanation:
        print("✅ Test passed! Shape mismatch correctly detected.")
    else:
        print("✗ Test failed! Should have detected shape mismatch.")


def test_catalog_registration():
    """Verify compare_grids is in catalog."""
    print("\n" + "="*70)
    print("Test 7: Catalog Registration")
    print("="*70)

    catalog = TransformationCatalog()

    assert "compare_grids" in catalog.transformations, "CompareGrids not in catalog!"
    print("✓ CompareGrids registered")

    count = len(catalog.transformations)
    print(f"✓ Total transformations: {count} (was 20, now includes compare_grids)")

    # List all
    print("\nAll transformations:")
    for i, name in enumerate(sorted(catalog.transformations.keys()), 1):
        symbol = "🆕" if name == "compare_grids" else "  "
        print(f"  {i:2}. {symbol} {name}")


if __name__ == "__main__":
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  Testing CompareGrids Transformation".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)

    try:
        test_equal_comparison()
        test_not_equal_comparison()
        test_greater_comparison()
        test_custom_output_values()
        test_ignore_color()
        test_shape_mismatch()
        test_catalog_registration()

        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nCompareGrids is ready for compositional reasoning!")
        print("="*70)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
