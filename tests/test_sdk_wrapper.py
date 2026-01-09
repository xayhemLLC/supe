"""Tests for Tascer SDK wrapper - TascerAgent and related classes."""

import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from tascer.sdk_wrapper import (
    TascerAgent,
    TascerAgentOptions,
    ToolValidationConfig,
    ToolExecutionRecord,
)
from tascer.contracts import GateResult, Context, GitState


class TestToolValidationConfig:
    """Tests for ToolValidationConfig dataclass."""

    def test_default_values(self):
        """Config should have sensible defaults."""
        config = ToolValidationConfig(tool_name="Edit")

        assert config.tool_name == "Edit"
        assert config.pre_gates == []
        assert config.post_gates == []
        assert config.timeout_ms == 30000
        assert config.require_proof is True

    def test_custom_gates(self):
        """Config should accept custom gate lists."""
        config = ToolValidationConfig(
            tool_name="Bash",
            pre_gates=["command_allowed"],
            post_gates=["exit_code_zero", "no_secrets"],
        )

        assert "command_allowed" in config.pre_gates
        assert len(config.post_gates) == 2

    def test_to_dict_roundtrip(self):
        """Config should serialize and deserialize correctly."""
        original = ToolValidationConfig(
            tool_name="Read",
            pre_gates=["file_exists"],
            post_gates=["content_valid"],
            timeout_ms=5000,
        )

        data = original.to_dict()
        restored = ToolValidationConfig.from_dict(data)

        assert restored.tool_name == original.tool_name
        assert restored.pre_gates == original.pre_gates
        assert restored.timeout_ms == original.timeout_ms


class TestTascerAgentOptions:
    """Tests for TascerAgentOptions."""

    def test_default_options(self):
        """Default options should be safe and useful."""
        opts = TascerAgentOptions()

        assert opts.capture_git_state is True
        assert opts.generate_proofs is True
        assert opts.store_to_ab is True
        assert "PATH" in opts.env_allowlist

    def test_tool_config_lookup(self):
        """Should store tool-specific configs."""
        opts = TascerAgentOptions(
            tool_configs={
                "Edit": ToolValidationConfig(
                    tool_name="Edit",
                    post_gates=["syntax_valid"],
                )
            }
        )

        assert "Edit" in opts.tool_configs
        assert "syntax_valid" in opts.tool_configs["Edit"].post_gates

    def test_default_gates(self):
        """Should support default gates for all tools."""
        opts = TascerAgentOptions(
            default_pre_gates=["check_permissions"],
            default_post_gates=["log_execution"],
        )

        assert "check_permissions" in opts.default_pre_gates
        assert "log_execution" in opts.default_post_gates


class TestToolExecutionRecord:
    """Tests for ToolExecutionRecord."""

    def test_basic_creation(self):
        """Record should capture tool execution basics."""
        record = ToolExecutionRecord(
            tool_use_id="tu_123",
            tool_name="Read",
            timestamp_start="2026-01-09T00:00:00",
            tool_input={"file_path": "/test.py"},
        )

        assert record.tool_use_id == "tu_123"
        assert record.tool_name == "Read"
        assert record.status == "pending"
        assert record.proof_hash == ""

    def test_to_dict_roundtrip(self):
        """Record should serialize/deserialize correctly."""
        record = ToolExecutionRecord(
            tool_use_id="tu_456",
            tool_name="Bash",
            timestamp_start="2026-01-09T00:00:00",
            timestamp_end="2026-01-09T00:00:01",
            tool_input={"command": "ls"},
            tool_output="file1.py\nfile2.py",
            status="validated",
            proof_hash="abc123def456",
        )

        data = record.to_dict()
        restored = ToolExecutionRecord.from_dict(data)

        assert restored.tool_use_id == record.tool_use_id
        assert restored.tool_name == record.tool_name
        assert restored.tool_output == record.tool_output
        assert restored.proof_hash == record.proof_hash
        assert restored.status == record.status

    def test_with_gate_results(self):
        """Record should handle gate results."""
        record = ToolExecutionRecord(
            tool_use_id="tu_789",
            tool_name="Edit",
            timestamp_start="2026-01-09T00:00:00",
        )

        record.pre_gate_results.append(
            GateResult(gate_name="file_exists", passed=True, message="OK")
        )
        record.post_gate_results.append(
            GateResult(gate_name="syntax_valid", passed=True, message="Valid")
        )

        data = record.to_dict()
        assert len(data["pre_gate_results"]) == 1
        assert len(data["post_gate_results"]) == 1
        assert data["pre_gate_results"][0]["gate_name"] == "file_exists"

    def test_with_context(self):
        """Record should handle context."""
        record = ToolExecutionRecord(
            tool_use_id="tu_context",
            tool_name="Bash",
            timestamp_start="2026-01-09T00:00:00",
        )

        record.context = Context(
            run_id="run_1",
            tasc_id="tasc_1",
            cwd="/home/user/project",
            git_state=GitState(
                branch="main",
                commit="abc123",
                dirty=False,
                diff_stat="",
                status="",
            ),
        )

        data = record.to_dict()
        assert data["context"]["cwd"] == "/home/user/project"
        assert data["context"]["git_state"]["branch"] == "main"


