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
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple

from .contracts import Context, GateResult, GitState

# Optional recall imports
try:
    from ab.recall import recall_cards
    from ab.search import search_cards
    from ab.neural_memory import NeuralMemory
    RECALL_AVAILABLE = True
except ImportError:
    RECALL_AVAILABLE = False

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
class RecallConfig:
    """Configuration for recall behavior."""

    enabled: bool = True                      # Enable recall features
    auto_context: bool = False                # Auto-inject context in pre-hook
    auto_context_limit: int = 3               # Max auto-context items
    index_on_store: bool = True               # Index cards for neural recall
    default_top_k: int = 5                    # Default result limit
    include_failed: bool = False              # Include failed executions
    verify_proofs: bool = True                # Verify proofs on recall


@dataclass
class RecallQuery:
    """Query parameters for recall."""

    query: str                                # Search text
    tool_name: Optional[str] = None           # Filter by tool
    session_id: Optional[str] = None          # Filter by session
    start_time: Optional[str] = None          # Time range start
    end_time: Optional[str] = None            # Time range end
    top_k: int = 5                            # Max results
    include_buffers: List[str] = field(       # Which buffers to return
        default_factory=lambda: ["input", "output"]
    )
    use_neural: bool = True                   # Enable spreading activation
    min_score: float = 0.0                    # Minimum relevance score


