"""Tests for Tasc Overlord decision system."""

import pytest


class TestStopConditions:
    """Tests for stop condition evaluation."""
    
    def test_no_legal_actions_triggers_stop(self):
        """Test stop when no legal actions remain."""
        from tascer.overlord.decision import (
            StopConditionState,
            evaluate_stop_conditions,
            StopCondition,
        )
        
        state = StopConditionState(
            legal_actions=set(),  # No legal actions
        )
        
        triggered = evaluate_stop_conditions(state)
        
        reasons = [t[0] for t in triggered]
        assert StopCondition.NO_LEGAL_ACTIONS in reasons
    
    def test_budget_exhausted_triggers_stop(self):
        """Test stop when budget is exhausted."""
        from tascer.overlord.decision import (
            StopConditionState,
            evaluate_stop_conditions,
            StopCondition,
        )
        
        state = StopConditionState(
            legal_actions={"terminal.run"},
            actions_taken=100,
            max_actions=100,
        )
        
        triggered = evaluate_stop_conditions(state)
        
        reasons = [t[0] for t in triggered]
        assert StopCondition.BUDGET_EXHAUSTED in reasons
    
    def test_goal_achieved_triggers_stop(self):
        """Test stop when goal is achieved."""
        from tascer.overlord.decision import (
            StopConditionState,
            evaluate_stop_conditions,
            StopCondition,
        )
        
        state = StopConditionState(
            legal_actions={"terminal.run"},
            goal_achieved=True,
        )
        
        triggered = evaluate_stop_conditions(state)
        
        reasons = [t[0] for t in triggered]
        assert StopCondition.GOAL_ACHIEVED in reasons
    
    def test_low_info_gain_triggers_stop(self):
        """Test stop when information gain is low."""
        from tascer.overlord.decision import (
            StopConditionState,
            evaluate_stop_conditions,
            StopCondition,
        )
        
        state = StopConditionState(
            legal_actions={"terminal.run"},
            recent_info_gains=[0.01, 0.02, 0.01],  # All below threshold
            info_gain_threshold=0.1,
        )
        
        triggered = evaluate_stop_conditions(state)
        
        reasons = [t[0] for t in triggered]
        assert StopCondition.LOW_INFORMATION_GAIN in reasons
    
    def test_repeated_observations_triggers_stop(self):
        """Test stop when observations repeat."""
        from tascer.overlord.decision import (
            StopConditionState,
            evaluate_stop_conditions,
            StopCondition,
        )
        
        state = StopConditionState(
            legal_actions={"terminal.run"},
            recent_observation_hashes=["abc", "abc", "abc"],  # Same hash
            max_repeated_observations=3,
        )
        
        triggered = evaluate_stop_conditions(state)
        
        reasons = [t[0] for t in triggered]
        assert StopCondition.REPEATED_OBSERVATIONS in reasons
    
    def test_safety_violation_triggers_stop(self):
        """Test stop on safety violation."""
        from tascer.overlord.decision import (
            StopConditionState,
            evaluate_stop_conditions,
            StopCondition,
        )
        
        state = StopConditionState(
            legal_actions={"terminal.run"},
            safety_violations=["Destructive command detected"],
        )
        
        triggered = evaluate_stop_conditions(state)
        
        reasons = [t[0] for t in triggered]
        assert StopCondition.SAFETY_GUARD in reasons
    
    def test_no_stop_when_all_good(self):
        """Test no stop when everything is fine."""
        from tascer.overlord.decision import (
            StopConditionState,
            evaluate_stop_conditions,
        )
        
        state = StopConditionState(
            legal_actions={"terminal.run", "file.read"},
            actions_taken=5,
            max_actions=100,
            goal_achieved=False,
        )
        
        triggered = evaluate_stop_conditions(state)
        
        assert len(triggered) == 0


class TestOverlordDecision:
    """Tests for OverlordDecision creation."""
    
    def test_should_stop_returns_decision(self):
        """Test should_stop returns stop decision."""
        from tascer.overlord.decision import (
            StopConditionState,
            should_stop,
        )
        
        state = StopConditionState(
            legal_actions=set(),  # No legal actions
        )
        
        decision = should_stop(state)
        
        assert decision is not None
        assert decision.decision == "STOP"
        assert decision.stop_reason is not None
    
    def test_should_stop_returns_none_when_ok(self):
        """Test should_stop returns None when no stop needed."""
        from tascer.overlord.decision import (
            StopConditionState,
            should_stop,
        )
        
        state = StopConditionState(
            legal_actions={"terminal.run"},
        )
        
        decision = should_stop(state)
        
        assert decision is None
    
    def test_create_continue_decision(self):
        """Test creating continue decision."""
        from tascer.overlord.decision import create_continue_decision
        
        decision = create_continue_decision(
            action="terminal.run",
            inputs={"command": "ls"},
            narrative="Listing files to understand structure",
            confidence=0.9,
        )
        
        assert decision.decision == "CONTINUE"
        assert decision.next_action == "terminal.run"
        assert decision.confidence == 0.9
    
    def test_create_backtrack_decision(self):
        """Test creating backtrack decision."""
        from tascer.overlord.decision import create_backtrack_decision
        
        decision = create_backtrack_decision(
            narrative="Wrong approach, trying different strategy",
        )
        
        assert decision.decision == "BACKTRACK"


