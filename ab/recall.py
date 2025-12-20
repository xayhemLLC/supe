"""Recall and memory traversal utilities for AB.

This module implements a basic recall mechanism for AB memory. Given
the current master input (a query string), ``recall_cards`` searches
for relevant cards and optionally uses explicit connections to rank
cards by relevance.  Connections are strengthened when they are
traversed, allowing frequently recalled paths to become stronger over
time.

The implementation integrates with the card_stats system to:
- Use existing card strength as a base score
- Update memory physics (strength, recall_count) when cards are accessed
- Strengthen connections along traversed paths
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .abdb import ABMemory
from .models import Card
from .search import search_cards


def recall_cards(
    memory: ABMemory,
    query: str,
    start_card_id: Optional[int] = None,
    top_k: int = 5,
    strengthen: bool = True,
    use_card_stats: bool = True,
) -> List[Tuple[Card, float]]:
    """Recall cards relevant to the query and starting card.

    Args:
        memory: The AB memory instance.
        query: Keyword used to search for relevant cards in payloads
            and headers.  The search is case-insensitive.
        start_card_id: Optional ID of a card representing the current
            context.  If provided, the recall score of candidate cards
            will be adjusted based on the number and strength of
            connections from this card.
        top_k: Maximum number of cards to return.
        strengthen: If ``True``, increment the strength of any
            traversed connections.  Strengthening occurs only for
            connections from ``start_card_id`` to the returned cards.
        use_card_stats: If ``True``, incorporate card strength from
            card_stats into the scoring.

    Returns:
        A list of tuples ``(card, score)`` sorted by descending score.
    """
    # First, search for candidate cards containing the query
    candidates = search_cards(memory, keyword=query)

    # Compute scores incorporating card_stats strength
    scored: List[Tuple[Card, float]] = []
    for card in candidates:
        # Base score from card_stats if enabled
        if use_card_stats and card.id is not None:
            stats = memory.get_card_stats(card.id)
            score = stats.strength
        else:
            score = 1.0

        # Adjust based on connections from start_card_id
        if start_card_id is not None and card.id is not None:
            conns = memory.list_connections(card_id=start_card_id)
            total_strength = 0.0
            for c in conns:
                if c["target_card_id"] == card.id:
                    total_strength += c.get("strength", 1.0)
                    if strengthen:
                        _increment_connection_strength(memory, c["id"], 0.5)
            # Add connection strength to score
            score += total_strength

        scored.append((card, score))

    # Sort by score descending and limit
    scored.sort(key=lambda x: x[1], reverse=True)
    top_results = scored[:top_k]

    # Update memory physics for returned cards
    for card, _ in top_results:
        if card.id is not None:
            memory.recall_card(card.id)

    return top_results


def _increment_connection_strength(memory: ABMemory, conn_id: int, delta: float) -> None:
    """Internal helper to increment the strength of a connection."""
    cur = memory.conn.cursor()
    cur.execute("UPDATE connections SET strength = strength + ? WHERE id = ?", (delta, conn_id))
    memory.conn.commit()