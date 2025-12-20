"""Tests for Tascer validation gates."""

import pytest

from tascer.gates import (
    ExitCodeGate,
    PatternGate,
    FileExistsGate,
    JsonPathGate,
)
from tascer.gates.jsonpath import JsonPathAssertion, _get_by_path


class TestExitCodeGate:
    """Tests for ExitCodeGate."""
    
    def test_pass_on_zero(self):
        """Should pass when exit code is 0."""
        gate = ExitCodeGate(expected=[0])
        result = gate.check(0)
        
        assert result.passed is True
        assert result.gate_name == "EXIT_CODE"
    
    def test_fail_on_nonzero(self):
        """Should fail when exit code doesn't match."""
        gate = ExitCodeGate(expected=[0])
        result = gate.check(1)
        
        assert result.passed is False
    
    def test_multiple_expected(self):
        """Should pass when exit code is in expected list."""
        gate = ExitCodeGate(expected=[0, 1, 2])
        
        assert gate.check(0).passed is True
        assert gate.check(1).passed is True
        assert gate.check(3).passed is False


class TestPatternGate:
    """Tests for PatternGate."""
    
    def test_pass_no_errors(self):
        """Should pass when no error patterns found."""
        gate = PatternGate()
        result = gate.check(
            stdout="All tests passed",
            stderr="",
        )
        
        assert result.passed is True
    
    def test_fail_on_error_pattern(self):
        """Should fail when error pattern is found."""
        gate = PatternGate()
        result = gate.check(
            stdout="Error: something went wrong",
            stderr="",
        )
        
        assert result.passed is False
    
    def test_fail_on_exception(self):
        """Should fail when exception pattern is found."""
        gate = PatternGate()
        result = gate.check(
            stdout="",
            stderr="Exception: ValueError occurred",
        )
        
        assert result.passed is False
    
    def test_allowlist_exception(self):
        """Allowlist should override denylist."""
        gate = PatternGate(
            denylist=[r"error"],
            allowlist_exceptions=[r"no error"],
        )
        result = gate.check(
            stdout="no error occurred",
            stderr="",
        )
        
        assert result.passed is True
    
    def test_warning_threshold(self):
        """Should allow warnings up to threshold."""
        gate = PatternGate(severity_threshold=2)
        result = gate.check(
            stdout="warning: one\nwarning: two",
            stderr="",
        )
        
        assert result.passed is True
    
    def test_warning_over_threshold(self):
        """Should fail when warnings exceed threshold."""
        gate = PatternGate(severity_threshold=1)
        result = gate.check(
            stdout="warning: one\nwarning: two\nwarning: three",
            stderr="",
        )
        
        assert result.passed is False


class TestFileExistsGate:
    """Tests for FileExistsGate."""
    
    def test_file_exists(self, tmp_path):
        """Should pass when file exists."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        gate = FileExistsGate(path=str(test_file))
        result = gate.check()
        
        assert result.passed is True
    
    def test_file_not_exists(self, tmp_path):
        """Should fail when file doesn't exist."""
        gate = FileExistsGate(path=str(tmp_path / "nonexistent.txt"))
        result = gate.check()
        
        assert result.passed is False
    
    def test_hash_match(self, tmp_path):
        """Should pass when hash matches."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        
        # Get the actual hash
        from tascer.primitives.file_ops import snapshot_file
        snap = snapshot_file(str(test_file))
        
        gate = FileExistsGate(path=str(test_file), expected_hash=snap.sha256)
        result = gate.check()
        
        assert result.passed is True
    
    def test_hash_mismatch(self, tmp_path):
        """Should fail when hash doesn't match."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        
        gate = FileExistsGate(path=str(test_file), expected_hash="wrong_hash")
        result = gate.check()
        
        assert result.passed is False


class TestJsonPathGetByPath:
    """Tests for JSONPath accessor."""
    
    def test_simple_key(self):
        """Should access simple key."""
        data = {"name": "test"}
        result = _get_by_path(data, "$.name")
        
        assert result == ["test"]
    
    def test_nested_key(self):
        """Should access nested keys."""
        data = {"user": {"name": "alice"}}
        result = _get_by_path(data, "$.user.name")
        
        assert result == ["alice"]
    
    def test_array_index(self):
        """Should access array by index."""
        data = {"items": ["a", "b", "c"]}
        result = _get_by_path(data, "$.items[1]")
        
        assert result == ["b"]
    
    def test_array_wildcard(self):
        """Should access all array elements."""
        data = {"items": [{"id": 1}, {"id": 2}]}
        result = _get_by_path(data, "$.items[*].id")
        
        assert result == [1, 2]


class TestJsonPathGate:
    """Tests for JsonPathGate."""
    
    def test_single_assertion_pass(self):
        """Should pass when assertion matches."""
        gate = JsonPathGate(assertions=[
            JsonPathAssertion(path="$.status", expected="ok", operator="eq"),
        ])
        
        result = gate.check(data={"status": "ok"})
        
        assert result.passed is True
    
    def test_single_assertion_fail(self):
        """Should fail when assertion doesn't match."""
        gate = JsonPathGate(assertions=[
            JsonPathAssertion(path="$.status", expected="ok", operator="eq"),
        ])
        
        result = gate.check(data={"status": "error"})
        
        assert result.passed is False
    
    def test_multiple_assertions(self):
        """Should check all assertions."""
        gate = JsonPathGate(assertions=[
            JsonPathAssertion(path="$.status", expected="ok", operator="eq"),
            JsonPathAssertion(path="$.count", expected=5, operator="gt"),
        ])
        
        result = gate.check(data={"status": "ok", "count": 10})
        
        assert result.passed is True
    
    def test_exists_operator(self):
        """Should check field existence."""
        gate = JsonPathGate(assertions=[
            JsonPathAssertion(path="$.name", expected=True, operator="exists"),
        ])
        
        assert gate.check(data={"name": "test"}).passed is True
        assert gate.check(data={"other": "field"}).passed is False
    
    def test_contains_operator(self):
        """Should check string contains."""
        gate = JsonPathGate(assertions=[
            JsonPathAssertion(path="$.message", expected="success", operator="contains"),
        ])
        
        assert gate.check(data={"message": "Operation success!"}).passed is True
        assert gate.check(data={"message": "Operation failed"}).passed is False
    
    def test_from_dict(self):
        """Should create gate from simple dict."""
        gate = JsonPathGate.from_dict({
            "$.status": "ok",
            "$.code": 200,
        })
        
        result = gate.check(data={"status": "ok", "code": 200})
        
        assert result.passed is True
    
    def test_json_string_input(self):
        """Should parse JSON string input."""
        gate = JsonPathGate(assertions=[
            JsonPathAssertion(path="$.value", expected=42, operator="eq"),
        ])
        
        result = gate.check(data='{"value": 42}')
        
        assert result.passed is True
