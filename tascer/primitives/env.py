"""Environment primitives.

ACTIONS:
- env.read: Read allow-listed environment variables
- env.set: Set environment variable (ephemeral scope)
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set


# Default allowlist of safe environment variables
DEFAULT_ENV_ALLOWLIST = [
    "PATH",
    "HOME",
    "USER",
    "SHELL",
    "TERM",
    "LANG",
    "LC_ALL",
    "TZ",
    "PWD",
    "NODE_ENV",
    "PYTHON_ENV",
    "DEBUG",
    "LOG_LEVEL",
]

# Variables that are NEVER allowed to be read
ENV_DENYLIST = [
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DATABASE_PASSWORD",
    "DB_PASSWORD",
    "SECRET_KEY",
    "PRIVATE_KEY",
    "API_KEY",
    "API_SECRET",
    "PASSWORD",
    "TOKEN",
    "CREDENTIALS",
]


@dataclass
class EnvReadResult:
    """Result of reading environment variables."""
    
    variables: Dict[str, str]
    requested: List[str]
    allowed: List[str]
    denied: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "variables": self.variables,
            "requested": self.requested,
            "allowed": self.allowed,
            "denied": self.denied,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class EnvSetResult:
    """Result of setting an environment variable."""
    
    variable: str
    old_value: Optional[str]
    new_value: str
    success: bool
    scope: str  # ephemeral, process
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable": self.variable,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "success": self.success,
            "scope": self.scope,
        }


# Ephemeral env storage (for sandbox scope)
_ephemeral_env: Dict[str, str] = {}
_original_env: Dict[str, str] = {}


def _is_denied(var: str) -> bool:
    """Check if variable is in denylist."""
    var_upper = var.upper()
    for denied in ENV_DENYLIST:
        if denied in var_upper:
            return True
    return False


def env_read(
    variables: Optional[List[str]] = None,
    allowlist: Optional[List[str]] = None,
) -> EnvReadResult:
    """Read allow-listed environment variables.
    
    ACTION: env.read
    
    This action will NEVER return sensitive variables like API keys,
    passwords, or tokens even if requested.
    
    Args:
        variables: Specific variables to read. If None, reads allowlist.
        allowlist: Custom allowlist. Defaults to DEFAULT_ENV_ALLOWLIST.
    
    Returns:
        EnvReadResult with allowed variables and which were denied.
    """
    if allowlist is None:
        allowlist = DEFAULT_ENV_ALLOWLIST
    
    if variables is None:
        variables = allowlist
    
    result_vars = {}
    allowed = []
    denied = []
    
    for var in variables:
        # Check denylist first
        if _is_denied(var):
            denied.append(var)
            continue
        
        # Check allowlist
        if var not in allowlist:
            denied.append(var)
            continue
        
        # Get value (check ephemeral first, then real env)
        if var in _ephemeral_env:
            value = _ephemeral_env[var]
        elif var in os.environ:
            value = os.environ[var]
        else:
            continue  # Variable doesn't exist
        
        result_vars[var] = value
        allowed.append(var)
    
    return EnvReadResult(
        variables=result_vars,
        requested=variables,
        allowed=allowed,
        denied=denied,
        timestamp=datetime.now(),
    )


def env_set(
    variable: str,
    value: str,
    scope: str = "ephemeral",
) -> EnvSetResult:
    """Set environment variable in ephemeral scope.
    
    ACTION: env.set (MUTATION)
    
    This action only sets variables in ephemeral scope by default,
    meaning they don't affect the actual process environment until
    explicitly applied.
    
    Args:
        variable: Variable name to set.
        value: Value to set.
        scope: Scope for the change (ephemeral, process).
    
    Returns:
        EnvSetResult with old and new values.
    """
    # Check denylist - can't set sensitive-looking variables
    if _is_denied(variable):
        return EnvSetResult(
            variable=variable,
            old_value=None,
            new_value=value,
            success=False,
            scope=scope,
        )
    
    old_value = None
    
    if scope == "ephemeral":
        # Store in ephemeral scope
        if variable in _ephemeral_env:
            old_value = _ephemeral_env[variable]
        elif variable in os.environ:
            old_value = os.environ[variable]
        
        _ephemeral_env[variable] = value
        
    elif scope == "process":
        # Set in actual process environment
        if variable in os.environ:
            old_value = os.environ[variable]
            _original_env[variable] = old_value
        
        os.environ[variable] = value
    
    return EnvSetResult(
        variable=variable,
        old_value=old_value,
        new_value=value,
        success=True,
        scope=scope,
    )


def env_reset(variable: Optional[str] = None) -> Dict[str, Any]:
    """Reset environment to original state.
    
    Args:
        variable: Specific variable to reset. If None, resets all.
    
    Returns:
        Dict with reset information.
    """
    reset_vars = []
    
    if variable:
        # Reset specific variable
        if variable in _ephemeral_env:
            del _ephemeral_env[variable]
            reset_vars.append(variable)
        if variable in _original_env:
            os.environ[variable] = _original_env[variable]
            del _original_env[variable]
            reset_vars.append(variable)
    else:
        # Reset all
        _ephemeral_env.clear()
        for var, original in _original_env.items():
            os.environ[var] = original
            reset_vars.append(var)
        _original_env.clear()
    
    return {
        "reset_variables": reset_vars,
        "timestamp": datetime.now().isoformat(),
    }


def get_ephemeral_env() -> Dict[str, str]:
    """Get all ephemeral environment variables."""
    return dict(_ephemeral_env)
