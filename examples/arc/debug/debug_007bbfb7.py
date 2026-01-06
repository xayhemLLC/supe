"""Debug task 007bbfb7 - Tile + Modify pattern."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import numpy as np
from supe.reasoning.arc.grid import ARCGrid
from supe.reasoning.arc.catalog import TransformationCatalog
from supe.reasoning.arc.composition_search import CompositionSearchEngine

def main():
    print("\n" + "="*70)
    print("DEBUGGING TASK 007bbfb7 - Tile + Modify Pattern")
    print("="*70)

    # Load task
    with open("data/arc_tasks/training/007bbfb7.json") as f:
        data = json.load(f)

    # Parse training examples
    train_inputs = []
    train_outputs = []
    for example in data['train']:
        train_inputs.append(ARCGrid.from_list(example['input']))
        train_outputs.append(ARCGrid.from_list(example['output']))

    print(f"\nLoaded {len(train_inputs)} training examples")

    # Test the pattern manually on first example
    print("\n--- Manual Pattern Test on First Example ---")
    inp = train_inputs[0]
    expected_out = train_outputs[0]

    print(f"Input shape: {inp.shape}")
    print(f"Expected output shape: {expected_out.shape}")
    print(f"Tiling factor: {expected_out.height // inp.height}")

    print(f"\nOriginal input grid:")
    for i in range(inp.height):
        print(f"  {list(inp.data[i, :])}")

    print(f"\nExpected output grid (all rows):")
    for i in range(expected_out.height):
        print(f"  Row {i}: {list(expected_out.data[i, :])}")

    catalog = TransformationCatalog()

    # Step 1: Tile
    tile_transform = catalog.get('tile')
    print(f"\nStep 1: Tile transformation")
    tile_result = tile_transform.apply(inp, count=3)
    print(f"  Success: {tile_result.success}")
    if tile_result.success:
        print(f"  Output shape: {tile_result.output_grid.shape}")
        print(f"\n  Tiled grid (all rows):")
        for i in range(tile_result.output_grid.height):
            print(f"    Row {i}: {list(tile_result.output_grid.data[i, :])}")

        # Step 2: ModifyTileRegion - try different configurations
        modify_transform = catalog.get('modify_tile_region')
        print(f"\nStep 2: Trying ModifyTileRegion transformations")

        # Try conditional_zero first
        print(f"\n  Testing conditional_zero modification:")
        for region_type in ['tile_column', 'tile_row']:
            for region_index in range(3):
                modify_result = modify_transform.apply(
                    tile_result.output_grid,
                    tile_height=inp.height,
                    tile_width=inp.width,
                    region_type=region_type,
                    region_index=region_index,
                    modification='conditional_zero',
                    original_grid=inp
                )

                if modify_result.success:
                    matches = (modify_result.output_grid.data == expected_out.data).all()
                    if matches:
                        print(f"  ✅ MATCH: {region_type} index {region_index} modification=conditional_zero")
                        print(f"\n  Result grid:")
                        for i in range(modify_result.output_grid.height):
                            print(f"    Row {i}: {list(modify_result.output_grid.data[i, :])}")
                        # Don't return yet, continue to test composition search

        # Also try unconditional modifications
        print(f"\n  Testing unconditional modifications:")
        for region_type in ['tile_column', 'tile_row']:
            for region_index in range(3):
                for modification in ['zero_nonzero', 'set_all_zero']:
                    modify_result = modify_transform.apply(
                        tile_result.output_grid,
                        tile_height=inp.height,
                        tile_width=inp.width,
                        region_type=region_type,
                        region_index=region_index,
                        modification=modification
                    )

                    if modify_result.success:
                        matches = (modify_result.output_grid.data == expected_out.data).all()
                        if matches:
                            print(f"  ✅ MATCH: {region_type} index {region_index} modification={modification}")
                            print(f"\nFirst few rows of result:")
                            for i in range(min(3, modify_result.output_grid.height)):
                                print(f"  {list(modify_result.output_grid.data[i, :])}")
                            print(f"\nFirst few rows of expected:")
                            for i in range(min(3, expected_out.height)):
                                print(f"  {list(expected_out.data[i, :])}")
                            return
                        else:
                            diff_count = (modify_result.output_grid.data != expected_out.data).sum()
                            if diff_count < 20:  # Close match
                                print(f"  ⚠️  Close: {region_type} index {region_index} {modification} - {diff_count} differences")
                                # Show where differences are
                                print(f"\n  First 3 rows of RESULT:")
                                for i in range(min(3, modify_result.output_grid.height)):
                                    print(f"    {list(modify_result.output_grid.data[i, :])}")
                                print(f"\n  First 3 rows of EXPECTED:")
                                for i in range(min(3, expected_out.height)):
                                    print(f"    {list(expected_out.data[i, :])}")

                                # Show difference locations
                                print(f"\n  Difference locations (row, col):")
                                diff_positions = []
                                for i in range(expected_out.height):
                                    for j in range(expected_out.width):
                                        if modify_result.output_grid.data[i, j] != expected_out.data[i, j]:
                                            diff_positions.append((i, j, modify_result.output_grid.data[i, j], expected_out.data[i, j]))
                                for pos in diff_positions[:10]:  # Show first 10 differences
                                    print(f"    ({pos[0]}, {pos[1]}): got {pos[2]}, expected {pos[3]}")

    # Test composition search
    print("\n--- Testing Composition Search ---")
    search = CompositionSearchEngine(catalog)

    # Test the pattern method directly with debug
    print("\n  Testing pattern method on all training examples:")
    for i, (inp, out) in enumerate(zip(train_inputs, train_outputs)):
        print(f"\n  Example {i+1}:")
        print(f"    Input shape: {inp.shape}")
        print(f"    Output shape: {out.shape}")
        print(f"    Input first row: {list(inp.data[0, :])}")

        # Try all possible configurations
        tile_transform = catalog.get('tile')
        modify_transform = catalog.get('modify_tile_region')

        found = False
        for tile_count in [2, 3, 4, 5]:
            if found:
                break
            tile_result = tile_transform.apply(inp, count=tile_count)
            if not tile_result.success:
                continue
            if tile_result.output_grid.shape != out.shape:
                continue

            # Try all region types and indices
            for region_type in ['tile_column', 'tile_row']:
                for region_index in range(tile_count):
                    for modification in ['conditional_zero']:
                        modify_result = modify_transform.apply(
                            tile_result.output_grid,
                            tile_height=inp.height,
                            tile_width=inp.width,
                            region_type=region_type,
                            region_index=region_index,
                            modification=modification,
                            original_grid=inp
                        )

                        if modify_result.success and (modify_result.output_grid.data == out.data).all():
                            print(f"    ✅ Match: tile={tile_count}, {region_type} idx={region_index}, {modification}")
                            found = True
                            break
                    if found:
                        break
                if found:
                    break

        if not found:
            print(f"    ❌ No matching configuration found")
            if i == 1:  # Show details for example 2
                print(f"\n    Example 2 input (3x3):")
                for r in range(inp.height):
                    print(f"      {list(inp.data[r, :])}")
                print(f"\n    Example 2 expected output (9x9):")
                for r in range(out.height):
                    print(f"      Row {r}: {list(out.data[r, :])}")

    solutions = search.search(train_inputs, train_outputs, max_steps=4)

    if solutions:
        print(f"\n✅ Found {len(solutions)} solutions:")
        for sol in solutions:
            print(f"  • {sol}")
    else:
        print("\n❌ No solutions found by composition search")


if __name__ == "__main__":
    main()
