"""Tests for Tasc action registry."""

import os
import pytest
import tempfile
from pathlib import Path


class TestActionMetadata:
    """Tests for ActionMetadata dataclass."""
    
    def test_from_dict_basic(self):
        """Test creating ActionMetadata from dict."""
        from tascer.action_registry import ActionMetadata, ActionCategory, RiskLevel
        
        data = {
            "id": "test.action",
            "name": "Test Action",
            "description": "A test action",
            "category": "observation",
            "mutates_state": False,
            "risk_level": "low",
            "permissions_required": ["test"],
            "evidence_produced": ["result"],
            "rollback_supported": False,
            "sandbox_only": False,
        }
        
        action = ActionMetadata.from_dict(data)
        
        assert action.id == "test.action"
        assert action.name == "Test Action"
        assert action.category == ActionCategory.OBSERVATION
        assert action.risk_level == RiskLevel.LOW
        assert not action.mutates_state
    
    def test_from_dict_mutation_with_checkpoint(self):
        """Test mutation action requires checkpoint."""
        from tascer.action_registry import ActionMetadata, ActionCategory, RiskLevel
        
        data = {
            "id": "file.write",
            "name": "Write File",
            "description": "Write to file",
            "category": "mutation",
            "mutates_state": True,
            "risk_level": "medium",
            "permissions_required": ["file_write"],
            "evidence_produced": ["sha256_after"],
            "rollback_supported": True,
            "sandbox_only": False,
            "requires_checkpoint": True,
        }
        
        action = ActionMetadata.from_dict(data)
        
        assert action.is_mutation()
        assert action.requires_checkpoint
        assert action.rollback_supported
    
    def test_is_mutation_by_category(self):
        """Test is_mutation detects by category."""
        from tascer.action_registry import ActionMetadata, ActionCategory, RiskLevel
        
        mutation = ActionMetadata(
            id="test.mut",
            name="Test",
            description="",
            category=ActionCategory.MUTATION,
            mutates_state=False,  # Even if False, category wins
            risk_level=RiskLevel.LOW,
            permissions_required=[],
            evidence_produced=[],
            rollback_supported=False,
            sandbox_only=False,
        )
        
        assert mutation.is_mutation()
    
    def test_is_mutation_by_flag(self):
        """Test is_mutation detects by flag."""
        from tascer.action_registry import ActionMetadata, ActionCategory, RiskLevel
        
        action = ActionMetadata(
            id="test.obs",
            name="Test",
            description="",
            category=ActionCategory.OBSERVATION,
            mutates_state=True,  # Flag overrides
            risk_level=RiskLevel.LOW,
            permissions_required=[],
            evidence_produced=[],
            rollback_supported=False,
            sandbox_only=False,
        )
        
        assert action.is_mutation()


class TestActionRegistry:
    """Tests for ActionRegistry loading and queries."""
    
    def test_load_actions_yaml(self):
        """Test loading actions.yaml."""
        from tascer.action_registry import get_registry
        
        registry = get_registry()
        registry.load()
        
        actions = registry.list_all()
        assert len(actions) == 32
    
    def test_get_action_by_id(self):
        """Test getting action by ID."""
        from tascer.action_registry import get_registry
        
        registry = get_registry()
        registry.load()
        
        action = registry.get("terminal.run")
        assert action is not None
        assert action.name == "Run Terminal Command"
        assert not action.mutates_state
    
    def test_list_observations(self):
        """Test listing observation actions."""
        from tascer.action_registry import get_registry, ActionCategory
        
        registry = get_registry()
        registry.load()
        
        observations = registry.list_observations()
        assert len(observations) == 15
        for action in observations:
            assert action.category == ActionCategory.OBSERVATION
    
    def test_list_mutations(self):
        """Test listing mutation actions."""
        from tascer.action_registry import get_registry, ActionCategory
        
        registry = get_registry()
        registry.load()
        
        mutations = registry.list_mutations()
        assert len(mutations) == 13
        for action in mutations:
            assert action.category == ActionCategory.MUTATION
    
    def test_get_nonexistent_action(self):
        """Test getting nonexistent action returns None."""
        from tascer.action_registry import get_registry
        
        registry = get_registry()
        registry.load()
        
        action = registry.get("nonexistent.action")
        assert action is None
    
    def test_is_legal_missing_permissions(self):
        """Test legality check fails with missing permissions."""
        from tascer.action_registry import get_registry
        
        registry = get_registry()
        registry.load()
        
        is_legal, reason = registry.is_legal(
            "terminal.run",
            permissions=[],  # No permissions
        )
        
        assert not is_legal
        assert "permission" in reason.lower()
    
    def test_is_legal_with_permissions(self):
        """Test legality check passes with correct permissions."""
        from tascer.action_registry import get_registry
        
        registry = get_registry()
        registry.load()
        
        is_legal, reason = registry.is_legal(
            "terminal.run",
            permissions=["terminal"],
        )
        
        assert is_legal
    
    def test_is_legal_mutation_needs_checkpoint(self):
        """Test mutation action requires checkpoint."""
        from tascer.action_registry import get_registry
        
        registry = get_registry()
        registry.load()
        
        is_legal, reason = registry.is_legal(
            "file.write",
            permissions=["file_write"],
            has_checkpoint=False,
        )
        
        assert not is_legal
        assert "checkpoint" in reason.lower()
    
    def test_is_legal_mutation_with_checkpoint(self):
        """Test mutation action passes with checkpoint."""
        from tascer.action_registry import get_registry
        
        registry = get_registry()
        registry.load()
        
        is_legal, reason = registry.is_legal(
            "file.write",
            permissions=["file_write"],
            has_checkpoint=True,
        )
        
        assert is_legal


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def test_get_action(self):
        """Test get_action convenience function."""
        from tascer.action_registry import get_action
        
        action = get_action("git.status")
        assert action is not None
        assert action.id == "git.status"
    
    def test_list_actions(self):
        """Test list_actions convenience function."""
        from tascer.action_registry import list_actions
        
        all_actions = list_actions()
        assert len(all_actions) == 32
    
    def test_is_mutation(self):
        """Test is_mutation convenience function."""
        from tascer.action_registry import is_mutation
        
        assert is_mutation("file.write")
        assert not is_mutation("terminal.run")
    
    def test_check_legality(self):
        """Test check_legality convenience function."""
        from tascer.action_registry import check_legality
        
        is_legal, _ = check_legality(
            "terminal.run",
            permissions=["terminal"],
        )
        assert is_legal
