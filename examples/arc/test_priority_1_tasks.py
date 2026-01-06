"""Test Priority 1 tasks - possibly already solvable with existing primitives.

Tests 3 tasks identified as promising:
1. 00d62c1b - Fill interior (FillInteriorTransformation)
2. 0d3d703e - Color mapping (ColorMapTransformation)
3. 28bf18c6 - Object extraction (CropTransformation)
"""

import json
import numpy as np
from pathlib import Path
from supe.reasoning.arc import ARCGrid, TransformationCatalog, print_grid


def load_task(task_id):
    """Load task data from JSON file."""
    task_file = Path(f"data/arc_tasks/training/{task_id}.json")
    with open(task_file, 'r') as f:
        return json.load(f)


def test_task_00d62c1b_fill_interior():
    """Test task 00d62c1b with FillInteriorTransformation."""
    print("\n" + "="*70)
    print("TASK 1: 00d62c1b - Fill Interior")
    print("="*70)

    data = load_task("00d62c1b")
    catalog = TransformationCatalog()
    fill_interior = catalog.get("fill_interior")

    if fill_interior is None:
        print("❌ FillInteriorTransformation not found in catalog")
        return False

    print("\nPattern: Green (3) boundaries → Yellow (4) interior fill")

    # Test on first training example
    first_example = data['train'][0]
    input_grid = ARCGrid.from_list(first_example['input'])
    expected_output = ARCGrid.from_list(first_example['output'])

    print("\nInput:")
    print_grid(input_grid)

    print("\nExpected Output:")
    print_grid(expected_output)

    # Try FillInterior with different parameter combinations
    test_configs = [
        {"fill_color": 4, "boundary_color": 3},
        {"fill_color": 4},  # Auto-detect boundary
        {},  # All defaults
    ]

    success = False
    for i, params in enumerate(test_configs):
        print(f"\n--- Attempt {i+1}: FillInterior with params {params} ---")

        result = fill_interior.apply(input_grid, **params)

        if not result.success:
            print(f"❌ Failed: {result.explanation}")
            continue

        print("Result:")
        print_grid(result.output_grid)

        # Check if matches expected
        if (result.output_grid.data == expected_output.data).all():
            print("✅ PERFECT MATCH!")
            success = True
            break
        else:
            diff_count = np.sum(result.output_grid.data != expected_output.data)
            print(f"⚠️  {diff_count} pixel differences")

    if success:
        # Validate on all training examples
        print("\n--- Validating on all training examples ---")
        all_pass = True
        for idx, example in enumerate(data['train']):
            inp = ARCGrid.from_list(example['input'])
            out = ARCGrid.from_list(example['output'])
            res = fill_interior.apply(inp, **params)

            if res.success and (res.output_grid.data == out.data).all():
                print(f"✅ Example {idx+1}: PASS")
            else:
                print(f"❌ Example {idx+1}: FAIL")
                all_pass = False

        return all_pass

    return False


