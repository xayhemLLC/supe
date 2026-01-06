"""Actual reasoning capability implementations.

This module contains the real implementations of reasoning methods
that the meta-solver can dispatch to.
"""

from typing import Dict, Any, Protocol


class ReasoningCapability(Protocol):
    """Protocol for reasoning capability implementations."""

    def execute(self, problem_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the reasoning capability.

        Args:
            problem_text: The problem statement
            context: Context from previous steps and analysis

        Returns:
            Dictionary with result and metadata
        """
        ...


# Import all capability implementations
from supe.reasoning.capabilities.algebraic import AlgebraicManipulation
from supe.reasoning.capabilities.search import ExhaustiveSearch
from supe.reasoning.capabilities.hypothesis import HypothesisTesting
from supe.reasoning.capabilities.pattern import PatternMatcher
from supe.reasoning.capabilities.deductive import DeductiveReasoner
from supe.reasoning.capabilities.optimizer import Optimizer

__all__ = [
    "AlgebraicManipulation",
    "ExhaustiveSearch",
    "HypothesisTesting",
    "PatternMatcher",
    "DeductiveReasoner",
    "Optimizer",
]
