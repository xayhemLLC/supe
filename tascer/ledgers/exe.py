"""Exe Ledger - Decision tree of intent.

The Exe Ledger captures what the agent intended:
- Overlord narratives and reasoning
- Proposed actions with rationale
- Rejected actions with reasons
- Confidence and uncertainty scores

This is INTENT - the record of thinking and decision-making.
Separated from reality (Moments) for forensic analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class DecisionType(Enum):
    """Types of decisions in the Exe Ledger."""
    NARRATIVE = "narrative"  # Overlord reasoning snapshot
    PROPOSE = "propose"      # Proposed action
    EXECUTE = "execute"      # Decided to execute
    REJECT = "reject"        # Rejected action
    STOP = "stop"            # Decision to stop
    BACKTRACK = "backtrack"  # Decision to undo/retry


class StopReason(Enum):
    """Reasons for stopping."""
    NO_LEGAL_ACTIONS = "no_legal_actions"
    LOW_INFORMATION_GAIN = "low_information_gain"
    REPEATED_OBSERVATIONS = "repeated_observations"
    BUDGET_EXHAUSTED = "budget_exhausted"
    HYPOTHESIS_PROVEN = "hypothesis_proven"
    HYPOTHESIS_DISPROVEN = "hypothesis_disproven"
    SAFETY_GUARD = "safety_guard"
    USER_INTERRUPT = "user_interrupt"
    GOAL_ACHIEVED = "goal_achieved"


@dataclass
class ConfidenceScore:
    """Confidence scoring for a decision."""

    value: float  # 0.0 to 1.0
    uncertainty: float = 0.0  # Epistemic uncertainty
    calibration_note: str | None = None  # Why this confidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "uncertainty": self.uncertainty,
            "calibration_note": self.calibration_note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfidenceScore":
        return cls(
            value=data["value"],
            uncertainty=data.get("uncertainty", 0.0),
            calibration_note=data.get("calibration_note"),
        )


@dataclass
class Decision:
    """A single decision in the Exe Ledger.

    Represents a moment of intent - what the agent was thinking
    and why it made a particular choice.
    """

    # Identity
    decision_id: str
    run_id: str
    sequence_num: int

    # Timing
    timestamp: datetime

    # Decision type
    decision_type: DecisionType

    # What action this relates to (if any)
    action_id: str | None = None

    # The reasoning/narrative
    narrative: str = ""

    # Alternatives considered
    alternatives: list[str] = field(default_factory=list)

    # Why rejected (for REJECT decisions)
    rejection_reason: str | None = None

    # Stop reason (for STOP decisions)
    stop_reason: StopReason | None = None

    # Confidence/uncertainty
    confidence: ConfidenceScore | None = None

    # Expected information gain
    expected_info_gain: float | None = None

    # Cross-reference to Moments entry
    moment_ref: str | None = None

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "run_id": self.run_id,
            "sequence_num": self.sequence_num,
            "timestamp": self.timestamp.isoformat(),
            "decision_type": self.decision_type.value,
            "action_id": self.action_id,
            "narrative": self.narrative,
            "alternatives": self.alternatives,
            "rejection_reason": self.rejection_reason,
            "stop_reason": self.stop_reason.value if self.stop_reason else None,
            "confidence": self.confidence.to_dict() if self.confidence else None,
            "expected_info_gain": self.expected_info_gain,
            "moment_ref": self.moment_ref,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Decision":
        return cls(
            decision_id=data["decision_id"],
            run_id=data["run_id"],
            sequence_num=data["sequence_num"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            decision_type=DecisionType(data["decision_type"]),
            action_id=data.get("action_id"),
            narrative=data.get("narrative", ""),
            alternatives=data.get("alternatives", []),
            rejection_reason=data.get("rejection_reason"),
            stop_reason=StopReason(data["stop_reason"]) if data.get("stop_reason") else None,
            confidence=ConfidenceScore.from_dict(data["confidence"]) if data.get("confidence") else None,
            expected_info_gain=data.get("expected_info_gain"),
            moment_ref=data.get("moment_ref"),
            metadata=data.get("metadata", {}),
        )


class ExeLedger:
    """Decision tree of intent.

    The Exe Ledger records what the agent was thinking and
    why it made decisions. This allows:
    - Forensic analysis of decision-making
    - Comparison with reality (Moments)
    - Debugging and improvement
    """

    def __init__(self, run_id: str):
        """Initialize ledger for a run.

        Args:
            run_id: Unique identifier for this run.
        """
        self.run_id = run_id
        self._decisions: list[Decision] = []
        self._sequence = 0

    def _create_decision(
        self,
        decision_type: DecisionType,
        **kwargs
    ) -> Decision:
        """Create and append a new decision."""
        self._sequence += 1

        decision = Decision(
            decision_id=f"{self.run_id}_d{self._sequence}",
            run_id=self.run_id,
            sequence_num=self._sequence,
            timestamp=datetime.now(),
            decision_type=decision_type,
            **kwargs,
        )

        self._decisions.append(decision)
        return decision

    def record_narrative(
        self,
        narrative: str,
        confidence: ConfidenceScore | None = None,
    ) -> Decision:
        """Record an Overlord narrative/reasoning snapshot."""
        return self._create_decision(
            DecisionType.NARRATIVE,
            narrative=narrative,
            confidence=confidence,
        )

    def record_proposal(
        self,
        action_id: str,
        narrative: str,
        alternatives: list[str] | None = None,
        expected_info_gain: float | None = None,
        confidence: ConfidenceScore | None = None,
    ) -> Decision:
        """Record a proposed action with rationale."""
        return self._create_decision(
            DecisionType.PROPOSE,
            action_id=action_id,
            narrative=narrative,
            alternatives=alternatives or [],
            expected_info_gain=expected_info_gain,
            confidence=confidence,
        )

    def record_execution(
        self,
        action_id: str,
        moment_ref: str | None = None,
        confidence: ConfidenceScore | None = None,
    ) -> Decision:
        """Record decision to execute an action."""
        return self._create_decision(
            DecisionType.EXECUTE,
            action_id=action_id,
            moment_ref=moment_ref,
            confidence=confidence,
        )

    def record_rejection(
        self,
        action_id: str,
        reason: str,
    ) -> Decision:
        """Record rejection of an action."""
        return self._create_decision(
            DecisionType.REJECT,
            action_id=action_id,
            rejection_reason=reason,
        )

    def record_stop(
        self,
        reason: StopReason,
        narrative: str,
    ) -> Decision:
        """Record decision to stop."""
        return self._create_decision(
            DecisionType.STOP,
            stop_reason=reason,
            narrative=narrative,
        )

    def record_backtrack(
        self,
        narrative: str,
        from_moment_ref: str | None = None,
    ) -> Decision:
        """Record decision to backtrack/retry."""
        return self._create_decision(
            DecisionType.BACKTRACK,
            narrative=narrative,
            moment_ref=from_moment_ref,
        )

    def get_all(self) -> list[Decision]:
        """Get all decisions (read-only copy)."""
        return list(self._decisions)

    def get_by_action(self, action_id: str) -> list[Decision]:
        """Get all decisions for a specific action."""
        return [d for d in self._decisions if d.action_id == action_id]

    def get_by_type(self, decision_type: DecisionType) -> list[Decision]:
        """Get all decisions of a specific type."""
        return [d for d in self._decisions if d.decision_type == decision_type]

    def get_proposals(self) -> list[Decision]:
        """Get all proposed actions."""
        return self.get_by_type(DecisionType.PROPOSE)

    def get_rejections(self) -> list[Decision]:
        """Get all rejected actions."""
        return self.get_by_type(DecisionType.REJECT)

    def get_stop_decision(self) -> Decision | None:
        """Get the stop decision if any."""
        stops = self.get_by_type(DecisionType.STOP)
        return stops[-1] if stops else None

    def get_latest(self, n: int = 1) -> list[Decision]:
        """Get the latest N decisions."""
        return self._decisions[-n:] if self._decisions else []

    def get_average_confidence(self) -> float | None:
        """Calculate average confidence across all decisions."""
        confidences = [
            d.confidence.value
            for d in self._decisions
            if d.confidence is not None
        ]
        return sum(confidences) / len(confidences) if confidences else None

    def to_dict(self) -> dict[str, Any]:
        """Serialize ledger to dictionary."""
        return {
            "run_id": self.run_id,
            "decisions": [d.to_dict() for d in self._decisions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExeLedger":
        """Deserialize ledger from dictionary."""
        ledger = cls(run_id=data["run_id"])
        ledger._decisions = [Decision.from_dict(d) for d in data["decisions"]]
        ledger._sequence = len(ledger._decisions)
        return ledger

    def __len__(self) -> int:
        return len(self._decisions)
