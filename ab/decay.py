"""Decay utilities for memory physics.

This module provides functions for applying time-based decay to card
strengths. Decay ensures that cards which are not recalled fade in
importance over time, mimicking natural memory degradation.

The primary function ``apply_decay_to_all`` calculates decay based on
the time elapsed since each card was last recalled and applies a
configurable decay formula.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from .abdb import ABMemory


def parse_iso(ts: str) -> datetime:
    """Parse an ISO-8601 timestamp string to datetime."""
    return datetime.fromisoformat(ts)


def decay_formula(
    current_strength: float,
    hours_since_recall: float,
    half_life_hours: float = 168.0,  # 1 week default
) -> float:
    """Calculate decayed strength based on time elapsed.

    Uses exponential decay: strength * (0.5 ^ (hours / half_life))

    Args:
        current_strength: The card's current strength.
        hours_since_recall: Hours since the card was last recalled.
        half_life_hours: Hours for strength to decay to half (default: 168 = 1 week).

    Returns:
        The new strength after decay.
    """
    if hours_since_recall <= 0:
        return current_strength
    decay_factor = 0.5 ** (hours_since_recall / half_life_hours)
    return current_strength * decay_factor


def apply_decay_to_all(
    memory: ABMemory,
    reference_time: Optional[datetime] = None,
    half_life_hours: float = 168.0,
    min_strength: float = 0.01,
) -> int:
    """Apply time-based decay to all cards based on last recall time.

    Cards that have never been recalled are not decayed (they keep their
    initial strength). Cards that were recalled long ago will have their
    strength significantly reduced.

    Args:
        memory: The AB memory instance.
        reference_time: The current time to calculate decay from.
            Defaults to UTC now.
        half_life_hours: Hours for strength to decay to half.
        min_strength: Minimum strength floor (cards won't go below this).

    Returns:
        Number of cards that were decayed.
    """
    if reference_time is None:
        reference_time = datetime.utcnow()

    cur = memory.conn.cursor()
    cur.execute("SELECT card_id, strength, last_recalled FROM card_stats WHERE last_recalled IS NOT NULL")
    rows = cur.fetchall()

    decayed_count = 0
    for row in rows:
        last_recalled = parse_iso(row["last_recalled"])
        hours_elapsed = (reference_time - last_recalled).total_seconds() / 3600.0
        new_strength = decay_formula(row["strength"], hours_elapsed, half_life_hours)
        new_strength = max(new_strength, min_strength)

        if new_strength != row["strength"]:
            cur.execute(
                "UPDATE card_stats SET strength = ? WHERE card_id = ?",
                (new_strength, row["card_id"]),
            )
            decayed_count += 1

    memory.conn.commit()
    return decayed_count


def get_stale_cards(
    memory: ABMemory,
    days_threshold: int = 7,
    reference_time: Optional[datetime] = None,
) -> list:
    """Find cards that haven't been recalled in a while.

    Args:
        memory: The AB memory instance.
        days_threshold: Number of days without recall to be considered stale.
        reference_time: Current time reference (defaults to UTC now).

    Returns:
        List of card_ids that are stale.
    """
    if reference_time is None:
        reference_time = datetime.utcnow()

    threshold_time = reference_time - timedelta(days=days_threshold)
    threshold_str = threshold_time.isoformat()

    cur = memory.conn.cursor()
    cur.execute(
        "SELECT card_id FROM card_stats WHERE last_recalled < ? OR last_recalled IS NULL",
        (threshold_str,),
    )
    return [row["card_id"] for row in cur.fetchall()]
