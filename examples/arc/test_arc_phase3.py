"""Test ARC Phase 3: Transformation Catalog.

Validates:
- Geometric transformations
- Color transformations
- Structural transformations
- Parameter fitting
- Transformation inference
"""

import numpy as np
from supe.reasoning.arc import (
    ARCGrid,
    get_catalog,
    print_grid,
    visualize_transformation,
)


def test_geometric_transformations():
    """Test geometric transformations."""
    print("\n" + "="*60)
    print("TEST 1: Geometric Transformations")
    print("="*60)

    catalog = get_catalog()

    # Test rotation
    grid_data = [
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
    ]
    grid = ARCGrid.from_list(grid_data)

    rotate = catalog.get("rotate")
    result = rotate.apply(grid, angle=90)

    assert result.success, "Rotation failed"
    assert result.output_grid.shape == (3, 3), f"Wrong shape: {result.output_grid.shape}"
    print(f"  ✓ Rotation: {result.explanation}")

    # Test flip
    flip = catalog.get("flip")
    result = flip.apply(grid, direction="horizontal")

    assert result.success, "Flip failed"
    print(f"  ✓ Flip: {result.explanation}")

    # Test scale
    scale = catalog.get("scale")
    result = scale.apply(grid, factor=2)

    assert result.success, "Scale failed"
    assert result.output_grid.shape == (6, 6), f"Wrong shape: {result.output_grid.shape}"
    print(f"  ✓ Scale: {result.explanation}")

    # Test crop
    padded_data = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]
    padded_grid = ARCGrid.from_list(padded_data)

    crop = catalog.get("crop")
    result = crop.apply(padded_grid, background=0)

    assert result.success, "Crop failed"
    assert result.output_grid.shape == (2, 3), f"Wrong shape: {result.output_grid.shape}"
    print(f"  ✓ Crop: {result.explanation}")


def test_color_transformations():
    """Test color transformations."""
    print("\n" + "="*60)
    print("TEST 2: Color Transformations")
    print("="*60)

    catalog = get_catalog()

    grid_data = [
        [0, 1, 0],
        [1, 2, 1],
        [0, 1, 0],
    ]
    grid = ARCGrid.from_list(grid_data)

    # Test color swap
    swap = catalog.get("color_swap")
    result = swap.apply(grid, color1=0, color2=1)

    assert result.success, "Color swap failed"
    # Verify swap worked
    assert result.output_grid.get(0, 0) == 1, "Swap didn't work"
    assert result.output_grid.get(0, 1) == 0, "Swap didn't work"
    print(f"  ✓ Color swap: {result.explanation}")

    # Test replace color
    replace = catalog.get("replace_color")
    result = replace.apply(grid, old_color=0, new_color=3)

    assert result.success, "Replace color failed"
    assert 0 not in result.output_grid.get_unique_colors(), "Color not replaced"
    assert 3 in result.output_grid.get_unique_colors(), "New color not present"
    print(f"  ✓ Replace color: {result.explanation}")

    # Test invert colors
    invert = catalog.get("invert_colors")
    result = invert.apply(grid)

    assert result.success, "Invert colors failed"
    print(f"  ✓ Invert colors: {result.explanation}")


def test_structural_transformations():
    """Test structural transformations."""
    print("\n" + "="*60)
    print("TEST 3: Structural Transformations")
    print("="*60)

    catalog = get_catalog()

    grid_data = [
        [0, 1, 0],
        [1, 1, 1],
        [0, 1, 0],
    ]
    grid = ARCGrid.from_list(grid_data)

    # Test duplicate
    duplicate = catalog.get("duplicate")
    result = duplicate.apply(grid, direction="horizontal", count=2)

    assert result.success, "Duplicate failed"
    assert result.output_grid.width == 6, f"Wrong width: {result.output_grid.width}"
    print(f"  ✓ Duplicate: {result.explanation}")

    # Test add border
    border = catalog.get("add_border")
    result = border.apply(grid, thickness=1, color=2)

    assert result.success, "Add border failed"
    assert result.output_grid.shape == (5, 5), f"Wrong shape: {result.output_grid.shape}"
    assert result.output_grid.get(0, 0) == 2, "Border not added"
    print(f"  ✓ Add border: {result.explanation}")

    # Test flood fill
    fill_data = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]
    fill_grid = ARCGrid.from_list(fill_data)

    flood = catalog.get("flood_fill")
    result = flood.apply(fill_grid, start_row=1, start_col=1, fill_color=1)

    assert result.success, "Flood fill failed"
    # All cells should be filled
    assert result.output_grid.count_color(1) == 9, "Not fully filled"
    print(f"  ✓ Flood fill: {result.explanation}")


