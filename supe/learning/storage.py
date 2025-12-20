"""AB Memory integration for the learning system.

Store learning artifacts (Questions, Evidence, Beliefs, LearningContext)
as Cards in AB Memory following the existing Tascer storage patterns.

Storage strategy:
- Questions → label="learning_question", track="awareness"
- Evidence → label="learning_evidence", track="awareness"
- Beliefs → label="learning_belief", track="awareness"
- LearningContext → label="learning_context", track="awareness"

All entities are connected via Relations:
- Question --has_evidence--> Evidence
- Question --answered_by--> Belief
- Belief --supported_by--> Evidence
- LearningContext --contains--> Question/Belief/Evidence
"""

import json
from typing import List, Optional, Dict, Any, Tuple

from .models import Question, Evidence, Belief, LearningContext
from .types import ID


# ============================================================================
# Question Storage
# ============================================================================


def store_question(
    memory,
    question: Question,
    moment_id: Optional[int] = None,
) -> int:
    """Store a Question as a Card in AB Memory.

    Args:
        memory: ABMemory instance.
        question: Question to store.
        moment_id: Optional moment ID.

    Returns:
        Card ID of the stored question.
    """
    from ab.models import Buffer

    # Serialize question to JSON
    question_json = json.dumps(question.to_dict(), indent=2).encode("utf-8")

    buf = Buffer(
        name="question",
        headers={
            "question_id": question.id,
            "question_type": question.question_type.value,
            "status": question.status.value,
            "priority": str(question.priority),
            "type": "learning_question",
        },
        payload=question_json,
    )

    card = memory.store_card(
        label="learning_question",
        buffers=[buf],
        moment_id=moment_id,
        master_input=question.text[:100],  # First 100 chars as input
        master_output=question.status.value,
        track="awareness",
    )
    return card.id


def load_question(memory, card_id: int) -> Question:
    """Load a Question from AB Memory.

    Args:
        memory: ABMemory instance.
        card_id: ID of the card to load.

    Returns:
        Decoded Question.

    Raises:
        ValueError: If card doesn't contain a valid question.
    """
    card = memory.get_card(card_id)

    if card.label != "learning_question":
        raise ValueError(f"Card {card_id} is not a learning_question (label={card.label})")

    # Find question buffer
    question_buf = None
    for buf in card.buffers:
        if buf.name == "question":
            question_buf = buf
            break

    if question_buf is None:
        raise ValueError(f"Card {card_id} does not contain a question buffer")

    question_data = json.loads(question_buf.payload.decode("utf-8"))
    return Question.from_dict(question_data)


def find_questions_by_status(memory, status: str) -> List[Tuple[int, Dict[str, Any]]]:
    """Find all questions with a given status.

    Args:
        memory: ABMemory instance.
        status: Question status (e.g., "OPEN", "ANSWERED").

    Returns:
        List of (card_id, question_summary) tuples.
    """
    cards = memory.find_cards_by_label("learning_question")
    results = []

    for card in cards:
        for buf in card.buffers:
            if buf.name == "question":
                headers = buf.headers
                if headers.get("status") == status:
                    results.append((
                        card.id,
                        {
                            "question_id": headers.get("question_id"),
                            "question_type": headers.get("question_type"),
                            "status": headers.get("status"),
                            "priority": headers.get("priority"),
                        }
                    ))
                break

    return results


# ============================================================================
# Evidence Storage
# ============================================================================


