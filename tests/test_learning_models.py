"""Tests for learning system data models (Phase 1.1)."""

import pytest
from datetime import datetime

from supe.learning.models import (
    Question, Evidence, CornellNote, Theorem, Belief, LearningContext
)
from supe.learning.types import (
    Mode, QuestionType, QuestionStatus, EvidenceSource, TheoremStatus, LearningState
)


# ============================================================================
# Question Tests
# ============================================================================

def test_question_creation():
    """Question.create() should create valid question."""
    q = Question.create(
        text="What is React?",
        question_type=QuestionType.CORE_CONCEPT,
        source="test",
    )
    assert q.id is not None
    assert q.text == "What is React?"
    assert q.question_type == QuestionType.CORE_CONCEPT
    assert q.status == QuestionStatus.OPEN
    assert q.source == "test"


def test_question_serialization():
    """Question should serialize to dict and back."""
    q = Question.create("Test question", QuestionType.OPERATIONAL)

    # Serialize
    data = q.to_dict()
    assert data["text"] == "Test question"
    assert data["question_type"] == "OPERATIONAL"

    # Deserialize
    q2 = Question.from_dict(data)
    assert q2.text == q.text
    assert q2.question_type == q.question_type
    assert q2.id == q.id


# ============================================================================
# Evidence Tests
# ============================================================================

def test_evidence_creation():
    """Evidence.create() should create valid evidence."""
    e = Evidence.create(
        text="Test evidence",
        source=EvidenceSource.DOC,
        citations=["http://example.com"],
    )
    assert e.id is not None
    assert e.text == "Test evidence"
    assert e.source == EvidenceSource.DOC
    assert e.citations == ["http://example.com"]
    assert not e.validated


def test_evidence_serialization():
    """Evidence should serialize to dict and back."""
    e = Evidence.create("Evidence text", EvidenceSource.EXPERIMENT, ["citation1"])
    e.validated = True
    e.validation_method = "test"

    # Serialize
    data = e.to_dict()
    assert data["text"] == "Evidence text"
    assert data["validated"] is True

    # Deserialize
    e2 = Evidence.from_dict(data)
    assert e2.text == e.text
    assert e2.validated == e.validated
    assert e2.validation_method == e.validation_method


# ============================================================================
# CornellNote Tests
# ============================================================================

def test_cornell_note_creation():
    """CornellNote should be creatable."""
    note = CornellNote(
        cue="What is X?",
        notes="X is...",
        examples=["example1"],
        conceptual_summary="X is a concept",
        operational_summary="Use X by...",
    )
    assert note.cue == "What is X?"
    assert len(note.examples) == 1


def test_cornell_note_serialization():
    """CornellNote should serialize to dict and back."""
    note = CornellNote(
        cue="Test cue",
        notes="Test notes",
        examples=["ex1", "ex2"],
    )

    data = note.to_dict()
    note2 = CornellNote.from_dict(data)

    assert note2.cue == note.cue
    assert note2.examples == note.examples


# ============================================================================
# Theorem Tests
# ============================================================================

def test_theorem_creation():
    """Theorem should be creatable."""
    theorem = Theorem(
        statement="X is true",
        proof="Proven by...",
        status=TheoremStatus.PROVEN,
    )
    assert theorem.statement == "X is true"
    assert theorem.status == TheoremStatus.PROVEN


def test_theorem_with_counterexample():
    """Theorem can have counterexample when disproven."""
    theorem = Theorem(
        statement="All X are Y",
        proof="Disproven",
        status=TheoremStatus.DISPROVEN,
        counterexample="Z is X but not Y",
    )
    assert theorem.status == TheoremStatus.DISPROVEN
    assert theorem.counterexample is not None


def test_theorem_serialization():
    """Theorem should serialize to dict and back."""
    theorem = Theorem(
        statement="Test statement",
        proof="Test proof",
        status=TheoremStatus.CONJECTURE,
        properties_validated=["prop1"],
    )

    data = theorem.to_dict()
    theorem2 = Theorem.from_dict(data)

    assert theorem2.statement == theorem.statement
    assert theorem2.status == theorem.status


