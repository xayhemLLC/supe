"""IDLE state - Terminal state for learning sessions.

The IDLE_OR_TERMINATE state is reached when:
1. All questions have been answered
2. Learning goals have been met
3. Max iterations reached
4. User requested termination

This is a terminal state that returns itself when executed.
"""

from ..models import LearningContext
from ..types import LearningState
from .base import TerminalState


class IdleState(TerminalState):
    """Terminal idle state."""

    async def execute(self, context: LearningContext) -> LearningState:
        """Terminal state - return self.

        Args:
            context: Learning context.

        Returns:
            IDLE_OR_TERMINATE (self).
        """
        self._log("Learning session complete")

        # Log session summary
        if self.machine.debug:
            summary = self.machine.get_summary()
            self._log(f"Session summary:")
            self._log(f"  - Beliefs created: {summary.get('beliefs_count', 0)}")
            self._log(f"  - Evidence collected: {summary.get('evidence_count', 0)}")
            self._log(f"  - Gaps identified: {summary.get('gaps_count', 0)}")
            self._log(f"  - Followup questions: {summary.get('followup_questions_count', 0)}")

        return LearningState.IDLE_OR_TERMINATE
