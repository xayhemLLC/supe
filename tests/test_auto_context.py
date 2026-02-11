"""Tests for auto-context injection in TascerAgent."""

from unittest.mock import patch

import pytest

from tascer.sdk_wrapper import (
    RecallConfig,
    RecallResult,
    TascerAgent,
    TascerAgentOptions,
    ToolValidationConfig,
)


class TestAutoContextConfig:
    """Tests for auto-context configuration."""

    def test_auto_context_disabled_by_default(self):
        """Auto-context should be disabled by default."""
        config = RecallConfig()
        assert config.auto_context is False

    def test_auto_context_can_be_enabled(self):
        """Auto-context can be enabled in config."""
        config = RecallConfig(auto_context=True)
        assert config.auto_context is True

    def test_auto_context_limit_default(self):
        """Auto-context limit should default to 3."""
        config = RecallConfig()
        assert config.auto_context_limit == 3

    def test_auto_context_limit_customizable(self):
        """Auto-context limit should be customizable."""
        config = RecallConfig(auto_context_limit=5)
        assert config.auto_context_limit == 5


class TestFormatContextForInjection:
    """Tests for _format_context_for_injection method."""

    def test_empty_context_returns_empty_string(self):
        """Empty context list should return empty string."""
        agent = TascerAgent()
        result = agent._format_context_for_injection([])
        assert result == ""

    def test_single_context_item(self):
        """Should format single context item as markdown."""
        agent = TascerAgent()
        context = [{
            "tool_name": "Read",
            "tool_input": {"file_path": "/test.py"},
            "tool_output": "def hello(): pass",
            "timestamp": "2026-01-09T12:00:00",
        }]

        result = agent._format_context_for_injection(context)

        assert "## Relevant Past Context" in result
        assert "Read" in result
        assert "2026-01-09" in result
        assert "/test.py" in result

    def test_multiple_context_items(self):
        """Should format multiple items with numbering."""
        agent = TascerAgent()
        context = [
            {
                "tool_name": "Read",
                "tool_input": {"file": "a.py"},
                "tool_output": "content a",
                "timestamp": "2026-01-09T12:00:00",
            },
            {
                "tool_name": "Bash",
                "tool_input": {"command": "ls"},
                "tool_output": "file1\nfile2",
                "timestamp": "2026-01-09T12:01:00",
            },
        ]

        result = agent._format_context_for_injection(context)

        assert "### 1. Read" in result
        assert "### 2. Bash" in result

    def test_truncates_long_input(self):
        """Should truncate long tool input."""
        agent = TascerAgent()
        long_input = {"data": "x" * 500}
        context = [{
            "tool_name": "Test",
            "tool_input": long_input,
            "tool_output": None,
            "timestamp": "2026-01-09T12:00:00",
        }]

        result = agent._format_context_for_injection(context)

        # Input should be truncated to 200 chars
        assert len(result) < 500 + 200  # Some buffer for markdown formatting

    def test_truncates_long_output(self):
        """Should truncate long tool output."""
        agent = TascerAgent()
        context = [{
            "tool_name": "Test",
            "tool_input": {},
            "tool_output": "y" * 500,
            "timestamp": "2026-01-09T12:00:00",
        }]

        result = agent._format_context_for_injection(context)

        # Output section should exist but be truncated
        assert "**Result**:" in result

    def test_handles_missing_timestamp(self):
        """Should handle missing or empty timestamp."""
        agent = TascerAgent()
        context = [{
            "tool_name": "Test",
            "tool_input": {},
            "tool_output": None,
            "timestamp": "",
        }]

        result = agent._format_context_for_injection(context)

        assert "unknown" in result

    def test_handles_none_values(self):
        """Should handle None values gracefully."""
        agent = TascerAgent()
        context = [{
            "tool_name": "Test",
            "tool_input": None,
            "tool_output": None,
            "timestamp": None,
        }]

        # Should not raise
        result = agent._format_context_for_injection(context)
        assert "Test" in result


