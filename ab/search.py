"""Search utilities for AB memory.

This module implements a simple search mechanism over the AB
memory system.  It allows callers to search for cards by label,
header or payload content and filter by time range or owner.

Note: this is a basic implementation intended as a starting point.
Future enhancements may include vector similarity search, recall
ranking, tree traversal along connections, and integration with
memory strength/decay metrics.
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional, Tuple

from .abdb import ABMemory
from .models import Card


def _payload_to_text(payload: bytes) -> str:
    """Attempt to decode bytes to UTF-8 text; fallback to repr."""
    try:
        return payload.decode("utf-8", errors="ignore")
    except Exception:
        return repr(payload)


def search_cards(
    memory: ABMemory,
    keyword: Optional[str] = None,
    label: Optional[str] = None,
    owner: Optional[str] = None,
    start_ts: Optional[str] = None,
    end_ts: Optional[str] = None,
) -> List[Card]:
    """Search cards by keyword, label, owner and time range.

    Args:
        memory: The ``ABMemory`` instance.
        keyword: If provided, search in buffer payloads and headers for
            this string (case-insensitive).
        label: If provided, restrict results to cards with this label.
        owner: If provided, restrict results to cards whose
            ``owner_self`` matches this string.
        start_ts: If provided, only include cards whose moment
            timestamps are >= this value.
        end_ts: If provided, only include cards whose moment
            timestamps are <= this value.

    Returns:
        A list of ``Card`` objects matching the filters.
    """
    cur = memory.conn.cursor()
    # Build base query joining cards to moments
    query = "SELECT cards.id FROM cards JOIN moments ON cards.moment_id = moments.id"
    conditions: List[str] = []
    params: List[object] = []
    if label is not None:
        conditions.append("cards.label = ?")
        params.append(label)
    if owner is not None:
        conditions.append("cards.owner_self = ?")
        params.append(owner)
    if start_ts is not None:
        conditions.append("moments.timestamp >= ?")
        params.append(start_ts)
    if end_ts is not None:
        conditions.append("moments.timestamp <= ?")
        params.append(end_ts)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY moments.timestamp ASC"
    cur.execute(query, tuple(params))
    card_ids = [row["id"] for row in cur.fetchall()]
    # Retrieve cards and filter by keyword
    results: List[Card] = []
    for cid in card_ids:
        card = memory.get_card(cid)
        include = True
        if keyword:
            kw = keyword.lower()
            # Search in label
            if kw in card.label.lower():
                pass
            else:
                match = False
                for buf in card.buffers:
                    # Search in headers
                    for k, v in buf.headers.items():
                        if kw in str(k).lower() or kw in str(v).lower():
                            match = True
                            break
                    if match:
                        break
                    # Search in payload text
                    text = _payload_to_text(buf.payload).lower()
                    if kw in text:
                        match = True
                        break
                include = match
        if include:
            results.append(card)
    return results


def search_payload_keyword(memory: ABMemory, keyword: str) -> List[Tuple[int, str]]:
    """Return (card_id, buffer_name) pairs where payload contains the keyword."""
    kw = keyword.lower()
    cur = memory.conn.cursor()
    # Fetch all cards and buffers (could be optimised)
    cur.execute("SELECT id FROM cards")
    ids = [row["id"] for row in cur.fetchall()]
    matches: List[Tuple[int, str]] = []
    for cid in ids:
        card = memory.get_card(cid)
        for buf in card.buffers:
            text = _payload_to_text(buf.payload).lower()
            if kw in text:
                matches.append((cid, buf.name))
    return matches