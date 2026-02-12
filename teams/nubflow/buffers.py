"""Master buffer registry initialization and absorb/store helpers."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .types import Buffer, BufferStatus, InputEvent, LedgerCursor, new_sid

MASTER_BUFFER_DEFS: tuple[tuple[str, str], ...] = (
    ("master_input", "input"),
    ("sensory_input", "input"),
    ("exec_track_in", "track_in"),
    ("awareness_track_in", "track_in"),
    ("git_ledger", "ledger"),
    ("jira_ledger", "ledger"),
    ("notion_ledger", "ledger"),
    ("discord_ledger", "ledger"),
    ("web_ledger", "ledger"),
    ("overlord_inbox", "inbox"),
    ("overlord_outbox", "outbox"),
    ("output_overlord", "outbox"),
)

_LEDGER_BUFFER_NAMES = {
    "git": "git_ledger",
    "jira": "jira_ledger",
    "notion": "notion_ledger",
    "discord": "discord_ledger",
    "web": "web_ledger",
}


class MasterBufferRegistry:
    """Mutable in-memory registry of initialized master buffers."""

    def __init__(self, buffers: dict[str, Buffer]):
        self._buffers = buffers

    @classmethod
    def initialize(cls, ledger_registry: Any | None = None) -> MasterBufferRegistry:
        """Create the registry required by FoT before absorb."""
        buffers: dict[str, Buffer] = {}
        for name, kind in MASTER_BUFFER_DEFS:
            buffer = Buffer(name=name, kind=kind, payload=None, status=BufferStatus.PENDING)

            if kind == "ledger":
                ledger_kind = name.replace("_ledger", "").capitalize() + "Ledger"
                adapter = None
                if ledger_registry is not None:
                    adapter = ledger_registry.get(ledger_kind)
                if adapter is not None:
                    buffer.ledger_ref_sid = adapter.sid
                    buffer.cursor = LedgerCursor(ledger_sid=adapter.sid)

            buffers[name] = buffer

        return cls(buffers)

    def names(self) -> list[str]:
        return list(self._buffers.keys())

    def get(self, name: str) -> Buffer:
        return self._buffers[name]

    def has(self, name: str) -> bool:
        return name in self._buffers

    def set(self, name: str, buffer: Buffer) -> None:
        self._buffers[name] = buffer

    def clone(self, name: str, *, payload: Any, source: str, event_sid: str) -> Buffer:
        """Clone a registry buffer into an instance used for one route pass."""
        proto = self.get(name)
        clone = replace(
            proto,
            sid=new_sid(),
            payload=payload,
            status=BufferStatus.PENDING,
            error=None,
            provenance=[f"{source}:{event_sid}"],
            transforms=[],
            destination=None,
            metadata={"source": source, "event_sid": event_sid},
        )
        if clone.cursor is not None:
            clone.cursor = replace(clone.cursor)
        return clone

    def absorb_events(self, events: list[InputEvent]) -> list[Buffer]:
        """Normalize absorbed events into initialized route buffers."""
        routed: list[Buffer] = []
        for event in events:
            destination = self._route_name_for_event(event)
            routed.append(
                self.clone(
                    destination,
                    payload=event.payload,
                    source=event.source,
                    event_sid=event.sid,
                )
            )
        return routed

    def update_ledger_cursor(self, buffer_name: str, cursor: LedgerCursor) -> None:
        if buffer_name not in self._buffers:
            return
        if self._buffers[buffer_name].kind != "ledger":
            return
        self._buffers[buffer_name].cursor = cursor

    def ledger_cursors(self) -> dict[str, LedgerCursor]:
        cursors: dict[str, LedgerCursor] = {}
        for name, buffer in self._buffers.items():
            if buffer.kind == "ledger" and buffer.cursor is not None:
                cursors[name] = replace(buffer.cursor)
        return cursors

    def _route_name_for_event(self, event: InputEvent) -> str:
        source = event.source.lower()
        if source in _LEDGER_BUFFER_NAMES:
            return _LEDGER_BUFFER_NAMES[source]

        if isinstance(event.payload, dict):
            ledger_hint = str(event.payload.get("ledger_kind", "")).lower()
            if ledger_hint in _LEDGER_BUFFER_NAMES:
                return _LEDGER_BUFFER_NAMES[ledger_hint]

        kind = event.kind.lower()
        if kind in {"sensory", "screenshot", "vision", "image", "audio"}:
            return "sensory_input"
        if kind in {"exec_track", "execution_track"}:
            return "exec_track_in"
        if kind in {"awareness_track"}:
            return "awareness_track_in"

        return "master_input"
