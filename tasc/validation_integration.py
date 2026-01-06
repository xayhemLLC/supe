"""Integration between evidence-based validation and typed semantic relations.

This module automatically creates and manages relations during validation workflows,
enabling the system to build a semantic knowledge graph as work is validated.

Key Integration Points:
1. Evidence validation → SUPPORTS relations
2. Debugging validation → CAUSES relations
3. Task validation → DEPENDS_ON checking
4. Validation results → CONTRADICTS detection
5. Support networks → Confidence aggregation
"""

from typing import List, Optional, Tuple, Dict, Any
import uuid
from datetime import datetime

from ab.abdb import ABMemory
from ab.models import Card, Buffer
from tasc.evidence import Evidence, EvidenceCollection, EvidenceSource
from tasc.relations import Relation, RelationType
from tasc.relation_storage import (
    store_relation,
    get_support_network,
    calculate_support_strength,
    find_contradictions,
    get_dependencies,
    check_dependencies_satisfied,
)
from tasc.validation import ValidationResult
from tasc.domains import TaskDomain


class ValidationRelationIntegrator:
    """Integrates validation system with relation system.

    Automatically creates and manages relations during validation workflows,
    building a semantic knowledge graph from validation artifacts.
    """

    def __init__(self, memory: ABMemory):
        """Initialize integrator with AB Memory instance.

        Args:
            memory: ABMemory instance for storage
        """
        self.memory = memory

    def store_evidence_as_card(
        self,
        evidence: Evidence,
        moment_id: Optional[int] = None,
    ) -> int:
        """Store evidence as a card in AB Memory.

        Args:
            evidence: Evidence object to store
            moment_id: Optional moment ID to associate with

        Returns:
            Card ID of stored evidence
        """
        import json

        # Create buffers from evidence
        buffers = [
            Buffer(name="evidence_type", payload=evidence.source.value.encode()),
            Buffer(name="text", payload=evidence.text.encode()),
            Buffer(name="citations", payload=json.dumps(evidence.citations).encode()),
            Buffer(name="confidence", payload=str(evidence.confidence).encode()),
            Buffer(name="validated", payload=str(evidence.validated).encode()),
        ]

        # Store as card
        card = self.memory.store_card(
            label=f"Evidence: {evidence.source.value}",
            buffers=buffers,
            track="execution",
            moment_id=moment_id,
        )

        return card.id

    def store_belief_as_card(
        self,
        belief_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        moment_id: Optional[int] = None,
    ) -> int:
        """Store a belief as a card in AB Memory.

        Args:
            belief_text: Text of the belief
            metadata: Optional metadata dictionary
            moment_id: Optional moment ID to associate with

        Returns:
            Card ID of stored belief
        """
        import json

        buffers = [
            Buffer(name="belief", payload=belief_text.encode()),
        ]

        if metadata:
            buffers.append(
                Buffer(name="metadata", payload=json.dumps(metadata).encode())
            )

        card = self.memory.store_card(
            label="Belief",
            buffers=buffers,
            track="awareness",
            moment_id=moment_id,
        )

        return card.id

    def create_support_relations_from_evidence(
        self,
        evidence_collection: EvidenceCollection,
        belief_card_id: int,
        relation_id_prefix: Optional[str] = None,
    ) -> List[Relation]:
        """Automatically create SUPPORTS relations from evidence to belief.

        This is called during validation to connect evidence artifacts
        to the belief/conclusion being validated.

        Args:
            evidence_collection: Collection of evidence
            belief_card_id: Card ID of the belief being supported
            relation_id_prefix: Optional prefix for relation IDs

        Returns:
            List of created SUPPORTS relations
        """
        if relation_id_prefix is None:
            relation_id_prefix = f"support_{uuid.uuid4().hex[:8]}"

        relations = []

        for i, evidence in enumerate(evidence_collection.evidence_items):
            # Store evidence as card
            evidence_card_id = self.store_evidence_as_card(evidence)

            # Create SUPPORTS relation
            relation = Relation.create(
                relation_id=f"{relation_id_prefix}_{i}",
                relation_type=RelationType.SUPPORTS,
                source_card_id=evidence_card_id,
                target_card_id=belief_card_id,
                confidence=evidence.confidence,
                metadata={
                    "evidence_source": evidence.source.value,
                    "validated": evidence.validated,
                    "created_by": "validation_integration",
                },
            )

            store_relation(self.memory, relation)
            relations.append(relation)

        return relations

    def create_causal_relation_from_debugging(
        self,
        root_cause_text: str,
        bug_card_id: int,
        confidence: float = 0.95,
    ) -> Tuple[int, Relation]:
        """Create CAUSES relation from debugging validation.

        Automatically links root cause to bug report during debugging validation.

        Args:
            root_cause_text: Description of root cause
            bug_card_id: Card ID of bug report
            confidence: Confidence in causal relationship

        Returns:
            Tuple of (root_cause_card_id, created_relation)
        """
        # Store root cause as card
        root_cause_card_id = self.memory.store_card(
            label="Root Cause",
            buffers=[Buffer(name="description", payload=root_cause_text.encode())],
            track="execution",
        ).id

        # Create CAUSES relation
        relation = Relation.create(
            relation_id=f"causes_{uuid.uuid4().hex[:8]}",
            relation_type=RelationType.CAUSES,
            source_card_id=root_cause_card_id,
            target_card_id=bug_card_id,
            confidence=confidence,
            metadata={
                "source": "debugging_validation",
                "created_at": datetime.now().isoformat(),
            },
        )

        store_relation(self.memory, relation)

        return root_cause_card_id, relation

    def check_contradictions_during_validation(
        self,
        new_evidence_card_id: int,
        validation_result: ValidationResult,
    ) -> List[Relation]:
        """Check for contradictions when adding new evidence.

        Automatically detects if new evidence contradicts existing beliefs
        and triggers human review if needed.

        Args:
            new_evidence_card_id: Card ID of new evidence
            validation_result: ValidationResult to update

        Returns:
            List of detected contradiction relations
        """
        contradictions = find_contradictions(self.memory, new_evidence_card_id)

        if contradictions:
            validation_result.requires_human_review = True
            validation_result.review_reasons.append(
                f"Evidence contradicts {len(contradictions)} existing belief(s)"
            )

            # Add details about each contradiction
            for contradiction in contradictions:
                other_card_id = (
                    contradiction.target_card_id
                    if contradiction.source_card_id == new_evidence_card_id
                    else contradiction.source_card_id
                )

                other_card = self.memory.get_card(other_card_id)
                validation_result.review_reasons.append(
                    f"  - Contradicts {other_card.label} (conf={contradiction.confidence:.2%})"
                )

        return contradictions

    def check_dependencies_during_validation(
        self,
        task_card_id: int,
        completed_card_ids: List[int],
        validation_result: ValidationResult,
    ) -> bool:
        """Check if task dependencies are satisfied during validation.

        Verifies that all prerequisite tasks are completed before validating
        a dependent task.

        Args:
            task_card_id: Card ID of task being validated
            completed_card_ids: List of completed task card IDs
            validation_result: ValidationResult to update

        Returns:
            True if all dependencies satisfied, False otherwise
        """
        satisfied = check_dependencies_satisfied(
            self.memory,
            task_card_id,
            completed_card_ids,
        )

        if not satisfied:
            dependencies = get_dependencies(self.memory, task_card_id)
            validation_result.requires_human_review = True
            validation_result.review_reasons.append(
                f"Task has {len(dependencies)} unsatisfied dependencies"
            )

            # Add details about missing dependencies
            for dep in dependencies:
                if dep.target_card_id not in completed_card_ids:
                    dep_card = self.memory.get_card(dep.target_card_id)
                    validation_result.review_reasons.append(
                        f"  - Requires: {dep_card.label}"
                    )

        return satisfied

    def calculate_belief_confidence_from_support(
        self,
        belief_card_id: int,
    ) -> float:
        """Calculate belief confidence from support network.

        Aggregates confidence from all SUPPORTS relations to determine
        overall belief strength.

        Args:
            belief_card_id: Card ID of belief

        Returns:
            Overall confidence score (0.0-1.0)
        """
        return calculate_support_strength(self.memory, belief_card_id)

    def update_validation_confidence_from_relations(
        self,
        belief_card_id: int,
        validation_result: ValidationResult,
    ) -> None:
        """Update validation confidence based on relation network.

        Enhances validation confidence by considering support network strength.

        Args:
            belief_card_id: Card ID of belief being validated
            validation_result: ValidationResult to update
        """
        support_strength = self.calculate_belief_confidence_from_support(belief_card_id)

        if support_strength > 0:
            # Enhance confidence with support network strength
            original_conf = validation_result.overall_confidence
            enhanced_conf = (original_conf + support_strength) / 2

            validation_result.overall_confidence = enhanced_conf
            validation_result.review_reasons.append(
                f"Confidence enhanced by support network: "
                f"{original_conf:.2%} → {enhanced_conf:.2%} "
                f"(support strength: {support_strength:.2%})"
            )

    def create_invalidation_relation_from_failure(
        self,
        hypothesis_card_id: int,
        counterexample_text: str,
        confidence: float = 0.95,
    ) -> Tuple[int, Relation]:
        """Create INVALIDATES relation when hypothesis fails validation.

        Args:
            hypothesis_card_id: Card ID of hypothesis that failed
            counterexample_text: Description of counterexample
            confidence: Confidence in invalidation

        Returns:
            Tuple of (counterexample_card_id, created_relation)
        """
        # Store counterexample as card
        counterexample_card_id = self.memory.store_card(
            label="Counterexample",
            buffers=[Buffer(name="description", payload=counterexample_text.encode())],
            track="execution",
        ).id

        # Create INVALIDATES relation
        relation = Relation.create(
            relation_id=f"invalidates_{uuid.uuid4().hex[:8]}",
            relation_type=RelationType.INVALIDATES,
            source_card_id=counterexample_card_id,
            target_card_id=hypothesis_card_id,
            confidence=confidence,
            metadata={
                "source": "validation_failure",
                "created_at": datetime.now().isoformat(),
            },
        )

        store_relation(self.memory, relation)

        return counterexample_card_id, relation


