"""Sandbox primitives - Filesystem isolation for safe exploration.

ACTIONS:
- sandbox.enter: Enter sandbox mode (mutations are provisional)
- sandbox.exit: Exit sandbox (commit or discard changes)

In sandbox mode, all mutations are reversible until explicitly committed.
Uses git worktree or directory copy for isolation.
"""

import hashlib
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

from .file_ops import snapshot_directory


@dataclass
class SandboxState:
    """State of an active sandbox."""
    
    sandbox_id: str
    created_at: datetime
    baseline_hash: str
    root_dir: str
    sandbox_dir: str
    isolation_method: str  # "git_worktree", "directory_copy", "symlink"
    mutations: List[Dict[str, Any]] = field(default_factory=list)
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sandbox_id": self.sandbox_id,
            "created_at": self.created_at.isoformat(),
            "baseline_hash": self.baseline_hash,
            "root_dir": self.root_dir,
            "sandbox_dir": self.sandbox_dir,
            "isolation_method": self.isolation_method,
            "mutations": self.mutations,
            "active": self.active,
        }


@dataclass
class SandboxEnterResult:
    """Result of entering sandbox mode."""
    
    sandbox_id: str
    baseline_hash: str
    sandbox_dir: str
    isolation_method: str
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sandbox_id": self.sandbox_id,
            "baseline_hash": self.baseline_hash,
            "sandbox_dir": self.sandbox_dir,
            "isolation_method": self.isolation_method,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class SandboxExitResult:
    """Result of exiting sandbox mode."""
    
    sandbox_id: str
    action: str  # "commit" or "discard"
    files_affected: List[str]
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sandbox_id": self.sandbox_id,
            "action": self.action,
            "files_affected": self.files_affected,
            "success": self.success,
            "error": self.error,
        }


class SandboxNotImplementedError(Exception):
    """Raised when sandbox operations fail."""
    pass


# Global sandbox state
_active_sandbox: Optional[SandboxState] = None


def is_in_sandbox() -> bool:
    """Check if currently in sandbox mode."""
    return _active_sandbox is not None and _active_sandbox.active


def get_active_sandbox() -> Optional[SandboxState]:
    """Get the active sandbox state."""
    return _active_sandbox


def get_sandbox_dir() -> Optional[str]:
    """Get the sandbox working directory."""
    if _active_sandbox:
        return _active_sandbox.sandbox_dir
    return None


