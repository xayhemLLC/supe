"""TASC_GATE_GAP - Validate knowledge gaps are below threshold.

Validates that the number of identified knowledge gaps from a learning
session is below the maximum allowed threshold.
"""

from dataclasses import dataclass

from ..contracts import GateResult


@dataclass
class GapGate:
    """Gate that validates number of gaps is below threshold.

    Used in learning validation to ensure the agent doesn't have too many
    unresolved knowledge gaps before marking learning as complete.
    """

    max_gaps: int = 5

    def check(self, actual_gaps: int) -> GateResult:
        """Check if gap count is below maximum threshold.

        Args:
            actual_gaps: The actual number of knowledge gaps identified.

        Returns:
            GateResult with pass/fail status.
        """
        passed = actual_gaps <= self.max_gaps

        comparison = "≤" if passed else ">"
        message = f"Gaps {actual_gaps} {comparison} {self.max_gaps}"

        return GateResult(
            gate_name="GAP",
            passed=passed,
            message=message,
            evidence={
                "actual_gaps": actual_gaps,
                "max_allowed_gaps": self.max_gaps,
                "margin": self.max_gaps - actual_gaps,
            },
        )
