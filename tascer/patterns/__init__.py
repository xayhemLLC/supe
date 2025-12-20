"""Patterns package - Intelligence accretion through pattern tracking.

Patterns are derived from comparing exe (intent) with moments (reality).
They compound over time to improve judgment.
"""

from .objects import (
    Pattern,
    FailurePattern,
    FixPattern,
    DecisionPattern,
    FrontendPattern,
    PatternStore,
)

__all__ = [
    "Pattern",
    "FailurePattern",
    "FixPattern",
    "DecisionPattern",
    "FrontendPattern",
    "PatternStore",
]