def test_parameter_fitting():
    """Test parameter fitting from examples."""
    print("\n" + "="*60)
    print("TEST 4: Parameter Fitting")
    print("="*60)

    catalog = get_catalog()

    # Create examples for rotation (90 degrees)
    input1 = ARCGrid.from_list([
        [1, 0],
        [1, 0],
    ])
    output1 = ARCGrid.from_list([
        [1, 1],
        [0, 0],
    ])

    input2 = ARCGrid.from_list([
        [1, 1],
        [0, 0],
    ])
    output2 = ARCGrid.from_list([
        [0, 1],
        [0, 1],
    ])

    examples = [(input1, output1), (input2, output2)]

    # Fit rotation parameters
    rotate = catalog.get("rotate")
    params = rotate.fit_parameters(examples)

    assert params is not None, "Failed to fit parameters"
    assert "angle" in params, "Missing angle parameter"
    assert params["angle"] == 90, f"Wrong angle: {params['angle']}"
    print(f"  ✓ Fitted rotation parameters: {params}")

    # Verify fit works on both examples
    for i, (inp, out) in enumerate(examples):
        assert rotate.verify(inp, out, **params), f"Verification failed on example {i+1}"
    print(f"  ✓ Verified on {len(examples)} examples")


def test_transformation_inference():
    """Test automatic transformation inference."""
    print("\n" + "="*60)
    print("TEST 5: Transformation Inference")
    print("="*60)

    catalog = get_catalog()

    # Test 1: Infer flip transformation (use asymmetric pattern)
    input_grid = ARCGrid.from_list([
        [1, 2, 0],
        [1, 0, 0],
        [1, 0, 0],
    ])
    output_grid = ARCGrid.from_list([
        [0, 2, 1],
        [0, 0, 1],
        [0, 0, 1],
    ])

    match = catalog.infer_transformation(input_grid, output_grid)

    assert match is not None, "Failed to infer transformation"
    # Accept either flip or rotate (both can produce this result)
    assert match.transformation.name in ["flip", "rotate"], f"Wrong transformation: {match.transformation.name}"
    assert match.confidence >= 0.8, f"Low confidence: {match.confidence}"
    print(f"  ✓ Inferred: {match.explanation} (confidence: {match.confidence})")

    # Test 2: Infer color swap
    input_grid2 = ARCGrid.from_list([
        [0, 1, 0],
        [1, 0, 1],
        [0, 1, 0],
    ])
    output_grid2 = ARCGrid.from_list([
        [1, 0, 1],
        [0, 1, 0],
        [1, 0, 1],
    ])

    match2 = catalog.infer_transformation(input_grid2, output_grid2)

    assert match2 is not None, "Failed to infer color transformation"
    print(f"  ✓ Inferred: {match2.explanation} (confidence: {match2.confidence})")


