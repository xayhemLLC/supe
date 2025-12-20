"""Action Registry - Load and query primitive actions.

This module provides:
- ActionMetadata dataclass with all action properties
- Registry loader from actions.yaml
- Query functions for action lookup and safety checks
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml


class RiskLevel(Enum):
    """Risk levels for actions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionCategory(Enum):
    """Action categories."""
    OBSERVATION = "observation"
    MUTATION = "mutation"
    CONTROL = "control"


@dataclass
class ActionMetadata:
    """Metadata for a primitive action.
    
    This defines the complete contract for an action including
    safety properties, permissions, and expected evidence.
    """
    
    id: str
    name: str
    description: str
    category: ActionCategory
    mutates_state: bool
    risk_level: RiskLevel
    permissions_required: List[str] = field(default_factory=list)
    evidence_produced: List[str] = field(default_factory=list)
    rollback_supported: bool = False
    sandbox_only: bool = False
    requires_checkpoint: bool = False
    gated: bool = False
    frontend_scope: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "mutates_state": self.mutates_state,
            "risk_level": self.risk_level.value,
            "permissions_required": self.permissions_required,
            "evidence_produced": self.evidence_produced,
            "rollback_supported": self.rollback_supported,
            "sandbox_only": self.sandbox_only,
            "requires_checkpoint": self.requires_checkpoint,
            "gated": self.gated,
            "frontend_scope": self.frontend_scope,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionMetadata":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=ActionCategory(data.get("category", "observation")),
            mutates_state=data.get("mutates_state", False),
            risk_level=RiskLevel(data.get("risk_level", "low")),
            permissions_required=data.get("permissions_required", []),
            evidence_produced=data.get("evidence_produced", []),
            rollback_supported=data.get("rollback_supported", False),
            sandbox_only=data.get("sandbox_only", False),
            requires_checkpoint=data.get("requires_checkpoint", False),
            gated=data.get("gated", False),
            frontend_scope=data.get("frontend_scope", []),
        )
    
    def is_mutation(self) -> bool:
        """Check if this action mutates state."""
        return self.mutates_state or self.category == ActionCategory.MUTATION
    
    def is_high_risk(self) -> bool:
        """Check if this action is high risk."""
        return self.risk_level == RiskLevel.HIGH
    
    def requires_permission(self, permission: str) -> bool:
        """Check if action requires a specific permission."""
        return permission in self.permissions_required


