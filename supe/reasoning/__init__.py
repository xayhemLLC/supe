"""Adaptive reasoning system for supe.

This package provides meta-cognitive capabilities that allow supe to:
- Classify problems by type
- Identify required reasoning patterns
- Synthesize new solving strategies
- Extend its own capabilities dynamically

Subagents (supe.reasoning.subagents):
- ProblemSolver: TASC-format structured reasoning with step validation
- Critiquer: Reviews reasoning for errors before committing
- Citer: Collects and validates evidence for claims
- ReasoningPipeline: Orchestrates all three subagents
"""

from supe.reasoning.problem_types import (
    ProblemClassifier,
    ProblemSignature,
    ProblemDomain,
    ReasoningPattern,
)

# Subagents
from supe.reasoning.subagents import (
    ReasoningPipeline,
    PipelineResult,
    ProblemSolver,
    TASC,
    Critiquer,
    CritiqueResult,
    Citer,
    GatheredEvidence,
)

__all__ = [
    # Problem classification
    "ProblemClassifier",
    "ProblemSignature",
    "ProblemDomain",
    "ReasoningPattern",
    # Subagents
    "ReasoningPipeline",
    "PipelineResult",
    "ProblemSolver",
    "TASC",
    "Critiquer",
    "CritiqueResult",
    "Citer",
    "GatheredEvidence",
]
