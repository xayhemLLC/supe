"""Reasoning subagents for Supe.

Three specialized subagents that form a validation pipeline:

1. ProblemSolver: TASC-format structured reasoning with step validation
2. Critiquer: Reviews reasoning for errors before committing
3. Citer: Collects and validates evidence for claims

Pipeline:
    Problem → [ProblemSolver] → Solution → [Critiquer] → Validated → [Citer] → Cited

Usage:
    from supe.reasoning.subagents import ReasoningPipeline

    pipeline = ReasoningPipeline(memory)
    result = await pipeline.run("Find f(g(2)) where f(x)=x²+1, g(x)=x-2")

    if result.approved:
        print(f"Answer: {result.tasc.proposed_answer}")
"""

from .problem_solver import ProblemSolver, TASC, ReasoningStep, ValidationCheckpoint
from .critiquer import Critiquer, CritiqueResult, ErrorType
from .citer import Citer, GatheredEvidence
from .pipeline import ReasoningPipeline, PipelineResult, solve_with_validation

__all__ = [
    # Pipeline
    "ReasoningPipeline",
    "PipelineResult",
    "solve_with_validation",
    # ProblemSolver
    "ProblemSolver",
    "TASC",
    "ReasoningStep",
    "ValidationCheckpoint",
    # Critiquer
    "Critiquer",
    "CritiqueResult",
    "ErrorType",
    # Citer
    "Citer",
    "GatheredEvidence",
]
