"""Analyze objects in task 025d127b."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import numpy as np
from supe.reasoning.arc.grid import ARCGrid

def find_objects(grid, color):
    """Find connected components of a color."""
    visited = set()
    objects = []

    for i in range(grid.height):
        for j in range(grid.width):
            if (i, j) in visited or grid.data[i, j] != color:
                continue

            # BFS to find connected component
            obj_pixels = []
            queue = [(i, j)]

            while queue:
                r, c = queue.pop(0)
                if (r, c) in visited:
                    continue
                if r < 0 or r >= grid.height or c < 0 or c >= grid.width:
                    continue
                if grid.data[r, c] != color:
                    continue

                visited.add((r, c))
                obj_pixels.append((r, c))

                # 4-connected neighbors
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    queue.append((r + dr, c + dc))

            if obj_pixels:
                objects.append(obj_pixels)

    return objects

def main():
    with open("data/arc_tasks/training/025d127b.json") as f:
        data = json.load(f)

    inp = ARCGrid.from_list(data['train'][0]['input'])
    out = ARCGrid.from_list(data['train'][0]['output'])

    print("Input objects:")
    for color in [6, 2]:
        objs = find_objects(inp, color)
        print(f"\n  Color {color}: {len(objs)} object(s)")
        for idx, obj in enumerate(objs):
            cols = [c for r, c in obj]
            rows = [r for r, c in obj]
            min_col, max_col = min(cols), max(cols)
            min_row, max_row = min(rows), max(rows)
            center_col = (min_col + max_col) / 2
            print(f"    Object {idx}: bbox=({min_row},{min_col})-({max_row},{max_col}), center_col={center_col:.1f}")

    print("\n\nOutput objects:")
    for color in [6, 2]:
        objs = find_objects(out, color)
        print(f"\n  Color {color}: {len(objs)} object(s)")
        for idx, obj in enumerate(objs):
            cols = [c for r, c in obj]
            rows = [r for r, c in obj]
            min_col, max_col = min(cols), max(cols)
            min_row, max_row = min(rows), max(rows)
            center_col = (min_col + max_col) / 2
            print(f"    Object {idx}: bbox=({min_row},{min_col})-({max_row},{max_col}), center_col={center_col:.1f}")

if __name__ == "__main__":
    main()
