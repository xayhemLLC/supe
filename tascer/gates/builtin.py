"""Built-in validation gates for supe actions.

These gates provide safety validation for action execution:
- Pre-gates run BEFORE execution (can block)
- Post-gates run AFTER execution (validate results)

Gates return GateResult(name, passed, message).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..contracts import GateResult

if TYPE_CHECKING:
    from ..contracts import ValidationRecord


# ─────────────────────────────────────────────────────────────────────────────
# Command Safety Gates (Pre-gates for SupeRun)
# ─────────────────────────────────────────────────────────────────────────────

# Patterns that are always blocked
BLOCKED_PATTERNS = [
    r"\brm\s+-rf\s+/",  # rm -rf /
    r"\brm\s+-rf\s+~",  # rm -rf ~
    r"\brm\s+-rf\s+\*",  # rm -rf *
    r":\(\)\s*\{\s*:\|\:\s*&\s*\}\s*;",  # Fork bomb
    r">\s*/dev/sd[a-z]",  # Write to raw disk
    r"mkfs\.",  # Format filesystem
    r"dd\s+if=.+of=/dev/",  # dd to device
    r"\bshutdown\b",  # Shutdown
    r"\breboot\b",  # Reboot
    r"\binit\s+[0-6]",  # Init level change
    r"chmod\s+-R\s+777\s+/",  # chmod 777 /
    r"chown\s+-R\s+.+\s+/\s*$",  # chown -R ... /
]

# Dangerous git commands
DANGEROUS_GIT_PATTERNS = [
    r"git\s+push\s+.*--force",  # Force push
    r"git\s+push\s+-f\b",  # Force push short
    r"git\s+reset\s+--hard",  # Hard reset
    r"git\s+clean\s+-f",  # Clean force
    r"git\s+checkout\s+\.",  # Checkout all
    r"git\s+restore\s+\.",  # Restore all
    r"git\s+branch\s+-D",  # Delete branch force
]

# Commands that need checkpoint
MUTATION_COMMANDS = [
    r"\brm\b",
    r"\bmv\b",
    r"\bcp\b",
    r"\bmkdir\b",
    r"\brmdir\b",
    r"\btouch\b",
    r"\bchmod\b",
    r"\bchown\b",
    r"\bgit\s+commit",
    r"\bgit\s+push",
    r"\bgit\s+merge",
    r"\bgit\s+rebase",
    r"\bgit\s+reset",
    r"\bgit\s+checkout",
    r"\bnpm\s+install",
    r"\bpip\s+install",
    r"\buv\s+pip\s+install",
]


def safe_commands(record: ValidationRecord, phase: str) -> GateResult:
    """Block dangerous commands that could harm the system."""
    command = record.tool_input.get("command", "")

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return GateResult(
                "safe_commands",
                False,
                f"BLOCKED: Command matches dangerous pattern: {pattern}",
            )

    return GateResult("safe_commands", True, f"Command allowed: {command[:50]}...")


def no_destructive_git(record: ValidationRecord, phase: str) -> GateResult:
    """Block destructive git commands unless explicitly allowed."""
    command = record.tool_input.get("command", "")

    for pattern in DANGEROUS_GIT_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return GateResult(
                "no_destructive_git",
                False,
                f"BLOCKED: Destructive git command: {pattern}. "
                "Use --allow-destructive-git to override.",
            )

    return GateResult("no_destructive_git", True, "Git command is safe")


def requires_checkpoint_for_mutation(
    record: ValidationRecord, phase: str
) -> GateResult:
    """Require checkpoint before mutation commands."""
    command = record.tool_input.get("command", "")

    is_mutation = any(
        re.search(pattern, command, re.IGNORECASE) for pattern in MUTATION_COMMANDS
    )

    if is_mutation:
        # Check if checkpoint exists (would be in context)
        has_checkpoint = record.context.get("has_checkpoint", False)
        if not has_checkpoint:
            return GateResult(
                "requires_checkpoint_for_mutation",
                False,
                "Mutation command requires checkpoint. Run SupeCheckpoint first.",
            )

    return GateResult("requires_checkpoint_for_mutation", True, "Checkpoint check passed")


# ─────────────────────────────────────────────────────────────────────────────
# Exit Code Gates (Post-gates for SupeRun)
# ─────────────────────────────────────────────────────────────────────────────


def exit_code_zero(record: ValidationRecord, phase: str) -> GateResult:
    """Validate that command exited with code 0."""
    exit_code = record.tool_output.get("exit_code", -1)

    if exit_code == 0:
        return GateResult("exit_code_zero", True, "Command succeeded (exit code 0)")

    return GateResult(
        "exit_code_zero",
        False,
        f"Command failed with exit code {exit_code}",
    )


def exit_code_success(record: ValidationRecord, phase: str) -> GateResult:
    """Validate that command exited successfully (0 or acceptable codes)."""
    exit_code = record.tool_output.get("exit_code", -1)
    acceptable_codes = record.context.get("acceptable_exit_codes", [0])

    if exit_code in acceptable_codes:
        return GateResult(
            "exit_code_success", True, f"Command succeeded (exit code {exit_code})"
        )

    return GateResult(
        "exit_code_success",
        False,
        f"Command failed with exit code {exit_code}. Acceptable: {acceptable_codes}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# File Path Gates (Pre-gates for SupeRead, SupeWrite, SupeEdit)
# ─────────────────────────────────────────────────────────────────────────────

# Paths that should never be written to
PROTECTED_PATHS = [
    "/etc/passwd",
    "/etc/shadow",
    "/etc/sudoers",
    "/etc/hosts",
    "/boot/",
    "/usr/bin/",
    "/usr/sbin/",
    "/bin/",
    "/sbin/",
]

# Sensitive file patterns
SENSITIVE_PATTERNS = [
    r"\.env$",
    r"\.env\..+$",
    r"credentials\.json$",
    r"secrets\.yaml$",
    r"secrets\.yml$",
    r"\.pem$",
    r"\.key$",
    r"id_rsa",
    r"id_ed25519",
    r"\.aws/credentials",
    r"\.ssh/",
]


def path_allowed(record: ValidationRecord, phase: str) -> GateResult:
    """Validate that file path is allowed for modification."""
    file_path = record.tool_input.get("file_path", "")

    # Check protected paths
    for protected in PROTECTED_PATHS:
        if file_path.startswith(protected):
            return GateResult(
                "path_allowed",
                False,
                f"BLOCKED: Cannot modify protected path: {protected}",
            )

    # Check if path is within allowed directories
    allowed_dirs = record.context.get("allowed_directories", [os.getcwd()])
    path = Path(file_path).resolve()

    is_allowed = any(
        str(path).startswith(str(Path(d).resolve())) for d in allowed_dirs
    )

    if not is_allowed:
        return GateResult(
            "path_allowed",
            False,
            f"BLOCKED: Path {file_path} is outside allowed directories",
        )

    return GateResult("path_allowed", True, f"Path allowed: {file_path}")


def not_sensitive_file(record: ValidationRecord, phase: str) -> GateResult:
    """Warn about sensitive files (non-blocking by default)."""
    file_path = record.tool_input.get("file_path", "")

    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, file_path, re.IGNORECASE):
            # Warning, not blocking
            return GateResult(
                "not_sensitive_file",
                True,  # Pass but with warning
                f"WARNING: Modifying potentially sensitive file: {file_path}",
            )

    return GateResult("not_sensitive_file", True, "File is not flagged as sensitive")


def file_exists(record: ValidationRecord, phase: str) -> GateResult:
    """Validate that file exists (for read operations)."""
    file_path = record.tool_input.get("file_path", "")

    if os.path.exists(file_path):
        return GateResult("file_exists", True, f"File exists: {file_path}")

    return GateResult("file_exists", False, f"File not found: {file_path}")


def file_written(record: ValidationRecord, phase: str) -> GateResult:
    """Validate that file was written successfully."""
    file_path = record.tool_input.get("file_path", "")
    expected_hash = record.tool_output.get("content_hash")

    if not os.path.exists(file_path):
        return GateResult("file_written", False, f"File not created: {file_path}")

    if expected_hash:
        import hashlib

        with open(file_path, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()[:16]
        if actual_hash != expected_hash:
            return GateResult(
                "file_written",
                False,
                f"File hash mismatch. Expected: {expected_hash}, Got: {actual_hash}",
            )

    return GateResult("file_written", True, f"File written successfully: {file_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Edit Gates (Pre-gates for SupeEdit)
# ─────────────────────────────────────────────────────────────────────────────


def string_is_unique(record: ValidationRecord, phase: str) -> GateResult:
    """Validate that old_string is unique in file (unless replace_all)."""
    file_path = record.tool_input.get("file_path", "")
    old_string = record.tool_input.get("old_string", "")
    replace_all = record.tool_input.get("replace_all", False)

    if replace_all:
        return GateResult("string_is_unique", True, "replace_all=True, uniqueness not required")

    if not os.path.exists(file_path):
        return GateResult("string_is_unique", False, f"File not found: {file_path}")

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return GateResult("string_is_unique", False, f"Cannot read file: {e}")

    count = content.count(old_string)

    if count == 0:
        return GateResult(
            "string_is_unique",
            False,
            "old_string not found in file. Check for exact match including whitespace.",
        )

    if count > 1:
        return GateResult(
            "string_is_unique",
            False,
            f"old_string appears {count} times. Add more context to make it unique, "
            "or use replace_all=True.",
        )

    return GateResult("string_is_unique", True, "old_string is unique in file")


def edit_applied(record: ValidationRecord, phase: str) -> GateResult:
    """Validate that edit was applied correctly."""
    file_path = record.tool_input.get("file_path", "")
    new_string = record.tool_input.get("new_string", "")
    old_string = record.tool_input.get("old_string", "")

    if not os.path.exists(file_path):
        return GateResult("edit_applied", False, f"File not found after edit: {file_path}")

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return GateResult("edit_applied", False, f"Cannot read file after edit: {e}")

    if new_string and new_string not in content:
        return GateResult(
            "edit_applied",
            False,
            "new_string not found in file after edit",
        )

    if old_string in content and not record.tool_input.get("replace_all", False):
        return GateResult(
            "edit_applied",
            False,
            "old_string still present in file after edit",
        )

    return GateResult("edit_applied", True, "Edit applied successfully")


# ─────────────────────────────────────────────────────────────────────────────
# Agent Gates (Pre-gates for SupeTask)
# ─────────────────────────────────────────────────────────────────────────────

VALID_AGENT_TYPES = ["explore", "plan", "build", "validate", "review", "document", "general"]


def agent_type_valid(record: ValidationRecord, phase: str) -> GateResult:
    """Validate that agent_type is recognized."""
    agent_type = record.tool_input.get("agent_type", "")

    if agent_type in VALID_AGENT_TYPES:
        return GateResult("agent_type_valid", True, f"Agent type valid: {agent_type}")

    return GateResult(
        "agent_type_valid",
        False,
        f"Unknown agent type: {agent_type}. Valid types: {VALID_AGENT_TYPES}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Phase Transition Gates (Pre-gates for SupeTransition)
# ─────────────────────────────────────────────────────────────────────────────


def phase_transition_allowed(record: ValidationRecord, phase: str) -> GateResult:
    """Validate that phase transition is allowed by CUF gates."""
    # This delegates to the phase_gates module
    from tasc import TascPhase
    from tasc.phase_gates import get_default_registry

    to_phase_str = record.tool_input.get("to_phase", "")
    validate_gates = record.tool_input.get("validate_gates", True)

    if not validate_gates:
        return GateResult(
            "phase_transition_allowed",
            True,
            "Gate validation disabled for this transition",
        )

    try:
        to_phase = TascPhase(to_phase_str)
    except ValueError:
        return GateResult(
            "phase_transition_allowed",
            False,
            f"Invalid phase: {to_phase_str}",
        )

    # Get current phase from context
    current_phase_str = record.context.get("current_phase", "explore")
    try:
        from_phase = TascPhase(current_phase_str)
    except ValueError:
        from_phase = TascPhase.EXPLORE

    # Run phase gates
    registry = get_default_registry()

    # We need a Tasc object - get from context or create minimal one
    tasc_data = record.context.get("tasc")
    if tasc_data:
        from tasc import Tasc
        tasc = Tasc.from_dict(tasc_data)
    else:
        # Create minimal tasc for validation
        from tasc import Tasc
        tasc = Tasc(
            id="temp",
            status="active",
            title="",
            additional_notes="",
            testing_instructions=record.context.get("testing_instructions", ""),
            desired_outcome=record.context.get("desired_outcome", ""),
        )
        tasc.phase = from_phase

    validation = registry.validate_transition(tasc, from_phase, to_phase)

    if validation.all_passed:
        return GateResult(
            "phase_transition_allowed",
            True,
            f"Transition {from_phase.value} → {to_phase.value} allowed",
        )

    failures = validation.blocking_failures
    failure_msgs = "; ".join(f"{f.gate_name}: {f.message}" for f in failures)
    return GateResult(
        "phase_transition_allowed",
        False,
        f"Transition blocked: {failure_msgs}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Gate Registry
# ─────────────────────────────────────────────────────────────────────────────

BUILTIN_GATES: dict[str, Any] = {
    # Command safety
    "safe_commands": safe_commands,
    "no_destructive_git": no_destructive_git,
    "requires_checkpoint_for_mutation": requires_checkpoint_for_mutation,
    # Exit codes
    "exit_code_zero": exit_code_zero,
    "exit_code_success": exit_code_success,
    # File paths
    "path_allowed": path_allowed,
    "not_sensitive_file": not_sensitive_file,
    "file_exists": file_exists,
    "file_written": file_written,
    # Edit validation
    "string_is_unique": string_is_unique,
    "edit_applied": edit_applied,
    # Agent validation
    "agent_type_valid": agent_type_valid,
    # Phase transitions
    "phase_transition_allowed": phase_transition_allowed,
}


def get_gate(name: str) -> Any | None:
    """Get a built-in gate by name."""
    return BUILTIN_GATES.get(name)


def list_gates() -> list[str]:
    """List all built-in gate names."""
    return list(BUILTIN_GATES.keys())
