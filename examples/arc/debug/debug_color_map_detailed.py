"""Detailed debugging of color map inference."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import numpy as np
from supe.reasoning.arc.grid import ARCGrid


def debug_color_map_manual():
    """Manually debug color mapping."""
    print("\n" + "="*70)
    print("MANUAL COLOR MAPPING DEBUG - Task 0d3d703e")
    print("="*70)

    # Load task
    with open("data/arc_tasks/training/0d3d703e.json") as f:
        data = json.load(f)

    for i, example in enumerate(data['train'][:2]):  # First 2 examples
        print(f"\nExample {i+1}:")

        inp = ARCGrid.from_list(example['input'])
        out = ARCGrid.from_list(example['output'])

        print(f"  Input shape: {inp.shape}")
        print(f"  Output shape: {out.shape}")
        print(f"  Shapes match: {inp.shape == out.shape}")

        # Try to build mapping
        mapping = {}
        inconsistent = False

        for row in range(inp.height):
            for col in range(inp.width):
                in_color = int(inp.data[row, col])
                out_color = int(out.data[row, col])

                if in_color in mapping:
                    if mapping[in_color] != out_color:
                        print(f"  ❌ Inconsistent mapping at ({row},{col}): {in_color} → {mapping[in_color]} vs {out_color}")
                        inconsistent = True
                else:
                    mapping[in_color] = out_color

        print(f"  Mapping: {mapping}")
        print(f"  Consistent: {not inconsistent}")


def debug_marker_color():
    """Debug marker color detection."""
    print("\n" + "="*70)
    print("MARKER COLOR DEBUG - Task 0520fde7")
    print("="*70)

    # Load task
    with open("data/arc_tasks/training/0520fde7.json") as f:
        data = json.load(f)

    for i, example in enumerate(data['train'][:2]):  # First 2 examples
        print(f"\nExample {i+1}:")

        inp = ARCGrid.from_list(example['input'])

        print(f"  Shape: {inp.shape}")
        print(f"  Unique colors: {inp.get_unique_colors()}")

        total_pixels = inp.height * inp.width

        for color in inp.get_unique_colors():
            count = inp.count_color(color)
            freq = count / total_pixels
            print(f"  Color {color}: {count} pixels ({freq*100:.1f}%)")

        # Check which colors are sparse
        sparse_colors = []
        for color in inp.get_unique_colors():
            if color == 0:
                continue
            count = inp.count_color(color)
            freq = count / total_pixels
            if freq < 0.1:
                sparse_colors.append((color, freq))

        print(f"  Sparse colors (< 10%): {sparse_colors}")


if __name__ == "__main__":
    debug_color_map_manual()
    debug_marker_color()
