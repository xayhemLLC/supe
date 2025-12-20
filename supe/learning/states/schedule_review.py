"""SCHEDULE_REVIEW state - Schedule spaced repetition reviews.

This state implements spaced repetition scheduling based on confidence
scores and learning performance. Uses a simplified SM-2 algorithm.
"""

from typing import TYPE_CHECKING
from datetime import datetime, timedelta

from ..types import LearningState
from .base import BaseState

if TYPE_CHECKING:
    from ..models import LearningContext, Belief


class ScheduleReviewState(BaseState):
    """Schedule spaced repetition reviews for learned beliefs.

    This state:
    1. Analyzes belief confidence scores
    2. Determines appropriate review intervals
    3. Sets next_review_at timestamps
    4. Stores review schedule in context

    Uses spaced repetition intervals:
    - Low confidence (< 0.6): 1 day
    - Medium confidence (0.6-0.8): 3 days
    - High confidence (> 0.8): 7 days
    - Very high confidence (> 0.9): 14 days
    """

    # Review intervals in days based on confidence
    REVIEW_INTERVALS = [
        (0.0, 0.5, 1),    # Very low: review tomorrow
        (0.5, 0.6, 2),    # Low: review in 2 days
        (0.6, 0.7, 3),    # Medium-low: review in 3 days
        (0.7, 0.8, 5),    # Medium: review in 5 days
        (0.8, 0.9, 7),    # High: review in 1 week
        (0.9, 0.95, 14),  # Very high: review in 2 weeks
        (0.95, 1.0, 30),  # Excellent: review in 1 month
    ]

    async def execute(self, context: "LearningContext") -> LearningState:
        """Execute review scheduling.

        Args:
            context: Current learning context.

        Returns:
            Next state (IDLE_OR_TERMINATE - end of learning cycle).
        """
        self._log("=== SCHEDULE_REVIEW State ===")

        if not context.beliefs_created:
            self._log("No beliefs to schedule for review")
            return LearningState.IDLE_OR_TERMINATE

        now = datetime.now()

        # Schedule each belief for review
        for belief in context.beliefs_created:
            interval_days = self._get_review_interval(belief.confidence)
            next_review = now + timedelta(days=interval_days)

            # Store in belief metadata
            if not hasattr(belief, '_review_schedule'):
                belief._review_schedule = {}

            belief._review_schedule = {
                "next_review_at": next_review.isoformat(),
                "interval_days": interval_days,
                "scheduled_at": now.isoformat(),
                "confidence_at_schedule": belief.confidence,
            }

            self._log(
                f"Belief {belief.id[:8]} (confidence={belief.confidence:.2f}): "
                f"review in {interval_days} days ({next_review.strftime('%Y-%m-%d')})"
            )

        # Store overall review schedule in context
        earliest_review = min(
            datetime.fromisoformat(b._review_schedule["next_review_at"])
            for b in context.beliefs_created
            if hasattr(b, '_review_schedule')
        )

        context.next_review_at = earliest_review.isoformat()

        self._log(f"Next review scheduled for: {earliest_review.strftime('%Y-%m-%d %H:%M')}")

        return LearningState.IDLE_OR_TERMINATE

    def _get_review_interval(self, confidence: float) -> int:
        """Get review interval based on confidence score.

        Uses spaced repetition principle:
        - Lower confidence = shorter interval (more practice needed)
        - Higher confidence = longer interval (knowledge retained)

        Args:
            confidence: Confidence score (0.0-1.0).

        Returns:
            Days until next review.
        """
        # Find matching interval
        for min_conf, max_conf, days in self.REVIEW_INTERVALS:
            if min_conf <= confidence < max_conf:
                return days

        # Default: 7 days
        return 7

    def _adjust_interval_for_gaps(
        self,
        base_interval: int,
        gap_count: int,
    ) -> int:
        """Adjust review interval based on knowledge gaps.

        More gaps = shorter interval (need to consolidate learning).

        Args:
            base_interval: Base interval in days.
            gap_count: Number of identified gaps.

        Returns:
            Adjusted interval in days.
        """
        if gap_count == 0:
            return base_interval

        # Reduce interval for each gap (up to 50% reduction)
        reduction_factor = 1.0 - min(0.5, gap_count * 0.1)
        adjusted = int(base_interval * reduction_factor)

        return max(1, adjusted)  # At least 1 day
