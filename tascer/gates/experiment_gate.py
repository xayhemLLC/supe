"""TASC_GATE_EXPERIMENT - Validate experiments passed successfully.

Validates that experiments in EXPLORE mode learning have a sufficient
pass rate to validate the learned theorems and conjectures.
"""

from dataclasses import dataclass

from ..contracts import GateResult


@dataclass
class ExperimentGate:
    """Gate that validates experiment pass rate meets threshold.

    Used in EXPLORE mode learning validation to ensure experiments
    validating theorems and conjectures have sufficient success rate.
    """

    min_pass_rate: float = 0.8

    def check(self, passed: int, total: int) -> GateResult:
        """Check if experiment pass rate meets minimum threshold.

        Args:
            passed: Number of experiments that passed.
            total: Total number of experiments run.

        Returns:
            GateResult with pass/fail status.
        """
        # Calculate pass rate (0.0 if no experiments)
        rate = passed / total if total > 0 else 0.0
        gate_passed = rate >= self.min_pass_rate

        # Handle edge case of no experiments
        if total == 0:
            message = "No experiments run (considered passing)"
            gate_passed = True
        else:
            comparison = "≥" if gate_passed else "<"
            message = f"Pass rate {rate:.1%} {comparison} {self.min_pass_rate:.1%} ({passed}/{total})"

        return GateResult(
            gate_name="EXPERIMENT",
            passed=gate_passed,
            message=message,
            evidence={
                "experiments_passed": passed,
                "experiments_total": total,
                "pass_rate": rate,
                "required_pass_rate": self.min_pass_rate,
                "margin": rate - self.min_pass_rate,
            },
        )