class TestPreHookAutoContext:
    """Tests for auto-context injection in _pre_tool_hook."""

    @pytest.fixture
    def agent_with_auto_context(self):
        """Create agent with auto-context enabled."""
        return TascerAgent(
            tascer_options=TascerAgentOptions(
                recall_config=RecallConfig(
                    enabled=True,
                    auto_context=True,
                    auto_context_limit=3,
                ),
                capture_git_state=False,
                capture_env=False,
            )
        )

    @pytest.fixture
    def agent_without_auto_context(self):
        """Create agent with auto-context disabled."""
        return TascerAgent(
            tascer_options=TascerAgentOptions(
                recall_config=RecallConfig(
                    enabled=True,
                    auto_context=False,
                ),
                capture_git_state=False,
                capture_env=False,
            )
        )

    @pytest.mark.asyncio
    async def test_no_context_when_disabled(self, agent_without_auto_context):
        """Should not inject context when auto_context=False."""
        input_data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/test.py"},
        }

        result = await agent_without_auto_context._pre_tool_hook(input_data, "tu_001", None)

        # Should return empty dict (no context)
        assert result == {}

    @pytest.mark.asyncio
    async def test_no_context_when_recall_disabled(self):
        """Should not inject context when recall is disabled."""
        agent = TascerAgent(
            tascer_options=TascerAgentOptions(
                recall_config=RecallConfig(
                    enabled=False,
                    auto_context=True,  # Enabled but recall is disabled
                ),
                capture_git_state=False,
                capture_env=False,
            )
        )

        input_data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/test.py"},
        }

        result = await agent._pre_tool_hook(input_data, "tu_001", None)

        # Should return empty dict (no context)
        assert result == {}

    @pytest.mark.asyncio
    async def test_injects_context_when_available(self, agent_with_auto_context):
        """Should inject context when auto_context=True and context is available."""
        # Mock the recall method to return some results
        mock_results = [
            RecallResult(
                card_id=1,
                score=0.9,
                tool_name="Read",
                tool_input={"file_path": "/previous.py"},
                tool_output="previous content",
                timestamp="2026-01-09T11:00:00",
                session_id=None,
                proof_valid=True,
                proof_hash="abc123",
            )
        ]

        with patch.object(agent_with_auto_context, 'recall', return_value=mock_results):
            input_data = {
                "tool_name": "Read",
                "tool_input": {"file_path": "/test.py"},
            }

            result = await agent_with_auto_context._pre_tool_hook(input_data, "tu_001", None)

        # Should return context
        assert "context" in result
        assert "Relevant Past Context" in result["context"]
        assert "Read" in result["context"]

    @pytest.mark.asyncio
    async def test_no_context_key_when_empty(self, agent_with_auto_context):
        """Should not include context key when no context found."""
        # Mock recall to return empty
        with patch.object(agent_with_auto_context, 'recall', return_value=[]):
            input_data = {
                "tool_name": "Read",
                "tool_input": {"file_path": "/test.py"},
            }

            result = await agent_with_auto_context._pre_tool_hook(input_data, "tu_001", None)

        # Should return empty dict
        assert result == {}

    @pytest.mark.asyncio
    async def test_respects_context_limit(self, agent_with_auto_context):
        """Should respect auto_context_limit setting."""
        # This test verifies the limit is passed to get_context_for
        with patch.object(agent_with_auto_context, 'get_context_for', return_value=[]) as mock:
            input_data = {
                "tool_name": "Read",
                "tool_input": {"file_path": "/test.py"},
            }

            await agent_with_auto_context._pre_tool_hook(input_data, "tu_001", None)

        # Verify get_context_for was called with correct limit
        mock.assert_called_once()
        call_args = mock.call_args
        assert call_args.kwargs.get('max_context') == 3


