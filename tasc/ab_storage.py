"""AB Memory integration for evidence-based validation.

This module provides functions to store and retrieve evidence, evidence collections,
and validation results in AB Memory. This enables:

1. Long-term evidence tracking across sessions
2. Retrospective validation (confidence can change over time)
3. Cross-task evidence sharing and reuse
4. Evidence-based search and recall
5. Validation history and audit trails

Evidence and validation results are stored as Cards with appropriate buffers,
maintaining the AB Memory architecture while extending it for validation.
"""

import json
from typing import Dict, List, Optional, Tuple

from ab.abdb import ABMemory
from ab.models import Buffer, Card

from .evidence import Evidence, EvidenceCollection, EvidenceSource
from .validation import ValidationResult
from .tasc import Tasc


# ============================================================================
# Evidence Storage
# ============================================================================

def store_evidence(memory: ABMemory, evidence: Evidence, moment_id: Optional[int] = None) -> int:
    """Store an evidence item as a Card in AB Memory.

    Args:
        memory: AB Memory instance
        evidence: Evidence to store
        moment_id: Optional moment ID to associate with

    Returns:
        Card ID of the stored evidence
    """
    # Create buffers for evidence data
    buffers = [
        Buffer(
            name="evidence_data",
            headers={"type": "evidence", "source": evidence.source.value},
            payload=json.dumps(evidence.to_dict()).encode("utf-8"),
        ),
        Buffer(
            name="text",
            headers={},
            payload=evidence.text.encode("utf-8"),
        ),
    ]

    # Add citations as a separate buffer if present
    if evidence.citations:
        buffers.append(
            Buffer(
                name="citations",
                headers={"count": len(evidence.citations)},
                payload=json.dumps(evidence.citations).encode("utf-8"),
            )
        )

    # Create card
    card = Card(
        label=f"Evidence: {evidence.source.value}",
        moment_id=moment_id,
        owner_self="validation_system",
        buffers=buffers,
        track="execution",  # Evidence is execution/validation tracking
    )

    # Store in AB Memory
    card_id = memory.store_card(card)

    return card_id


def load_evidence(memory: ABMemory, card_id: int) -> Optional[Evidence]:
    """Load an evidence item from AB Memory.

    Args:
        memory: AB Memory instance
        card_id: Card ID of the evidence

    Returns:
        Evidence object or None if not found
    """
    card = memory.fetch_card(card_id)
    if not card:
        return None

    # Find evidence_data buffer
    for buffer in card.buffers:
        if buffer.name == "evidence_data":
            data = json.loads(buffer.payload.decode("utf-8"))
            return Evidence.from_dict(data)

    return None


def store_evidence_collection(
    memory: ABMemory,
    collection: EvidenceCollection,
    moment_id: Optional[int] = None
) -> int:
    """Store an evidence collection as a Card in AB Memory.

    This stores the collection metadata and references to individual evidence cards.

    Args:
        memory: AB Memory instance
        collection: Evidence collection to store
        moment_id: Optional moment ID to associate with

    Returns:
        Card ID of the stored collection
    """
    # Store individual evidence items first and collect their card IDs
    evidence_card_ids = []
    for evidence in collection.evidence_items:
        card_id = store_evidence(memory, evidence, moment_id)
        evidence_card_ids.append(card_id)

    # Create collection card with references
    buffers = [
        Buffer(
            name="collection_data",
            headers={
                "type": "evidence_collection",
                "tasc_id": collection.tasc_id,
                "evidence_count": len(collection.evidence_items),
            },
            payload=json.dumps({
                "id": collection.id,
                "tasc_id": collection.tasc_id,
                "created_at": collection.created_at,
                "evidence_card_ids": evidence_card_ids,
            }).encode("utf-8"),
        ),
        Buffer(
            name="evidence_summary",
            headers={},
            payload=json.dumps({
                "total_evidence": len(collection.evidence_items),
                "source_diversity": collection.get_source_diversity(),
                "validated_count": len(collection.get_validated_evidence()),
                "sources": list(set(e.source.value for e in collection.evidence_items)),
            }).encode("utf-8"),
        ),
    ]

    card = Card(
        label=f"Evidence Collection: {collection.tasc_id}",
        moment_id=moment_id,
        owner_self="validation_system",
        buffers=buffers,
        track="execution",
    )

    card_id = memory.store_card(card)
    return card_id


def load_evidence_collection(
    memory: ABMemory,
    card_id: int
) -> Optional[EvidenceCollection]:
    """Load an evidence collection from AB Memory.

    Args:
        memory: AB Memory instance
        card_id: Card ID of the collection

    Returns:
        EvidenceCollection object or None if not found
    """
    card = memory.fetch_card(card_id)
    if not card:
        return None

    # Find collection_data buffer
    for buffer in card.buffers:
        if buffer.name == "collection_data":
            data = json.loads(buffer.payload.decode("utf-8"))

            # Load individual evidence items
            evidence_items = []
            for evidence_card_id in data.get("evidence_card_ids", []):
                evidence = load_evidence(memory, evidence_card_id)
                if evidence:
                    evidence_items.append(evidence)

            return EvidenceCollection(
                id=data["id"],
                tasc_id=data["tasc_id"],
                evidence_items=evidence_items,
                created_at=data["created_at"],
            )

    return None