class ActionRegistry:
    """Registry of all primitive actions.
    
    Loads action definitions from actions.yaml and provides
    query functions for action lookup and safety checks.
    """
    
    def __init__(self, yaml_path: Optional[str] = None):
        """Initialize registry.
        
        Args:
            yaml_path: Path to actions.yaml. Defaults to module directory.
        """
        self._actions: Dict[str, ActionMetadata] = {}
        self._yaml_path = yaml_path or self._default_yaml_path()
        self._loaded = False
    
    def _default_yaml_path(self) -> str:
        """Get default path to actions.yaml."""
        return os.path.join(os.path.dirname(__file__), "actions.yaml")
    
    def load(self) -> None:
        """Load actions from YAML file."""
        if not os.path.exists(self._yaml_path):
            raise FileNotFoundError(f"Actions file not found: {self._yaml_path}")
        
        with open(self._yaml_path, "r") as f:
            data = yaml.safe_load(f)
        
        if not data or "actions" not in data:
            raise ValueError("Invalid actions.yaml format")
        
        for action_id, action_data in data["actions"].items():
            self._actions[action_id] = ActionMetadata.from_dict(action_data)
        
        self._loaded = True
    
    def ensure_loaded(self) -> None:
        """Ensure registry is loaded."""
        if not self._loaded:
            self.load()
    
    def get(self, action_id: str) -> Optional[ActionMetadata]:
        """Get action by ID.
        
        Args:
            action_id: Action identifier (e.g., "terminal.run")
        
        Returns:
            ActionMetadata or None if not found.
        """
        self.ensure_loaded()
        return self._actions.get(action_id)
    
    def get_required(self, action_id: str) -> ActionMetadata:
        """Get action by ID, raising if not found.
        
        Args:
            action_id: Action identifier.
        
        Returns:
            ActionMetadata.
        
        Raises:
            KeyError: If action not found.
        """
        action = self.get(action_id)
        if action is None:
            raise KeyError(f"Unknown action: {action_id}")
        return action
    
    def list_all(self) -> List[ActionMetadata]:
        """Get all registered actions."""
        self.ensure_loaded()
        return list(self._actions.values())
    
    def list_by_category(self, category: ActionCategory) -> List[ActionMetadata]:
        """Get actions by category."""
        self.ensure_loaded()
        return [a for a in self._actions.values() if a.category == category]
    
    def list_observations(self) -> List[ActionMetadata]:
        """Get all observation (read-only) actions."""
        return self.list_by_category(ActionCategory.OBSERVATION)
    
    def list_mutations(self) -> List[ActionMetadata]:
        """Get all mutation (state-changing) actions."""
        return self.list_by_category(ActionCategory.MUTATION)
    
    def list_by_risk(self, level: RiskLevel) -> List[ActionMetadata]:
        """Get actions by risk level."""
        self.ensure_loaded()
        return [a for a in self._actions.values() if a.risk_level == level]
    
    def list_requiring_checkpoint(self) -> List[ActionMetadata]:
        """Get actions that require an active checkpoint."""
        self.ensure_loaded()
        return [a for a in self._actions.values() if a.requires_checkpoint]
    
    def list_sandbox_only(self) -> List[ActionMetadata]:
        """Get actions that can only run in sandbox mode."""
        self.ensure_loaded()
        return [a for a in self._actions.values() if a.sandbox_only]
    
    def register_action(self, action: ActionMetadata) -> None:
        """Register an action dynamically (used by plugins).
        
        Plugins can register their own actions at runtime:
        
            registry.register_action(ActionMetadata(
                id="browser.get",
                name="Browser GET",
                ...
            ))
        
        Args:
            action: ActionMetadata to register.
        """
        self._actions[action.id] = action
    
    def register_actions(self, actions: List[ActionMetadata]) -> None:
        """Register multiple actions at once.
        
        Args:
            actions: List of ActionMetadata to register.
        """
        for action in actions:
            self.register_action(action)
    
    def is_mutation(self, action_id: str) -> bool:
        """Check if action mutates state."""
        action = self.get(action_id)
        return action.is_mutation() if action else False
    
    def is_legal(
        self,
        action_id: str,
        permissions: List[str],
        has_checkpoint: bool = False,
        in_sandbox: bool = False,
    ) -> tuple[bool, str]:
        """Check if action is legal given current context.
        
        Args:
            action_id: Action to check.
            permissions: Currently granted permissions.
            has_checkpoint: Whether a checkpoint is active.
            in_sandbox: Whether currently in sandbox mode.
        
        Returns:
            Tuple of (is_legal, reason).
        """
        action = self.get(action_id)
        if action is None:
            return False, f"Unknown action: {action_id}"
        
        # Check permissions
        for perm in action.permissions_required:
            if perm not in permissions:
                return False, f"Missing permission: {perm}"
        
        # Check checkpoint requirement
        if action.requires_checkpoint and not has_checkpoint:
            return False, "Action requires active checkpoint"
        
        # Check sandbox requirement
        if action.sandbox_only and not in_sandbox:
            return False, "Action can only run in sandbox mode"
        
        # Check gated actions
        if action.gated:
            if "gated_actions" not in permissions:
                return False, "Action is gated and requires explicit approval"
        
        return True, "Action is legal"


# Global registry instance
_registry: Optional[ActionRegistry] = None


def get_registry() -> ActionRegistry:
    """Get the global action registry instance."""
    global _registry
    if _registry is None:
        _registry = ActionRegistry()
    return _registry


def get_action(action_id: str) -> Optional[ActionMetadata]:
    """Get action metadata by ID."""
    return get_registry().get(action_id)


def list_actions() -> List[ActionMetadata]:
    """List all registered actions."""
    return get_registry().list_all()


def is_mutation(action_id: str) -> bool:
    """Check if action mutates state."""
    return get_registry().is_mutation(action_id)


def check_legality(
    action_id: str,
    permissions: List[str],
    has_checkpoint: bool = False,
    in_sandbox: bool = False,
) -> tuple[bool, str]:
    """Check if action is legal."""
    return get_registry().is_legal(
        action_id=action_id,
        permissions=permissions,
        has_checkpoint=has_checkpoint,
        in_sandbox=in_sandbox,
    )
