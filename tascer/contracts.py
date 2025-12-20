"""Core contract data structures for Tascer.

These dataclasses define the canonical schemas for:
- Context: Execution environment snapshot
- ActionSpec: Action specification
- ActionResult: Action execution result
- ValidationReport: Full validation report
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import json


@dataclass
class GitState:
    """Git repository state snapshot."""
    
    branch: str
    commit: str
    dirty: bool
    diff_stat: str
    status: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch": self.branch,
            "commit": self.commit,
            "dirty": self.dirty,
            "diff_stat": self.diff_stat,
            "status": self.status,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GitState":
        return cls(
            branch=data.get("branch", ""),
            commit=data.get("commit", ""),
            dirty=data.get("dirty", False),
            diff_stat=data.get("diff_stat", ""),
            status=data.get("status", ""),
        )


@dataclass
class Context:
    """Snapshot describing the world in which a tasc runs.
    
    Required fields capture enough state to reproduce and audit the tasc.
    Artifact stored at: context/<run_id>/<tasc_id>.json
    """
    
    run_id: str
    tasc_id: str
    timestamp_start: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    timestamp_end: Optional[str] = None
    
    # Environment
    repo_root: str = ""
    cwd: str = ""
    os_name: str = ""
    arch: str = ""
    
    # Toolchain versions
    toolchain_versions: Dict[str, str] = field(default_factory=dict)
    
    # Git state
    git_state: Optional[GitState] = None
    
    # Environment variables (only allowlisted, never secrets)
    env_allowlist: Dict[str, str] = field(default_factory=dict)
    
    # Network
    network_mode: str = "online"  # online | offline
    hostnames_ports: List[str] = field(default_factory=list)
    
    # Permissions granted to action
    permissions_granted: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "tasc_id": self.tasc_id,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "repo_root": self.repo_root,
            "cwd": self.cwd,
            "os_name": self.os_name,
            "arch": self.arch,
            "toolchain_versions": self.toolchain_versions,
            "git_state": self.git_state.to_dict() if self.git_state else None,
            "env_allowlist": self.env_allowlist,
            "network_mode": self.network_mode,
            "hostnames_ports": self.hostnames_ports,
            "permissions_granted": self.permissions_granted,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Context":
        git_data = data.get("git_state")
        return cls(
            run_id=data.get("run_id", ""),
            tasc_id=data.get("tasc_id", ""),
            timestamp_start=data.get("timestamp_start", ""),
            timestamp_end=data.get("timestamp_end"),
            repo_root=data.get("repo_root", ""),
            cwd=data.get("cwd", ""),
            os_name=data.get("os_name", ""),
            arch=data.get("arch", ""),
            toolchain_versions=data.get("toolchain_versions", {}),
            git_state=GitState.from_dict(git_data) if git_data else None,
            env_allowlist=data.get("env_allowlist", {}),
            network_mode=data.get("network_mode", "online"),
            hostnames_ports=data.get("hostnames_ports", []),
            permissions_granted=data.get("permissions_granted", []),
        )
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def finalize(self) -> None:
        """Set the end timestamp."""
        self.timestamp_end = datetime.utcnow().isoformat()


@dataclass
class ErrorInfo:
    """Structured error information."""
    
    error_type: str
    message: str
    traceback: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type,
            "message": self.message,
            "traceback": self.traceback,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorInfo":
        return cls(
            error_type=data.get("error_type", ""),
            message=data.get("message", ""),
            traceback=data.get("traceback"),
        )


@dataclass
class ActionSpec:
    """Specification for an executable action.
    
    Defines inputs, permissions, operation type, and expected evidence.
    """
    
    id: str
    name: str
    version: str = "1.0"
    
    # Input schema (JSON Schema style)
    inputs_schema: Dict[str, Any] = field(default_factory=dict)
    
    # Required permissions
    permissions_required: List[str] = field(default_factory=list)
    # Valid permissions: terminal, network, fs_read, fs_write, secrets, browser
    
    # Operation specification
    op_kind: str = "command"  # script | command | endpoint | function | browser_task
    op_ref: str = ""  # path/command/url/function reference
    
    # Response contract
    response_contract: Dict[str, str] = field(default_factory=dict)
    # Keys: success, fail, timeout, partial with semantic descriptions
    
    # Expected evidence types
    evidence_expected: List[str] = field(default_factory=list)
    # Valid types: stdout, stderr, exit_code, diff, screenshot, file, http_response
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "inputs_schema": self.inputs_schema,
            "permissions_required": self.permissions_required,
            "op_kind": self.op_kind,
            "op_ref": self.op_ref,
            "response_contract": self.response_contract,
            "evidence_expected": self.evidence_expected,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionSpec":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            version=data.get("version", "1.0"),
            inputs_schema=data.get("inputs_schema", {}),
            permissions_required=data.get("permissions_required", []),
            op_kind=data.get("op_kind", "command"),
            op_ref=data.get("op_ref", ""),
            response_contract=data.get("response_contract", {}),
            evidence_expected=data.get("evidence_expected", []),
        )


@dataclass
class ActionResult:
    """Result of executing an action.
    
    Captures status, outputs, parsed results, and evidence paths.
    """
    
    status: str  # success | fail | timeout | partial
    
    # Operation result (exit code, HTTP status, return value)
    op_result: Union[int, str, Dict[str, Any]] = 0
    
    # Parsed/extracted results (jsonpath, regex extractions)
    parsed: Dict[str, Any] = field(default_factory=dict)
    
    # Paths to evidence artifacts
    evidence_paths: List[str] = field(default_factory=list)
    
    # Error info (if failed)
    error: Optional[ErrorInfo] = None
    
    # Metrics
    metrics: Dict[str, float] = field(default_factory=dict)
    # Common: duration_ms, bytes_read, bytes_written
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "op_result": self.op_result,
            "parsed": self.parsed,
            "evidence_paths": self.evidence_paths,
            "error": self.error.to_dict() if self.error else None,
            "metrics": self.metrics,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionResult":
        error_data = data.get("error")
        return cls(
            status=data.get("status", "fail"),
            op_result=data.get("op_result", 0),
            parsed=data.get("parsed", {}),
            evidence_paths=data.get("evidence_paths", []),
            error=ErrorInfo.from_dict(error_data) if error_data else None,
            metrics=data.get("metrics", {}),
        )


@dataclass
class GateResult:
    """Result of a validation gate check."""
    
    gate_name: str
    passed: bool
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "passed": self.passed,
            "message": self.message,
            "evidence": self.evidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GateResult":
        return cls(
            gate_name=data.get("gate_name", ""),
            passed=data.get("passed", False),
            message=data.get("message", ""),
            evidence=data.get("evidence", {}),
        )


@dataclass
class TascValidation:
    """Validation result for a single Tasc step.
    
    Ties a Tasc ID to its validation gates, proof hash, and timing.
    This is used by TascPlan to track validation state for each Tasc.
    """
    
    tasc_id: str
    validated: bool
    proof_hash: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    duration_ms: float = 0
    gate_results: List[GateResult] = field(default_factory=list)
    evidence_paths: List[str] = field(default_factory=list)
    command_executed: str = ""
    exit_code: int = 0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tasc_id": self.tasc_id,
            "validated": self.validated,
            "proof_hash": self.proof_hash,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "gate_results": [g.to_dict() for g in self.gate_results],
            "evidence_paths": self.evidence_paths,
            "command_executed": self.command_executed,
            "exit_code": self.exit_code,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TascValidation":
        return cls(
            tasc_id=data.get("tasc_id", ""),
            validated=data.get("validated", False),
            proof_hash=data.get("proof_hash", ""),
            timestamp=data.get("timestamp", ""),
            duration_ms=data.get("duration_ms", 0),
            gate_results=[GateResult.from_dict(g) for g in data.get("gate_results", [])],
            evidence_paths=data.get("evidence_paths", []),
            command_executed=data.get("command_executed", ""),
            exit_code=data.get("exit_code", 0),
            error_message=data.get("error_message"),
        )
    
    def verify(self) -> bool:
        """Verify that the proof hash is consistent with the data."""
        import hashlib
        data = self.to_dict()
        data.pop("proof_hash", None)
        content = json.dumps(data, sort_keys=True, default=str)
        computed = hashlib.sha256(content.encode()).hexdigest()[:16]
        return computed == self.proof_hash
    
    @property
    def all_gates_passed(self) -> bool:
        """Check if all gates passed."""
        return all(g.passed for g in self.gate_results) if self.gate_results else self.validated


@dataclass
class ValidationReport:
    """Full validation report for a tasc run.
    
    Aggregates context, action result, and gate results into
    a complete audit trail.
    """
    
    run_id: str
    tasc_id: str
    
    # Captured context
    context: Context
    
    # Action executed
    action_spec: ActionSpec
    action_result: ActionResult
    
    # Gate results
    gates_passed: List[GateResult] = field(default_factory=list)
    gates_failed: List[GateResult] = field(default_factory=list)
    
    # Overall status
    overall_status: str = "pending"  # pass | fail | partial
    
    # Evidence index (name -> artifact path)
    evidence_index: Dict[str, str] = field(default_factory=dict)
    
    # Human-readable summary
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "tasc_id": self.tasc_id,
            "context": self.context.to_dict(),
            "action_spec": self.action_spec.to_dict(),
            "action_result": self.action_result.to_dict(),
            "gates_passed": [g.to_dict() for g in self.gates_passed],
            "gates_failed": [g.to_dict() for g in self.gates_failed],
            "overall_status": self.overall_status,
            "evidence_index": self.evidence_index,
            "summary": self.summary,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationReport":
        return cls(
            run_id=data.get("run_id", ""),
            tasc_id=data.get("tasc_id", ""),
            context=Context.from_dict(data.get("context", {})),
            action_spec=ActionSpec.from_dict(data.get("action_spec", {})),
            action_result=ActionResult.from_dict(data.get("action_result", {})),
            gates_passed=[GateResult.from_dict(g) for g in data.get("gates_passed", [])],
            gates_failed=[GateResult.from_dict(g) for g in data.get("gates_failed", [])],
            overall_status=data.get("overall_status", "pending"),
            evidence_index=data.get("evidence_index", {}),
            summary=data.get("summary", ""),
        )
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def compute_overall_status(self) -> None:
        """Compute overall status from gate results."""
        if self.gates_failed:
            if self.gates_passed:
                self.overall_status = "partial"
            else:
                self.overall_status = "fail"
        elif self.gates_passed:
            self.overall_status = "pass"
        else:
            self.overall_status = "pending"
    
    def generate_summary(self) -> None:
        """Generate a human-readable summary."""
        lines = [
            f"Run: {self.run_id} | Tasc: {self.tasc_id}",
            f"Status: {self.overall_status.upper()}",
            f"Gates passed: {len(self.gates_passed)}, failed: {len(self.gates_failed)}",
        ]
        if self.gates_failed:
            lines.append("Failed gates:")
            for g in self.gates_failed:
                lines.append(f"  - {g.gate_name}: {g.message}")
        self.summary = "\n".join(lines)
