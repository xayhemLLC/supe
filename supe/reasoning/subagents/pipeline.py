"""Reasoning Pipeline - Orchestrates the three subagents.

The pipeline connects the three subagents in sequence:
    Problem → [ProblemSolver] → Solution → [Critiquer] → Validated → [Citer] → Cited

Example:
    pipeline = ReasoningPipeline(memory)
    result = await pipeline.run(problem_text, options)

    if result.approved:
        print(f"Answer: {result.tasc.proposed_answer}")
        print(f"Confidence: {result.final_confidence:.0%}")
        print(f"Evidence: {result.evidence.get_strength_label()}")
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
import json

from ab.abdb import ABMemory
from ab.models import Buffer

from .problem_solver import ProblemSolver, TASC
from .critiquer import Critiquer, CritiqueResult, CritiqueVerdict
from .citer import Citer, GatheredEvidence


@dataclass
class PipelineResult:
    """Result from running the full reasoning pipeline."""

    tasc: TASC
    critique: CritiqueResult
    evidence: GatheredEvidence

    # Aggregated status
    approved: bool = False
    final_confidence: float = 0.0
    revision_needed: bool = False
    blocked: bool = False

    # Timing
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tasc": self.tasc.to_dict(),
            "critique": self.critique.to_dict(),
            "evidence": self.evidence.to_dict(),
            "approved": self.approved,
            "final_confidence": self.final_confidence,
            "revision_needed": self.revision_needed,
            "blocked": self.blocked,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
        }

    def to_ascii(self) -> str:
        """Render full pipeline result as ASCII."""
        lines = []

        # TASC output
        lines.append(self.tasc.to_ascii())
        lines.append("")

        # Critique output
        lines.append(self.critique.to_ascii())
        lines.append("")

        # Evidence output
        lines.append(self.evidence.to_ascii())
        lines.append("")

        # Final summary
        width = 60
        lines.append("┌" + "─" * (width - 2) + "┐")
        lines.append(f"│  PIPELINE SUMMARY{' ' * (width - 20)}│")
        lines.append("├" + "─" * (width - 2) + "┤")

        status = "✅ APPROVED" if self.approved else "⚠️ NEEDS REVISION" if self.revision_needed else "🚫 BLOCKED"
        lines.append(f"│  Status: {status:<{width - 14}}│")
        lines.append(f"│  Final Confidence: {self.final_confidence*100:.0f}%{' ' * (width - 28)}│")
        lines.append(f"│  Evidence Strength: {self.evidence.get_strength_label():<{width - 25}}│")
        lines.append(f"│  Duration: {self.duration_ms}ms{' ' * (width - 20 - len(str(self.duration_ms)))}│")

        lines.append("└" + "─" * (width - 2) + "┘")

        return "\n".join(lines)


class ReasoningPipeline:
    """Orchestrates the three reasoning subagents.

    The pipeline runs:
    1. ProblemSolver: Generates structured TASC solution
    2. Critiquer: Reviews for errors and issues
    3. Citer: Gathers supporting evidence

    The final result combines all three with adjusted confidence.

    Example:
        pipeline = ReasoningPipeline(memory)

        # Simple usage
        result = await pipeline.run("Find f(g(2)) where f(x)=x²+1, g(x)=x-2")

        # With options
        result = await pipeline.run(
            problem_text="Find f(g(2))",
            options={"A": 1, "B": 5, "C": -1, "D": 0},
            given=["f(x) = x² + 1", "g(x) = x - 2"],
            find="f(g(2))"
        )

        if result.approved:
            print(f"Answer: {result.tasc.proposed_answer}")
    """

    def __init__(
        self,
        memory: ABMemory,
        search_function: Optional[Callable] = None,
        auto_revise: bool = False,
        max_revisions: int = 2,
    ):
        """Initialize the pipeline.

        Args:
            memory: ABMemory instance for storage
            search_function: Optional async function for external evidence search
            auto_revise: Whether to automatically attempt revisions on critique failure
            max_revisions: Maximum revision attempts if auto_revise is True
        """
        self.memory = memory
        self.solver = ProblemSolver(memory)
        self.critiquer = Critiquer(memory)
        self.citer = Citer(memory, search_function)
        self.auto_revise = auto_revise
        self.max_revisions = max_revisions

    async def run(
        self,
        problem_text: str,
        options: Optional[Dict[str, Any]] = None,
        given: Optional[List[str]] = None,
        find: Optional[str] = None,
        title: Optional[str] = None,
    ) -> PipelineResult:
        """Run the full reasoning pipeline.

        Args:
            problem_text: The problem statement
            options: Optional answer options
            given: List of given information
            find: What we're looking for
            title: Optional title for the TASC

        Returns:
            PipelineResult with all outputs
        """
        import time
        start_time = time.time()

        # Stage 1: Problem Solving
        tasc = await self.solver.solve(
            problem_text=problem_text,
            options=options,
            given=given,
            find=find,
            title=title,
        )

        # Stage 2: Critique
        critique = await self.critiquer.review(tasc)

        # Handle auto-revision if enabled
        revision_count = 0
        while (
            self.auto_revise
            and critique.verdict in [CritiqueVerdict.NEEDS_REVISION, CritiqueVerdict.REJECTED]
            and revision_count < self.max_revisions
        ):
            # Attempt to fix issues and re-solve
            tasc = await self._revise_solution(tasc, critique)
            critique = await self.critiquer.review(tasc)
            revision_count += 1

        # Stage 3: Evidence Gathering
        evidence = await self.citer.gather(tasc)

        # Calculate final confidence
        final_confidence = self._calculate_final_confidence(tasc, critique, evidence)

        # Determine final status
        approved = critique.verdict in [CritiqueVerdict.APPROVED, CritiqueVerdict.APPROVED_WITH_NOTES]
        revision_needed = critique.verdict == CritiqueVerdict.NEEDS_REVISION
        blocked = critique.verdict in [CritiqueVerdict.REJECTED, CritiqueVerdict.BLOCKED]

        # Build result
        end_time = time.time()
        result = PipelineResult(
            tasc=tasc,
            critique=critique,
            evidence=evidence,
            approved=approved,
            final_confidence=final_confidence,
            revision_needed=revision_needed,
            blocked=blocked,
            completed_at=datetime.utcnow().isoformat(),
            duration_ms=int((end_time - start_time) * 1000),
        )

        # Store pipeline result
        await self._store_result(result)

        return result

    def _calculate_final_confidence(
        self,
        tasc: TASC,
        critique: CritiqueResult,
        evidence: GatheredEvidence,
    ) -> float:
        """Calculate final confidence from all stages."""
        # Start with TASC confidence
        base_confidence = tasc.confidence

        # Apply critique adjustment
        adjusted = base_confidence + critique.confidence_adjustment

        # Factor in evidence score
        evidence_factor = 0.5 + (evidence.overall_score * 0.5)  # 0.5 to 1.0
        final = adjusted * evidence_factor

        return max(0.0, min(1.0, final))

    async def _revise_solution(
        self,
        tasc: TASC,
        critique: CritiqueResult,
    ) -> TASC:
        """Attempt to revise a solution based on critique feedback.

        This is a simplified revision that adds missing checkpoints.
        A full implementation would re-run problematic steps.
        """
        # For now, just add observations about the critique
        for item in critique.items:
            if item.severity.value in ["error", "warning"]:
                # Add a revision note to the TASC
                tasc.evidence.append({
                    "type": "revision_note",
                    "source": "critiquer",
                    "content": f"Addressed: {item.description}",
                    "validated": False,
                })

        return tasc

    async def _store_result(self, result: PipelineResult) -> int:
        """Store pipeline result in AB memory."""
        result_json = json.dumps(result.to_dict()).encode("utf-8")
        result_ascii = result.to_ascii().encode("utf-8")

        buffers = [
            Buffer(
                name="pipeline_json",
                headers={"type": "pipeline_result", "format": "json"},
                payload=result_json,
            ),
            Buffer(
                name="pipeline_ascii",
                headers={"type": "pipeline_result", "format": "ascii"},
                payload=result_ascii,
            ),
        ]

        card = self.memory.store_card(
            label=f"Pipeline: {result.tasc.title}",
            buffers=buffers,
            track="reasoning",
            master_input=result.tasc.problem_text[:200],
            master_output=f"{'✅' if result.approved else '❌'} {result.tasc.proposed_answer} ({result.final_confidence:.0%})",
        )

        return card.id


# Convenience function for quick pipeline execution
async def solve_with_validation(
    memory: ABMemory,
    problem_text: str,
    options: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> PipelineResult:
    """Quick helper to run the full reasoning pipeline.

    Args:
        memory: ABMemory instance
        problem_text: The problem to solve
        options: Optional answer options
        **kwargs: Additional arguments passed to pipeline.run()

    Returns:
        PipelineResult with validated solution
    """
    pipeline = ReasoningPipeline(memory)
    return await pipeline.run(problem_text, options, **kwargs)