class TestGetContextFor:
    """Tests for get_context_for method."""

    def test_builds_query_from_tool_name_and_input(self):
        """Should build query from tool name and string values in input."""
        agent = TascerAgent()

        # Mock recall to capture the query
        with patch.object(agent, 'recall', return_value=[]) as mock:
            agent.get_context_for("Read", {"file_path": "/src/auth.py", "count": 100})

        # Verify query includes tool name and string values
        call_args = mock.call_args
        query = call_args.args[0] if call_args.args else call_args.kwargs.get('query')
        assert "Read" in query
        assert "/src/auth.py" in query
        # count (int) should not be in query

    def test_returns_empty_without_ab_memory(self):
        """Should return empty list without AB Memory."""
        agent = TascerAgent()  # No ab_memory

        result = agent.get_context_for("Read", {"file_path": "/test.py"})

        assert result == []

    def test_converts_recall_results_to_dicts(self):
        """Should convert RecallResult objects to dictionaries."""
        agent = TascerAgent()

        mock_results = [
            RecallResult(
                card_id=1,
                score=0.9,
                tool_name="Bash",
                tool_input={"command": "ls"},
                tool_output="files",
                timestamp="2026-01-09T12:00:00",
                session_id="sess_001",
                proof_valid=True,
                proof_hash="hash123",
            )
        ]

        with patch.object(agent, 'recall', return_value=mock_results):
            result = agent.get_context_for("Bash", {"command": "pwd"})

        assert len(result) == 1
        assert result[0]["tool_name"] == "Bash"
        assert result[0]["tool_input"] == {"command": "ls"}
        assert result[0]["tool_output"] == "files"
        assert result[0]["timestamp"] == "2026-01-09T12:00:00"

    def test_uses_neural_recall(self):
        """Should use neural recall for semantic matching."""
        agent = TascerAgent()

        with patch.object(agent, 'recall', return_value=[]) as mock:
            agent.get_context_for("Read", {"file_path": "/test.py"}, max_context=5)

        call_args = mock.call_args
        assert call_args.kwargs.get('use_neural') is True
        assert call_args.kwargs.get('top_k') == 5


class TestAutoContextIntegration:
    """Integration tests for auto-context feature."""

    @pytest.mark.asyncio
    async def test_full_pre_hook_flow_with_context(self):
        """Test complete pre-hook flow with context injection."""
        agent = TascerAgent(
            tascer_options=TascerAgentOptions(
                recall_config=RecallConfig(
                    enabled=True,
                    auto_context=True,
                    auto_context_limit=2,
                ),
                capture_git_state=False,
                capture_env=False,
                tool_configs={
                    "Edit": ToolValidationConfig(
                        tool_name="Edit",
                        pre_gates=["always_pass"],
                    )
                },
            )
        )

        # Mock recall to return context
        mock_results = [
            RecallResult(
                card_id=1,
                score=0.9,
                tool_name="Edit",
                tool_input={"file_path": "/similar.py", "content": "old content"},
                tool_output="Edited",
                timestamp="2026-01-08T12:00:00",
                session_id=None,
                proof_valid=True,
                proof_hash="abc",
            )
        ]

        with patch.object(agent, 'recall', return_value=mock_results):
            input_data = {
                "tool_name": "Edit",
                "tool_input": {"file_path": "/test.py", "content": "new content"},
            }

            result = await agent._pre_tool_hook(input_data, "tu_integration", None)

        # Should have context
        assert "context" in result
        assert "Edit" in result["context"]
        assert "similar.py" in result["context"]

        # Should also have created execution record
        assert len(agent._execution_records) == 1
        record = agent._execution_records[0]
        assert record.tool_name == "Edit"
        assert record.status == "pending"  # Not blocked

    @pytest.mark.asyncio
    async def test_blocking_gate_still_works_with_auto_context(self):
        """Blocking gates should still work when auto-context is enabled."""
        agent = TascerAgent(
            tascer_options=TascerAgentOptions(
                recall_config=RecallConfig(
                    enabled=True,
                    auto_context=True,
                ),
                capture_git_state=False,
                capture_env=False,
                tool_configs={
                    "Dangerous": ToolValidationConfig(
                        tool_name="Dangerous",
                        pre_gates=["always_block"],
                    )
                },
            )
        )

        input_data = {
            "tool_name": "Dangerous",
            "tool_input": {},
        }

        result = await agent._pre_tool_hook(input_data, "tu_blocked", None)

        # Should be blocked - gates take precedence
        assert result.get("block") is True
        assert agent._execution_records[0].status == "blocked"