# ============================================================================
# Validation Result Storage
# ============================================================================

def store_validation_result(
    memory: ABMemory,
    result: ValidationResult,
    tasc_id: str,
    moment_id: Optional[int] = None
) -> int:
    """Store a validation result as a Card in AB Memory.

    Args:
        memory: AB Memory instance
        result: ValidationResult to store
        tasc_id: ID of the tasc being validated
        moment_id: Optional moment ID to associate with

    Returns:
        Card ID of the stored validation result
    """
    buffers = [
        Buffer(
            name="validation_result",
            headers={
                "type": "validation_result",
                "tasc_id": tasc_id,
                "confidence": result.overall_confidence,
                "status": result.validation_status,
            },
            payload=json.dumps(result.to_dict()).encode("utf-8"),
        ),
        Buffer(
            name="confidence_breakdown",
            headers={},
            payload=json.dumps({
                "evidence_factor": result.evidence_factor,
                "process_factor": result.process_factor,
                "objective_factor": result.objective_factor,
            }).encode("utf-8"),
        ),
    ]

    # Add review requirements if needed
    if result.requires_human_review:
        buffers.append(
            Buffer(
                name="review_requirements",
                headers={"required": True},
                payload=json.dumps({
                    "reasons": result.review_reasons,
                    "missing_evidence": result.missing_evidence_types,
                    "missing_steps": result.missing_process_steps,
                }).encode("utf-8"),
            )
        )

    card = Card(
        label=f"Validation: {tasc_id} ({result.validation_status})",
        moment_id=moment_id,
        owner_self="validation_system",
        buffers=buffers,
        track="execution",
        master_output=f"Validation confidence: {result.overall_confidence:.2f}",
    )

    card_id = memory.store_card(card)
    return card_id


def load_validation_result(
    memory: ABMemory,
    card_id: int
) -> Optional[Tuple[ValidationResult, str]]:
    """Load a validation result from AB Memory.

    Args:
        memory: AB Memory instance
        card_id: Card ID of the validation result

    Returns:
        Tuple of (ValidationResult, tasc_id) or None if not found
    """
    card = memory.fetch_card(card_id)
    if not card:
        return None

    # Find validation_result buffer
    for buffer in card.buffers:
        if buffer.name == "validation_result":
            data = json.loads(buffer.payload.decode("utf-8"))

            result = ValidationResult(
                overall_confidence=data["overall_confidence"],
                evidence_factor=data["evidence_factor"],
                process_factor=data["process_factor"],
                objective_factor=data["objective_factor"],
                evidence_count=data["evidence_count"],
                source_diversity=data["source_diversity"],
                validated_evidence_count=data["validated_evidence_count"],
                cited_evidence_count=data["cited_evidence_count"],
                missing_evidence_types=data.get("missing_evidence_types", []),
                missing_process_steps=data.get("missing_process_steps", []),
                objective_checks=data.get("objective_checks", {}),
                requires_human_review=data.get("requires_human_review", False),
                review_reasons=data.get("review_reasons", []),
                validation_status=data.get("validation_status", "pending"),
            )

            tasc_id = buffer.headers.get("tasc_id", "")
            return result, tasc_id

    return None


# ============================================================================
# Validation History & Retrospective Validation
# ============================================================================

def get_validation_history(
    memory: ABMemory,
    tasc_id: str
) -> List[Tuple[int, ValidationResult]]:
    """Get validation history for a tasc.

    Args:
        memory: AB Memory instance
        tasc_id: Tasc ID

    Returns:
        List of (card_id, ValidationResult) tuples in chronological order
    """
    # Search for validation result cards for this tasc
    # Using label search since validation cards have predictable labels
    all_cards = memory.search_cards(
        query=f"Validation: {tasc_id}",
        track="execution",
        limit=100,
    )

    history = []
    for card in all_cards:
        result_tuple = load_validation_result(memory, card.id)
        if result_tuple:
            result, _ = result_tuple
            history.append((card.id, result))

    # Sort by card ID (chronological order)
    history.sort(key=lambda x: x[0])

    return history


def get_latest_validation(
    memory: ABMemory,
    tasc_id: str
) -> Optional[ValidationResult]:
    """Get the most recent validation result for a tasc.

    Args:
        memory: AB Memory instance
        tasc_id: Tasc ID

    Returns:
        Latest ValidationResult or None if no validation exists
    """
    history = get_validation_history(memory, tasc_id)
    if not history:
        return None

    _, result = history[-1]
    return result


