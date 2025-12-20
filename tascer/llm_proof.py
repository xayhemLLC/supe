"""LLM Proof-of-Work System.

This module implements the structured task validation protocol for LLM agents.
It enforces a plan → tasc hierarchy where each tasc requires validation
(TascValidation) before advancing.

Key concepts:
- TascPlan: A structured plan containing Tascs with validation tracking
- Tasc: Imported from tasc.tasc - a task requiring validation
- TascValidation: Validation result for each Tasc (from contracts)
- ProofRequirement: What constitutes valid proof
- LLMTaskProof: Cryptographic proof of task completion
"""

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# Import base Tasc from tasc module
from tasc.tasc import Tasc

# Import validation and contracts
from .contracts import Context, GateResult, TascValidation
from .proofs import prove_script_success, prove_tests_passing, prove_lint_passing


# ---------------------------------------------------------------------------
# Enums and Types
# ---------------------------------------------------------------------------

class ProofType(str, Enum):
    """Types of proof that can validate task completion."""
    SCRIPT = "script"       # Exit code + output validation
    TEST = "test"           # Test suite passes
    LINT = "lint"           # Linting passes
    FILE = "file"           # Expected file(s) exist
    MANUAL = "manual"       # Human approval required
    COMPOSITE = "composite" # Multiple proofs required
    # Learning-specific proof types
    LEARNING_SESSION = "learning_session"  # Validates learning outcomes
    EXPERIMENT = "experiment"              # Validates experiments
    EXPLORATION = "exploration"            # Validates exploratory learning
    CONFIDENCE = "confidence"              # Validates confidence threshold
    REVIEW = "review"                      # Validates spaced repetition review


class TaskStatus(str, Enum):
    """Status of a task in the proof workflow."""
    PENDING = "pending"       # Not started
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"       # Waiting on dependency
    PROVING = "proving"       # Proof in progress
    PROVEN = "proven"         # Completed with proof
    FAILED = "failed"         # Proof failed
    SKIPPED = "skipped"       # Intentionally skipped
    AWAITING_APPROVAL = "awaiting_approval"  # Waiting for human sign-off
    # Learning-specific statuses
    EXPLORING = "exploring"        # Active exploration
    LEARNING = "learning"          # Learning in progress
    UNCERTAIN = "uncertain"        # Low confidence result
    NEEDS_REVIEW = "needs_review"  # Scheduled for review


# ---------------------------------------------------------------------------
# Core Data Structures
# ---------------------------------------------------------------------------

