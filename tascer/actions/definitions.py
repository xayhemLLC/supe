"""Supe Action Definitions - Validated tool primitives with proof-of-work.

This module defines supe's core actions, analogous to Claude Code's tools but with:
- Pre/post validation gates
- Proof-of-work generation
- CUF phase awareness
- Audit trail integration

Each action is a governed operation that can be validated, audited, and proven.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from tasc import TascPhase


class ActionCategory(Enum):
    """Categories of actions for permission grouping."""

    OBSERVATION = "observation"  # Read-only operations
    MUTATION = "mutation"  # State-changing operations
    EXECUTION = "execution"  # Process execution
    NETWORK = "network"  # Network operations
    AGENT = "agent"  # Sub-agent spawning


class RiskLevel(Enum):
    """Risk level for actions - affects required gates."""

    LOW = "low"  # Safe, read-only
    MEDIUM = "medium"  # Reversible mutations
    HIGH = "high"  # Potentially destructive
    CRITICAL = "critical"  # Requires explicit approval


@dataclass
class ActionParameter:
    """Definition of an action parameter."""

    name: str
    description: str
    param_type: str  # "string", "number", "boolean", "array", "object"
    required: bool = True
    default: Any = None
    enum: list[str] | None = None
    min_value: float | None = None
    max_value: float | None = None

    def to_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format."""
        schema: dict[str, Any] = {
            "description": self.description,
            "type": self.param_type,
        }
        if self.enum:
            schema["enum"] = self.enum
        if self.min_value is not None:
            schema["minimum"] = self.min_value
        if self.max_value is not None:
            schema["maximum"] = self.max_value
        if self.default is not None:
            schema["default"] = self.default
        return schema


@dataclass
class ActionDefinition:
    """Definition of a supe action with validation metadata."""

    name: str
    description: str
    category: ActionCategory
    risk_level: RiskLevel
    parameters: list[ActionParameter] = field(default_factory=list)

    # Validation configuration
    requires_checkpoint: bool = False  # Must have checkpoint before execution
    requires_approval: bool = False  # Requires human approval
    default_pre_gates: list[str] = field(default_factory=list)
    default_post_gates: list[str] = field(default_factory=list)

    # CUF phase restrictions
    allowed_phases: list[TascPhase] | None = None  # None = all phases
    blocked_phases: list[TascPhase] | None = None

    # Proof configuration
    generates_proof: bool = True
    proof_includes_output: bool = False  # Include output in proof hash

    def to_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format for tool definition."""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_schema()
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
            "metadata": {
                "category": self.category.value,
                "risk_level": self.risk_level.value,
                "requires_checkpoint": self.requires_checkpoint,
                "requires_approval": self.requires_approval,
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# Core Action Definitions
# ─────────────────────────────────────────────────────────────────────────────

SUPE_RUN = ActionDefinition(
    name="SupeRun",
    description="""Execute a shell command with validation gates and proof generation.

Similar to Claude Code's Bash tool but with:
- Pre-execution safety validation
- Post-execution result verification
- Proof-of-work generation
- Automatic checkpoint creation for mutations

Usage notes:
- Commands are validated against configured safety patterns
- Mutations require an active checkpoint
- Output is captured and included in audit trail
- Timeout defaults to 120 seconds (max 600 seconds)
""",
    category=ActionCategory.EXECUTION,
    risk_level=RiskLevel.MEDIUM,
    parameters=[
        ActionParameter(
            name="command",
            description="The shell command to execute",
            param_type="string",
        ),
        ActionParameter(
            name="description",
            description="Human-readable description of what this command does",
            param_type="string",
            required=False,
        ),
        ActionParameter(
            name="timeout",
            description="Timeout in milliseconds (max 600000)",
            param_type="number",
            required=False,
            default=120000,
            max_value=600000,
        ),
        ActionParameter(
            name="run_in_background",
            description="Run command in background, retrieve output later with SupeTaskOutput",
            param_type="boolean",
            required=False,
            default=False,
        ),
        ActionParameter(
            name="working_dir",
            description="Working directory for command execution",
            param_type="string",
            required=False,
        ),
        ActionParameter(
            name="env",
            description="Environment variables to set",
            param_type="object",
            required=False,
        ),
    ],
    requires_checkpoint=True,  # Mutations need checkpoint
    default_pre_gates=["safe_commands", "no_destructive_git"],
    default_post_gates=["exit_code_zero"],
    generates_proof=True,
    proof_includes_output=True,
)

SUPE_READ = ActionDefinition(
    name="SupeRead",
    description="""Read a file from the filesystem with content hashing.

