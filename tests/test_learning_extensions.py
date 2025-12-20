"""Tests for learning system extensions to Tasc and Tascer.

Tests Phase 0 implementation:
- Tasc dataclass with learning fields
- Learning validation gates (confidence, gap, experiment)
- Learning proof generator
- LearningTascValidation contract
"""

import pytest
from datetime import datetime

from tasc.tasc import Tasc
from tasc.atom import decode_atom
from tasc.atomtypes import registry
from tascer.gates.confidence_gate import ConfidenceGate
from tascer.gates.gap_gate import GapGate
from tascer.gates.experiment_gate import ExperimentGate
from tascer.proofs.learning_proof import (
    prove_learning_session,
    prove_experiment_success,
    compute_proof_hash,
)
from tascer.contracts import LearningTascValidation, GateResult


# ============================================================================
# Tasc Learning Fields Tests
# ============================================================================


def test_tasc_learning_fields_roundtrip():
    """Tasc with learning fields should encode and decode without loss."""
    original = Tasc(
        id="LEARN-001",
        status="learning",
        title="Learn React Hooks",
        additional_notes="Study useState and useEffect",
        testing_instructions="python -m supe learn 'How do React hooks work?' --mode=ingest",
        desired_outcome="Understand hooks with confidence > 0.7",
        dependencies=["LEARN-JSX-001"],
        # Learning-specific fields
        learning_mode="INGEST",
        confidence_score=0.85,
        gaps=["useContext", "useReducer"],
        unresolved_questions=["When to use useCallback?", "useEffect cleanup?"],
        review_schedule={"next_review": "2025-01-01T00:00:00", "interval_days": "7"},
        related_session_id="session_abc123",
    )

    # Encode to atom
    atom = original.to_atom()
    encoded = atom.encode()

    # Decode from atom
    decoded_atom, offset = decode_atom(encoded, 0)
    assert offset == len(encoded)

    tasc_type = registry.get_by_name("tasc")
    assert decoded_atom.pindex == tasc_type.pindex

    # Reconstruct and verify
    reconstructed = Tasc.from_atom(decoded_atom)
    assert reconstructed.id == original.id
    assert reconstructed.learning_mode == original.learning_mode
    assert reconstructed.confidence_score == original.confidence_score
    assert reconstructed.gaps == original.gaps
    assert reconstructed.unresolved_questions == original.unresolved_questions
    assert reconstructed.review_schedule == original.review_schedule
    assert reconstructed.related_session_id == original.related_session_id


def test_tasc_learning_fields_optional():
    """Tasc without learning fields should still work."""
    t = Tasc(
        id="TASC-001",
        status="pending",
        title="Regular task",
        additional_notes="",
        testing_instructions="pytest",
        desired_outcome="Tests pass",
        dependencies=[],
    )

    # Should have default None values for learning fields
    assert t.learning_mode is None
    assert t.confidence_score is None
    assert t.gaps == []
    assert t.unresolved_questions == []
    assert t.review_schedule is None
    assert t.related_session_id is None

    # Should still roundtrip correctly
    atom = t.to_atom()
    decoded_atom, _ = decode_atom(atom.encode(), 0)
    reconstructed = Tasc.from_atom(decoded_atom)
    assert reconstructed.id == t.id


# ============================================================================
# Learning Validation Gates Tests
# ============================================================================


def test_confidence_gate_pass():
    """ConfidenceGate should pass when confidence meets threshold."""
    gate = ConfidenceGate(min_confidence=0.7)
    result = gate.check(0.85)

    assert result.passed is True
    assert result.gate_name == "CONFIDENCE"
    assert "0.85" in result.message
    assert "0.70" in result.message
    assert result.evidence["actual_confidence"] == 0.85
    assert result.evidence["required_confidence"] == 0.7


def test_confidence_gate_fail():
    """ConfidenceGate should fail when confidence below threshold."""
    gate = ConfidenceGate(min_confidence=0.7)
    result = gate.check(0.5)

    assert result.passed is False
    assert result.gate_name == "CONFIDENCE"
    assert "0.50" in result.message
    assert result.evidence["actual_confidence"] == 0.5


def test_gap_gate_pass():
    """GapGate should pass when gaps below threshold."""
    gate = GapGate(max_gaps=5)
    result = gate.check(3)

    assert result.passed is True
    assert result.gate_name == "GAP"
    assert "3" in result.message
    assert "5" in result.message
    assert result.evidence["actual_gaps"] == 3
    assert result.evidence["max_allowed_gaps"] == 5