@dataclass
class ProofRequirement:
    """What constitutes valid proof of completion.
    
    Defines the evidence and validation gates needed to prove a task is done.
    """
    proof_type: ProofType
    criteria: Dict[str, Any] = field(default_factory=dict)
    required_evidence: List[str] = field(default_factory=list)
    timeout_seconds: float = 300
    allow_retry: bool = True
    max_retries: int = 3
    
    def to_dict(self) -> Dict:
        return {
            "proof_type": self.proof_type.value,
            "criteria": self.criteria,
            "required_evidence": self.required_evidence,
            "timeout_seconds": self.timeout_seconds,
            "allow_retry": self.allow_retry,
            "max_retries": self.max_retries,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ProofRequirement":
        return cls(
            proof_type=ProofType(data.get("proof_type", "script")),
            criteria=data.get("criteria", {}),
            required_evidence=data.get("required_evidence", []),
            timeout_seconds=data.get("timeout_seconds", 300),
            allow_retry=data.get("allow_retry", True),
            max_retries=data.get("max_retries", 3),
        )


@dataclass
class TascPlan:
    """A plan that LLMs must follow - the proof-of-work entry point.
    
    Plans are the top-level container for structured work.
    They define a set of Tascs with dependencies and validation requirements.
    Each Tasc's validation is tracked via the validations dict.
    """
    id: str
    title: str
    description: str = ""
    tascs: List[Tasc] = field(default_factory=list)
    validations: Dict[str, TascValidation] = field(default_factory=dict)
    proof_requirements: Dict[str, ProofRequirement] = field(default_factory=dict)
    validation_requirements: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: TaskStatus = TaskStatus.PENDING
    proof_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tascs": [t.to_dict() for t in self.tascs],
            "validations": {k: v.to_dict() for k, v in self.validations.items()},
            "proof_requirements": {k: v.to_dict() for k, v in self.proof_requirements.items()},
            "validation_requirements": self.validation_requirements,
            "created_at": self.created_at,
            "status": self.status.value,
            "proof_hash": self.proof_hash,
            "metadata": self.metadata,
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TascPlan":
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            tascs=[Tasc.from_dict(t) for t in data.get("tascs", [])],
            validations={k: TascValidation.from_dict(v) for k, v in data.get("validations", {}).items()},
            proof_requirements={k: ProofRequirement.from_dict(v) for k, v in data.get("proof_requirements", {}).items()},
            validation_requirements=data.get("validation_requirements", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            status=TaskStatus(data.get("status", "pending")),
            proof_hash=data.get("proof_hash"),
            metadata=data.get("metadata", {}),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "TascPlan":
        return cls.from_dict(json.loads(json_str))
    
    @property
    def progress(self) -> float:
        """Get overall plan completion progress."""
        if not self.tascs:
            return 1.0 if self.status == TaskStatus.PROVEN else 0.0
        validated_count = sum(1 for t in self.tascs if t.id in self.validations and self.validations[t.id].validated)
        return validated_count / len(self.tascs)
    
    @property
    def all_validated(self) -> bool:
        """Check if all Tascs are validated."""
        return all(
            t.id in self.validations and self.validations[t.id].validated 
            for t in self.tascs
        )
    
    def get_next_tasc(self) -> Optional[Tasc]:
        """Get the next Tasc that can be worked on."""
        validated_ids = {
            t.id for t in self.tascs 
            if t.id in self.validations and self.validations[t.id].validated
        }
        
        for tasc in self.tascs:
            if tasc.id not in validated_ids:
                # Check if dependencies are met
                deps_met = all(dep in validated_ids for dep in tasc.dependencies)
                if deps_met:
                    return tasc
        return None
    
    def get_validation(self, tasc_id: str) -> Optional[TascValidation]:
        """Get the validation for a specific Tasc."""
        return self.validations.get(tasc_id)


# ---------------------------------------------------------------------------
# Proof Results (Legacy compatibility)
# ---------------------------------------------------------------------------

@dataclass
class LLMTaskProof:
    """Cryptographic proof of LLM task completion.
    
    Contains all evidence and validation results needed to verify
    that a task was completed correctly.
    """
    task_id: str
    plan_id: str
    proven: bool
    proof_hash: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    execution_log: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)
    gate_results: List[GateResult] = field(default_factory=list)
    context_snapshot: Optional[Dict] = None
    duration_ms: float = 0
    retries: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "plan_id": self.plan_id,
            "proven": self.proven,
            "proof_hash": self.proof_hash,
            "timestamp": self.timestamp,
            "execution_log": self.execution_log,
            "evidence": self.evidence,
            "gate_results": [g.to_dict() if hasattr(g, 'to_dict') else g for g in self.gate_results],
            "context_snapshot": self.context_snapshot,
            "duration_ms": self.duration_ms,
            "retries": self.retries,
        }
    
    def verify(self) -> bool:
        """Verify the proof hash is valid."""
        computed = compute_proof_hash(self.to_dict())
        return computed == self.proof_hash
    
    def to_validation(self) -> TascValidation:
        """Convert to TascValidation format."""
        return TascValidation(
            tasc_id=self.task_id,
            validated=self.proven,
            proof_hash=self.proof_hash,
            timestamp=self.timestamp,
            duration_ms=self.duration_ms,
            gate_results=self.gate_results,
            evidence_paths=list(self.evidence.keys()),
            command_executed=self.execution_log.get("command", ""),
            exit_code=self.evidence.get("exit_code", 0),
        )


