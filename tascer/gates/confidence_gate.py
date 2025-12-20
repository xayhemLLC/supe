"""TASC_GATE_CONFIDENCE - Validate learning confidence meets threshold.

Validates that the confidence score from a learning session meets
the required threshold for validated learning.
"""

from dataclasses import dataclass

from ..contracts import GateResult


@dataclass
class ConfidenceGate:
    """Gate that validates confidence score meets minimum threshold.

    Used in learning validation to ensure the agent has sufficient
    confidence in the learned material before marking as complete.
    """

    min_confidence: float = 0.7

    def check(self, actual_confidence: float) -> GateResult:
        """Check if confidence score meets minimum threshold.

        Args:
            actual_confidence: The actual confidence score (0.0-1.0).

        Returns:
            GateResult with pass/fail status.
        """
        passed = actual_confidence >= self.min_confidence

        comparison = "≥" if passed else "<"
        message = f"Confidence {actual_confidence:.2f} {comparison} {self.min_confidence:.2f}"

        return GateResult(
            gate_name="CONFIDENCE",
            passed=passed,
            message=message,
            evidence={
                "actual_confidence": actual_confidence,
                "required_confidence": self.min_confidence,
                "margin": actual_confidence - self.min_confidence,
            },
        )
