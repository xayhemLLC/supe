"""Overlord package - Decision loop and intelligent control.

The Overlord is the narrator and chooser, not the executor.
It decides what to do, when to stop, and why.
"""

from .decision import (
    OverlordDecision,
    StopCondition,
    evaluate_stop_conditions,
    should_stop,
)
from .legality import (
    LegalityCheck,
    check_action_legality,
    is_action_legal,
    SecurityViolation,
)
from .prompt import (
    build_action_context,
    inject_action_metadata,
)

__all__ = [
    # Decision
    "OverlordDecision",
    "StopCondition",
    "evaluate_stop_conditions",
    "should_stop",
    # Legality
    "LegalityCheck",
    "check_action_legality",
    "is_action_legal",
    "SecurityViolation",
    # Prompt
    "build_action_context",
    "inject_action_metadata",
]