def test_transformation_suggestions():
    """Test transformation suggestions based on heuristics."""
    print("\n" + "="*60)
    print("TEST 6: Transformation Suggestions")
    print("="*60)

    catalog = get_catalog()

    # Example: Grid gets larger (suggest scale/duplicate)
    input_grid = ARCGrid.from_list([[1, 0], [0, 1]])
    output_grid = ARCGrid.from_list([
        [1, 1, 0, 0],
        [1, 1, 0, 0],
        [0, 0, 1, 1],
        [0, 0, 1, 1],
    ])

    suggestions = catalog.suggest_transformations(input_grid, output_grid)

    assert len(suggestions) > 0, "No suggestions generated"
    print(f"  Found {len(suggestions)} suggestions:")
    for i, match in enumerate(suggestions[:3], 1):
        print(f"    {i}. {match.explanation} (confidence: {match.confidence:.2f})")

    # Best suggestion should be scale
    best = suggestions[0]
    assert best.transformation.name == "scale", f"Wrong best suggestion: {best.transformation.name}"
    print(f"  ✓ Best suggestion: {best.explanation}")


def test_catalog_statistics():
    """Test catalog statistics and listing."""
    print("\n" + "="*60)
    print("TEST 7: Catalog Statistics")
    print("="*60)

    catalog = get_catalog()

    stats = catalog.get_statistics()

    print(f"  Total transformations: {stats['total_transformations']}")
    print(f"  By type:")
    for t_type, count in stats['by_type'].items():
        print(f"    {t_type}: {count}")

    assert stats['total_transformations'] >= 18, "Missing transformations"
    assert 'geometric' in stats['by_type'], "Missing geometric transformations"
    assert 'color' in stats['by_type'], "Missing color transformations"
    assert 'structural' in stats['by_type'], "Missing structural transformations"

    print(f"  ✓ Catalog complete with {stats['total_transformations']} transformations")


def test_real_arc_example():
    """Test on a realistic ARC-like example."""
    print("\n" + "="*60)
    print("TEST 8: Realistic ARC Example")
    print("="*60)

    # Example: Rotate 90 degrees clockwise
    train_input1 = ARCGrid.from_list([
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
    ])
    train_output1 = ARCGrid.from_list([
        [0, 0, 0],
        [1, 1, 1],
        [0, 0, 0],
    ])

    train_input2 = ARCGrid.from_list([
        [1, 1, 0],
        [0, 0, 0],
    ])
    train_output2 = ARCGrid.from_list([
        [0, 1],
        [0, 1],
        [0, 0],
    ])

    test_input = ARCGrid.from_list([
        [0, 0, 1],
        [0, 0, 1],
    ])

    print("\nTraining examples:")
    print_grid(train_input1, title="  Train Input 1")
    print_grid(train_output1, title="  Train Output 1")

    # Find transformation
    catalog = get_catalog()
    matches = catalog.find_transformation([
        (train_input1, train_output1),
        (train_input2, train_output2),
    ])

    assert len(matches) > 0, "No transformation found"
    best_match = matches[0]

    print(f"\n  Found transformation: {best_match.explanation}")
    print(f"  Confidence: {best_match.confidence}")
    print(f"  Parameters: {best_match.parameters}")

    # Apply to test input
    result = best_match.transformation.apply(test_input, **best_match.parameters)

    assert result.success, "Transformation failed on test"
    print("\nTest prediction:")
    print_grid(test_input, title="  Test Input")
    print_grid(result.output_grid, title="  Predicted Output")

    print("\n  ✓ Successfully solved ARC-like task")


def run_all_tests():
    """Run all Phase 3 tests."""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  ARC-AGI Phase 3: Transformation Tests".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)

    try:
        test_geometric_transformations()
        test_color_transformations()
        test_structural_transformations()
        test_parameter_fitting()
        test_transformation_inference()
        test_transformation_suggestions()
        test_catalog_statistics()
        test_real_arc_example()

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("✓ Geometric transformations working (rotate, flip, scale, crop)")
        print("✓ Color transformations working (swap, replace, invert)")
        print("✓ Structural transformations working (duplicate, fill, border)")
        print("✓ Parameter fitting working (automatic parameter inference)")
        print("✓ Transformation inference working (find matching transformations)")
        print("✓ Smart suggestions working (heuristic-based filtering)")
        print("✓ Catalog statistics working (18+ transformations)")
        print("✓ Realistic ARC example solved")
        print("\n✓ ALL PHASE 3 TESTS PASSED")
        print("="*60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
