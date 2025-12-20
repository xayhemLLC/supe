"""ACTION_APPLY_PATCH - Apply unified diff patches.

Apply unified diff patch or targeted edits.
Validator: diff evidence + hashes updated.
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..primitives.file_ops import snapshot_file, FileSnapshot


@dataclass
class ApplyPatchResult:
    """Result of applying a patch."""
    
    success: bool
    files_modified: List[str] = field(default_factory=list)
    before_hashes: Dict[str, str] = field(default_factory=dict)
    after_hashes: Dict[str, str] = field(default_factory=dict)
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "files_modified": self.files_modified,
            "before_hashes": self.before_hashes,
            "after_hashes": self.after_hashes,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
        }


def apply_patch(
    patch: str,
    cwd: Optional[str] = None,
    dry_run: bool = False,
    strip_level: int = 1,
) -> ApplyPatchResult:
    """Apply a unified diff patch.
    
    ACTION_APPLY_PATCH implementation.
    
    Args:
        patch: The unified diff patch content.
        cwd: Working directory to apply patch in.
        dry_run: If True, don't actually apply, just check.
        strip_level: Number of leading path components to strip (-p option).
    
    Returns:
        ApplyPatchResult with success status and file changes.
    """
    if cwd is None:
        cwd = os.getcwd()
    
    # Parse patch to find affected files
    affected_files = _parse_patch_files(patch)
    
    # Snapshot before
    before_hashes = {}
    for rel_path in affected_files:
        full_path = os.path.join(cwd, rel_path)
        snap = snapshot_file(full_path, preview_bytes=0)
        if snap.exists and snap.sha256:
            before_hashes[rel_path] = snap.sha256
    
    # Write patch to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".patch", delete=False) as f:
        f.write(patch)
        patch_file = f.name
    
    try:
        # Build patch command
        cmd = ["patch", f"-p{strip_level}"]
        if dry_run:
            cmd.append("--dry-run")
        cmd.extend(["-i", patch_file])
        
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        success = result.returncode == 0
        
        # Snapshot after
        after_hashes = {}
        if success and not dry_run:
            for rel_path in affected_files:
                full_path = os.path.join(cwd, rel_path)
                snap = snapshot_file(full_path, preview_bytes=0)
                if snap.exists and snap.sha256:
                    after_hashes[rel_path] = snap.sha256
        
        # Determine which files actually changed
        files_modified = [
            f for f in affected_files
            if before_hashes.get(f) != after_hashes.get(f)
        ]
        
        return ApplyPatchResult(
            success=success,
            files_modified=files_modified,
            before_hashes=before_hashes,
            after_hashes=after_hashes,
            stdout=result.stdout,
            stderr=result.stderr,
            error=None if success else result.stderr,
        )
    
    except subprocess.TimeoutExpired:
        return ApplyPatchResult(
            success=False,
            error="Patch command timed out",
        )
    except FileNotFoundError:
        return ApplyPatchResult(
            success=False,
            error="patch command not found",
        )
    finally:
        os.unlink(patch_file)


def _parse_patch_files(patch: str) -> List[str]:
    """Parse a unified diff to extract affected file paths."""
    files = []
    for line in patch.split("\n"):
        # Look for +++ lines which indicate target files
        if line.startswith("+++ "):
            # Remove +++ prefix and strip leading path component
            path = line[4:].strip()
            # Handle common prefixes like b/ or ./
            if path.startswith("b/"):
                path = path[2:]
            elif path.startswith("./"):
                path = path[2:]
            # Remove timestamp if present
            if "\t" in path:
                path = path.split("\t")[0]
            if path and path != "/dev/null":
                files.append(path)
    return files


def apply_targeted_edit(
    file_path: str,
    old_content: str,
    new_content: str,
) -> ApplyPatchResult:
    """Apply a targeted string replacement edit.
    
    A simpler alternative to full patch application for single replacements.
    
    Args:
        file_path: Path to file to edit.
        old_content: Content to find and replace.
        new_content: Replacement content.
    
    Returns:
        ApplyPatchResult with success status.
    """
    # Snapshot before
    before_snap = snapshot_file(file_path, preview_bytes=0)
    
    if not before_snap.exists:
        return ApplyPatchResult(
            success=False,
            error=f"File not found: {file_path}",
        )
    
    try:
        with open(file_path, "r") as f:
            content = f.read()
        
        if old_content not in content:
            return ApplyPatchResult(
                success=False,
                error="Target content not found in file",
                before_hashes={file_path: before_snap.sha256 or ""},
            )
        
        # Apply replacement
        new_file_content = content.replace(old_content, new_content, 1)
        
        with open(file_path, "w") as f:
            f.write(new_file_content)
        
        # Snapshot after
        after_snap = snapshot_file(file_path, preview_bytes=0)
        
        return ApplyPatchResult(
            success=True,
            files_modified=[file_path],
            before_hashes={file_path: before_snap.sha256 or ""},
            after_hashes={file_path: after_snap.sha256 or ""},
        )
    
    except IOError as e:
        return ApplyPatchResult(
            success=False,
            error=str(e),
        )
