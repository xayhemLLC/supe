"""Tascer - Task Execution and Validation Framework.

Tascer provides primitives for falsifiable, observable, reproducible,
and auditable task execution built on AB Memory and Tasc.

A Tasc is a state transition: S0 -> Op -> S1
Validation checks whether observed(S1) matches hypothesized(S1).

Core components:
- contracts: Context, ActionSpec, ActionResult, ValidationReport
- primitives: Observation and measurement instruments
- gates: Validation assertions
- actions: Controlled mutation primitives
- proofs: End-to-end reality proof composites
- boosters: Innovative utility primitives

Expansion (v2):
- action_registry: 32 primitive actions with metadata
- ledgers: Dual-ledger model (Moments + Exe)
- checkpoint: Time-travel and rollback
- overlord: Decision loop and intelligent stopping
- benchmarks: Capability validation experiments
- patterns: Intelligence accretion
- audit: Markdown export
"""

# Re-export Tasc from tasc module
from tasc.tasc import Tasc

# New expansion modules
from .action_registry import (
    ActionMetadata,
    ActionRegistry,
    check_legality,
    get_action,
    get_registry,
    is_mutation,
    list_actions,
)

# Agent Session Tracking
from .agent_session import (
    AgentSession,
    SessionStore,
    StepLog,
    complete_session,
    get_session_summary,
    log_step,
    replay_session,
    start_session,
)

# Approval System
from .approval import (
    Approval,
    ApprovalRequest,
    approve,
    get_approval,
    get_pending_approvals,
    is_dangerous_action,
    reject,
    request_approval,
)
from .checkpoint import (
    Checkpoint,
    CheckpointManager,
    requires_checkpoint,
)
from .contracts import (
    ActionResult,
    ActionSpec,
    Context,
    ErrorInfo,
    GateResult,
    GitState,
    TascValidation,
    ValidationReport,
)
from .gates import (
    ExitCodeGate,
    FileExistsGate,
    JsonPathGate,
    PatternGate,
)

# LLM Planner
from .llm_planner import (
    BenchmarkSuite,
    CitationStore,
    GeneratedPlan,
    PlanGenerationRequest,
    PlanMetrics,
    TascCitation,
    calculate_plan_metrics,
    cite_tasc,
    generate_plan,  # Main entry point - uses Claude by default
    generate_plan_prompt,
    parse_generated_plan,
)

# LLM Proof-of-Work
from .llm_proof import (
    LLMTaskProof,
    PlanVerificationReport,
    ProofRequirement,
    ProofType,
    TascPlan,
    TaskStatus,
    create_plan,
    execute_plan,
    load_plan,
    prove_task,
    save_plan,
    save_validation,
    validate_tasc,
    verify_plan_completion,
)
from .primitives import (
    DirectoryDiff,
    FileSnapshot,
    TerminalResult,
    WatchResult,
    capture_context,
    capture_git_state,
    diff_directories,
    run_and_observe,
    snapshot_directory,
    snapshot_file,
    terminal_watch,
)
from .report import write_validation_report
from .runner import TascRunner, run_tasc

__all__ = [
    # Contracts
    "Context",
    "GitState",
    "ActionSpec",
    "ActionResult",
    "ValidationReport",
    "GateResult",
    "ErrorInfo",
    "TascValidation",
    # Primitives
    "capture_context",
    "run_and_observe",
    "terminal_watch",
    "capture_git_state",
    "snapshot_file",
    "snapshot_directory",
    "diff_directories",
    "TerminalResult",
    "WatchResult",
    "FileSnapshot",
    "DirectoryDiff",
    # Gates
    "ExitCodeGate",
    "PatternGate",
    "FileExistsGate",
    "JsonPathGate",
    # Report
    "write_validation_report",
    # Runner
    "TascRunner",
    "run_tasc",
    # Action Registry
    "ActionMetadata",
    "ActionRegistry",
    "get_registry",
    "get_action",
    "list_actions",
    "is_mutation",
    "check_legality",
    # Checkpoint
    "Checkpoint",
    "CheckpointManager",
    "requires_checkpoint",
    # LLM Proof-of-Work
    "TascPlan",
    "Tasc",
    "ProofType",
    "TaskStatus",
    "ProofRequirement",
    "LLMTaskProof",
    "PlanVerificationReport",
    "create_plan",
    "prove_task",
    "validate_tasc",
    "execute_plan",
    "verify_plan_completion",
    "save_plan",
    "load_plan",
    "save_validation",
    # Approval System
    "ApprovalRequest",
    "Approval",
    "request_approval",
    "approve",
    "reject",
    "get_pending_approvals",
    "get_approval",
    "is_dangerous_action",
    # LLM Planner
    "TascCitation",
    "PlanMetrics",
    "BenchmarkSuite",
    "PlanGenerationRequest",
    "GeneratedPlan",
    "generate_plan_prompt",
    "parse_generated_plan",
    "calculate_plan_metrics",
    "cite_tasc",
    "CitationStore",
    "generate_plan",
    # Agent Session
    "StepLog",
    "AgentSession",
    "SessionStore",
    "start_session",
    "log_step",
    "complete_session",
    "replay_session",
    "get_session_summary",
]
