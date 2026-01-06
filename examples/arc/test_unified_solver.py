"""Test unified task solver on all 11 evaluation tasks.

Tests the complete system with parameter inference and composition search.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supe.reasoning.arc.task_solver import ARCTaskSolver


def main():
    """Test unified solver on all tasks."""
    print("\n" + "="*70)
    print("TESTING UNIFIED ARC TASK SOLVER")
    print("="*70)
    print("\nFeatures:")
    print("  • Automatic parameter inference")
    print("  • Composition search (up to 4 steps)")
    print("  • Known pattern matching")
    print("  • Multi-example validation")

    # Load task files
    task_files = [
        "data/arc_tasks/training/0520fde7.json",  # Already solved
        "data/arc_tasks/training/007bbfb7.json",
        "data/arc_tasks/training/00d62c1b.json",
        "data/arc_tasks/training/025d127b.json",
        "data/arc_tasks/training/0d3d703e.json",  # Already solved
        "data/arc_tasks/training/1e0a9b12.json",
        "data/arc_tasks/training/28bf18c6.json",  # Already solved
        "data/arc_tasks/training/3c9b0459.json",
        "data/arc_tasks/training/6d0160f0.json",
        "data/arc_tasks/training/a85d4709.json",
        "data/arc_tasks/training/ae3edfdc.json",
    ]

    task_files = [Path(f) for f in task_files if Path(f).exists()]

    print(f"\nTesting on {len(task_files)} tasks")

    # Create solver
    solver = ARCTaskSolver()

    # Evaluate
    results = solver.evaluate_on_tasks(task_files, verbose=True)

    # Detailed summary
    print("\n" + "="*70)
    print("DETAILED RESULTS")
    print("="*70)

    print("\n✅ SOLVED TASKS:")
    for task_id, status in results['solutions'].items():
        if status == 'SOLVED':
            print(f"  • {task_id}")

    print("\n⚠️  PARTIAL SOLUTIONS:")
    for task_id, status in results['solutions'].items():
        if status == 'PARTIAL':
            print(f"  • {task_id}")

    print("\n❌ UNSOLVED TASKS:")
    for task_id, status in results['solutions'].items():
        if status == 'UNSOLVED':
            print(f"  • {task_id}")

    # Final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)

    total = results['total_tasks']
    solved = results['solved_tasks']
    partial = results['partial_solutions']
    unsolved = results['no_solution']

    print(f"\nTotal Tasks:       {total}")
    print(f"Solved:            {solved} ({solved/total*100:.1f}%)")
    print(f"Partial Solutions: {partial}")
    print(f"No Solution:       {unsolved}")

    print("\n" + "="*70)

    if solved >= 5:
        print("🎉 EXCELLENT! Reached 45%+ solve rate target!")
    elif solved >= 4:
        print("✅ GOOD! Significant improvement achieved!")
    elif solved >= 3:
        print("📊 Progress made, more work needed")
    else:
        print("⚠️  Need to improve search strategies")

    print("="*70 + "\n")


if __name__ == "__main__":
    main()
