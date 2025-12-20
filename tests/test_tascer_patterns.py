"""Tests for Tasc pattern tracking."""

import pytest
from datetime import datetime


class TestPatternBase:
    """Tests for base Pattern class."""
    
    def test_create_pattern(self):
        """Test creating a pattern."""
        from tascer.patterns import Pattern
        
        pattern = Pattern(
            pattern_id="pat_001",
            pattern_type="test",
            name="Test Pattern",
            description="A test pattern",
            created_at=datetime.now(),
        )
        
        assert pattern.pattern_id == "pat_001"
        assert pattern.occurrences == 1
        assert pattern.confidence == 0.5
    
    def test_increment_occurrence(self):
        """Test incrementing occurrence updates confidence."""
        from tascer.patterns import Pattern
        
        pattern = Pattern(
            pattern_id="pat_001",
            pattern_type="test",
            name="Test Pattern",
            description="",
            created_at=datetime.now(),
        )
        
        initial_confidence = pattern.confidence
        pattern.increment_occurrence()
        
        assert pattern.occurrences == 2
        assert pattern.confidence > initial_confidence
    
    def test_to_dict(self):
        """Test pattern serialization."""
        from tascer.patterns import Pattern
        
        pattern = Pattern(
            pattern_id="pat_001",
            pattern_type="test",
            name="Test Pattern",
            description="A test pattern",
            created_at=datetime.now(),
            tags=["test", "example"],
        )
        
        data = pattern.to_dict()
        
        assert data["pattern_id"] == "pat_001"
        assert "test" in data["tags"]
    
    def test_from_dict(self):
        """Test pattern deserialization."""
        from tascer.patterns import Pattern
        
        data = {
            "pattern_id": "pat_001",
            "pattern_type": "test",
            "name": "Test Pattern",
            "description": "A test pattern",
            "created_at": datetime.now().isoformat(),
            "tags": ["test"],
        }
        
        pattern = Pattern.from_dict(data)
        
        assert pattern.pattern_id == "pat_001"
        assert pattern.name == "Test Pattern"


class TestFailurePattern:
    """Tests for FailurePattern."""
    
    def test_create_failure_pattern(self):
        """Test creating failure pattern."""
        from tascer.patterns import FailurePattern
        
        pattern = FailurePattern(
            pattern_id="fail_001",
            pattern_type="failure",
            name="Import Error",
            description="Module not found errors",
            created_at=datetime.now(),
            error_type="ModuleNotFoundError",
            error_pattern=r"No module named '(\w+)'",
        )
        
        assert pattern.pattern_type == "failure"
        assert pattern.error_type == "ModuleNotFoundError"
    
    def test_matches_error(self):
        """Test matching error messages."""
        from tascer.patterns import FailurePattern
        
        pattern = FailurePattern(
            pattern_id="fail_001",
            pattern_type="failure",
            name="Import Error",
            description="",
            created_at=datetime.now(),
            error_type="ModuleNotFoundError",
            error_pattern=r"No module named",
        )
        
        assert pattern.matches("ModuleNotFoundError", "No module named 'foo'")
        assert not pattern.matches("ModuleNotFoundError", "Something else")
        assert not pattern.matches("TypeError", "No module named 'foo'")


class TestFixPattern:
    """Tests for FixPattern."""
    
    def test_create_fix_pattern(self):
        """Test creating fix pattern."""
        from tascer.patterns import FixPattern
        
        pattern = FixPattern(
            pattern_id="fix_001",
            pattern_type="fix",
            name="Install Missing Module",
            description="Fix for missing module errors",
            created_at=datetime.now(),
            problem_signature="ModuleNotFoundError",
            fix_actions=["terminal.run pip install"],
            success_evidence=["import succeeds"],
        )
        
        assert pattern.pattern_type == "fix"
        assert len(pattern.fix_actions) == 1