class TestTascerAgent:
    """Tests for TascerAgent class."""

    def test_init_default_options(self):
        """Agent should initialize with default options."""
        agent = TascerAgent()

        assert agent.tascer_options is not None
        assert agent.tascer_options.generate_proofs is True
        assert len(agent._execution_records) == 0

    def test_init_custom_options(self):
        """Agent should accept custom options."""
        opts = TascerAgentOptions(
            generate_proofs=False,
            capture_git_state=False,
        )
        agent = TascerAgent(tascer_options=opts)

        assert agent.tascer_options.generate_proofs is False
        assert agent.tascer_options.capture_git_state is False

    def test_builtin_gates_registered(self):
        """Agent should have built-in gates registered."""
        agent = TascerAgent()

        assert "exit_code_zero" in agent._gates
        assert "always_block" in agent._gates
        assert "always_pass" in agent._gates

    def test_register_gate_direct(self):
        """Should register gate directly."""
        agent = TascerAgent()

        def my_gate(record, phase):
            return GateResult(gate_name="my_gate", passed=True, message="OK")

        agent.register_gate("my_gate", my_gate)

        assert "my_gate" in agent._gates

    def test_register_gate_decorator(self):
        """Should register gate as decorator."""
        agent = TascerAgent()

        @agent.register_gate("decorated_gate")
        def my_gate(record, phase):
            return GateResult(gate_name="decorated_gate", passed=True, message="OK")

        assert "decorated_gate" in agent._gates

    def test_get_tool_config_existing(self):
        """Should return existing tool config."""
        agent = TascerAgent(
            tascer_options=TascerAgentOptions(
                tool_configs={
                    "Edit": ToolValidationConfig(
                        tool_name="Edit",
                        pre_gates=["check"],
                    )
                }
            )
        )

        config = agent._get_tool_config("Edit")
        assert config.tool_name == "Edit"
        assert "check" in config.pre_gates

    def test_get_tool_config_default(self):
        """Should return default config for unknown tool."""
        agent = TascerAgent()

        config = agent._get_tool_config("UnknownTool")
        assert config.tool_name == "UnknownTool"
        assert config.pre_gates == []

    def test_find_record(self):
        """Should find record by tool_use_id."""
        agent = TascerAgent()

        record1 = ToolExecutionRecord(
            tool_use_id="tu_1",
            tool_name="Read",
            timestamp_start="2026-01-09T00:00:00",
        )
        record2 = ToolExecutionRecord(
            tool_use_id="tu_2",
            tool_name="Edit",
            timestamp_start="2026-01-09T00:00:01",
        )

        agent._execution_records.append(record1)
        agent._execution_records.append(record2)

        found = agent._find_record("tu_1")
        assert found is record1

        found = agent._find_record("tu_2")
        assert found is record2

        found = agent._find_record("nonexistent")
        assert found is None

    def test_get_validation_report(self):
        """Should return copy of execution records."""
        agent = TascerAgent()

        record = ToolExecutionRecord(
            tool_use_id="tu_report",
            tool_name="Bash",
            timestamp_start="2026-01-09T00:00:00",
        )
        agent._execution_records.append(record)

        report = agent.get_validation_report()
        assert len(report) == 1
        assert report[0].tool_use_id == "tu_report"

        # Should be a copy
        report.clear()
        assert len(agent._execution_records) == 1


