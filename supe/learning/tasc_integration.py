"""Tasc/Tascer integration utilities for the learning system.

Bridges learning sessions with the Tasc task management and proof-of-work
validation system. Enables learning sessions to be tracked as Tascs with
cryptographic proof of learning outcomes.

Key functions:
- create_learning_tasc: Convert learning question → Tasc
- create_learning_validation: Convert learning results → LearningTascValidation
- store_learning_tasc_execution: Store validated learning in execution track
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from tasc.tasc import Tasc
from tascer.llm_proof import ProofType, TaskStatus
from tascer.contracts import LearningTascValidation
from tascer.proofs.learning_proof import prove_learning_session, prove_experiment_success
from tascer.ab_storage import store_tasc_execution

from .models import Belief, Question, Evidence, LearningContext
from .types import Mode


# ============================================================================
# Tasc Creation
# ============================================================================


def create_learning_tasc(
    question: str,
    mode: Mode,
    source_url: Optional[str] = None,
    dependencies: Optional[List[str]] = None,
) -> Tasc:
    """Create a Tasc for a learning session.

    Converts a learning question into a validated task that can be
    tracked through the Tasc system.

    Args:
        question: The learning question.
        mode: INGEST or EXPLORE mode.
        source_url: Optional source URL for learning material.
        dependencies: Optional list of dependency Tasc IDs.

    Returns:
        Tasc configured for learning validation.
    """
    # Generate tasc ID from question hash
    tasc_id = f"learn_{hashlib.sha256(question.encode()).hexdigest()[:8]}"

    # Determine testing instructions based on mode
    if mode == Mode.INGEST:
        testing_instructions = f"python -m supe learn '{question}' --mode=ingest"
    else:
        testing_instructions = f"python -m supe learn '{question}' --mode=explore"

    return Tasc(
        id=tasc_id,
        status=TaskStatus.LEARNING.value,
        title=f"Learn: {question}",
        additional_notes=source_url or "",
        testing_instructions=testing_instructions,
        desired_outcome="Confidence > 0.7, gaps < 5, key questions answered",
        dependencies=dependencies or [],
        learning_mode=mode.value,
        confidence_score=None,  # Filled after validation
        gaps=[],  # Filled after validation
        unresolved_questions=[],  # Filled after validation
        review_schedule=None,  # Filled after validation
        related_session_id=None,  # Filled after validation
    )


def create_learning_tasc_from_question(
    question: Question,
    mode: Mode,
    source_url: Optional[str] = None,
) -> Tasc:
    """Create a Tasc from a Question object.

    Args:
        question: Question object.
        mode: INGEST or EXPLORE mode.
        source_url: Optional source URL.

    Returns:
        Tasc configured for learning.
    """
    return create_learning_tasc(
        question=question.text,
        mode=mode,
        source_url=source_url or question.source,
    )


# ============================================================================
# Validation Creation
# ============================================================================


def create_learning_validation(
    session_id: str,
    beliefs: List[Belief],
    gaps: List[str],
    mode: Mode,
    unresolved_questions: Optional[List[str]] = None,
    min_confidence: float = 0.7,
    max_gaps: int = 5,
    min_questions_answered: int = 1,
) -> LearningTascValidation:
    """Create LearningTascValidation from learning results.

    Converts learning session outcomes into a validated proof using
    the learning proof generator.

    Args:
        session_id: Learning session ID.
        beliefs: Beliefs created during session.
        gaps: Identified knowledge gaps.
        mode: Learning mode.
        unresolved_questions: Optional list of unresolved questions.
        min_confidence: Minimum confidence threshold.
        max_gaps: Maximum allowed gaps.
        min_questions_answered: Minimum questions that must be answered.

    Returns:
        LearningTascValidation with proof hash.
    """
    # Prepare session data for proof generator
    session_data = {
        "session_id": session_id,
        "mode": mode.value,
        "beliefs": [
            {
                "content": str(b.content),
                "confidence": float(b.confidence),
            }
            for b in beliefs
        ],
        "gaps": gaps,
        "questions": [
            {
                "text": f"Question for belief {b.id}",
                "answered": True,
            }
            for b in beliefs
        ],
        "experiments": [],  # TODO: Add experiment support for EXPLORE mode
    }

    # Generate proof
    proof_result = prove_learning_session(
        session_data,
        min_confidence=min_confidence,
        max_gaps=max_gaps,
        min_questions_answered=min_questions_answered,
    )

    # Convert to LearningTascValidation
    return LearningTascValidation(
        tasc_id=session_id,
        validated=proof_result.proven,
        proof_hash=proof_result.proof_hash,
        gate_results=proof_result.gate_results,
        timestamp=datetime.now().isoformat(),
        duration_ms=proof_result.duration_ms,
        # Learning-specific fields
        confidence_level=proof_result.confidence_level,
        questions_answered=proof_result.questions_answered,
        questions_total=proof_result.questions_total,
        experiments_passed=proof_result.experiments_passed,
        experiments_failed=proof_result.experiments_failed,
        gaps_identified=proof_result.gaps_identified,
        next_review_at=proof_result.next_review_at,
        mode=mode.value,
    )


def create_learning_validation_from_context(
    context: LearningContext,
    min_confidence: float = 0.7,
    max_gaps: int = 5,
) -> LearningTascValidation:
    """Create validation from LearningContext.

    Convenience function that extracts beliefs and gaps from context.

    Args:
        context: LearningContext with session results.
        min_confidence: Minimum confidence threshold.
        max_gaps: Maximum allowed gaps.

    Returns:
        LearningTascValidation with proof hash.
    """
    unresolved = [q.text for q in context.followup_questions]

    return create_learning_validation(
        session_id=context.session_id,
        beliefs=context.beliefs_created,
        gaps=context.gaps,
        mode=context.mode,
        unresolved_questions=unresolved,
        min_confidence=min_confidence,
        max_gaps=max_gaps,
    )


# ============================================================================
# Storage Integration
# ============================================================================


def store_learning_tasc_execution(
    memory,
    tasc: Tasc,
    validation: LearningTascValidation,
    session_card_id: int,
    moment_id: Optional[int] = None,
) -> int:
    """Store learning Tasc execution linked to session card.

    Creates a traceable chain:
    Tasc (task) → TascValidation (proof) → LearningSession Card (details)

    Uses the existing store_tasc_execution function from tascer.ab_storage.

    Args:
        memory: AB Memory instance.
        tasc: Learning Tasc.
        validation: Validation result.
        session_card_id: Card ID of detailed learning session.
        moment_id: Optional moment ID.

    Returns:
        Execution card ID.
    """
    # Store execution in "execution" track with link to session
    exec_card_id = store_tasc_execution(
        memory,
        tasc_id=tasc.id,
        validation=validation,
        linked_awareness_id=session_card_id,  # Link to session details
        moment_id=moment_id,
    )

    # Create explicit connection
    memory.create_connection(
        source_card_id=exec_card_id,
        target_card_id=session_card_id,
        relation="validated_learning_session",
    )

    return exec_card_id


def update_tasc_with_results(
    tasc: Tasc,
    validation: LearningTascValidation,
    session_id: str,
    unresolved_questions: Optional[List[str]] = None,
) -> Tasc:
    """Update Tasc with learning results.

    Fills in the learning-specific fields after validation.

    Args:
        tasc: Original learning Tasc.
        validation: Validation result with metrics.
        session_id: Learning session ID.
        unresolved_questions: Optional unresolved questions.

    Returns:
        Updated Tasc with results.
    """
    # Update learning fields
    tasc.confidence_score = validation.confidence_level
    tasc.gaps = validation.gaps_identified
    tasc.unresolved_questions = unresolved_questions or []
    tasc.review_schedule = {
        "next_review": validation.next_review_at,
        "interval_days": "1",  # TODO: Calculate based on spaced repetition
    }
    tasc.related_session_id = session_id

    # Update status based on validation
    if validation.validated:
        tasc.status = TaskStatus.PROVEN.value
    else:
        tasc.status = TaskStatus.UNCERTAIN.value

    # Update proof fields
    tasc.proof_hash = validation.proof_hash
    tasc.validated_at = validation.timestamp

    return tasc


# ============================================================================
# Full Workflow Integration
# ============================================================================


def process_learning_session_as_tasc(
    memory,
    context: LearningContext,
    session_card_id: int,
    source_url: Optional[str] = None,
    min_confidence: float = 0.7,
    max_gaps: int = 5,
    moment_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Full workflow: Context → Tasc → Validation → Storage.

    This is the main integration function that processes a complete
    learning session through the Tasc/Tascer validation pipeline.

    Args:
        memory: AB Memory instance.
        context: LearningContext with session results.
        session_card_id: Card ID where session is stored.
        source_url: Optional source URL.
        min_confidence: Minimum confidence threshold.
        max_gaps: Maximum allowed gaps.
        moment_id: Optional moment ID.

    Returns:
        Dictionary with:
        {
            "tasc": Tasc object,
            "validation": LearningTascValidation,
            "execution_card_id": int,
            "success": bool,
        }
    """
    # 1. Create learning Tasc
    if context.focus_question:
        tasc = create_learning_tasc_from_question(
            question=context.focus_question,
            mode=context.mode,
            source_url=source_url,
        )
    else:
        # Fallback: create generic tasc
        tasc = create_learning_tasc(
            question=f"Learning session {context.session_id}",
            mode=context.mode,
            source_url=source_url,
        )

    # 2. Create validation from context
    validation = create_learning_validation_from_context(
        context,
        min_confidence=min_confidence,
        max_gaps=max_gaps,
    )

    # 3. Update tasc with results
    unresolved = [q.text for q in context.followup_questions]
    tasc = update_tasc_with_results(
        tasc,
        validation,
        context.session_id,
        unresolved,
    )

    # 4. Store execution in execution track
    exec_card_id = store_learning_tasc_execution(
        memory,
        tasc,
        validation,
        session_card_id,
        moment_id,
    )

    return {
        "tasc": tasc,
        "validation": validation,
        "execution_card_id": exec_card_id,
        "success": validation.validated,
        "proof_hash": validation.proof_hash,
        "confidence": validation.confidence_level,
        "gaps_count": len(validation.gaps_identified),
    }


