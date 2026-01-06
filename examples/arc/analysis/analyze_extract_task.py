"""Analyze task 0520fde7 to understand extract by marker pattern."""

import json
from supe.reasoning.arc import ARCGrid, print_grid


def analyze_task():
    """Analyze the extract by marker task."""
    with open("data/arc_tasks/training/0520fde7.json", 'r') as f:
        data = json.load(f)

    print("\n" + "="*70)
    print("Task 0520fde7 Analysis: Extract by Marker")
    print("="*70)

    for i, example in enumerate(data['train'], 1):
        print(f"\n{'='*70}")
        print(f"Example {i}")
        print(f"{'='*70}")

        input_grid = ARCGrid.from_list(example['input'])
        output_grid = ARCGrid.from_list(example['output'])

        print(f"\nInput ({input_grid.height}x{input_grid.width}):")
        print_grid(input_grid)

        print(f"\nOutput ({output_grid.height}x{output_grid.width}):")
        print_grid(output_grid)

        # Find marker color (the one that appears in input but not output)
        input_colors = input_grid.get_unique_colors()
        output_colors = output_grid.get_unique_colors()

        marker_candidates = input_colors - output_colors
        print(f"\nAnalysis:")
        print(f"  Input colors: {sorted(input_colors)}")
        print(f"  Output colors: {sorted(output_colors)}")
        print(f"  Marker candidate(s): {sorted(marker_candidates)}")

        # Find marker column
        if marker_candidates:
            marker = list(marker_candidates)[0]
            marker_cols = []
            for col in range(input_grid.width):
                if any(input_grid.data[row, col] == marker for row in range(input_grid.height)):
                    marker_cols.append(col)

            print(f"  Marker color: {marker}")
            print(f"  Marker column(s): {marker_cols}")

            if marker_cols:
                marker_col = marker_cols[0]  # Assume first marker column

                # Determine extraction pattern
                print(f"\n  Extraction pattern analysis:")
                print(f"    Input width: {input_grid.width}")
                print(f"    Output width: {output_grid.width}")
                print(f"    Marker at column: {marker_col}")
                print(f"    Columns extracted: {output_grid.width}")

                # Check which columns were extracted
                # Try: columns before marker
                if marker_col >= output_grid.width:
                    extracted_start = marker_col - output_grid.width
                    extracted_end = marker_col
                    print(f"    Hypothesis: Columns [{extracted_start}:{extracted_end}] (before marker)")

                    # Verify
                    extracted = input_grid.data[:, extracted_start:extracted_end]
                    matches = (extracted == output_grid.data).all()
                    print(f"    Verification: {'✓ Matches!' if matches else '✗ Does not match'}")

                # Try: columns after marker
                if marker_col + output_grid.width < input_grid.width:
                    extracted_start = marker_col + 1
                    extracted_end = marker_col + 1 + output_grid.width
                    print(f"    Hypothesis: Columns [{extracted_start}:{extracted_end}] (after marker)")

                    # Verify
                    if extracted_end <= input_grid.width:
                        extracted = input_grid.data[:, extracted_start:extracted_end]
                        matches = (extracted == output_grid.data).all()
                        print(f"    Verification: {'✓ Matches!' if matches else '✗ Does not match'}")

                # Try: columns around marker (excluding marker itself)
                half = output_grid.width // 2
                if marker_col >= half and marker_col + half + 1 <= input_grid.width:
                    left_start = marker_col - half
                    left_end = marker_col
                    right_start = marker_col + 1
                    right_end = marker_col + 1 + half

                    print(f"    Hypothesis: Columns [{left_start}:{left_end}] + [{right_start}:{right_end}] (around marker, excluding)")

                    # Verify by reconstructing
                    import numpy as np
                    left_part = input_grid.data[:, left_start:left_end]
                    right_part = input_grid.data[:, right_start:right_end]
                    reconstructed = np.hstack([left_part, right_part])

                    if reconstructed.shape == output_grid.data.shape:
                        matches = (reconstructed == output_grid.data).all()
                        print(f"    Verification: {'✓ Matches!' if matches else '✗ Does not match'}")


if __name__ == "__main__":
    analyze_task()
