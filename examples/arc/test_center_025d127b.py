"""Test centering transformation on task 025d127b."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import numpy as np
from supe.reasoning.arc.grid import ARCGrid
from supe.reasoning.arc.catalog import TransformationCatalog

def main():
    # Load task
    with open("data/arc_tasks/training/025d127b.json") as f:
        data = json.load(f)

    inp = ARCGrid.from_list(data['train'][0]['input'])
    out = ARCGrid.from_list(data['train'][0]['output'])

    catalog = TransformationCatalog()
    center_transform = catalog.get('center_objects_by_color')

    # Test horizontal centering
    result = center_transform.apply(inp, axis='horizontal')

    print("Testing horizontal centering:")
    print(f"  Success: {result.success}")

    if result.success:
        matches = np.array_equal(result.output_grid.data, out.data)
        print(f"  Matches expected: {matches}")

        if not matches:
            diff_count = (result.output_grid.data != out.data).sum()
            print(f"  Differences: {diff_count}")

            # Show all differences
            print("\n  Difference locations:")
            for i in range(result.output_grid.height):
                for j in range(result.output_grid.width):
                    if result.output_grid.data[i, j] != out.data[i, j]:
                        print(f"    ({i}, {j}): got {result.output_grid.data[i, j]}, expected {out.data[i, j]}")

            # Show full grids side by side
            print("\n  Full output vs expected:")
            for i in range(result.output_grid.height):
                result_row = list(result.output_grid.data[i, :])
                expected_row = list(out.data[i, :])
                match = "✓" if result_row == expected_row else "✗"
                print(f"    Row {i:2d}: {result_row} vs {expected_row} {match}")

if __name__ == "__main__":
    main()
