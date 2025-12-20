"""EVALUATE_AND_UPDATE_CONFIDENCE state - Adjust confidence based on evidence.

This state evaluates the quality of learning and adjusts confidence scores
based on multiple factors:
- Quality and quantity of evidence
- Self-test recall performance
- Identified gaps and unresolved questions
- Cross-validation with existing knowledge
"""

from typing import TYPE_CHECKING, List

from ..types import LearningState, EvidenceSource
from .base import BaseState

if TYPE_CHECKING:
    from ..models import LearningContext, Belief, Evidence


class EvaluateAndUpdateConfidenceState(BaseState):
    """Evaluate learning quality and update confidence scores.

    This state performs a comprehensive evaluation:
    1. Evidence quality assessment (sources, validation, citations)
    2. Self-test performance (if available)
    3. Gap analysis (number and severity)
    4. Unresolved questions impact
    5. Consistency with existing knowledge

    Updates belief confidence scores based on evaluation.
    """

    async def execute(self, context: "LearningContext") -> LearningState:
        """Execute confidence evaluation and update.

        Args:
            context: Current learning context.

        Returns:
            Next state (GENERATE_FOLLOWUP_QUESTIONS).
        """
        self._log("=== EVALUATE_AND_UPDATE_CONFIDENCE State ===")

        if not context.beliefs_created:
            self._log("No beliefs to evaluate")
            return LearningState.GENERATE_FOLLOWUP_QUESTIONS

        # Evaluate each belief
        for belief in context.beliefs_created:
            original_confidence = belief.confidence

            # Get evidence for this belief
            evidence_list = self._get_belief_evidence(context, belief)

            # Calculate confidence adjustments
            evidence_factor = self._evaluate_evidence_quality(evidence_list)
            recall_factor = self._evaluate_recall_performance(context, belief)
            gap_factor = self._evaluate_gap_impact(context)

            # Compute updated confidence
            updated_confidence = self._compute_updated_confidence(
                original_confidence,
                evidence_factor,
                recall_factor,
                gap_factor,
            )

            # Update belief
            belief.confidence = updated_confidence

            self._log(
                f"Belief {belief.id[:8]}: "
                f"{original_confidence:.2f} → {updated_confidence:.2f} "
                f"(evidence={evidence_factor:.2f}, "
                f"recall={recall_factor:.2f}, "
                f"gaps={gap_factor:.2f})"
            )

        return LearningState.GENERATE_FOLLOWUP_QUESTIONS

    def _get_belief_evidence(
        self,
        context: "LearningContext",
        belief: "Belief",
    ) -> List["Evidence"]:
        """Get evidence associated with a belief.

        Args:
            context: Learning context.
            belief: Belief to get evidence for.

        Returns:
            List of Evidence objects.
        """
        # Get evidence IDs from belief
        evidence_ids = set(belief.evidence_ids)

        # Filter context evidence to those referenced by belief
        return [e for e in context.evidence_collected if e.id in evidence_ids]

    def _evaluate_evidence_quality(self, evidence_list: List["Evidence"]) -> float:
        """Evaluate quality of evidence.

        Factors:
        - Number of evidence items (more = better, up to a point)
        - Source diversity (multiple sources = better)
        - Validation status (validated evidence = better)
        - Citation quality (specific citations = better)

        Args:
            evidence_list: List of evidence to evaluate.

        Returns:
            Quality factor (0.0-1.2, can boost confidence).
        """
        if not evidence_list:
            return 0.8  # Penalty for no evidence

        # Count evidence (1-5 optimal, diminishing returns after)
        evidence_count = len(evidence_list)
        count_factor = min(1.0, evidence_count / 5.0)

        # Source diversity (different source types)
        sources = set(e.source for e in evidence_list)
        diversity_factor = min(1.0, len(sources) / 3.0)

        # Validation status
        validated_count = sum(1 for e in evidence_list if e.validated)
        validation_factor = validated_count / len(evidence_list)

        # Citation quality (evidence with citations is better)
        with_citations = sum(1 for e in evidence_list if e.citations)
        citation_factor = with_citations / len(evidence_list)

        # Prefer validated, cited evidence from experiments/docs
        quality_bonus = 0.0
        for e in evidence_list:
            if e.source == EvidenceSource.EXPERIMENT and e.validated:
                quality_bonus += 0.1
            elif e.source == EvidenceSource.DOC and e.citations:
                quality_bonus += 0.05

        # Combine factors (weighted average + bonus)
        base_quality = (
            count_factor * 0.3 +
            diversity_factor * 0.2 +
            validation_factor * 0.3 +
            citation_factor * 0.2
        )

        return min(1.2, base_quality + quality_bonus)

    def _evaluate_recall_performance(
        self,
        context: "LearningContext",
        belief: "Belief",
    ) -> float:
        """Evaluate recall performance from self-test.

        Args:
            context: Learning context.
            belief: Belief to evaluate.

        Returns:
            Recall factor (0.7-1.1, affects confidence).
        """
        # Check if we have test results
        test_results = getattr(context, '_test_results', {})

        # Find test result for this belief
        for question_id, result in test_results.items():
            if result.get('belief_id') == belief.id:
                recall_quality = result.get('recall_quality', 0.8)
                # Good recall boosts, poor recall penalizes
                return 0.7 + (recall_quality * 0.4)

        # No test results, use neutral factor
        return 1.0

    def _evaluate_gap_impact(self, context: "LearningContext") -> float:
        """Evaluate impact of knowledge gaps.

        More gaps = lower confidence in related beliefs.

        Args:
            context: Learning context.

        Returns:
            Gap factor (0.8-1.0, reduces confidence if many gaps).
        """
        gap_count = len(context.gaps)

        if gap_count == 0:
            return 1.0  # No gaps, no penalty
        elif gap_count <= 2:
            return 0.95  # Minor gaps
        elif gap_count <= 5:
            return 0.9  # Moderate gaps
        else:
            return 0.8  # Many gaps, significant uncertainty

    def _compute_updated_confidence(
        self,
        original: float,
        evidence_factor: float,
        recall_factor: float,
        gap_factor: float,
    ) -> float:
        """Compute updated confidence score.

        Combines original confidence with adjustment factors.

        Args:
            original: Original confidence score.
            evidence_factor: Evidence quality adjustment.
            recall_factor: Recall performance adjustment.
            gap_factor: Gap impact adjustment.

        Returns:
            Updated confidence (0.0-1.0).
        """
        # Apply multiplicative adjustments
        updated = original * evidence_factor * recall_factor * gap_factor

        # Clamp to valid range
        return max(0.0, min(1.0, updated))
