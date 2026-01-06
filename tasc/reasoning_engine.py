"""Reasoning engine for semantic knowledge graph.

Provides sophisticated reasoning capabilities using typed semantic relations:
- Transitive closure (multi-hop inference)
- Confidence propagation through networks
- Belief revision from contradictions
- Causal analysis with branch points
- Logical inference (forward/backward chaining)
- Support network analysis

This is Layer 7 of the cognitive architecture.
"""

from typing import List, Optional, Set, Tuple, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from ab.abdb import ABMemory
from tasc.relations import Relation, RelationType
from tasc.relation_storage import (
    get_relations_from_card,
    get_relations_to_card,
    store_relation,
)


class InferenceDirection(Enum):
    """Direction for inference chains."""
    FORWARD = "forward"   # Follow relations forward (source → target)
    BACKWARD = "backward"  # Follow relations backward (target → source)


@dataclass
class InferencePath:
    """A path through the knowledge graph."""
    cards: List[int] = field(default_factory=list)
    relations: List[Relation] = field(default_factory=list)
    confidence: float = 1.0
    length: int = 0

    def add_step(self, relation: Relation, card_id: int) -> None:
        """Add a step to the inference path."""
        self.relations.append(relation)
        self.cards.append(card_id)
        self.confidence *= relation.confidence
        self.length += 1


@dataclass
class BeliefRevision:
    """Represents a belief revision due to contradiction."""
    belief_card_id: int
    original_confidence: float
    revised_confidence: float
    reason: str
    contradicting_cards: List[int] = field(default_factory=list)


