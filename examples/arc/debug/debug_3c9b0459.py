"""Debug task 3c9b0459 - rotation detection."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import numpy as np
from supe.reasoning.arc.grid import ARCGrid
from supe.reasoning.arc.catalog import TransformationCatalog

def main():
    print("\n" + "="*70)
    print("DEBUGGING TASK 3c9b0459 - Rotation Pattern")
    print("="*70)

    # Load task
    with open("data/arc_tasks/training/3c9b0459.json") as f:
        data = json.load(f)

    # Parse training examples
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

    print(f"\n  Input grid:")
    for i in range(inp.height):
        print(f"    {list(inp.data[i, :])}")

    print(f"\n  Output grid:")
    for i in range(out.height):
        print(f"    {list(out.data[i, :])}")

    # Test rotation transformations
    catalog = TransformationCatalog()
    rotate_transform = catalog.get('rotate')

    print(f"\n  Testing rotations:")
    for angle in [90, 180, 270]:
        result = rotate_transform.apply(inp, angle=angle)
        if result.success:
            matches = (result.output_grid.data == out.data).all()
            if matches:
                print(f"    ✅ MATCH: {angle}° rotation")
            else:
                diff = (result.output_grid.data != out.data).sum()
                print(f"    ❌ {angle}°: {diff} differences")

    # Test flip transformations
    flip_transform = catalog.get('flip')
    print(f"\n  Testing flips:")
    for direction in ['horizontal', 'vertical']:
        result = flip_transform.apply(inp, direction=direction)
        if result.success:
            matches = (result.output_grid.data == out.data).all()
            if matches:
                print(f"    ✅ MATCH: {direction} flip")
            else:
                diff = (result.output_grid.data != out.data).sum()
                print(f"    ❌ {direction}: {diff} differences")

    # Test all examples
    print(f"\n  Testing 180° rotation on all examples:")
    for i, (inp, out) in enumerate(zip(train_inputs, train_outputs)):
        result = rotate_transform.apply(inp, angle=180)
        if result.success:
            matches = (result.output_grid.data == out.data).all()
            if matches:
                print(f"    Example {i+1}: ✅ MATCH")
            else:
                diff = (result.output_grid.data != out.data).sum()
                print(f"    Example {i+1}: ❌ {diff} differences")

if __name__ == "__main__":
    main()
