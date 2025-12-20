"""ACTION_TEST_RUN_AND_TRIAGE - Run tests and extract failure information.

Run tests, extract:
- Failing test names
- Stack traces
- Probable file roots
- Reproduction command(s)
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..primitives.terminal import run_and_observe


@dataclass
class TestFailure:
    """Information about a single test failure."""
    
    test_name: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    error_type: Optional[str] = None
    error_message: str = ""
    stack_trace: str = ""
    reproduction_cmd: Optional[str] = None


@dataclass
class TestTriageResult:
    """Result of test run and triage."""
    
    success: bool
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    duration_ms: float = 0
    failures: List[TestFailure] = field(default_factory=list)
    probable_files: List[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "duration_ms": self.duration_ms,
            "failures": [
                {
                    "test_name": f.test_name,
                    "file_path": f.file_path,
                    "error_type": f.error_type,
                    "error_message": f.error_message,
                }
                for f in self.failures
            ],
            "probable_files": self.probable_files,
            "exit_code": self.exit_code,
        }


def test_run_and_triage(
    test_cmd: str = "pytest -v",
    cwd: Optional[str] = None,
    timeout_sec: float = 300,
    test_file: Optional[str] = None,
) -> TestTriageResult:
    """Run tests and extract failure information.
    
    ACTION_TEST_RUN_AND_TRIAGE implementation.
    
    Args:
        test_cmd: Test command to run.
        cwd: Working directory.
        timeout_sec: Command timeout.
        test_file: Specific test file to run (appended to command).
    
    Returns:
        TestTriageResult with test results and failure details.
    """
    if cwd is None:
        cwd = os.getcwd()
    
    cmd = test_cmd
    if test_file:
        cmd = f"{test_cmd} {test_file}"
    
    result = run_and_observe(
        cmd,
        cwd=cwd,
        timeout_sec=timeout_sec,
        shell=True,
    )
    
    # Parse test output
    output = result.stdout + "\n" + result.stderr
    
    # Try to extract test counts (pytest style)
    total, passed, failed, skipped = _parse_pytest_summary(output)
    
    # Extract failures
    failures = _parse_pytest_failures(output, cwd)
    
    # Extract probable files from failures
    probable_files = list(set(f.file_path for f in failures if f.file_path))
    
    return TestTriageResult(
        success=result.exit_code == 0,
        total_tests=total,
        passed_tests=passed,
        failed_tests=failed,
        skipped_tests=skipped,
        duration_ms=result.duration_ms,
        failures=failures,
        probable_files=probable_files,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
    )


def _parse_pytest_summary(output: str) -> tuple:
    """Parse pytest summary line for test counts."""
    # Look for patterns like "5 passed, 2 failed, 1 skipped"
    # or "====== 5 passed in 1.23s ======"
    
    total = 0
    passed = 0
    failed = 0
    skipped = 0
    
    for line in output.split("\n"):
        # Match final summary line
        passed_match = re.search(r"(\d+) passed", line)
        failed_match = re.search(r"(\d+) failed", line)
        skipped_match = re.search(r"(\d+) skipped", line)
        error_match = re.search(r"(\d+) error", line)
        
        if passed_match:
            passed = int(passed_match.group(1))
        if failed_match:
            failed = int(failed_match.group(1))
        if skipped_match:
            skipped = int(skipped_match.group(1))
        if error_match:
            failed += int(error_match.group(1))
    
    total = passed + failed + skipped
    return total, passed, failed, skipped


def _parse_pytest_failures(output: str, cwd: str) -> List[TestFailure]:
    """Parse pytest output to extract failure details."""
    failures = []
    
    # Split by failure markers
    sections = re.split(r"_{10,}|={10,}", output)
    
    for section in sections:
        if "FAILED" not in section and "ERROR" not in section:
            continue
        
        # Try to extract test name
        test_match = re.search(r"(test_\w+|Test\w+::\w+)", section)
        if not test_match:
            continue
        
        test_name = test_match.group(1)
        
        # Try to extract file path and line
        file_match = re.search(r"([\w/]+\.py):(\d+)", section)
        file_path = None
        line_number = None
        if file_match:
            file_path = file_match.group(1)
            line_number = int(file_match.group(2))
        
        # Try to extract error type and message
        error_match = re.search(r"(\w+Error|\w+Exception): (.+?)(?:\n|$)", section)
        error_type = None
        error_message = ""
        if error_match:
            error_type = error_match.group(1)
            error_message = error_match.group(2)[:200]
        
        # Build reproduction command
        repro_cmd = None
        if file_path:
            repro_cmd = f"pytest {file_path}::{test_name} -v"
        
        failures.append(TestFailure(
            test_name=test_name,
            file_path=file_path,
            line_number=line_number,
            error_type=error_type,
            error_message=error_message,
            stack_trace=section[:1000],  # Limit trace size
            reproduction_cmd=repro_cmd,
        ))
    
    return failures
