"""TASC_PROVE_LINT_PASSING - Prove lint passes in repository.

Runs lint command in repo root and proves:
- Exit code ok
- No error patterns
- Artifacts captured
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..primitives import capture_context, run_and_observe
from ..gates import ExitCodeGate, PatternGate
from ..contracts import GateResult, ValidationReport, ActionSpec, ActionResult


@dataclass
class LintProofResult:
    """Result of proving lint passes."""
    
    proven: bool
    exit_code: int
    error_count: int
    warnings_count: int
    gate_results: List[GateResult] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0
    context_snapshot: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "proven": self.proven,
            "exit_code": self.exit_code,
            "error_count": self.error_count,
            "warnings_count": self.warnings_count,
            "duration_ms": self.duration_ms,
            "gate_results": [g.to_dict() for g in self.gate_results],
        }


def prove_lint_passing(
    lint_cmd: str = "ruff check .",
    cwd: Optional[str] = None,
    timeout_sec: float = 120,
    allow_warnings: int = 0,
    tasc_id: str = "lint_proof",
) -> LintProofResult:
    """Prove that lint passes in the repository.
    
    TASC_PROVE_LINT_PASSING implementation.
    
    Args:
        lint_cmd: Lint command to run.
        cwd: Working directory (repo root).
        timeout_sec: Command timeout.
        allow_warnings: Maximum warnings allowed.
        tasc_id: Identifier for context capture.
    
    Returns:
        LintProofResult proving lint status.
    """
    if cwd is None:
        cwd = os.getcwd()
    
    # Capture context
    context = capture_context(
        tasc_id=tasc_id,
        repo_root=cwd,
        permissions=["terminal"],
    )
    
    # Run lint command
    result = run_and_observe(
        lint_cmd,
        cwd=cwd,
        timeout_sec=timeout_sec,
        shell=True,
    )
    
    # Count errors and warnings
    output = result.stdout + result.stderr
    error_count = _count_pattern(output, [r"error", r": E\d+", r": F\d+"])
    warnings_count = _count_pattern(output, [r"warning", r": W\d+"])
    
    # Apply gates
    gates = [
        ExitCodeGate(expected=[0]),
        PatternGate(
            severity_threshold=allow_warnings,
            check_stderr=True,
        ),
    ]
    
    gate_results = []
    all_passed = True
    
    for gate in gates:
        if hasattr(gate, "check_terminal_result"):
            gate_result = gate.check_terminal_result(result)
        elif isinstance(gate, ExitCodeGate):
            gate_result = gate.check(result.exit_code)
        elif isinstance(gate, PatternGate):
            gate_result = gate.check(result.stdout, result.stderr)
        else:
            continue
        
        gate_results.append(gate_result)
        if not gate_result.passed:
            all_passed = False
    
    context.finalize()
    
    return LintProofResult(
        proven=all_passed,
        exit_code=result.exit_code,
        error_count=error_count,
        warnings_count=warnings_count,
        gate_results=gate_results,
        stdout=result.stdout,
        stderr=result.stderr,
        duration_ms=result.duration_ms,
        context_snapshot=context.to_dict(),
    )


def _count_pattern(text: str, patterns: List[str]) -> int:
    """Count occurrences of patterns in text."""
    import re
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text, re.IGNORECASE))
    return count
