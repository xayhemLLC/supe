"""Typed relations between cards in AB Memory.

This module defines typed semantic relationships between cards, enabling
sophisticated reasoning capabilities including:
- Causal reasoning (CAUSES)
- Logical inference (IMPLIES)
- Contradiction detection (CONTRADICTS)
- Evidence support (SUPPORTS)
- Task dependencies (DEPENDS_ON)

Relations are Atom-serializable (pindex=12), maintaining architectural consistency.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
import json

from tasc.atom import Atom


class RelationType(Enum):
    """Types of semantic relations between cards.

    Each relation type has specific semantics and properties:

    CAUSES: Causal relationship (A caused B)
        Properties: Transitive, time-ordered, asymmetric
        Example: code_change CAUSES bug

    IMPLIES: Logical implication (If A then B)
        Properties: Transitive, logical, asymmetric
        Example: requirement IMPLIES design_decision

    CONTRADICTS: Logical contradiction (A and B conflict)
        Properties: Symmetric, triggers review
        Example: measurement CONTRADICTS belief

    SUPPORTS: Evidential support (A supports B)
        Properties: Weighted, asymmetric, aggregatable
        Example: experiment SUPPORTS hypothesis

    DEPENDS_ON: Prerequisite dependency (B requires A)
        Properties: Creates ordering, transitive
        Example: deploy DEPENDS_ON tests_pass

    EQUALS: Equivalence (A same as B)
        Properties: Symmetric, transitive, reflexive
        Example: concept EQUALS synonym

    TRANSFORMS: State evolution (A evolved to B)
        Properties: Time-ordered, tracks history
        Example: hypothesis_v1 TRANSFORMS hypothesis_v2

    REFINES: Detail addition (B adds detail to A)
        Properties: Hierarchical, transitive
        Example: general_idea REFINES specific_implementation

    INVALIDATES: Obsolescence (B makes A obsolete)
        Properties: Time-ordered, asymmetric
        Example: new_fix INVALIDATES old_hypothesis

    GENERALIZES: Abstraction (B generalizes A)
        Properties: Hierarchical, inverse of REFINES
        Example: pattern GENERALIZES specific_instance
    """
    CAUSES = "causes"
    IMPLIES = "implies"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    DEPENDS_ON = "depends_on"
    EQUALS = "equals"
    TRANSFORMS = "transforms"
    REFINES = "refines"
    INVALIDATES = "invalidates"
    GENERALIZES = "generalizes"


@dataclass
class Relation:
    """A typed semantic relation between two cards.

    Relations are directional (source → target) except for symmetric types
    (CONTRADICTS, EQUALS) where direction is arbitrary.

    Attributes:
        id: Unique identifier for this relation
        type: Type of relation (see RelationType for semantics)
        source_card_id: Card ID that is the source of the relation
        target_card_id: Card ID that is the target of the relation
        confidence: Confidence in this relation (0.0-1.0)
        metadata: Additional context (reason, detected_at, etc.)
        created_at: Timestamp when relation was created (milliseconds)

    Example:
        # Evidence supports belief
        Relation(
            id="rel_001",
            type=RelationType.SUPPORTS,
            source_card_id=123,  # Evidence card
            target_card_id=456,  # Belief card
            confidence=0.95,
            metadata={"source": "experiment", "validated": True}
        )
    """
    id: str
    type: RelationType
    source_card_id: int
    target_card_id: int
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "source_card_id": self.source_card_id,
            "target_card_id": self.target_card_id,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relation":
        """Create Relation from dictionary."""
        return cls(
            id=data["id"],
            type=RelationType(data["type"]),
            source_card_id=data["source_card_id"],
            target_card_id=data["target_card_id"],
            confidence=data.get("confidence", 1.0),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", int(datetime.now().timestamp() * 1000)),
        )

    def to_atom(self) -> Atom:
        """Encode as Atom of type 'relation' (pindex=12).

        Returns:
            Atom containing serialized relation data
        """
        payload = json.dumps(self.to_dict()).encode('utf-8')
        return Atom(pindex=12, payload=payload)

    @classmethod
    def from_atom(cls, atom: Atom) -> "Relation":
        """Decode Relation from Atom.

        Args:
            atom: Atom with pindex=12 (relation type)

        Returns:
            Relation instance

        Raises:
            ValueError: If atom is not a relation type
        """
        if atom.pindex != 12:
            raise ValueError(f"Expected relation atom (pindex=12), got pindex={atom.pindex}")

        data = json.loads(atom.payload.decode('utf-8'))
        return cls.from_dict(data)

    @classmethod
    def create(
        cls,
        relation_id: str,
        relation_type: RelationType,
        source_card_id: int,
        target_card_id: int,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Relation":
        """Factory method for creating relations.

        Args:
            relation_id: Unique identifier
            relation_type: Type of relation
            source_card_id: Source card ID
            target_card_id: Target card ID
            confidence: Confidence score (0.0-1.0)
            metadata: Additional context

        Returns:
            New Relation instance
        """
        return cls(
            id=relation_id,
            type=relation_type,
            source_card_id=source_card_id,
            target_card_id=target_card_id,
            confidence=confidence,
            metadata=metadata or {},
        )

    def is_symmetric(self) -> bool:
        """Check if this relation type is symmetric.

        Symmetric relations: CONTRADICTS, EQUALS
        """
        return self.type in (RelationType.CONTRADICTS, RelationType.EQUALS)

    def is_transitive(self) -> bool:
        """Check if this relation type is transitive.

        Transitive relations: CAUSES, IMPLIES, EQUALS, DEPENDS_ON, REFINES, GENERALIZES
        """
        return self.type in (
            RelationType.CAUSES,
            RelationType.IMPLIES,
            RelationType.EQUALS,
            RelationType.DEPENDS_ON,
            RelationType.REFINES,
            RelationType.GENERALIZES,
        )

    def get_inverse_type(self) -> Optional[RelationType]:
        """Get the inverse relation type if it exists.

        Returns:
            Inverse RelationType or None if no natural inverse
        """
        inverses = {
            RelationType.REFINES: RelationType.GENERALIZES,
            RelationType.GENERALIZES: RelationType.REFINES,
        }
        return inverses.get(self.type)

    def __repr__(self) -> str:
        """Human-readable representation."""
        return (
            f"Relation({self.source_card_id} --{self.type.value}-> "
            f"{self.target_card_id}, conf={self.confidence:.2f})"
        )


@dataclass
class RelationCollection:
    """A collection of related relations for a specific context.

    Used for grouping relations that belong together (e.g., all relations
    created during a single validation, all support relations for a belief).

    Attributes:
        id: Unique identifier for this collection
        description: Human-readable description
        relations: List of Relation objects in this collection
        metadata: Additional context
        created_at: Timestamp when collection was created
    """
    id: str
    description: str
    relations: List[Relation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))

    def add_relation(self, relation: Relation) -> None:
        """Add a relation to this collection."""
        self.relations.append(relation)

    def get_by_type(self, relation_type: RelationType) -> List[Relation]:
        """Get all relations of a specific type."""
        return [r for r in self.relations if r.type == relation_type]

    def get_by_source(self, card_id: int) -> List[Relation]:
        """Get all relations with this card as source."""
        return [r for r in self.relations if r.source_card_id == card_id]

    def get_by_target(self, card_id: int) -> List[Relation]:
        """Get all relations with this card as target."""
        return [r for r in self.relations if r.target_card_id == card_id]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "description": self.description,
            "relations": [r.to_dict() for r in self.relations],
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RelationCollection":
        """Create RelationCollection from dictionary."""
        return cls(
            id=data["id"],
            description=data["description"],
            relations=[Relation.from_dict(r) for r in data.get("relations", [])],
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", int(datetime.now().timestamp() * 1000)),
        )

    @classmethod
    def create(
        cls,
        collection_id: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "RelationCollection":
        """Factory method for creating collections.

        Args:
            collection_id: Unique identifier
            description: Human-readable description
            metadata: Additional context

        Returns:
            New RelationCollection instance
        """
        return cls(
            id=collection_id,
            description=description,
            metadata=metadata or {},
        )

    def __repr__(self) -> str:
        """Human-readable representation."""
        return f"RelationCollection(id={self.id}, {len(self.relations)} relations)"


# Helper functions for common relation patterns

def create_causal_chain(
    card_ids: List[int],
    relation_id_prefix: str,
    confidence: float = 1.0,
) -> List[Relation]:
    """Create a causal chain: A causes B causes C causes D...

    Args:
        card_ids: List of card IDs in causal order
        relation_id_prefix: Prefix for relation IDs
        confidence: Confidence for all relations

    Returns:
        List of CAUSES relations forming a chain
    """
    relations = []
    for i in range(len(card_ids) - 1):
        relations.append(
            Relation.create(
                relation_id=f"{relation_id_prefix}_{i}",
                relation_type=RelationType.CAUSES,
                source_card_id=card_ids[i],
                target_card_id=card_ids[i + 1],
                confidence=confidence,
            )
        )
    return relations


def create_support_network(
    evidence_card_ids: List[int],
    belief_card_id: int,
    relation_id_prefix: str,
    confidences: Optional[List[float]] = None,
) -> List[Relation]:
    """Create support relations from multiple evidence to one belief.

    Args:
        evidence_card_ids: List of evidence card IDs
        belief_card_id: Belief card ID being supported
        relation_id_prefix: Prefix for relation IDs
        confidences: Optional list of confidence scores (one per evidence)

    Returns:
        List of SUPPORTS relations
    """
    if confidences is None:
        confidences = [1.0] * len(evidence_card_ids)

    relations = []
    for i, evidence_id in enumerate(evidence_card_ids):
        relations.append(
            Relation.create(
                relation_id=f"{relation_id_prefix}_{i}",
                relation_type=RelationType.SUPPORTS,
                source_card_id=evidence_id,
                target_card_id=belief_card_id,
                confidence=confidences[i],
            )
        )
    return relations


def create_dependency_graph(
    task_pairs: List[tuple[int, int]],
    relation_id_prefix: str,
) -> List[Relation]:
    """Create DEPENDS_ON relations for task ordering.

    Args:
        task_pairs: List of (dependent_task_id, prerequisite_task_id) tuples
        relation_id_prefix: Prefix for relation IDs

    Returns:
        List of DEPENDS_ON relations
    """
    relations = []
    for i, (dependent, prerequisite) in enumerate(task_pairs):
        relations.append(
            Relation.create(
                relation_id=f"{relation_id_prefix}_{i}",
                relation_type=RelationType.DEPENDS_ON,
                source_card_id=dependent,
                target_card_id=prerequisite,
            )
        )
    return relations
