"""Debug task a85d4709 - marker-based row coloring."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import numpy as np
from supe.reasoning.arc.grid import ARCGrid

def main():
    print("\n" + "="*70)
    print("DEBUGGING TASK a85d4709 - Marker-Based Row Coloring")
    print("="*70)

    # Load task
    with open("data/arc_tasks/training/a85d4709.json") as f:
        data = json.load(f)

    # Parse training examples
    train_inputs = []
    train_outputs = []
    for example in data['train']:
        train_inputs.append(ARCGrid.from_list(example['input']))
        train_outputs.append(ARCGrid.from_list(example['output']))

    print(f"\nLoaded {len(train_inputs)} training examples")

    # Analyze all examples
    for i, (inp, out) in enumerate(zip(train_inputs, train_outputs)):
        print(f"\n{'='*60}")
        print(f"Example {i+1}:")
        print(f"  Input shape: {inp.shape}")
        print(f"  Output shape: {out.shape}")
        print(f"  Input colors: {sorted(inp.get_unique_colors())}")
        print(f"  Output colors: {sorted(out.get_unique_colors())}")

        print(f"\n  Input grid:")
        for r in range(inp.height):
            row_data = list(inp.data[r, :])
            marker_pos = [j for j, v in enumerate(row_data) if v == 5]
            marker_info = f" (marker at col {marker_pos[0]})" if marker_pos else ""
            print(f"    Row {r}: {row_data}{marker_info}")

        print(f"\n  Output grid:")
        for r in range(out.height):
            row_data = list(out.data[r, :])
            unique = set(row_data)
            color_info = f" (all {list(unique)[0]})" if len(unique) == 1 else ""
            print(f"    Row {r}: {row_data}{color_info}")

        # Analyze the pattern
        print(f"\n  Pattern analysis:")
        for r in range(inp.height):
            input_row = inp.data[r, :]
            output_row = out.data[r, :]

            # Find marker position
            marker_positions = np.where(input_row == 5)[0]
            if len(marker_positions) > 0:
                marker_col = marker_positions[0]
                output_color = output_row[0]  # All pixels in output row have same color
                print(f"    Row {r}: marker at col {marker_col} → row colored with {output_color}")

if __name__ == "__main__":
    main()
