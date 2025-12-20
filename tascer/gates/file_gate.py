"""TASC_GATE_FILE_EXISTS_AND_HASH - File existence and integrity validation.

Assert:
- File exists
- Optional hash matches expected
- Optional size bounds
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from ..contracts import GateResult
from ..primitives.file_ops import snapshot_file


@dataclass
class FileExistsGate:
    """Gate that validates file existence and optionally hash/size."""
    
    path: str
    expected_hash: Optional[str] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    
    def check(self) -> GateResult:
        """Check if file exists and matches expected criteria.
        
        Returns:
            GateResult with pass/fail status.
        """
        snapshot = snapshot_file(self.path, preview_bytes=0, compute_hash=self.expected_hash is not None)
        
        issues = []
        
        # Check existence
        if not snapshot.exists:
            return GateResult(
                gate_name="FILE_EXISTS_AND_HASH",
                passed=False,
                message=f"File does not exist: {self.path}",
                evidence={"path": self.path, "exists": False},
            )
        
        # Check hash if expected
        if self.expected_hash is not None:
            if snapshot.sha256 != self.expected_hash:
                issues.append(
                    f"Hash mismatch: expected {self.expected_hash[:16]}..., "
                    f"got {snapshot.sha256[:16] if snapshot.sha256 else 'None'}..."
                )
        
        # Check size bounds
        if snapshot.size is not None:
            if self.min_size is not None and snapshot.size < self.min_size:
                issues.append(f"Size {snapshot.size} below minimum {self.min_size}")
            if self.max_size is not None and snapshot.size > self.max_size:
                issues.append(f"Size {snapshot.size} above maximum {self.max_size}")
        
        passed = len(issues) == 0
        
        if passed:
            message = f"File exists and matches criteria: {os.path.basename(self.path)}"
        else:
            message = "; ".join(issues)
        
        return GateResult(
            gate_name="FILE_EXISTS_AND_HASH",
            passed=passed,
            message=message,
            evidence={
                "path": self.path,
                "exists": snapshot.exists,
                "sha256": snapshot.sha256,
                "size": snapshot.size,
                "expected_hash": self.expected_hash,
                "min_size": self.min_size,
                "max_size": self.max_size,
            },
        )


@dataclass
class DirectoryContainsGate:
    """Gate that validates directory contains expected files."""
    
    directory: str
    expected_files: list = field(default_factory=list)
    forbidden_files: list = field(default_factory=list)
    
    def check(self) -> GateResult:
        """Check if directory contains expected files and no forbidden ones.
        
        Returns:
            GateResult with pass/fail status.
        """
        if not os.path.isdir(self.directory):
            return GateResult(
                gate_name="DIRECTORY_CONTAINS",
                passed=False,
                message=f"Directory does not exist: {self.directory}",
                evidence={"directory": self.directory, "exists": False},
            )
        
        # Get actual files
        actual_files = set()
        for root, dirs, files in os.walk(self.directory):
            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), self.directory)
                actual_files.add(rel_path)
        
        issues = []
        
        # Check expected files
        missing = []
        for expected in self.expected_files:
            if expected not in actual_files:
                missing.append(expected)
        if missing:
            issues.append(f"Missing files: {', '.join(missing[:5])}")
        
        # Check forbidden files
        found_forbidden = []
        for forbidden in self.forbidden_files:
            if forbidden in actual_files:
                found_forbidden.append(forbidden)
        if found_forbidden:
            issues.append(f"Forbidden files present: {', '.join(found_forbidden[:5])}")
        
        passed = len(issues) == 0
        
        if passed:
            message = f"Directory contains all expected files"
        else:
            message = "; ".join(issues)
        
        return GateResult(
            gate_name="DIRECTORY_CONTAINS",
            passed=passed,
            message=message,
            evidence={
                "directory": self.directory,
                "missing": missing,
                "forbidden_found": found_forbidden,
            },
        )