class ReasoningEngine:
    """Advanced reasoning engine for semantic knowledge graph."""

    def __init__(self, memory: ABMemory):
        """Initialize reasoning engine.

        Args:
            memory: ABMemory instance
        """
        self.memory = memory

    # ==========================================================================
    # Transitive Closure & Multi-Hop Inference
    # ==========================================================================

    def find_transitive_closure(
        self,
        start_card_id: int,
        relation_type: RelationType,
        direction: InferenceDirection = InferenceDirection.FORWARD,
        max_depth: int = 10,
    ) -> List[InferencePath]:
        """Find all cards reachable through transitive relations.

        For transitive relations (CAUSES, IMPLIES, DEPENDS_ON, etc.),
        finds all reachable cards through multi-hop inference.

        Args:
            start_card_id: Starting card ID
            relation_type: Type of relation to follow
            direction: Direction to traverse (forward or backward)
            max_depth: Maximum path length

        Returns:
            List of InferencePath objects, one per reachable card
        """
        if not self._is_transitive(relation_type):
            raise ValueError(f"Relation type {relation_type} is not transitive")

        paths = []
        visited = set()
        queue = [(start_card_id, InferencePath(cards=[start_card_id]))]

        while queue:
            current_id, current_path = queue.pop(0)

            if current_id in visited or current_path.length >= max_depth:
                continue

            visited.add(current_id)

            # Get relations from current card
            if direction == InferenceDirection.FORWARD:
                relations = get_relations_from_card(self.memory, current_id, relation_type)
                next_cards = [(r.target_card_id, r) for r in relations]
            else:  # BACKWARD
                relations = get_relations_to_card(self.memory, current_id, relation_type)
                next_cards = [(r.source_card_id, r) for r in relations]

            # Add each reachable card to queue
            for next_card_id, relation in next_cards:
                if next_card_id not in visited:
                    new_path = InferencePath(
                        cards=current_path.cards.copy(),
                        relations=current_path.relations.copy(),
                        confidence=current_path.confidence,
                        length=current_path.length,
                    )
                    new_path.add_step(relation, next_card_id)
                    queue.append((next_card_id, new_path))
                    paths.append(new_path)

        return paths

    def find_shortest_path(
        self,
        start_card_id: int,
        end_card_id: int,
        relation_type: RelationType,
        direction: InferenceDirection = InferenceDirection.FORWARD,
    ) -> Optional[InferencePath]:
        """Find shortest path between two cards.

        Args:
            start_card_id: Start card ID
            end_card_id: End card ID
            relation_type: Type of relation to follow
            direction: Direction to traverse

        Returns:
            InferencePath if path exists, None otherwise
        """
        paths = self.find_transitive_closure(start_card_id, relation_type, direction)

        # Filter paths that reach end_card_id
        valid_paths = [p for p in paths if p.cards[-1] == end_card_id]

        if not valid_paths:
            return None

        # Return shortest path (or highest confidence if same length)
        return min(valid_paths, key=lambda p: (p.length, -p.confidence))

    def calculate_transitive_confidence(
        self,
        start_card_id: int,
        end_card_id: int,
        relation_type: RelationType,
    ) -> float:
        """Calculate confidence for transitive inference.

        Finds path from start to end and returns product of confidences.

        Args:
            start_card_id: Start card ID
            end_card_id: End card ID
            relation_type: Type of relation to follow

        Returns:
            Confidence score (0.0-1.0), or 0.0 if no path exists
        """
        path = self.find_shortest_path(start_card_id, end_card_id, relation_type)
        return path.confidence if path else 0.0

    # ==========================================================================
    # Causal Analysis
    # ==========================================================================

    def analyze_causal_chain(
        self,
        effect_card_id: int,
        max_depth: int = 10,
    ) -> Dict[str, Any]:
        """Analyze complete causal chain for an effect.

        Traces CAUSES relations backwards to find all contributing factors,
        including branch points where multiple causes converge.

        Args:
            effect_card_id: Card ID of effect to analyze
            max_depth: Maximum depth to trace

        Returns:
            Dictionary with:
            - root_causes: List of root cause card IDs
            - all_causes: List of all intermediate causes
            - branch_points: Cards with multiple incoming causes
            - confidence_by_path: Confidence for each root → effect path
        """
        # Find all paths to root causes
        paths = self.find_transitive_closure(
            effect_card_id,
            RelationType.CAUSES,
            InferenceDirection.BACKWARD,
            max_depth,
        )

        # Identify root causes (no incoming CAUSES relations)
        all_cards = {effect_card_id}
        for path in paths:
            all_cards.update(path.cards)

        root_causes = []
        for card_id in all_cards:
            incoming = get_relations_to_card(self.memory, card_id, RelationType.CAUSES)
            if not incoming and card_id != effect_card_id:
                root_causes.append(card_id)

        # Find branch points (multiple incoming causes)
        branch_points = []
        for card_id in all_cards:
            incoming = get_relations_to_card(self.memory, card_id, RelationType.CAUSES)
            if len(incoming) > 1:
                branch_points.append(card_id)

        # Calculate confidence for each root → effect path
        confidence_by_path = {}
        for root_id in root_causes:
            path = self.find_shortest_path(
                root_id,
                effect_card_id,
                RelationType.CAUSES,
                InferenceDirection.FORWARD,
            )
            if path:
                confidence_by_path[root_id] = path.confidence

        return {
            "root_causes": root_causes,
            "all_causes": list(all_cards - {effect_card_id}),
            "branch_points": branch_points,
            "confidence_by_path": confidence_by_path,
            "total_paths": len(paths),
        }

    # ==========================================================================
    # Logical Inference
    # ==========================================================================

    def forward_chain(
        self,
        premise_card_ids: List[int],
        max_hops: int = 5,
    ) -> List[Tuple[int, float]]:
        """Forward chaining: derive conclusions from premises.

        Follows IMPLIES relations forward from given premises to find
        all derivable conclusions.

        Args:
            premise_card_ids: List of premise card IDs
            max_hops: Maximum inference hops

        Returns:
            List of (conclusion_card_id, confidence) tuples
        """
        conclusions = {}  # card_id -> best confidence

        for premise_id in premise_card_ids:
            paths = self.find_transitive_closure(
                premise_id,
                RelationType.IMPLIES,
                InferenceDirection.FORWARD,
                max_hops,
            )

            for path in paths:
                conclusion_id = path.cards[-1]
                if conclusion_id not in conclusions or path.confidence > conclusions[conclusion_id]:
                    conclusions[conclusion_id] = path.confidence

        return sorted(conclusions.items(), key=lambda x: -x[1])

    def backward_chain(
        self,
        goal_card_id: int,
        known_facts: Set[int],
        max_hops: int = 5,
    ) -> Tuple[bool, float, List[int]]:
        """Backward chaining: check if goal is derivable from known facts.

        Traces IMPLIES relations backwards from goal to see if any known
        facts can derive it.

        Args:
            goal_card_id: Card ID of goal to prove
            known_facts: Set of card IDs representing known facts
            max_hops: Maximum inference hops

        Returns:
            Tuple of (provable, confidence, required_facts)
        """
        paths = self.find_transitive_closure(
            goal_card_id,
            RelationType.IMPLIES,
            InferenceDirection.BACKWARD,
            max_hops,
        )

        # Find paths that start with known facts
        valid_paths = []
        for path in paths:
            if path.cards[-1] in known_facts:
                valid_paths.append(path)

        if not valid_paths:
            return False, 0.0, []

        # Return best path
        best_path = max(valid_paths, key=lambda p: p.confidence)
        return True, best_path.confidence, best_path.cards[:-1]

    # ==========================================================================
    # Belief Revision
    # ==========================================================================

    def detect_all_contradictions(self) -> List[Tuple[int, int, float]]:
        """Detect all contradictions in the knowledge graph.

        Returns:
            List of (card_id_1, card_id_2, confidence) tuples
        """
        # Get all CONTRADICTS relations
        all_relations = self.memory.get_relations(relation_type="contradicts")

        contradictions = []
        seen = set()

        for rel_dict in all_relations:
            pair = tuple(sorted([rel_dict["source_card_id"], rel_dict["target_card_id"]]))
            if pair not in seen:
                seen.add(pair)
                contradictions.append((pair[0], pair[1], rel_dict["confidence"]))

        return contradictions

    def revise_belief_from_contradiction(
        self,
        belief_card_id: int,
        contradicting_card_id: int,
        contradiction_confidence: float,
    ) -> BeliefRevision:
        """Revise belief confidence based on contradiction.

        When a contradiction is detected, reduces belief confidence
        proportional to the contradiction strength.

        Args:
            belief_card_id: Card ID of belief to revise
            contradicting_card_id: Card ID of contradicting evidence
            contradiction_confidence: Confidence in the contradiction

        Returns:
            BeliefRevision object with revision details
        """
        # Get current belief confidence (from support network if available)
        from tasc.relation_storage import calculate_support_strength

        original_confidence = calculate_support_strength(self.memory, belief_card_id)
        if original_confidence == 0.0:
            original_confidence = 0.5  # Default if no support network

        # Calculate revised confidence
        # Stronger contradiction → larger reduction
        reduction_factor = contradiction_confidence
        revised_confidence = original_confidence * (1.0 - reduction_factor)

        revision = BeliefRevision(
            belief_card_id=belief_card_id,
            original_confidence=original_confidence,
            revised_confidence=revised_confidence,
            reason=f"Contradicted by evidence with {contradiction_confidence:.2%} confidence",
            contradicting_cards=[contradicting_card_id],
        )

        return revision

    def auto_revise_all_contradicted_beliefs(self) -> List[BeliefRevision]:
        """Automatically revise all beliefs with contradictions.

        Returns:
            List of BeliefRevision objects
        """
        contradictions = self.detect_all_contradictions()
        revisions = []

        for card1, card2, conf in contradictions:
            # Revise both beliefs
            rev1 = self.revise_belief_from_contradiction(card1, card2, conf)
            rev2 = self.revise_belief_from_contradiction(card2, card1, conf)
            revisions.extend([rev1, rev2])

        return revisions

    # ==========================================================================
    # Confidence Propagation
    # ==========================================================================

    def propagate_confidence_through_network(
        self,
        start_card_id: int,
        relation_type: RelationType,
        initial_confidence: float,
        propagation_factor: float = 0.9,
        max_hops: int = 5,
    ) -> Dict[int, float]:
        """Propagate confidence through network.

        Spreads confidence from source card through relations,
        with decay at each hop.

        Args:
            start_card_id: Starting card ID
            relation_type: Type of relation to follow
            initial_confidence: Starting confidence
            propagation_factor: Decay factor per hop (0.0-1.0)
            max_hops: Maximum hops to propagate

        Returns:
            Dictionary mapping card_id → propagated confidence
        """
        confidences = {start_card_id: initial_confidence}
        visited = set()
        queue = [(start_card_id, initial_confidence, 0)]

        while queue:
            current_id, current_conf, depth = queue.pop(0)

            if current_id in visited or depth >= max_hops:
                continue

            visited.add(current_id)

            # Get outgoing relations
            relations = get_relations_from_card(self.memory, current_id, relation_type)

            for relation in relations:
                target_id = relation.target_card_id

                # Calculate propagated confidence
                propagated = current_conf * relation.confidence * propagation_factor

                # Update if better than existing
                if target_id not in confidences or propagated > confidences[target_id]:
                    confidences[target_id] = propagated
                    queue.append((target_id, propagated, depth + 1))

        return confidences

    def calculate_network_support_strength(
        self,
        belief_card_id: int,
        include_transitive: bool = True,
        max_hops: int = 3,
    ) -> float:
        """Calculate support strength including transitive support.

        Not just direct SUPPORTS relations, but also indirect support
        through IMPLIES chains (if A supports B and B implies C, then A
        indirectly supports C).

        Args:
            belief_card_id: Card ID of belief
            include_transitive: Whether to include transitive support
            max_hops: Maximum hops for transitive support

        Returns:
            Overall support strength (0.0-1.0)
        """
        from tasc.relation_storage import get_support_network

        # Get direct support
        direct_support = get_support_network(self.memory, belief_card_id)

        if not include_transitive:
            if not direct_support:
                return 0.0
            return sum(r.confidence for r in direct_support) / len(direct_support)

        # Calculate transitive support
        all_support_confidences = [r.confidence for r in direct_support]

        # For each direct supporter, find what supports it (transitively)
        for supporter_rel in direct_support:
            supporter_id = supporter_rel.source_card_id

            # Find IMPLIES chains leading to this supporter
            paths = self.find_transitive_closure(
                supporter_id,
                RelationType.IMPLIES,
                InferenceDirection.BACKWARD,
                max_hops,
            )

            # Add transitive support with decay
            for path in paths:
                transitive_conf = path.confidence * supporter_rel.confidence * 0.8
                all_support_confidences.append(transitive_conf)

        if not all_support_confidences:
            return 0.0

        # Calculate average with bonus for multiple sources
        avg_conf = sum(all_support_confidences) / len(all_support_confidences)
        if len(all_support_confidences) >= 3:
            avg_conf = min(1.0, avg_conf * 1.1)

        return avg_conf

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    def _is_transitive(self, relation_type: RelationType) -> bool:
        """Check if relation type is transitive."""
        transitive_types = {
            RelationType.CAUSES,
            RelationType.IMPLIES,
            RelationType.EQUALS,
            RelationType.DEPENDS_ON,
            RelationType.REFINES,
            RelationType.GENERALIZES,
        }
        return relation_type in transitive_types

    def explain_inference(
        self,
        path: InferencePath,
        memory: ABMemory,
    ) -> str:
        """Generate human-readable explanation of inference path.

        Args:
            path: InferencePath to explain
            memory: ABMemory instance to get card labels

        Returns:
            Human-readable explanation string
        """
        if not path.relations:
            return "No inference path"

        explanation = []
        explanation.append(f"Inference Path (confidence: {path.confidence:.2%}):\n")

        for i, (card_id, relation) in enumerate(zip(path.cards[:-1], path.relations)):
            card = memory.get_card(card_id)
            next_card = memory.get_card(path.cards[i + 1])

            explanation.append(
                f"  {i + 1}. {card.label} "
                f"--{relation.type.value}-> "
                f"{next_card.label} "
                f"(conf={relation.confidence:.2%})"
            )

        return "\n".join(explanation)