class TestTascerAgentHooks:
    """Tests for TascerAgent hook behavior."""

    @pytest.fixture
    def agent(self):
        """Create agent with test config."""
        return TascerAgent(
            tascer_options=TascerAgentOptions(
                tool_configs={
                    "Edit": ToolValidationConfig(
                        tool_name="Edit",
                        pre_gates=["always_pass"],
                        post_gates=["always_pass"],
                    )
                },
                capture_git_state=False,
                capture_env=False,
            )
        )

    @pytest.mark.asyncio
    async def test_pre_hook_creates_record(self, agent):
        """Pre-hook should create execution record."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "/test.py", "content": "x = 1"},
        }

        result = await agent._pre_tool_hook(input_data, "tu_001", None)

        assert len(agent._execution_records) == 1
        assert agent._execution_records[0].tool_name == "Edit"
        assert agent._execution_records[0].tool_use_id == "tu_001"
        assert result == {}  # No block

    @pytest.mark.asyncio
    async def test_pre_hook_captures_input(self, agent):
        """Pre-hook should capture tool input."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
        }

        await agent._pre_tool_hook(input_data, "tu_input", None)

        record = agent._execution_records[0]
        assert record.tool_input == {"command": "ls -la"}

    @pytest.mark.asyncio
    async def test_pre_hook_blocks_on_failed_gate(self, agent):
        """Pre-hook should block when gate fails."""
        # Add a config with blocking gate
        agent.tascer_options.tool_configs["Dangerous"] = ToolValidationConfig(
            tool_name="Dangerous",
            pre_gates=["always_block"],
        )

        input_data = {"tool_name": "Dangerous", "tool_input": {}}
        result = await agent._pre_tool_hook(input_data, "tu_blocked", None)

        assert result.get("block") is True
        assert "blocked by policy" in result.get("message", "")
        assert agent._execution_records[0].status == "blocked"

    @pytest.mark.asyncio
    async def test_post_hook_updates_record(self, agent):
        """Post-hook should update existing record."""
        # Create record via pre-hook
        input_data = {"tool_name": "Edit", "tool_input": {}}
        await agent._pre_tool_hook(input_data, "tu_post", None)

        # Call post-hook
        result_data = {"tool_result": "File edited successfully"}
        await agent._post_tool_hook(result_data, "tu_post", None)

        record = agent._execution_records[0]
        assert record.tool_output == "File edited successfully"
        assert record.timestamp_end is not None

    @pytest.mark.asyncio
    async def test_post_hook_generates_proof(self, agent):
        """Post-hook should generate proof hash."""
        input_data = {"tool_name": "Edit", "tool_input": {"file": "test.py"}}
        await agent._pre_tool_hook(input_data, "tu_proof", None)

        result_data = {"tool_result": "Done"}
        await agent._post_tool_hook(result_data, "tu_proof", None)

        record = agent._execution_records[0]
        assert record.proof_hash != ""
        assert len(record.proof_hash) == 16  # SHA256 truncated

    @pytest.mark.asyncio
    async def test_post_hook_sets_validated_status(self, agent):
        """Post-hook should set validated status when gates pass."""
        input_data = {"tool_name": "Edit", "tool_input": {}}
        await agent._pre_tool_hook(input_data, "tu_validated", None)

        result_data = {"tool_result": "Success"}
        await agent._post_tool_hook(result_data, "tu_validated", None)

        record = agent._execution_records[0]
        assert record.status == "validated"

    @pytest.mark.asyncio
    async def test_post_hook_sets_failed_status(self, agent):
        """Post-hook should set failed status when gates fail."""
        # Configure with failing post-gate
        agent.tascer_options.tool_configs["FailPost"] = ToolValidationConfig(
            tool_name="FailPost",
            pre_gates=["always_pass"],
            post_gates=["always_block"],
        )

        input_data = {"tool_name": "FailPost", "tool_input": {}}
        await agent._pre_tool_hook(input_data, "tu_failed", None)

        result_data = {"tool_result": "Done"}
        await agent._post_tool_hook(result_data, "tu_failed", None)

        record = agent._execution_records[0]
        assert record.status == "failed"


