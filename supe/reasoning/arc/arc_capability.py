"""ARC-AGI reasoning capability for supe.

This module integrates ARC visual reasoning into supe's capability system,
enabling the meta-solver to use ARC for visual pattern recognition and
transformation inference tasks.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import json

from supe.reasoning.arc import (
    ARCGrid,
    ProgramSynthesizer,
    IncrementalSynthesizer,
    ProgramCandidate,
    get_catalog,
)


@dataclass
class ARCTask:
    """An ARC task with training and test examples."""
    train: List[Tuple[ARCGrid, ARCGrid]]
    test_inputs: List[ARCGrid]
    test_outputs: Optional[List[ARCGrid]] = None
    task_id: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ARCTask":
        """Create task from dictionary (ARC JSON format).

        Args:
            data: Dictionary with 'train' and 'test' keys

        Returns:
            ARCTask instance
        """
        # Parse training examples
        train = []
        for example in data.get("train", []):
            input_grid = ARCGrid.from_list(example["input"])
            output_grid = ARCGrid.from_list(example["output"])
            train.append((input_grid, output_grid))

        # Parse test inputs
        test_inputs = []
        test_outputs = []
        for example in data.get("test", []):
            test_inputs.append(ARCGrid.from_list(example["input"]))
            if "output" in example:
                test_outputs.append(ARCGrid.from_list(example["output"]))

        return cls(
            train=train,
            test_inputs=test_inputs,
            test_outputs=test_outputs if test_outputs else None,
            task_id=data.get("task_id", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (ARC JSON format)."""
        result = {
            "train": [
                {"input": inp.to_list(), "output": out.to_list()}
                for inp, out in self.train
            ],
            "test": [
                {"input": inp.to_list()}
                for inp in self.test_inputs
            ],
        }

        if self.test_outputs:
            for i, output in enumerate(self.test_outputs):
                result["test"][i]["output"] = output.to_list()

        if self.task_id:
            result["task_id"] = self.task_id

        return result


@dataclass
class ARCResult:
    """Result from solving an ARC task."""
    success: bool
    predictions: List[Optional[ARCGrid]]
    program: Optional[ProgramCandidate]
    explanation: str
    confidence: float
    synthesis_time: float  # seconds


class ARCCapability:
    """ARC visual reasoning capability for supe.

    This capability solves ARC tasks by:
    1. Analyzing training examples (input-output pairs)
    2. Synthesizing transformation programs via beam search
    3. Applying programs to test inputs
    4. Learning from successful solutions
    """

    def __init__(
        self,
        max_depth: int = 3,
        beam_width: int = 5,
        enable_learning: bool = True,
    ):
        """Initialize ARC capability.

        Args:
            max_depth: Maximum program depth (transformation steps)
            beam_width: Beam search width
            enable_learning: Whether to learn from solutions
        """
        self.max_depth = max_depth
        self.beam_width = beam_width
        self.enable_learning = enable_learning

        # Use incremental synthesizer if learning enabled
        if enable_learning:
            self.synthesizer = IncrementalSynthesizer(
                max_depth=max_depth,
                beam_width=beam_width,
            )
        else:
            self.synthesizer = ProgramSynthesizer(
                max_depth=max_depth,
                beam_width=beam_width,
            )

        self.catalog = get_catalog()

        # Statistics
        self.tasks_attempted = 0
        self.tasks_solved = 0
        self.total_synthesis_time = 0.0
        self.solution_library: List[ProgramCandidate] = []

    def __call__(
        self,
        task: ARCTask,
        verbose: bool = False,
    ) -> ARCResult:
        """Solve an ARC task.

        Args:
            task: The ARC task to solve
            verbose: Print synthesis progress

        Returns:
            ARCResult with predictions and metadata
        """
        import time

        self.tasks_attempted += 1
        start_time = time.time()

        # Synthesize program from training examples
        candidates = self.synthesizer.synthesize(task.train, verbose=verbose)

        if not candidates or candidates[0].score < 1.0:
            # Failed to find perfect program
            return ARCResult(
                success=False,
                predictions=[None] * len(task.test_inputs),
                program=candidates[0] if candidates else None,
                explanation=f"Failed to synthesize perfect program (best score: {candidates[0].score:.0%})" if candidates else "No programs found",
                confidence=candidates[0].score if candidates else 0.0,
                synthesis_time=time.time() - start_time,
            )

        best_program = candidates[0]

        # Apply to all test inputs
        predictions = []
        for test_input in task.test_inputs:
            result = best_program.program.execute(test_input)
            if result.success:
                predictions.append(result.output_grid)
            else:
                predictions.append(None)

        success = all(pred is not None for pred in predictions)

        # If successful and learning enabled, add to library
        if success and self.enable_learning:
            if hasattr(self.synthesizer, 'add_solution'):
                self.synthesizer.add_solution(best_program.program)
            self.solution_library.append(best_program)

        if success:
            self.tasks_solved += 1

        synthesis_time = time.time() - start_time
        self.total_synthesis_time += synthesis_time

        return ARCResult(
            success=success,
            predictions=predictions,
            program=best_program,
            explanation=f"Synthesized program: {best_program.explanation}",
            confidence=best_program.score,
            synthesis_time=synthesis_time,
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "tasks_attempted": self.tasks_attempted,
            "tasks_solved": self.tasks_solved,
            "solve_rate": self.tasks_solved / self.tasks_attempted if self.tasks_attempted > 0 else 0.0,
            "total_synthesis_time": self.total_synthesis_time,
            "avg_synthesis_time": self.total_synthesis_time / self.tasks_attempted if self.tasks_attempted > 0 else 0.0,
            "solution_library_size": len(self.solution_library),
            "max_depth": self.max_depth,
            "beam_width": self.beam_width,
        }

    def reset_statistics(self):
        """Reset statistics counters."""
        self.tasks_attempted = 0
        self.tasks_solved = 0
        self.total_synthesis_time = 0.0

    def clear_library(self):
        """Clear solution library (for fresh evaluation)."""
        self.solution_library = []
        if hasattr(self.synthesizer, 'learned_programs'):
            self.synthesizer.learned_programs = []


def load_arc_task(filepath: str) -> ARCTask:
    """Load an ARC task from JSON file.

    Args:
        filepath: Path to ARC task JSON file

    Returns:
        ARCTask instance
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    return ARCTask.from_dict(data)


def save_arc_task(task: ARCTask, filepath: str):
    """Save an ARC task to JSON file.

    Args:
        task: ARCTask to save
        filepath: Output path
    """
    with open(filepath, 'w') as f:
        json.dump(task.to_dict(), f, indent=2)
