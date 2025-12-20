"""TASC_CORE_GIT_STATE_CAPTURE - Capture git repository state.

Hypothesis: "We can capture authoritative repo state."
Evidence: git status, git diff, git diff --stat, HEAD sha.
"""

import subprocess
from typing import Optional

from ..contracts import GitState


def capture_git_state(repo_root: str) -> GitState:
    """Capture authoritative git repository state.
    
    TASC_CORE_GIT_STATE_CAPTURE implementation.
    
    Args:
        repo_root: Path to git repository root.
    
    Returns:
        GitState with branch, commit, dirty status, diff stats.
    
    Raises:
        ValueError: If path is not a git repository.
    """
    # Check if it's a git repo
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            raise ValueError(f"Not a git repository: {repo_root}")
    except FileNotFoundError:
        raise ValueError("git command not found")
    
    # Get branch
    branch_result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=5,
    )
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else ""
    
    # Get commit SHA
    commit_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=5,
    )
    commit = commit_result.stdout.strip() if commit_result.returncode == 0 else ""
    
    # Get porcelain status
    status_result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=10,
    )
    status = status_result.stdout.strip() if status_result.returncode == 0 else ""
    dirty = bool(status)
    
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


def get_git_diff(repo_root: str, cached: bool = False) -> str:
    """Get the full git diff.
    
    Args:
        repo_root: Path to git repository.
        cached: If True, show staged changes. Otherwise unstaged.
    
    Returns:
        Full diff output.
    """
    cmd = ["git", "diff"]
    if cached:
        cmd.append("--cached")
    
    result = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout if result.returncode == 0 else ""


def get_untracked_files(repo_root: str) -> list:
    """Get list of untracked files.
    
    Args:
        repo_root: Path to git repository.
    
    Returns:
        List of untracked file paths.
    """
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode == 0:
        return [f for f in result.stdout.strip().split("\n") if f]
    return []
