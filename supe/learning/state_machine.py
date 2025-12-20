"""Learning state machine orchestrator.

The LearningStateMachine orchestrates the unified INGEST + EXPLORE learning
process through a series of state transitions.

State flow:
    INIT → SELECT_FOCUS_QUESTION → PLAN_EVIDENCE_STRATEGY →
    ├─ INGEST_DOC (docs/APIs) →
    └─ EXPLORE_ENV (math experiments) →
    INTEGRATE_KNOWLEDGE → SELF_TEST → EVALUATE_AND_UPDATE_CONFIDENCE →
    GENERATE_FOLLOWUP_QUESTIONS → SCHEDULE_REVIEW → IDLE_OR_TERMINATE

Key features:
- Async state transitions (like Supe's moment cycle)
- Context persistence after each state
- Configurable max steps limit
- Debug logging support
- State registry for extensibility
"""

import asyncio
from typing import Dict, Optional, Type

from ab.abdb import ABMemory

from .models import LearningContext, Question
from .types import Mode, LearningState, QuestionType
from .states.base import BaseState
from .storage import store_learning_context


class LearningStateMachine:
    """Main orchestrator for the learning state machine.

    Manages state transitions and context persistence throughout a
    learning session.

    Attributes:
        memory: AB Memory instance for storage.
        mode: Learning mode (INGEST or EXPLORE).
        context: Current learning context.
        debug: Whether to enable debug logging.
        states: Registry of state implementations.
    """

    def __init__(
        self,
        memory: ABMemory,
        mode: Mode,
        debug: bool = False,
    ):
        """Initialize state machine.

        Args:
            memory: AB Memory instance.
            mode: Learning mode (INGEST or EXPLORE).
            debug: Enable debug logging.
        """
        self.memory = memory
        self.mode = mode
        self.debug = debug
        self.context: Optional[LearningContext] = None
        self._states: Dict[LearningState, Type[BaseState]] = {}
        self._context_card_id: Optional[int] = None

        # Register default states
        self._register_states()

    def _register_states(self) -> None:
        """Register state implementations.

        This creates the state registry mapping LearningState enum values
        to their implementation classes. States are lazily imported to
        avoid circular dependencies.
        """
        # Import states lazily to avoid circular imports
        from .states.init import InitState
        from .states.idle import IdleState
        from .states.select_focus_question import SelectFocusQuestionState
        from .states.plan_evidence import PlanEvidenceState
        from .states.ingest_doc import IngestDocState
        from .states.explore_env import ExploreEnvState
        from .states.integrate_knowledge import IntegrateKnowledgeState
        from .states.self_test import SelfTestState
        from .states.evaluate import EvaluateAndUpdateConfidenceState
        from .states.generate_followup import GenerateFollowupQuestionsState
        from .states.schedule_review import ScheduleReviewState

        # Register all states
        self._states[LearningState.INIT] = InitState
        self._states[LearningState.SELECT_FOCUS_QUESTION] = SelectFocusQuestionState
        self._states[LearningState.PLAN_EVIDENCE_STRATEGY] = PlanEvidenceState
        self._states[LearningState.INGEST_DOC] = IngestDocState
        self._states[LearningState.EXPLORE_ENV] = ExploreEnvState
        self._states[LearningState.INTEGRATE_KNOWLEDGE] = IntegrateKnowledgeState
        self._states[LearningState.SELF_TEST] = SelfTestState
        self._states[LearningState.EVALUATE_AND_UPDATE_CONFIDENCE] = EvaluateAndUpdateConfidenceState
        self._states[LearningState.GENERATE_FOLLOWUP_QUESTIONS] = GenerateFollowupQuestionsState
        self._states[LearningState.SCHEDULE_REVIEW] = ScheduleReviewState
        self._states[LearningState.IDLE_OR_TERMINATE] = IdleState

    async def initialize(
        self,
        initial_question: Optional[str] = None,
    ) -> None:
        """Initialize learning session.

        Creates a new LearningContext and optionally seeds it with an
        initial question.

        Args:
            initial_question: Optional starting question.
        """
        if self.debug:
            print(f"[LearningStateMachine] Initializing {self.mode.value} mode session")

        # Create initial question if provided
        question = None
        if initial_question:
            question = Question.create(
                text=initial_question,
                question_type=QuestionType.CORE_CONCEPT,  # Default type
                source="user_input",
            )

        # Create context
        self.context = LearningContext.create(
            mode=self.mode,
            initial_question=question,
        )

        # Store initial context
        self._context_card_id = store_learning_context(self.memory, self.context)

        if self.debug:
            print(f"[LearningStateMachine] Session {self.context.session_id} initialized")

    async def step(self) -> LearningState:
        """Execute one state transition.

        This is analogous to Supe's step() method - it executes the current
        state's logic and transitions to the next state.

        Returns:
            Next state after transition.

        Raises:
            RuntimeError: If context not initialized or state not implemented.
        """
        if self.context is None:
            raise RuntimeError("Context not initialized. Call initialize() first.")

        current_state = self.context.current_state

        if self.debug:
            print(f"\n[LearningStateMachine] Step: {current_state.value}")

        # Get state implementation
        state_class = self._states.get(current_state)
        if state_class is None:
            raise RuntimeError(
                f"State {current_state.value} not implemented. "
                f"Available states: {list(self._states.keys())}"
            )

        # Execute state
        state = state_class(self)
        next_state = await state.execute(self.context)

        # Update context
        self.context.update_state(next_state)

        # Persist context
        if self._context_card_id is not None:
            # Update existing card (would need update method in storage)
            # For now, create new card
            self._context_card_id = store_learning_context(self.memory, self.context)

        if self.debug:
            print(f"[LearningStateMachine] Transitioned: {current_state.value} -> {next_state.value}")

        return next_state

    async def run(self, max_steps: int = 100) -> None:
        """Run state machine until terminal state or max steps.

        Executes step() repeatedly until reaching IDLE_OR_TERMINATE state
        or hitting the max steps limit.

        Args:
            max_steps: Maximum number of steps to execute.

        Raises:
            RuntimeError: If context not initialized.
        """
        if self.context is None:
            raise RuntimeError("Context not initialized. Call initialize() first.")

        if self.debug:
            print(f"\n[LearningStateMachine] Starting run (max {max_steps} steps)")

        steps = 0
        while steps < max_steps:
            current_state = self.context.current_state

            # Check for terminal state
            if current_state == LearningState.IDLE_OR_TERMINATE:
                if self.debug:
                    print(f"[LearningStateMachine] Terminal state reached after {steps} steps")
                break

            # Execute step
            await self.step()
            steps += 1

        if steps >= max_steps:
            if self.debug:
                print(f"[LearningStateMachine] Max steps ({max_steps}) reached")

    def get_beliefs(self):
        """Get beliefs created during this session.

        Returns:
            List of Belief objects.
        """
        if self.context is None:
            return []
        return self.context.beliefs_created

    def get_evidence(self):
        """Get evidence collected during this session.

        Returns:
            List of Evidence objects.
        """
        if self.context is None:
            return []
        return self.context.evidence_collected

    def get_gaps(self):
        """Get knowledge gaps identified during this session.

        Returns:
            List of gap descriptions.
        """
        if self.context is None:
            return []
        return self.context.gaps

    def get_followup_questions(self):
        """Get followup questions generated during this session.

        Returns:
            List of Question objects.
        """
        if self.context is None:
            return []
        return self.context.followup_questions

    def get_summary(self) -> Dict:
        """Get session summary.

        Returns:
            Dictionary with session metrics.
        """
        if self.context is None:
            return {}

        return {
            "session_id": self.context.session_id,
            "mode": self.context.mode.value,
            "current_state": self.context.current_state.value,
            "beliefs_count": len(self.context.beliefs_created),
            "evidence_count": len(self.context.evidence_collected),
            "gaps_count": len(self.context.gaps),
            "followup_questions_count": len(self.context.followup_questions),
            "focus_question": self.context.focus_question.text if self.context.focus_question else None,
        }


# Convenience function for quick usage
async def learn(
    memory: ABMemory,
    question: str,
    mode: Mode = Mode.INGEST,
    debug: bool = False,
) -> Dict:
    """Convenience function to run a complete learning session.

    Args:
        memory: AB Memory instance.
        question: Question to learn about.
        mode: Learning mode (default INGEST).
        debug: Enable debug logging.

    Returns:
        Session summary dictionary.
    """
    sm = LearningStateMachine(memory, mode, debug)
    await sm.initialize(question)
    await sm.run()
    return sm.get_summary()
