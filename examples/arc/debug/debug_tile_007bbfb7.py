"""Debug why tile transformation isn't solving task 007bbfb7."""

import json
from supe.reasoning.arc import (
    ARCGrid,
    ARCTask,
    TransformationCatalog,
    print_grid,
)


def load_task():
    """Load the 007bbfb7 task."""
    with open("data/arc_tasks/training/007bbfb7.json", 'r') as f:
        data = json.load(f)

    # Get first training example
    train_input = ARCGrid.from_list(data['train'][0]['input'])
    train_output = ARCGrid.from_list(data['train'][0]['output'])

    return train_input, train_output


def test_tile_directly():
    """Test if tile transformation works on this specific example."""
    print("\n" + "="*70)
    print("Direct Tile Test on 007bbfb7")
    print("="*70)

    train_input, train_output = load_task()

    print("\nInput (3x3):")
    print_grid(train_input)

    print("\nExpected Output (9x9):")
    print_grid(train_output)

    # Try tile transformation directly
    catalog = TransformationCatalog()
    tile = catalog.transformations["tile"]

    result = tile.apply(train_input, n_rows=3, n_cols=3)

    print(f"\nTile transformation result:")
    print(f"  Success: {result.success}")
    print(f"  Explanation: {result.explanation}")

    if result.success:
        print("\nActual Output (from tile):")
        print_grid(result.output_grid)

        # Compare
        matches = result.output_grid.equals(train_output)
        print(f"\nMatches expected? {matches}")

        if not matches:
            print("\nDifference detected!")
            print(f"Expected shape: {train_output.shape}")
            print(f"Actual shape: {result.output_grid.shape}")

            # Check pixel-by-pixel
            expected_data = train_output.data
            actual_data = result.output_grid.data

            differences = 0
            for i in range(min(expected_data.shape[0], actual_data.shape[0])):
                for j in range(min(expected_data.shape[1], actual_data.shape[1])):
                    if expected_data[i,j] != actual_data[i,j]:
                        differences += 1
                        if differences <= 5:  # Show first 5 differences
                            print(f"  Diff at ({i},{j}): expected {expected_data[i,j]}, got {actual_data[i,j]}")

            print(f"\nTotal differences: {differences} pixels")
    else:
        print("✗ Transformation failed!")


def test_parameter_fitting():
    """Test if parameter fitting works for tile."""
    print("\n" + "="*70)
    print("Parameter Fitting Test")
    print("="*70)

    # Load task
    with open("data/arc_tasks/training/007bbfb7.json", 'r') as f:
        data = json.load(f)

    # Get training examples
    examples = []
    for ex in data['train']:
        input_grid = ARCGrid.from_list(ex['input'])
        output_grid = ARCGrid.from_list(ex['output'])
        examples.append((input_grid, output_grid))

    print(f"\nTrying to fit parameters from {len(examples)} examples...")

    catalog = TransformationCatalog()
    tile = catalog.transformations["tile"]

    # Try to fit parameters
    params = tile.fit_parameters(examples)

    print(f"\nFitting result: {params}")

    if params:
        print(f"✓ Found parameters: {params}")

        # Verify on first example
        result = tile.apply(examples[0][0], **params)
        if result.success:
            matches = result.output_grid.equals(examples[0][1])
            print(f"  Verification: {'✓ Matches' if matches else '✗ Does not match'}")
    else:
        print("✗ Parameter fitting failed!")

        # Debug: Try manually
        print("\nDebug: Trying manual parameters...")
        for n_rows in [1, 2, 3, 4]:
            for n_cols in [1, 2, 3, 4]:
                result = tile.apply(examples[0][0], n_rows=n_rows, n_cols=n_cols)
                if result.success:
                    matches = result.output_grid.equals(examples[0][1])
                    if matches:
                        print(f"  ✓ Found working parameters: n_rows={n_rows}, n_cols={n_cols}")
                        return
        print("  ✗ No working parameters found in range 1-4")


def test_catalog_search():
    """Test if catalog.find_transformation finds tile."""
    print("\n" + "="*70)
    print("Catalog Search Test")
    print("="*70)

    # Load task
    with open("data/arc_tasks/training/007bbfb7.json", 'r') as f:
        data = json.load(f)

    # Get training examples
    examples = []
    for ex in data['train'][:2]:  # Use first 2 examples
        input_grid = ARCGrid.from_list(ex['input'])
        output_grid = ARCGrid.from_list(ex['output'])
        examples.append((input_grid, output_grid))

    print(f"\nSearching for transformations matching {len(examples)} examples...")

    catalog = TransformationCatalog()

    # Search for matching transformations
    matches = catalog.find_transformation(examples, max_results=5)

    print(f"\nFound {len(matches)} matching transformations:")
    for i, match in enumerate(matches, 1):
        print(f"  {i}. {match.transformation.name}")
        print(f"     Parameters: {match.parameters}")
        print(f"     Confidence: {match.confidence:.2f}")
        print(f"     Explanation: {match.explanation}")

    if not matches:
        print("✗ No transformations found!")
    elif matches[0].transformation.name == "tile":
        print("\n✓ Tile transformation found as best match!")
    else:
        print(f"\n⚠ Tile not the best match (best: {matches[0].transformation.name})")


if __name__ == "__main__":
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  Debugging TileTransformation on 007bbfb7".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)

    try:
        test_tile_directly()
        test_parameter_fitting()
        test_catalog_search()

        print("\n" + "="*70)
        print("DEBUG COMPLETE")
        print("="*70)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
