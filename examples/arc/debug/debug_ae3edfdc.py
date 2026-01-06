"""Debug task ae3edfdc - cross pattern with association."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import numpy as np
from supe.reasoning.arc.grid import ARCGrid

def main():
    print("\n" + "="*70)
    print("DEBUGGING TASK ae3edfdc - Cross Pattern")
    print("="*70)

    with open("data/arc_tasks/training/ae3edfdc.json") as f:
        data = json.load(f)

    train_inputs = []
    train_outputs = []
    for example in data['train']:
        train_inputs.append(ARCGrid.from_list(example['input']))
        train_outputs.append(ARCGrid.from_list(example['output']))

    print(f"\nLoaded {len(train_inputs)} training examples")

    # Analyze first example
    inp = train_inputs[0]
    out = train_outputs[0]

    print(f"\nExample 1:")
    print(f"  Input shape: {inp.shape}")
    print(f"  Output shape: {out.shape}")
    print(f"  Input colors: {sorted(inp.get_unique_colors())}")
    print(f"  Output colors: {sorted(out.get_unique_colors())}")

    # Find non-zero pixels in input
    print(f"\n  Input non-zero pixels:")
    for color in sorted(inp.get_unique_colors()):
        if color != 0:
            positions = np.argwhere(inp.data == color)
            print(f"    Color {color}: {len(positions)} pixels at {list(map(tuple, positions))}")

    # Find non-zero pixels in output
    print(f"\n  Output non-zero pixels:")
    for color in sorted(out.get_unique_colors()):
        if color != 0:
            positions = np.argwhere(out.data == color)
            print(f"    Color {color}: {len(positions)} pixels")
            if len(positions) <= 20:
                print(f"      Positions: {list(map(tuple, positions))}")

    # Show a section of the grids
    print(f"\n  Input grid around row 4:")
    for i in range(max(0, 4-2), min(inp.height, 4+3)):
        print(f"    Row {i:2d}: {list(inp.data[i, :])}")

    print(f"\n  Output grid around row 4:")
    for i in range(max(0, 4-2), min(out.height, 4+3)):
        print(f"    Row {i:2d}: {list(out.data[i, :])}")

if __name__ == "__main__":
    main()
