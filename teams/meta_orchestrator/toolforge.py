"""ToolForge signal detection for meta-orchestrator v1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..nubflow.types import new_sid


@dataclass
class PainSignal:
    """Observed repeated friction during execution."""

    signal_key: str
    count: int
    examples: list[str] = field(default_factory=list)
    desired_constraint: str = ""
    sid: str = field(default_factory=new_sid)


@dataclass
class ToolForgeRequest:
    """Resulting request to create templates/gates/constraints/ops."""

    pain_signal: str
    new_template: str | None = None
    new_gate: str | None = None
    new_constraint: str | None = None
    new_op: str | None = None
    sid: str = field(default_factory=new_sid)


class ToolForge:
    """Generate ToolForge requests from repeated pain signals."""

    def detect_pain_signals(self, action_records: list[dict[str, Any]]) -> list[PainSignal]:
        counts: dict[str, list[str]] = {}
        for record in action_records:
            status = str(record.get("status", ""))
            op_name = str(record.get("op", "unknown_op"))
            if status not in {"failed", "hold", "error"}:
                continue
            key = f"{status}:{op_name}"
            counts.setdefault(key, []).append(str(record.get("message") or ""))

        signals: list[PainSignal] = []
        for key, examples in counts.items():
            if len(examples) < 2:
                continue
            if key.startswith("hold:"):
                desired = "reduce_human_gate_latency"
            elif key.startswith("failed:"):
                desired = "improve_action_reliability"
            else:
                desired = "increase_execution_stability"
            signals.append(
                PainSignal(
                    signal_key=key,
                    count=len(examples),
                    examples=examples[:3],
                    desired_constraint=desired,
                )
            )
        return signals

    def forge(self, signals: list[PainSignal]) -> list[ToolForgeRequest]:
        requests: list[ToolForgeRequest] = []
        for signal in signals:
            normalized = signal.signal_key.replace(":", "_")
            requests.append(
                ToolForgeRequest(
                    pain_signal=signal.signal_key,
                    new_template=f"Template_{normalized}",
                    new_gate=f"Gate_{normalized}",
                    new_constraint=signal.desired_constraint,
                    new_op=f"Op_{normalized}",
                )
            )
        return requests
