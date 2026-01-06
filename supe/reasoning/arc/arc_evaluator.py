"""Evaluation harness for ARC-AGI benchmark.

This module provides tools for evaluating ARC capabilities on the official
ARC benchmark and custom test sets.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import time

from supe.reasoning.arc.arc_capability import ARCTask, ARCResult, ARCCapability
from supe.reasoning.arc import ARCGrid


@dataclass
class TaskResult:
    """Result from evaluating a single task."""
    task_id: str
    success: bool
    predictions: List[Optional[ARCGrid]]
    ground_truth: Optional[List[ARCGrid]]
    correct: Optional[List[bool]]  # Per-test correctness
    program_explanation: str
    confidence: float
    synthesis_time: float
    error: Optional[str] = None

    def accuracy(self) -> float:
        """Calculate per-test accuracy."""
        if not self.correct:
            return 0.0
        return sum(self.correct) / len(self.correct) if self.correct else 0.0


@dataclass
class EvaluationResults:
    """Results from evaluating on multiple tasks."""
    task_results: List[TaskResult]
    total_tasks: int
    solved_tasks: int
    total_tests: int
    correct_tests: int
    total_time: float
    capability_stats: Dict[str, Any]

    def solve_rate(self) -> float:
        """Task-level solve rate (all tests correct)."""
        return self.solved_tasks / self.total_tasks if self.total_tasks > 0 else 0.0

    def test_accuracy(self) -> float:
        """Test-level accuracy (per-test correctness)."""
        return self.correct_tests / self.total_tests if self.total_tests > 0 else 0.0

    def avg_time_per_task(self) -> float:
        """Average synthesis time per task."""
        return self.total_time / self.total_tasks if self.total_tasks > 0 else 0.0

    def summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            "total_tasks": self.total_tasks,
            "solved_tasks": self.solved_tasks,
            "solve_rate": self.solve_rate(),
            "total_tests": self.total_tests,
            "correct_tests": self.correct_tests,
            "test_accuracy": self.test_accuracy(),
            "total_time": self.total_time,
            "avg_time_per_task": self.avg_time_per_task(),
            **self.capability_stats,
        }


class ARCEvaluator:
    """Evaluator for ARC benchmark tasks."""

    def __init__(self, capability: ARCCapability):
        """Initialize evaluator with ARC capability.

        Args:
            capability: The ARC capability to evaluate
        """
        self.capability = capability

    def evaluate_task(
        self,
        task: ARCTask,
        check_correctness: bool = True,
        verbose: bool = False,
    ) -> TaskResult:
        """Evaluate capability on a single task.

        Args:
            task: The ARC task to evaluate
            check_correctness: Whether to check against ground truth
            verbose: Print progress

        Returns:
            TaskResult with evaluation metrics
        """
        try:
            # Solve task
            result = self.capability(task, verbose=verbose)

            # Check correctness if ground truth available
            correct = None
            if check_correctness and task.test_outputs:
                correct = []
                for pred, truth in zip(result.predictions, task.test_outputs):
                    if pred is None:
                        correct.append(False)
                    else:
                        correct.append(pred.equals(truth))

            return TaskResult(
                task_id=task.task_id,
                success=result.success,
                predictions=result.predictions,
                ground_truth=task.test_outputs,
                correct=correct,
                program_explanation=result.explanation,
                confidence=result.confidence,
                synthesis_time=result.synthesis_time,
            )

        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                predictions=[None] * len(task.test_inputs),
                ground_truth=task.test_outputs,
                correct=[False] * len(task.test_inputs) if task.test_outputs else None,
                program_explanation="",
                confidence=0.0,
                synthesis_time=0.0,
                error=str(e),
            )

    def evaluate_tasks(
        self,
        tasks: List[ARCTask],
        verbose: bool = False,
        print_progress: bool = True,
    ) -> EvaluationResults:
        """Evaluate capability on multiple tasks.

        Args:
            tasks: List of ARC tasks to evaluate
            verbose: Print synthesis progress for each task
            print_progress: Print evaluation progress

        Returns:
            EvaluationResults with aggregate metrics
        """
        task_results = []
        total_time = 0.0
        total_tests = 0
        correct_tests = 0

        for i, task in enumerate(tasks):
            if print_progress:
                print(f"\n[{i+1}/{len(tasks)}] Evaluating task {task.task_id}...")

            result = self.evaluate_task(task, check_correctness=True, verbose=verbose)
            task_results.append(result)

            total_time += result.synthesis_time

            if result.correct:
                total_tests += len(result.correct)
                correct_tests += sum(result.correct)

            if print_progress:
                if result.success:
                    accuracy = result.accuracy() if result.correct else 1.0
                    print(f"  ✓ Solved (accuracy: {accuracy:.0%}, time: {result.synthesis_time:.2f}s)")
                elif result.error:
                    print(f"  ✗ Error: {result.error}")
                else:
                    print(f"  ✗ Failed (confidence: {result.confidence:.0%}, time: {result.synthesis_time:.2f}s)")

        solved_tasks = sum(1 for r in task_results if r.success and (r.accuracy() == 1.0 if r.correct else True))

        return EvaluationResults(
            task_results=task_results,
            total_tasks=len(tasks),
            solved_tasks=solved_tasks,
            total_tests=total_tests,
            correct_tests=correct_tests,
            total_time=total_time,
            capability_stats=self.capability.get_statistics(),
        )

    def evaluate_directory(
        self,
        directory: Path,
        pattern: str = "*.json",
        max_tasks: Optional[int] = None,
        verbose: bool = False,
        print_progress: bool = True,
    ) -> EvaluationResults:
        """Evaluate on all tasks in a directory.

        Args:
            directory: Directory containing ARC task JSON files
            pattern: File pattern to match (default: *.json)
            max_tasks: Maximum number of tasks to evaluate (None = all)
            verbose: Print synthesis progress
            print_progress: Print evaluation progress

        Returns:
            EvaluationResults
        """
        # Load tasks
        task_files = sorted(Path(directory).glob(pattern))
        if max_tasks:
            task_files = task_files[:max_tasks]

        if print_progress:
            print(f"Loading {len(task_files)} tasks from {directory}")

        tasks = []
        for task_file in task_files:
            try:
                with open(task_file) as f:
                    data = json.load(f)
                    task = ARCTask.from_dict(data)
                    task.task_id = task.task_id or task_file.stem
                    tasks.append(task)
            except Exception as e:
                if print_progress:
                    print(f"  Warning: Failed to load {task_file}: {e}")

        # Evaluate
        return self.evaluate_tasks(tasks, verbose=verbose, print_progress=print_progress)

    def print_summary(self, results: EvaluationResults):
        """Print evaluation summary.

        Args:
            results: Evaluation results to summarize
        """
        print("\n" + "="*70)
        print("ARC EVALUATION SUMMARY")
        print("="*70)

        print(f"\nTask Performance:")
        print(f"  Total tasks: {results.total_tasks}")
        print(f"  Solved tasks: {results.solved_tasks}")
        print(f"  Solve rate: {results.solve_rate():.1%}")

        print(f"\nTest Performance:")
        print(f"  Total tests: {results.total_tests}")
        print(f"  Correct tests: {results.correct_tests}")
        print(f"  Test accuracy: {results.test_accuracy():.1%}")

        print(f"\nTiming:")
        print(f"  Total time: {results.total_time:.1f}s")
        print(f"  Avg per task: {results.avg_time_per_task():.2f}s")

        print(f"\nCapability Statistics:")
        for key, value in results.capability_stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")

        print("="*70)

    def save_results(self, results: EvaluationResults, filepath: Path):
        """Save evaluation results to JSON file.

        Args:
            results: Results to save
            filepath: Output file path
        """
        data = {
            "summary": results.summary(),
            "tasks": [
                {
                    "task_id": r.task_id,
                    "success": r.success,
                    "accuracy": r.accuracy() if r.correct else None,
                    "program": r.program_explanation,
                    "confidence": r.confidence,
                    "synthesis_time": r.synthesis_time,
                    "error": r.error,
                    "predictions": [
                        pred.to_list() if pred else None
                        for pred in r.predictions
                    ],
                    "ground_truth": [
                        truth.to_list()
                        for truth in r.ground_truth
                    ] if r.ground_truth else None,
                    "correct": r.correct,
                }
                for r in results.task_results
            ],
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\nResults saved to {filepath}")


def quick_evaluation(
    num_tasks: int = 10,
    max_depth: int = 3,
    beam_width: int = 5,
    enable_learning: bool = True,
) -> EvaluationResults:
    """Quick evaluation on synthetic test tasks.

    Args:
        num_tasks: Number of test tasks to generate
        max_depth: Program synthesis max depth
        beam_width: Beam search width
        enable_learning: Enable incremental learning

    Returns:
        EvaluationResults
    """
    from supe.reasoning.arc import ARCGrid

    # Create simple synthetic tasks (rotation examples)
    tasks = []
    for i in range(num_tasks):
        # Create rotation task
        train = [
            (ARCGrid.from_list([[1, 0], [1, 0]]),
             ARCGrid.from_list([[1, 1], [0, 0]])),
            (ARCGrid.from_list([[0, 1], [0, 1]]),
             ARCGrid.from_list([[0, 0], [1, 1]])),
        ]
        test_input = ARCGrid.from_list([[1, 1], [0, 0]])
        test_output = ARCGrid.from_list([[0, 1], [0, 1]])

        tasks.append(ARCTask(
            train=train,
            test_inputs=[test_input],
            test_outputs=[test_output],
            task_id=f"synthetic_{i}",
        ))

    # Create capability and evaluate
    capability = ARCCapability(
        max_depth=max_depth,
        beam_width=beam_width,
        enable_learning=enable_learning,
    )

    evaluator = ARCEvaluator(capability)
    results = evaluator.evaluate_tasks(tasks, print_progress=True)

    evaluator.print_summary(results)

    return results
