"""End-to-End Reality Proof Composites.

High-value composite primitives that combine observation, action,
and validation to prove real-world states.
"""

from .lint_passing import LintProofResult, prove_lint_passing
from .llm_execution import (
    LLMExecutionProof,
    load_llm_proof,
    prove_llm_task,
    save_llm_proof,
    verify_proof_chain,
)
from .script_success import ScriptProofResult, prove_script_success
from .tests_passing import TestProofResult, prove_tests_passing

__all__ = [
    "prove_lint_passing",
    "LintProofResult",
    "prove_tests_passing",
    "TestProofResult",
    "prove_script_success",
    "ScriptProofResult",
    "prove_llm_task",
    "save_llm_proof",
    "load_llm_proof",
    "verify_proof_chain",
    "LLMExecutionProof",
]
