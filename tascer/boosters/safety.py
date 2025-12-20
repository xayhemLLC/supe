"""TASC_SAFETY_GUARDRAILS - Pre-flight safety checks.

Pre-flight checks for dangerous operations:
- Forbids `rm -rf /` patterns
- Forbids writing outside repo root unless permitted
- Forbids printing env vars unless allowlisted
- Enforces max file touch budget without escalation
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class SafetyViolation:
    """A detected safety violation."""
    
    rule: str
    severity: str  # warning | error | critical
    message: str
    matched_pattern: Optional[str] = None


@dataclass
class SafetyCheckResult:
    """Result of safety checks."""
    
    safe: bool
    violations: List[SafetyViolation] = field(default_factory=list)
    
    def to_dict(self):
        return {
            "safe": self.safe,
            "violations": [
                {"rule": v.rule, "severity": v.severity, "message": v.message}
                for v in self.violations
            ],
        }


@dataclass
class SafetyGuardrails:
    """Configurable safety guardrails for command execution.
    
    TASC_SAFETY_GUARDRAILS implementation.
    """
    
    # Repo root - commands should not write outside this
    repo_root: Optional[str] = None
    
    # Maximum number of files that can be touched
    max_file_touch_budget: int = 100
    
    # Allowlisted env vars for printing
    env_allowlist: Set[str] = field(default_factory=lambda: {
        "PATH", "HOME", "USER", "SHELL", "TERM", "LANG",
        "NODE_ENV", "PYTHON_PATH", "VIRTUAL_ENV",
    })
    
    # Dangerous command patterns (critical - always blocked)
    critical_patterns: List[str] = field(default_factory=lambda: [
        r"rm\s+-rf\s+/\s*$",           # rm -rf /
        r"rm\s+-rf\s+/\*",             # rm -rf /*
        r"rm\s+-rf\s+~",               # rm -rf ~
        r"rm\s+-rf\s+\$HOME",          # rm -rf $HOME
        r":\s*\(\)\s*{\s*:\s*\|\s*:\s*&\s*}",  # Fork bomb
        r">\s*/dev/sd[a-z]",           # Write to raw disk
        r"mkfs\.",                     # Format filesystem
        r"dd\s+if=.*of=/dev/",         # DD to device
        r"chmod\s+-R\s+777\s+/",       # chmod 777 /
    ])
    
    # Dangerous patterns (error - blocked by default)
    error_patterns: List[str] = field(default_factory=lambda: [
        r"sudo\s+rm\s+-rf",
        r"curl\s+.*\|\s*sh",           # Pipe curl to shell
        r"wget\s+.*\|\s*sh",
        r"eval\s+\$\(",                # Eval subshell
        r">\s*/etc/",                  # Write to /etc
        r"rm\s+-rf\s+\.",              # rm -rf .
    ])
    
    # Warning patterns (logged but allowed)
    warning_patterns: List[str] = field(default_factory=lambda: [
        r"rm\s+-rf",                   # Any rm -rf
        r"git\s+push\s+-f",            # Force push
        r"git\s+reset\s+--hard",       # Hard reset
        r"npm\s+publish",              # Publishing
        r"pip\s+install\s+--user",     # User install
    ])
    
    # Env vars that should never be printed
    secret_env_patterns: List[str] = field(default_factory=lambda: [
        r".*KEY.*",
        r".*SECRET.*",
        r".*TOKEN.*",
        r".*PASSWORD.*",
        r".*CREDENTIAL.*",
        r".*API_.*",
        r".*AUTH.*",
    ])
    
    def check_command(self, command: str) -> SafetyCheckResult:
        """Check a command for safety violations.
        
        Args:
            command: The command string to check.
        
        Returns:
            SafetyCheckResult with violations list.
        """
        violations = []
        
        # Check critical patterns
        for pattern in self.critical_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                violations.append(SafetyViolation(
                    rule="CRITICAL_COMMAND",
                    severity="critical",
                    message=f"Critical unsafe command pattern detected",
                    matched_pattern=pattern,
                ))
        
        # Check error patterns
        for pattern in self.error_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                violations.append(SafetyViolation(
                    rule="DANGEROUS_COMMAND",
                    severity="error",
                    message=f"Dangerous command pattern detected",
                    matched_pattern=pattern,
                ))
        
        # Check warning patterns
        for pattern in self.warning_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                violations.append(SafetyViolation(
                    rule="RISKY_COMMAND",
                    severity="warning",
                    message=f"Potentially risky command pattern",
                    matched_pattern=pattern,
                ))
        
        # Check for secret env var exposure
        env_match = re.search(r"echo\s+\$(\w+)|printenv\s+(\w+)", command)
        if env_match:
            var_name = env_match.group(1) or env_match.group(2)
            if var_name not in self.env_allowlist:
                for pattern in self.secret_env_patterns:
                    if re.match(pattern, var_name, re.IGNORECASE):
                        violations.append(SafetyViolation(
                            rule="SECRET_EXPOSURE",
                            severity="error",
                            message=f"Potential secret env var exposure: {var_name}",
                        ))
                        break
        
        # Check repo boundary
        if self.repo_root:
            # Look for paths outside repo
            path_matches = re.findall(r'(?:>|>>|<)\s*(/[^\s]+)', command)
            for path in path_matches:
                if not path.startswith(self.repo_root):
                    violations.append(SafetyViolation(
                        rule="REPO_BOUNDARY",
                        severity="error",
                        message=f"Path outside repo root: {path}",
                    ))
        
        # Determine overall safety
        has_critical = any(v.severity == "critical" for v in violations)
        has_error = any(v.severity == "error" for v in violations)
        
        return SafetyCheckResult(
            safe=not (has_critical or has_error),
            violations=violations,
        )
    
    def check_file_budget(self, files_touched: int) -> SafetyCheckResult:
        """Check if file touch count is within budget.
        
        Args:
            files_touched: Number of files being modified.
        
        Returns:
            SafetyCheckResult with budget violation if exceeded.
        """
        if files_touched > self.max_file_touch_budget:
            return SafetyCheckResult(
                safe=False,
                violations=[SafetyViolation(
                    rule="FILE_BUDGET",
                    severity="error",
                    message=f"File touch budget exceeded: {files_touched} > {self.max_file_touch_budget}",
                )],
            )
        return SafetyCheckResult(safe=True)


def check_command_safety(
    command: str,
    repo_root: Optional[str] = None,
) -> SafetyCheckResult:
    """Convenience function to check command safety.
    
    Args:
        command: Command to check.
        repo_root: Optional repo root for boundary checks.
    
    Returns:
        SafetyCheckResult.
    """
    guardrails = SafetyGuardrails(repo_root=repo_root)
    return guardrails.check_command(command)