Similar to Claude Code's Read tool but with:
- Content hash generation for integrity verification
- Line range support for large files
- Image and PDF support
- Automatic encoding detection

Usage notes:
- Returns content with line numbers (cat -n format)
- Large files can be read in chunks with offset/limit
- Binary files return hash only
- Images are processed for visual analysis
""",
    category=ActionCategory.OBSERVATION,
    risk_level=RiskLevel.LOW,
    parameters=[
        ActionParameter(
            name="file_path",
            description="Absolute path to the file to read",
            param_type="string",
        ),
        ActionParameter(
            name="offset",
            description="Line number to start reading from (1-indexed)",
            param_type="number",
            required=False,
        ),
        ActionParameter(
            name="limit",
            description="Maximum number of lines to read",
            param_type="number",
            required=False,
            default=2000,
        ),
        ActionParameter(
            name="include_hash",
            description="Include content hash in response",
            param_type="boolean",
            required=False,
            default=True,
        ),
    ],
    requires_checkpoint=False,
    default_pre_gates=[],
    default_post_gates=["file_exists"],
    generates_proof=True,
)

SUPE_WRITE = ActionDefinition(
    name="SupeWrite",
    description="""Write content to a file with automatic backup and proof generation.

Similar to Claude Code's Write tool but with:
- Automatic backup before overwrite
- Content hash verification
- Diff generation for audit trail
- Rollback capability

Usage notes:
- Creates backup of existing file before write
- Generates proof with before/after hashes
- Supports atomic writes
- Validates file path is within allowed directories
""",
    category=ActionCategory.MUTATION,
    risk_level=RiskLevel.MEDIUM,
    parameters=[
        ActionParameter(
            name="file_path",
            description="Absolute path to the file to write",
            param_type="string",
        ),
        ActionParameter(
            name="content",
            description="Content to write to the file",
            param_type="string",
        ),
        ActionParameter(
            name="create_backup",
            description="Create backup of existing file",
            param_type="boolean",
            required=False,
            default=True,
        ),
        ActionParameter(
            name="atomic",
            description="Use atomic write (write to temp, then rename)",
            param_type="boolean",
            required=False,
            default=True,
        ),
    ],
    requires_checkpoint=True,
    default_pre_gates=["path_allowed", "not_sensitive_file"],
    default_post_gates=["file_written"],
    generates_proof=True,
)

SUPE_EDIT = ActionDefinition(
    name="SupeEdit",
    description="""Perform exact string replacement in a file with validation.

Similar to Claude Code's Edit tool but with:
- Uniqueness validation before edit
- Automatic backup
- Diff generation
- Rollback support

Usage notes:
- old_string must be unique in file (or use replace_all)
- Creates backup before modification
- Generates proof with exact changes
- Preserves file permissions and encoding
""",
    category=ActionCategory.MUTATION,
    risk_level=RiskLevel.MEDIUM,
    parameters=[
        ActionParameter(
            name="file_path",
            description="Absolute path to the file to edit",
            param_type="string",
        ),
        ActionParameter(
            name="old_string",
            description="The exact string to replace",
            param_type="string",
        ),
        ActionParameter(
            name="new_string",
            description="The replacement string",
            param_type="string",
        ),
        ActionParameter(
            name="replace_all",
            description="Replace all occurrences (default: false, requires unique match)",
            param_type="boolean",
            required=False,
            default=False,
        ),
    ],
    requires_checkpoint=True,
    default_pre_gates=["string_is_unique", "path_allowed"],
    default_post_gates=["edit_applied"],
    generates_proof=True,
)

SUPE_GLOB = ActionDefinition(
    name="SupeGlob",
    description="""Find files matching a glob pattern.

