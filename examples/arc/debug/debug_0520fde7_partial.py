"""Debug why 0520fde7 is only partial."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from supe.reasoning.arc.grid import ARCGrid
from supe.reasoning.arc.task_solver import ARCTaskSolver


def main():
    print("\n" + "="*70)
    print("DEBUGGING TASK 0520fde7 - Extract+Compare+Conditional")
    print("="*70)

    # Load task
    with open("data/arc_tasks/training/0520fde7.json") as f:
        data = json.load(f)

    # Create solver
    solver = ARCTaskSolver()

    # Get solution
    solution = solver.solve_task(data, "0520fde7")

    if not solution:
        print("\n❌ No solution found!")
        return

    print(f"\n✅ Found solution: {solution.solution}")
    print(f"   Confidence: {solution.solution.confidence:.2f}")
    print(f"   Steps: {len(solution.solution.steps)}")

    for i, step in enumerate(solution.solution.steps):
        print(f"   Step {i+1}: {step.transformation_name}")
        print(f"     Params: {step.parameters}")

    print(f"\n📊 Training validation: {solution.solution.validation_results}")
    print(f"📊 Test validation: {solution.test_results}")

    print(f"\n{'='*70}")

    if solution.is_complete():
        print("✅ COMPLETE SOLUTION")
    else:
        print("⚠️  PARTIAL SOLUTION - Test examples failed")
        print(f"   Training: {sum(solution.solution.validation_results)}/{len(solution.solution.validation_results)}")
        print(f"   Test: {sum(solution.test_results)}/{len(solution.test_results)}")

        # Try to see what went wrong on test
        print("\n🔍 Analyzing test failure...")
        for i, test_example in enumerate(data['test']):
            test_input = ARCGrid.from_list(test_example['input'])
            expected_output = ARCGrid.from_list(test_example['output'])

            result = solver.composition_search.apply_solution(
                solution.solution,
                test_input,
                output_grid=expected_output
            )

            print(f"\n   Test {i+1}:")
            print(f"     Input shape: {test_input.shape}")
            print(f"     Expected shape: {expected_output.shape}")

            if result:
                print(f"     Result shape: {result.shape}")
                matches = (result.data == expected_output.data).all()
                print(f"     Matches: {matches}")

                if not matches:
                    diff_count = (result.data != expected_output.data).sum()
                    print(f"     Differences: {diff_count} pixels")
            else:
                print(f"     Result: None (transformation failed)")


if __name__ == "__main__":
    main()
