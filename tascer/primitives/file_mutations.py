"""File mutation primitives.

ACTIONS (mutations requiring checkpoint):
- file.write: Write content to file
- file.patch: Apply unified diff
- file.delete: Delete file

All mutations require an active checkpoint for safety.
"""

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .file_ops import _compute_sha256


@dataclass
class WriteResult:
    """Result of file write operation."""
    
    path: str
    success: bool
    sha256_before: Optional[str]
    sha256_after: Optional[str]
    bytes_written: int
    created: bool  # True if file was created (didn't exist)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "success": self.success,
            "sha256_before": self.sha256_before,
            "sha256_after": self.sha256_after,
            "bytes_written": self.bytes_written,
            "created": self.created,
            "error": self.error,
        }


@dataclass
class PatchHunk:
    """A single hunk from a unified diff."""
    
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[str]
    applied: bool = False


@dataclass
class PatchResult:
    """Result of patch operation."""
    
    path: str
    success: bool
    hunks_total: int
    hunks_applied: int
    sha256_before: Optional[str]
    sha256_after: Optional[str]
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "success": self.success,
            "hunks_total": self.hunks_total,
            "hunks_applied": self.hunks_applied,
            "sha256_before": self.sha256_before,
            "sha256_after": self.sha256_after,
            "error": self.error,
        }


@dataclass
class DeleteResult:
    """Result of file deletion."""
    
    path: str
    success: bool
    sha256_deleted: Optional[str]
    size_deleted: int
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "success": self.success,
            "sha256_deleted": self.sha256_deleted,
            "size_deleted": self.size_deleted,
            "error": self.error,
        }


def file_write(
    path: str,
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True,
    checkpoint_manager=None,
) -> WriteResult:
    """Write content to file.
    
    ACTION: file.write (MUTATION)
    
    Requires active checkpoint for safety.
    
    Args:
        path: File path to write to.
        content: Content to write.
        encoding: Text encoding.
        create_dirs: Create parent directories if needed.
        checkpoint_manager: Optional checkpoint manager for safety check.
    
    Returns:
        WriteResult with before/after hashes.
    """
    abs_path = os.path.abspath(path)
    
    # Check checkpoint if manager provided
    if checkpoint_manager:
        checkpoint_manager.require_checkpoint("file.write")
    
    # Get before state
    sha256_before = None
    created = not os.path.exists(abs_path)
    if not created:
        try:
            sha256_before = _compute_sha256(abs_path)
        except (IOError, OSError):
            pass
    
    try:
        # Create parent directories if needed
        if create_dirs:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        # Write content
        with open(abs_path, "w", encoding=encoding) as f:
            f.write(content)
        
        # Get after state
        sha256_after = _compute_sha256(abs_path)
        
        return WriteResult(
            path=abs_path,
            success=True,
            sha256_before=sha256_before,
            sha256_after=sha256_after,
            bytes_written=len(content.encode(encoding)),
            created=created,
        )
        
    except Exception as e:
        return WriteResult(
            path=abs_path,
            success=False,
            sha256_before=sha256_before,
            sha256_after=None,
            bytes_written=0,
            created=False,
            error=str(e),
        )


def file_patch(
    path: str,
    patch: str,
    checkpoint_manager=None,
) -> PatchResult:
    """Apply a unified diff patch to a file.
    
    ACTION: file.patch (MUTATION)
    
    Requires active checkpoint for safety.
    
    Args:
        path: File path to patch.
        patch: Unified diff patch content.
        checkpoint_manager: Optional checkpoint manager for safety check.
    
    Returns:
        PatchResult with hunks applied.
    """
    abs_path = os.path.abspath(path)
    
    # Check checkpoint if manager provided
    if checkpoint_manager:
        checkpoint_manager.require_checkpoint("file.patch")
    
    # Get before state
    sha256_before = None
    if os.path.exists(abs_path):
        try:
            sha256_before = _compute_sha256(abs_path)
        except (IOError, OSError):
            pass
    
    try:
        # Read current content
        with open(abs_path, "r") as f:
            lines = f.readlines()
        
        # Parse and apply patch
        hunks = _parse_hunks(patch)
        hunks_applied = 0
        
        for hunk in hunks:
            if _apply_hunk(lines, hunk):
                hunks_applied += 1
        
        # Write result
        with open(abs_path, "w") as f:
            f.writelines(lines)
        
        sha256_after = _compute_sha256(abs_path)
        
        return PatchResult(
            path=abs_path,
            success=hunks_applied == len(hunks),
            hunks_total=len(hunks),
            hunks_applied=hunks_applied,
            sha256_before=sha256_before,
            sha256_after=sha256_after,
        )
        
    except Exception as e:
        return PatchResult(
            path=abs_path,
            success=False,
            hunks_total=0,
            hunks_applied=0,
            sha256_before=sha256_before,
            sha256_after=None,
            error=str(e),
        )


