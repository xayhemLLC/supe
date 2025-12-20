"""INIT state - Initialize learning session.

The INIT state is the entry point for all learning sessions. It:
1. Validates the initial question exists
2. Sets up the question queue
3. Transitions to SELECT_FOCUS_QUESTION

If no initial question is provided, it generates one based on mode.
"""

from ..models import LearningContext, Question
from ..types import LearningState, QuestionType
from .base import BaseState


class InitState(BaseState):
    """Initialize learning session state."""

    async def execute(self, context: LearningContext) -> LearningState:
        """Initialize learning session.

        Args:
            context: Learning context.

        Returns:
            Next state (SELECT_FOCUS_QUESTION or IDLE).
        """
        self._log("Initializing learning session")

        # Check if we have an initial question
        if context.focus_question is None:
            self._log("No initial question provided")

            # For now, transition to IDLE if no question
            # TODO: In future, could generate questions from available content
            return LearningState.IDLE_OR_TERMINATE

        self._log(f"Initial question: {context.focus_question.text}")

        # Validate question type based on mode
        if context.mode.value == "INGEST":
            # INGEST mode typically uses CORE_CONCEPT or OPERATIONAL questions
            valid_types = [QuestionType.CORE_CONCEPT, QuestionType.OPERATIONAL, QuestionType.IMPACT]
            if context.focus_question.question_type not in valid_types:
                self._log(f"Adjusting question type for INGEST mode")
                context.focus_question.question_type = QuestionType.CORE_CONCEPT

        elif context.mode.value == "EXPLORE":
            # EXPLORE mode typically uses MATH_STRUCTURE questions
            if context.focus_question.question_type not in [QuestionType.MATH_STRUCTURE, QuestionType.CONSTRAINT]:
                self._log(f"Adjusting question type for EXPLORE mode")
                context.focus_question.question_type = QuestionType.MATH_STRUCTURE

        # Session initialized successfully
        self._log("Session initialization complete")

        # Transition to SELECT_FOCUS_QUESTION
        self._log_transition(LearningState.INIT, LearningState.SELECT_FOCUS_QUESTION)
        return LearningState.SELECT_FOCUS_QUESTION
