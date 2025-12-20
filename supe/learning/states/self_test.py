"""SELF_TEST state - Test retrieval without looking at answers.

This state validates learning by testing the system's ability to
answer questions without referring back to the source material.
Similar to closing your notes and trying to recall.
"""

from typing import TYPE_CHECKING

from ..types import LearningState, QuestionStatus
from .base import BaseState

if TYPE_CHECKING:
    from ..models import LearningContext


class SelfTestState(BaseState):
    """Test retrieval of learned information without referring to sources.

    This state:
    1. Takes the recently learned belief
    2. Attempts to answer the focus question from memory alone
    3. Compares the recall against the stored belief
    4. Updates confidence based on recall quality

    The self-test validates that learning was successful - the system
    can reproduce the answer without re-reading source material.
    """

    async def execute(self, context: "LearningContext") -> LearningState:
        """Execute self-test validation.

        Args:
            context: Current learning context.

        Returns:
            Next state (EVALUATE_AND_UPDATE_CONFIDENCE).
        """
        self._log("=== SELF_TEST State ===")

        if not context.beliefs_created:
            self._log("No beliefs to test, skipping self-test")
            return LearningState.EVALUATE_AND_UPDATE_CONFIDENCE

        # Get the most recent belief
        latest_belief = context.beliefs_created[-1]
        question = context.focus_question

        if not question:
            self._log("No focus question, skipping self-test")
            return LearningState.EVALUATE_AND_UPDATE_CONFIDENCE

        self._log(f"Testing recall for: {question.text}")

        # Test recall by attempting to reconstruct answer from memory
        # In a real implementation, this would use the LLM to try answering
        # without providing the original source material
        recall_quality = self._test_recall(question, latest_belief)

        self._log(f"Recall quality: {recall_quality:.2f}")

        # Store recall quality in context metadata for EVALUATE state
        if not hasattr(context, '_test_results'):
            context._test_results = {}
        context._test_results[question.id] = {
            "recall_quality": recall_quality,
            "belief_id": latest_belief.id,
            "tested_at": self._timestamp_now(),
        }

        # Mark question as tested
        question.status = QuestionStatus.ANSWERED

        return LearningState.EVALUATE_AND_UPDATE_CONFIDENCE

    def _test_recall(self, question, belief) -> float:
        """Test recall quality.

        In a real implementation, this would:
        1. Ask LLM to answer question WITHOUT providing sources
        2. Compare generated answer to stored belief
        3. Compute similarity score

        For now, we use confidence as a proxy:
        - High confidence beliefs = assumed good recall
        - Low confidence beliefs = assumed poor recall

        Args:
            question: Question to test.
            belief: Stored belief to compare against.

        Returns:
            Recall quality score (0.0-1.0).
        """
        # Simple heuristic: use belief confidence as recall proxy
        # In production, would actually test LLM recall
        base_recall = belief.confidence

        # Slight penalty for recall (always easier to recognize than recall)
        recall_quality = base_recall * 0.9

        return max(0.0, min(1.0, recall_quality))

    def _timestamp_now(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
