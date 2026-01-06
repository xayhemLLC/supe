"""Comprehensive tests for evidence-based validation system.

Tests all components:
- Evidence creation and serialization
- Evidence collections
- Unified validator
- Domain-specific requirements
- Self-testing tascs
- AB Memory integration
"""

import pytest
from tasc.evidence import (
    Evidence,
    EvidenceCollection,
    EvidenceSource,
    collect_test_evidence,
    collect_code_evidence,
)
from tasc.tasc import Tasc
from tasc.validation import UnifiedValidator, ValidationResult
from tasc.domains import (
    TaskDomain,
    get_requirements_for_domain,
    apply_domain_to_tasc,
    infer_domain_from_title,
)
from tasc.self_validation import (
    SelfValidatingTaskc,
    ExperimentStatus,
    ValidationExperiment,
)


# ============================================================================
# Evidence Tests
# ============================================================================

def test_evidence_creation():
    """Test evidence creation and basic properties."""
    evidence = Evidence.create(
        text="Test passed successfully",
        source=EvidenceSource.TEST,
        citations=["tests/test_foo.py::test_bar"],
    )

    assert evidence.id is not None
    assert evidence.text == "Test passed successfully"
    assert evidence.source == EvidenceSource.TEST
    assert evidence.citations == ["tests/test_foo.py::test_bar"]
    assert evidence.validated == False
    assert evidence.confidence == 1.0


def test_evidence_serialization():
    """Test evidence serialization to/from dict."""
    original = Evidence.create(
        text="Code review approved",
        source=EvidenceSource.PEER_REVIEW,
        citations=["github.com/org/repo/pull/123"],
    )
    original.validated = True
    original.validation_method = "manual"

    # Serialize
    data = original.to_dict()

    # Deserialize
    restored = Evidence.from_dict(data)

    assert restored.id == original.id
    assert restored.text == original.text
    assert restored.source == original.source
    assert restored.citations == original.citations
    assert restored.validated == original.validated
    assert restored.validation_method == original.validation_method


def test_evidence_helper_functions():
    """Test evidence helper functions."""
    # Test evidence
    test_evidence = collect_test_evidence(
        test_results={"passed": 42, "total": 45, "coverage": 87},
        test_command="pytest",
    )

    assert test_evidence.source == EvidenceSource.TEST
    assert "42/45" in test_evidence.text
    assert "coverage: 87%" in test_evidence.text

    # Code evidence
    code_evidence = collect_code_evidence(
        file_path="src/foo.py",
        line_start=10,
        line_end=20,
        description="Fixed null pointer bug",
        commit_hash="abc123",
    )

    assert code_evidence.source == EvidenceSource.CODE
    assert "src/foo.py:10-20" in code_evidence.citations
    assert "commit:abc123" in code_evidence.citations


# ============================================================================
# Evidence Collection Tests
# ============================================================================

def test_evidence_collection_creation():
    """Test evidence collection creation."""
    collection = EvidenceCollection.create("tasc-123")

    assert collection.id is not None
    assert collection.tasc_id == "tasc-123"
    assert len(collection.evidence_items) == 0


def test_evidence_collection_operations():
    """Test evidence collection operations."""
    collection = EvidenceCollection.create("tasc-123")

    # Add evidence
    evidence1 = Evidence.create("Test 1", EvidenceSource.TEST, [])
    evidence2 = Evidence.create("Code 2", EvidenceSource.CODE, [])
    evidence3 = Evidence.create("Test 3", EvidenceSource.TEST, [])

    collection.add_evidence(evidence1)
    collection.add_evidence(evidence2)
    collection.add_evidence(evidence3)

    assert len(collection.evidence_items) == 3

    # Get by source
    test_evidence = collection.get_evidence_by_source(EvidenceSource.TEST)
    assert len(test_evidence) == 2

    # Source diversity
    assert collection.get_source_diversity() == 2  # TEST and CODE

    # Validated evidence
    evidence1.validated = True
    assert len(collection.get_validated_evidence()) == 1


# ============================================================================
# Unified Validator Tests
# ============================================================================

@pytest.mark.asyncio
async def test_validator_evidence_quality():
    """Test evidence quality evaluation."""
    validator = UnifiedValidator(debug=False)

    # Create collection with good evidence
    evidence_list = [
        Evidence.create("Test 1", EvidenceSource.TEST, ["file1"]),
        Evidence.create("Code 2", EvidenceSource.CODE, ["file2"]),
        Evidence.create("Doc 3", EvidenceSource.DOC, ["file3"]),
        Evidence.create("Experiment 4", EvidenceSource.EXPERIMENT, ["file4"]),
        Evidence.create("Analysis 5", EvidenceSource.CODE_ANALYSIS, ["file5"]),
    ]

    # Mark some as validated
    evidence_list[0].validated = True
    evidence_list[3].validated = True

    factor = validator._evaluate_evidence_quality(evidence_list)

    # Should be high quality: 5 items, 5 sources, 2 validated, all cited
    assert factor > 1.0  # Should get bonuses
    assert factor <= 1.2  # Capped at 1.2


