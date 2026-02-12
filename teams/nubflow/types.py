"""Core types for Flow of Time (FoT) v0.0.0."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from itertools import count
from typing import Any, Protocol

_SNOWFLAKE_EPOCH_MS = 1704067200000  # 2024-01-01T00:00:00Z
_SNOWFLAKE_SEQ_BITS = 22
_SNOWFLAKE_SEQ_MASK = (1 << _SNOWFLAKE_SEQ_BITS) - 1
_sid_counter = count(0)


def utcnow_iso() -> str:
    """Return a naive UTC timestamp string."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def new_sid(now: datetime | None = None) -> str:
    """Return a Discord-style decimal Snowflake64-like identifier string."""
    ts = now or datetime.now(timezone.utc)
    now_ms = int(ts.timestamp() * 1000)
    seq = next(_sid_counter) & _SNOWFLAKE_SEQ_MASK
    value = max(0, (now_ms - _SNOWFLAKE_EPOCH_MS))
    sid_value = (value << _SNOWFLAKE_SEQ_BITS) | seq
    return str(sid_value)


class FoTState(str, Enum):
    """Finite state machine states for FoT."""

    ENTER = "nub::enter"
    ABSORB = "nub::absorb"
    STORE = "nub::store"
    ROUTE = "nub::route"
    TRANSFORM = "nub::transform"
    FINALIZE = "nub::finalize"
    OVERLORD_COMMIT = "nub::overlord_commit"
    EXIT = "nub::exit"
    HOLD = "nub::hold"
    ERROR = "nub::error"


class BufferStatus(str, Enum):
    """Lifecycle status for buffers."""

    PENDING = "pending"
    OK = "ok"
    FAILED = "failed"
    SKIPPED = "skipped"
    HELD = "held"


@dataclass
class InputEvent:
    """Normalized event entering FoT."""

    kind: str
    payload: Any
    source: str = "system"
    timestamp: str = field(default_factory=utcnow_iso)
    sid: str = field(default_factory=new_sid)


@dataclass
class LedgerCursor:
    """Pagination and query state for a ledger."""

    ledger_sid: str
    query_plan: dict[str, Any] = field(default_factory=dict)
    last_seen: str | None = None
    paging_cursor: str | None = None


@dataclass
class LedgerQueryResult:
    """Result returned by ``LedgerRef.query``."""

    items: list[dict[str, Any]]
    next_cursor: str | None = None
    evidence_pack: dict[str, Any] = field(default_factory=dict)


@dataclass
class LedgerSummaryResult:
    """Result returned by ``LedgerRef.summarize``."""

    summary_artifact: dict[str, Any]
    pointers: list[str] = field(default_factory=list)


class LedgerRef(Protocol):
    """Ledger adapter interface used by FoT routing."""

    sid: str
    kind: str

    def query(
        self,
        query_plan: dict[str, Any],
        cursor: LedgerCursor,
        budget: int,
    ) -> LedgerQueryResult:
        """Query the ledger and return items and cursor delta."""

    def summarize(
        self,
        items: list[dict[str, Any]],
        goal: str,
        budget: int,
    ) -> LedgerSummaryResult:
        """Produce summarized artifacts from query items."""


@dataclass
class Buffer:
    """Routed value with metadata and provenance."""

    name: str
    kind: str
    payload: Any = None
    sid: str = field(default_factory=new_sid)
    status: BufferStatus = BufferStatus.PENDING
    error: str | None = None
    provenance: list[str] = field(default_factory=list)
    ttl: int | None = None
    transforms: list[str] = field(default_factory=list)
    destination: str | None = None
    ledger_ref_sid: str | None = None
    cursor: LedgerCursor | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteToken:
    """Execution token that traverses the buffer graph."""

    buffer_sid: str
    current_node: str
    sid: str = field(default_factory=new_sid)
    hop_count: int = 0
    provenance: list[str] = field(default_factory=list)
    budget_used: int = 0
    status: BufferStatus = BufferStatus.PENDING
    error: str | None = None


ConditionFn = Callable[[Buffer, RouteToken, "NubContext"], bool]


@dataclass
class TransformResult:
    """Result returned by a buffer-node transform hook."""

    applicable: bool = True
    buffers: list[Buffer] = field(default_factory=list)
    error: str | None = None
    hold: bool = False
    hold_reason: str | None = None
    stop_token: bool = False


