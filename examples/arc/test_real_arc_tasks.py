"""Test ARC System on Real ARC-AGI Tasks

This script loads real tasks from the official ARC-AGI dataset
and evaluates our system's performance on them.
"""

import json
from pathlib import Path
from supe.reasoning.arc import (
    ARCGrid,
    ARCTask,
    ARCCapability,
    print_grid,
)


def load_arc_task_from_json(json_path: str) -> ARCTask:
    """Load an ARC task from official JSON format."""
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Convert training examples
    train = []
    for example in data['train']:
        input_grid = ARCGrid.from_list(example['input'])
        output_grid = ARCGrid.from_list(example['output'])
        train.append((input_grid, output_grid))

    # Convert test examples
    test_inputs = []
    test_outputs = []
    for example in data['test']:
        test_inputs.append(ARCGrid.from_list(example['input']))
        test_outputs.append(ARCGrid.from_list(example['output']))

    task_id = Path(json_path).stem

    return ARCTask(
        train=train,
        test_inputs=test_inputs,
        test_outputs=test_outputs,
        task_id=task_id,
    )


def visualize_task(task: ARCTask, max_examples: int = 2):
    """Visualize training and test examples."""
    print(f"\n{'='*70}")
    print(f"Task: {task.task_id}")
    print(f"{'='*70}")

    print(f"\nTraining Examples: {len(task.train)}")
    for i, (inp, out) in enumerate(task.train[:max_examples]):
        print(f"\n  Example {i+1}:")
        print_grid(inp, title=f"    Input ({inp.height}x{inp.width})")
        print_grid(out, title=f"    Output ({out.height}x{out.width})")

    if len(task.train) > max_examples:
        print(f"\n  ... and {len(task.train) - max_examples} more examples")

    print(f"\nTest Cases: {len(task.test_inputs)}")
    for i, test_input in enumerate(task.test_inputs[:1]):
        print(f"\n  Test {i+1}:")
        print_grid(test_input, title=f"    Input ({test_input.height}x{test_input.width})")


def test_single_task(task: ARCTask, capability: ARCCapability, verbose: bool = False):
    """Test system on a single task."""
    print(f"\n{'='*70}")
    print(f"Attempting to solve: {task.task_id}")
    print(f"{'='*70}")

    # Show task structure
    print(f"Training examples: {len(task.train)}")
    print(f"Test cases: {len(task.test_inputs)}")

    # Analyze input/output patterns
    if task.train:
        inp, out = task.train[0]
        print(f"Input size: {inp.height}x{inp.width}")
        print(f"Output size: {out.height}x{out.width}")
        print(f"Size change: {inp.height}x{inp.width} → {out.height}x{out.width}")

    # Attempt to solve
    print(f"\nSynthesizing program...")
    result = capability(task, verbose=verbose)

    print(f"\n{'='*70}")
    print(f"RESULT: {'✓ SUCCESS' if result.success else '✗ FAILED'}")
    print(f"{'='*70}")

    if result.success:
        print(f"\nProgram: {result.explanation}")
        print(f"Confidence: {result.confidence:.0%}")
        print(f"Time: {result.synthesis_time:.3f}s")

        # Check accuracy if we have ground truth
        if task.test_outputs:
            correct = 0
            for i, (pred, truth) in enumerate(zip(result.predictions, task.test_outputs)):
                if pred and pred.equals(truth):
                    correct += 1
                    status = "✓ CORRECT"
                else:
                    status = "✗ INCORRECT"
                print(f"\n  Test {i+1}: {status}")

            accuracy = correct / len(task.test_outputs)
            print(f"\nTest Accuracy: {accuracy:.0%} ({correct}/{len(task.test_outputs)})")

        # Show first prediction
        if result.predictions:
            print(f"\n  Predicted Output (Test 1):")
            print_grid(result.predictions[0], title=f"    Prediction ({result.predictions[0].height}x{result.predictions[0].width})")

            if task.test_outputs:
                print(f"\n  Ground Truth (Test 1):")
                print_grid(task.test_outputs[0], title=f"    Expected ({task.test_outputs[0].height}x{task.test_outputs[0].width})")
    else:
        print(f"\nReason: {result.explanation}")

    return result


def main():
    """Run tests on real ARC tasks."""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  Testing ARC System on Real ARC-AGI Tasks".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)

    # Initialize capability
    print("\nInitializing ARC capability...")
    capability = ARCCapability(
        max_depth=3,
        beam_width=5,
        enable_learning=True,
    )
    print("✓ Ready")

    # Find all downloaded tasks
    task_dir = Path("data/arc_tasks/training")
    task_files = sorted(task_dir.glob("*.json"))

    if not task_files:
        print("\n✗ No task files found!")
        print("Expected tasks in: data/arc_tasks/training/")
        return

    print(f"\nFound {len(task_files)} tasks to evaluate")

    # Test each task
    results = []
    for i, task_file in enumerate(task_files, 1):
        print(f"\n{'█'*70}")
        print(f"█ Task {i}/{len(task_files)}: {task_file.stem}")
        print(f"{'█'*70}")

        # Load task
        task = load_arc_task_from_json(task_file)

        # Visualize (first 2 training examples)
        visualize_task(task, max_examples=2)

        # Attempt to solve
        result = test_single_task(task, capability, verbose=False)
        results.append((task.task_id, result))

    # Summary
    print(f"\n{'='*70}")
    print("EVALUATION SUMMARY")
    print(f"{'='*70}")

    solved = sum(1 for _, r in results if r.success)
    total = len(results)

    print(f"\nTasks Evaluated: {total}")
    print(f"Tasks Solved: {solved}")
    print(f"Solve Rate: {solved/total:.1%}")

    print(f"\nDetailed Results:")
    for task_id, result in results:
        status = "✓" if result.success else "✗"
        time_str = f"{result.synthesis_time:.3f}s" if result.success else "N/A"
        print(f"  {status} {task_id}: {time_str}")

    # Statistics
    stats = capability.get_statistics()
    print(f"\nCapability Statistics:")
    print(f"  Solution library: {stats['solution_library_size']} programs")
    print(f"  Avg synthesis time: {stats['avg_synthesis_time']:.3f}s")

    print(f"\n{'='*70}")
    print(f"✓ EVALUATION COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
