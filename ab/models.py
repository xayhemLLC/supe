"""Data classes for core AB entities: Moment, Card and Buffer.

These classes provide a Python representation of the fundamental
structures used by the AB memory engine. They are deliberately
lightweight and are not tied to any particular storage backend. The
``ABMemory`` class in ``ab.abdb`` handles persistence.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Buffer:
    """A functional conduit for storing named payloads.

    ``Buffer`` corresponds closely to the definition in the AB FAQ: it
    has a name, optional headers (metadata), a payload (raw bytes) and
    an optional ``exe`` transformation identifier. The headers can be
    any serialisable dictionary; they are stored as JSON in the
    database.
    """

    name: str
    headers: dict[str, Any] = field(default_factory=dict)
    payload: bytes = b""
    exe: str | None = None


@dataclass
class Moment:
    """A single tick in time used as the backbone of the AB ledger."""

    id: int | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None).isoformat())
    # Each moment records the aggregate input and output of the cognitive pulse.
    # ``master_input`` captures the primary prompt or context that initiated
    # this moment, and ``master_output`` stores the final integrated output
    # produced by the Overlord after all subselves have emitted proposals.
    master_input: str | None = None
    master_output: str | None = None
    # Every moment also references an ``awareness_card`` capturing raw
    # inputs (prompt, state, files, etc.) fused into a single card.  The
    # awareness card ID is stored here for quick lookup.
    awareness_card_id: int | None = None
    # ID of the master card containing raw sensory and internal state
    # data for this moment.  Each moment has exactly one master card
    # capturing the hardware inputs prior to awareness fusion.  The
    # master card can be ``None`` when hardware is disabled.
    master_card_id: int | None = None


@dataclass
class Card:
    """Primary memory unit storing buffers with a label and metadata."""

    id: int | None = None
    label: str = ""
    moment_id: int | None = None
    owner_self: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None).isoformat())
    buffers: list[Buffer] = field(default_factory=list)
    # A card has exactly one ``master_input`` and one ``master_output``.  They
    # capture the primary input the card operates on and the result it
    # produces.  For many cards (e.g., content cards or awareness cards)
    # these fields may be ``None``.
    master_input: str | None = None
    master_output: str | None = None
    # Memory track: 'awareness' (knowledge/content), 'execution' (tasc history),
    # or 'sensory' (raw input data). Defaults to 'awareness'.
    track: str = "awareness"


@dataclass
class CardStats:
    """Memory physics statistics for a card.

    Tracks the strength, recall count, and last recall time for each card.
    These statistics influence search ranking and decision-making:

    - ``strength``: Accumulated strength from recalls (higher = more dominant)
    - ``recall_count``: Number of times the card has been recalled
    - ``last_recalled``: Timestamp of the most recent recall

    The strength formula on recall is: ``strength = strength * 0.9 + 1.0``
    """

    card_id: int
    strength: float = 1.0
    recall_count: int = 0
    last_recalled: str | None = None