TransformFn = Callable[[Buffer, RouteToken, "NubContext"], TransformResult]


@dataclass
class BufferNode:
    """Node in the FoT buffer graph."""

    name: str
    kind: str
    sid: str = field(default_factory=new_sid)
    transform: TransformFn | None = None
    is_terminal: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BufferEdge:
    """Directed edge in the FoT buffer graph."""

    from_node: str
    to_node: str
    sid: str = field(default_factory=new_sid)
    condition: ConditionFn | None = None
    max_hops: int = 12
    weight: float = 1.0


@dataclass
class RouteBounds:
    """Global bounds to keep routing deterministic and safe."""

    max_hops: int = 12
    max_tokens: int = 200
    max_ms: int = 8000


@dataclass
class RouteOutcome:
    """Summary of one bounded routing pass."""

    final_buffers: list[Buffer] = field(default_factory=list)
    active_tokens: int = 0
    emitted_tokens: int = 0
    holds: list[Buffer] = field(default_factory=list)
    errors: list[Buffer] = field(default_factory=list)
    exhausted_budget: bool = False


@dataclass
class HoldPack:
    """Pack produced when human signoff is required."""

    reason: str
    required_signoff: str
    artifact_key: str = "signoff_artifact"
    sid: str = field(default_factory=new_sid)


@dataclass
class ErrorPack:
    """Pack produced when a recoverable error occurs."""

    message: str
    recoverable: bool = True
    code: str = "route_error"
    details: dict[str, Any] = field(default_factory=dict)
    sid: str = field(default_factory=new_sid)


@dataclass
class AwarenessTrack:
    """Overlord awareness-track output."""

    objective: str = ""
    decisions: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    top_risks: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    ledger_pointers: list[str] = field(default_factory=list)


@dataclass
class ExecutionTrack:
    """Overlord execution-track output."""

    next_actions: list[str] = field(default_factory=list)
    gates_and_signoffs: list[str] = field(default_factory=list)
    artifacts_to_produce: list[str] = field(default_factory=list)
    stop_conditions: list[str] = field(default_factory=list)
    wip_budget: int = 0


@dataclass
class NubContext:
    """Per-moment FoT execution context."""

    nub_sid: str
    start_time: str
    budget: int
    constraints: dict[str, Any] = field(default_factory=dict)
    active_workflow_cursor: str | None = None
    team_scope: str | None = None
    state: FoTState = FoTState.ENTER
    budget_used: int = 0
    audit: list[str] = field(default_factory=list)


@dataclass
class OverlordCommitResult:
    """Result returned by Overlord commit."""

    output_buffers: list[Buffer]
    awareness_track: AwarenessTrack
    execution_track: ExecutionTrack
    working_context_pack: dict[str, Any] = field(default_factory=dict)
    updated_ledger_cursors: dict[str, LedgerCursor] = field(default_factory=dict)
    next_query_plan_seeds: dict[str, dict[str, Any]] = field(default_factory=dict)
    next_moment_refs: list[str] = field(default_factory=list)
    audit_records: list[str] = field(default_factory=list)


@dataclass
class NubExitPack:
    """FoT output pack passed to the next moment."""

    nub_sid: str
    state: FoTState
    output_buffers: list[Buffer]
    awareness_track: AwarenessTrack
    execution_track: ExecutionTrack
    updated_ledger_cursors: dict[str, LedgerCursor] = field(default_factory=dict)
    next_query_plan_seeds: dict[str, dict[str, Any]] = field(default_factory=dict)
    next_moment_refs: list[str] = field(default_factory=list)
    audit_records: list[str] = field(default_factory=list)
    hold_pack: HoldPack | None = None
    error_pack: ErrorPack | None = None


def ensure_input_event(value: InputEvent | dict[str, Any] | Any, source: str = "system") -> InputEvent:
    """Normalize arbitrary values into an ``InputEvent``."""
    if isinstance(value, InputEvent):
        return value

    if isinstance(value, dict):
        kind = str(value.get("kind") or value.get("type") or "input")
        return InputEvent(
            kind=kind,
            payload=value.get("payload", value),
            source=str(value.get("source") or source),
            timestamp=str(value.get("timestamp") or utcnow_iso()),
            sid=str(value.get("sid") or new_sid()),
        )

    return InputEvent(kind="input", payload=value, source=source)