def update_validation_confidence(
    memory: ABMemory,
    tasc_id: str,
    new_evidence: List[Evidence],
    moment_id: Optional[int] = None
) -> Optional[ValidationResult]:
    """Update validation confidence with new evidence (retrospective validation).

    This allows confidence scores to be updated as new evidence emerges,
    enabling retrospective validation and learning from outcomes.

    Args:
        memory: AB Memory instance
        tasc_id: Tasc ID
        new_evidence: New evidence to incorporate
        moment_id: Optional moment ID

    Returns:
        Updated ValidationResult or None if no existing validation
    """
    # Get existing validation
    latest = get_latest_validation(memory, tasc_id)
    if not latest:
        return None

    # Store new evidence
    for evidence in new_evidence:
        store_evidence(memory, evidence, moment_id)

    # TODO: Recalculate validation with combined evidence
    # For now, just create a note that confidence should be re-evaluated
    buffers = [
        Buffer(
            name="retrospective_evidence",
            headers={
                "tasc_id": tasc_id,
                "new_evidence_count": len(new_evidence),
            },
            payload=json.dumps({
                "message": "New evidence added - validation should be re-run",
                "previous_confidence": latest.overall_confidence,
                "new_evidence_ids": [e.id for e in new_evidence],
            }).encode("utf-8"),
        )
    ]

    card = Card(
        label=f"Retrospective Evidence: {tasc_id}",
        moment_id=moment_id,
        owner_self="validation_system",
        buffers=buffers,
        track="execution",
    )

    memory.store_card(card)

    return latest


# ============================================================================
# Evidence Search & Reuse
# ============================================================================

def search_evidence_by_source(
    memory: ABMemory,
    source: EvidenceSource,
    limit: int = 50
) -> List[Evidence]:
    """Search for evidence by source type.

    Args:
        memory: AB Memory instance
        source: Evidence source to search for
        limit: Maximum number of results

    Returns:
        List of Evidence objects
    """
    # Search for evidence cards with specific source
    cards = memory.search_cards(
        query=f"Evidence: {source.value}",
        track="execution",
        limit=limit,
    )

    evidence_list = []
    for card in cards:
        evidence = load_evidence(memory, card.id)
        if evidence and evidence.source == source:
            evidence_list.append(evidence)

    return evidence_list


def search_evidence_by_text(
    memory: ABMemory,
    search_text: str,
    limit: int = 50
) -> List[Evidence]:
    """Search for evidence by text content.

    Args:
        memory: AB Memory instance
        search_text: Text to search for
        limit: Maximum number of results

    Returns:
        List of Evidence objects
    """
    # Search for evidence cards containing the text
    cards = memory.search_cards(
        query=search_text,
        track="execution",
        limit=limit,
    )

    evidence_list = []
    for card in cards:
        # Only include cards that are actually evidence
        if card.label.startswith("Evidence:"):
            evidence = load_evidence(memory, card.id)
            if evidence:
                evidence_list.append(evidence)

    return evidence_list


def find_similar_validation_cases(
    memory: ABMemory,
    tasc: Tasc,
    limit: int = 10
) -> List[Tuple[str, ValidationResult]]:
    """Find similar past validation cases to learn from.

    This searches for tascs with similar titles or requirements and
    returns their validation results to help guide current validation.

    Args:
        memory: AB Memory instance
        tasc: Current tasc
        limit: Maximum number of results

    Returns:
        List of (tasc_id, ValidationResult) tuples
    """
    # Search for validation results with similar tasc titles
    cards = memory.search_cards(
        query=tasc.title,
        track="execution",
        limit=limit,
    )

    similar_cases = []
    for card in cards:
        if card.label.startswith("Validation:"):
            result_tuple = load_validation_result(memory, card.id)
            if result_tuple:
                result, similar_tasc_id = result_tuple
                if similar_tasc_id != tasc.id:  # Exclude self
                    similar_cases.append((similar_tasc_id, result))

    return similar_cases


# ============================================================================
# Complete Validation Workflow
# ============================================================================

async def validate_and_store(
    memory: ABMemory,
    tasc: Tasc,
    evidence_collection: EvidenceCollection,
    moment_id: Optional[int] = None,
    debug: bool = False,
) -> Tuple[ValidationResult, int]:
    """Complete validation workflow: validate, store evidence, store results.

    This is the main entry point for validation with AB Memory persistence.

    Args:
        memory: AB Memory instance
        tasc: Tasc to validate
        evidence_collection: Evidence collection
        moment_id: Optional moment ID
        debug: Enable debug logging

    Returns:
        Tuple of (ValidationResult, validation_card_id)
    """
    from .validation import UnifiedValidator

    # 1. Run validation
    validator = UnifiedValidator(debug=debug)
    result = await validator.validate(tasc, evidence_collection)

    # 2. Store evidence collection
    collection_card_id = store_evidence_collection(memory, evidence_collection, moment_id)

    # 3. Store validation result
    validation_card_id = store_validation_result(memory, result, tasc.id, moment_id)

    # 4. Update tasc with validation metadata
    tasc.evidence_collection_id = str(collection_card_id)
    tasc.validation_confidence = result.overall_confidence
    tasc.validation_status = result.validation_status

    if debug:
        print(f"\nStored in AB Memory:")
        print(f"  Evidence Collection: Card {collection_card_id}")
        print(f"  Validation Result: Card {validation_card_id}")

    return result, validation_card_id
