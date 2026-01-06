"""Analyze remaining 5 unsolved tasks to understand what patterns they need."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import numpy as np
from supe.reasoning.arc.grid import ARCGrid

def analyze_task(task_file):
    """Analyze a single task."""
    task_id = task_file.stem
    print(f"\n{'='*70}")
    print(f"TASK {task_id}")
    print(f"{'='*70}")

    with open(task_file) as f:
        data = json.load(f)

    train_examples = data['train']
    print(f"\nTraining examples: {len(train_examples)}")

    # Analyze first training example
    if train_examples:
        ex = train_examples[0]
        inp = ARCGrid.from_list(ex['input'])
        out = ARCGrid.from_list(ex['output'])

        print(f"\nExample 1:")
        print(f"  Input shape: {inp.shape}")
        print(f"  Output shape: {out.shape}")
        print(f"  Input colors: {sorted(inp.get_unique_colors())}")
        print(f"  Output colors: {sorted(out.get_unique_colors())}")

        print(f"\n  Input grid:")
        for i in range(inp.height):
            print(f"    {list(inp.data[i, :])}")

        print(f"\n  Output grid:")
        for i in range(out.height):
            print(f"    {list(out.data[i, :])}")

        # Shape analysis
        if inp.shape == out.shape:
            print(f"\n  Same shape → likely in-place transformation")
        elif out.height > inp.height or out.width > inp.width:
            print(f"\n  Output larger → likely tiling/scaling/duplication")
        else:
            print(f"\n  Output smaller → likely cropping/extraction")

        # Color analysis
        if len(out.get_unique_colors()) > len(inp.get_unique_colors()):
            print(f"  More colors in output → likely color addition/mapping")
        elif len(out.get_unique_colors()) < len(inp.get_unique_colors()):
            print(f"  Fewer colors in output → likely color reduction/merging")

def main():
    unsolved_tasks = [
        "025d127b",  # Object translation
        "3c9b0459",  # Unknown
        "6d0160f0",  # Grid sectioning
        "a85d4709",  # Conditional row coloring
        "ae3edfdc",  # Object association + pattern
    ]

    for task_id in unsolved_tasks:
        task_file = Path(f"data/arc_tasks/training/{task_id}.json")
        if task_file.exists():
            analyze_task(task_file)
        else:
            print(f"\n❌ Task file not found: {task_file}")

if __name__ == "__main__":
    main()