class TestProofGeneration:
    """Tests for proof generation and verification."""

    def test_proof_hash_deterministic(self):
        """Same input should produce same proof hash."""
        agent = TascerAgent()

        record1 = ToolExecutionRecord(
            tool_use_id="tu_100",
            tool_name="Read",
            timestamp_start="2026-01-09T12:00:00",
            timestamp_end="2026-01-09T12:00:01",
            tool_input={"file_path": "/test.py"},
            tool_output="content",
        )

        record2 = ToolExecutionRecord(
            tool_use_id="tu_100",
            tool_name="Read",
            timestamp_start="2026-01-09T12:00:00",
            timestamp_end="2026-01-09T12:00:01",
            tool_input={"file_path": "/test.py"},
            tool_output="content",
        )

        hash1 = agent._generate_proof(record1)
        hash2 = agent._generate_proof(record2)

        assert hash1 == hash2

    def test_proof_changes_with_input(self):
        """Different input should produce different proof."""
        agent = TascerAgent()

        record1 = ToolExecutionRecord(
            tool_use_id="tu_101",
            tool_name="Read",
            timestamp_start="2026-01-09T12:00:00",
            tool_input={"file_path": "/test.py"},
        )

        record2 = ToolExecutionRecord(
            tool_use_id="tu_101",
            tool_name="Read",
            timestamp_start="2026-01-09T12:00:00",
            tool_input={"file_path": "/other.py"},  # Different file
        )

        hash1 = agent._generate_proof(record1)
        hash2 = agent._generate_proof(record2)

        assert hash1 != hash2

    def test_proof_changes_with_output(self):
        """Different output should produce different proof."""
        agent = TascerAgent()

        record1 = ToolExecutionRecord(
            tool_use_id="tu_102",
            tool_name="Bash",
            timestamp_start="2026-01-09T12:00:00",
            tool_input={"command": "echo test"},
            tool_output="test",
        )

        record2 = ToolExecutionRecord(
            tool_use_id="tu_102",
            tool_name="Bash",
            timestamp_start="2026-01-09T12:00:00",
            tool_input={"command": "echo test"},
            tool_output="different",  # Different output
        )

        hash1 = agent._generate_proof(record1)
        hash2 = agent._generate_proof(record2)

        assert hash1 != hash2

    def test_verify_proofs_all_valid(self):
        """verify_proofs should return True when all valid."""
        agent = TascerAgent()

        for i in range(3):
            record = ToolExecutionRecord(
                tool_use_id=f"tu_{i}",
                tool_name="Read",
                timestamp_start="2026-01-09T12:00:00",
                tool_input={"file": f"file{i}.py"},
            )
            record.proof_hash = agent._generate_proof(record)
            agent._execution_records.append(record)

        assert agent.verify_proofs() is True

    def test_verify_proofs_detects_tampering(self):
        """verify_proofs should detect tampered records."""
        agent = TascerAgent()

        record = ToolExecutionRecord(
            tool_use_id="tu_999",
            tool_name="Bash",
            timestamp_start="2026-01-09T12:00:00",
            tool_input={"command": "ls"},
        )
        record.proof_hash = agent._generate_proof(record)

        # Tamper with the record after proof generation
        record.tool_input = {"command": "rm -rf /"}

        agent._execution_records.append(record)

        assert agent.verify_proofs() is False

    def test_verify_empty_records(self):
        """verify_proofs should return True for empty records."""
        agent = TascerAgent()
        assert agent.verify_proofs() is True

    def test_verify_no_proof_hash(self):
        """Records without proof hash should pass verification."""
        agent = TascerAgent()

        record = ToolExecutionRecord(
            tool_use_id="tu_no_proof",
            tool_name="Read",
            timestamp_start="2026-01-09T12:00:00",
            # No proof_hash set
        )
        agent._execution_records.append(record)

        assert agent.verify_proofs() is True


