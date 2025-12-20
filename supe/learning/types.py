"""Core types and enums for the learning system.

Follows the design spec for unified INGEST + EXPLORE learning.
"""

from enum import Enum
from typing import NewType

# Type aliases
ID = NewType('ID', str)
Timestamp = NewType('Timestamp', int)  # ms since epoch
Confidence = NewType('Confidence', float)  # 0.0 - 1.0


class Mode(Enum):
    """Learning mode."""
    INGEST = "INGEST"  # Document/API learning
    EXPLORE = "EXPLORE"  # Math/system exploration


class QuestionType(Enum):
    """Types of questions the agent can ask."""
    CORE_CONCEPT = "CORE_CONCEPT"      # What is it?
    OPERATIONAL = "OPERATIONAL"        # How do I use it?
    CONSTRAINT = "CONSTRAINT"          # What breaks?
    IMPACT = "IMPACT"                  # Why care?
    MATH_STRUCTURE = "MATH_STRUCTURE"  # Math patterns/conjectures
    META = "META"                      # Questions about learning itself


class QuestionStatus(Enum):
    """Status of a question."""
    OPEN = "OPEN"
    ANSWERED = "ANSWERED"
    DEFERRED = "DEFERRED"


class EvidenceSource(Enum):
    """Where evidence came from."""
    DOC = "DOC"                    # From documentation
    EXPERIMENT = "EXPERIMENT"      # From running experiments
    MODEL_CHECK = "MODEL_CHECK"    # From model checking
    PROOF = "PROOF"                # From formal proof


class TheoremStatus(Enum):
    """Status of a mathematical theorem."""
    CONJECTURE = "CONJECTURE"
    PROVEN = "PROVEN"
    DISPROVEN = "DISPROVEN"


class LearningState(Enum):
    """States in the learning state machine."""
    INIT = "INIT"
    SELECT_FOCUS_QUESTION = "SELECT_FOCUS_QUESTION"
    PLAN_EVIDENCE_STRATEGY = "PLAN_EVIDENCE_STRATEGY"
    INGEST_DOC = "INGEST_DOC"
    EXPLORE_ENV = "EXPLORE_ENV"
    INTEGRATE_KNOWLEDGE = "INTEGRATE_KNOWLEDGE"
    SELF_TEST = "SELF_TEST"
    EVALUATE_AND_UPDATE_CONFIDENCE = "EVALUATE_AND_UPDATE_CONFIDENCE"
    GENERATE_FOLLOWUP_QUESTIONS = "GENERATE_FOLLOWUP_QUESTIONS"
    SCHEDULE_REVIEW = "SCHEDULE_REVIEW"
    IDLE_OR_TERMINATE = "IDLE_OR_TERMINATE"
