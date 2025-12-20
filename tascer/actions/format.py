"""ACTION_FORMAT_FIX - Run formatters and confirm stable result.

Run formatters (prettier/ruff/gofmt), confirm stable result.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..primitives.terminal import run_and_observe
from ..primitives.file_ops import snapshot_directory, diff_directories


@dataclass
class FormatFixResult:
    """Result of format fix action."""
    
    success: bool
    stable: bool  # True if running again produces no changes
    files_modified: List[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "stable": self.stable,
            "files_modified": self.files_modified,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
        }


def format_fix(
    format_cmd: str = "ruff format .",
    cwd: Optional[str] = None,
    check_stability: bool = True,
    timeout_sec: float = 120,
) -> FormatFixResult:
    """Run formatter and optionally verify stability.
    
    ACTION_FORMAT_FIX implementation.
    
    Args:
        format_cmd: Formatting command to run.
        cwd: Working directory.
        check_stability: If True, run formatter twice to ensure stability.
        timeout_sec: Command timeout.
    
    Returns:
        FormatFixResult with success and stability status.
    """
    if cwd is None:
        cwd = os.getcwd()
    
    # Snapshot before
    before_snapshot = snapshot_directory(cwd)
    
    # Run formatter
    result = run_and_observe(
        format_cmd,
        cwd=cwd,
        timeout_sec=timeout_sec,
        shell=True,
    )
    
    if result.timed_out:
        return FormatFixResult(
            success=False,
            stable=False,
            error="Format command timed out",
            stdout=result.stdout,
            stderr=result.stderr,
        )
    
    # Snapshot after first run
    after_first = snapshot_directory(cwd)
    
    # Calculate changes from first run
    diff = diff_directories(cwd, before_snapshot, after_first)
    
    # Check stability by running again
    stable = True
    if check_stability:
        result2 = run_and_observe(
            format_cmd,
            cwd=cwd,
            timeout_sec=timeout_sec,
            shell=True,
        )
        
        after_second = snapshot_directory(cwd)
        diff2 = diff_directories(cwd, after_first, after_second)
        
        stable = not diff2.has_changes
    
    return FormatFixResult(
        success=result.exit_code == 0,
        stable=stable,
        files_modified=diff.modified + diff.added,
        stdout=result.stdout,
        stderr=result.stderr,
    )