class TestBuiltinGates:
    """Tests for built-in validation gates."""

    def test_exit_code_zero_passes(self):
        """exit_code_zero should pass for exit code 0."""
        record = ToolExecutionRecord(
            tool_use_id="tu_exit",
            tool_name="Bash",
            timestamp_start="2026-01-09T12:00:00",
            tool_output={"exit_code": 0, "stdout": "success"},
        )

        result = TascerAgent._gate_exit_code_zero(record, "post")

        assert result.passed is True
        assert "Exit code: 0" in result.message

    def test_exit_code_zero_fails(self):
        """exit_code_zero should fail for non-zero exit code."""
        record = ToolExecutionRecord(
            tool_use_id="tu_exit_fail",
            tool_name="Bash",
            timestamp_start="2026-01-09T12:00:00",
            tool_output={"exit_code": 1, "stderr": "error"},
        )

        result = TascerAgent._gate_exit_code_zero(record, "post")

        assert result.passed is False
        assert "Non-zero exit: 1" in result.message

    def test_exit_code_zero_skips_pre(self):
        """exit_code_zero should skip pre-phase."""
        record = ToolExecutionRecord(
            tool_use_id="tu_exit_pre",
            tool_name="Bash",
            timestamp_start="2026-01-09T12:00:00",
        )

        result = TascerAgent._gate_exit_code_zero(record, "pre")

        assert result.passed is True
        assert "skipped" in result.message.lower()

    def test_always_block_blocks(self):
        """always_block should always block."""
        record = ToolExecutionRecord(
            tool_use_id="tu_block",
            tool_name="Delete",
            timestamp_start="2026-01-09T12:00:00",
        )

        result = TascerAgent._gate_always_block(record, "pre")

        assert result.passed is False
        assert "blocked by policy" in result.message

    def test_always_pass_passes(self):
        """always_pass should always pass."""
        record = ToolExecutionRecord(
            tool_use_id="tu_pass",
            tool_name="Read",
            timestamp_start="2026-01-09T12:00:00",
        )

        result = TascerAgent._gate_always_pass(record, "pre")

        assert result.passed is True


class TestExportReport:
    """Tests for report export functionality."""

    def test_export_report(self, tmp_path):
        """Should export report to JSON file."""
        agent = TascerAgent()
        agent._session_id = "test_session_123"

        record = ToolExecutionRecord(
            tool_use_id="tu_export",
            tool_name="Read",
            timestamp_start="2026-01-09T12:00:00",
            status="validated",
        )
        record.proof_hash = agent._generate_proof(record)
        agent._execution_records.append(record)

        report_path = tmp_path / "report.json"
        agent.export_report(str(report_path))

        assert report_path.exists()

        with open(report_path) as f:
            data = json.load(f)

        assert data["session_id"] == "test_session_123"
        assert data["proofs_valid"] is True
        assert len(data["records"]) == 1
        assert data["records"][0]["tool_name"] == "Read"


class TestRecallDataClasses:
    """Tests for recall-related data classes."""

    def test_recall_config_defaults(self):
        """RecallConfig should have sensible defaults."""
        from tascer.sdk_wrapper import RecallConfig

        config = RecallConfig()

        assert config.enabled is True
        assert config.auto_context is False
        assert config.auto_context_limit == 3
        assert config.index_on_store is True
        assert config.default_top_k == 5
        assert config.include_failed is False
        assert config.verify_proofs is True

    def test_recall_query_defaults(self):
        """RecallQuery should have sensible defaults."""
        from tascer.sdk_wrapper import RecallQuery

        query = RecallQuery(query="test search")

        assert query.query == "test search"
        assert query.tool_name is None
        assert query.session_id is None
        assert query.top_k == 5
        assert query.use_neural is True
        assert query.min_score == 0.0

    def test_recall_result_to_dict(self):
        """RecallResult should serialize correctly."""
        from tascer.sdk_wrapper import RecallResult

        result = RecallResult(
            card_id=42,
            score=0.95,
            tool_name="Read",
            tool_input={"file_path": "/test.py"},
            tool_output="content here",
            timestamp="2026-01-09T12:00:00",
            session_id="sess_001",
            proof_valid=True,
            proof_hash="abc123def456",
        )

        data = result.to_dict()

        assert data["card_id"] == 42
        assert data["score"] == 0.95
        assert data["tool_name"] == "Read"
        assert data["proof_valid"] is True