def test_task_0d3d703e_color_map():
    """Test task 0d3d703e with ColorMapTransformation."""
    print("\n" + "="*70)
    print("TASK 2: 0d3d703e - Color Mapping")
    print("="*70)

    data = load_task("0d3d703e")
    catalog = TransformationCatalog()
    color_map = catalog.get("color_map")

    if color_map is None:
        print("❌ ColorMapTransformation not found in catalog")
        return False

    print("\nPattern: Systematic color replacement")

    # Analyze first example to infer color mapping
    first_example = data['train'][0]
    input_grid = ARCGrid.from_list(first_example['input'])
    expected_output = ARCGrid.from_list(first_example['output'])

    print("\nInput:")
    print_grid(input_grid)

    print("\nExpected Output:")
    print_grid(expected_output)

    # Infer color map from first example
    print("\n--- Inferring color mapping ---")
    input_colors = set(input_grid.data.flatten())
    output_colors = set(expected_output.data.flatten())

    print(f"Input colors: {sorted(input_colors)}")
    print(f"Output colors: {sorted(output_colors)}")

    # Build color map by comparing positions (convert numpy types to Python ints)
    color_mapping = {}
    for i in range(input_grid.height):
        for j in range(input_grid.width):
            in_color = int(input_grid.data[i, j])  # Convert to Python int
            out_color = int(expected_output.data[i, j])  # Convert to Python int
            if in_color not in color_mapping:
                color_mapping[in_color] = out_color
            elif color_mapping[in_color] != out_color:
                print(f"⚠️  Inconsistent mapping detected: {in_color} → {color_mapping[in_color]} vs {out_color}")

    print(f"\nInferred mapping: {color_mapping}")

    # Test the mapping (use 'mapping' parameter, not 'color_map')
    result = color_map.apply(input_grid, mapping=color_mapping)

    if not result.success:
        print(f"❌ Failed: {result.explanation}")
        return False

    print("\nResult:")
    print_grid(result.output_grid)

    # Check if matches expected
    if (result.output_grid.data == expected_output.data).all():
        print("✅ PERFECT MATCH!")

        # Validate on all training examples
        print("\n--- Validating on all training examples ---")
        all_pass = True
        for idx, example in enumerate(data['train']):
            inp = ARCGrid.from_list(example['input'])
            out = ARCGrid.from_list(example['output'])

            # Infer mapping for this example (convert to Python ints)
            example_mapping = {}
            for i in range(inp.height):
                for j in range(inp.width):
                    in_c = int(inp.data[i, j])
                    out_c = int(out.data[i, j])
                    if in_c not in example_mapping:
                        example_mapping[in_c] = out_c

            res = color_map.apply(inp, mapping=example_mapping)

            if res.success and (res.output_grid.data == out.data).all():
                print(f"✅ Example {idx+1}: PASS (mapping: {example_mapping})")
            else:
                print(f"❌ Example {idx+1}: FAIL")
                all_pass = False

        return all_pass
    else:
        diff_count = np.sum(result.output_grid.data != expected_output.data)
        print(f"❌ {diff_count} pixel differences")
        return False


