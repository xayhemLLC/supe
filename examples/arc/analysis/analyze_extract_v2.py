"""Refined analysis of task 0520fde7."""

import json
import numpy as np
from supe.reasoning.arc import ARCGrid, print_grid


def detailed_analysis():
    """Detailed analysis with marker = 5."""
    with open("data/arc_tasks/training/0520fde7.json", 'r') as f:
        data = json.load(f)

    print("\n" + "="*70)
    print("Task 0520fde7: Detailed Analysis (Marker = 5)")
    print("="*70)

    for i, example in enumerate(data['train'][:1], 1):  # Just first example for now
        print(f"\nExample {i}")
        print("="*70)

        input_grid = ARCGrid.from_list(example['input'])
        output_grid = ARCGrid.from_list(example['output'])

        print(f"\nInput ({input_grid.height}x{input_grid.width}):")
        print_grid(input_grid)
        print(f"Data:\n{input_grid.data}")

        print(f"\nOutput ({output_grid.height}x{output_grid.width}):")
        print_grid(output_grid)
        print(f"Data:\n{output_grid.data}")

        # Marker is color 5 (appears as column separator)
        marker_color = 5
        marker_col = None

        # Find marker column (column where all cells are marker color)
        for col in range(input_grid.width):
            if all(input_grid.data[row, col] == marker_color for row in range(input_grid.height)):
                marker_col = col
                print(f"\n✓ Found marker column: {marker_col} (color {marker_color})")
                break

        if marker_col is not None:
            # Try extracting columns before marker
            print(f"\nTrying: Extract columns [0:{marker_col}]")
            before_marker = input_grid.data[:, 0:marker_col]
            print(f"Before marker shape: {before_marker.shape}")
            print(f"Before marker data:\n{before_marker}")

            # Try extracting columns after marker
            print(f"\nTrying: Extract columns [{marker_col+1}:]")
            after_marker = input_grid.data[:, marker_col+1:]
            print(f"After marker shape: {after_marker.shape}")
            print(f"After marker data:\n{after_marker}")

            # Check if output matches before marker
            if before_marker.shape == output_grid.data.shape:
                # But colors might be different
                print(f"\n✓ Before marker has same shape as output!")
                print(f"  Checking if patterns match (ignoring colors)...")

                # Map colors in before_marker to output colors
                unique_input = np.unique(before_marker)
                unique_output = np.unique(output_grid.data)

                print(f"  Before marker unique colors: {unique_input}")
                print(f"  Output unique colors: {unique_output}")

                # Check if it's a simple color mapping
                if len(unique_input) == len(unique_output):
                    # Try to infer mapping
                    color_map = {}
                    # Most common approach: map by frequency or position
                    for inp_color in unique_input:
                        inp_positions = np.where(before_marker == inp_color)
                        for out_color in unique_output:
                            out_positions = np.where(output_grid.data == out_color)
                            if len(inp_positions[0]) == len(out_positions[0]):
                                if np.array_equal(inp_positions, out_positions):
                                    color_map[inp_color] = out_color
                                    print(f"  Mapping: {inp_color} → {out_color}")

            # Check if output matches after marker
            if after_marker.shape == output_grid.data.shape:
                print(f"\n✓ After marker has same shape as output!")
                print(f"  Similar color transformation may apply")


if __name__ == "__main__":
    detailed_analysis()
