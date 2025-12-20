"""TASC_GATE_EXIT_CODE - Assert exit code expectations.

Assert exit_code == 0 (or other expected values).
"""

from dataclasses import dataclass, field
from typing import List, Union

from ..contracts import GateResult


@dataclass
class ExitCodeGate:
    """Gate that validates exit code against expected values."""
    
    expected: List[int] = field(default_factory=lambda: [0])
    
    def check(self, exit_code: int) -> GateResult:
        """Check if exit code matches expected values.
        
        Args:
            exit_code: The actual exit code from command execution.
        
        Returns:
            GateResult with pass/fail status.
        """
        passed = exit_code in self.expected
        
        if passed:
            message = f"Exit code {exit_code} is in expected values {self.expected}"
        else:
            message = f"Exit code {exit_code} not in expected values {self.expected}"
        
        return GateResult(
            gate_name="EXIT_CODE",
            passed=passed,
            message=message,
            evidence={
                "exit_code": exit_code,
                "expected": self.expected,
            },
        )
    
    def check_terminal_result(self, result) -> GateResult:
        """Check a TerminalResult object.
        
        Args:
            result: A TerminalResult from run_and_observe.
        
        Returns:
            GateResult with pass/fail status.
        """
        return self.check(result.exit_code)
