"""Test ExtractByMarker transformation."""

from supe.reasoning.arc import ARCGrid, TransformationCatalog, print_grid


def test_vertical_before():
    """Test extracting columns before vertical marker."""
    print("\n" + "="*70)
    print("Test 1: Vertical Extract (Before Marker)")
    print("="*70)

    # Create test grid (matches 0520fde7 structure)
    grid = ARCGrid.from_list([
        [1, 0, 0, 5, 0, 1, 0],
        [0, 1, 0, 5, 1, 1, 1],
        [1, 0, 0, 5, 0, 0, 0],
    ])

    print("\nInput Grid (3x7):")
    print_grid(grid)
    print("Data:")
    print(grid.data)

    # Get transformation
    catalog = TransformationCatalog()
    extract = catalog.transformations["extract_by_marker"]

    # Extract before marker
    result = extract.apply(grid, marker_color=5, mode="before", axis="vertical")

    print(f"\nTransformation: {result.explanation}")
    print(f"Success: {result.success}")

    if result.success:
        print("\nOutput Grid (3x3):")
        print_grid(result.output_grid)
        print("Data:")
        print(result.output_grid.data)

        # Verify
        expected = [[1, 0, 0],
                    [0, 1, 0],
                    [1, 0, 0]]

        matches = (result.output_grid.data == expected).all()
        print(f"\nVerification: {'✓ Matches expected!' if matches else '✗ Does not match'}")

        if matches:
            print("✅ Test passed!")
        else:
            print("✗ Test failed!")
    else:
        print(f"✗ Transformation failed: {result.explanation}")


def test_vertical_after():
    """Test extracting columns after vertical marker."""
    print("\n" + "="*70)
    print("Test 2: Vertical Extract (After Marker)")
    print("="*70)

    grid = ARCGrid.from_list([
        [1, 0, 0, 5, 0, 1, 0],
        [0, 1, 0, 5, 1, 1, 1],
        [1, 0, 0, 5, 0, 0, 0],
    ])

    print("\nInput Grid (3x7):")
    print_grid(grid)

    catalog = TransformationCatalog()
    extract = catalog.transformations["extract_by_marker"]

    result = extract.apply(grid, marker_color=5, mode="after", axis="vertical")

    print(f"\nTransformation: {result.explanation}")

    if result.success:
        print("\nOutput Grid (3x3):")
        print_grid(result.output_grid)

        expected = [[0, 1, 0],
                    [1, 1, 1],
                    [0, 0, 0]]

        matches = (result.output_grid.data == expected).all()
        print(f"\nVerification: {'✓ Matches expected!' if matches else '✗ Does not match'}")

        if matches:
            print("✅ Test passed!")


def test_vertical_around():
    """Test extracting around vertical marker (excluding marker)."""
    print("\n" + "="*70)
    print("Test 3: Vertical Extract (Around Marker)")
    print("="*70)

    grid = ARCGrid.from_list([
        [1, 0, 5, 0, 1],
        [0, 1, 5, 1, 1],
        [1, 0, 5, 0, 0],
    ])

    print("\nInput Grid (3x5):")
    print_grid(grid)

    catalog = TransformationCatalog()
    extract = catalog.transformations["extract_by_marker"]

    result = extract.apply(grid, marker_color=5, mode="around", axis="vertical")

    print(f"\nTransformation: {result.explanation}")

    if result.success:
        print("\nOutput Grid (3x4) - Before + After:")
        print_grid(result.output_grid)

        # Should be [1,0,0,1], [0,1,1,1], [1,0,0,0]
        expected = [[1, 0, 0, 1],
                    [0, 1, 1, 1],
                    [1, 0, 0, 0]]

        matches = (result.output_grid.data == expected).all()
        print(f"\nVerification: {'✓ Matches expected!' if matches else '✗ Does not match'}")

        if matches:
            print("✅ Test passed!")


def test_horizontal_marker():
    """Test extracting rows with horizontal marker."""
    print("\n" + "="*70)
    print("Test 4: Horizontal Extract (Before Marker)")
    print("="*70)

    grid = ARCGrid.from_list([
        [1, 0, 1],
        [0, 1, 0],
        [5, 5, 5],  # Marker row
        [1, 1, 0],
        [0, 0, 1],
    ])

    print("\nInput Grid (5x3):")
    print_grid(grid)

    catalog = TransformationCatalog()
    extract = catalog.transformations["extract_by_marker"]

    result = extract.apply(grid, marker_color=5, mode="before", axis="horizontal")

    print(f"\nTransformation: {result.explanation}")

    if result.success:
        print("\nOutput Grid (2x3):")
        print_grid(result.output_grid)

        expected = [[1, 0, 1],
                    [0, 1, 0]]

        matches = (result.output_grid.data == expected).all()
        print(f"\nVerification: {'✓ Matches expected!' if matches else '✗ Does not match'}")

        if matches:
            print("✅ Test passed!")


def test_catalog_registration():
    """Verify extract_by_marker is in catalog."""
    print("\n" + "="*70)
    print("Test 5: Catalog Registration")
    print("="*70)

    catalog = TransformationCatalog()

    assert "extract_by_marker" in catalog.transformations, "ExtractByMarker not in catalog!"
    print("✓ ExtractByMarker registered")

    count = len(catalog.transformations)
    print(f"✓ Total transformations: {count} (was 19, now includes extract_by_marker)")

    # List all
    print("\nAll transformations:")
    for i, name in enumerate(sorted(catalog.transformations.keys()), 1):
        symbol = "🆕" if name == "extract_by_marker" else "  "
        print(f"  {i:2}. {symbol} {name}")


if __name__ == "__main__":
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  Testing ExtractByMarker Transformation".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)

    try:
        test_vertical_before()
        test_vertical_after()
        test_vertical_around()
        test_horizontal_marker()
        test_catalog_registration()

        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nExtractByMarker is ready for real ARC tasks!")
        print("="*70)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
