"""Storage layer for typed semantic relations in AB Memory.

This module provides high-level functions for storing and querying
typed relations between cards. It bridges between the Relation
dataclass (tasc/relations.py) and the ABMemory database layer.
"""

from typing import List, Optional
from ab.abdb import ABMemory
from tasc.relations import Relation, RelationType


def store_relation(memory: ABMemory, relation: Relation) -> None:
    """Store a relation in AB Memory.

    Args:
        memory: ABMemory instance
        relation: Relation object to store
    """
    memory.add_relation(
        relation_id=relation.id,
        relation_type=relation.type.value,
        source_card_id=relation.source_card_id,
        target_card_id=relation.target_card_id,
        confidence=relation.confidence,
        metadata=relation.metadata,
    )


def get_relations_from_card(
    memory: ABMemory,
    card_id: int,
    relation_type: Optional[RelationType] = None,
) -> List[Relation]:
    """Get all relations where the specified card is the source.

    Args:
        memory: ABMemory instance
        card_id: Source card ID
        relation_type: Optional filter by relation type

    Returns:
        List of Relation objects
    """
    type_str = relation_type.value if relation_type else None
    rows = memory.get_relations(source_card_id=card_id, relation_type=type_str)
    return [_row_to_relation(row) for row in rows]


def get_relations_to_card(
    memory: ABMemory,
    card_id: int,
    relation_type: Optional[RelationType] = None,
) -> List[Relation]:
    """Get all relations where the specified card is the target.

    Args:
        memory: ABMemory instance
        card_id: Target card ID
        relation_type: Optional filter by relation type

    Returns:
        List of Relation objects
    """
    type_str = relation_type.value if relation_type else None
    rows = memory.get_inverse_relations(card_id=card_id, relation_type=type_str)
    return [_row_to_relation(row) for row in rows]


def get_relation_by_id(memory: ABMemory, relation_id: str) -> Optional[Relation]:
    """Get a specific relation by ID.

    Args:
        memory: ABMemory instance
        relation_id: Relation ID

    Returns:
        Relation object or None if not found
    """
    row = memory.get_relation_by_id(relation_id)
    return _row_to_relation(row) if row else None


def delete_relation(memory: ABMemory, relation_id: str) -> None:
    """Delete a relation by ID.

    Args:
        memory: ABMemory instance
        relation_id: Relation ID to delete
    """
    memory.delete_relation(relation_id)


def count_relations(
    memory: ABMemory,
    source_card_id: Optional[int] = None,
    target_card_id: Optional[int] = None,
    relation_type: Optional[RelationType] = None,
) -> int:
    """Count relations matching the specified filters.

    Args:
        memory: ABMemory instance
        source_card_id: Optional filter by source card
        target_card_id: Optional filter by target card
        relation_type: Optional filter by relation type

    Returns:
        Number of matching relations
    """
    type_str = relation_type.value if relation_type else None
    return memory.count_relations(
        source_card_id=source_card_id,
        target_card_id=target_card_id,
        relation_type=type_str,
    )


def get_causal_chain(
    memory: ABMemory,
    start_card_id: int,
    max_depth: int = 10,
) -> List[Relation]:
    """Trace a causal chain backwards from a card.

    Follows CAUSES relations backwards to find root causes.

    Args:
        memory: ABMemory instance
        start_card_id: Starting card ID
        max_depth: Maximum chain length to trace

    Returns:
        List of CAUSES relations forming the chain
    """
    chain = []
    current_id = start_card_id
    depth = 0

    while depth < max_depth:
        # Find relations where current card is the target
        relations = get_relations_to_card(memory, current_id, RelationType.CAUSES)

        if not relations:
            break

        # Take the highest confidence relation
        relation = max(relations, key=lambda r: r.confidence)
        chain.append(relation)

        # Move to the source card
        current_id = relation.source_card_id
        depth += 1

    return chain


def get_support_network(
    memory: ABMemory,
    belief_card_id: int,
) -> List[Relation]:
    """Get all evidence supporting a belief.

    Args:
        memory: ABMemory instance
        belief_card_id: Card ID of the belief being supported

    Returns:
        List of SUPPORTS relations
    """
    return get_relations_to_card(memory, belief_card_id, RelationType.SUPPORTS)


def calculate_support_strength(
    memory: ABMemory,
    belief_card_id: int,
) -> float:
    """Calculate overall support strength for a belief.

    Aggregates confidence from all SUPPORTS relations.

    Args:
        memory: ABMemory instance
        belief_card_id: Card ID of the belief

    Returns:
        Average confidence across all supporting evidence (0.0-1.0)
    """
    support_relations = get_support_network(memory, belief_card_id)

    if not support_relations:
        return 0.0

    total_confidence = sum(r.confidence for r in support_relations)
    avg_confidence = total_confidence / len(support_relations)

    # Bonus for having multiple diverse sources
    if len(support_relations) >= 3:
        avg_confidence = min(1.0, avg_confidence * 1.1)

    return avg_confidence


def find_contradictions(
    memory: ABMemory,
    card_id: int,
) -> List[Relation]:
    """Find all contradictions involving a specific card.

    Args:
        memory: ABMemory instance
        card_id: Card ID to check for contradictions

    Returns:
        List of CONTRADICTS relations
    """
    # Get contradictions where this card is source or target
    as_source = get_relations_from_card(memory, card_id, RelationType.CONTRADICTS)
    as_target = get_relations_to_card(memory, card_id, RelationType.CONTRADICTS)

    # Combine and deduplicate (contradictions are symmetric)
    all_contradictions = as_source + as_target
    seen_pairs = set()
    unique_contradictions = []

    for rel in all_contradictions:
        pair = tuple(sorted([rel.source_card_id, rel.target_card_id]))
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            unique_contradictions.append(rel)

    return unique_contradictions