Similar to Claude Code's Glob tool but with:
- Result caching for repeated patterns
- Modification time sorting
- Count limits for large codebases

Usage notes:
- Supports standard glob patterns (**, *, ?)
- Returns files sorted by modification time (newest first)
- Respects .gitignore by default
- Can search specific directory or entire codebase
""",
    category=ActionCategory.OBSERVATION,
    risk_level=RiskLevel.LOW,
    parameters=[
        ActionParameter(
            name="pattern",
            description="Glob pattern to match (e.g., '**/*.py', 'src/**/*.ts')",
            param_type="string",
        ),
        ActionParameter(
            name="path",
            description="Directory to search in (default: current working directory)",
            param_type="string",
            required=False,
        ),
        ActionParameter(
            name="limit",
            description="Maximum number of results to return",
            param_type="number",
            required=False,
            default=100,
        ),
        ActionParameter(
            name="include_hidden",
            description="Include hidden files/directories",
            param_type="boolean",
            required=False,
            default=False,
        ),
    ],
    requires_checkpoint=False,
    generates_proof=False,  # Read-only, no proof needed
)

SUPE_GREP = ActionDefinition(
    name="SupeGrep",
    description="""Search file contents using regex patterns.

Similar to Claude Code's Grep tool (ripgrep-based) but with:
- Result caching
- Context line support
- Multiple output modes

Usage notes:
- Uses ripgrep syntax (not GNU grep)
- Supports full regex patterns
- Can filter by file type or glob
- Returns file paths, content, or counts
""",
    category=ActionCategory.OBSERVATION,
    risk_level=RiskLevel.LOW,
    parameters=[
        ActionParameter(
            name="pattern",
            description="Regex pattern to search for",
            param_type="string",
        ),
        ActionParameter(
            name="path",
            description="File or directory to search",
            param_type="string",
            required=False,
        ),
        ActionParameter(
            name="glob",
            description="Glob pattern to filter files (e.g., '*.py')",
            param_type="string",
            required=False,
        ),
        ActionParameter(
            name="file_type",
            description="File type to search (e.g., 'py', 'js', 'rust')",
            param_type="string",
            required=False,
        ),
        ActionParameter(
            name="output_mode",
            description="Output format",
            param_type="string",
            required=False,
            default="files_with_matches",
            enum=["content", "files_with_matches", "count"],
        ),
        ActionParameter(
            name="context_lines",
            description="Number of context lines before/after match",
            param_type="number",
            required=False,
            default=0,
        ),
        ActionParameter(
            name="case_insensitive",
            description="Case-insensitive search",
            param_type="boolean",
            required=False,
            default=False,
        ),
        ActionParameter(
            name="limit",
            description="Maximum number of results",
            param_type="number",
            required=False,
            default=100,
        ),
    ],
    requires_checkpoint=False,
    generates_proof=False,
)

SUPE_TASK = ActionDefinition(
    name="SupeTask",
    description="""Launch a specialized sub-agent to handle complex tasks.

Similar to Claude Code's Task tool but with:
- CUF phase-aware agent types
- Validation gate inheritance
- Proof chain continuation
- Background execution support

Available agent types:
- explore: Fast codebase exploration (read-only)
- plan: Architecture and implementation planning
- build: Code generation and modification
- validate: Testing and verification
- review: Code review with confidence scoring
- document: Documentation generation