def store_evidence(
    memory,
    evidence: Evidence,
    question_card_id: Optional[int] = None,
    moment_id: Optional[int] = None,
) -> int:
    """Store an Evidence as a Card in AB Memory.

    Args:
        memory: ABMemory instance.
        evidence: Evidence to store.
        question_card_id: Optional question card ID to link to.
        moment_id: Optional moment ID.

    Returns:
        Card ID of the stored evidence.
    """
    from ab.models import Buffer

    # Serialize evidence to JSON
    evidence_json = json.dumps(evidence.to_dict(), indent=2).encode("utf-8")

    buf = Buffer(
        name="evidence",
        headers={
            "evidence_id": evidence.id,
            "source": evidence.source.value,
            "validated": str(evidence.validated),
            "confidence": str(float(evidence.confidence)),
            "type": "learning_evidence",
        },
        payload=evidence_json,
    )

    card = memory.store_card(
        label="learning_evidence",
        buffers=[buf],
        moment_id=moment_id,
        master_input=evidence.text[:100],
        master_output=evidence.source.value,
        track="awareness",
    )

    # Link to question if provided
    if question_card_id is not None:
        memory.create_connection(
            source_card_id=question_card_id,
            target_card_id=card.id,
            relation="has_evidence",
        )

    return card.id


def load_evidence(memory, card_id: int) -> Evidence:
    """Load an Evidence from AB Memory.

    Args:
        memory: ABMemory instance.
        card_id: ID of the card to load.

    Returns:
        Decoded Evidence.

    Raises:
        ValueError: If card doesn't contain valid evidence.
    """
    card = memory.get_card(card_id)

    if card.label != "learning_evidence":
        raise ValueError(f"Card {card_id} is not a learning_evidence (label={card.label})")

    # Find evidence buffer
    evidence_buf = None
    for buf in card.buffers:
        if buf.name == "evidence":
            evidence_buf = buf
            break

    if evidence_buf is None:
        raise ValueError(f"Card {card_id} does not contain an evidence buffer")

    evidence_data = json.loads(evidence_buf.payload.decode("utf-8"))
    return Evidence.from_dict(evidence_data)


def find_evidence_for_question(memory, question_card_id: int) -> List[Tuple[int, Evidence]]:
    """Find all evidence linked to a question.

    Args:
        memory: ABMemory instance.
        question_card_id: Question card ID.

    Returns:
        List of (card_id, evidence) tuples.
    """
    # Get all connections from question
    connections = memory.get_connections(source_card_id=question_card_id, relation="has_evidence")
    results = []

    for conn in connections:
        try:
            evidence = load_evidence(memory, conn.target_card_id)
            results.append((conn.target_card_id, evidence))
        except ValueError:
            # Skip invalid cards
            continue

    return results


# ============================================================================
# Belief Storage
# ============================================================================


def store_belief(
    memory,
    belief: Belief,
    question_card_id: int,
    evidence_card_ids: List[int],
    moment_id: Optional[int] = None,
) -> int:
    """Store a Belief as a Card in AB Memory.

    Args:
        memory: ABMemory instance.
        belief: Belief to store.
        question_card_id: Question card ID this belief answers.
        evidence_card_ids: Evidence card IDs supporting this belief.
        moment_id: Optional moment ID.

    Returns:
        Card ID of the stored belief.
    """
    from ab.models import Buffer

    # Serialize belief to JSON
    belief_json = json.dumps(belief.to_dict(), indent=2).encode("utf-8")

    buf = Buffer(
        name="belief",
        headers={
            "belief_id": belief.id,
            "question_id": belief.question_id,
            "mode": belief.mode.value,
            "confidence": str(float(belief.confidence)),
            "type": "learning_belief",
        },
        payload=belief_json,
    )

    card = memory.store_card(
        label="learning_belief",
        buffers=[buf],
        moment_id=moment_id,
        master_input=belief.question_id,
        master_output=f"confidence={belief.confidence:.2f}",
        track="awareness",
    )

    # Link to question
    memory.create_connection(
        source_card_id=question_card_id,
        target_card_id=card.id,
        relation="answered_by",
    )

    # Link to all supporting evidence
    for evidence_card_id in evidence_card_ids:
        memory.create_connection(
            source_card_id=card.id,
            target_card_id=evidence_card_id,
            relation="supported_by",
        )

    return card.id


