"""Checkpoint System - Time travel for safe exploration.

Checkpoints capture full state allowing:
- Safe exploration of mutations
- Rollback when things go wrong
- Counterfactual reasoning

Mutation guards ensure destructive actions require active checkpoints.
"""

import hashlib
import json
import os
import shutil
import signal
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .primitives.file_ops import snapshot_directory
from .primitives.git import capture_git_state


@dataclass
class ProcessSnapshot:
    """Snapshot of a running process."""
    
    pid: int
    command: str
    cwd: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "command": self.command,
            "cwd": self.cwd,
            "env": self.env,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessSnapshot":
        return cls(
            pid=data["pid"],
            command=data["command"],
            cwd=data.get("cwd"),
            env=data.get("env", {}),
        )


@dataclass
class Checkpoint:
    """Full state checkpoint for rollback.
    
    Captures:
    - Git state (branch, commit, dirty status)
    - File tree with hashes
    - Running process list
    - Optional frontend/browser state hash
    """
    
    # Identity
    checkpoint_id: str
    run_id: str
    
    # Timing
    created_at: datetime
    
    # Git state
    git_branch: str
    git_commit: str
    git_dirty: bool
    git_stash_ref: Optional[str] = None  # If we stashed changes
    
    # File state
    root_dir: str = ""
    file_tree_hash: str = ""  # Hash of entire file tree snapshot
    file_snapshot: Dict[str, str] = field(default_factory=dict)  # path -> hash
    
    # Backup of modified files (for rollback)
    backup_dir: Optional[str] = None
    
    # Process state
    processes: List[ProcessSnapshot] = field(default_factory=list)
    tracked_pids: Set[int] = field(default_factory=set)
    
    # Frontend state (optional)
    frontend_state_hash: Optional[str] = None
    
    # Browser state (optional)
    browser_url: Optional[str] = None
    browser_state_hash: Optional[str] = None
    
    # Metadata
    description: str = ""
    
    def compute_tree_hash(self) -> str:
        """Compute hash of the file tree snapshot."""
        serialized = json.dumps(self.file_snapshot, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "run_id": self.run_id,
            "created_at": self.created_at.isoformat(),
            "git_branch": self.git_branch,
            "git_commit": self.git_commit,
            "git_dirty": self.git_dirty,
            "git_stash_ref": self.git_stash_ref,
            "root_dir": self.root_dir,
            "file_tree_hash": self.file_tree_hash,
            "file_snapshot": self.file_snapshot,
            "backup_dir": self.backup_dir,
            "processes": [p.to_dict() for p in self.processes],
            "tracked_pids": list(self.tracked_pids),
            "frontend_state_hash": self.frontend_state_hash,
            "browser_url": self.browser_url,
            "browser_state_hash": self.browser_state_hash,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        return cls(
            checkpoint_id=data["checkpoint_id"],
            run_id=data["run_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            git_branch=data["git_branch"],
            git_commit=data["git_commit"],
            git_dirty=data["git_dirty"],
            git_stash_ref=data.get("git_stash_ref"),
            root_dir=data.get("root_dir", ""),
            file_tree_hash=data.get("file_tree_hash", ""),
            file_snapshot=data.get("file_snapshot", {}),
            backup_dir=data.get("backup_dir"),
            processes=[ProcessSnapshot.from_dict(p) for p in data.get("processes", [])],
            tracked_pids=set(data.get("tracked_pids", [])),
            frontend_state_hash=data.get("frontend_state_hash"),
            browser_url=data.get("browser_url"),
            browser_state_hash=data.get("browser_state_hash"),
            description=data.get("description", ""),
        )


class CheckpointManager:
    """Manages checkpoints for a run.
    
    Provides:
    - Checkpoint creation with full state capture
    - Rollback to previous checkpoint
    - Mutation guards that require active checkpoint
    """
    
    def __init__(
        self,
        run_id: str,
        root_dir: str,
        output_dir: str = "./tascer_output",
    ):
        """Initialize checkpoint manager.
        
        Args:
            run_id: Run identifier.
            root_dir: Root directory to track.
            output_dir: Directory for checkpoint storage.
        """
        self.run_id = run_id
        self.root_dir = os.path.abspath(root_dir)
        self.output_dir = output_dir
        
        self._checkpoints: List[Checkpoint] = []
        self._checkpoint_count = 0
        self._active_checkpoint: Optional[Checkpoint] = None
        self._tracked_pids: Set[int] = set()
    
    def has_active_checkpoint(self) -> bool:
        """Check if there's an active checkpoint."""
        return self._active_checkpoint is not None
    
    def get_active(self) -> Optional[Checkpoint]:
        """Get the active checkpoint."""
        return self._active_checkpoint
    
    def require_checkpoint(self, action_id: str) -> None:
        """Raise if no active checkpoint (mutation guard).
        
        Args:
            action_id: Action requiring checkpoint.
        
        Raises:
            RuntimeError: If no active checkpoint.
        """
        if not self.has_active_checkpoint():
            raise RuntimeError(
                f"Action '{action_id}' requires an active checkpoint. "
                "Create one with checkpoint.create before mutating state."
            )
    
    def create(
        self,
        description: str = "",
        capture_processes: bool = True,
        backup_files: bool = True,
    ) -> Checkpoint:
        """Create a new checkpoint capturing current state.
        
        Args:
            description: Human-readable description.
            capture_processes: Whether to snapshot running processes.
            backup_files: Whether to backup files for rollback.
        
        Returns:
            Created Checkpoint.
        """
        self._checkpoint_count += 1
        checkpoint_id = f"{self.run_id}_cp{self._checkpoint_count}"
        
        # Capture git state
        try:
            git_state = capture_git_state(self.root_dir)
            git_branch = git_state.branch
            git_commit = git_state.commit
            git_dirty = git_state.dirty
        except (ValueError, FileNotFoundError):
            git_branch = ""
            git_commit = ""
            git_dirty = False
        
        # Snapshot file tree
        file_snapshot = snapshot_directory(self.root_dir)
        
        # Create backup directory if needed
        backup_dir = None
        if backup_files:
            backup_dir = os.path.join(
                self.output_dir,
                "checkpoints",
                checkpoint_id,
            )
            os.makedirs(backup_dir, exist_ok=True)
            self._backup_files(backup_dir, file_snapshot)
        
        # Capture process list
        processes = []
        if capture_processes:
            processes = self._capture_processes()
        
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            run_id=self.run_id,
            created_at=datetime.now(),
            git_branch=git_branch,
            git_commit=git_commit,
            git_dirty=git_dirty,
            root_dir=self.root_dir,
            file_snapshot=file_snapshot,
            backup_dir=backup_dir,
            processes=processes,
            tracked_pids=self._tracked_pids.copy(),
            description=description,
        )
        
        checkpoint.file_tree_hash = checkpoint.compute_tree_hash()
        
        self._checkpoints.append(checkpoint)
        self._active_checkpoint = checkpoint
        
        # Save checkpoint to disk
        self._save_checkpoint(checkpoint)
        
        return checkpoint
    
    def _backup_files(
        self,
        backup_dir: str,
        file_snapshot: Dict[str, str],
    ) -> None:
        """Backup files for potential rollback."""
        for rel_path in file_snapshot:
            src_path = os.path.join(self.root_dir, rel_path)
            dst_path = os.path.join(backup_dir, rel_path)
            
            if os.path.exists(src_path):
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
    
    def _capture_processes(self) -> List[ProcessSnapshot]:
        """Capture list of tracked processes."""
        processes = []
        for pid in self._tracked_pids:
            try:
                # Get process info (platform-dependent)
                result = subprocess.run(
                    ["ps", "-p", str(pid), "-o", "command="],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    processes.append(ProcessSnapshot(
                        pid=pid,
                        command=result.stdout.strip(),
                    ))
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        return processes
    
    def _save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Save checkpoint to disk."""
        checkpoint_dir = os.path.join(self.output_dir, "checkpoints")
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        path = os.path.join(checkpoint_dir, f"{checkpoint.checkpoint_id}.json")
        with open(path, "w") as f:
            json.dump(checkpoint.to_dict(), f, indent=2)
    
    def rollback(
        self,
        checkpoint_id: Optional[str] = None,
        restore_files: bool = True,
        stop_processes: bool = True,
    ) -> Dict[str, Any]:
        """Rollback to a checkpoint.
        
        Args:
            checkpoint_id: Checkpoint to rollback to. Defaults to active.
            restore_files: Whether to restore file contents.
            stop_processes: Whether to stop processes started after checkpoint.
        
        Returns:
            Dict with rollback details.
        """
        # Find checkpoint
        if checkpoint_id:
            checkpoint = next(
                (cp for cp in self._checkpoints if cp.checkpoint_id == checkpoint_id),
                None,
            )
            if not checkpoint:
                raise ValueError(f"Checkpoint not found: {checkpoint_id}")
        else:
            checkpoint = self._active_checkpoint
            if not checkpoint:
                raise RuntimeError("No active checkpoint to rollback to")
        
        result = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "files_restored": [],
            "files_deleted": [],
            "processes_stopped": [],
        }
        
        # Restore files from backup
        if restore_files and checkpoint.backup_dir:
            result.update(self._restore_files(checkpoint))
        
        # Stop processes started after checkpoint
        if stop_processes:
            result["processes_stopped"] = self._stop_new_processes(checkpoint)
        
        # Reset git if it was clean
        if not checkpoint.git_dirty and checkpoint.git_commit:
            try:
                subprocess.run(
                    ["git", "checkout", "."],
                    cwd=self.root_dir,
                    capture_output=True,
                    timeout=30,
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        return result
    
    def _restore_files(self, checkpoint: Checkpoint) -> Dict[str, List[str]]:
        """Restore files from checkpoint backup."""
        result: Dict[str, List[str]] = {
            "files_restored": [],
            "files_deleted": [],
        }
        
        if not checkpoint.backup_dir:
            return result
        
        # Get current state
        current_snapshot = snapshot_directory(self.root_dir)
        
        # Restore files that existed at checkpoint
        for rel_path in checkpoint.file_snapshot:
            backup_path = os.path.join(checkpoint.backup_dir, rel_path)
            target_path = os.path.join(self.root_dir, rel_path)
            
            if os.path.exists(backup_path):
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(backup_path, target_path)
                result["files_restored"].append(rel_path)
        
        # Delete files created after checkpoint
        for rel_path in current_snapshot:
            if rel_path not in checkpoint.file_snapshot:
                target_path = os.path.join(self.root_dir, rel_path)
                if os.path.exists(target_path):
                    os.remove(target_path)
                    result["files_deleted"].append(rel_path)
        
        return result
    
    def _stop_new_processes(self, checkpoint: Checkpoint) -> List[int]:
        """Stop processes started after checkpoint."""
        stopped = []
        
        # Find PIDs not in checkpoint
        new_pids = self._tracked_pids - checkpoint.tracked_pids
        
        for pid in new_pids:
            try:
                os.kill(pid, signal.SIGTERM)
                stopped.append(pid)
            except (ProcessLookupError, PermissionError):
                continue
        
        return stopped
    
    def track_process(self, pid: int) -> None:
        """Add a process to tracking list."""
        self._tracked_pids.add(pid)
    
    def untrack_process(self, pid: int) -> None:
        """Remove a process from tracking list."""
        self._tracked_pids.discard(pid)
    
    def list_checkpoints(self) -> List[Checkpoint]:
        """Get all checkpoints."""
        return list(self._checkpoints)
    
    def clear(self) -> None:
        """Clear all checkpoints (for cleanup)."""
        self._checkpoints.clear()
        self._active_checkpoint = None
        self._checkpoint_count = 0


# Mutation guard decorator
def requires_checkpoint(func):
    """Decorator that requires an active checkpoint for mutations."""
    def wrapper(*args, **kwargs):
        # Look for checkpoint_manager in args or kwargs
        manager = kwargs.get("checkpoint_manager")
        if manager and not manager.has_active_checkpoint():
            raise RuntimeError(
                f"Function '{func.__name__}' requires an active checkpoint. "
                "Create one before mutating state."
            )
        return func(*args, **kwargs)
    return wrapper
