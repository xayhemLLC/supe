"""Overlord Decision System.

Implements intelligent stopping and decision-making.
Stopping is a DECISION, not a timeout.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ..ledgers import MomentsLedger, ExeLedger


class StopCondition(Enum):
    """Reasons the Overlord may decide to stop."""
    
    NO_LEGAL_ACTIONS = "no_legal_actions"
    LOW_INFORMATION_GAIN = "low_information_gain"
    REPEATED_OBSERVATIONS = "repeated_observations"
    BUDGET_EXHAUSTED = "budget_exhausted"
    HYPOTHESIS_PROVEN = "hypothesis_proven"
    HYPOTHESIS_DISPROVEN = "hypothesis_disproven"
    SAFETY_GUARD = "safety_guard"
    USER_INTERRUPT = "user_interrupt"
    GOAL_ACHIEVED = "goal_achieved"
    MAX_ITERATIONS = "max_iterations"
    CONVERGENCE = "convergence"


@dataclass
class OverlordDecision:
    """A decision from the Overlord.
    
    The Overlord decides whether to continue, what action to take,
    or when and why to stop.
    """
    
    # Decision type
    decision: str  # "CONTINUE", "STOP", "BACKTRACK"
    
    # For CONTINUE
    next_action: Optional[str] = None
    action_inputs: Dict[str, Any] = field(default_factory=dict)
    
    # For STOP
    stop_reason: Optional[StopCondition] = None
    
    # Reasoning
    narrative: str = ""
    confidence: float = 0.0
    
    # Alternatives considered
    alternatives: List[str] = field(default_factory=list)
    
    # Metrics
    information_gain_expected: float = 0.0
    actions_remaining: int = 0
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "next_action": self.next_action,
            "action_inputs": self.action_inputs,
            "stop_reason": self.stop_reason.value if self.stop_reason else None,
            "narrative": self.narrative,
            "confidence": self.confidence,
            "alternatives": self.alternatives,
            "information_gain_expected": self.information_gain_expected,
            "actions_remaining": self.actions_remaining,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class StopConditionState:
    """Current state for evaluating stop conditions."""
    
    # Action legality
    legal_actions: Set[str] = field(default_factory=set)
    
    # Information gain
    recent_info_gains: List[float] = field(default_factory=list)
    info_gain_threshold: float = 0.1
    
    # Observation tracking
    recent_observation_hashes: List[str] = field(default_factory=list)
    max_repeated_observations: int = 3
    
    # Budget
    actions_taken: int = 0
    max_actions: int = 100
    
    # Hypothesis tracking
    hypothesis: Optional[str] = None
    hypothesis_status: Optional[str] = None  # proven, disproven, unknown
    
    # Safety
    safety_violations: List[str] = field(default_factory=list)
    
    # Goal tracking
    goal_achieved: bool = False


def evaluate_stop_conditions(
    state: StopConditionState,
) -> List[tuple[StopCondition, str]]:
    """Evaluate all stop conditions.
    
    Args:
        state: Current state for evaluation.
    
    Returns:
        List of triggered (condition, reason) tuples.
    """
    triggered = []
    
    # No legal actions remaining
    if not state.legal_actions:
        triggered.append((
            StopCondition.NO_LEGAL_ACTIONS,
            "No legal actions remain given current permissions and constraints."
        ))
    
    # Low information gain
    if len(state.recent_info_gains) >= 3:
        avg_gain = sum(state.recent_info_gains[-3:]) / 3
        if avg_gain < state.info_gain_threshold:
            triggered.append((
                StopCondition.LOW_INFORMATION_GAIN,
                f"Average information gain ({avg_gain:.3f}) below threshold ({state.info_gain_threshold})."
            ))
    
    # Repeated identical observations
    if len(state.recent_observation_hashes) >= state.max_repeated_observations:
        recent = state.recent_observation_hashes[-state.max_repeated_observations:]
        if len(set(recent)) == 1:
            triggered.append((
                StopCondition.REPEATED_OBSERVATIONS,
                f"Last {state.max_repeated_observations} observations were identical."
            ))
    
    # Budget exhaustion
    if state.actions_taken >= state.max_actions:
        triggered.append((
            StopCondition.BUDGET_EXHAUSTED,
            f"Action budget exhausted ({state.actions_taken}/{state.max_actions})."
        ))
    
    # Hypothesis status
    if state.hypothesis_status == "proven":
        triggered.append((
            StopCondition.HYPOTHESIS_PROVEN,
            f"Hypothesis proven: {state.hypothesis}"
        ))
    elif state.hypothesis_status == "disproven":
        triggered.append((
            StopCondition.HYPOTHESIS_DISPROVEN,
            f"Hypothesis disproven: {state.hypothesis}"
        ))
    
    # Safety violations
    if state.safety_violations:
        triggered.append((
            StopCondition.SAFETY_GUARD,
            f"Safety violations detected: {', '.join(state.safety_violations)}"
        ))
    
    # Goal achieved
    if state.goal_achieved:
        triggered.append((
            StopCondition.GOAL_ACHIEVED,
            "Goal has been achieved."
        ))
    
    return triggered


def should_stop(state: StopConditionState) -> Optional[OverlordDecision]:
    """Check if Overlord should stop.
    
    Args:
        state: Current state for evaluation.
    
    Returns:
        OverlordDecision with stop reason, or None to continue.
    """
    triggered = evaluate_stop_conditions(state)
    
    if not triggered:
        return None
    
    # Pick highest priority stop condition
    # Priority: safety > goal > hypothesis > budget > info gain
    priority_order = [
        StopCondition.SAFETY_GUARD,
        StopCondition.GOAL_ACHIEVED,
        StopCondition.HYPOTHESIS_PROVEN,
        StopCondition.HYPOTHESIS_DISPROVEN,
        StopCondition.NO_LEGAL_ACTIONS,
        StopCondition.BUDGET_EXHAUSTED,
        StopCondition.REPEATED_OBSERVATIONS,
        StopCondition.LOW_INFORMATION_GAIN,
    ]
    
    for priority_condition in priority_order:
        for condition, reason in triggered:
            if condition == priority_condition:
                return OverlordDecision(
                    decision="STOP",
                    stop_reason=condition,
                    narrative=reason,
                    confidence=0.9,
                )
    
    # Fallback (shouldn't reach here)
    condition, reason = triggered[0]
    return OverlordDecision(
        decision="STOP",
        stop_reason=condition,
        narrative=reason,
        confidence=0.7,
    )


def create_continue_decision(
    action: str,
    inputs: Dict[str, Any],
    narrative: str,
    confidence: float = 0.8,
    alternatives: Optional[List[str]] = None,
    info_gain: float = 0.0,
) -> OverlordDecision:
    """Create a decision to continue with an action."""
    return OverlordDecision(
        decision="CONTINUE",
        next_action=action,
        action_inputs=inputs,
        narrative=narrative,
        confidence=confidence,
        alternatives=alternatives or [],
        information_gain_expected=info_gain,
    )


def create_backtrack_decision(
    narrative: str,
    confidence: float = 0.7,
) -> OverlordDecision:
    """Create a decision to backtrack."""
    return OverlordDecision(
        decision="BACKTRACK",
        narrative=narrative,
        confidence=confidence,
    )