Usage notes:
- Agents inherit parent validation gates
- Background agents can be monitored via SupeTaskOutput
- Each agent execution generates linked proofs
- Agents are CUF phase-aware
""",
    category=ActionCategory.AGENT,
    risk_level=RiskLevel.MEDIUM,
    parameters=[
        ActionParameter(
            name="description",
            description="Short (3-5 word) description of the task",
            param_type="string",
        ),
        ActionParameter(
            name="prompt",
            description="Detailed task description for the agent",
            param_type="string",
        ),
        ActionParameter(
            name="agent_type",
            description="Type of specialized agent to use",
            param_type="string",
            enum=[
                "explore",
                "plan",
                "build",
                "validate",
                "review",
                "document",
                "general",
            ],
        ),
        ActionParameter(
            name="run_in_background",
            description="Run agent in background",
            param_type="boolean",
            required=False,
            default=False,
        ),
        ActionParameter(
            name="max_turns",
            description="Maximum agent turns before stopping",
            param_type="number",
            required=False,
        ),
        ActionParameter(
            name="inherit_gates",
            description="Inherit validation gates from parent",
            param_type="boolean",
            required=False,
            default=True,
        ),
        ActionParameter(
            name="allowed_actions",
            description="Actions this agent is allowed to use",
            param_type="array",
            required=False,
        ),
    ],
    requires_checkpoint=False,  # Agent manages its own checkpoints
    default_pre_gates=["agent_type_valid"],
    generates_proof=True,
    allowed_phases=[
        TascPhase.EXPLORE,
        TascPhase.DEFINE,
        TascPhase.DESIGN,
        TascPhase.BUILD,
        TascPhase.VALIDATE,
        TascPhase.IMPROVE,
    ],
)

SUPE_TASK_OUTPUT = ActionDefinition(
    name="SupeTaskOutput",
    description="""Retrieve output from a running or completed background task.

Similar to Claude Code's TaskOutput tool but with:
- Proof verification for completed tasks
- Progress tracking
- Partial result retrieval

Usage notes:
- Use block=true to wait for completion
- Use block=false for status check
- Returns task status and any available output
- Can retrieve incremental output from long-running tasks
""",
    category=ActionCategory.OBSERVATION,
    risk_level=RiskLevel.LOW,
    parameters=[
        ActionParameter(
            name="task_id",
            description="ID of the task to get output from",
            param_type="string",
        ),
        ActionParameter(
            name="block",
            description="Wait for task completion",
            param_type="boolean",
            required=False,
            default=True,
        ),
        ActionParameter(
            name="timeout",
            description="Maximum wait time in milliseconds",
            param_type="number",
            required=False,
            default=30000,
            max_value=600000,
        ),
    ],
    requires_checkpoint=False,
    generates_proof=False,
)

SUPE_TASK_STOP = ActionDefinition(
    name="SupeTaskStop",
    description="""Stop a running background task.

Usage notes:
- Gracefully terminates the task
- Generates proof of termination
- Any partial results are preserved
""",
    category=ActionCategory.EXECUTION,
    risk_level=RiskLevel.LOW,
    parameters=[
        ActionParameter(
            name="task_id",
            description="ID of the task to stop",
            param_type="string",
        ),
    ],
    requires_checkpoint=False,
    generates_proof=True,
)

SUPE_CHECKPOINT = ActionDefinition(
    name="SupeCheckpoint",
    description="""Create a checkpoint for rollback capability.

Captures current state for potential rollback:
- File system snapshots
- Git state
- Running process state

Usage notes:
- Required before mutation actions
- Enables rollback to known-good state
- Checkpoints are pruned after successful completion
""",
    category=ActionCategory.MUTATION,
    risk_level=RiskLevel.LOW,
    parameters=[
        ActionParameter(
            name="name",
            description="Human-readable checkpoint name",
            param_type="string",
            required=False,
        ),
        ActionParameter(
            name="include_git",
            description="Include git state in checkpoint",
            param_type="boolean",
            required=False,
            default=True,
        ),
        ActionParameter(
            name="paths",
            description="Specific paths to include (default: working directory)",
            param_type="array",
            required=False,
        ),
    ],
    requires_checkpoint=False,  # This creates checkpoints
    generates_proof=True,
)

SUPE_ROLLBACK = ActionDefinition(
    name="SupeRollback",
    description="""Rollback to a previous checkpoint.

Restores state to a checkpoint:
- Reverts file changes
- Restores git state (if included)
- Terminates spawned processes

Usage notes:
- Requires existing checkpoint
- Generates proof of rollback
- Cannot be undone (creates new checkpoint first)
""",
    category=ActionCategory.MUTATION,
    risk_level=RiskLevel.HIGH,
    parameters=[
        ActionParameter(
            name="checkpoint_id",
            description="ID of checkpoint to rollback to (default: most recent)",
            param_type="string",
            required=False,
        ),
        ActionParameter(
            name="confirm",
            description="Confirm rollback (required for safety)",
            param_type="boolean",
            default=False,
        ),
    ],
    requires_checkpoint=False,
    requires_approval=True,
    generates_proof=True,
)

SUPE_PROVE = ActionDefinition(
    name="SupeProve",
    description="""Generate a proof-of-work for a command or assertion.

