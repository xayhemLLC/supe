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

from .contracts import (
    Context,
    GitState,
    ActionSpec,
    ActionResult,
    ValidationReport,
    GateResult,
    ErrorInfo,
    TascValidation,
)
from .primitives import (
    capture_context,
    run_and_observe,
    terminal_watch,
    capture_git_state,
    snapshot_file,
    snapshot_directory,
    diff_directories,
    TerminalResult,
    WatchResult,
    FileSnapshot,
    DirectoryDiff,
)
from .gates import (
    ExitCodeGate,
    PatternGate,
    FileExistsGate,
    JsonPathGate,
)
from .report import write_validation_report
from .runner import TascRunner, run_tasc

# New expansion modules
from .action_registry import (
    ActionMetadata,
    ActionRegistry,
    get_registry,
    get_action,
    list_actions,
    is_mutation,
    check_legality,
)
from .checkpoint import (
    Checkpoint,
    CheckpointManager,
    requires_checkpoint,
)

# LLM Proof-of-Work
from .llm_proof import (
    TascPlan,
    ProofType,
    TaskStatus,
    ProofRequirement,
    LLMTaskProof,
    PlanVerificationReport,
    create_plan,
    prove_task,
    validate_tasc,
    execute_plan,
    verify_plan_completion,
    save_plan,
    load_plan,
    save_validation,
)

# Approval System
from .approval import (
    ApprovalRequest,
    Approval,
    request_approval,
    approve,
    reject,
    get_pending_approvals,
    get_approval,
    is_dangerous_action,
)

# LLM Planner
from .llm_planner import (
    TascCitation,
    PlanMetrics,
    BenchmarkSuite,
    PlanGenerationRequest,
    GeneratedPlan,
    generate_plan_prompt,
    parse_generated_plan,
    calculate_plan_metrics,
    cite_tasc,
    CitationStore,
    generate_plan,  # Main entry point - uses Claude by default
)

# Agent Session Tracking
from .agent_session import (
    StepLog,
    AgentSession,
    SessionStore,
    start_session,
    log_step,
    complete_session,
    replay_session,
    get_session_summary,
)

# Re-export Tasc from tasc module
from tasc.tasc import Tasc

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
