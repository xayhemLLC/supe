"""Controlled mutation action primitives.

These actions provide safe ways to change state with full evidence capture.

Structure:
    Existing mutation primitives:
    - patch.py     - apply_patch
    - lint.py      - lint_fix_loop
    - format.py    - format_fix
    - test.py      - test_run_and_triage
    
    Agent action system:
    - base.py      - ActionType, AgentAction, ActionResult
    - registry.py  - Action metadata and lookup
    - executor.py  - Safe action execution
"""

# Existing mutation primitives
from .patch import apply_patch, ApplyPatchResult
from .lint import lint_fix_loop, LintFixResult
from .format import format_fix, FormatFixResult
from .test import test_run_and_triage, TestTriageResult

# Agent action system
from .base import (
    ActionType,
    AgentAction,
    ActionResult,
    ActionMetadata,
    ValidationResult,
)

from .registry import (
    get_action_handler,
    get_action_metadata,
    list_action_types,
    is_dangerous,
    requires_approval,
    is_mutation,
    register_action,
)

from .executor import (
    ActionExecutor,
    execute_action,
    validate_params,
)

__all__ = [
    # Existing primitives
    "apply_patch",
    "ApplyPatchResult",
    "lint_fix_loop",
    "LintFixResult",
    "format_fix",
    "FormatFixResult",
    "test_run_and_triage",
    "TestTriageResult",
    # Base types
    "ActionType",
    "AgentAction",
    "ActionResult",
    "ActionMetadata",
    "ValidationResult",
    # Registry
    "get_action_handler",
    "get_action_metadata",
    "list_action_types",
    "is_dangerous",
    "requires_approval",
    "is_mutation",
    "register_action",
    # Executor
    "ActionExecutor",
    "execute_action",
    "validate_params",
]

