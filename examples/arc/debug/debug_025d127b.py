"""Debug task 025d127b - object alignment."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import numpy as np
from supe.reasoning.arc.grid import ARCGrid

def main():
    print("\n" + "="*70)
    print("DEBUGGING TASK 025d127b - Object Alignment")
    print("="*70)

    # Load task
    with open("data/arc_tasks/training/025d127b.json") as f:
        data = json.load(f)

    # Parse training examples
    train_inputs = []
    train_outputs = []
    for example in data['train']:
        train_inputs.append(ARCGrid.from_list(example['input']))
        train_outputs.append(ARCGrid.from_list(example['output']))

    print(f"\nLoaded {len(train_inputs)} training examples")

    # Analyze first example in detail
    inp = train_inputs[0]
    out = train_outputs[0]

    print(f"\nExample 1 (first 10 rows):")
    print(f"  Input shape: {inp.shape}")
    print(f"  Output shape: {out.shape}")

    # Find non-zero objects in input
    print(f"\n  Input (first 10 rows):")
    for i in range(min(10, inp.height)):
        row = list(inp.data[i, :])
        print(f"    Row {i:2d}: {row}")

    print(f"\n  Output (first 10 rows):")
    for i in range(min(10, out.height)):
        row = list(out.data[i, :])
        print(f"    Row {i:2d}: {row}")

    # Find differences
    print(f"\n  Analysis:")
    for color in [2, 6]:  # Non-background colors
        if color in inp.get_unique_colors():
            # Find positions in input
            inp_positions = np.argwhere(inp.data == color)
            out_positions = np.argwhere(out.data == color)

            if len(inp_positions) > 0 and len(out_positions) > 0:
                inp_center = inp_positions.mean(axis=0)
                out_center = out_positions.mean(axis=0)
                offset = out_center - inp_center

                print(f"    Color {color}:")
                print(f"      Input center: ({inp_center[0]:.1f}, {inp_center[1]:.1f})")
                print(f"      Output center: ({out_center[0]:.1f}, {out_center[1]:.1f})")
                print(f"      Offset: ({offset[0]:.1f}, {offset[1]:.1f})")

if __name__ == "__main__":
    main()
