"""RFS (Recursive Feature Similarity) recall and multi-hop traversal.

This module implements advanced recall mechanisms that traverse the
connection graph between cards. Unlike simple keyword search, RFS
recall follows explicit relationships to find conceptually related
memories across multiple hops.

Key functions:
- ``rfs_recall``: Recursive recall with connection traversal
- ``attention_jump``: Jump to related cards via connections
- ``build_recall_chain``: Construct a chain of related memories
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from .abdb import ABMemory
from .models import Card


def attention_jump(
    memory: ABMemory,
    card_id: int,
    relation_filter: Optional[str] = None,
    direction: str = "outgoing",  # "outgoing", "incoming", or "both"
) -> List[Tuple[int, str, float]]:
    """Jump to related cards via connections.

    Args:
        memory: The AB memory instance.
        card_id: The source card to jump from.
        relation_filter: Optional filter for relation type (e.g., "references").
        direction: "outgoing" (source->target), "incoming" (target->source), or "both".

    Returns:
        List of tuples (target_card_id, relation, connection_strength).
    """
    connections = memory.list_connections(card_id=card_id)
    results: List[Tuple[int, str, float]] = []

    for conn in connections:
        source = conn["source_card_id"]
        target = conn["target_card_id"]
        relation = conn["relation"]
        strength = conn.get("strength", 1.0)

        if relation_filter and relation != relation_filter:
            continue

        if direction == "outgoing" and source == card_id:
            results.append((target, relation, strength))
        elif direction == "incoming" and target == card_id:
            results.append((source, relation, strength))
        elif direction == "both":
            if source == card_id:
                results.append((target, relation, strength))
            elif target == card_id:
                results.append((source, relation, strength))

    return results


def rfs_recall(
    memory: ABMemory,
    start_card_id: int,
    max_hops: int = 3,
    max_results: int = 10,
    relation_filter: Optional[str] = None,
    strengthen_path: bool = True,
) -> List[Tuple[Card, float, List[int]]]:
    """Recursive Feature Similarity recall with multi-hop traversal.

    Starting from a card, traverse connections to find related cards.
    Each hop accumulates a score based on connection strengths. The
    final score reflects the quality of the path from start to result.

    Args:
        memory: The AB memory instance.
        start_card_id: The card to start traversal from.
        max_hops: Maximum number of hops to traverse.
        max_results: Maximum number of results to return.
        relation_filter: Optional filter for relation types.
        strengthen_path: If True, strengthen connections along visited paths.

    Returns:
        List of tuples (card, score, path) where:
        - card: The found Card
        - score: Accumulated path score
        - path: List of card_ids in the path from start to this card
    """
    visited: Set[int] = {start_card_id}
    results: List[Tuple[int, float, List[int]]] = []

    # BFS with score accumulation
    # Queue items: (card_id, accumulated_score, path)
    queue: List[Tuple[int, float, List[int]]] = [(start_card_id, 1.0, [start_card_id])]

    while queue:
        current_id, current_score, path = queue.pop(0)

        if len(path) > 1:  # Don't include start card in results
            results.append((current_id, current_score, path))

        if len(path) <= max_hops:
            jumps = attention_jump(
                memory, current_id, relation_filter=relation_filter, direction="both"
            )
            for target_id, relation, strength in jumps:
                if target_id not in visited:
                    visited.add(target_id)
                    new_score = current_score * strength * 0.8  # Decay with each hop
                    new_path = path + [target_id]
                    queue.append((target_id, new_score, new_path))

                    if strengthen_path:
                        # Strengthen the connection we just traversed
                        _strengthen_connection_by_endpoints(
                            memory, current_id, target_id, delta=0.1
                        )

    # Sort by score and limit
    results.sort(key=lambda x: x[1], reverse=True)
    results = results[:max_results]

    # Fetch full cards and recall them
    final_results: List[Tuple[Card, float, List[int]]] = []
    for card_id, score, path in results:
        card = memory.get_card(card_id)
        memory.recall_card(card_id)  # Update memory physics
        final_results.append((card, score, path))

    return final_results


def build_recall_chain(
    memory: ABMemory,
    start_card_id: int,
    chain_length: int = 5,
    relation_filter: Optional[str] = None,
) -> List[Card]:
    """Build a linear chain of related memories.

    Starting from a card, follow the strongest connection at each
    step to build a chain of related cards.

    Args:
        memory: The AB memory instance.
        start_card_id: The card to start from.
        chain_length: Maximum length of the chain.
        relation_filter: Optional filter for relation types.

    Returns:
        List of Cards forming the chain (including start).
    """
    chain: List[Card] = []
    current_id = start_card_id
    visited: Set[int] = set()

    for _ in range(chain_length):
        if current_id in visited:
            break
        visited.add(current_id)

        card = memory.get_card(current_id)
        chain.append(card)

        # Find strongest outgoing connection
        jumps = attention_jump(
            memory, current_id, relation_filter=relation_filter, direction="outgoing"
        )
        if not jumps:
            break

        # Pick the strongest connection
        best_jump = max(jumps, key=lambda x: x[2])
        current_id = best_jump[0]

    return chain


def _strengthen_connection_by_endpoints(
    memory: ABMemory,
    source_id: int,
    target_id: int,
    delta: float = 0.1,
) -> None:
    """Strengthen a connection between two cards.

    Internal helper that finds the connection by endpoints and
    increments its strength.
    """
    cur = memory.conn.cursor()
    cur.execute(
        "UPDATE connections SET strength = strength + ? "
        "WHERE source_card_id = ? AND target_card_id = ?",
        (delta, source_id, target_id),
    )
    memory.conn.commit()


def get_connection_graph(
    memory: ABMemory,
    center_card_id: int,
    depth: int = 2,
) -> Dict[int, List[Tuple[int, str]]]:
    """Build a local connection graph around a card.

    Args:
        memory: The AB memory instance.
        center_card_id: The card at the center of the graph.
        depth: How many hops to include.

    Returns:
        Dict mapping card_id to list of (connected_card_id, relation).
    """
    graph: Dict[int, List[Tuple[int, str]]] = {}
    frontier: Set[int] = {center_card_id}
    visited: Set[int] = set()

    for _ in range(depth):
        next_frontier: Set[int] = set()
        for card_id in frontier:
            if card_id in visited:
                continue
            visited.add(card_id)

            jumps = attention_jump(memory, card_id, direction="both")
            graph[card_id] = [(j[0], j[1]) for j in jumps]

            for target_id, _, _ in jumps:
                if target_id not in visited:
                    next_frontier.add(target_id)

        frontier = next_frontier

    return graph
