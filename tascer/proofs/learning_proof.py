"""TASC_PROVE_LEARNING - Prove learning sessions meet requirements.

Validates learning outcomes against confidence, gap, and experiment criteria.
Supports both INGEST (document learning) and EXPLORE (experimental) modes.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..gates.confidence_gate import ConfidenceGate
from ..gates.gap_gate import GapGate
from ..gates.experiment_gate import ExperimentGate
from ..contracts import GateResult


@dataclass
class LearningProofResult:
    """Result of proving learning session success."""

    proven: bool
    confidence_level: float
    questions_answered: int
    questions_total: int
    experiments_passed: int
    experiments_failed: int
    gaps_identified: List[str] = field(default_factory=list)
    gate_results: List[GateResult] = field(default_factory=list)
    mode: str = "INGEST"  # "INGEST" or "EXPLORE"
    session_id: str = ""
    proof_hash: str = ""
    next_review_at: str = ""
    duration_ms: float = 0

    @property
    def learning_success_rate(self) -> float:
        """Calculate learning success rate."""
        if self.questions_total == 0:
            return 0.0
        return self.questions_answered / self.questions_total

    @property
    def experiment_success_rate(self) -> float:
        """Calculate experiment success rate."""
        total = self.experiments_passed + self.experiments_failed
        if total == 0:
            return 1.0  # No experiments = no failures
        return self.experiments_passed / total

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "proven": self.proven,
            "confidence_level": self.confidence_level,
            "questions_answered": self.questions_answered,
            "questions_total": self.questions_total,
            "experiments_passed": self.experiments_passed,
            "experiments_failed": self.experiments_failed,
            "gaps_identified": self.gaps_identified,
            "gate_results": [g.to_dict() for g in self.gate_results],
            "mode": self.mode,
            "session_id": self.session_id,
            "proof_hash": self.proof_hash,
            "next_review_at": self.next_review_at,
            "duration_ms": self.duration_ms,
            "learning_success_rate": self.learning_success_rate,
            "experiment_success_rate": self.experiment_success_rate,
        }


def compute_proof_hash(data: Dict[str, Any]) -> str:
    """Compute deterministic proof hash from learning data.

    Args:
        data: Learning session data to hash.

    Returns:
        16-character truncated SHA256 hash.
    """
    # Serialize with sorted keys for deterministic hash
    json_str = json.dumps(data, sort_keys=True, default=str)
    hash_obj = hashlib.sha256(json_str.encode())
    return hash_obj.hexdigest()[:16]


def prove_learning_session(
    session_data: Dict[str, Any],
    min_confidence: float = 0.7,
    max_gaps: int = 5,
    min_questions_answered: int = 1,
    min_experiment_pass_rate: float = 0.8,
    review_interval_days: int = 1,
) -> LearningProofResult:
    """Prove that a learning session met requirements.

    TASC_PROVE_LEARNING_SESSION implementation.

    Validates learning outcomes using multiple gates:
    - ConfidenceGate: Check if average confidence > threshold
    - GapGate: Check if gaps < max allowed
    - ExperimentGate: Check if experiments passed (EXPLORE mode only)

    Args:
        session_data: Learning session data containing:
            - session_id: Unique session identifier
            - mode: "INGEST" or "EXPLORE"
            - beliefs: List of beliefs with confidence scores
            - gaps: List of identified knowledge gaps
            - questions: List of questions and answers
            - experiments: (Optional) List of experiment results
        min_confidence: Minimum required confidence (0.0-1.0).
        max_gaps: Maximum allowed knowledge gaps.
        min_questions_answered: Minimum questions that must be answered.
        min_experiment_pass_rate: Minimum experiment pass rate (EXPLORE mode).
        review_interval_days: Days until next review (for spaced repetition).

    Returns:
        LearningProofResult with validation status and proof hash.
    """
    # Extract session data
    session_id = session_data.get("session_id", "")
    mode = session_data.get("mode", "INGEST")
    beliefs = session_data.get("beliefs", [])
    gaps = session_data.get("gaps", [])
    questions = session_data.get("questions", [])
    experiments = session_data.get("experiments", [])

    # Calculate metrics
    avg_confidence = 0.0
    if beliefs:
        confidences = [b.get("confidence", 0.0) for b in beliefs]
        avg_confidence = sum(confidences) / len(confidences)

    gap_count = len(gaps)

    answered_questions = [q for q in questions if q.get("answered", False)]
    questions_answered = len(answered_questions)
    questions_total = len(questions)

    experiments_passed = sum(1 for e in experiments if e.get("success", False))
    experiments_failed = len(experiments) - experiments_passed

    # Apply gates
    gate_results = []

    # Confidence gate
    confidence_gate = ConfidenceGate(min_confidence=min_confidence)
    confidence_result = confidence_gate.check(avg_confidence)
    gate_results.append(confidence_result)

    # Gap gate
    gap_gate = GapGate(max_gaps=max_gaps)
    gap_result = gap_gate.check(gap_count)
    gate_results.append(gap_result)

    # Questions answered gate
    questions_gate = GateResult(
        gate_name="QUESTIONS_ANSWERED",
        passed=questions_answered >= min_questions_answered,
        message=f"Answered {questions_answered}/{questions_total} questions (minimum: {min_questions_answered})",
        evidence={
            "questions_answered": questions_answered,
            "questions_total": questions_total,
            "minimum_required": min_questions_answered,
        },
    )
    gate_results.append(questions_gate)

    # Experiment gate (EXPLORE mode only)
    if mode == "EXPLORE" and experiments:
        experiment_gate = ExperimentGate(min_pass_rate=min_experiment_pass_rate)
        experiment_result = experiment_gate.check(experiments_passed, len(experiments))
        gate_results.append(experiment_result)

    # Determine overall proof status
    proven = all(g.passed for g in gate_results)

    # Compute proof hash
    proof_data = {
        "session_id": session_id,
        "mode": mode,
        "confidence": avg_confidence,
        "gaps": gaps,
        "questions_answered": questions_answered,
        "questions_total": questions_total,
        "experiments_passed": experiments_passed,
        "experiments_failed": experiments_failed,
    }
    proof_hash = compute_proof_hash(proof_data)

    # Calculate next review time
    next_review_at = (
        datetime.now() + timedelta(days=review_interval_days)
    ).isoformat()

    return LearningProofResult(
        proven=proven,
        confidence_level=avg_confidence,
        questions_answered=questions_answered,
        questions_total=questions_total,
        experiments_passed=experiments_passed,
        experiments_failed=experiments_failed,
        gaps_identified=gaps,
        gate_results=gate_results,
        mode=mode,
        session_id=session_id,
        proof_hash=proof_hash,
        next_review_at=next_review_at,
        duration_ms=session_data.get("duration_ms", 0),
    )


def prove_experiment_success(
    experiment_data: Dict[str, Any],
    min_pass_rate: float = 0.8,
    expected_properties: Optional[List[str]] = None,
) -> LearningProofResult:
    """Prove that an EXPLORE mode experiment succeeded.

    TASC_PROVE_EXPERIMENT implementation for EXPLORE mode.

    Validates experimental learning where the agent tests hypotheses
    and conjectures through controlled experiments.

    Args:
        experiment_data: Experiment data containing:
            - experiment_id: Unique experiment identifier
            - hypothesis: The hypothesis being tested
            - tests: List of test results
            - properties_validated: List of validated properties
        min_pass_rate: Minimum test pass rate (0.0-1.0).
        expected_properties: Properties that must be validated.

    Returns:
        LearningProofResult with validation status and proof hash.
    """
    # Extract experiment data
    experiment_id = experiment_data.get("experiment_id", "")
    hypothesis = experiment_data.get("hypothesis", "")
    tests = experiment_data.get("tests", [])
    properties_validated = experiment_data.get("properties_validated", [])

    # Calculate metrics
    tests_passed = sum(1 for t in tests if t.get("passed", False))
    tests_failed = len(tests) - tests_passed

    # Apply gates
    gate_results = []

    # Experiment gate
    experiment_gate = ExperimentGate(min_pass_rate=min_pass_rate)
    experiment_result = experiment_gate.check(tests_passed, len(tests))
    gate_results.append(experiment_result)

    # Properties validation gate
    if expected_properties:
        missing_properties = [p for p in expected_properties if p not in properties_validated]
        properties_gate = GateResult(
            gate_name="PROPERTIES_VALIDATED",
            passed=len(missing_properties) == 0,
            message=f"Validated {len(properties_validated)}/{len(expected_properties)} required properties",
            evidence={
                "validated": properties_validated,
                "expected": expected_properties,
                "missing": missing_properties,
            },
        )
        gate_results.append(properties_gate)

    # Determine overall proof status
    proven = all(g.passed for g in gate_results)

    # Compute proof hash
    proof_data = {
        "experiment_id": experiment_id,
        "hypothesis": hypothesis,
        "tests_passed": tests_passed,
        "tests_total": len(tests),
        "properties_validated": properties_validated,
    }
    proof_hash = compute_proof_hash(proof_data)

    # Calculate confidence based on test results
    confidence = tests_passed / len(tests) if tests else 0.0

    return LearningProofResult(
        proven=proven,
        confidence_level=confidence,
        questions_answered=1 if proven else 0,  # Hypothesis counts as 1 question
        questions_total=1,
        experiments_passed=tests_passed,
        experiments_failed=tests_failed,
        gaps_identified=[],
        gate_results=gate_results,
        mode="EXPLORE",
        session_id=experiment_id,
        proof_hash=proof_hash,
        next_review_at=(datetime.now() + timedelta(days=7)).isoformat(),
        duration_ms=experiment_data.get("duration_ms", 0),
    )