def integrate_validation_with_relations(
    memory: ABMemory,
    validation_result: ValidationResult,
    evidence_collection: EvidenceCollection,
    belief_text: str,
    domain: TaskDomain,
    task_card_id: Optional[int] = None,
    completed_task_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Complete integration workflow for validation with relations.

    This is the main entry point for integrated validation. It:
    1. Creates belief card from validation result
    2. Creates SUPPORTS relations from evidence
    3. Checks for contradictions
    4. Checks task dependencies (if applicable)
    5. Creates domain-specific relations (CAUSES for debugging, etc.)
    6. Updates confidence from support network

    Args:
        memory: ABMemory instance
        validation_result: Result from validation
        evidence_collection: Evidence that was validated
        belief_text: Text of belief/conclusion being validated
        domain: Task domain
        task_card_id: Optional task card ID for dependency checking
        completed_task_ids: Optional list of completed task card IDs

    Returns:
        Dictionary with integration results:
        - belief_card_id: Card ID of stored belief
        - support_relations: List of created SUPPORTS relations
        - contradictions: List of detected contradictions
        - dependencies_satisfied: Boolean (if task_card_id provided)
        - final_confidence: Updated confidence score
    """
    integrator = ValidationRelationIntegrator(memory)

    # 1. Store belief as card
    belief_card_id = integrator.store_belief_as_card(
        belief_text,
        metadata={"domain": domain.value, "initial_confidence": validation_result.overall_confidence},
    )

    # 2. Create SUPPORTS relations from evidence
    support_relations = integrator.create_support_relations_from_evidence(
        evidence_collection,
        belief_card_id,
    )

    # 3. Check for contradictions with existing beliefs
    contradictions = []
    for relation in support_relations:
        evidence_card_id = relation.source_card_id
        contradictions.extend(
            integrator.check_contradictions_during_validation(
                evidence_card_id,
                validation_result,
            )
        )

    # 4. Check task dependencies (if task validation)
    dependencies_satisfied = True
    if task_card_id is not None and completed_task_ids is not None:
        dependencies_satisfied = integrator.check_dependencies_during_validation(
            task_card_id,
            completed_task_ids,
            validation_result,
        )

    # 5. Domain-specific relation creation
    if domain == TaskDomain.DEBUGGING:
        # For debugging, look for root cause in evidence
        for evidence in evidence_collection.evidence_items:
            if evidence.source == EvidenceSource.CODE_ANALYSIS:
                # Found root cause - create CAUSES relation
                integrator.create_causal_relation_from_debugging(
                    evidence.text,
                    belief_card_id,
                    confidence=evidence.confidence,
                )
                break

    # 6. Update confidence from support network
    integrator.update_validation_confidence_from_relations(
        belief_card_id,
        validation_result,
    )

    # Calculate final confidence from support network
    final_confidence = integrator.calculate_belief_confidence_from_support(belief_card_id)

    return {
        "belief_card_id": belief_card_id,
        "support_relations": support_relations,
        "contradictions": contradictions,
        "dependencies_satisfied": dependencies_satisfied,
        "final_confidence": final_confidence,
        "validation_result": validation_result,
    }