def _is_git_repo(path: str) -> bool:
    """Check if path is a git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=path,
        capture_output=True,
    )
    return result.returncode == 0


def _compute_baseline_hash(root_dir: str) -> str:
    """Compute hash of directory state."""
    snapshot = snapshot_directory(root_dir)
    content = str(sorted(snapshot.items()))
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def sandbox_enter(
    root_dir: str,
    description: str = "",
    prefer_git: bool = True,
) -> SandboxEnterResult:
    """Enter sandbox mode.
    
    ACTION: sandbox.enter
    
    Creates an isolated environment where:
    - All mutations are provisional
    - Changes can be discarded without side effects
    - Exit with commit to make changes permanent
    
    Args:
        root_dir: Directory to sandbox.
        description: Description of sandbox purpose.
        prefer_git: Use git worktree if in git repo.
    
    Returns:
        SandboxEnterResult with sandbox ID.
    """
    global _active_sandbox
    
    if _active_sandbox and _active_sandbox.active:
        return SandboxEnterResult(
            sandbox_id="",
            baseline_hash="",
            sandbox_dir="",
            isolation_method="",
            success=False,
            error="Already in sandbox mode. Exit first.",
        )
    
    root_dir = os.path.abspath(root_dir)
    sandbox_id = f"sandbox_{int(datetime.now().timestamp())}"
    baseline_hash = _compute_baseline_hash(root_dir)
    
    # Determine isolation method
    isolation_method = "directory_copy"
    sandbox_dir = ""
    
    if prefer_git and _is_git_repo(root_dir):
        # Use git worktree for isolation
        try:
            worktree_name = f"sandbox-{sandbox_id}"
            worktree_path = os.path.join(tempfile.gettempdir(), worktree_name)
            
            # Create worktree from current HEAD
            result = subprocess.run(
                ["git", "worktree", "add", "--detach", worktree_path, "HEAD"],
                cwd=root_dir,
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                isolation_method = "git_worktree"
                sandbox_dir = worktree_path
        except Exception:
            pass
    
    # Fallback to directory copy
    if not sandbox_dir:
        sandbox_dir = os.path.join(tempfile.gettempdir(), sandbox_id)
        shutil.copytree(root_dir, sandbox_dir, dirs_exist_ok=True)
        isolation_method = "directory_copy"
    
    # Create sandbox state
    _active_sandbox = SandboxState(
        sandbox_id=sandbox_id,
        created_at=datetime.now(),
        baseline_hash=baseline_hash,
        root_dir=root_dir,
        sandbox_dir=sandbox_dir,
        isolation_method=isolation_method,
    )
    
    return SandboxEnterResult(
        sandbox_id=sandbox_id,
        baseline_hash=baseline_hash,
        sandbox_dir=sandbox_dir,
        isolation_method=isolation_method,
        success=True,
    )


def sandbox_exit(
    action: str = "discard",
) -> SandboxExitResult:
    """Exit sandbox mode.
    
    ACTION: sandbox.exit
    
    Args:
        action: "commit" to apply changes, "discard" to revert.
    
    Returns:
        SandboxExitResult with affected files.
    """
    global _active_sandbox
    
    if not _active_sandbox or not _active_sandbox.active:
        return SandboxExitResult(
            sandbox_id="",
            action=action,
            files_affected=[],
            success=False,
            error="Not in sandbox mode.",
        )
    
    sandbox = _active_sandbox
    files_affected = []
    
    try:
        if action == "commit":
            # Copy changes back to original
            files_affected = _commit_sandbox(sandbox)
        
        # Cleanup sandbox
        _cleanup_sandbox(sandbox)
        
        sandbox.active = False
        _active_sandbox = None
        
        return SandboxExitResult(
            sandbox_id=sandbox.sandbox_id,
            action=action,
            files_affected=files_affected,
            success=True,
        )
        
    except Exception as e:
        return SandboxExitResult(
            sandbox_id=sandbox.sandbox_id,
            action=action,
            files_affected=[],
            success=False,
            error=str(e),
        )


def _commit_sandbox(sandbox: SandboxState) -> List[str]:
    """Copy sandbox changes back to original directory."""
    files_affected = []
    
    # Get current sandbox state
    current_snapshot = snapshot_directory(sandbox.sandbox_dir)
    original_snapshot = snapshot_directory(sandbox.root_dir)
    
    # Find changed/new files
    for rel_path, new_hash in current_snapshot.items():
        original_hash = original_snapshot.get(rel_path)
        if original_hash != new_hash:
            # File changed or is new
            src = os.path.join(sandbox.sandbox_dir, rel_path)
            dst = os.path.join(sandbox.root_dir, rel_path)
            
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            files_affected.append(rel_path)
    
    # Find deleted files
    for rel_path in original_snapshot:
        if rel_path not in current_snapshot:
            full_path = os.path.join(sandbox.root_dir, rel_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                files_affected.append(f"(deleted) {rel_path}")
    
    return files_affected


def _cleanup_sandbox(sandbox: SandboxState) -> None:
    """Clean up sandbox resources."""
    if sandbox.isolation_method == "git_worktree":
        # Remove git worktree
        try:
            subprocess.run(
                ["git", "worktree", "remove", "--force", sandbox.sandbox_dir],
                cwd=sandbox.root_dir,
                capture_output=True,
            )
        except Exception:
            pass
    
    # Remove directory if it exists
    if os.path.exists(sandbox.sandbox_dir):
        try:
            shutil.rmtree(sandbox.sandbox_dir)
        except Exception:
            pass


def record_sandbox_mutation(action_id: str, details: Dict[str, Any]) -> None:
    """Record a mutation in the sandbox."""
    if _active_sandbox and _active_sandbox.active:
        _active_sandbox.mutations.append({
            "action_id": action_id,
            "timestamp": datetime.now().isoformat(),
            "details": details,
        })


@contextmanager
def sandbox_context(
    root_dir: str,
    description: str = "",
    commit_on_success: bool = False,
) -> Generator[str, None, None]:
    """Context manager for sandbox operations.
    
    Usage:
        with sandbox_context("/path/to/project") as sandbox_dir:
            # Work in sandbox_dir
            # Changes are discarded on exit unless commit_on_success=True
    
    Args:
        root_dir: Directory to sandbox.
        description: Description of sandbox purpose.
        commit_on_success: If True, commit changes on normal exit.
    
    Yields:
        Path to sandbox working directory.
    """
    result = sandbox_enter(root_dir, description)
    if not result.success:
        raise SandboxNotImplementedError(result.error or "Failed to enter sandbox")
    
    try:
        yield result.sandbox_dir
        # Normal exit
        action = "commit" if commit_on_success else "discard"
        sandbox_exit(action)
    except Exception:
        # Error - always discard
        sandbox_exit("discard")
        raise
