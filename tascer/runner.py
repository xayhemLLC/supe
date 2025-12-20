"""Tascer Runner Protocol.

Executes the full tasc validation lifecycle:
compile → snapshot → run actions → validate → emit report → store in AB

This is the main orchestration layer that ties together primitives,
gates, and reporting.
"""

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

from .contracts import (
    ActionResult,
    ActionSpec,
    Context,
    ErrorInfo,
    GateResult,
    ValidationReport,
)
from .primitives import capture_context, run_and_observe, TerminalResult
from .gates import ExitCodeGate, PatternGate
from .report import write_validation_report, format_summary


@dataclass
class TascRunner:
    """Orchestrates tasc execution and validation.
    
    Implements the runner protocol:
    1. Capture context (S0)
    2. Execute action
    3. Capture result (S1)
    4. Run validation gates
    5. Generate report
    6. Optionally store in AB
    """
    
    # Configuration
    output_dir: str = "./tascer_output"
    repo_root: Optional[str] = None
    env_allowlist: List[str] = field(default_factory=list)
    
    # Default gates applied to all runs
    default_gates: List = field(default_factory=lambda: [
        ExitCodeGate(expected=[0]),
        PatternGate(),
    ])
    
    # AB Memory instance for storage (optional)
    ab_memory: Optional[Any] = None
    
    def run_command(
        self,
        tasc_id: str,
        command: Union[str, List[str]],
        cwd: Optional[str] = None,
        timeout_sec: float = 60,
        gates: Optional[List] = None,
        action_name: Optional[str] = None,
        shell: bool = False,
    ) -> ValidationReport:
        """Execute a command and validate the result.
        
        Args:
            tasc_id: Identifier for this tasc.
            command: Command to run.
            cwd: Working directory.
            timeout_sec: Execution timeout.
            gates: Additional gates to apply. Default gates always run.
            action_name: Human-readable action name.
            shell: Whether to run through shell.
        
        Returns:
            ValidationReport with full execution details.
        """
        run_id = str(uuid.uuid4())[:8]
        
        # 1. Capture context (S0)
        context = capture_context(
            run_id=run_id,
            tasc_id=tasc_id,
            repo_root=self.repo_root or os.getcwd(),
            env_allowlist=self.env_allowlist,
            permissions=["terminal"],
        )
        
        # 2. Build action spec
        cmd_str = command if isinstance(command, str) else " ".join(command)
        action_spec = ActionSpec(
            id=f"run_{run_id}",
            name=action_name or cmd_str[:50],
            op_kind="command",
            op_ref=cmd_str,
            permissions_required=["terminal"],
            evidence_expected=["stdout", "stderr", "exit_code"],
        )
        
        # 3. Execute action
        terminal_result = run_and_observe(
            command=command,
            cwd=cwd or context.cwd,
            timeout_sec=timeout_sec,
            shell=shell,
        )
        
        # 4. Build action result
        action_result = ActionResult(
            status="success" if terminal_result.exit_code == 0 else "fail",
            op_result=terminal_result.exit_code,
            parsed={},
            evidence_paths=[],
            metrics={
                "duration_ms": terminal_result.duration_ms,
            },
        )
        
        if terminal_result.timed_out:
            action_result.status = "timeout"
            action_result.error = ErrorInfo(
                error_type="TimeoutError",
                message=f"Command timed out after {timeout_sec}s",
            )
        
        # 5. Finalize context (S1)
        context.finalize()
        
        # 6. Run gates
        all_gates = list(self.default_gates) + (gates or [])
        gates_passed = []
        gates_failed = []
        
        for gate in all_gates:
            if hasattr(gate, "check_terminal_result"):
                result = gate.check_terminal_result(terminal_result)
            elif hasattr(gate, "check"):
                # Try to call check with appropriate args
                try:
                    if isinstance(gate, ExitCodeGate):
                        result = gate.check(terminal_result.exit_code)
                    elif isinstance(gate, PatternGate):
                        result = gate.check(terminal_result.stdout, terminal_result.stderr)
                    else:
                        result = gate.check()
                except Exception as e:
                    result = GateResult(
                        gate_name=type(gate).__name__,
                        passed=False,
                        message=f"Gate error: {e}",
                    )
            else:
                continue
            
            if result.passed:
                gates_passed.append(result)
            else:
                gates_failed.append(result)
        
        # 7. Build report
        report = ValidationReport(
            run_id=run_id,
            tasc_id=tasc_id,
            context=context,
            action_spec=action_spec,
            action_result=action_result,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )
        report.compute_overall_status()
        report.generate_summary()
        
        # 8. Write report
        os.makedirs(self.output_dir, exist_ok=True)
        evidence_paths = write_validation_report(
            report=report,
            output_dir=self.output_dir,
        )
        report.evidence_index.update(evidence_paths)
        
        # Save stdout/stderr as evidence
        stdout_path = os.path.join(self.output_dir, f"{run_id}_{tasc_id}_stdout.txt")
        stderr_path = os.path.join(self.output_dir, f"{run_id}_{tasc_id}_stderr.txt")
        
        with open(stdout_path, "w") as f:
            f.write(terminal_result.stdout)
        report.evidence_index["stdout"] = stdout_path
        
        with open(stderr_path, "w") as f:
            f.write(terminal_result.stderr)
        report.evidence_index["stderr"] = stderr_path
        
        # 9. Optionally store in AB
        if self.ab_memory:
            self._store_in_ab(report)
        
        return report
    
    def _store_in_ab(self, report: ValidationReport) -> None:
        """Store report in AB Memory."""
        # Import here to avoid circular deps
        from .ab_storage import store_validation_report
        store_validation_report(self.ab_memory, report)


def run_tasc(
    tasc_id: str,
    command: Union[str, List[str]],
    **kwargs,
) -> ValidationReport:
    """Convenience function to run a tasc without creating a runner.
    
    Args:
        tasc_id: Tasc identifier.
        command: Command to execute.
        **kwargs: Additional arguments passed to TascRunner.run_command.
    
    Returns:
        ValidationReport with execution results.
    """
    runner = TascRunner()
    return runner.run_command(tasc_id=tasc_id, command=command, **kwargs)
