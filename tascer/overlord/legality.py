"""Action Legality and Safety System.

Before every action:
- Permission check
- Scope check (repo root, sandbox)
- Risk escalation rules
- Diff / blast-radius estimation
- Secret leakage prevention
- Destructive pattern detection
"""

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


class SecurityViolation(Exception):
    """Raised when an action violates security constraints."""
    pass


@dataclass
class LegalityCheck:
    """Result of legality check for an action."""
    
    is_legal: bool
    action_id: str
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    requires_escalation: bool = False
    escalation_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_legal": self.is_legal,
            "action_id": self.action_id,
            "violations": self.violations,
            "warnings": self.warnings,
            "requires_escalation": self.requires_escalation,
            "escalation_reason": self.escalation_reason,
        }


# Patterns that indicate destructive operations
DESTRUCTIVE_PATTERNS = [
    r"rm\s+-rf\s+/",  # rm -rf /
    r"rm\s+-rf\s+\*",  # rm -rf *
    r"rm\s+-rf\s+\.",  # rm -rf .
    r"chmod\s+-R\s+777",  # chmod -R 777
    r">\s*/dev/",  # Redirecting to devices
    r"dd\s+if=.*/dev/",  # dd from devices
    r"mkfs\.",  # Formatting filesystems
    r":\(\)\s*{\s*:\s*\|",  # Fork bomb
    r"curl.*\|\s*bash",  # Piping curl to bash
    r"wget.*\|\s*bash",  # Piping wget to bash
]

# Patterns for secret/credential leakage
SECRET_PATTERNS = [
    r"password\s*=",
    r"api_key\s*=",
    r"secret\s*=",
    r"token\s*=",
    r"bearer\s+",
    r"aws_secret",
    r"private_key",
    r"BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE",
]

# Maximum allowed diff sizes
MAX_DIFF_LINES = 5000
MAX_AFFECTED_FILES = 100


def check_action_legality(
    action_id: str,
    inputs: Dict[str, Any],
    permissions: Set[str],
    repo_root: Optional[str] = None,
    in_sandbox: bool = False,
    has_checkpoint: bool = False,
) -> LegalityCheck:
    """Check if an action is legal given current context.
    
    Args:
        action_id: Action to execute.
        inputs: Action inputs/arguments.
        permissions: Currently granted permissions.
        repo_root: Repository root for scope checking.
        in_sandbox: Whether in sandbox mode.
        has_checkpoint: Whether checkpoint is active.
    
    Returns:
        LegalityCheck with violations and warnings.
    """
    violations = []
    warnings = []
    requires_escalation = False
    escalation_reason = None
    
    # Check for destructive patterns in commands
    command = inputs.get("command", "")
    if isinstance(command, str):
        for pattern in DESTRUCTIVE_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                violations.append(f"Destructive pattern detected: {pattern}")
    
    # Check for secret leakage in outputs/inputs
    for key, value in inputs.items():
        if isinstance(value, str):
            for pattern in SECRET_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    warnings.append(f"Potential secret in input '{key}'")
    
    # Scope checking - ensure paths are within repo root
    if repo_root:
        for key in ["path", "file", "target", "destination"]:
            if key in inputs and isinstance(inputs[key], str):
                path = os.path.abspath(inputs[key])
                if not path.startswith(os.path.abspath(repo_root)):
                    violations.append(
                        f"Path '{path}' is outside repository root"
                    )
    
    # Check mutation actions require checkpoint
    mutation_actions = {
        "file.write", "file.patch", "file.delete",
        "git.checkout", "git.commit",
        "process.start", "process.stop", "process.restart",
    }
    if action_id in mutation_actions and not has_checkpoint:
        violations.append(
            f"Action '{action_id}' requires active checkpoint"
        )
    
    # Check sandbox-only actions
    sandbox_only_actions = {"frontend.inject"}
    if action_id in sandbox_only_actions and not in_sandbox:
        violations.append(
            f"Action '{action_id}' can only run in sandbox mode"
        )
    
    # Check gated actions
    gated_actions = {"git.commit"}
    if action_id in gated_actions:
        if "gated_actions" not in permissions:
            requires_escalation = True
            escalation_reason = f"Action '{action_id}' requires explicit approval"
    
    # Estimate blast radius for file operations
    if action_id == "file.delete":
        pattern = inputs.get("pattern", "")
        if "*" in pattern or "?" in pattern:
            warnings.append("Glob pattern in delete - verify scope")
            requires_escalation = True
            escalation_reason = "Bulk delete requires approval"
    
    # Check permissions
    action_permissions = {
        "terminal.run": {"terminal"},
        "terminal.watch": {"terminal"},
        "file.read": {"file_read"},
        "file.write": {"file_write"},
        "file.delete": {"file_write", "file_delete"},
        "git.status": {"git"},
        "git.commit": {"git", "git_write", "git_commit"},
        "http.request": {"network"},
        "browser.capture": {"browser"},
        "process.start": {"process"},
    }
    
    required_perms = action_permissions.get(action_id, set())
    missing_perms = required_perms - permissions
    if missing_perms:
        violations.append(f"Missing permissions: {', '.join(missing_perms)}")
    
    return LegalityCheck(
        is_legal=len(violations) == 0,
        action_id=action_id,
        violations=violations,
        warnings=warnings,
        requires_escalation=requires_escalation,
        escalation_reason=escalation_reason,
    )


def is_action_legal(
    action_id: str,
    inputs: Dict[str, Any],
    permissions: Set[str],
    **kwargs,
) -> bool:
    """Quick check if action is legal."""
    check = check_action_legality(action_id, inputs, permissions, **kwargs)
    return check.is_legal


def check_command_safety(command: str) -> tuple[bool, List[str]]:
    """Check if a shell command is safe to run.
    
    Returns:
        Tuple of (is_safe, list of concerns).
    """
    concerns = []
    
    for pattern in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            concerns.append(f"Matches destructive pattern: {pattern}")
    
    # Check for common dangerous commands
    dangerous_commands = [
        "shutdown", "reboot", "halt",
        "su ", "sudo ",
        "crontab ",
        "passwd",
    ]
    for cmd in dangerous_commands:
        if cmd in command.lower():
            concerns.append(f"Contains dangerous command: {cmd.strip()}")
    
    return len(concerns) == 0, concerns


def estimate_blast_radius(
    action_id: str,
    inputs: Dict[str, Any],
) -> Dict[str, Any]:
    """Estimate the blast radius of an action.
    
    Returns:
        Dict with estimated impact metrics.
    """
    return {
        "action": action_id,
        "estimated_files_affected": 1,  # Simplified
        "estimated_lines_changed": 0,
        "reversible": True,
        "scope": "local",
    }