class TestRecallConfig:
    """Tests for recall configuration in TascerAgentOptions."""

    def test_options_include_recall_config(self):
        """TascerAgentOptions should include recall_config."""
        from tascer.sdk_wrapper import RecallConfig

        options = TascerAgentOptions()

        assert hasattr(options, "recall_config")
        assert isinstance(options.recall_config, RecallConfig)

    def test_custom_recall_config(self):
        """Should accept custom recall config."""
        from tascer.sdk_wrapper import RecallConfig

        custom = RecallConfig(
            enabled=True,
            auto_context=True,
            default_top_k=10,
        )
        options = TascerAgentOptions(recall_config=custom)

        assert options.recall_config.auto_context is True
        assert options.recall_config.default_top_k == 10


class TestExtractConcepts:
    """Tests for concept extraction for neural indexing."""

    def test_extracts_tool_name(self):
        """Should extract tool name as concept."""
        agent = TascerAgent()
        record = ToolExecutionRecord(
            tool_use_id="tu_001",
            tool_name="Read",
            timestamp_start="2026-01-09T12:00:00",
            tool_input={},
        )

        concepts = agent._extract_concepts(record)

        assert "read" in concepts

    def test_extracts_from_file_path(self):
        """Should extract words from file paths."""
        agent = TascerAgent()
        record = ToolExecutionRecord(
            tool_use_id="tu_002",
            tool_name="Read",
            timestamp_start="2026-01-09T12:00:00",
            tool_input={"file_path": "/app/player/structs.h"},
        )

        concepts = agent._extract_concepts(record)

        assert "player" in concepts
        assert "structs" in concepts

    def test_extracts_from_command(self):
        """Should extract words from commands."""
        agent = TascerAgent()
        record = ToolExecutionRecord(
            tool_use_id="tu_003",
            tool_name="Bash",
            timestamp_start="2026-01-09T12:00:00",
            tool_input={"command": "ghidra_headless analyze binary.exe"},
        )

        concepts = agent._extract_concepts(record)

        assert "ghidra_headless" in concepts or "ghidra" in concepts
        assert "analyze" in concepts
        assert "binary" in concepts

    def test_limits_concept_count(self):
        """Should limit concepts to 20."""
        agent = TascerAgent()
        record = ToolExecutionRecord(
            tool_use_id="tu_004",
            tool_name="Bash",
            timestamp_start="2026-01-09T12:00:00",
            tool_input={"command": " ".join([f"word{i}" for i in range(50)])},
        )

        concepts = agent._extract_concepts(record)

        assert len(concepts) <= 20

    def test_deduplicates_concepts(self):
        """Should deduplicate concepts."""
        agent = TascerAgent()
        record = ToolExecutionRecord(
            tool_use_id="tu_005",
            tool_name="Read",
            timestamp_start="2026-01-09T12:00:00",
            tool_input={"file_path": "/player/player.py"},
        )

        concepts = agent._extract_concepts(record)
        player_count = sum(1 for c in concepts if c == "player")

        assert player_count == 1


class TestRecallWithoutABMemory:
    """Tests for recall when AB Memory is not available."""

    def test_recall_returns_empty_without_ab(self):
        """recall() should return empty list without AB Memory."""
        agent = TascerAgent()  # No ab_memory passed

        results = agent.recall("test query")

        assert results == []

    def test_recall_tool_returns_empty_without_ab(self):
        """recall_tool() should return empty list without AB Memory."""
        agent = TascerAgent()

        results = agent.recall_tool("Read")

        assert results == []

    def test_recall_session_returns_empty_without_session(self):
        """recall_session() should return empty without session."""
        agent = TascerAgent()

        results = agent.recall_session()

        assert results == []

    def test_recall_similar_returns_empty_without_ab(self):
        """recall_similar() should return empty without AB Memory."""
        agent = TascerAgent()

        results = agent.recall_similar({"file_path": "/test.py"})

        assert results == []

    def test_get_context_for_returns_empty_without_ab(self):
        """get_context_for() should return empty without AB Memory."""
        agent = TascerAgent()

        results = agent.get_context_for("Read", {"file_path": "/test.py"})

        assert results == []
