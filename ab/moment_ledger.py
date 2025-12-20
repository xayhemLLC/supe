"""Advanced timeline and moment ledger queries.

This module provides higher-level functions to query and aggregate
moments stored in the AB memory database. Moments are the backbone
of the AB ledger: each card belongs to a moment, and moments are
ordered in time.  The functions here allow callers to retrieve
moments within a time range, paginate through them, and group
moments by calendar intervals.

All operations are read-only and do not modify the underlying
database.  They rely on the ``ABMemory`` instance passed by the
caller and use standard SQLite queries to fetch data.

Example usage::

    from ab.abdb import ABMemory
    from ab.moment_ledger import get_moments_between, group_moments_by_day

    mem = ABMemory()
    moments = get_moments_between(mem, "2025-01-01T00:00:00", "2025-01-31T23:59:59")
    groups = group_moments_by_day(mem)

Note: timestamps are ISO-8601 strings.  No timezone handling is
performed; callers should normalise timestamps as desired.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .abdb import ABMemory
from .models import Moment


def _parse_iso(ts: str) -> datetime:
    """Parse an ISO-8601 timestamp into a naive datetime object."""
    return datetime.fromisoformat(ts)


def get_moments_between(
    memory: ABMemory,
    start_ts: str,
    end_ts: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Moment]:
    """Return moments with timestamps between ``start_ts`` and ``end_ts``.

    Args:
        memory: The ``ABMemory`` instance.
        start_ts: Start of the range (inclusive) as ISO-8601 string.
        end_ts: End of the range (inclusive) as ISO-8601 string.
        limit: Optional maximum number of moments to return.
        offset: Optional offset for pagination.

    Returns:
        A list of ``Moment`` objects ordered by timestamp ascending.
    """
    cur = memory.conn.cursor()
    query = "SELECT id, timestamp FROM moments WHERE timestamp >= ? AND timestamp <= ? ORDER BY timestamp ASC"
    params: List[object] = [start_ts, end_ts]
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)
    elif offset is not None:
        # Offset only makes sense with limit; ignore if limit is None
        pass
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    return [Moment(id=row["id"], timestamp=row["timestamp"]) for row in rows]


def paginate_moments(memory: ABMemory, page: int = 0, page_size: int = 50) -> Tuple[List[Moment], int]:
    """Return a page of moments along with total count.

    Args:
        memory: The ``ABMemory`` instance.
        page: Zero-based page index.
        page_size: Number of moments per page.

    Returns:
        A tuple ``(moments, total_count)`` where ``moments`` is a list
        of ``Moment`` objects for the requested page and ``total_count``
        is the total number of moments in the database.
    """
    cur = memory.conn.cursor()
    # Total count
    cur.execute("SELECT COUNT(*) as cnt FROM moments")
    total_count = cur.fetchone()["cnt"]
    offset = page * page_size
    cur.execute(
        "SELECT id, timestamp FROM moments ORDER BY timestamp ASC LIMIT ? OFFSET ?",
        (page_size, offset),
    )
    rows = cur.fetchall()
    moments = [Moment(id=row["id"], timestamp=row["timestamp"]) for row in rows]
    return moments, total_count


def group_moments_by_day(memory: ABMemory) -> Dict[str, List[Moment]]:
    """Group all moments by calendar day (YYYY-MM-DD).

    Returns a dictionary mapping date strings to lists of moments
    occurring on that day.  Moments are ordered by timestamp.
    """
    cur = memory.conn.cursor()
    cur.execute("SELECT id, timestamp FROM moments ORDER BY timestamp ASC")
    rows = cur.fetchall()
    groups: Dict[str, List[Moment]] = defaultdict(list)
    for row in rows:
        dt = _parse_iso(row["timestamp"])
        key = dt.date().isoformat()
        groups[key].append(Moment(id=row["id"], timestamp=row["timestamp"]))
    return groups


def group_moments_by_week(memory: ABMemory) -> Dict[str, List[Moment]]:
    """Group all moments by ISO week (YYYY-Www)."""
    cur = memory.conn.cursor()
    cur.execute("SELECT id, timestamp FROM moments ORDER BY timestamp ASC")
    rows = cur.fetchall()
    groups: Dict[str, List[Moment]] = defaultdict(list)
    for row in rows:
        dt = _parse_iso(row["timestamp"])
        year, week, _ = dt.isocalendar()
        key = f"{year}-W{week:02d}"
        groups[key].append(Moment(id=row["id"], timestamp=row["timestamp"]))
    return groups