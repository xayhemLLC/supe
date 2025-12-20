"""PLAN_EVIDENCE_STRATEGY state - Route to INGEST or EXPLORE mode.

This state determines which evidence gathering strategy to use based on:
1. The learning mode (INGEST vs EXPLORE)
2. The question type
3. Available resources

Routes to:
- INGEST_DOC for document/API learning
- EXPLORE_ENV for mathematical experimentation
"""

from ..models import LearningContext
from ..types import LearningState, Mode, QuestionType
from .base import BaseState


class PlanEvidenceState(BaseState):
    """Plan evidence gathering strategy."""

    async def execute(self, context: LearningContext) -> LearningState:
        """Determine evidence gathering strategy.

        Args:
            context: Learning context.

        Returns:
            Next state (INGEST_DOC or EXPLORE_ENV).
        """
        self._log("Planning evidence gathering strategy")

        if context.focus_question is None:
            self._log("ERROR: No focus question set")
            return LearningState.IDLE_OR_TERMINATE

        question = context.focus_question
        self._log(f"Question: {question.text}")
        self._log(f"Question type: {question.question_type.value}")
        self._log(f"Mode: {context.mode.value}")

        # Route based on mode
        if context.mode == Mode.INGEST:
            self._log("Routing to INGEST_DOC mode")
            self._log_transition(LearningState.PLAN_EVIDENCE_STRATEGY, LearningState.INGEST_DOC)
            return LearningState.INGEST_DOC

        elif context.mode == Mode.EXPLORE:
            self._log("Routing to EXPLORE_ENV mode")
            self._log_transition(LearningState.PLAN_EVIDENCE_STRATEGY, LearningState.EXPLORE_ENV)
            return LearningState.EXPLORE_ENV

        else:
            self._log(f"ERROR: Unknown mode {context.mode}")
            return LearningState.IDLE_OR_TERMINATE
