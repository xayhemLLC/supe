"""End-to-End Reality Proof Composites.

High-value composite primitives that combine observation, action,
and validation to prove real-world states.
"""

from .lint_passing import prove_lint_passing, LintProofResult
from .tests_passing import prove_tests_passing, TestProofResult
from .script_success import prove_script_success, ScriptProofResult
from .llm_execution import (
    prove_llm_task,
    save_llm_proof,
    load_llm_proof,
    verify_proof_chain,
    LLMExecutionProof,
)

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
