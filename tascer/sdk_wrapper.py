"""Tascer Agent SDK Integration.

Wraps Claude Agent SDK with Tascer validation, providing:
- Pre/post validation gates for all tool calls
- Context capture (git state, environment)
- Proof-of-work generation for audit trails
- Evidence collection and storage

Example:
    from tascer.sdk_wrapper import TascerAgent

    agent = TascerAgent()
    async for msg in agent.query("Fix the bug in auth.py"):
        print(msg)

    # Verify all proofs
    assert agent.verify_proofs()
"""

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from .contracts import Context, GateResult, GitState

# Optional AB Memory integration
try:
    from ab import ABMemory, Moment, Card, Buffer
    AB_AVAILABLE = True
except ImportError:
    AB_AVAILABLE = False


# ---------------------------------------------------------------------------
# Configuration Data Structures
# ---------------------------------------------------------------------------

@dataclass
class ToolValidationConfig:
    """Configuration for validating a specific tool."""

    tool_name: str
    pre_gates: List[str] = field(default_factory=list)
    post_gates: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    evidence_types: List[str] = field(default_factory=list)
    timeout_ms: int = 30000
    require_proof: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "pre_gates": self.pre_gates,
            "post_gates": self.post_gates,
            "required_permissions": self.required_permissions,
            "evidence_types": self.evidence_types,
            "timeout_ms": self.timeout_ms,
            "require_proof": self.require_proof,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolValidationConfig":
        return cls(
            tool_name=data.get("tool_name", ""),
            pre_gates=data.get("pre_gates", []),
            post_gates=data.get("post_gates", []),
            required_permissions=data.get("required_permissions", []),
            evidence_types=data.get("evidence_types", []),
            timeout_ms=data.get("timeout_ms", 30000),
            require_proof=data.get("require_proof", True),
        )


@dataclass
class ToolExecutionRecord:
    """Record of a validated tool execution."""

    tool_use_id: str
    tool_name: str
    timestamp_start: str
    timestamp_end: Optional[str] = None

    # Input/output
    tool_input: Dict[str, Any] = field(default_factory=dict)
    tool_output: Any = None

    # Context
    context: Optional[Context] = None

    # Validation
    pre_gate_results: List[GateResult] = field(default_factory=list)
    post_gate_results: List[GateResult] = field(default_factory=list)

    # Proof
    proof_hash: str = ""
    evidence_paths: List[str] = field(default_factory=list)

    # Status: pending | validated | failed | blocked
    status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_use_id": self.tool_use_id,
            "tool_name": self.tool_name,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "tool_input": self.tool_input,
            "tool_output": self.tool_output,
            "context": self.context.to_dict() if self.context else None,
            "pre_gate_results": [g.to_dict() for g in self.pre_gate_results],
            "post_gate_results": [g.to_dict() for g in self.post_gate_results],
            "proof_hash": self.proof_hash,
            "evidence_paths": self.evidence_paths,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolExecutionRecord":
        context_data = data.get("context")
        return cls(
            tool_use_id=data.get("tool_use_id", ""),
            tool_name=data.get("tool_name", ""),
            timestamp_start=data.get("timestamp_start", ""),
            timestamp_end=data.get("timestamp_end"),
            tool_input=data.get("tool_input", {}),
            tool_output=data.get("tool_output"),
            context=Context.from_dict(context_data) if context_data else None,
            pre_gate_results=[
                GateResult.from_dict(g) for g in data.get("pre_gate_results", [])
            ],
            post_gate_results=[
                GateResult.from_dict(g) for g in data.get("post_gate_results", [])
            ],
            proof_hash=data.get("proof_hash", ""),
            evidence_paths=data.get("evidence_paths", []),
            status=data.get("status", "pending"),
        )