# ============================================================================
# Belief Tests
# ============================================================================

def test_belief_from_cornell_note():
    """Belief can wrap a CornellNote."""
    q = Question.create("Q", QuestionType.CORE_CONCEPT)
    note = CornellNote(cue="Q", notes="A")

    belief = Belief.create_from_cornell_note(
        question_id=q.id,
        note=note,
        confidence=0.8,
        evidence_ids=[],
    )

    assert belief.mode == Mode.INGEST
    assert belief.confidence == 0.8
    assert isinstance(belief.content, CornellNote)


def test_belief_from_theorem():
    """Belief can wrap a Theorem."""
    q = Question.create("Is X true?", QuestionType.MATH_STRUCTURE)
    theorem = Theorem(statement="X is true", proof="...", status=TheoremStatus.PROVEN)

    belief = Belief.create_from_theorem(
        question_id=q.id,
        theorem=theorem,
        confidence=0.95,
        evidence_ids=[],
    )

    assert belief.mode == Mode.EXPLORE
    assert belief.confidence == 0.95
    assert isinstance(belief.content, Theorem)


def test_belief_serialization():
    """Belief should serialize to dict and back."""
    q = Question.create("Test", QuestionType.CORE_CONCEPT)
    note = CornellNote(cue="Test", notes="Answer")

    belief = Belief.create_from_cornell_note(q.id, note, 0.9, [])

    data = belief.to_dict()
    belief2 = Belief.from_dict(data)

    assert belief2.confidence == belief.confidence
    assert belief2.mode == belief.mode
    assert isinstance(belief2.content, CornellNote)


# ============================================================================
# LearningContext Tests
# ============================================================================

def test_learning_context_creation():
    """LearningContext.create() should initialize properly."""
    q = Question.create("Test", QuestionType.CORE_CONCEPT)
    context = LearningContext.create(mode=Mode.INGEST, initial_question=q)

    assert context.session_id is not None
    assert context.mode == Mode.INGEST
    assert context.current_state == LearningState.INIT
    assert context.focus_question == q


def test_learning_context_update_state():
    """Context should update state and timestamp."""
    context = LearningContext.create(Mode.INGEST)
    initial_timestamp = context.updated_at

    context.update_state(LearningState.SELECT_FOCUS_QUESTION)

    assert context.current_state == LearningState.SELECT_FOCUS_QUESTION
    assert context.updated_at >= initial_timestamp


def test_learning_context_add_evidence():
    """Context should track evidence."""
    context = LearningContext.create(Mode.INGEST)
    e = Evidence.create("Test", EvidenceSource.DOC, [])

    context.add_evidence(e)

    assert len(context.evidence_collected) == 1
    assert context.evidence_collected[0] == e


def test_learning_context_add_belief():
    """Context should track beliefs."""
    context = LearningContext.create(Mode.INGEST)
    q = Question.create("Q", QuestionType.CORE_CONCEPT)
    note = CornellNote(cue="Q", notes="A")
    belief = Belief.create_from_cornell_note(q.id, note, 0.8, [])

    context.add_belief(belief)

    assert len(context.beliefs_created) == 1


def test_learning_context_add_gap():
    """Context should track gaps."""
    context = LearningContext.create(Mode.INGEST)

    context.add_gap("Gap 1")
    context.add_gap("Gap 2")
    context.add_gap("Gap 1")  # Duplicate

    assert len(context.gaps) == 2  # Duplicates not added


def test_learning_context_serialization():
    """LearningContext should serialize to dict and back."""
    q = Question.create("Test", QuestionType.CORE_CONCEPT)
    context = LearningContext.create(Mode.EXPLORE, q)
    context.add_gap("Test gap")

    data = context.to_dict()
    context2 = LearningContext.from_dict(data)

    assert context2.session_id == context.session_id
    assert context2.mode == context.mode
    assert len(context2.gaps) == 1
    assert context2.focus_question.text == q.text