class TestLegalityChecks:
    """Tests for action legality checking."""
    
    def test_destructive_pattern_blocked(self):
        """Test destructive commands are blocked."""
        from tascer.overlord.legality import check_action_legality
        
        result = check_action_legality(
            action_id="terminal.run",
            inputs={"command": "rm -rf /"},
            permissions={"terminal"},
        )
        
        assert not result.is_legal
        assert len(result.violations) > 0
    
    def test_safe_command_allowed(self):
        """Test safe commands are allowed."""
        from tascer.overlord.legality import check_action_legality
        
        result = check_action_legality(
            action_id="terminal.run",
            inputs={"command": "ls -la"},
            permissions={"terminal"},
        )
        
        assert result.is_legal
    
    def test_missing_permissions_blocked(self):
        """Test missing permissions block action."""
        from tascer.overlord.legality import check_action_legality
        
        result = check_action_legality(
            action_id="terminal.run",
            inputs={"command": "ls"},
            permissions=set(),  # No permissions
        )
        
        assert not result.is_legal
        assert "permissions" in result.violations[0].lower()
    
    def test_mutation_needs_checkpoint(self):
        """Test mutation actions need checkpoint."""
        from tascer.overlord.legality import check_action_legality
        
        result = check_action_legality(
            action_id="file.write",
            inputs={"path": "/test.txt"},
            permissions={"file_write"},
            has_checkpoint=False,
        )
        
        assert not result.is_legal
        assert "checkpoint" in result.violations[0].lower()
    
    def test_mutation_allowed_with_checkpoint(self):
        """Test mutation allowed with checkpoint."""
        from tascer.overlord.legality import check_action_legality
        
        result = check_action_legality(
            action_id="file.write",
            inputs={"path": "/repo/test.txt"},
            permissions={"file_write"},
            has_checkpoint=True,
            repo_root="/repo",
        )
        
        assert result.is_legal
    
    def test_path_outside_repo_blocked(self):
        """Test path outside repo root is blocked."""
        from tascer.overlord.legality import check_action_legality
        
        result = check_action_legality(
            action_id="file.write",
            inputs={"path": "/etc/passwd"},
            permissions={"file_write"},
            has_checkpoint=True,
            repo_root="/home/user/project",
        )
        
        assert not result.is_legal
        assert "outside" in result.violations[0].lower()
    
    def test_gated_action_requires_escalation(self):
        """Test gated actions require escalation."""
        from tascer.overlord.legality import check_action_legality
        
        result = check_action_legality(
            action_id="git.commit",
            inputs={"message": "test"},
            permissions={"git", "git_write"},  # Missing gated_actions
            has_checkpoint=True,
        )
        
        assert result.requires_escalation
        assert result.escalation_reason is not None


class TestPromptInjection:
    """Tests for Overlord prompt building."""
    
    def test_build_action_context(self):
        """Test building action context string."""
        from tascer.overlord.prompt import build_action_context
        
        context = build_action_context(
            permissions=["terminal", "file_read"],
            has_checkpoint=True,
            in_sandbox=False,
        )
        
        assert "Available Actions" in context
        assert "Checkpoint Active: True" in context
    
    def test_build_stop_conditions_context(self):
        """Test building stop conditions context."""
        from tascer.overlord.prompt import build_stop_conditions_context
        
        context = build_stop_conditions_context()
        
        assert "Stop Conditions" in context
        assert "No Legal Actions" in context
        assert "Budget Exhausted" in context
    
    def test_inject_action_metadata(self):
        """Test injecting action metadata."""
        from tascer.overlord.prompt import inject_action_metadata
        
        # First need to load registry
        from tascer.action_registry import get_registry
        registry = get_registry()
        registry.load()
        
        metadata = inject_action_metadata("terminal.run")
        
        assert "terminal.run" in metadata
        assert "Run Terminal Command" in metadata