def test_gap_gate_fail():
    """GapGate should fail when gaps exceed threshold."""
    gate = GapGate(max_gaps=5)
    result = gate.check(8)

    assert result.passed is False
    assert result.gate_name == "GAP"
    assert "8" in result.message
    assert result.evidence["actual_gaps"] == 8


def test_experiment_gate_pass():
    """ExperimentGate should pass when pass rate meets threshold."""
    gate = ExperimentGate(min_pass_rate=0.8)
    result = gate.check(passed=9, total=10)

    assert result.passed is True
    assert result.gate_name == "EXPERIMENT"
    assert "90.0%" in result.message or "90%" in result.message
    assert result.evidence["experiments_passed"] == 9
    assert result.evidence["experiments_total"] == 10
    assert result.evidence["pass_rate"] == 0.9


def test_experiment_gate_fail():
    """ExperimentGate should fail when pass rate below threshold."""
    gate = ExperimentGate(min_pass_rate=0.8)
    result = gate.check(passed=5, total=10)

    assert result.passed is False
    assert result.gate_name == "EXPERIMENT"
    assert result.evidence["pass_rate"] == 0.5


def test_experiment_gate_no_experiments():
    """ExperimentGate should pass when no experiments run."""
    gate = ExperimentGate(min_pass_rate=0.8)
    result = gate.check(passed=0, total=0)

    assert result.passed is True
    assert "No experiments" in result.message


# ============================================================================
# Learning Proof Generator Tests
# ============================================================================


def test_prove_learning_session_success():
    """prove_learning_session should succeed with good metrics."""
    session_data = {
        "session_id": "session_123",
        "mode": "INGEST",
        "beliefs": [
            {"content": "React hooks are functions", "confidence": 0.9},
            {"content": "useState returns array", "confidence": 0.8},
        ],
        "gaps": ["useContext", "custom hooks"],
        "questions": [
            {"text": "What is useState?", "answered": True},
            {"text": "What is useEffect?", "answered": True},
        ],
        "experiments": [],
        "duration_ms": 5000,
    }

    result = prove_learning_session(
        session_data,
        min_confidence=0.7,
        max_gaps=5,
        min_questions_answered=1,
    )

    assert result.proven is True
    assert abs(result.confidence_level - 0.85) < 0.01  # Average of 0.9 and 0.8 (approx)
    assert result.questions_answered == 2
    assert result.questions_total == 2
    assert len(result.gaps_identified) == 2
    assert result.mode == "INGEST"
    assert result.session_id == "session_123"
    assert len(result.proof_hash) == 16
    assert len(result.gate_results) >= 3  # Confidence, Gap, Questions


def test_prove_learning_session_failure_low_confidence():
    """prove_learning_session should fail with low confidence."""
    session_data = {
        "session_id": "session_456",
        "mode": "INGEST",
        "beliefs": [
            {"content": "Uncertain knowledge", "confidence": 0.5},
        ],
        "gaps": [],
        "questions": [{"text": "Question 1", "answered": True}],
        "experiments": [],
    }

    result = prove_learning_session(session_data, min_confidence=0.7)

    assert result.proven is False
    assert result.confidence_level == 0.5
    # Find the confidence gate result
    confidence_gate = next(g for g in result.gate_results if g.gate_name == "CONFIDENCE")
    assert confidence_gate.passed is False


def test_prove_learning_session_failure_too_many_gaps():
    """prove_learning_session should fail with too many gaps."""
    session_data = {
        "session_id": "session_789",
        "mode": "INGEST",
        "beliefs": [{"content": "Knowledge", "confidence": 0.9}],
        "gaps": ["gap1", "gap2", "gap3", "gap4", "gap5", "gap6"],
        "questions": [{"text": "Question 1", "answered": True}],
        "experiments": [],
    }

    result = prove_learning_session(session_data, max_gaps=5)

    assert result.proven is False
    assert len(result.gaps_identified) == 6
    # Find the gap gate result
    gap_gate = next(g for g in result.gate_results if g.gate_name == "GAP")
    assert gap_gate.passed is False