@pytest.mark.asyncio
async def test_validator_no_evidence():
    """Test validation with no evidence."""
    validator = UnifiedValidator()
    factor = validator._evaluate_evidence_quality([])

    assert factor == 0.8  # Penalty for no evidence


@pytest.mark.asyncio
async def test_complete_validation():
    """Test complete validation workflow."""
    tasc = Tasc(
        id="test-001",
        status="completed",
        title="Test tasc",
        additional_notes="",
        testing_instructions="echo 'test'",
        desired_outcome="Success",
        required_evidence_types=["test", "code"],
    )

    collection = EvidenceCollection.create(tasc.id)
    collection.add_evidence(Evidence.create("Test", EvidenceSource.TEST, ["f1"]))
    collection.add_evidence(Evidence.create("Code", EvidenceSource.CODE, ["f2"]))

    validator = UnifiedValidator(debug=False)
    result = await validator.validate(tasc, collection, run_objective_checks=False)

    assert isinstance(result, ValidationResult)
    assert result.overall_confidence > 0
    assert result.overall_confidence <= 1.0
    assert result.evidence_count == 2
    assert result.source_diversity == 2


# ============================================================================
# Domain Requirements Tests
# ============================================================================

def test_domain_requirements_debugging():
    """Test debugging domain requirements."""
    reqs = get_requirements_for_domain(TaskDomain.DEBUGGING)

    assert reqs.domain == TaskDomain.DEBUGGING
    assert EvidenceSource.REASONING in reqs.required_sources
    assert EvidenceSource.EXPERIMENT in reqs.required_sources
    assert EvidenceSource.CODE_ANALYSIS in reqs.required_sources
    assert EvidenceSource.CODE in reqs.required_sources
    assert EvidenceSource.REGRESSION_TEST in reqs.required_sources
    assert reqs.min_confidence == 0.8  # Higher bar for bugs


def test_domain_requirements_design():
    """Test design domain requirements."""
    reqs = get_requirements_for_domain(TaskDomain.DESIGN)

    assert reqs.domain == TaskDomain.DESIGN
    assert EvidenceSource.DOC in reqs.required_sources
    assert EvidenceSource.REASONING in reqs.required_sources
    assert EvidenceSource.CODE in reqs.required_sources


def test_domain_inference():
    """Test domain inference from title."""
    assert infer_domain_from_title("Fix crash in login") == TaskDomain.DEBUGGING
    assert infer_domain_from_title("Design caching layer") == TaskDomain.DESIGN
    assert infer_domain_from_title("Research React hooks") == TaskDomain.RESEARCH
    assert infer_domain_from_title("Refactor auth module") == TaskDomain.REFACTORING
    assert infer_domain_from_title("Add user profile") == TaskDomain.FEATURE
    assert infer_domain_from_title("Fix security vulnerability") == TaskDomain.SECURITY
    assert infer_domain_from_title("Optimize query performance") == TaskDomain.PERFORMANCE


def test_apply_domain_to_tasc():
    """Test applying domain to tasc."""
    tasc = Tasc(
        id="test",
        status="pending",
        title="Fix memory leak",
        additional_notes="",
        testing_instructions="",
        desired_outcome="",
    )

    apply_domain_to_tasc(tasc, TaskDomain.DEBUGGING)

    assert len(tasc.required_evidence_types) > 0
    assert "reasoning" in tasc.required_evidence_types
    assert "experiment" in tasc.required_evidence_types
    assert "[Domain: debugging]" in tasc.additional_notes


# ============================================================================
# Self-Validation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_experiment_generation():
    """Test experiment generation for debugging task."""
    tasc = Tasc(
        id="test-001",
        status="completed",
        title="Fix null pointer bug",
        additional_notes="",
        testing_instructions="pytest tests/test_foo.py",
        desired_outcome="No crash",
    )

    self_val = SelfValidatingTaskc(tasc, TaskDomain.DEBUGGING)
    experiments = await self_val.synthesize_validation_experiments()

    assert len(experiments) > 0
    assert all(isinstance(e, ValidationExperiment) for e in experiments)
    assert all(e.status == ExperimentStatus.PENDING for e in experiments)

    # Check experiment types for debugging
    exp_ids = [e.id for e in experiments]
    assert any("reproduction" in id for id in exp_ids)
    assert any("regression" in id for id in exp_ids)


@pytest.mark.asyncio
async def test_validation_summary():
    """Test validation summary generation."""
    tasc = Tasc(
        id="test-001",
        status="completed",
        title="Test",
        additional_notes="",
        testing_instructions="",
        desired_outcome="",
    )

    async def mock_exec(exp):
        if "1" in exp.id:
            return {"success": True}
        else:
            raise Exception("Mock failure")

    self_val = SelfValidatingTaskc(tasc, TaskDomain.FEATURE)
    await self_val.self_validate(executor_func=mock_exec)

    summary = self_val.get_validation_summary()

    assert "total_experiments" in summary
    assert "passed" in summary
    assert "failed" in summary
    assert "errors" in summary
    assert "success_rate" in summary
    assert summary["total_experiments"] > 0