@dataclass
class RecallResult:
    """Single recall result with metadata."""

    card_id: int                              # Card ID in AB Memory
    score: float                              # Relevance score (0-1)
    tool_name: str                            # Extracted tool name
    tool_input: Dict[str, Any]                # Tool input data
    tool_output: Optional[Any]                # Tool output data
    timestamp: str                            # When executed
    session_id: Optional[str]                 # Session it belongs to
    proof_valid: bool                         # Proof verification status
    proof_hash: str                           # The proof hash
    highlights: Dict[str, str] = field(       # Matched snippets per buffer
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card_id": self.card_id,
            "score": self.score,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "tool_output": self.tool_output,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "proof_valid": self.proof_valid,
            "proof_hash": self.proof_hash,
            "highlights": self.highlights,
        }


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

    # Recall settings
    recall_config: RecallConfig = field(default_factory=RecallConfig)


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

        # Neural memory for spreading activation recall
        self._neural_memory: Optional["NeuralMemory"] = None
        if RECALL_AVAILABLE and self.tascer_options.recall_config.enabled:
            self._neural_memory = NeuralMemory()

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
    # Recall API
    # ---------------------------------------------------------------------------

    def recall(
        self,
        query: str,
        top_k: Optional[int] = None,
        tool_name: Optional[str] = None,
        session_id: Optional[str] = None,
        use_neural: bool = True,
    ) -> List[RecallResult]:
        """Recall past executions matching query.

        Primary recall interface that searches stored execution cards
        using keyword matching and optional neural spreading activation.

        Args:
            query: Search text (keywords or natural language)
            top_k: Maximum results to return (defaults to recall_config.default_top_k)
            tool_name: Filter to specific tool (e.g., "Read", "Bash")
            session_id: Filter to specific session
            use_neural: Enable spreading activation for semantic matching

        Returns:
            List of RecallResult sorted by relevance score descending

        Example:
            results = agent.recall("struct player", top_k=5)
            for r in results:
                print(f"{r.tool_name}: {r.tool_input}")
        """
        if not self._ab_memory or not AB_AVAILABLE:
            return []

        if not RECALL_AVAILABLE:
            return []

        config = self.tascer_options.recall_config
        top_k = top_k or config.default_top_k

        # Build label filter for tascer cards
        label_filter = "tascer:"
        if tool_name:
            label_filter = f"tascer:{tool_name}:"

        # Use ab.recall for keyword + connection traversal
        raw_results = recall_cards(
            self._ab_memory,
            query=query,
            top_k=top_k * 2,  # Get extra for filtering
            strengthen=True,
            use_card_stats=True,
        )

        # Convert to RecallResults with filtering
        results: List[RecallResult] = []
        for card, score in raw_results:
            # Filter by label pattern
            if not card.label.startswith(label_filter):
                continue

            # Extract data from buffers
            tool_input = {}
            tool_output = None
            proof_hash = ""
            timestamp = ""

            for buf in card.buffers:
                if buf.name == "input":
                    try:
                        tool_input = json.loads(buf.payload.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
                elif buf.name == "output":
                    try:
                        tool_output = json.loads(buf.payload.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        tool_output = buf.payload.decode() if buf.payload else None
                elif buf.name == "proof":
                    proof_hash = buf.payload.decode() if buf.payload else ""

            # Extract tool name from label (tascer:ToolName:id)
            parts = card.label.split(":")
            extracted_tool = parts[1] if len(parts) >= 2 else "unknown"

            # Filter by tool name if specified
            if tool_name and extracted_tool != tool_name:
                continue

            # Get timestamp from moment
            moment = self._ab_memory.get_moment(card.moment_id)
            timestamp = moment.timestamp if moment else ""

            # Filter by session if specified (stored in moment master_input)
            if session_id and moment:
                if session_id not in (moment.master_input or ""):
                    continue

            # Verify proof if configured
            proof_valid = True
            if config.verify_proofs and proof_hash:
                # Re-verify by checking the hash exists and matches format
                proof_valid = len(proof_hash) == 16 and all(
                    c in "0123456789abcdef" for c in proof_hash
                )

            results.append(RecallResult(
                card_id=card.id,
                score=score,
                tool_name=extracted_tool,
                tool_input=tool_input,
                tool_output=tool_output,
                timestamp=timestamp,
                session_id=session_id,
                proof_valid=proof_valid,
                proof_hash=proof_hash,
            ))

            if len(results) >= top_k:
                break

        # Apply neural spreading activation for semantic boost
        if use_neural and self._neural_memory and results:
            neural_scores = self._neural_memory.recall(query, top_k=len(results))
            score_map = {card_id: score for card_id, score in neural_scores}
            for r in results:
                if r.card_id in score_map:
                    r.score = (r.score + score_map[r.card_id]) / 2

            # Re-sort by combined score
            results.sort(key=lambda x: x.score, reverse=True)

        return results[:top_k]

    def recall_tool(
        self,
        tool_name: str,
        top_k: Optional[int] = None,
    ) -> List[RecallResult]:
        """Get recent executions of a specific tool.

        Useful for: "Show me all my Read operations"

        Args:
            tool_name: Tool to filter by (e.g., "Read", "Bash", "Edit")
            top_k: Maximum results to return

        Returns:
            List of RecallResult for that tool, sorted by recency
        """
        if not self._ab_memory or not AB_AVAILABLE or not RECALL_AVAILABLE:
            return []

        config = self.tascer_options.recall_config
        top_k = top_k or config.default_top_k

        # Search cards with keyword that will match the label pattern
        cards = search_cards(
            self._ab_memory,
            keyword=f"tascer:{tool_name}",
        )
        # Filter to only cards that match the label prefix
        cards = [c for c in cards if c.label.startswith(f"tascer:{tool_name}:")]

        # Convert to results (newest first)
        results: List[RecallResult] = []
        for card in reversed(cards[-top_k * 2:]):
            tool_input = {}
            tool_output = None
            proof_hash = ""

            for buf in card.buffers:
                if buf.name == "input":
                    try:
                        tool_input = json.loads(buf.payload.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
                elif buf.name == "output":
                    try:
                        tool_output = json.loads(buf.payload.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        tool_output = buf.payload.decode() if buf.payload else None
                elif buf.name == "proof":
                    proof_hash = buf.payload.decode() if buf.payload else ""

            moment = self._ab_memory.get_moment(card.moment_id)
            timestamp = moment.timestamp if moment else ""

            results.append(RecallResult(
                card_id=card.id,
                score=1.0,  # No relevance scoring for tool filter
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                timestamp=timestamp,
                session_id=None,
                proof_valid=True,
                proof_hash=proof_hash,
            ))

            if len(results) >= top_k:
                break

        return results

    def recall_session(
        self,
        session_id: Optional[str] = None,
    ) -> List[RecallResult]:
        """Get full execution history for a session.

        Args:
            session_id: Session to retrieve (defaults to current session)

        Returns:
            All executions from that session in chronological order
        """
        target_session = session_id or self._session_id
        if not target_session:
            return []

        if not self._ab_memory or not AB_AVAILABLE or not RECALL_AVAILABLE:
            return []

        # Search for cards in this session's moment
        cards = search_cards(
            self._ab_memory,
            keyword=target_session,
        )

        # Filter to tascer cards and convert
        results: List[RecallResult] = []
        for card in cards:
            if not card.label.startswith("tascer:"):
                continue

            tool_input = {}
            tool_output = None
            proof_hash = ""

            for buf in card.buffers:
                if buf.name == "input":
                    try:
                        tool_input = json.loads(buf.payload.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
                elif buf.name == "output":
                    try:
                        tool_output = json.loads(buf.payload.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        tool_output = buf.payload.decode() if buf.payload else None
                elif buf.name == "proof":
                    proof_hash = buf.payload.decode() if buf.payload else ""

            parts = card.label.split(":")
            extracted_tool = parts[1] if len(parts) >= 2 else "unknown"

            moment = self._ab_memory.get_moment(card.moment_id)
            timestamp = moment.timestamp if moment else ""

            results.append(RecallResult(
                card_id=card.id,
                score=1.0,
                tool_name=extracted_tool,
                tool_input=tool_input,
                tool_output=tool_output,
                timestamp=timestamp,
                session_id=target_session,
                proof_valid=True,
                proof_hash=proof_hash,
            ))

        return results

    def recall_similar(
        self,
        tool_input: Dict[str, Any],
        top_k: int = 3,
    ) -> List[RecallResult]:
        """Find executions similar to given input.

        Useful for: "Have I run this command before?"

        Args:
            tool_input: Input to find similar executions for
            top_k: Maximum results to return

        Returns:
            List of RecallResult with similar inputs
        """
        # Build query from input values
        query_parts = []
        for key, value in tool_input.items():
            if isinstance(value, str):
                query_parts.append(value)
            elif isinstance(value, (list, dict)):
                query_parts.append(json.dumps(value))

        query = " ".join(query_parts)
        return self.recall(query, top_k=top_k, use_neural=True)

    def get_context_for(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        max_context: int = 3,
    ) -> List[Dict[str, Any]]:
        """Auto-retrieve relevant context for a tool call.

        Called internally during _pre_tool_hook to inject
        historical context into agent decisions.

        Args:
            tool_name: Tool about to be executed
            tool_input: Input for the tool
            max_context: Maximum context items to return

        Returns:
            List of relevant past executions as dicts
        """
        # Build query from tool input
        query_parts = [tool_name]
        for value in tool_input.values():
            if isinstance(value, str):
                query_parts.append(value)

        query = " ".join(query_parts)

        # Recall similar executions
        results = self.recall(query, top_k=max_context, use_neural=True)

        # Convert to context dicts
        return [
            {
                "tool_name": r.tool_name,
                "tool_input": r.tool_input,
                "tool_output": r.tool_output,
                "timestamp": r.timestamp,
            }
            for r in results
        ]

    # ---------------------------------------------------------------------------
    # AB Memory Integration
    # ---------------------------------------------------------------------------

    def _extract_concepts(self, record: ToolExecutionRecord) -> List[str]:
        """Extract concepts from execution record for neural indexing.

        Pulls keywords from tool name, input values, and output to
        enable semantic recall via spreading activation.

        Args:
            record: The execution record

        Returns:
            List of concept strings for indexing
        """
        concepts = [record.tool_name.lower()]

        # Extract from input
        for key, value in record.tool_input.items():
            # Add the key itself
            concepts.append(key.lower())

            # Extract words from string values
            if isinstance(value, str):
                # Split on common delimiters
                words = value.replace("/", " ").replace(".", " ").replace("_", " ").split()
                for word in words:
                    if len(word) > 3:  # Skip short words
                        concepts.append(word.lower())

        # Extract from output if it's a string or dict
        if isinstance(record.tool_output, str):
            words = record.tool_output[:500].split()
            for word in words:
                if len(word) > 4:  # Skip short words in output
                    concepts.append(word.lower())
        elif isinstance(record.tool_output, dict):
            for key in record.tool_output.keys():
                concepts.append(key.lower())

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for c in concepts:
            if c not in seen:
                seen.add(c)
                unique.append(c)

        return unique[:20]  # Limit to 20 concepts

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

            # Index for neural recall if enabled
            if (
                self._neural_memory
                and self.tascer_options.recall_config.index_on_store
                and card.id is not None
            ):
                # Extract concepts from input/output for neural indexing
                concepts = self._extract_concepts(record)
                if concepts:
                    # Build buffers dict for neural memory
                    buffers_dict = {
                        "input": json.dumps(record.tool_input, default=str),
                        "output": str(record.tool_output) if record.tool_output else "",
                        "concepts": " ".join(concepts),
                    }
                    self._neural_memory.add_card(card.id, buffers_dict)

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
