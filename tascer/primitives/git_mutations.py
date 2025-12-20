"""Git mutation primitives - STUBS for gated operations.

ACTIONS (mutations):
- git.checkout: Checkout branch or commit
- git.commit: Create a commit (gated)

These are potentially destructive and require checkpoint + explicit approval.
"""

import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CheckoutResult:
    """Result of git checkout operation."""
    
    success: bool
    old_ref: str
    new_ref: str
    files_changed: int
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "old_ref": self.old_ref,
            "new_ref": self.new_ref,
            "files_changed": self.files_changed,
            "error": self.error,
        }


@dataclass
class CommitResult:
    """Result of git commit operation."""
    
    success: bool
    commit_sha: Optional[str]
    message: str
    files_committed: List[str]
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "commit_sha": self.commit_sha,
            "message": self.message,
            "files_committed": self.files_committed,
            "error": self.error,
        }


def git_checkout(
    ref: str,
    repo_root: str,
    create_branch: bool = False,
    checkpoint_manager=None,
) -> CheckoutResult:
    """Checkout a branch or commit.
    
    ACTION: git.checkout (MUTATION)
    
    Requires active checkpoint for safety.
    
    Args:
        ref: Branch name or commit SHA to checkout.
        repo_root: Repository root directory.
        create_branch: If True, create the branch.
        checkpoint_manager: Optional checkpoint manager for safety check.
    
    Returns:
        CheckoutResult with before/after refs.
    """
    # Check checkpoint if manager provided
    if checkpoint_manager:
        checkpoint_manager.require_checkpoint("git.checkout")
    
    # Get current ref
    try:
        old_ref_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        old_ref = old_ref_result.stdout.strip() if old_ref_result.returncode == 0 else ""
    except Exception:
        old_ref = ""
    
    try:
        # Build command
        cmd = ["git", "checkout"]
        if create_branch:
            cmd.append("-b")
        cmd.append(ref)
        
        result = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            return CheckoutResult(
                success=False,
                old_ref=old_ref,
                new_ref="",
                files_changed=0,
                error=result.stderr.strip(),
            )
        
        # Count files changed
        files_changed = 0
        if "files changed" in result.stderr:
            # Parse output
            pass
        
        return CheckoutResult(
            success=True,
            old_ref=old_ref,
            new_ref=ref,
            files_changed=files_changed,
        )
        
    except Exception as e:
        return CheckoutResult(
            success=False,
            old_ref=old_ref,
            new_ref="",
            files_changed=0,
            error=str(e),
        )


def git_commit(
    message: str,
    repo_root: str,
    files: Optional[List[str]] = None,
    all_changes: bool = False,
    checkpoint_manager=None,
    gated_approval: bool = False,
) -> CommitResult:
    """Create a git commit.
    
    ACTION: git.commit (MUTATION, GATED)
    
    This is a gated operation requiring explicit approval.
    Requires active checkpoint for safety.
    
    Args:
        message: Commit message.
        repo_root: Repository root directory.
        files: Specific files to commit. If None and all_changes=True, commits all.
        all_changes: If True, stage and commit all changes.
        checkpoint_manager: Optional checkpoint manager for safety check.
        gated_approval: Must be True to execute (gate).
    
    Returns:
        CommitResult with commit SHA.
    """
    # Gate check
    if not gated_approval:
        return CommitResult(
            success=False,
            commit_sha=None,
            message=message,
            files_committed=[],
            error="git.commit is a gated action. Set gated_approval=True to proceed.",
        )
    
    # Check checkpoint if manager provided
    if checkpoint_manager:
        checkpoint_manager.require_checkpoint("git.commit")
    
    try:
        # Stage files
        if files:
            for file in files:
                subprocess.run(
                    ["git", "add", file],
                    cwd=repo_root,
                    capture_output=True,
                    timeout=10,
                )
        elif all_changes:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=repo_root,
                capture_output=True,
                timeout=10,
            )
        
        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            return CommitResult(
                success=False,
                commit_sha=None,
                message=message,
                files_committed=[],
                error=result.stderr.strip(),
            )
        
        # Get commit SHA
        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        commit_sha = sha_result.stdout.strip() if sha_result.returncode == 0 else None
        
        # Get committed files
        files_result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        files_committed = files_result.stdout.strip().split("\n") if files_result.returncode == 0 else []
        
        return CommitResult(
            success=True,
            commit_sha=commit_sha,
            message=message,
            files_committed=files_committed,
        )
        
    except Exception as e:
        return CommitResult(
            success=False,
            commit_sha=None,
            message=message,
            files_committed=[],
            error=str(e),
        )


def git_log(
    repo_root: str,
    max_count: int = 10,
    format_str: str = "%H|%an|%ae|%s|%ci",
) -> Dict[str, Any]:
    """Get git commit history.
    
    ACTION: git.log (OBSERVATION)
    
    Args:
        repo_root: Repository root directory.
        max_count: Maximum number of commits.
        format_str: Git log format string.
    
    Returns:
        Dict with commits list.
    """
    try:
        result = subprocess.run(
            ["git", "log", f"-{max_count}", f"--format={format_str}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            return {"commits": [], "error": result.stderr.strip()}
        
        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("|")
                if len(parts) >= 5:
                    commits.append({
                        "sha": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "message": parts[3],
                        "date": parts[4],
                    })
        
        return {"commits": commits}
        
    except Exception as e:
        return {"commits": [], "error": str(e)}
