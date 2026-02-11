"""Validation gates for asserting expected conditions.

Gates are reusable validation checks that can be composed to validate
tasc execution results. Each gate produces a GateResult with pass/fail
status and evidence.

Built-in gates for supe actions are in builtin.py.
"""

from .builtin import (
    BUILTIN_GATES,
    # Edit validation
    edit_applied,
    # Command safety
    exit_code_success,
    exit_code_zero,
    file_exists,
    file_written,
    get_gate,
    list_gates,
    no_destructive_git,
    # File validation
    not_sensitive_file,
    path_allowed,
    # Phase transitions
    phase_transition_allowed,
    requires_checkpoint_for_mutation,
    safe_commands,
    string_is_unique,
)
from .exit_code import ExitCodeGate
from .file_gate import FileExistsGate
from .jsonpath import JsonPathAssertion, JsonPathGate
from .patterns import PatternGate

__all__ = [
    # Class-based gates
    "ExitCodeGate",
    "PatternGate",
    "FileExistsGate",
    "JsonPathGate",
    "JsonPathAssertion",
    # Built-in function gates
    "BUILTIN_GATES",
    "get_gate",
    "list_gates",
    "safe_commands",
    "no_destructive_git",
    "requires_checkpoint_for_mutation",
    "exit_code_zero",
    "exit_code_success",
    "path_allowed",
    "not_sensitive_file",
    "file_exists",
    "file_written",
    "string_is_unique",
    "edit_applied",
    "phase_transition_allowed",
]