def test_task_28bf18c6_extract_object():
    """Test task 28bf18c6 with composition: Crop + Horizontal Duplication."""
    print("\n" + "="*70)
    print("TASK 3: 28bf18c6 - Object Extraction + Duplication")
    print("="*70)

    data = load_task("28bf18c6")
    catalog = TransformationCatalog()
    crop = catalog.get("crop")
    duplicate = catalog.get("duplicate")

    if crop is None:
        print("❌ CropTransformation not found in catalog")
        return False

    if duplicate is None:
        print("❌ DuplicateTransformation not found in catalog")
        return False

    print("\nPattern: Extract colored object → Crop to bbox → Duplicate horizontally")

    # Test on first training example
    first_example = data['train'][0]
    input_grid = ARCGrid.from_list(first_example['input'])
    expected_output = ARCGrid.from_list(first_example['output'])

    print("\nInput:")
    print_grid(input_grid)

    print("\nExpected Output:")
    print_grid(expected_output)

    # Find bounding box of non-zero pixels
    print("\n--- Finding bounding box of colored object ---")

    non_zero_positions = np.argwhere(input_grid.data != 0)
    if len(non_zero_positions) == 0:
        print("❌ No colored pixels found")
        return False

    min_row = non_zero_positions[:, 0].min()
    max_row = non_zero_positions[:, 0].max()
    min_col = non_zero_positions[:, 1].min()
    max_col = non_zero_positions[:, 1].max()

    print(f"Bounding box: rows [{min_row}, {max_row}], cols [{min_col}, {max_col}]")
    print(f"Size: {max_row - min_row + 1}x{max_col - min_col + 1}")
    print(f"Expected size: {expected_output.height}x{expected_output.width}")

    # Step 1: Crop to bounding box
    print("\n--- Step 1: Crop to bounding box ---")
    crop_result = crop.apply(
        input_grid,
        top=min_row,
        left=min_col,
        height=max_row - min_row + 1,
        width=max_col - min_col + 1
    )

    if not crop_result.success:
        print(f"❌ Crop failed: {crop_result.explanation}")
        return False

    print("Cropped:")
    print_grid(crop_result.output_grid)

    # Step 2: Duplicate horizontally (2 copies)
    print("\n--- Step 2: Duplicate horizontally (2 copies) ---")
    dup_result = duplicate.apply(
        crop_result.output_grid,
        direction="horizontal",
        count=2
    )

    if not dup_result.success:
        print(f"❌ Duplicate failed: {dup_result.explanation}")
        return False

    print("After duplication:")
    print_grid(dup_result.output_grid)

    # Check if matches expected
    if (dup_result.output_grid.data == expected_output.data).all():
        print("✅ PERFECT MATCH! (Compositional solution)")

        # Validate on all training examples
        print("\n--- Validating on all training examples ---")
        all_pass = True
        for idx, example in enumerate(data['train']):
            inp = ARCGrid.from_list(example['input'])
            out = ARCGrid.from_list(example['output'])

            # Find bounding box for this example
            nz = np.argwhere(inp.data != 0)
            if len(nz) == 0:
                print(f"❌ Example {idx+1}: No colored pixels")
                all_pass = False
                continue

            mr = nz[:, 0].min()
            Mr = nz[:, 0].max()
            mc = nz[:, 1].min()
            Mc = nz[:, 1].max()

            # Step 1: Crop
            crop_res = crop.apply(
                inp,
                top=mr,
                left=mc,
                height=Mr - mr + 1,
                width=Mc - mc + 1
            )

            if not crop_res.success:
                print(f"❌ Example {idx+1}: Crop failed")
                all_pass = False
                continue

            # Step 2: Duplicate horizontally
            dup_res = duplicate.apply(
                crop_res.output_grid,
                direction="horizontal",
                count=2
            )

            if dup_res.success and (dup_res.output_grid.data == out.data).all():
                print(f"✅ Example {idx+1}: PASS")
            else:
                print(f"❌ Example {idx+1}: FAIL")
                if dup_res.success:
                    print(f"   Expected shape: {out.shape}, Got: {dup_res.output_grid.shape}")
                all_pass = False

        return all_pass
    else:
        diff_count = np.sum(dup_result.output_grid.data != expected_output.data)
        print(f"❌ {diff_count} pixel differences")
        print(f"Shape mismatch? Expected: {expected_output.shape}, Got: {dup_result.output_grid.shape}")
        return False


def main():
    """Run all Priority 1 tests."""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  Testing Priority 1 Tasks - Existing Primitives".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)

    results = {}

    # Test each task
    results['00d62c1b'] = test_task_00d62c1b_fill_interior()
    results['0d3d703e'] = test_task_0d3d703e_color_map()
    results['28bf18c6'] = test_task_28bf18c6_extract_object()

    # Summary
    print("\n" + "="*70)
    print("PRIORITY 1 TEST SUMMARY")
    print("="*70)

    solved = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nSolve Rate: {solved}/{total} ({solved/total*100:.1f}%)")

    for task_id, success in results.items():
        status = "✅ SOLVED" if success else "❌ UNSOLVED"
        print(f"  {status}: {task_id}")

    if solved > 0:
        print(f"\n🎉 Successfully solved {solved} task(s) with existing primitives!")
        print("   This demonstrates the catalog's power without adding new transformations.")
    else:
        print("\n⚠️  No tasks solved yet. These require:")
        print("   • Parameter inference improvements")
        print("   • Enhanced primitive capabilities")
        print("   • Or compositional approaches")

    print("\n" + "█"*70 + "\n")

    return results


if __name__ == "__main__":
    main()
