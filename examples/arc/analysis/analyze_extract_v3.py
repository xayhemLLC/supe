"""Final analysis: Extract before marker AND compare with after marker."""

import json
import numpy as np
from supe.reasoning.arc import ARCGrid, print_grid


def final_analysis():
    """Understand the full transformation."""
    with open("data/arc_tasks/training/0520fde7.json", 'r') as f:
        data = json.load(f)

    print("\n" + "="*70)
    print("Task 0520fde7: Complete Pattern Analysis")
    print("="*70)

    for i, example in enumerate(data['train'], 1):
        print(f"\n{'='*70}")
        print(f"Example {i}")
        print(f"{'='*70}")

        input_grid = ARCGrid.from_list(example['input'])
        output_grid = ARCGrid.from_list(example['output'])

        # Find marker column (all cells = 5)
        marker_col = None
        for col in range(input_grid.width):
            if all(input_grid.data[row, col] == 5 for row in range(input_grid.height)):
                marker_col = col
                break

        if marker_col is None:
            print("✗ No marker column found!")
            continue

        print(f"Marker column: {marker_col}")

        # Extract before and after
        before = input_grid.data[:, :marker_col]
        after = input_grid.data[:, marker_col+1:]

        print(f"\nBefore marker (cols 0:{marker_col}):")
        print(before)

        print(f"\nAfter marker (cols {marker_col+1}:):")
        print(after)

        print(f"\nOutput:")
        print(output_grid.data)

        # Analyze the transformation
        print(f"\nTransformation analysis:")

        if before.shape == after.shape == output_grid.data.shape:
            print(f"  ✓ All have same shape: {before.shape}")

            # Check if output = (before AND after) with color transform
            matches = 0
            for r in range(before.shape[0]):
                for c in range(before.shape[1]):
                    before_val = before[r, c]
                    after_val = after[r, c]
                    output_val = output_grid.data[r, c]

                    # Hypothesis: if before == after and both non-zero, output=2
                    # Otherwise output=0
                    if before_val == after_val and before_val != 0:
                        expected = 2
                    else:
                        expected = 0

                    if output_val == expected:
                        matches += 1
                    else:
                        print(f"    Position ({r},{c}): before={before_val}, after={after_val}, output={output_val}, expected={expected}")

            total = before.shape[0] * before.shape[1]
            print(f"\n  Matches: {matches}/{total}")

            if matches == total:
                print(f"  ✓ Pattern confirmed: Output = 2 where (before == after) AND both non-zero, else 0")
            else:
                # Try alternative: Output = before where (before == after), else 0
                matches_alt = 0
                for r in range(before.shape[0]):
                    for c in range(before.shape[1]):
                        before_val = before[r, c]
                        after_val = after[r, c]
                        output_val = output_grid.data[r, c]

                        if before_val == after_val:
                            expected = 2 if before_val != 0 else 0
                        else:
                            expected = 0

                        if output_val == expected:
                            matches_alt += 1

                if matches_alt == total:
                    print(f"  ✓ Alternative confirmed: Output = 2 where (before == after) AND non-zero")


if __name__ == "__main__":
    final_analysis()