Creates cryptographic proof that:
- A command was executed with specific output
- A file has specific content
- A test passed with specific results

Usage notes:
- Proofs are SHA256 hashes of inputs + outputs
- Proofs chain together for integrity
- Can be verified with SupeVerify
""",
    category=ActionCategory.OBSERVATION,
    risk_level=RiskLevel.LOW,
    parameters=[
        ActionParameter(
            name="command",
            description="Command to execute and prove",
            param_type="string",
            required=False,
        ),
        ActionParameter(
            name="assertion",
            description="Assertion to prove (file exists, content matches, etc.)",
            param_type="string",
            required=False,
        ),
        ActionParameter(
            name="include_timestamp",
            description="Include timestamp in proof",
            param_type="boolean",
            required=False,
            default=True,
        ),
    ],
    generates_proof=True,
)

SUPE_VERIFY = ActionDefinition(
    name="SupeVerify",
    description="""Verify an existing proof-of-work.

Validates that:
- Proof hash is correctly computed
- Chain integrity is maintained
- Claimed outputs match actual state

Usage notes:
- Returns verification status and details
- Can verify single proof or entire chain
- Reports any integrity violations
""",
    category=ActionCategory.OBSERVATION,
    risk_level=RiskLevel.LOW,
    parameters=[
        ActionParameter(
            name="proof_id",
            description="ID of proof to verify",
            param_type="string",
        ),
        ActionParameter(
            name="verify_chain",
            description="Also verify all proofs in the chain",
            param_type="boolean",
            required=False,
            default=False,
        ),
    ],
    generates_proof=False,
)

SUPE_TRANSITION = ActionDefinition(
    name="SupeTransition",
    description="""Transition a Tasc to a new CUF phase.

Executes phase transition with:
- Gate validation
- Proof generation
- Audit trail update

Usage notes:
- Validates transition is allowed
- Runs phase-specific gates
- Records transition in tasc history
""",
    category=ActionCategory.MUTATION,
    risk_level=RiskLevel.MEDIUM,
    parameters=[
        ActionParameter(
            name="tasc_id",
            description="ID of the tasc to transition",
            param_type="string",
        ),
        ActionParameter(
            name="to_phase",
            description="Target phase",
            param_type="string",
            enum=[
                "explore",
                "define",
                "design",
                "build",
                "validate",
                "ship",
                "observe",
                "improve",
                "institutionalize",
                "retire",
            ],
        ),
        ActionParameter(
            name="reason",
            description="Reason for transition",
            param_type="string",
            required=False,
        ),
        ActionParameter(
            name="validate_gates",
            description="Enforce phase transition gates",
            param_type="boolean",
            required=False,
            default=True,
        ),
    ],
    requires_checkpoint=False,
    default_pre_gates=["phase_transition_allowed"],
    generates_proof=True,
)

SUPE_ASK = ActionDefinition(
    name="SupeAsk",
    description="""Ask the user a question during execution.

Similar to Claude Code's AskUserQuestion but with:
- Response validation
- Audit trail integration
- Timeout handling

Usage notes:
- Use for gathering preferences or decisions
- Supports multiple choice or free text
- Responses are recorded in audit trail
""",
    category=ActionCategory.OBSERVATION,
    risk_level=RiskLevel.LOW,
    parameters=[
        ActionParameter(
            name="question",
            description="The question to ask",
            param_type="string",
        ),
        ActionParameter(
            name="options",
            description="Multiple choice options (if applicable)",
            param_type="array",
            required=False,
        ),
        ActionParameter(
            name="multi_select",
            description="Allow multiple selections",
            param_type="boolean",
            required=False,
            default=False,
        ),
        ActionParameter(
            name="default",
            description="Default option if no response",
            param_type="string",
            required=False,
        ),
        ActionParameter(
            name="timeout",
            description="Timeout in seconds (0 = no timeout)",
            param_type="number",
            required=False,
            default=0,
        ),
    ],
    generates_proof=True,  # Record user decisions
)

SUPE_WEB_FETCH = ActionDefinition(
    name="SupeWebFetch",
    description="""Fetch and process web content.

