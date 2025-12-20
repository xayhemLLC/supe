"""Core data models for the learning system.

Defines the fundamental data structures used throughout the unified
INGEST + EXPLORE learning state machine.

Key abstractions:
- Question: Learning questions with metadata
- Evidence: Citations and proof of knowledge
- CornellNote: INGEST mode knowledge representation
- Theorem: EXPLORE mode knowledge representation
- Belief: Unified wrapper for both modes
- LearningContext: State machine execution context
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .types import (
    ID,
    Timestamp,
    Confidence,
    Mode,
    QuestionType,
    QuestionStatus,
    EvidenceSource,
    TheoremStatus,
    LearningState,
)


# ============================================================================
# Questions
# ============================================================================


@dataclass
class Question:
    """A learning question with metadata.

    Questions drive the learning process. They can be manually specified
    or automatically generated from content analysis.
    """

    id: ID
    text: str
    question_type: QuestionType
    status: QuestionStatus = QuestionStatus.OPEN
    priority: int = 0
    created_at: Timestamp = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    answered_at: Optional[Timestamp] = None
    source: str = ""  # Where the question came from
    related_concepts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "question_type": self.question_type.value,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at,
            "answered_at": self.answered_at,
            "source": self.source,
            "related_concepts": self.related_concepts,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Question":
        """Create Question from dictionary."""
        return cls(
            id=ID(data["id"]),
            text=data["text"],
            question_type=QuestionType(data["question_type"]),
            status=QuestionStatus(data.get("status", "OPEN")),
            priority=data.get("priority", 0),
            created_at=Timestamp(data.get("created_at", int(datetime.now().timestamp() * 1000))),
            answered_at=Timestamp(data["answered_at"]) if data.get("answered_at") else None,
            source=data.get("source", ""),
            related_concepts=data.get("related_concepts", []),
        )

    @classmethod
    def create(cls, text: str, question_type: QuestionType, source: str = "") -> "Question":
        """Factory method to create a new question."""
        return cls(
            id=ID(str(uuid4())),
            text=text,
            question_type=question_type,
            source=source,
        )


# ============================================================================
# Evidence
# ============================================================================


@dataclass
class Evidence:
    """Evidence supporting a belief or answer.

    Evidence can come from documentation, experiments, model checking,
    or formal proofs. Each piece of evidence must be traceable.
    """

    id: ID
    text: str
    source: EvidenceSource
    citations: List[str] = field(default_factory=list)  # URLs, file paths, proof hashes
    validated: bool = False
    validation_method: str = ""  # e.g., "tascer_proof", "manual_verification"
    confidence: Confidence = Confidence(1.0)
    created_at: Timestamp = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "source": self.source.value,
            "citations": self.citations,
            "validated": self.validated,
            "validation_method": self.validation_method,
            "confidence": float(self.confidence),
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Evidence":
        """Create Evidence from dictionary."""
        return cls(
            id=ID(data["id"]),
            text=data["text"],
            source=EvidenceSource(data["source"]),
            citations=data.get("citations", []),
            validated=data.get("validated", False),
            validation_method=data.get("validation_method", ""),
            confidence=Confidence(data.get("confidence", 1.0)),
            created_at=Timestamp(data.get("created_at", int(datetime.now().timestamp() * 1000))),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def create(cls, text: str, source: EvidenceSource, citations: List[str]) -> "Evidence":
        """Factory method to create new evidence."""
        return cls(
            id=ID(str(uuid4())),
            text=text,
            source=source,
            citations=citations,
        )


# ============================================================================
# INGEST Mode: Cornell Notes
# ============================================================================


@dataclass
class CornellNote:
    """Cornell-style note for INGEST mode learning.

    Structure:
    - Cue: The question or keyword
    - Notes: Detailed answer with examples
    - Summary: Conceptual and operational summaries
    """

    cue: str  # The question
    notes: str  # Detailed notes
    examples: List[str] = field(default_factory=list)
    conceptual_summary: str = ""
    operational_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "cue": self.cue,
            "notes": self.notes,
            "examples": self.examples,
            "conceptual_summary": self.conceptual_summary,
            "operational_summary": self.operational_summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CornellNote":
        """Create CornellNote from dictionary."""
        return cls(
            cue=data["cue"],
            notes=data["notes"],
            examples=data.get("examples", []),
            conceptual_summary=data.get("conceptual_summary", ""),
            operational_summary=data.get("operational_summary", ""),
        )


# ============================================================================
# EXPLORE Mode: Theorems
# ============================================================================


@dataclass
class Theorem:
    """Mathematical theorem for EXPLORE mode learning.

    Represents a conjecture, proven theorem, or disproven hypothesis
    discovered through experimental exploration.
    """

    statement: str
    proof: str
    status: TheoremStatus = TheoremStatus.CONJECTURE
    counterexample: Optional[str] = None
    experiments: List[Dict[str, Any]] = field(default_factory=list)
    properties_validated: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "statement": self.statement,
            "proof": self.proof,
            "status": self.status.value,
            "counterexample": self.counterexample,
            "experiments": self.experiments,
            "properties_validated": self.properties_validated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Theorem":
        """Create Theorem from dictionary."""
        return cls(
            statement=data["statement"],
            proof=data["proof"],
            status=TheoremStatus(data.get("status", "CONJECTURE")),
            counterexample=data.get("counterexample"),
            experiments=data.get("experiments", []),
            properties_validated=data.get("properties_validated", []),
        )


# ============================================================================
# Unified Belief
# ============================================================================


@dataclass
class Belief:
    """Unified knowledge representation for both INGEST and EXPLORE modes.

    A Belief wraps either a CornellNote (INGEST) or Theorem (EXPLORE)
    and provides a common interface for storage and retrieval.
    """

    id: ID
    question_id: ID  # Links to the question this belief answers
    mode: Mode
    content: Any  # CornellNote or Theorem
    confidence: Confidence
    evidence_ids: List[ID] = field(default_factory=list)
    created_at: Timestamp = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    last_reviewed_at: Optional[Timestamp] = None
    next_review_at: Optional[Timestamp] = None
    review_interval_days: int = 1  # For spaced repetition

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        # Serialize content based on type
        if isinstance(self.content, CornellNote):
            content_dict = self.content.to_dict()
            content_type = "cornell_note"
        elif isinstance(self.content, Theorem):
            content_dict = self.content.to_dict()
            content_type = "theorem"
        else:
            content_dict = self.content
            content_type = "unknown"

        return {
            "id": self.id,
            "question_id": self.question_id,
            "mode": self.mode.value,
            "content_type": content_type,
            "content": content_dict,
            "confidence": float(self.confidence),
            "evidence_ids": self.evidence_ids,
            "created_at": self.created_at,
            "last_reviewed_at": self.last_reviewed_at,
            "next_review_at": self.next_review_at,
            "review_interval_days": self.review_interval_days,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Belief":
        """Create Belief from dictionary."""
        # Deserialize content based on type
        content_type = data.get("content_type", "unknown")
        if content_type == "cornell_note":
            content = CornellNote.from_dict(data["content"])
        elif content_type == "theorem":
            content = Theorem.from_dict(data["content"])
        else:
            content = data["content"]

        return cls(
            id=ID(data["id"]),
            question_id=ID(data["question_id"]),
            mode=Mode(data["mode"]),
            content=content,
            confidence=Confidence(data["confidence"]),
            evidence_ids=[ID(eid) for eid in data.get("evidence_ids", [])],
            created_at=Timestamp(data.get("created_at", int(datetime.now().timestamp() * 1000))),
            last_reviewed_at=Timestamp(data["last_reviewed_at"]) if data.get("last_reviewed_at") else None,
            next_review_at=Timestamp(data["next_review_at"]) if data.get("next_review_at") else None,
            review_interval_days=data.get("review_interval_days", 1),
        )

    @classmethod
    def create_from_cornell_note(
        cls,
        question_id: ID,
        note: CornellNote,
        confidence: Confidence,
        evidence_ids: List[ID],
    ) -> "Belief":
        """Factory method for INGEST mode beliefs."""
        return cls(
            id=ID(str(uuid4())),
            question_id=question_id,
            mode=Mode.INGEST,
            content=note,
            confidence=confidence,
            evidence_ids=evidence_ids,
        )

    @classmethod
    def create_from_theorem(
        cls,
        question_id: ID,
        theorem: Theorem,
        confidence: Confidence,
        evidence_ids: List[ID],
    ) -> "Belief":
        """Factory method for EXPLORE mode beliefs."""
        return cls(
            id=ID(str(uuid4())),
            question_id=question_id,
            mode=Mode.EXPLORE,
            content=theorem,
            confidence=confidence,
            evidence_ids=evidence_ids,
        )


# ============================================================================
# Learning Context
# ============================================================================


@dataclass
class LearningContext:
    """State machine execution context.

    Tracks the current state of a learning session, including the focus
    question, accumulated evidence, beliefs, and identified gaps.
    """

    session_id: ID
    mode: Mode
    current_state: LearningState
    focus_question: Optional[Question] = None
    evidence_collected: List[Evidence] = field(default_factory=list)
    beliefs_created: List[Belief] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    followup_questions: List[Question] = field(default_factory=list)
    created_at: Timestamp = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    updated_at: Timestamp = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "mode": self.mode.value,
            "current_state": self.current_state.value,
            "focus_question": self.focus_question.to_dict() if self.focus_question else None,
            "evidence_collected": [e.to_dict() for e in self.evidence_collected],
            "beliefs_created": [b.to_dict() for b in self.beliefs_created],
            "gaps": self.gaps,
            "followup_questions": [q.to_dict() for q in self.followup_questions],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningContext":
        """Create LearningContext from dictionary."""
        return cls(
            session_id=ID(data["session_id"]),
            mode=Mode(data["mode"]),
            current_state=LearningState(data["current_state"]),
            focus_question=Question.from_dict(data["focus_question"]) if data.get("focus_question") else None,
            evidence_collected=[Evidence.from_dict(e) for e in data.get("evidence_collected", [])],
            beliefs_created=[Belief.from_dict(b) for b in data.get("beliefs_created", [])],
            gaps=data.get("gaps", []),
            followup_questions=[Question.from_dict(q) for q in data.get("followup_questions", [])],
            created_at=Timestamp(data.get("created_at", int(datetime.now().timestamp() * 1000))),
            updated_at=Timestamp(data.get("updated_at", int(datetime.now().timestamp() * 1000))),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def create(cls, mode: Mode, initial_question: Optional[Question] = None) -> "LearningContext":
        """Factory method to create new learning context."""
        return cls(
            session_id=ID(str(uuid4())),
            mode=mode,
            current_state=LearningState.INIT,
            focus_question=initial_question,
        )

    def update_state(self, new_state: LearningState) -> None:
        """Update current state and timestamp."""
        self.current_state = new_state
        self.updated_at = Timestamp(int(datetime.now().timestamp() * 1000))

    def add_evidence(self, evidence: Evidence) -> None:
        """Add evidence to collection."""
        self.evidence_collected.append(evidence)
        self.updated_at = Timestamp(int(datetime.now().timestamp() * 1000))

    def add_belief(self, belief: Belief) -> None:
        """Add belief to collection."""
        self.beliefs_created.append(belief)
        self.updated_at = Timestamp(int(datetime.now().timestamp() * 1000))

    def add_gap(self, gap: str) -> None:
        """Add identified knowledge gap."""
        if gap not in self.gaps:
            self.gaps.append(gap)
            self.updated_at = Timestamp(int(datetime.now().timestamp() * 1000))

    def add_followup_question(self, question: Question) -> None:
        """Add followup question for future learning."""
        self.followup_questions.append(question)
        self.updated_at = Timestamp(int(datetime.now().timestamp() * 1000))
