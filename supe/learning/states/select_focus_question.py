"""SELECT_FOCUS_QUESTION state - Select question to work on.

This state:
1. Checks if focus_question is already set
2. If not, attempts to pop from QuestionQueue
3. Transitions to PLAN_EVIDENCE_STRATEGY or IDLE

This is where the question-driven learning flow begins.
"""

from ..models import LearningContext
from ..types import LearningState, QuestionStatus
from .base import BaseState


class SelectFocusQuestionState(BaseState):
    """Select the next question to answer."""

    async def execute(self, context: LearningContext) -> LearningState:
        """Select focus question.

        Args:
            context: Learning context.

        Returns:
            Next state (PLAN_EVIDENCE_STRATEGY or IDLE).
        """
        self._log("Selecting focus question")

        # Check if we already have a focus question
        if context.focus_question is not None:
            # Check if it's already answered
            if context.focus_question.status == QuestionStatus.ANSWERED:
                self._log(f"Focus question already answered: {context.focus_question.text}")
                # TODO: Pop next question from queue
                # For now, transition to IDLE
                return LearningState.IDLE_OR_TERMINATE

            self._log(f"Using existing focus question: {context.focus_question.text}")
            self._log_transition(LearningState.SELECT_FOCUS_QUESTION, LearningState.PLAN_EVIDENCE_STRATEGY)
            return LearningState.PLAN_EVIDENCE_STRATEGY

        # No focus question - check if we have followup questions
        if context.followup_questions:
            self._log(f"Using followup question from queue ({len(context.followup_questions)} available)")
            context.focus_question = context.followup_questions.pop(0)
            self._log(f"Selected: {context.focus_question.text}")
            self._log_transition(LearningState.SELECT_FOCUS_QUESTION, LearningState.PLAN_EVIDENCE_STRATEGY)
            return LearningState.PLAN_EVIDENCE_STRATEGY

        # No questions available
        self._log("No questions available - terminating")
        self._log_transition(LearningState.SELECT_FOCUS_QUESTION, LearningState.IDLE_OR_TERMINATE)
        return LearningState.IDLE_OR_TERMINATE