Similar to Claude Code's WebFetch but with:
- Content hash verification
- Cache management
- Rate limiting

Usage notes:
- Converts HTML to markdown
- Caches responses for 15 minutes
- Follows redirects automatically
- Respects robots.txt
""",
    category=ActionCategory.NETWORK,
    risk_level=RiskLevel.LOW,
    parameters=[
        ActionParameter(
            name="url",
            description="URL to fetch",
            param_type="string",
        ),
        ActionParameter(
            name="prompt",
            description="What to extract from the content",
            param_type="string",
        ),
        ActionParameter(
            name="use_cache",
            description="Use cached response if available",
            param_type="boolean",
            required=False,
            default=True,
        ),
    ],
    generates_proof=True,
)

SUPE_WEB_SEARCH = ActionDefinition(
    name="SupeWebSearch",
    description="""Search the web for information.

Similar to Claude Code's WebSearch but with:
- Result caching
- Source tracking
- Audit trail

Usage notes:
- Returns search results with sources
- Always include Sources section in response
- Supports domain filtering
""",
    category=ActionCategory.NETWORK,
    risk_level=RiskLevel.LOW,
    parameters=[
        ActionParameter(
            name="query",
            description="Search query",
            param_type="string",
        ),
        ActionParameter(
            name="allowed_domains",
            description="Only include results from these domains",
            param_type="array",
            required=False,
        ),
        ActionParameter(
            name="blocked_domains",
            description="Exclude results from these domains",
            param_type="array",
            required=False,
        ),
        ActionParameter(
            name="max_results",
            description="Maximum number of results",
            param_type="number",
            required=False,
            default=10,
        ),
    ],
    generates_proof=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Action Registry
# ─────────────────────────────────────────────────────────────────────────────

ALL_ACTIONS: dict[str, ActionDefinition] = {
    "SupeRun": SUPE_RUN,
    "SupeRead": SUPE_READ,
    "SupeWrite": SUPE_WRITE,
    "SupeEdit": SUPE_EDIT,
    "SupeGlob": SUPE_GLOB,
    "SupeGrep": SUPE_GREP,
    "SupeTask": SUPE_TASK,
    "SupeTaskOutput": SUPE_TASK_OUTPUT,
    "SupeTaskStop": SUPE_TASK_STOP,
    "SupeCheckpoint": SUPE_CHECKPOINT,
    "SupeRollback": SUPE_ROLLBACK,
    "SupeProve": SUPE_PROVE,
    "SupeVerify": SUPE_VERIFY,
    "SupeTransition": SUPE_TRANSITION,
    "SupeAsk": SUPE_ASK,
    "SupeWebFetch": SUPE_WEB_FETCH,
    "SupeWebSearch": SUPE_WEB_SEARCH,
}


def get_action(name: str) -> ActionDefinition | None:
    """Get an action definition by name."""
    return ALL_ACTIONS.get(name)


def list_actions(
    category: ActionCategory | None = None,
    risk_level: RiskLevel | None = None,
) -> list[ActionDefinition]:
    """List actions, optionally filtered by category or risk level."""
    actions = list(ALL_ACTIONS.values())

    if category:
        actions = [a for a in actions if a.category == category]

    if risk_level:
        actions = [a for a in actions if a.risk_level == risk_level]

    return actions


def get_actions_for_phase(phase: TascPhase) -> list[ActionDefinition]:
    """Get actions allowed in a specific CUF phase."""
    result = []
    for action in ALL_ACTIONS.values():
        # Check if phase is blocked
        if action.blocked_phases and phase in action.blocked_phases:
            continue
        # Check if phase is allowed (None = all allowed)
        if action.allowed_phases is None or phase in action.allowed_phases:
            result.append(action)
    return result


def export_tool_schemas() -> list[dict[str, Any]]:
    """Export all action definitions as tool schemas (for LLM integration)."""
    return [action.to_schema() for action in ALL_ACTIONS.values()]
