"""TASC_PROVE_TESTS_PASSING - Prove test suite passes.

Runs test command and proves:
- Exit code ok
- JUnit/coverage artifacts (optional)
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..primitives import capture_context, run_and_observe
from ..actions.test import test_run_and_triage, TestTriageResult
from ..gates import ExitCodeGate, PatternGate
from ..contracts import GateResult


@dataclass
class TestProofResult:
    """Result of proving tests pass."""
    
    proven: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    gate_results: List[GateResult] = field(default_factory=list)
    failure_summary: List[Dict] = field(default_factory=list)
    coverage_percent: Optional[float] = None
    duration_ms: float = 0
    stdout: str = ""
    stderr: str = ""
    context_snapshot: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "proven": self.proven,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "coverage_percent": self.coverage_percent,
            "duration_ms": self.duration_ms,
            "gate_results": [g.to_dict() for g in self.gate_results],
            "failure_summary": self.failure_summary,
        }


def prove_tests_passing(
    test_cmd: str = "pytest -v",
    cwd: Optional[str] = None,
    timeout_sec: float = 300,
    allow_skipped: bool = True,
    require_coverage: bool = False,
    min_coverage: float = 0.0,
    tasc_id: str = "test_proof",
) -> TestProofResult:
    """Prove that test suite passes.
    
    TASC_PROVE_TESTS_PASSING implementation.
    
    Args:
        test_cmd: Test command to run.
        cwd: Working directory.
        timeout_sec: Command timeout.
        allow_skipped: Whether skipped tests are acceptable.
        require_coverage: Whether to check coverage threshold.
        min_coverage: Minimum coverage percentage required.
        tasc_id: Identifier for context capture.
    
    Returns:
        TestProofResult proving test status.
    """
    if cwd is None:
        cwd = os.getcwd()
    
    # Capture context
    context = capture_context(
        tasc_id=tasc_id,
        repo_root=cwd,
        permissions=["terminal"],
    )
    
    # Run tests with triage
    triage = test_run_and_triage(
        test_cmd=test_cmd,
        cwd=cwd,
        timeout_sec=timeout_sec,
    )
    
    # Build failure summary
    failure_summary = [
        {
            "test": f.test_name,
            "file": f.file_path,
            "error": f.error_type,
            "message": f.error_message[:100],
        }
        for f in triage.failures[:10]  # Limit to first 10
    ]
    
    # Apply gates
    gate_results = []
    
    # Exit code gate
    exit_gate = ExitCodeGate(expected=[0])
    exit_result = exit_gate.check(triage.exit_code)
    gate_results.append(exit_result)
    
    # Pattern gate (check for unexpected errors in output)
    pattern_gate = PatternGate(
        denylist=[r"(?i)fatal", r"(?i)panic"],
        check_stderr=True,
    )
    pattern_result = pattern_gate.check(triage.stdout, triage.stderr)
    gate_results.append(pattern_result)
    
    # Custom gate for test counts
    tests_gate = GateResult(
        gate_name="TESTS_COUNT",
        passed=triage.failed_tests == 0,
        message=f"{triage.passed_tests} passed, {triage.failed_tests} failed, {triage.skipped_tests} skipped",
        evidence={
            "passed": triage.passed_tests,
            "failed": triage.failed_tests,
            "skipped": triage.skipped_tests,
        },
    )
    gate_results.append(tests_gate)
    
    # Parse coverage if available
    coverage = _parse_coverage(triage.stdout)
    
    if require_coverage and coverage is not None:
        coverage_gate = GateResult(
            gate_name="COVERAGE_THRESHOLD",
            passed=coverage >= min_coverage,
            message=f"Coverage {coverage:.1f}% {'≥' if coverage >= min_coverage else '<'} {min_coverage}%",
            evidence={"coverage": coverage, "min_required": min_coverage},
        )
        gate_results.append(coverage_gate)
    
    # Determine overall proof status
    proven = all(g.passed for g in gate_results)
    
    context.finalize()
    
    return TestProofResult(
        proven=proven,
        total_tests=triage.total_tests,
        passed_tests=triage.passed_tests,
        failed_tests=triage.failed_tests,
        skipped_tests=triage.skipped_tests,
        gate_results=gate_results,
        failure_summary=failure_summary,
        coverage_percent=coverage,
        duration_ms=triage.duration_ms,
        stdout=triage.stdout,
        stderr=triage.stderr,
        context_snapshot=context.to_dict(),
    )


def _parse_coverage(output: str) -> Optional[float]:
    """Try to parse coverage percentage from pytest output."""
    import re
    
    # Look for patterns like "TOTAL ... 85%" or "Coverage: 85.5%"
    patterns = [
        r"TOTAL\s+\d+\s+\d+\s+(\d+(?:\.\d+)?)%",
        r"Coverage[:\s]+(\d+(?:\.\d+)?)%",
        r"(\d+(?:\.\d+)?)%\s+covered",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return float(match.group(1))
    
    return None