def get_dependencies(
    memory: ABMemory,
    task_card_id: int,
) -> List[Relation]:
    """Get all dependencies for a task.

    Args:
        memory: ABMemory instance
        task_card_id: Card ID of the task

    Returns:
        List of DEPENDS_ON relations where this task is the source
    """
    return get_relations_from_card(memory, task_card_id, RelationType.DEPENDS_ON)


def check_dependencies_satisfied(
    memory: ABMemory,
    task_card_id: int,
    completed_card_ids: List[int],
) -> bool:
    """Check if all dependencies for a task are satisfied.

    Args:
        memory: ABMemory instance
        task_card_id: Card ID of the task
        completed_card_ids: List of completed task card IDs

    Returns:
        True if all dependencies are in completed list
    """
    dependencies = get_dependencies(memory, task_card_id)

    for dep in dependencies:
        if dep.target_card_id not in completed_card_ids:
            return False

    return True


def topological_sort_tasks(
    memory: ABMemory,
    task_card_ids: List[int],
) -> List[int]:
    """Sort tasks by dependencies using topological sort.

    Args:
        memory: ABMemory instance
        task_card_ids: List of task card IDs to sort

    Returns:
        List of card IDs in execution order

    Raises:
        ValueError: If there's a circular dependency
    """
    # Build adjacency list and in-degree counts
    in_degree = {card_id: 0 for card_id in task_card_ids}
    adj_list = {card_id: [] for card_id in task_card_ids}

    for card_id in task_card_ids:
        deps = get_dependencies(memory, card_id)
        for dep in deps:
            if dep.target_card_id in task_card_ids:
                adj_list[dep.target_card_id].append(card_id)
                in_degree[card_id] += 1

    # Kahn's algorithm for topological sort
    queue = [card_id for card_id in task_card_ids if in_degree[card_id] == 0]
    result = []

    while queue:
        current = queue.pop(0)
        result.append(current)

        for neighbor in adj_list[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(task_card_ids):
        raise ValueError("Circular dependency detected in task graph")

    return result


def get_evolution_chain(
    memory: ABMemory,
    start_card_id: int,
    max_depth: int = 10,
) -> List[Relation]:
    """Trace knowledge evolution through TRANSFORMS relations.

    Args:
        memory: ABMemory instance
        start_card_id: Starting card ID
        max_depth: Maximum chain length to trace

    Returns:
        List of TRANSFORMS relations showing evolution
    """
    chain = []
    current_id = start_card_id
    depth = 0

    while depth < max_depth:
        # Find what this card transformed into
        relations = get_relations_from_card(memory, current_id, RelationType.TRANSFORMS)

        if not relations:
            break

        # Take the most recent transformation
        relation = max(relations, key=lambda r: r.created_at)
        chain.append(relation)

        # Move to the target card
        current_id = relation.target_card_id
        depth += 1

    return chain


# Helper functions

def _row_to_relation(row: dict) -> Relation:
    """Convert database row to Relation object.

    Args:
        row: Database row dictionary

    Returns:
        Relation object
    """
    return Relation(
        id=row["id"],
        type=RelationType(row["type"]),
        source_card_id=row["source_card_id"],
        target_card_id=row["target_card_id"],
        confidence=row["confidence"],
        metadata=row["metadata"],
        created_at=row["created_at"],
    )


# Integration with evidence-based validation

def create_support_relations_from_evidence(
    memory: ABMemory,
    evidence_card_ids: List[int],
    belief_card_id: int,
    relation_id_prefix: str,
) -> List[Relation]:
    """Automatically create SUPPORTS relations from evidence to belief.

    This is the integration point between evidence-based validation
    and the relation system.

    Args:
        memory: ABMemory instance
        evidence_card_ids: List of evidence card IDs
        belief_card_id: Belief card ID being supported
        relation_id_prefix: Prefix for relation IDs

    Returns:
        List of created SUPPORTS relations
    """
    from tasc.relations import create_support_network

    relations = create_support_network(
        evidence_card_ids=evidence_card_ids,
        belief_card_id=belief_card_id,
        relation_id_prefix=relation_id_prefix,
    )

    # Store all relations
    for relation in relations:
        store_relation(memory, relation)

    return relations


def create_causal_relation_from_validation(
    memory: ABMemory,
    root_cause_card_id: int,
    bug_card_id: int,
    confidence: float = 0.95,
) -> Relation:
    """Create a CAUSES relation from debugging validation.

    Args:
        memory: ABMemory instance
        root_cause_card_id: Card ID of root cause
        bug_card_id: Card ID of bug report
        confidence: Confidence in causal relationship

    Returns:
        Created CAUSES relation
    """
    from tasc.relations import Relation, RelationType
    import uuid

    relation = Relation.create(
        relation_id=f"causes_{uuid.uuid4().hex[:8]}",
        relation_type=RelationType.CAUSES,
        source_card_id=root_cause_card_id,
        target_card_id=bug_card_id,
        confidence=confidence,
        metadata={"source": "debugging_validation"},
    )

    store_relation(memory, relation)
    return relation
