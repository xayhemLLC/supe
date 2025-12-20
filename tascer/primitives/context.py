"""TASC_CORE_CONTEXT_SNAPSHOT - Capture execution context.

Hypothesis: "We can record enough state to reproduce and audit the tasc."
Validator: context artifact exists and contains required fields.
"""

import os
import platform
import shutil
import subprocess
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from ..contracts import Context, GitState


def _get_toolchain_version(cmd: str) -> Optional[str]:
    """Get version of a toolchain command if available."""
    try:
        result = subprocess.run(
            [cmd, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Usually first line contains version
            first_line = result.stdout.strip().split("\n")[0]
            return first_line
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _detect_toolchain_versions(tools: Optional[List[str]] = None) -> Dict[str, str]:
    """Detect versions of common development tools."""
    if tools is None:
        tools = ["node", "npm", "npx", "pnpm", "yarn", "python", "python3", "pip", "ruff", "pytest"]
    
    versions = {}
    for tool in tools:
        if shutil.which(tool):
            version = _get_toolchain_version(tool)
            if version:
                versions[tool] = version
    return versions


def _capture_git_state(repo_root: str) -> Optional[GitState]:
    """Capture git repository state."""
    try:
        # Check if it's a git repo
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None
        
        # Get branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else ""
        
        # Get commit
        commit_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        commit = commit_result.stdout.strip() if commit_result.returncode == 0 else ""
        
        # Check if dirty
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        dirty = bool(status_result.stdout.strip()) if status_result.returncode == 0 else False
        status = status_result.stdout.strip() if status_result.returncode == 0 else ""
        
        # Get diff stat
        diff_result = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        diff_stat = diff_result.stdout.strip() if diff_result.returncode == 0 else ""
        
        return GitState(
            branch=branch,
            commit=commit,
            dirty=dirty,
            diff_stat=diff_stat,
            status=status,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def capture_context(
    run_id: Optional[str] = None,
    tasc_id: str = "",
    repo_root: Optional[str] = None,
    env_allowlist: Optional[List[str]] = None,
    tools_to_check: Optional[List[str]] = None,
    permissions: Optional[List[str]] = None,
) -> Context:
    """Capture current execution context snapshot.
    
    TASC_CORE_CONTEXT_SNAPSHOT implementation.
    
    Args:
        run_id: Unique run identifier. Generated if not provided.
        tasc_id: Tasc identifier.
        repo_root: Repository root path. Defaults to cwd.
        env_allowlist: List of env var names to capture (never secrets!).
        tools_to_check: List of tool commands to check versions for.
        permissions: List of permissions granted to the action.
    
    Returns:
        A Context object with captured state.
    """
    if run_id is None:
        run_id = str(uuid.uuid4())[:8]
    
    cwd = os.getcwd()
    if repo_root is None:
        repo_root = cwd
    
    # Capture allowed environment variables
    captured_env = {}
    if env_allowlist:
        for var in env_allowlist:
            if var in os.environ:
                captured_env[var] = os.environ[var]
    
    # Capture toolchain versions
    toolchain = _detect_toolchain_versions(tools_to_check)
    
    # Capture git state
    git_state = _capture_git_state(repo_root)
    
    return Context(
        run_id=run_id,
        tasc_id=tasc_id,
        timestamp_start=datetime.utcnow().isoformat(),
        repo_root=os.path.abspath(repo_root),
        cwd=cwd,
        os_name=platform.system(),
        arch=platform.machine(),
        toolchain_versions=toolchain,
        git_state=git_state,
        env_allowlist=captured_env,
        network_mode="online",  # Default assumption
        hostnames_ports=[],
        permissions_granted=permissions or [],
    )
