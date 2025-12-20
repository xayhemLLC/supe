"""Tests for Tascer contracts - Context, ActionSpec, ActionResult, ValidationReport."""

import json
import pytest
from datetime import datetime

from tascer.contracts import (
    Context,
    GitState,
    ActionSpec,
    ActionResult,
    ValidationReport,
    GateResult,
    ErrorInfo,
)


class TestGitState:
    """Tests for GitState dataclass."""
    
    def test_to_dict_and_from_dict_roundtrip(self):
        """GitState should roundtrip through dict serialization."""
        original = GitState(
            branch="main",
            commit="abc123def456",
            dirty=True,
            diff_stat="2 files changed",
            status="M file.py",
        )
        
        data = original.to_dict()
        restored = GitState.from_dict(data)
        
        assert restored == original
    
    def test_from_dict_with_missing_fields(self):
        """from_dict should handle missing fields gracefully."""
        data = {"branch": "feature"}
        gs = GitState.from_dict(data)
        
        assert gs.branch == "feature"
        assert gs.commit == ""
        assert gs.dirty is False


class TestContext:
    """Tests for Context dataclass."""
    
    def test_basic_creation(self):
        """Context should be created with required fields."""
        ctx = Context(run_id="run123", tasc_id="tasc456")
        
        assert ctx.run_id == "run123"
        assert ctx.tasc_id == "tasc456"
        assert ctx.timestamp_start  # Auto-generated
        assert ctx.timestamp_end is None
    
    def test_finalize_sets_end_timestamp(self):
        """finalize() should set timestamp_end."""
        ctx = Context(run_id="run1", tasc_id="tasc1")
        assert ctx.timestamp_end is None
        
        ctx.finalize()
        
        assert ctx.timestamp_end is not None
    
    def test_to_json_roundtrip(self):
        """Context should serialize to JSON and back."""
        original = Context(
            run_id="run1",
            tasc_id="tasc1",
            repo_root="/path/to/repo",
            cwd="/path/to/repo/src",
            os_name="Darwin",
            arch="arm64",
            toolchain_versions={"python": "3.11.0", "node": "20.0.0"},
            git_state=GitState(
                branch="main",
                commit="abc123",
                dirty=False,
                diff_stat="",
                status="",
            ),
        )
        
        json_str = original.to_json()
        data = json.loads(json_str)
        restored = Context.from_dict(data)
        
        assert restored.run_id == original.run_id
        assert restored.tasc_id == original.tasc_id
        assert restored.git_state.branch == "main"


class TestActionSpec:
    """Tests for ActionSpec dataclass."""
    
    def test_basic_creation(self):
        """ActionSpec should be created with required fields."""
        spec = ActionSpec(
            id="action1",
            name="Run tests",
            op_kind="command",
            op_ref="pytest -v",
        )
        
        assert spec.id == "action1"
        assert spec.name == "Run tests"
        assert spec.version == "1.0"  # Default
    
    def test_roundtrip(self):
        """ActionSpec should roundtrip through dict."""
        original = ActionSpec(
            id="lint1",
            name="Lint check",
            permissions_required=["terminal"],
            op_kind="command",
            op_ref="ruff check .",
            evidence_expected=["stdout", "stderr", "exit_code"],
        )
        
        data = original.to_dict()
        restored = ActionSpec.from_dict(data)
        
        assert restored.id == original.id
        assert restored.permissions_required == ["terminal"]


class TestActionResult:
    """Tests for ActionResult dataclass."""
    
    def test_success_result(self):
        """ActionResult should represent success."""
        result = ActionResult(
            status="success",
            op_result=0,
            metrics={"duration_ms": 1234.5},
        )
        
        assert result.status == "success"
        assert result.op_result == 0
        assert result.error is None
    
    def test_failure_with_error(self):
        """ActionResult should capture error info."""
        result = ActionResult(
            status="fail",
            op_result=1,
            error=ErrorInfo(
                error_type="CommandError",
                message="Command failed",
            ),
        )
        
        data = result.to_dict()
        assert data["error"]["error_type"] == "CommandError"


class TestGateResult:
    """Tests for GateResult dataclass."""
    
    def test_passed_gate(self):
        """GateResult should represent passing gate."""
        gate = GateResult(
            gate_name="EXIT_CODE",
            passed=True,
            message="Exit code 0 matches expected",
            evidence={"exit_code": 0},
        )
        
        assert gate.passed is True
    
    def test_failed_gate(self):
        """GateResult should represent failing gate."""
        gate = GateResult(
            gate_name="PATTERNS",
            passed=False,
            message="Error pattern found",
        )
        
        assert gate.passed is False


class TestValidationReport:
    """Tests for ValidationReport dataclass."""
    
    def test_compute_overall_status_pass(self):
        """overall_status should be 'pass' when all gates pass."""
        report = ValidationReport(
            run_id="run1",
            tasc_id="tasc1",
            context=Context(run_id="run1", tasc_id="tasc1"),
            action_spec=ActionSpec(id="a1", name="test"),
            action_result=ActionResult(status="success"),
            gates_passed=[GateResult(gate_name="G1", passed=True, message="ok")],
            gates_failed=[],
        )
        
        report.compute_overall_status()
        
        assert report.overall_status == "pass"
    
    def test_compute_overall_status_fail(self):
        """overall_status should be 'fail' when gates fail."""
        report = ValidationReport(
            run_id="run1",
            tasc_id="tasc1",
            context=Context(run_id="run1", tasc_id="tasc1"),
            action_spec=ActionSpec(id="a1", name="test"),
            action_result=ActionResult(status="fail"),
            gates_passed=[],
            gates_failed=[GateResult(gate_name="G1", passed=False, message="fail")],
        )
        
        report.compute_overall_status()
        
        assert report.overall_status == "fail"
    
    def test_compute_overall_status_partial(self):
        """overall_status should be 'partial' when some gates pass."""
        report = ValidationReport(
            run_id="run1",
            tasc_id="tasc1",
            context=Context(run_id="run1", tasc_id="tasc1"),
            action_spec=ActionSpec(id="a1", name="test"),
            action_result=ActionResult(status="partial"),
            gates_passed=[GateResult(gate_name="G1", passed=True, message="ok")],
            gates_failed=[GateResult(gate_name="G2", passed=False, message="fail")],
        )
        
        report.compute_overall_status()
        
        assert report.overall_status == "partial"
    
    def test_generate_summary(self):
        """generate_summary should create human-readable summary."""
        report = ValidationReport(
            run_id="run1",
            tasc_id="tasc1",
            context=Context(run_id="run1", tasc_id="tasc1"),
            action_spec=ActionSpec(id="a1", name="test"),
            action_result=ActionResult(status="fail"),
            gates_passed=[GateResult(gate_name="G1", passed=True, message="ok")],
            gates_failed=[GateResult(gate_name="G2", passed=False, message="Error found")],
        )
        
        report.compute_overall_status()
        report.generate_summary()
        
        assert "run1" in report.summary
        assert "G2" in report.summary
    
    def test_to_json_roundtrip(self):
        """ValidationReport should serialize to JSON and back."""
        original = ValidationReport(
            run_id="run1",
            tasc_id="tasc1",
            context=Context(run_id="run1", tasc_id="tasc1", os_name="Linux"),
            action_spec=ActionSpec(id="a1", name="test", op_ref="echo hello"),
            action_result=ActionResult(status="success", op_result=0),
        )
        
        json_str = original.to_json()
        data = json.loads(json_str)
        restored = ValidationReport.from_dict(data)
        
        assert restored.run_id == "run1"
        assert restored.context.os_name == "Linux"
