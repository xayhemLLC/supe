"""Program synthesis for ARC tasks.

This module implements program synthesis using beam search over the DSL.
It generates candidate programs and ranks them by performance on examples.
"""

from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
import heapq

from supe.reasoning.arc.grid import ARCGrid
from supe.reasoning.arc.dsl import (
    Program,
    ProgramNode,
    TransformNode,
    SequenceNode,
    IdentityNode,
)
from supe.reasoning.arc.catalog import get_catalog, TransformationMatch


@dataclass
class ProgramCandidate:
    """Candidate program with score."""
    program: Program
    score: float  # Accuracy on examples
    explanation: str

    def __lt__(self, other):
        """For heap ordering (higher score is better)."""
        return self.score > other.score  # Reverse for max-heap


class ProgramSynthesizer:
    """Synthesize programs from input-output examples using beam search."""

    def __init__(
        self,
        max_depth: int = 3,
        beam_width: int = 5,
        max_programs: int = 10,
    ):
        """Initialize synthesizer.

        Args:
            max_depth: Maximum program depth (number of transformation steps)
            beam_width: Number of candidates to keep at each depth
            max_programs: Maximum programs to return
        """
        self.max_depth = max_depth
        self.beam_width = beam_width
        self.max_programs = max_programs
        self.catalog = get_catalog()

    def synthesize(
        self,
        examples: List[Tuple[ARCGrid, ARCGrid]],
        verbose: bool = False,
    ) -> List[ProgramCandidate]:
        """Synthesize programs from examples.

        Args:
            examples: List of (input, output) training pairs
            verbose: Print synthesis progress

        Returns:
            List of candidate programs sorted by score
        """
        if not examples:
            return []

        if verbose:
            print(f"\n=== Program Synthesis ===")
            print(f"Examples: {len(examples)}")
            print(f"Max depth: {self.max_depth}")
            print(f"Beam width: {self.beam_width}")

        # Start with identity program and single-transformation programs
        beam = self._initialize_beam(examples, verbose)

        # Expand beam iteratively up to max depth
        for depth in range(1, self.max_depth):
            if verbose:
                print(f"\n--- Depth {depth} ---")
                print(f"Current beam size: {len(beam)}")

            beam = self._expand_beam(beam, examples, verbose)

            if not beam:
                break

        # Convert to list and sort
        candidates = []
        while beam:
            candidates.append(heapq.heappop(beam))

        if verbose:
            print(f"\n=== Synthesis Complete ===")
            print(f"Found {len(candidates)} programs")
            if candidates:
                print(f"Best score: {candidates[0].score:.2%}")

        return candidates[:self.max_programs]

    def _initialize_beam(
        self,
        examples: List[Tuple[ARCGrid, ARCGrid]],
        verbose: bool,
    ) -> List[ProgramCandidate]:
        """Initialize beam with simple programs."""
        beam = []

        # Try identity (baseline)
        identity_program = Program(IdentityNode(), name="identity")
        identity_score = identity_program.verify(examples)

        if identity_score > 0:
            heapq.heappush(beam, ProgramCandidate(
                program=identity_program,
                score=identity_score,
                explanation="identity",
            ))

        # Try single transformations with parameter fitting
        matches = self.catalog.find_transformation(examples, max_results=self.beam_width * 2)

        for match in matches:
            if match.confidence == 0:
                continue

            # Create program from single transformation
            transform_node = TransformNode(
                transformation=match.transformation,
                parameters=match.parameters,
            )
            program = Program(transform_node, name=match.explanation)
            score = program.verify(examples)

            if score > 0:
                heapq.heappush(beam, ProgramCandidate(
                    program=program,
                    score=score,
                    explanation=match.explanation,
                ))

                if verbose:
                    print(f"  Added: {match.explanation} (score: {score:.2%})")

        # Keep top beam_width
        beam = heapq.nsmallest(self.beam_width, beam)

        return beam

    def _expand_beam(
        self,
        beam: List[ProgramCandidate],
        examples: List[Tuple[ARCGrid, ARCGrid]],
        verbose: bool,
    ) -> List[ProgramCandidate]:
        """Expand beam by adding one more transformation."""
        new_beam = []

        for candidate in beam:
            # Try extending with each transformation
            expansions = self._expand_program(candidate.program, examples)

            for new_program, score, explanation in expansions:
                if score > 0:
                    heapq.heappush(new_beam, ProgramCandidate(
                        program=new_program,
                        score=score,
                        explanation=explanation,
                    ))

                    if verbose and score > candidate.score:
                        print(f"  Improved: {explanation} (score: {score:.2%})")

        # Keep top beam_width unique programs
        seen_programs = set()
        unique_beam = []

        while new_beam and len(unique_beam) < self.beam_width:
            candidate = heapq.heappop(new_beam)
            program_str = candidate.program.to_string()

            if program_str not in seen_programs:
                seen_programs.add(program_str)
                unique_beam.append(candidate)

        return unique_beam

    def _expand_program(
        self,
        program: Program,
        examples: List[Tuple[ARCGrid, ARCGrid]],
    ) -> List[Tuple[Program, float, str]]:
        """Expand program by adding one transformation.

        Returns list of (new_program, score, explanation) tuples.
        """
        expansions = []

        # Apply current program to get intermediate outputs
        intermediate_pairs = []
        for input_grid, output_grid in examples:
            result = program.execute(input_grid)
            if result.success and result.output_grid:
                intermediate_pairs.append((result.output_grid, output_grid))

        if not intermediate_pairs:
            return []

        # Find transformations that map intermediate to final output
        matches = self.catalog.find_transformation(
            intermediate_pairs,
            max_results=self.beam_width,
        )

        for match in matches[:self.beam_width]:
            # Create extended program
            new_steps = []

            # Add existing steps
            if isinstance(program.root, SequenceNode):
                new_steps.extend(program.root.steps)
            else:
                new_steps.append(program.root)

            # Add new step
            new_steps.append(TransformNode(
                transformation=match.transformation,
                parameters=match.parameters,
            ))

            # Create new program
            new_root = SequenceNode(new_steps)
            new_program = Program(
                new_root,
                name=f"{program.name} → {match.explanation}"
            )

            # Evaluate
            score = new_program.verify(examples)

            expansions.append((new_program, score, new_program.name))

        return expansions

    def synthesize_best(
        self,
        examples: List[Tuple[ARCGrid, ARCGrid]],
        min_score: float = 1.0,
        verbose: bool = False,
    ) -> Optional[ProgramCandidate]:
        """Synthesize and return best program above threshold.

        Args:
            examples: Training examples
            min_score: Minimum score required
            verbose: Print progress

        Returns:
            Best program or None if none meet threshold
        """
        candidates = self.synthesize(examples, verbose=verbose)

        if not candidates:
            return None

        best = candidates[0]
        if best.score >= min_score:
            return best

        return None

    def solve_task(
        self,
        train_examples: List[Tuple[ARCGrid, ARCGrid]],
        test_input: ARCGrid,
        verbose: bool = False,
    ) -> Optional[ARCGrid]:
        """Solve ARC task by synthesizing program and applying to test input.

        Args:
            train_examples: Training input-output pairs
            test_input: Test input grid
            verbose: Print progress

        Returns:
            Predicted test output or None if synthesis fails
        """
        if verbose:
            print("\n" + "="*60)
            print("SOLVING ARC TASK")
            print("="*60)
            print(f"Training examples: {len(train_examples)}")

        # Synthesize program
        best = self.synthesize_best(train_examples, min_score=1.0, verbose=verbose)

        if not best:
            if verbose:
                print("  Failed to synthesize perfect program")
            return None

        if verbose:
            print(f"\n  Synthesized program (score: {best.score:.2%}):")
            print(best.program.to_string())

        # Apply to test input
        result = best.program.execute(test_input)

        if not result.success:
            if verbose:
                print(f"  Execution failed: {result.explanation}")
            return None

        if verbose:
            print("  ✓ Successfully predicted test output")

        return result.output_grid


class IncrementalSynthesizer(ProgramSynthesizer):
    """Synthesizer that learns from previous solutions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.learned_programs: List[Program] = []

    def add_solution(self, program: Program):
        """Add successful program to library."""
        self.learned_programs.append(program)

    def _initialize_beam(
        self,
        examples: List[Tuple[ARCGrid, ARCGrid]],
        verbose: bool,
    ) -> List[ProgramCandidate]:
        """Initialize with both catalog and learned programs."""
        beam = super()._initialize_beam(examples, verbose)

        # Try learned programs
        for learned_program in self.learned_programs:
            score = learned_program.verify(examples)

            if score > 0:
                heapq.heappush(beam, ProgramCandidate(
                    program=learned_program,
                    score=score,
                    explanation=f"learned: {learned_program.name}",
                ))

                if verbose:
                    print(f"  Reused learned program: {learned_program.name} (score: {score:.2%})")

        # Keep top beam_width
        return heapq.nsmallest(self.beam_width, beam)