def load_belief(memory, card_id: int) -> Belief:
    """Load a Belief from AB Memory.

    Args:
        memory: ABMemory instance.
        card_id: ID of the card to load.

    Returns:
        Decoded Belief.

    Raises:
        ValueError: If card doesn't contain valid belief.
    """
    card = memory.get_card(card_id)

    if card.label != "learning_belief":
        raise ValueError(f"Card {card_id} is not a learning_belief (label={card.label})")

    # Find belief buffer
    belief_buf = None
    for buf in card.buffers:
        if buf.name == "belief":
            belief_buf = buf
            break

    if belief_buf is None:
        raise ValueError(f"Card {card_id} does not contain a belief buffer")

    belief_data = json.loads(belief_buf.payload.decode("utf-8"))
    return Belief.from_dict(belief_data)


def load_beliefs(memory, belief_ids: List[str]) -> List[Belief]:
    """Load multiple beliefs by their IDs.

    Args:
        memory: ABMemory instance.
        belief_ids: List of belief IDs (not card IDs).

    Returns:
        List of Beliefs.
    """
    # Find all belief cards
    cards = memory.find_cards_by_label("learning_belief")
    beliefs = []

    for card in cards:
        for buf in card.buffers:
            if buf.name == "belief" and buf.headers.get("belief_id") in belief_ids:
                belief_data = json.loads(buf.payload.decode("utf-8"))
                beliefs.append(Belief.from_dict(belief_data))
                break

    return beliefs


def find_beliefs_for_question(memory, question_card_id: int) -> List[Tuple[int, Belief]]:
    """Find all beliefs that answer a question.

    Args:
        memory: ABMemory instance.
        question_card_id: Question card ID.

    Returns:
        List of (card_id, belief) tuples.
    """
    # Get all connections from question
    connections = memory.get_connections(source_card_id=question_card_id, relation="answered_by")
    results = []

    for conn in connections:
        try:
            belief = load_belief(memory, conn.target_card_id)
            results.append((conn.target_card_id, belief))
        except ValueError:
            # Skip invalid cards
            continue

    return results


# ============================================================================
# LearningContext Storage
# ============================================================================


def store_learning_context(
    memory,
    context: LearningContext,
    moment_id: Optional[int] = None,
) -> int:
    """Store a LearningContext as a Card in AB Memory.

    Creates a card with multiple buffers:
    - context: Full JSON context
    - summary: Human-readable summary
    - metadata: Session metadata

    Args:
        memory: ABMemory instance.
        context: LearningContext to store.
        moment_id: Optional moment ID.

    Returns:
        Card ID of the stored context.
    """
    from ab.models import Buffer

    # Full context buffer
    context_json = json.dumps(context.to_dict(), indent=2).encode("utf-8")
    context_buf = Buffer(
        name="context",
        headers={
            "session_id": context.session_id,
            "mode": context.mode.value,
            "current_state": context.current_state.value,
            "type": "learning_context",
        },
        payload=context_json,
    )

    # Summary buffer
    summary_lines = [
        f"Session: {context.session_id}",
        f"Mode: {context.mode.value}",
        f"State: {context.current_state.value}",
        f"Beliefs: {len(context.beliefs_created)}",
        f"Gaps: {len(context.gaps)}",
        f"Evidence: {len(context.evidence_collected)}",
    ]
    summary = "\n".join(summary_lines)
    summary_buf = Buffer(
        name="summary",
        headers={"type": "text"},
        payload=summary.encode("utf-8"),
    )

    card = memory.store_card(
        label="learning_context",
        buffers=[context_buf, summary_buf],
        moment_id=moment_id,
        master_input=context.session_id,
        master_output=context.current_state.value,
        track="awareness",
    )

    return card.id


