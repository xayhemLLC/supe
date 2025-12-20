"""TASC_PROVE_SCRIPT_SUCCESS - Prove a script runs successfully.

Given a script operation:
- Confirms exit code
- Confirms output schema or expected file outputs
- Confirms no error patterns
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from ..primitives import capture_context, run_and_observe
from ..primitives.file_ops import snapshot_file, FileSnapshot
from ..gates import ExitCodeGate, PatternGate, JsonPathGate, JsonPathAssertion
from ..contracts import GateResult


@dataclass
class ScriptProofResult:
    """Result of proving script success."""
    
    proven: bool
    exit_code: int
    gate_results: List[GateResult] = field(default_factory=list)
    output_files_valid: bool = True
    missing_outputs: List[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0
    parsed_output: Optional[Dict] = None
    context_snapshot: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "proven": self.proven,
            "exit_code": self.exit_code,
            "output_files_valid": self.output_files_valid,
            "missing_outputs": self.missing_outputs,
            "duration_ms": self.duration_ms,
            "gate_results": [g.to_dict() for g in self.gate_results],
        }


def prove_script_success(
    command: Union[str, List[str]],
    cwd: Optional[str] = None,
    timeout_sec: float = 120,
    expected_exit_codes: List[int] = None,
    expected_output_files: List[str] = None,
    output_json_assertions: Dict[str, Any] = None,
    error_patterns: List[str] = None,
    tasc_id: str = "script_proof",
    shell: bool = True,
) -> ScriptProofResult:
    """Prove that a script executes successfully.
    
    TASC_PROVE_SCRIPT_SUCCESS implementation.
    
    Args:
        command: Script command to run.
        cwd: Working directory.
        timeout_sec: Command timeout.
        expected_exit_codes: Expected exit codes (default [0]).
        expected_output_files: Files that should exist after execution.
        output_json_assertions: JSONPath assertions on stdout (if JSON).
        error_patterns: Additional patterns to deny in output.
        tasc_id: Identifier for context capture.
        shell: Whether to run through shell.
    
    Returns:
        ScriptProofResult proving script status.
    """
    if cwd is None:
        cwd = os.getcwd()
    
    if expected_exit_codes is None:
        expected_exit_codes = [0]
    
    # Capture context
    context = capture_context(
        tasc_id=tasc_id,
        repo_root=cwd,
        permissions=["terminal", "fs_write"],
    )
    
    # Run script
    result = run_and_observe(
        command,
        cwd=cwd,
        timeout_sec=timeout_sec,
        shell=shell,
    )
    
    gate_results = []
    
    # Exit code gate
    exit_gate = ExitCodeGate(expected=expected_exit_codes)
    exit_result = exit_gate.check(result.exit_code)
    gate_results.append(exit_result)
    
    # Pattern gate
    deny_patterns = [r"(?i)error:", r"(?i)exception:", r"(?i)fatal:"]
    if error_patterns:
        deny_patterns.extend(error_patterns)
    
    pattern_gate = PatternGate(denylist=deny_patterns)
    pattern_result = pattern_gate.check(result.stdout, result.stderr)
    gate_results.append(pattern_result)
    
    # Check expected output files
    missing_outputs = []
    if expected_output_files:
        for output_file in expected_output_files:
            full_path = os.path.join(cwd, output_file) if not os.path.isabs(output_file) else output_file
            snap = snapshot_file(full_path, preview_bytes=0, compute_hash=False)
            if not snap.exists:
                missing_outputs.append(output_file)
        
        files_gate = GateResult(
            gate_name="OUTPUT_FILES",
            passed=len(missing_outputs) == 0,
            message=f"Expected output files: {len(expected_output_files) - len(missing_outputs)}/{len(expected_output_files)} present",
            evidence={"missing": missing_outputs},
        )
        gate_results.append(files_gate)
    
    # Check JSON output assertions
    parsed_output = None
    if output_json_assertions:
        try:
            import json
            parsed_output = json.loads(result.stdout)
            
            assertions = [
                JsonPathAssertion(path=path, expected=value, operator="eq")
                for path, value in output_json_assertions.items()
            ]
            json_gate = JsonPathGate(assertions=assertions)
            json_result = json_gate.check(data=parsed_output)
            gate_results.append(json_result)
        except Exception as e:
            json_gate = GateResult(
                gate_name="JSONPATH",
                passed=False,
                message=f"Failed to parse JSON output: {e}",
                evidence={},
            )
            gate_results.append(json_gate)
    
    # Determine overall proof status
    proven = all(g.passed for g in gate_results)
    
    context.finalize()
    
    return ScriptProofResult(
        proven=proven,
        exit_code=result.exit_code,
        gate_results=gate_results,
        output_files_valid=len(missing_outputs) == 0,
        missing_outputs=missing_outputs,
        stdout=result.stdout,
        stderr=result.stderr,
        duration_ms=result.duration_ms,
        parsed_output=parsed_output,
        context_snapshot=context.to_dict(),
    )
