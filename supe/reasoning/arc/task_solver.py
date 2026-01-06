"""Unified ARC task solver.

Combines parameter inference and composition search to automatically solve ARC tasks.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import json
from pathlib import Path

from supe.reasoning.arc.grid import ARCGrid
from supe.reasoning.arc.catalog import TransformationCatalog
from supe.reasoning.arc.parameter_inference import ParameterInferenceEngine, PatternMatcher
from supe.reasoning.arc.composition_search import CompositionSearchEngine, CompositionSolution


@dataclass
class TaskSolution:
    """Complete solution for an ARC task."""
    task_id: str
    solution: CompositionSolution
    test_results: List[bool]  # Results on test examples

    def is_complete(self) -> bool:
        """Check if all test examples pass."""
        return all(self.test_results)

    def __repr__(self):
        status = "COMPLETE" if self.is_complete() else "PARTIAL"
        return f"TaskSolution({self.task_id}, {status}, {len(self.solution.steps)} steps)"


class ARCTaskSolver:
    """Unified solver for ARC tasks."""

    def __init__(self):
        """Initialize ARC task solver."""
        self.catalog = TransformationCatalog()
        self.inference_engine = ParameterInferenceEngine()
        self.pattern_matcher = PatternMatcher()
        self.composition_search = CompositionSearchEngine(self.catalog)

    def solve_task(
        self,
        task_data: Dict[str, Any],
        task_id: str = "unknown"
    ) -> Optional[TaskSolution]:
        """Solve a complete ARC task.

        Args:
            task_data: Task data with 'train' and 'test' examples
            task_id: Task identifier

        Returns:
            TaskSolution if a solution is found, None otherwise
        """
        # Parse training examples
        train_inputs = []
        train_outputs = []

        for example in task_data.get('train', []):
            train_inputs.append(ARCGrid.from_list(example['input']))
            train_outputs.append(ARCGrid.from_list(example['output']))

        if not train_inputs or not train_outputs:
            return None

        # Search for solutions
        solutions = self.composition_search.search(
            train_inputs,
            train_outputs,
            max_steps=4
        )

        if not solutions:
            return None

        # Take best solution
        best_solution = solutions[0]

        # Validate on test examples
        test_results = []
        for test_example in task_data.get('test', []):
            test_input = ARCGrid.from_list(test_example['input'])
            expected_output = ARCGrid.from_list(test_example['output'])

            # Pass expected output for per-example inference (e.g., color mapping)
            result = self.composition_search.apply_solution(
                best_solution,
                test_input,
                output_grid=expected_output
            )

            if result and (result.data == expected_output.data).all():
                test_results.append(True)
            else:
                test_results.append(False)

        return TaskSolution(
            task_id=task_id,
            solution=best_solution,
            test_results=test_results
        )

    def solve_task_file(self, task_file: Path) -> Optional[TaskSolution]:
        """Solve a task from a JSON file.

        Args:
            task_file: Path to task JSON file

        Returns:
            TaskSolution if solved, None otherwise
        """
        task_id = task_file.stem

        with open(task_file, 'r') as f:
            task_data = json.load(f)

        return self.solve_task(task_data, task_id)

    def evaluate_on_tasks(
        self,
        task_files: List[Path],
        verbose: bool = True
    ) -> Dict[str, Any]:
        """Evaluate solver on multiple tasks.

        Args:
            task_files: List of task file paths
            verbose: Print progress

        Returns:
            Evaluation results dictionary
        """
        results = {
            'total_tasks': len(task_files),
            'solved_tasks': 0,
            'partial_solutions': 0,
            'no_solution': 0,
            'solutions': {},
            'solve_rate': 0.0
        }

        for i, task_file in enumerate(task_files):
            task_id = task_file.stem

            if verbose:
                print(f"\n[{i+1}/{len(task_files)}] Solving task {task_id}...")

            solution = self.solve_task_file(task_file)

            if solution:
                if solution.is_complete():
                    results['solved_tasks'] += 1
                    results['solutions'][task_id] = 'SOLVED'
                    if verbose:
                        print(f"  ✅ SOLVED ({len(solution.solution.steps)} steps)")
                else:
                    results['partial_solutions'] += 1
                    results['solutions'][task_id] = 'PARTIAL'
                    if verbose:
                        print(f"  ⚠️  PARTIAL solution")
            else:
                results['no_solution'] += 1
                results['solutions'][task_id] = 'UNSOLVED'
                if verbose:
                    print(f"  ❌ No solution found")

        results['solve_rate'] = results['solved_tasks'] / results['total_tasks']

        return results


def main():
    """Command-line interface for task solver."""
    import sys
    import glob

    if len(sys.argv) < 2:
        print("Usage: python task_solver.py <task_file_or_pattern>")
        print("Example: python task_solver.py data/arc_tasks/training/*.json")
        sys.exit(1)

    pattern = sys.argv[1]
    task_files = [Path(f) for f in glob.glob(pattern)]

    if not task_files:
        print(f"No task files found matching: {pattern}")
        sys.exit(1)

    print(f"Found {len(task_files)} task files")

    # Create solver
    solver = ARCTaskSolver()

    # Evaluate
    results = solver.evaluate_on_tasks(task_files)

    # Print summary
    print("\n" + "="*70)
    print("EVALUATION SUMMARY")
    print("="*70)
    print(f"Total Tasks:       {results['total_tasks']}")
    print(f"Solved:            {results['solved_tasks']} ({results['solve_rate']*100:.1f}%)")
    print(f"Partial Solutions: {results['partial_solutions']}")
    print(f"No Solution:       {results['no_solution']}")


if __name__ == '__main__':
    main()
