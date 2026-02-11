"""Tests for the `supe memory` CLI commands."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from supe.cli import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.sqlite"
        # Yield the path and set environment
        with patch.dict(os.environ, {"TASC_DB": str(db_path)}):
            yield db_path


class TestMemorySearchCommand:
    """Tests for `supe memory search` command."""

    def test_search_no_database(self, runner):
        """Should handle missing database gracefully."""
        with patch.dict(os.environ, {"TASC_DB": "/nonexistent/path.sqlite"}):
            result = runner.invoke(cli, ["memory", "search", "test"])

        assert result.exit_code == 0
        assert "No memory database found" in result.output

    def test_search_no_results(self, runner, temp_db):
        """Should handle empty results."""
        # Create an empty database
        from ab.abdb import ABMemory
        ABMemory(str(temp_db))

        result = runner.invoke(cli, ["memory", "search", "nonexistent"])

        assert result.exit_code == 0
        assert "No results found" in result.output

    def test_search_with_results(self, runner, temp_db):
        """Should display search results in table format."""
        from ab.abdb import ABMemory
        from ab.models import Buffer

        mem = ABMemory(str(temp_db))
        moment = mem.create_moment(master_input="test moment")
        mem.store_card(
            label="test_card",
            buffers=[Buffer(name="content", payload=b"searchable content")],
            owner_self="test_owner",
            moment_id=moment.id,
        )

        result = runner.invoke(cli, ["memory", "search", "searchable"])

        assert result.exit_code == 0
        assert "test_card" in result.output

    def test_search_json_format(self, runner, temp_db):
        """Should output JSON when requested."""
        from ab.abdb import ABMemory
        from ab.models import Buffer

        mem = ABMemory(str(temp_db))
        moment = mem.create_moment(master_input="test moment")
        mem.store_card(
            label="json_card",
            buffers=[Buffer(name="data", payload=b"json test content")],
            owner_self="owner",
            moment_id=moment.id,
        )

        result = runner.invoke(cli, ["memory", "search", "json", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert any(c["label"] == "json_card" for c in data)

    def test_search_with_label_filter(self, runner, temp_db):
        """Should filter by label."""
        from ab.abdb import ABMemory
        from ab.models import Buffer

        mem = ABMemory(str(temp_db))
        moment = mem.create_moment(master_input="test")
        mem.store_card(
            label="target_label",
            buffers=[Buffer(name="data", payload=b"content")],
            moment_id=moment.id,
        )
        mem.store_card(
            label="other_label",
            buffers=[Buffer(name="data", payload=b"content")],
            moment_id=moment.id,
        )

        result = runner.invoke(cli, ["memory", "search", "content", "-l", "target_label"])

        assert result.exit_code == 0
        assert "target_label" in result.output


class TestMemorySemanticCommand:
    """Tests for `supe memory semantic` command."""

    def test_semantic_no_database(self, runner):
        """Should handle missing database."""
        with patch.dict(os.environ, {"TASC_DB": "/nonexistent/path.sqlite"}):
            result = runner.invoke(cli, ["memory", "semantic", "test query"])

        assert result.exit_code == 0
        assert "No memory database found" in result.output

    def test_semantic_no_results(self, runner, temp_db):
        """Should handle no matches."""
        from ab.abdb import ABMemory
        ABMemory(str(temp_db))

        result = runner.invoke(cli, ["memory", "semantic", "completely unique query xyz"])

        assert result.exit_code == 0
        assert "No semantic matches" in result.output

    def test_semantic_with_results(self, runner, temp_db):
        """Should show semantic search results with scores."""
        from ab.abdb import ABMemory
        from ab.models import Buffer

        mem = ABMemory(str(temp_db))
        moment = mem.create_moment(master_input="test")
        mem.store_card(
            label="auth_module",
            buffers=[Buffer(name="desc", payload=b"user authentication login flow")],
            moment_id=moment.id,
        )

        result = runner.invoke(cli, ["memory", "semantic", "authentication"])

        assert result.exit_code == 0
        # Should show the card with a similarity score
        assert "auth_module" in result.output or "Semantic" in result.output


class TestMemoryRecallCommand:
    """Tests for `supe memory recall` command."""

    def test_recall_no_database(self, runner):
        """Should handle missing database."""
        with patch.dict(os.environ, {"TASC_DB": "/nonexistent/path.sqlite"}):
            result = runner.invoke(cli, ["memory", "recall", "test"])

        assert result.exit_code == 0
        assert "No memory database found" in result.output

    def test_recall_empty_results(self, runner, temp_db):
        """Should handle empty recall results."""
        from ab.abdb import ABMemory
        ABMemory(str(temp_db))

        result = runner.invoke(cli, ["memory", "recall", "nonexistent query"])

        assert result.exit_code == 0
        assert "No recall results" in result.output

    def test_recall_json_format(self, runner, temp_db):
        """Should output JSON with scores."""
        from ab.abdb import ABMemory
        from ab.models import Buffer

        mem = ABMemory(str(temp_db))
        moment = mem.create_moment(master_input="test")
        mem.store_card(
            label="recall_test",
            buffers=[Buffer(name="data", payload=b"recall query match")],
            moment_id=moment.id,
        )

        result = runner.invoke(cli, ["memory", "recall", "recall", "-f", "json"])

        assert result.exit_code == 0
        # Output should be valid JSON if there are results
        if "No recall results" not in result.output:
            data = json.loads(result.output)
            assert isinstance(data, list)


class TestMemoryTimelineCommand:
    """Tests for `supe memory timeline` command."""

    def test_timeline_no_database(self, runner):
        """Should handle missing database."""
        with patch.dict(os.environ, {"TASC_DB": "/nonexistent/path.sqlite"}):
            result = runner.invoke(
                cli, ["memory", "timeline", "--start", "2025-01-01", "--end", "2025-12-31"]
            )

        assert result.exit_code == 0
        assert "No memory database found" in result.output

    def test_timeline_empty_range(self, runner, temp_db):
        """Should handle empty time range."""
        from ab.abdb import ABMemory
        ABMemory(str(temp_db))

        result = runner.invoke(
            cli, ["memory", "timeline", "--start", "2020-01-01", "--end", "2020-01-02"]
        )

        assert result.exit_code == 0
        assert "No moments" in result.output

    def test_timeline_with_moments(self, runner, temp_db):
        """Should show moments in time range."""
        from ab.abdb import ABMemory

        mem = ABMemory(str(temp_db))
        # Create some moments - they get current timestamp
        mem.create_moment(master_input="moment 1")
        mem.create_moment(master_input="moment 2")

        # Use a wide date range that includes now
        result = runner.invoke(
            cli, ["memory", "timeline", "--start", "2020-01-01", "--end", "2030-12-31"]
        )

        assert result.exit_code == 0
        assert "Timeline" in result.output or "moments" in result.output

    def test_timeline_json_format(self, runner, temp_db):
        """Should output JSON format."""
        from ab.abdb import ABMemory

        mem = ABMemory(str(temp_db))
        mem.create_moment(master_input="test moment")

        result = runner.invoke(
            cli, ["memory", "timeline", "-s", "2020-01-01", "-e", "2030-12-31", "-f", "json"]
        )

        assert result.exit_code == 0
        if "No moments" not in result.output:
            data = json.loads(result.output)
            assert isinstance(data, list)
            assert all("id" in m and "timestamp" in m for m in data)


class TestMemoryCardCommand:
    """Tests for `supe memory card` command."""

    def test_card_no_database(self, runner):
        """Should handle missing database."""
        with patch.dict(os.environ, {"TASC_DB": "/nonexistent/path.sqlite"}):
            result = runner.invoke(cli, ["memory", "card", "1"])

        assert result.exit_code == 0
        assert "No memory database found" in result.output

    def test_card_not_found(self, runner, temp_db):
        """Should handle card not found."""
        from ab.abdb import ABMemory
        ABMemory(str(temp_db))

        result = runner.invoke(cli, ["memory", "card", "9999"])

        assert result.exit_code == 0
        assert "not found" in result.output

    def test_card_details(self, runner, temp_db):
        """Should show card details."""
        from ab.abdb import ABMemory
        from ab.models import Buffer

        mem = ABMemory(str(temp_db))
        moment = mem.create_moment(master_input="test")
        card = mem.store_card(
            label="detailed_card",
            buffers=[
                Buffer(name="content", headers={"type": "code"}, payload=b"def hello(): pass"),
            ],
            owner_self="test_owner",
            moment_id=moment.id,
            master_input="some input",
            master_output="some output",
        )

        result = runner.invoke(cli, ["memory", "card", str(card.id)])

        assert result.exit_code == 0
        assert "detailed_card" in result.output
        assert "test_owner" in result.output or "Owner" in result.output

    def test_card_json_format(self, runner, temp_db):
        """Should output JSON format."""
        from ab.abdb import ABMemory
        from ab.models import Buffer

        mem = ABMemory(str(temp_db))
        moment = mem.create_moment(master_input="test")
        card = mem.store_card(
            label="json_card",
            buffers=[Buffer(name="data", payload=b"content")],
            moment_id=moment.id,
        )

        result = runner.invoke(cli, ["memory", "card", str(card.id), "-f", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["label"] == "json_card"
        assert "buffers" in data


class TestMemoryContextCommand:
    """Tests for `supe memory context` command."""

    def test_context_no_database(self, runner):
        """Should handle missing database."""
        with patch.dict(os.environ, {"TASC_DB": "/nonexistent/path.sqlite"}):
            result = runner.invoke(cli, ["memory", "context", "Read"])

        assert result.exit_code == 0
        assert "No memory database found" in result.output

    def test_context_no_relevant_context(self, runner, temp_db):
        """Should handle no relevant context."""
        from ab.abdb import ABMemory
        ABMemory(str(temp_db))

        result = runner.invoke(cli, ["memory", "context", "Read"])

        assert result.exit_code == 0
        assert "No relevant context" in result.output

    def test_context_with_tool_input(self, runner, temp_db):
        """Should parse tool input JSON."""
        from ab.abdb import ABMemory
        ABMemory(str(temp_db))

        result = runner.invoke(
            cli,
            ["memory", "context", "Read", "--input", '{"file_path": "/test.py"}']
        )

        assert result.exit_code == 0
        # Either shows context or reports none found
        assert "context" in result.output.lower() or "No relevant" in result.output

    def test_context_invalid_json(self, runner, temp_db):
        """Should handle invalid JSON input."""
        from ab.abdb import ABMemory
        ABMemory(str(temp_db))

        result = runner.invoke(
            cli,
            ["memory", "context", "Read", "--input", "not valid json"]
        )

        assert result.exit_code == 0
        assert "Invalid JSON" in result.output


class TestMemoryCommandGroup:
    """Tests for the memory command group itself."""

    def test_memory_group_exists(self, runner):
        """Memory command group should exist."""
        result = runner.invoke(cli, ["memory", "--help"])

        assert result.exit_code == 0
        assert "Memory query commands" in result.output

    def test_memory_subcommands_listed(self, runner):
        """All subcommands should be listed."""
        result = runner.invoke(cli, ["memory", "--help"])

        assert "search" in result.output
        assert "semantic" in result.output
        assert "recall" in result.output
        assert "timeline" in result.output
        assert "card" in result.output
        assert "context" in result.output