@dataclass
class TascerAgentOptions:
    """Options for Tascer-validated agent execution."""

    # Tool validation configs (tool_name -> config)
    tool_configs: Dict[str, ToolValidationConfig] = field(default_factory=dict)

    # Default gates for all tools
    default_pre_gates: List[str] = field(default_factory=list)
    default_post_gates: List[str] = field(default_factory=list)

    # Context capture
    capture_git_state: bool = True
    capture_env: bool = True
    env_allowlist: List[str] = field(
        default_factory=lambda: ["PATH", "HOME", "USER", "SHELL"]
    )

    # Storage
    store_to_ab: bool = True
    evidence_dir: str = ".tascer/evidence"

    # Proof settings
    generate_proofs: bool = True
    proof_algorithm: str = "sha256"


# Type alias for gate functions
GateFunction = Callable[["ToolExecutionRecord", str], GateResult]


# ---------------------------------------------------------------------------
# TascerAgent - Main Integration Class
# ---------------------------------------------------------------------------

class TascerAgent:
    """Claude Agent with Tascer validation.

    Wraps the Claude Agent SDK query() function, injecting PreToolUse and
    PostToolUse hooks that:
    - Capture execution context (git state, environment)
    - Run validation gates before/after tool execution
    - Generate cryptographic proofs of execution
    - Store audit records

    Example:
        agent = TascerAgent()
        async for msg in agent.query("Fix auth.py"):
            print(msg)
        assert agent.verify_proofs()
    """

    def __init__(
        self,
        tascer_options: Optional[TascerAgentOptions] = None,
        ab_memory: Optional["ABMemory"] = None,
    ):
        """Initialize TascerAgent.

        Args:
            tascer_options: Tascer validation configuration
            ab_memory: Optional ABMemory instance for storing execution records
        """
        self.tascer_options = tascer_options or TascerAgentOptions()
        self._execution_records: List[ToolExecutionRecord] = []
        self._gates: Dict[str, GateFunction] = {}
        self._session_id: Optional[str] = None

        # AB Memory integration
        self._ab_memory = ab_memory
        self._session_moment_id: Optional[int] = None

        # Register built-in gates
        self._register_builtin_gates()

    def _register_builtin_gates(self) -> None:
        """Register built-in validation gates."""
        # Exit code gate
        self._gates["exit_code_zero"] = self._gate_exit_code_zero
        # Always block gate (for testing/read-only agents)
        self._gates["always_block"] = self._gate_always_block
        # Always pass gate
        self._gates["always_pass"] = self._gate_always_pass

    def register_gate(
        self, name: str, func: Optional[GateFunction] = None
    ) -> Callable:
        """Register a custom validation gate.

        Can be used as a decorator:
            @agent.register_gate("my_gate")
            def my_gate(record, phase):
                return GateResult(...)

        Or directly:
            agent.register_gate("my_gate", my_gate_func)

        Args:
            name: Gate name to register
            func: Gate function (optional if used as decorator)

        Returns:
            Decorator function if func is None, else the func
        """
        def decorator(f: GateFunction) -> GateFunction:
            self._gates[name] = f
            return f

        if func is not None:
            self._gates[name] = func
            return func

        return decorator

    async def query(
        self,
        prompt: str,
        allowed_tools: Optional[List[str]] = None,
        resume: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[Any]:
        """Execute agent query with Tascer validation.

        Args:
            prompt: The prompt to send to the agent
            allowed_tools: List of tools the agent can use
            resume: Session ID to resume from
            **kwargs: Additional arguments passed to SDK query()

        Yields:
            Messages from the agent
        """
        try:
            # Import SDK here to allow graceful fallback if not installed
            from claude_agent_sdk import query as sdk_query, ClaudeAgentOptions, HookMatcher
        except ImportError:
            raise ImportError(
                "claude-agent-sdk is required. Install with: pip install claude-agent-sdk"
            )

        # Build hooks
        hooks = {
            "PreToolUse": [
                HookMatcher(matcher=".*", hooks=[self._pre_tool_hook])
            ],
            "PostToolUse": [
                HookMatcher(matcher=".*", hooks=[self._post_tool_hook])
            ],
        }

        # Build options
        sdk_options = ClaudeAgentOptions(
            allowed_tools=allowed_tools,
            hooks=hooks,
            **({"resume": resume} if resume else {}),
        )

        # Execute with SDK
        async for message in sdk_query(prompt=prompt, options=sdk_options, **kwargs):
            # Capture session ID
            if hasattr(message, "subtype") and message.subtype == "init":
                self._session_id = getattr(message, "session_id", None)

            yield message

    async def _pre_tool_hook(
        self,
        input_data: Dict[str, Any],
        tool_use_id: str,
        context: Any,
    ) -> Dict[str, Any]:
        """Pre-execution validation hook.

        Called before each tool execution to:
        - Create execution record
        - Capture context (git state, env)
        - Run pre-validation gates

        Args:
            input_data: Tool input from SDK
            tool_use_id: Unique ID for this tool use
            context: SDK context object

        Returns:
            Empty dict to proceed, or {"block": True, "message": "..."} to block
        """
        tool_name = input_data.get("tool_name", "unknown")
        tool_input = input_data.get("tool_input", {})

        # Create execution record
        record = ToolExecutionRecord(
            tool_use_id=tool_use_id,
            tool_name=tool_name,
            timestamp_start=datetime.now(timezone.utc).isoformat(),
            tool_input=tool_input,
        )

        # Capture context
        if self.tascer_options.capture_git_state or self.tascer_options.capture_env:
            record.context = await self._capture_context()

        # Get tool config
        config = self._get_tool_config(tool_name)

        # Run pre-gates
        gates_to_run = config.pre_gates + self.tascer_options.default_pre_gates
        for gate_name in gates_to_run:
            result = await self._run_gate(gate_name, record, "pre")
            record.pre_gate_results.append(result)

            if not result.passed:
                record.status = "blocked"
                self._execution_records.append(record)
                return {"block": True, "message": result.message}

        # Store record for post-hook
        self._execution_records.append(record)
        return {}

    async def _post_tool_hook(
        self,
        input_data: Dict[str, Any],
        tool_use_id: str,
        context: Any,
    ) -> Dict[str, Any]:
        """Post-execution validation and proof generation.

        Called after each tool execution to:
        - Capture tool output
        - Run post-validation gates
        - Generate proof hash

        Args:
            input_data: Tool result from SDK
            tool_use_id: Unique ID for this tool use
            context: SDK context object

        Returns:
            Empty dict (post-hooks don't block)
        """
        # Find the record
        record = self._find_record(tool_use_id)
        if not record:
            return {}

        # Update record
        record.timestamp_end = datetime.now(timezone.utc).isoformat()
        record.tool_output = input_data.get("tool_result")

        # Get tool config
        config = self._get_tool_config(record.tool_name)

        # Run post-gates
        gates_to_run = config.post_gates + self.tascer_options.default_post_gates
        for gate_name in gates_to_run:
            result = await self._run_gate(gate_name, record, "post")
            record.post_gate_results.append(result)

        # Generate proof
        if self.tascer_options.generate_proofs:
            record.proof_hash = self._generate_proof(record)

        # Determine status
        all_pre_passed = all(g.passed for g in record.pre_gate_results)
        all_post_passed = all(g.passed for g in record.post_gate_results)

        if all_pre_passed and all_post_passed:
            record.status = "validated"
        else:
            record.status = "failed"

        # Store to AB Memory
        if self.tascer_options.store_to_ab:
            self._store_to_ab(record)

        return {}

    def _get_tool_config(self, tool_name: str) -> ToolValidationConfig:
        """Get validation config for a tool.

        Returns tool-specific config if defined, otherwise a default config.

        Args:
            tool_name: Name of the tool

        Returns:
            ToolValidationConfig for the tool
        """
        if tool_name in self.tascer_options.tool_configs:
            return self.tascer_options.tool_configs[tool_name]

        # Return default config
        return ToolValidationConfig(tool_name=tool_name)

    def _find_record(self, tool_use_id: str) -> Optional[ToolExecutionRecord]:
        """Find execution record by tool_use_id.

        Args:
            tool_use_id: The tool use ID to find

        Returns:
            The record if found, None otherwise
        """
        for record in reversed(self._execution_records):
            if record.tool_use_id == tool_use_id:
                return record
        return None

    async def _capture_context(self) -> Context:
        """Capture execution context.

        Returns:
            Context with git state and environment info
        """
        import subprocess

        ctx = Context(
            run_id=str(uuid.uuid4())[:8],
            tasc_id=str(uuid.uuid4())[:8],
            cwd=os.getcwd(),
            os_name=os.name,
        )

        # Capture git state
        if self.tascer_options.capture_git_state:
            try:
                branch = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                ).stdout.strip()

                commit = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                ).stdout.strip()[:12]

                status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                ).stdout.strip()

                ctx.git_state = GitState(
                    branch=branch,
                    commit=commit,
                    dirty=bool(status),
                    diff_stat="",
                    status=status[:200] if status else "",
                )
            except Exception:
                pass  # Not a git repo or git not available

        # Capture environment
        if self.tascer_options.capture_env:
            ctx.env_allowlist = {
                k: os.environ.get(k, "")
                for k in self.tascer_options.env_allowlist
                if k in os.environ
            }

        return ctx

    async def _run_gate(
        self,
        gate_name: str,
        record: ToolExecutionRecord,
        phase: str,
    ) -> GateResult:
        """Run a validation gate.

        Args:
            gate_name: Name of the gate to run
            record: The execution record
            phase: "pre" or "post"

        Returns:
            GateResult from the gate
        """
        if gate_name not in self._gates:
            return GateResult(
                gate_name=gate_name,
                passed=True,
                message=f"Gate '{gate_name}' not found, skipping",
            )

        gate_func = self._gates[gate_name]

        try:
            result = gate_func(record, phase)
            # Handle async gates
            if hasattr(result, "__await__"):
                result = await result
            return result
        except Exception as e:
            return GateResult(
                gate_name=gate_name,
                passed=False,
                message=f"Gate error: {str(e)}",
            )

    def _generate_proof(self, record: ToolExecutionRecord) -> str:
        """Generate proof hash for an execution record.

        The proof is a SHA256 hash of the record's key fields,
        allowing verification that the record hasn't been tampered with.

        Args:
            record: The execution record

        Returns:
            Hex string of the proof hash (first 16 chars)
        """
        # Build proof content from immutable fields
        proof_data = {
            "tool_use_id": record.tool_use_id,
            "tool_name": record.tool_name,
            "timestamp_start": record.timestamp_start,
            "timestamp_end": record.timestamp_end,
            "tool_input": record.tool_input,
            "tool_output": str(record.tool_output)[:1000] if record.tool_output else None,
            "pre_gates": [g.to_dict() for g in record.pre_gate_results],
            "post_gates": [g.to_dict() for g in record.post_gate_results],
        }

        # Include context if available
        if record.context:
            proof_data["context"] = {
                "cwd": record.context.cwd,
                "git_commit": record.context.git_state.commit if record.context.git_state else None,
            }

        content = json.dumps(proof_data, sort_keys=True, default=str)
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()[:16]

    def _verify_proof(self, record: ToolExecutionRecord) -> bool:
        """Verify a single record's proof hash.

        Args:
            record: The record to verify

        Returns:
            True if proof is valid, False if tampered
        """
        if not record.proof_hash:
            return True  # No proof to verify

        expected = self._generate_proof(record)
        return expected == record.proof_hash

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def get_validation_report(self) -> List[ToolExecutionRecord]:
        """Get all execution records from this session.

        Returns:
            List of ToolExecutionRecord objects
        """
        return self._execution_records.copy()

    def verify_proofs(self) -> bool:
        """Verify all proof hashes are valid.

        Returns:
            True if all proofs verify, False if any are invalid
        """
        return all(self._verify_proof(r) for r in self._execution_records)

    def get_session_id(self) -> Optional[str]:
        """Get the current session ID.

        Returns:
            Session ID if available, None otherwise
        """
        return self._session_id

    def export_report(self, path: str) -> None:
        """Export validation report to JSON file.

        Args:
            path: Path to write the report
        """
        report = {
            "session_id": self._session_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "proofs_valid": self.verify_proofs(),
            "records": [r.to_dict() for r in self._execution_records],
        }

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(report, f, indent=2)

    # ---------------------------------------------------------------------------
    # AB Memory Integration
    # ---------------------------------------------------------------------------

    def _store_to_ab(self, record: ToolExecutionRecord) -> Optional[int]:
        """Store execution record to AB Memory as a Card.

        Creates a Card on the 'execution' track with buffers for:
        - input: Tool input as JSON
        - output: Tool output as JSON
        - context: Execution context
        - gates: Gate results
        - proof: Proof hash and verification data

        Args:
            record: The execution record to store

        Returns:
            Card ID if stored, None otherwise
        """
        if not self._ab_memory or not AB_AVAILABLE:
            return None

        try:
            # Create or get session moment
            if self._session_moment_id is None:
                moment = self._ab_memory.create_moment(
                    master_input=f"TascerAgent session: {self._session_id or 'unknown'}",
                )
                self._session_moment_id = moment.id

            # Create buffers for the card
            buffers = [
                Buffer(
                    name="input",
                    headers={"tool": record.tool_name, "type": "tool_input"},
                    payload=json.dumps(record.tool_input, default=str).encode(),
                ),
                Buffer(
                    name="output",
                    headers={"type": "tool_output"},
                    payload=json.dumps(record.tool_output, default=str).encode()
                    if record.tool_output else b"",
                ),
                Buffer(
                    name="proof",
                    headers={
                        "algorithm": self.tascer_options.proof_algorithm,
                        "status": record.status,
                    },
                    payload=record.proof_hash.encode(),
                ),
            ]

            # Add context buffer if available
            if record.context:
                buffers.append(Buffer(
                    name="context",
                    headers={"type": "execution_context"},
                    payload=json.dumps(record.context.to_dict(), default=str).encode(),
                ))

            # Add gate results buffer
            gate_data = {
                "pre_gates": [g.to_dict() for g in record.pre_gate_results],
                "post_gates": [g.to_dict() for g in record.post_gate_results],
            }
            buffers.append(Buffer(
                name="gates",
                headers={"type": "validation_gates"},
                payload=json.dumps(gate_data).encode(),
            ))

            # Store the card using ABMemory's API
            card = self._ab_memory.store_card(
                label=f"tascer:{record.tool_name}:{record.tool_use_id[:8]}",
                buffers=buffers,
                owner_self="tascer_agent",
                moment_id=self._session_moment_id,
                master_input=json.dumps(record.tool_input, default=str)[:500],
                master_output=str(record.tool_output)[:500] if record.tool_output else None,
                track="execution",
            )

            return card.id

        except Exception as e:
            # Don't fail validation if storage fails
            print(f"Warning: Failed to store to AB Memory: {e}")
            return None

    # ---------------------------------------------------------------------------
    # Built-in Gates
    # ---------------------------------------------------------------------------

    @staticmethod
    def _gate_exit_code_zero(record: ToolExecutionRecord, phase: str) -> GateResult:
        """Gate that checks Bash exit code is zero."""
        if phase != "post":
            return GateResult(
                gate_name="exit_code_zero",
                passed=True,
                message="Pre-check skipped",
            )

        # Check if this is a Bash tool result
        output = record.tool_output
        if isinstance(output, dict) and "exit_code" in output:
            exit_code = output["exit_code"]
            passed = exit_code == 0
            return GateResult(
                gate_name="exit_code_zero",
                passed=passed,
                message=f"Exit code: {exit_code}" if passed else f"Non-zero exit: {exit_code}",
            )

        return GateResult(
            gate_name="exit_code_zero",
            passed=True,
            message="No exit code in output",
        )

    @staticmethod
    def _gate_always_block(record: ToolExecutionRecord, phase: str) -> GateResult:
        """Gate that always blocks (for read-only agents)."""
        return GateResult(
            gate_name="always_block",
            passed=False,
            message=f"Tool '{record.tool_name}' is blocked by policy",
        )

    @staticmethod
    def _gate_always_pass(record: ToolExecutionRecord, phase: str) -> GateResult:
        """Gate that always passes (for testing)."""
        return GateResult(
            gate_name="always_pass",
            passed=True,
            message="Gate passed",
        )