def load_learning_context(memory, card_id: int) -> LearningContext:
    """Load a LearningContext from AB Memory.

    Args:
        memory: ABMemory instance.
        card_id: ID of the card to load.

    Returns:
        Decoded LearningContext.

    Raises:
        ValueError: If card doesn't contain valid context.
    """
    card = memory.get_card(card_id)

    if card.label != "learning_context":
        raise ValueError(f"Card {card_id} is not a learning_context (label={card.label})")

    # Find context buffer
    context_buf = None
    for buf in card.buffers:
        if buf.name == "context":
            context_buf = buf
            break

    if context_buf is None:
        raise ValueError(f"Card {card_id} does not contain a context buffer")

    context_data = json.loads(context_buf.payload.decode("utf-8"))
    return LearningContext.from_dict(context_data)


def find_learning_sessions(memory, mode: Optional[str] = None) -> List[Tuple[int, Dict[str, Any]]]:
    """Find all learning sessions (contexts).

    Args:
        memory: ABMemory instance.
        mode: Optional mode filter ("INGEST" or "EXPLORE").

    Returns:
        List of (card_id, session_summary) tuples.
    """
    cards = memory.find_cards_by_label("learning_context")
    results = []

    for card in cards:
        for buf in card.buffers:
            if buf.name == "context":
                headers = buf.headers
                session_mode = headers.get("mode")

                # Filter by mode if specified
                if mode is None or session_mode == mode:
                    results.append((
                        card.id,
                        {
                            "session_id": headers.get("session_id"),
                            "mode": session_mode,
                            "current_state": headers.get("current_state"),
                        }
                    ))
                break

    return results


# ============================================================================
# Batch Operations
# ============================================================================


def store_learning_session_full(
    memory,
    context: LearningContext,
    moment_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Store a complete learning session with all artifacts.

    This is a convenience function that stores the context and creates
    connections to all related questions, evidence, and beliefs.

    Args:
        memory: ABMemory instance.
        context: LearningContext with all artifacts.
        moment_id: Optional moment ID.

    Returns:
        Dictionary with card IDs:
        {
            "context_card_id": int,
            "question_card_ids": {question_id: card_id},
            "evidence_card_ids": {evidence_id: card_id},
            "belief_card_ids": {belief_id: card_id},
        }
    """
    # Store context
    context_card_id = store_learning_context(memory, context, moment_id)

    # Store focus question if present
    question_card_ids = {}
    if context.focus_question:
        q_card_id = store_question(memory, context.focus_question, moment_id)
        question_card_ids[context.focus_question.id] = q_card_id

        # Link context to question
        memory.create_connection(
            source_card_id=context_card_id,
            target_card_id=q_card_id,
            relation="contains_question",
        )

    # Store all evidence
    evidence_card_ids = {}
    for evidence in context.evidence_collected:
        e_card_id = store_evidence(memory, evidence, None, moment_id)
        evidence_card_ids[evidence.id] = e_card_id

        # Link context to evidence
        memory.create_connection(
            source_card_id=context_card_id,
            target_card_id=e_card_id,
            relation="contains_evidence",
        )

    # Store all beliefs with connections
    belief_card_ids = {}
    for belief in context.beliefs_created:
        # Get question card ID
        q_card_id = question_card_ids.get(belief.question_id)
        if q_card_id is None:
            # Question not in focus, skip linking
            continue

        # Get evidence card IDs
        e_card_ids = [evidence_card_ids[eid] for eid in belief.evidence_ids if eid in evidence_card_ids]

        # Store belief with connections
        b_card_id = store_belief(memory, belief, q_card_id, e_card_ids, moment_id)
        belief_card_ids[belief.id] = b_card_id

        # Link context to belief
        memory.create_connection(
            source_card_id=context_card_id,
            target_card_id=b_card_id,
            relation="contains_belief",
        )

    return {
        "context_card_id": context_card_id,
        "question_card_ids": question_card_ids,
        "evidence_card_ids": evidence_card_ids,
        "belief_card_ids": belief_card_ids,
    }
