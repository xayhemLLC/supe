"""Validation gates for asserting expected conditions.

Gates are reusable validation checks that can be composed to validate
tasc execution results. Each gate produces a GateResult with pass/fail
status and evidence.
"""

from .exit_code import ExitCodeGate
from .patterns import PatternGate
from .file_gate import FileExistsGate
from .jsonpath import JsonPathGate, JsonPathAssertion

__all__ = [
    "ExitCodeGate",
    "PatternGate",
    "FileExistsGate",
    "JsonPathGate",
    "JsonPathAssertion",
]
