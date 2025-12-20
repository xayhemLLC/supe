"""Action Registry.

Central registry for all action types with metadata, handlers, and lookup.
"""

from typing import Callable, Dict, List, Optional

from .base import ActionType, ActionMetadata, AgentAction, ActionResult


# Handler type: function that takes action and returns result
ActionHandler = Callable[[AgentAction], ActionResult]

# Global registry
_action_metadata: Dict[ActionType, ActionMetadata] = {}
_action_handlers: Dict[ActionType, ActionHandler] = {}


def register_action(
    action_type: ActionType,
    metadata: ActionMetadata,
    handler: Optional[ActionHandler] = None,
) -> None:
    """Register an action type with its metadata and optional handler."""
    _action_metadata[action_type] = metadata
    if handler:
        _action_handlers[action_type] = handler


def get_action_handler(action_type: ActionType) -> Optional[ActionHandler]:
    """Get the handler for an action type."""
    return _action_handlers.get(action_type)


def get_action_metadata(action_type: ActionType) -> Optional[ActionMetadata]:
    """Get metadata for an action type."""
    return _action_metadata.get(action_type)


def list_action_types() -> List[ActionType]:
    """List all registered action types."""
    return list(_action_metadata.keys())


def is_dangerous(action_type: ActionType) -> bool:
    """Check if an action type is dangerous."""
    meta = _action_metadata.get(action_type)
    return meta.is_dangerous if meta else False


def requires_approval(action_type: ActionType) -> bool:
    """Check if an action type requires human approval."""
    meta = _action_metadata.get(action_type)
    return meta.requires_approval if meta else False


def is_mutation(action_type: ActionType) -> bool:
    """Check if an action type mutates state."""
    meta = _action_metadata.get(action_type)
    return meta.is_mutation if meta else False


# ---------------------------------------------------------------------------
# Register Built-in Actions
# ---------------------------------------------------------------------------

# File Operations
register_action(
    ActionType.READ_FILE,
    ActionMetadata(
        action_type=ActionType.READ_FILE,
        name="Read File",
        description="Read the contents of a file",
        is_mutation=False,
        is_dangerous=False,
        required_params=["path"],
        optional_params=["start_line", "end_line", "encoding"],
    ),
)

register_action(
    ActionType.WRITE_FILE,
    ActionMetadata(
        action_type=ActionType.WRITE_FILE,
        name="Write File",
        description="Write content to a file (creates or overwrites)",
        is_mutation=True,
        is_dangerous=True,
        required_params=["path", "content"],
        optional_params=["encoding", "create_dirs"],
    ),
)

register_action(
    ActionType.DELETE_FILE,
    ActionMetadata(
        action_type=ActionType.DELETE_FILE,
        name="Delete File",
        description="Delete a file from the filesystem",
        is_mutation=True,
        is_dangerous=True,
        requires_approval=True,  # Always requires approval
        required_params=["path"],
    ),
)

# Search
register_action(
    ActionType.SEARCH_CODEBASE,
    ActionMetadata(
        action_type=ActionType.SEARCH_CODEBASE,
        name="Search Codebase",
        description="Search for text patterns in the codebase",
        is_mutation=False,
        required_params=["query"],
        optional_params=["path", "include_patterns", "exclude_patterns", "max_results"],
    ),
)

register_action(
    ActionType.SEARCH_SYMBOLS,
    ActionMetadata(
        action_type=ActionType.SEARCH_SYMBOLS,
        name="Search Symbols",
        description="Search for function/class definitions",
        is_mutation=False,
        required_params=["query"],
        optional_params=["symbol_type", "path"],
    ),
)

# Edit
register_action(
    ActionType.EDIT_FILE,
    ActionMetadata(
        action_type=ActionType.EDIT_FILE,
        name="Edit File",
        description="Apply a diff patch to a file",
        is_mutation=True,
        is_dangerous=False,
        required_params=["path", "diff"],
        optional_params=["reason"],
    ),
)

# Terminal
register_action(
    ActionType.RUN_CMD,
    ActionMetadata(
        action_type=ActionType.RUN_CMD,
        name="Run Command",
        description="Execute a shell command",
        is_mutation=True,
        is_dangerous=True,
        required_params=["command"],
        optional_params=["cwd", "timeout", "allow_network"],
        timeout_seconds=300,
    ),
)

register_action(
    ActionType.RUN_TESTS,
    ActionMetadata(
        action_type=ActionType.RUN_TESTS,
        name="Run Tests",
        description="Execute test suite",
        is_mutation=False,
        is_dangerous=False,
        required_params=[],
        optional_params=["pattern", "path", "verbose"],
        timeout_seconds=600,
    ),
)

# User Interaction
register_action(
    ActionType.ASK_USER,
    ActionMetadata(
        action_type=ActionType.ASK_USER,
        name="Ask User",
        description="Ask the user a question and wait for response",
        is_mutation=False,
        is_dangerous=False,
        required_params=["question"],
        optional_params=["blocking", "choices"],
    ),
)

register_action(
    ActionType.NOTIFY_USER,
    ActionMetadata(
        action_type=ActionType.NOTIFY_USER,
        name="Notify User",
        description="Send a notification to the user",
        is_mutation=False,
        is_dangerous=False,
        required_params=["message"],
        optional_params=["level"],  # info, warning, error
    ),
)

# Control Flow
register_action(
    ActionType.FINISH,
    ActionMetadata(
        action_type=ActionType.FINISH,
        name="Finish",
        description="Mark the task as complete",
        is_mutation=False,
        is_dangerous=False,
        required_params=["summary"],
        optional_params=["risks", "follow_ups"],
    ),
)

register_action(
    ActionType.ABORT,
    ActionMetadata(
        action_type=ActionType.ABORT,
        name="Abort",
        description="Abort the current task",
        is_mutation=False,
        is_dangerous=False,
        required_params=["reason"],
    ),
)

register_action(
    ActionType.CHECKPOINT,
    ActionMetadata(
        action_type=ActionType.CHECKPOINT,
        name="Checkpoint",
        description="Create a checkpoint for rollback",
        is_mutation=False,
        is_dangerous=False,
        required_params=[],
        optional_params=["name"],
    ),
)

# Existing mutation actions
register_action(
    ActionType.APPLY_PATCH,
    ActionMetadata(
        action_type=ActionType.APPLY_PATCH,
        name="Apply Patch",
        description="Apply a unified diff patch to files",
        is_mutation=True,
        is_dangerous=False,
        required_params=["patch"],
        optional_params=["cwd"],
    ),
)

register_action(
    ActionType.LINT_FIX,
    ActionMetadata(
        action_type=ActionType.LINT_FIX,
        name="Lint Fix",
        description="Run linter with auto-fix",
        is_mutation=True,
        is_dangerous=False,
        required_params=["path"],
        optional_params=["linter"],
    ),
)

register_action(
    ActionType.FORMAT_FIX,
    ActionMetadata(
        action_type=ActionType.FORMAT_FIX,
        name="Format Fix",
        description="Run formatter on code",
        is_mutation=True,
        is_dangerous=False,
        required_params=["path"],
        optional_params=["formatter"],
    ),
)

register_action(
    ActionType.TEST_TRIAGE,
    ActionMetadata(
        action_type=ActionType.TEST_TRIAGE,
        name="Test Triage",
        description="Run tests and triage failures",
        is_mutation=False,
        is_dangerous=False,
        required_params=[],
        optional_params=["path", "pattern"],
    ),
)