def test_prove_experiment_success():
    """prove_experiment_success should validate EXPLORE mode experiments."""
    experiment_data = {
        "experiment_id": "exp_001",
        "hypothesis": "Addition is commutative",
        "tests": [
            {"name": "test_1", "passed": True},
            {"name": "test_2", "passed": True},
            {"name": "test_3", "passed": True},
            {"name": "test_4", "passed": False},
        ],
        "properties_validated": ["commutativity", "associativity"],
        "duration_ms": 3000,
    }

    result = prove_experiment_success(
        experiment_data,
        min_pass_rate=0.7,
        expected_properties=["commutativity"],
    )

    assert result.proven is True
    assert result.mode == "EXPLORE"
    assert result.experiments_passed == 3
    assert result.experiments_failed == 1
    assert result.confidence_level == 0.75  # 3/4
    assert len(result.proof_hash) == 16


def test_compute_proof_hash_deterministic():
    """Proof hash should be deterministic for same input."""
    data = {"session_id": "test", "confidence": 0.8}

    hash1 = compute_proof_hash(data)
    hash2 = compute_proof_hash(data)

    assert hash1 == hash2
    assert len(hash1) == 16


# ============================================================================
# LearningTascValidation Tests
# ============================================================================


def test_learning_tasc_validation_creation():
    """LearningTascValidation should be creatable with all fields."""
    validation = LearningTascValidation(
        tasc_id="LEARN-001",
        validated=True,
        proof_hash="abc123def456",
        gate_results=[
            GateResult(gate_name="CONFIDENCE", passed=True, message="Pass", evidence={})
        ],
        timestamp=datetime.now().isoformat(),
        duration_ms=5000,
        # Learning-specific fields
        confidence_level=0.85,
        questions_answered=10,
        questions_total=12,
        experiments_passed=5,
        experiments_failed=1,
        gaps_identified=["gap1", "gap2"],
        next_review_at="2025-01-01T00:00:00",
        mode="INGEST",
    )

    assert validation.tasc_id == "LEARN-001"
    assert validation.confidence_level == 0.85
    assert validation.learning_success_rate == 10 / 12
    assert validation.experiment_success_rate == 5 / 6


def test_learning_tasc_validation_serialization():
    """LearningTascValidation should serialize to dict and back."""
    original = LearningTascValidation(
        tasc_id="LEARN-002",
        validated=True,
        proof_hash="hash123",
        gate_results=[],
        timestamp=datetime.now().isoformat(),
        confidence_level=0.9,
        questions_answered=5,
        questions_total=5,
        experiments_passed=0,
        experiments_failed=0,
        gaps_identified=["gap1"],
        next_review_at="2025-01-01T00:00:00",
        mode="EXPLORE",
    )

    # Serialize
    data = original.to_dict()

    # Verify all fields present
    assert data["tasc_id"] == "LEARN-002"
    assert data["confidence_level"] == 0.9
    assert data["mode"] == "EXPLORE"
    assert data["learning_success_rate"] == 1.0
    assert data["experiment_success_rate"] == 1.0

    # Deserialize
    reconstructed = LearningTascValidation.from_dict(data)

    assert reconstructed.tasc_id == original.tasc_id
    assert reconstructed.confidence_level == original.confidence_level
    assert reconstructed.mode == original.mode


def test_learning_success_rate_edge_cases():
    """Learning success rate should handle edge cases."""
    # Zero questions
    v1 = LearningTascValidation(
        tasc_id="test",
        validated=True,
        proof_hash="hash",
        gate_results=[],
        questions_answered=0,
        questions_total=0,
    )
    assert v1.learning_success_rate == 0.0

    # All answered
    v2 = LearningTascValidation(
        tasc_id="test",
        validated=True,
        proof_hash="hash",
        gate_results=[],
        questions_answered=10,
        questions_total=10,
    )
    assert v2.learning_success_rate == 1.0


def test_experiment_success_rate_edge_cases():
    """Experiment success rate should handle edge cases."""
    # No experiments
    v1 = LearningTascValidation(
        tasc_id="test",
        validated=True,
        proof_hash="hash",
        gate_results=[],
        experiments_passed=0,
        experiments_failed=0,
    )
    assert v1.experiment_success_rate == 1.0  # No failures = perfect

    # All passed
    v2 = LearningTascValidation(
        tasc_id="test",
        validated=True,
        proof_hash="hash",
        gate_results=[],
        experiments_passed=5,
        experiments_failed=0,
    )
    assert v2.experiment_success_rate == 1.0

    # Mixed results
    v3 = LearningTascValidation(
        tasc_id="test",
        validated=True,
        proof_hash="hash",
        gate_results=[],
        experiments_passed=7,
        experiments_failed=3,
    )
    assert v3.experiment_success_rate == 0.7
