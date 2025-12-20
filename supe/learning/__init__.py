"""Unified INGEST + EXPLORE learning system for Supe.

This module implements a question-driven, evidence-based learning system
that supports both INGEST (document learning) and EXPLORE (mathematical
experimentation) modes.

Main components:
- LearningStateMachine: Orchestrates the learning process
- Models: Question, Evidence, Belief, CornellNote, Theorem, LearningContext
- Storage: AB Memory integration for persistence
- TascIntegration: Proof-of-work validation for learning

Quick start:
    from ab.abdb import ABMemory
    from supe.learning import LearningStateMachine, Mode

    memory = ABMemory(":memory:")
    sm = LearningStateMachine(memory, mode=Mode.INGEST, debug=True)
    await sm.initialize("How do React hooks work?")
    await sm.run()

    beliefs = sm.get_beliefs()
    print(f"Created {len(beliefs)} beliefs")
"""

# Core state machine
from .state_machine import LearningStateMachine, learn

# Types and enums
from .types import (
    Mode,
    QuestionType,
    QuestionStatus,
    EvidenceSource,
    TheoremStatus,
    LearningState,
)

# Data models
from .models import (
    Question,
    Evidence,
    CornellNote,
    Theorem,
    Belief,
    LearningContext,
)

# Storage layer
from .storage import (
    store_question,
    load_question,
    store_evidence,
    load_evidence,
    store_belief,
    load_belief,
    store_learning_context,
    load_learning_context,
    store_learning_session_full,
)

# Tasc integration
from .tasc_integration import (
    create_learning_tasc,
    create_learning_validation,
    process_learning_session_as_tasc,
    create_learning_curriculum,
)

__all__ = [
    # State machine
    "LearningStateMachine",
    "learn",
    # Types
    "Mode",
    "QuestionType",
    "QuestionStatus",
    "EvidenceSource",
    "TheoremStatus",
    "LearningState",
    # Models
    "Question",
    "Evidence",
    "CornellNote",
    "Theorem",
    "Belief",
    "LearningContext",
    # Storage
    "store_question",
    "load_question",
    "store_evidence",
    "load_evidence",
    "store_belief",
    "load_belief",
    "store_learning_context",
    "load_learning_context",
    "store_learning_session_full",
    # Tasc integration
    "create_learning_tasc",
    "create_learning_validation",
    "process_learning_session_as_tasc",
    "create_learning_curriculum",
]