@dataclass
class PlanVerificationReport:
    """Full verification report for a completed plan."""
    plan_id: str
    plan_title: str
    verified: bool
    total_tasks: int
    proven_tasks: int
    failed_tasks: int
    validations: Dict[str, TascValidation] = field(default_factory=dict)
    verification_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    overall_proof_hash: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "plan_id": self.plan_id,
            "plan_title": self.plan_title,
            "verified": self.verified,
            "total_tasks": self.total_tasks,
            "proven_tasks": self.proven_tasks,
            "failed_tasks": self.failed_tasks,
            "validations": {k: v.to_dict() for k, v in self.validations.items()},
            "verification_timestamp": self.verification_timestamp,
            "overall_proof_hash": self.overall_proof_hash,
        }


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def compute_proof_hash(data: Dict) -> str:
    """Compute a cryptographic hash of proof data."""
    # Remove the proof_hash field itself if present
    data_copy = {k: v for k, v in data.items() if k != "proof_hash"}
    content = json.dumps(data_copy, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def create_plan(
    title: str,
    tascs: List[Dict],
    description: str = "",
    validation_requirements: Optional[List[str]] = None,
) -> TascPlan:
    """Create a new structured plan.
    
    Args:
        title: Human-readable plan title
        tascs: List of Tasc definitions (dicts with id, title, testing_instructions, etc.)
        description: Plan description
        validation_requirements: Overall validation requirements
    
    Returns:
        TascPlan ready for execution
    
    Example:
        plan = create_plan(
            title="Implement Auth",
            tascs=[
                {
                    "id": "tasc_1",
                    "title": "Create auth module",
                    "testing_instructions": "pytest tests/test_auth.py",
                    "desired_outcome": "All tests pass",
                },
            ]
        )
    """
    plan_id = f"plan_{uuid.uuid4().hex[:8]}"
    
    converted_tascs = []
    proof_requirements = {}
    
    for i, tasc_data in enumerate(tascs):
        tasc_id = tasc_data.get("id", f"tasc_{i+1}")
        
        tasc = Tasc(
            id=tasc_id,
            status=tasc_data.get("status", "pending"),
            title=tasc_data.get("title", ""),
            additional_notes=tasc_data.get("additional_notes", tasc_data.get("description", "")),
            testing_instructions=tasc_data.get("testing_instructions", tasc_data.get("command", "")),
            desired_outcome=tasc_data.get("desired_outcome", ""),
            dependencies=tasc_data.get("dependencies", []),
        )
        converted_tascs.append(tasc)
        
        # Add proof requirement if provided
        if "proof_required" in tasc_data:
            proof_requirements[tasc_id] = ProofRequirement.from_dict(tasc_data["proof_required"])
        else:
            # Default to script proof
            proof_requirements[tasc_id] = ProofRequirement(
                proof_type=ProofType.SCRIPT,
                criteria={"expected_exit_codes": [0]},
            )
    
    return TascPlan(
        id=plan_id,
        title=title,
        description=description,
        tascs=converted_tascs,
        proof_requirements=proof_requirements,
        validation_requirements=validation_requirements or [],
    )


def validate_tasc(
    tasc: Tasc,
    plan: TascPlan,
    command: Optional[str] = None,
    cwd: Optional[str] = None,
) -> TascValidation:
    """Validate a single Tasc and produce TascValidation.
    
    Args:
        tasc: The Tasc to validate
        plan: Parent TascPlan (for context and proof requirements)
        command: Override command (defaults to tasc.testing_instructions)
        cwd: Working directory
    
    Returns:
        TascValidation with validation results
    """
    import time
    start_time = time.time()
    
    # Determine the command to run
    cmd = command or tasc.command or tasc.testing_instructions
    if not cmd:
        cmd = "echo 'No command specified'"
    
    # Get proof requirement
    proof_req = plan.proof_requirements.get(tasc.id, ProofRequirement(proof_type=ProofType.SCRIPT))
    
    # Execute based on proof type
    if proof_req.proof_type == ProofType.SCRIPT:
        result = prove_script_success(
            command=cmd,
            cwd=cwd or os.getcwd(),
            tasc_id=tasc.id,
            expected_exit_codes=proof_req.criteria.get("expected_exit_codes", [0]),
            expected_output_files=proof_req.criteria.get("expected_output_files"),
            error_patterns=proof_req.criteria.get("error_patterns"),
        )
        validated = result.proven
        gate_results = result.gate_results
        exit_code = result.exit_code
        
    elif proof_req.proof_type == ProofType.TEST:
        result = prove_tests_passing(
            command=cmd,
            cwd=cwd or os.getcwd(),
            tasc_id=tasc.id,
        )
        validated = result.proven
        gate_results = result.gate_results
        exit_code = 0 if validated else 1
        
    elif proof_req.proof_type == ProofType.LINT:
        result = prove_lint_passing(
            command=cmd,
            cwd=cwd or os.getcwd(),
            tasc_id=tasc.id,
        )
        validated = result.proven
        gate_results = result.gate_results
        exit_code = 0 if validated else 1
    
    elif proof_req.proof_type == ProofType.MANUAL:
        # Manual approval required - create approval request
        from .approval import request_approval, get_approval
        
        # Check if there's an existing approved request for this tasc
        approval_id = plan.metadata.get(f"approval_{tasc.id}")
        if approval_id:
            approval = get_approval(approval_id)
            if approval and approval.is_approved:
                # Approval granted - mark as validated
                validated = True
                gate_results = [GateResult(
                    gate_name="MANUAL_APPROVAL",
                    passed=True,
                    message=f"Approved by: {', '.join(a.approver for a in approval.approvals if a.approved)}",
                    evidence={"approval_id": approval.id},
                )]
                exit_code = 0
            elif approval and approval.is_rejected:
                validated = False
                gate_results = [GateResult(
                    gate_name="MANUAL_APPROVAL",
                    passed=False,
                    message=f"Rejected: {approval.rejection_reason}",
                    evidence={"approval_id": approval.id},
                )]
                exit_code = 1
            else:
                # Still pending
                validated = False
                gate_results = [GateResult(
                    gate_name="MANUAL_APPROVAL",
                    passed=False,
                    message="Awaiting human approval",
                    evidence={"approval_id": approval.id, "status": "pending"},
                )]
                exit_code = -1  # Special code for pending
                tasc.status = "awaiting_approval"
        else:
            # Create new approval request
            approval = request_approval(
                tasc_id=tasc.id,
                title=f"Approve: {tasc.title}",
                description=tasc.additional_notes or tasc.desired_outcome or "Manual approval required",
                action_type="manual_gate",
                requested_by="agent",
                plan_id=plan.id,
                required_approvals=proof_req.criteria.get("required_approvals", 1),
                context={
                    "command": cmd,
                    "tasc_title": tasc.title,
                },
            )
            # Store approval ID in plan metadata
            plan.metadata[f"approval_{tasc.id}"] = approval.id
            
            validated = False
            gate_results = [GateResult(
                gate_name="MANUAL_APPROVAL",
                passed=False,
                message="Approval requested - awaiting human sign-off",
                evidence={"approval_id": approval.id},
            )]
            exit_code = -1
            tasc.status = "awaiting_approval"
        
    else:
        # Default behavior
        from .primitives import run_and_observe
        result = run_and_observe(cmd, cwd=cwd, shell=True, timeout_sec=proof_req.timeout_seconds)
        validated = result.exit_code == 0
        gate_results = []
        exit_code = result.exit_code
    
    duration_ms = (time.time() - start_time) * 1000
    timestamp = datetime.now().isoformat()
    
    # Compute proof hash
    proof_data = {
        "tasc_id": tasc.id,
        "plan_id": plan.id,
        "validated": validated,
        "command": cmd,
        "exit_code": exit_code,
        "timestamp": timestamp,
    }
    proof_hash = compute_proof_hash(proof_data)
    
    # Update Tasc proof fields
    if validated:
        tasc.proof_hash = proof_hash
        tasc.validated_at = timestamp
        tasc.status = "proven"
    else:
        tasc.status = "failed"
    
    # Create TascValidation
    validation = TascValidation(
        tasc_id=tasc.id,
        validated=validated,
        proof_hash=proof_hash,
        timestamp=timestamp,
        duration_ms=duration_ms,
        gate_results=gate_results,
        command_executed=cmd,
        exit_code=exit_code,
    )
    
    # Store in plan
    plan.validations[tasc.id] = validation
    
    return validation


# Legacy function for backwards compatibility
def prove_task(
    task: Tasc,
    command: Optional[str] = None,
    cwd: Optional[str] = None,
    plan_id: str = "standalone",
) -> LLMTaskProof:
    """Legacy function - validates a Tasc and returns LLMTaskProof.
    
    For new code, use validate_tasc() instead.
    """
    # Create a temporary plan for standalone validation
    temp_plan = TascPlan(
        id=plan_id,
        title="Standalone",
        tascs=[task],
    )
    
    validation = validate_tasc(task, temp_plan, command, cwd)
    
    # Convert to LLMTaskProof for backwards compatibility
    return LLMTaskProof(
        task_id=task.id,
        plan_id=plan_id,
        proven=validation.validated,
        proof_hash=validation.proof_hash,
        timestamp=validation.timestamp,
        execution_log={"command": validation.command_executed, "cwd": cwd},
        evidence={"exit_code": validation.exit_code},
        gate_results=validation.gate_results,
        duration_ms=validation.duration_ms,
    )


def verify_plan_completion(plan: TascPlan) -> PlanVerificationReport:
    """Verify that an entire plan has been completed with valid proofs.
    
    Args:
        plan: The plan to verify
    
    Returns:
        PlanVerificationReport with verification results
    """
    validated_count = 0
    failed_count = 0
    
    for tasc in plan.tascs:
        validation = plan.validations.get(tasc.id)
        if validation and validation.validated:
            validated_count += 1
        elif validation and not validation.validated:
            failed_count += 1
    
    verified = validated_count == len(plan.tascs) and failed_count == 0
    
    # Compute overall proof hash
    all_hashes = [v.proof_hash for v in plan.validations.values() if v.validated]
    overall_hash = hashlib.sha256("".join(all_hashes).encode()).hexdigest()[:16] if all_hashes else None
    
    if verified:
        plan.status = TaskStatus.PROVEN
        plan.proof_hash = overall_hash
    
    return PlanVerificationReport(
        plan_id=plan.id,
        plan_title=plan.title,
        verified=verified,
        total_tasks=len(plan.tascs),
        proven_tasks=validated_count,
        failed_tasks=failed_count,
        validations=plan.validations,
        overall_proof_hash=overall_hash,
    )


# ---------------------------------------------------------------------------
# Plan Execution
# ---------------------------------------------------------------------------

def execute_plan(
    plan: TascPlan,
    cwd: Optional[str] = None,
    on_tasc_complete: Optional[Callable[[Tasc, TascValidation], None]] = None,
) -> PlanVerificationReport:
    """Execute all Tascs in a plan in dependency order.
    
    Args:
        plan: The plan to execute
        cwd: Working directory
        on_tasc_complete: Callback called after each Tasc completes
    
    Returns:
        PlanVerificationReport with full results
    """
    plan.status = TaskStatus.IN_PROGRESS
    
    while True:
        next_tasc = plan.get_next_tasc()
        if next_tasc is None:
            break
        
        validation = validate_tasc(
            tasc=next_tasc,
            plan=plan,
            cwd=cwd,
        )
        
        if on_tasc_complete:
            on_tasc_complete(next_tasc, validation)
        
        # If Tasc failed, stop execution
        if not validation.validated:
            break
    
    return verify_plan_completion(plan)


# ---------------------------------------------------------------------------
# Storage Functions
# ---------------------------------------------------------------------------

def save_plan(plan: TascPlan, path: str) -> None:
    """Save a plan to disk."""
    with open(path, 'w') as f:
        f.write(plan.to_json())


def load_plan(path: str) -> TascPlan:
    """Load a plan from disk."""
    with open(path) as f:
        return TascPlan.from_json(f.read())


def save_validation(validation: TascValidation, output_dir: str = ".tascer/proofs") -> str:
    """Save a TascValidation to disk."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{validation.timestamp.replace(':', '-')}_{validation.tasc_id}.json"
    path = os.path.join(output_dir, filename)
    
    with open(path, 'w') as f:
        json.dump(validation.to_dict(), f, indent=2)
    
    return path


# Legacy alias
def save_proof(proof: LLMTaskProof, output_dir: str = ".tascer/proofs") -> str:
    """Save a proof to disk (legacy function)."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{proof.timestamp.replace(':', '-')}_{proof.task_id}.json"
    path = os.path.join(output_dir, filename)
    
    with open(path, 'w') as f:
        json.dump(proof.to_dict(), f, indent=2)
    
    return path
