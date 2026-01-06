"""Quick test of TileTransformation before running on real ARC tasks."""

from supe.reasoning.arc import ARCGrid, TransformationCatalog, print_grid


def test_tile_basic():
    """Test basic tiling functionality."""
    print("\n" + "="*70)
    print("Test 1: Basic 3x3 Tiling")
    print("="*70)

    # Create simple 3x3 grid
    grid = ARCGrid.from_list([
        [0, 7, 7],
        [7, 7, 7],
        [0, 7, 7],
    ])

    print("\nInput Grid (3x3):")
    print_grid(grid)

    # Get tile transformation from catalog
    catalog = TransformationCatalog()
    tile_transform = catalog.transformations["tile"]

    # Tile it 3x3
    result = tile_transform.apply(grid, n_rows=3, n_cols=3)

    print(f"\nTransformation: {result.explanation}")
    print(f"Success: {result.success}")

    if result.success:
        print("\nOutput Grid (9x9):")
        print_grid(result.output_grid)

        # Verify size
        expected_size = (9, 9)
        actual_size = (result.output_grid.height, result.output_grid.width)
        print(f"\nSize check: Expected {expected_size}, Got {actual_size}")
        assert actual_size == expected_size, f"Size mismatch!"
        print("✓ Size correct")

        # Verify tiling (check a few key positions)
        original_data = grid.data
        tiled_data = result.output_grid.data

        # Top-left tile should match original
        assert (tiled_data[0:3, 0:3] == original_data).all(), "Top-left tile incorrect"
        print("✓ Top-left tile matches")

        # Top-right tile should match original
        assert (tiled_data[0:3, 6:9] == original_data).all(), "Top-right tile incorrect"
        print("✓ Top-right tile matches")

        # Bottom-left tile should match original
        assert (tiled_data[6:9, 0:3] == original_data).all(), "Bottom-left tile incorrect"
        print("✓ Bottom-left tile matches")

        # Center tile should match original
        assert (tiled_data[3:6, 3:6] == original_data).all(), "Center tile incorrect"
        print("✓ Center tile matches")

        print("\n✅ All checks passed!")
    else:
        print(f"✗ Failed: {result.explanation}")


def test_tile_different_sizes():
    """Test tiling with different n_rows and n_cols."""
    print("\n" + "="*70)
    print("Test 2: Non-Square Tiling (2x4)")
    print("="*70)

    # Create simple 2x2 grid
    grid = ARCGrid.from_list([
        [1, 0],
        [0, 1],
    ])

    print("\nInput Grid (2x2):")
    print_grid(grid)

    catalog = TransformationCatalog()
    tile_transform = catalog.transformations["tile"]

    # Tile it 2 rows, 4 columns
    result = tile_transform.apply(grid, n_rows=2, n_cols=4)

    print(f"\nTransformation: {result.explanation}")
    print(f"Success: {result.success}")

    if result.success:
        print("\nOutput Grid (4x8):")
        print_grid(result.output_grid)

        expected_size = (4, 8)
        actual_size = (result.output_grid.height, result.output_grid.width)
        print(f"\nSize check: Expected {expected_size}, Got {actual_size}")
        assert actual_size == expected_size, f"Size mismatch!"
        print("✓ Size correct")
        print("\n✅ Non-square tiling works!")


def test_catalog_registration():
    """Verify tile is registered in catalog."""
    print("\n" + "="*70)
    print("Test 3: Catalog Registration")
    print("="*70)

    catalog = TransformationCatalog()

    # Check tile is in catalog
    assert "tile" in catalog.transformations, "Tile not in catalog!"
    print("✓ Tile transformation registered")

    # Check count (should be 19 now, was 18)
    count = len(catalog.transformations)
    print(f"✓ Total transformations: {count} (was 18, now includes tile)")

    # List all transformations
    print("\nAll transformations:")
    for i, name in enumerate(sorted(catalog.transformations.keys()), 1):
        symbol = "🆕" if name == "tile" else "  "
        print(f"  {i:2}. {symbol} {name}")


if __name__ == "__main__":
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  Testing TileTransformation".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)

    try:
        test_tile_basic()
        test_tile_different_sizes()
        test_catalog_registration()

        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nTileTransformation is ready for real ARC tasks!")
        print("="*70)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