def _parse_hunks(patch: str) -> List[PatchHunk]:
    """Parse unified diff into hunks."""
    hunks = []
    hunk_header_re = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
    
    lines = patch.split('\n')
    current_hunk = None
    
    for line in lines:
        match = hunk_header_re.match(line)
        if match:
            if current_hunk:
                hunks.append(current_hunk)
            
            current_hunk = PatchHunk(
                old_start=int(match.group(1)),
                old_count=int(match.group(2) or 1),
                new_start=int(match.group(3)),
                new_count=int(match.group(4) or 1),
                lines=[],
            )
        elif current_hunk is not None:
            if line.startswith('+') or line.startswith('-') or line.startswith(' '):
                current_hunk.lines.append(line)
    
    if current_hunk:
        hunks.append(current_hunk)
    
    return hunks


def _apply_hunk(lines: List[str], hunk: PatchHunk) -> bool:
    """Apply a single hunk to lines. Returns success."""
    # Simplified patch application
    # A full implementation would handle context matching and fuzzy matching
    try:
        # Calculate insertion point
        insert_at = hunk.new_start - 1
        
        # Apply changes
        for patch_line in hunk.lines:
            if patch_line.startswith('-'):
                # Remove line
                if insert_at < len(lines):
                    lines.pop(insert_at)
            elif patch_line.startswith('+'):
                # Add line
                lines.insert(insert_at, patch_line[1:] + '\n')
                insert_at += 1
            elif patch_line.startswith(' '):
                # Context line - skip
                insert_at += 1
        
        hunk.applied = True
        return True
        
    except Exception:
        return False


def file_delete(
    path: str,
    checkpoint_manager=None,
    must_exist: bool = True,
) -> DeleteResult:
    """Delete a file.
    
    ACTION: file.delete (MUTATION)
    
    Requires active checkpoint for safety.
    
    Args:
        path: File path to delete.
        checkpoint_manager: Optional checkpoint manager for safety check.
        must_exist: If True, error if file doesn't exist.
    
    Returns:
        DeleteResult with deleted file info.
    """
    abs_path = os.path.abspath(path)
    
    # Check checkpoint if manager provided
    if checkpoint_manager:
        checkpoint_manager.require_checkpoint("file.delete")
    
    # Check existence
    if not os.path.exists(abs_path):
        if must_exist:
            return DeleteResult(
                path=abs_path,
                success=False,
                sha256_deleted=None,
                size_deleted=0,
                error="File does not exist",
            )
        else:
            return DeleteResult(
                path=abs_path,
                success=True,
                sha256_deleted=None,
                size_deleted=0,
            )
    
    try:
        # Get file info before delete
        stat = os.stat(abs_path)
        sha256_deleted = _compute_sha256(abs_path)
        size_deleted = stat.st_size
        
        # Delete
        os.remove(abs_path)
        
        return DeleteResult(
            path=abs_path,
            success=True,
            sha256_deleted=sha256_deleted,
            size_deleted=size_deleted,
        )
        
    except Exception as e:
        return DeleteResult(
            path=abs_path,
            success=False,
            sha256_deleted=None,
            size_deleted=0,
            error=str(e),
        )
