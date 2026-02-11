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

    Supe action definitions (Claude Code-style tools):
    - definitions.py - ActionDefinition, ALL_ACTIONS, tool schemas
"""

# Existing mutation primitives
# Agent action system
from .base import (
    ActionMetadata,
    ActionResult,
    ActionType,
    AgentAction,
    ValidationResult,
)

# Supe action definitions (Claude Code-style tools with validation)
from .definitions import (
    ALL_ACTIONS,
    ActionCategory,
    ActionDefinition,
    ActionParameter,
    RiskLevel,
    export_tool_schemas,
    get_action,
    get_actions_for_phase,
    list_actions,
)
from .executor import (
    ActionExecutor,
    execute_action,
    validate_params,
)
from .format import FormatFixResult, format_fix
from .lint import LintFixResult, lint_fix_loop
from .patch import ApplyPatchResult, apply_patch
from .registry import (
    get_action_handler,
    get_action_metadata,
    is_dangerous,
    is_mutation,
    list_action_types,
    register_action,
    requires_approval,
)
from .test import TestTriageResult, test_run_and_triage

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
    # Supe action definitions
    "ActionDefinition",
    "ActionParameter",
    "ActionCategory",
    "RiskLevel",
    "ALL_ACTIONS",
    "get_action",
    "list_actions",
    "get_actions_for_phase",
    "export_tool_schemas",
]


