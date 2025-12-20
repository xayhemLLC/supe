"""Base state class for the learning state machine.

All learning states inherit from BaseState and implement the execute() method
which performs the state's logic and returns the next state to transition to.

State pattern:
- Each state is responsible for its own logic
- States are stateless - all data in LearningContext
- execute() is async and returns next LearningState
- States can access machine.memory, machine.mode, etc.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..models import LearningContext
from ..types import LearningState

if TYPE_CHECKING:
    from ..state_machine import LearningStateMachine


class BaseState(ABC):
    """Abstract base class for learning states.

    Each state implements execute() which:
    1. Performs state-specific logic
    2. Updates context as needed
    3. Returns the next state to transition to

    States should be stateless - all data stored in context.
    """

    def __init__(self, machine: "LearningStateMachine"):
        """Initialize state with reference to state machine.

        Args:
            machine: The parent state machine.
        """
        self.machine = machine

    @abstractmethod
    async def execute(self, context: LearningContext) -> LearningState:
        """Execute state logic and return next state.

        This is the main entry point for state execution. It should:
        - Perform all state-specific logic
        - Update context with new data
        - Return the next state to transition to

        Args:
            context: Current learning context.

        Returns:
            Next state to transition to.
        """
        pass

    def _log(self, message: str) -> None:
        """Log a debug message if debug mode is enabled.

        Args:
            message: Message to log.
        """
        if self.machine.debug:
            print(f"[{self.__class__.__name__}] {message}")

    def _log_transition(self, from_state: LearningState, to_state: LearningState) -> None:
        """Log a state transition.

        Args:
            from_state: Current state.
            to_state: Next state.
        """
        self._log(f"Transitioning: {from_state.value} -> {to_state.value}")


class TerminalState(BaseState):
    """Base class for terminal states (IDLE, TERMINATE)."""

    async def execute(self, context: LearningContext) -> LearningState:
        """Terminal states return themselves."""
        self._log("Terminal state reached")
        return context.current_state