# ============================================================================
# Learning Curriculum Support
# ============================================================================


def create_learning_curriculum(
    title: str,
    questions: List[str],
    mode: Mode,
    dependencies: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, Any]:
    """Create a learning curriculum as a TascPlan.

    Organizes multiple learning questions into a structured plan
    with dependency tracking.

    Args:
        title: Curriculum title.
        questions: List of learning questions.
        mode: Learning mode for all questions.
        dependencies: Optional question → [dependencies] mapping.

    Returns:
        Dictionary suitable for create_plan() from tascer.llm_proof.
    """
    tascs = []
    deps = dependencies or {}

    for i, question in enumerate(questions):
        tasc_id = f"learn_{hashlib.sha256(question.encode()).hexdigest()[:8]}"

        tascs.append({
            "id": tasc_id,
            "title": f"Learn: {question}",
            "testing_instructions": f"python -m supe learn '{question}' --mode={mode.value.lower()}",
            "desired_outcome": "Confidence > 0.7, gaps < 5",
            "dependencies": deps.get(question, []),
            "learning_mode": mode.value,
        })

    return {
        "title": title,
        "description": f"Learning curriculum with {len(questions)} topics",
        "tascs": tascs,
    }


def track_curriculum_progress(
    memory,
    plan_id: str,
) -> Dict[str, Any]:
    """Track progress of a learning curriculum.

    Args:
        memory: AB Memory instance.
        plan_id: Plan identifier.

    Returns:
        Dictionary with progress metrics:
        {
            "total": int,
            "completed": int,
            "in_progress": int,
            "not_started": int,
            "avg_confidence": float,
            "total_gaps": int,
        }
    """
    from tascer.ab_storage import find_executions_by_plan

    executions = find_executions_by_plan(memory, plan_id)

    total = len(executions)
    completed = sum(1 for _, ex in executions if ex.get("validated"))
    in_progress = 0  # TODO: Determine from status
    not_started = total - completed - in_progress

    # Calculate aggregate metrics (would need to load full validations)
    avg_confidence = 0.0  # TODO: Calculate from validations
    total_gaps = 0  # TODO: Calculate from validations

    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "not_started": not_started,
        "avg_confidence": avg_confidence,
        "total_gaps": total_gaps,
        "completion_rate": completed / total if total > 0 else 0.0,
    }