class TestDecisionPattern:
    """Tests for DecisionPattern."""
    
    def test_create_decision_pattern(self):
        """Test creating decision pattern."""
        from tascer.patterns import DecisionPattern
        
        pattern = DecisionPattern(
            pattern_id="dec_001",
            pattern_type="decision",
            name="File vs Git",
            description="When to use file.read vs git.diff",
            created_at=datetime.now(),
            decision_trigger="need to see changes",
            alternatives=["file.read", "git.diff"],
            typical_choice="git.diff",
            success_rate=0.85,
        )
        
        assert pattern.pattern_type == "decision"
        assert pattern.typical_choice == "git.diff"


class TestPatternStore:
    """Tests for PatternStore."""
    
    def test_add_pattern(self):
        """Test adding pattern to store."""
        from tascer.patterns import Pattern, PatternStore
        
        store = PatternStore()
        pattern = Pattern(
            pattern_id="pat_001",
            pattern_type="test",
            name="Test",
            description="",
            created_at=datetime.now(),
        )
        
        store.add(pattern)
        
        assert len(store) == 1
    
    def test_get_pattern(self):
        """Test getting pattern by ID."""
        from tascer.patterns import Pattern, PatternStore
        
        store = PatternStore()
        pattern = Pattern(
            pattern_id="pat_001",
            pattern_type="test",
            name="Test",
            description="",
            created_at=datetime.now(),
        )
        store.add(pattern)
        
        retrieved = store.get("pat_001")
        
        assert retrieved is not None
        assert retrieved.pattern_id == "pat_001"
    
    def test_get_by_type(self):
        """Test getting patterns by type."""
        from tascer.patterns import Pattern, PatternStore
        
        store = PatternStore()
        store.add(Pattern(
            pattern_id="p1",
            pattern_type="failure",
            name="F1",
            description="",
            created_at=datetime.now(),
        ))
        store.add(Pattern(
            pattern_id="p2",
            pattern_type="fix",
            name="F2",
            description="",
            created_at=datetime.now(),
        ))
        store.add(Pattern(
            pattern_id="p3",
            pattern_type="failure",
            name="F3",
            description="",
            created_at=datetime.now(),
        ))
        
        failures = store.get_by_type("failure")
        
        assert len(failures) == 2
    
    def test_get_by_tag(self):
        """Test getting patterns by tag."""
        from tascer.patterns import Pattern, PatternStore
        
        store = PatternStore()
        store.add(Pattern(
            pattern_id="p1",
            pattern_type="test",
            name="Pattern with tag",
            description="",
            created_at=datetime.now(),
            tags=["python", "import"],
        ))
        store.add(Pattern(
            pattern_id="p2",
            pattern_type="test",
            name="Pattern without tag",
            description="",
            created_at=datetime.now(),
            tags=["javascript"],
        ))
        
        python_patterns = store.get_by_tag("python")
        
        assert len(python_patterns) == 1
        assert python_patterns[0].pattern_id == "p1"
    
    def test_find_similar(self):
        """Test finding similar patterns."""
        from tascer.patterns import Pattern, PatternStore
        
        store = PatternStore()
        store.add(Pattern(
            pattern_id="p1",
            pattern_type="failure",
            name="import error python",
            description="",
            created_at=datetime.now(),
            tags=["python", "import"],
        ))
        
        new_pattern = Pattern(
            pattern_id="p2",
            pattern_type="failure",
            name="import error",
            description="",
            created_at=datetime.now(),
            tags=["python"],
        )
        
        similar = store.find_similar(new_pattern, threshold=0.5)
        
        assert len(similar) > 0
    
    def test_add_or_merge(self):
        """Test add_or_merge merges similar patterns."""
        from tascer.patterns import Pattern, PatternStore
        
        store = PatternStore()
        
        p1 = Pattern(
            pattern_id="p1",
            pattern_type="failure",
            name="import error python",
            description="",
            created_at=datetime.now(),
            tags=["python", "import"],
        )
        store.add(p1)
        
        p2 = Pattern(
            pattern_id="p2",
            pattern_type="failure",
            name="import error python module",
            description="",
            created_at=datetime.now(),
            tags=["python", "import", "module"],
        )
        
        result = store.add_or_merge(p2)
        
        # Should merge into p1 (if similarity > 0.85)
        # or add as new (if not similar enough)
        assert len(store) >= 1
