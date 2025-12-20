"""TASC_CORE_FILE_READ_SNAPSHOT and TASC_CORE_DIRECTORY_DIFF_SNAPSHOT.

File snapshot hypothesis: "We can snapshot a file's existence + hash + metadata."
Evidence: exists, sha256, size, mtime, preview (bounded).

Directory diff hypothesis: "We can measure file tree changes between S0 and S1."
Evidence: file adds/deletes/renames, hash diffs.
"""

import hashlib
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FileSnapshot:
    """Snapshot of a file's state."""
    
    path: str
    exists: bool
    sha256: Optional[str] = None
    size: Optional[int] = None
    mtime: Optional[float] = None
    preview: Optional[str] = None  # First N bytes
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "exists": self.exists,
            "sha256": self.sha256,
            "size": self.size,
            "mtime": self.mtime,
            "preview": self.preview,
        }


@dataclass
class FileChange:
    """A single file change in a directory diff."""
    
    path: str
    change_type: str  # added | deleted | modified | renamed
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    old_path: Optional[str] = None  # For renames
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "change_type": self.change_type,
            "old_hash": self.old_hash,
            "new_hash": self.new_hash,
            "old_path": self.old_path,
        }


@dataclass
class DirectoryDiff:
    """Diff between two directory states."""
    
    root: str
    added: List[str] = field(default_factory=list)
    deleted: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    changes: List[FileChange] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "root": self.root,
            "added": self.added,
            "deleted": self.deleted,
            "modified": self.modified,
            "changes": [c.to_dict() for c in self.changes],
        }
    
    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.deleted or self.modified)


def _compute_sha256(path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def snapshot_file(
    path: str,
    preview_bytes: int = 1024,
    compute_hash: bool = True,
) -> FileSnapshot:
    """Take a snapshot of a file's state.
    
    TASC_CORE_FILE_READ_SNAPSHOT implementation.
    
    Args:
        path: Path to the file.
        preview_bytes: Number of bytes to include in preview.
        compute_hash: Whether to compute SHA256 hash.
    
    Returns:
        FileSnapshot with existence, hash, size, mtime, preview.
    """
    abs_path = os.path.abspath(path)
    
    if not os.path.exists(abs_path):
        return FileSnapshot(path=abs_path, exists=False)
    
    if not os.path.isfile(abs_path):
        # It's a directory or other, not a file
        return FileSnapshot(path=abs_path, exists=True)
    
    stat = os.stat(abs_path)
    
    # Compute hash if requested
    file_hash = None
    if compute_hash:
        try:
            file_hash = _compute_sha256(abs_path)
        except (IOError, OSError):
            pass
    
    # Get preview
    preview = None
    if preview_bytes > 0:
        try:
            with open(abs_path, "rb") as f:
                preview_data = f.read(preview_bytes)
                try:
                    preview = preview_data.decode("utf-8", errors="replace")
                except Exception:
                    preview = preview_data.hex()
        except (IOError, OSError):
            pass
    
    return FileSnapshot(
        path=abs_path,
        exists=True,
        sha256=file_hash,
        size=stat.st_size,
        mtime=stat.st_mtime,
        preview=preview,
    )


def snapshot_directory(
    root: str,
    exclude_patterns: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Take a snapshot of all files in a directory.
    
    Args:
        root: Directory root.
        exclude_patterns: Glob patterns to exclude (simple string matching).
    
    Returns:
        Dict mapping relative paths to SHA256 hashes.
    """
    if exclude_patterns is None:
        exclude_patterns = [".git", "__pycache__", "*.pyc", ".venv", "node_modules"]
    
    snapshots: Dict[str, str] = {}
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Filter out excluded directories
        dirnames[:] = [
            d for d in dirnames
            if not any(pattern in d for pattern in exclude_patterns)
        ]
        
        for filename in filenames:
            # Skip excluded files
            if any(pattern.replace("*", "") in filename for pattern in exclude_patterns):
                continue
            
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, root)
            
            try:
                file_hash = _compute_sha256(full_path)
                snapshots[rel_path] = file_hash
            except (IOError, OSError):
                continue
    
    return snapshots


def diff_directories(
    root: str,
    before: Dict[str, str],
    after: Optional[Dict[str, str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> DirectoryDiff:
    """Compute diff between two directory states.
    
    TASC_CORE_DIRECTORY_DIFF_SNAPSHOT implementation.
    
    Args:
        root: Directory root path.
        before: Previous snapshot (path -> hash mapping).
        after: Current snapshot. If None, computed from disk.
        exclude_patterns: Patterns to exclude from snapshot.
    
    Returns:
        DirectoryDiff with added, deleted, modified files.
    """
    if after is None:
        after = snapshot_directory(root, exclude_patterns)
    
    before_paths = set(before.keys())
    after_paths = set(after.keys())
    
    added = list(after_paths - before_paths)
    deleted = list(before_paths - after_paths)
    
    # Check for modifications
    modified = []
    for path in before_paths & after_paths:
        if before[path] != after[path]:
            modified.append(path)
    
    # Build detailed change list
    changes = []
    for path in added:
        changes.append(FileChange(
            path=path,
            change_type="added",
            new_hash=after[path],
        ))
    for path in deleted:
        changes.append(FileChange(
            path=path,
            change_type="deleted",
            old_hash=before[path],
        ))
    for path in modified:
        changes.append(FileChange(
            path=path,
            change_type="modified",
            old_hash=before[path],
            new_hash=after[path],
        ))
    
    return DirectoryDiff(
        root=root,
        added=sorted(added),
        deleted=sorted(deleted),
        modified=sorted(modified),
        changes=changes,
    )
