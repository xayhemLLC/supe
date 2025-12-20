"""LLM Execution Proof - Prove LLM task execution.

Provides specific proof generation for LLM-driven task execution,
including structured command execution, output capture, and verification.

This module uses TascValidation from contracts for consistent validation
across the entire tascer system.
"""

import os
import json
import time
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..primitives import capture_context, run_and_observe
from ..gates import ExitCodeGate, PatternGate
from ..contracts import GateResult, TascValidation


def prove_llm_task(
    task_id: str,
    command: str,
    expected_outputs: Optional[List[str]] = None,
    validation_gates: Optional[List[str]] = None,
    cwd: Optional[str] = None,
    timeout_sec: float = 120,
    capture_context_snapshot: bool = True,
) -> TascValidation:
    """Execute a command as part of an LLM task and produce validation.
    
    This is the primary function for LLM agents to prove their work.
    
    Args:
        task_id: Identifier for the task (tasc_id)
        command: Command to execute
        expected_outputs: Files expected to exist after execution
        validation_gates: Which gates to apply (default: exit_code, no_errors)
        cwd: Working directory
        timeout_sec: Execution timeout
        capture_context_snapshot: Whether to capture full context
    
    Returns:
        TascValidation with all evidence and verification results
    """
    if cwd is None:
        cwd = os.getcwd()
    
    if validation_gates is None:
        validation_gates = ["exit_code", "no_errors"]
    
    if expected_outputs is None:
        expected_outputs = []
    
    start_time = time.time()
    
    # Optionally capture context
    context_snapshot = None
    if capture_context_snapshot:
        context = capture_context(
            tasc_id=task_id,
            repo_root=cwd,
            permissions=["terminal", "fs_read"],
        )
        context_snapshot = context.to_dict()
    
    # Execute command
    result = run_and_observe(
        command=command,
        cwd=cwd,
        timeout_sec=timeout_sec,
        shell=True,
    )
    
    duration_ms = (time.time() - start_time) * 1000
    
    # Apply gates
    gate_results = []
    
    if "exit_code" in validation_gates:
        exit_gate = ExitCodeGate(expected=[0])
        gate_results.append(exit_gate.check(result.exit_code))
    
    if "no_errors" in validation_gates:
        pattern_gate = PatternGate(denylist=[
            r"(?i)error:",
            r"(?i)exception:",
            r"(?i)fatal:",
            r"(?i)failed:",
            r"Traceback \(most recent call last\)",
        ])
        gate_results.append(pattern_gate.check(result.stdout, result.stderr))
    
    # Check expected outputs
    missing_outputs = []
    evidence_paths = []
    if expected_outputs:
        for output in expected_outputs:
            path = output if os.path.isabs(output) else os.path.join(cwd, output)
            if os.path.exists(path):
                evidence_paths.append(path)
            else:
                missing_outputs.append(output)
        
        outputs_gate = GateResult(
            gate_name="EXPECTED_OUTPUTS",
            passed=len(missing_outputs) == 0,
            message=f"{len(expected_outputs) - len(missing_outputs)}/{len(expected_outputs)} outputs found",
            evidence={"missing": missing_outputs},
        )
        gate_results.append(outputs_gate)
    
    # Determine if validated
    validated = all(g.passed for g in gate_results)
    
    # Finalize context
    if context_snapshot and capture_context_snapshot:
        context.finalize()
    
    timestamp = datetime.now().isoformat()
    
    # Create proof hash
    proof_data = {
        "tasc_id": task_id,
        "command": command,
        "exit_code": result.exit_code,
        "timestamp": timestamp,
        "validated": validated,
    }
    content = json.dumps(proof_data, sort_keys=True)
    proof_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    
    return TascValidation(
        tasc_id=task_id,
        validated=validated,
        proof_hash=proof_hash,
        timestamp=timestamp,
        duration_ms=duration_ms,
        gate_results=gate_results,
        evidence_paths=evidence_paths,
        command_executed=command,
        exit_code=result.exit_code,
        error_message=result.stderr[:500] if result.stderr and not validated else None,
    )


def save_llm_proof(validation: TascValidation, output_dir: str = ".tascer/proofs") -> str:
    """Save a TascValidation to disk.
    
    Args:
        validation: The validation to save
        output_dir: Directory to save in
    
    Returns:
        Path to the saved proof file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename from timestamp and tasc_id
    timestamp = validation.timestamp.replace(":", "-").replace(".", "-")
    filename = f"{timestamp}_{validation.tasc_id}.json"
    path = os.path.join(output_dir, filename)
    
    with open(path, 'w') as f:
        json.dump(validation.to_dict(), f, indent=2)
    
    return path


def load_llm_proof(path: str) -> TascValidation:
    """Load a TascValidation from disk."""
    with open(path) as f:
        data = json.load(f)
    
    return TascValidation.from_dict(data)


def verify_proof_chain(proof_paths: List[str]) -> Dict[str, Any]:
    """Verify a chain of proofs for an LLM workflow.
    
    Ensures all proofs in the chain are valid and form a coherent sequence.
    
    Args:
        proof_paths: List of paths to proof files
    
    Returns:
        Verification result with overall status and details
    """
    validations = [load_llm_proof(p) for p in proof_paths]
    
    results = {
        "verified": True,
        "total": len(validations),
        "valid": 0,
        "invalid": 0,
        "validations": [],
    }
    
    for validation in validations:
        is_valid = validation.validated and validation.verify()
        
        if is_valid:
            results["valid"] += 1
        else:
            results["invalid"] += 1
            results["verified"] = False
        
        results["validations"].append({
            "tasc_id": validation.tasc_id,
            "valid": is_valid,
            "proof_hash": validation.proof_hash,
        })
    
    # Create chain hash
    all_hashes = [v.proof_hash for v in validations]
    results["chain_hash"] = hashlib.sha256("".join(all_hashes).encode()).hexdigest()[:16]
    
    return results


# Deprecated alias for backwards compatibility
LLMExecutionProof = TascValidation
