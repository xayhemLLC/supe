"""Control primitives.

ACTIONS:
- sleep.wait: Explicit wait with reason
- noop: Explicit no-operation
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class WaitResult:
    """Result of sleep/wait operation."""
    
    duration_ms: float
    reason: str
    started_at: datetime
    ended_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration_ms": self.duration_ms,
            "reason": self.reason,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
        }


@dataclass
class NoopResult:
    """Result of noop operation."""
    
    reason: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }


def sleep_wait(
    duration_ms: float,
    reason: str = "Waiting for condition",
) -> WaitResult:
    """Explicit wait with documented reason.
    
    ACTION: sleep.wait
    
    This creates a visible, documented pause in execution.
    The reason is recorded for audit and understanding.
    
    Args:
        duration_ms: Time to wait in milliseconds.
        reason: Why we're waiting (for audit/understanding).
    
    Returns:
        WaitResult with actual duration and timing.
    """
    started_at = datetime.now()
    
    # Sleep
    time.sleep(duration_ms / 1000.0)
    
    ended_at = datetime.now()
    actual_duration = (ended_at - started_at).total_seconds() * 1000
    
    return WaitResult(
        duration_ms=actual_duration,
        reason=reason,
        started_at=started_at,
        ended_at=ended_at,
    )


def noop(reason: str = "Explicit no-operation") -> NoopResult:
    """Explicit no-operation for decision legibility.
    
    ACTION: noop
    
    Sometimes the right action is to do nothing.
    This makes that decision visible and documented.
    
    Args:
        reason: Why we're choosing to do nothing.
    
    Returns:
        NoopResult with reason and timestamp.
    """
    return NoopResult(
        reason=reason,
        timestamp=datetime.now(),
    )
