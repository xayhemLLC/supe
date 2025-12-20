"""Base classes for Agent Actions.

Provides the foundational types for agent action execution, logging, and validation.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


class ActionType(str, Enum):
    """Types of actions an agent can take."""
    
    # File Operations
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    
    # Search
    SEARCH_CODEBASE = "search_codebase"
    SEARCH_SYMBOLS = "search_symbols"
    
    # Edit
    EDIT_FILE = "edit_file"  # Diff-based editing
    
    # Terminal
    RUN_CMD = "run_cmd"
    RUN_TESTS = "run_tests"
    
    # User Interaction
    ASK_USER = "ask_user"
    NOTIFY_USER = "notify_user"
    
    # Control Flow
    FINISH = "finish"
    ABORT = "abort"
    CHECKPOINT = "checkpoint"
    
    # Existing mutation actions (aliased)
    APPLY_PATCH = "apply_patch"
    LINT_FIX = "lint_fix"
    FORMAT_FIX = "format_fix"
    TEST_TRIAGE = "test_triage"


@dataclass
class ValidationResult:
    """Result of validating an action's output."""
    name: str
    status: Literal["pass", "fail", "skip"]
    message: str = ""
    details: Optional[Dict[str, Any]] = None


@dataclass
class AgentAction:
    """A single action taken by an agent.
    
    Represents one step in an agent's execution, with full context for
    logging, auditing, and replay.
    """
    id: str
    type: ActionType
    params: Dict[str, Any]
    
    # Context
    tasc_id: str
    session_id: str
    step_index: int
    
    # Timing
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: float = 0
    
    # Optional reasoning
    thought: Optional[str] = None  # Agent's reasoning for this action
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, ActionType) else self.type,
            "params": self.params,
            "tasc_id": self.tasc_id,
            "session_id": self.session_id,
            "step_index": self.step_index,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "thought": self.thought,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentAction":
        action_type = data.get("type", "")
        if isinstance(action_type, str):
            try:
                action_type = ActionType(action_type)
            except ValueError:
                pass  # Keep as string for unknown types
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=action_type,
            params=data.get("params", {}),
            tasc_id=data.get("tasc_id", ""),
            session_id=data.get("session_id", ""),
            step_index=data.get("step_index", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            duration_ms=data.get("duration_ms", 0),
            thought=data.get("thought"),
        )
    
    @classmethod
    def create(
        cls,
        action_type: ActionType,
        params: Dict[str, Any],
        tasc_id: str,
        session_id: str,
        step_index: int,
        thought: Optional[str] = None,
    ) -> "AgentAction":
        """Factory method for creating a new action."""
        return cls(
            id=f"action_{uuid.uuid4().hex[:12]}",
            type=action_type,
            params=params,
            tasc_id=tasc_id,
            session_id=session_id,
            step_index=step_index,
            thought=thought,
        )


@dataclass
class ActionResult:
    """Result of executing an agent action.
    
    Contains the output, any validation results, and status information.
    """
    action_id: str
    status: Literal["ok", "failed", "reverted", "pending"]
    
    # Output
    output: Any = None  # The primary output (file content, search results, etc.)
    output_summary: str = ""  # Human-readable summary
    
    # Validation
    validations: List[ValidationResult] = field(default_factory=list)
    
    # Error info
    error: Optional[str] = None
    
    # Timing
    duration_ms: float = 0
    
    # For tracking
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "status": self.status,
            "output": self.output if isinstance(self.output, (str, int, float, bool, list, dict, type(None))) else str(self.output),
            "output_summary": self.output_summary,
            "validations": [
                {"name": v.name, "status": v.status, "message": v.message, "details": v.details}
                for v in self.validations
            ],
            "error": self.error,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionResult":
        validations = [
            ValidationResult(
                name=v["name"],
                status=v["status"],
                message=v.get("message", ""),
                details=v.get("details"),
            )
            for v in data.get("validations", [])
        ]
        
        return cls(
            action_id=data.get("action_id", ""),
            status=data.get("status", "ok"),
            output=data.get("output"),
            output_summary=data.get("output_summary", ""),
            validations=validations,
            error=data.get("error"),
            duration_ms=data.get("duration_ms", 0),
            timestamp=data.get("timestamp", ""),
        )
    
    @property
    def is_success(self) -> bool:
        return self.status == "ok"
    
    @property
    def all_validations_passed(self) -> bool:
        return all(v.status == "pass" for v in self.validations)


@dataclass
class ActionMetadata:
    """Metadata about an action type."""
    action_type: ActionType
    name: str
    description: str
    
    # Classification
    is_mutation: bool = False  # Does it change state?
    is_dangerous: bool = False  # Requires extra caution?
    requires_approval: bool = False  # Needs human sign-off?
    
    # Constraints
    allowed_in_sandbox: bool = True
    max_retries: int = 3
    timeout_seconds: int = 60
    
    # Parameter schema
    required_params: List[str] = field(default_factory=list)
    optional_params: List[str] = field(default_factory=list)
