"""Tests for the vault markdown view layer.

Tests cover:
- Pure rendering: card_to_frontmatter, card_to_markdown, generate_index
- Slug generation
- Filesystem export: export_card, export_vault
- ABMemory.vault_index() SQL query
"""

import json
import os
import tempfile

import pytest

from ab.abdb import ABMemory
from ab.models import Buffer, Card, CardStats
from ab.vault import (
    VaultIndexEntry,
    _card_summary,
    _is_text_buffer,
    card_to_frontmatter,
    card_to_markdown,
    export_card,
    export_vault,
    generate_index,
    slugify,
)


@pytest.fixture
def memory():
    """Create a temporary SQLite database for testing."""
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    mem = ABMemory(db_path=path)
    yield mem
    mem.close()
    os.unlink(path)


@pytest.fixture
def sample_card():
    """A card with text and binary buffers."""
    return Card(
        id=42,
        label="decision",
        moment_id=1,
        owner_self="my-project",
        created_at="2026-02-13T10:30:00",
        track="awareness",
        master_input="Should we use request-response or event-driven?",
        master_output="Event-driven for throughput and backpressure.",
        buffers=[
            Buffer(
                name="spec_text",
                headers={"content_type": "text/plain"},
                payload=b"Chose event-driven architecture.",
            ),
            Buffer(
                name="diagram",
                headers={"content_type": "image/png"},
                payload=b"\x89PNG\r\n\x1a\n",
            ),
        ],
    )


@pytest.fixture
def sample_stats():
    return CardStats(card_id=42, strength=0.85, recall_count=3, last_recalled="2026-02-13T11:00:00")


# ---------------------------------------------------------------------------
# Slugify
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert slugify("auth: login & signup?") == "auth-login-signup"

    def test_max_length(self):
        result = slugify("a" * 100, max_len=10)
        assert len(result) <= 10

    def test_empty(self):
        assert slugify("") == ""

    def test_trailing_dash(self):
        result = slugify("hello-world-test", max_len=12)
        assert not result.endswith("-")


# ---------------------------------------------------------------------------
# Pure Rendering
# ---------------------------------------------------------------------------

class TestCardToFrontmatter:
    def test_basic_fields(self, sample_card, sample_stats):
        fm = card_to_frontmatter(sample_card, sample_stats)

        assert fm["id"] == 42
        assert fm["label"] == "decision"
        assert fm["track"] == "awareness"
        assert fm["owner"] == "my-project"
        assert fm["moment_id"] == 1
        assert fm["strength"] == 0.85
        assert fm["recall_count"] == 3
        assert fm["tags"] == []

    def test_without_stats(self, sample_card):
        fm = card_to_frontmatter(sample_card)

        assert fm["strength"] is None
        assert fm["recall_count"] == 0

    def test_created_at_preserved(self, sample_card):
        fm = card_to_frontmatter(sample_card)
        assert fm["created_at"] == "2026-02-13T10:30:00"


class TestCardToMarkdown:
    def test_contains_frontmatter(self, sample_card, sample_stats):
        md = card_to_markdown(sample_card, sample_stats)

        assert md.startswith("---\n")
        assert "id: 42" in md
        assert "label: decision" in md

    def test_contains_title(self, sample_card):
        md = card_to_markdown(sample_card)
        assert "# decision #42" in md

    def test_contains_master_fields(self, sample_card):
        md = card_to_markdown(sample_card)
        assert "**Input:** Should we use request-response" in md
        assert "**Output:** Event-driven for throughput" in md

    def test_text_buffer_inlined(self, sample_card):
        md = card_to_markdown(sample_card)
        assert "## spec_text" in md
        assert "Chose event-driven architecture." in md

    def test_binary_buffer_linked(self, sample_card):
        md = card_to_markdown(sample_card)
        assert "## diagram" in md
        assert "![diagram](../assets/42-diagram.png)" in md

    def test_no_master_fields(self):
        card = Card(id=1, label="test", moment_id=1, buffers=[])
        md = card_to_markdown(card)
        assert "**Input:**" not in md
        assert "**Output:**" not in md

    def test_custom_assets_rel(self, sample_card):
        md = card_to_markdown(sample_card, assets_rel="./assets")
        assert "![diagram](./assets/42-diagram.png)" in md


class TestGenerateIndex:
    def test_empty(self):
        md = generate_index([])
        assert "Total cards: 0" in md

    def test_with_entries(self):
        entries = [
            VaultIndexEntry(
                card_id=1, label="decision", track="awareness",
                summary="Pick a database", strength=1.5, recall_count=2,
                created_at="2026-01-01", buffer_count=3,
            ),
            VaultIndexEntry(
                card_id=2, label="spec", track="execution",
                summary="API spec draft", strength=0.8, recall_count=0,
                created_at="2026-01-02", buffer_count=1,
            ),
        ]
        md = generate_index(entries)

        assert "Total cards: 2" in md
        assert "| 1 |" in md
        assert "Pick a database" in md
        assert "| 2 |" in md
        assert "API spec draft" in md

    def test_summary_truncated(self):
        entry = VaultIndexEntry(
            card_id=1, label="t", track="a",
            summary="x" * 100, strength=1.0, recall_count=0,
            created_at="", buffer_count=0,
        )
        md = generate_index([entry])
        # Summary column should be truncated to 60 chars
        lines = md.split("\n")
        data_line = [l for l in lines if "| 1 |" in l][0]
        assert len(data_line) < 200


# ---------------------------------------------------------------------------
# Buffer helpers
# ---------------------------------------------------------------------------

class TestBufferHelpers:
    def test_text_buffer(self):
        buf = Buffer(name="t", headers={"content_type": "text/plain"})
        assert _is_text_buffer(buf) is True

    def test_json_buffer(self):
        buf = Buffer(name="j", headers={"content_type": "application/json"})
        assert _is_text_buffer(buf) is True

    def test_binary_buffer(self):
        buf = Buffer(name="b", headers={"content_type": "image/png"})
        assert _is_text_buffer(buf) is False

    def test_default_is_text(self):
        buf = Buffer(name="d", headers={})
        assert _is_text_buffer(buf) is True

    def test_card_summary_from_master(self, sample_card):
        assert _card_summary(sample_card).startswith("Should we use")

    def test_card_summary_from_buffer(self):
        card = Card(
            id=1, label="test", moment_id=1,
            buffers=[Buffer(name="a", payload=b"Buffer content here")],
        )
        assert "Buffer content" in _card_summary(card)

    def test_card_summary_fallback(self):
        card = Card(id=99, label="empty", moment_id=1, buffers=[])
        assert _card_summary(card) == "empty-99"


# ---------------------------------------------------------------------------
# Filesystem Export
# ---------------------------------------------------------------------------

class TestExportCard:
    def test_creates_md_file(self, sample_card, sample_stats):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = os.path.join(tmpdir, "vault")
            path = export_card(sample_card, sample_stats, vault_dir=__import__("pathlib").Path(vault_dir))

            assert path.exists()
            assert path.suffix == ".md"
            assert path.parent.name == "decision"

            content = path.read_text()
            assert "id: 42" in content
            assert "# decision #42" in content

    def test_creates_binary_assets(self, sample_card):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = __import__("pathlib").Path(tmpdir) / "vault"
            export_card(sample_card, None, vault_dir)

            asset_path = vault_dir / "assets" / "42-diagram.png"
            assert asset_path.exists()
            assert asset_path.read_bytes() == b"\x89PNG\r\n\x1a\n"

    def test_text_only_card(self):
        card = Card(
            id=5, label="note", moment_id=1,
            master_input="A simple note",
            buffers=[Buffer(name="body", payload=b"Hello world")],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = __import__("pathlib").Path(tmpdir) / "vault"
            path = export_card(card, None, vault_dir)

            assert path.exists()
            assert "note" in str(path.parent)
            content = path.read_text()
            assert "Hello world" in content


# ---------------------------------------------------------------------------
# ABMemory.vault_index()
# ---------------------------------------------------------------------------

class TestVaultIndex:
    def test_returns_entries(self, memory):
        memory.store_card(
            label="decision", buffers=[Buffer(name="a", payload=b"test")],
            master_input="Pick a DB", owner_self="proj1",
        )
        memory.store_card(
            label="spec", buffers=[], master_input="API spec",
            owner_self="proj1",
        )

        entries = memory.vault_index()

        assert len(entries) == 2
        assert all(isinstance(e, VaultIndexEntry) for e in entries)

    def test_excludes_forgotten(self, memory):
        card = memory.store_card(
            label="old", buffers=[], master_input="Forgotten card",
        )
        memory.forget(card.id)

        entries = memory.vault_index()
        ids = [e.card_id for e in entries]
        assert card.id not in ids

    def test_filter_by_project(self, memory):
        memory.store_card(label="a", buffers=[], owner_self="proj-a")
        memory.store_card(label="b", buffers=[], owner_self="proj-b")

        entries = memory.vault_index(project="proj-a")
        assert len(entries) == 1
        assert entries[0].label == "a"

    def test_ordered_by_strength(self, memory):
        c1 = memory.store_card(label="weak", buffers=[])
        c2 = memory.store_card(label="strong", buffers=[])

        # Recall c2 multiple times to boost strength
        memory.recall_card(c2.id)
        memory.recall_card(c2.id)

        entries = memory.vault_index()
        assert entries[0].card_id == c2.id
        assert entries[0].strength > entries[1].strength

    def test_buffer_count(self, memory):
        memory.store_card(
            label="multi", buffers=[
                Buffer(name="a", payload=b"x"),
                Buffer(name="b", payload=b"y"),
                Buffer(name="c", payload=b"z"),
            ],
        )

        entries = memory.vault_index()
        assert entries[0].buffer_count == 3

    def test_limit(self, memory):
        for i in range(5):
            memory.store_card(label=f"card-{i}", buffers=[])

        entries = memory.vault_index(limit=3)
        assert len(entries) == 3

    def test_summary_from_master_input(self, memory):
        memory.store_card(
            label="test", buffers=[], master_input="Hello world summary",
        )

        entries = memory.vault_index()
        assert "Hello world summary" in entries[0].summary


# ---------------------------------------------------------------------------
# Full Vault Export
# ---------------------------------------------------------------------------

class TestExportVault:
    def test_full_export(self, memory):
        memory.store_card(
            label="decision", buffers=[Buffer(name="reason", payload=b"Because X")],
            master_input="Choose framework",
        )
        memory.store_card(
            label="spec", buffers=[Buffer(name="draft", payload=b"API v1")],
            master_input="Write spec",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = __import__("pathlib").Path(tmpdir) / "vault"
            result = export_vault(memory, vault_dir)

            assert result["exported"] == 2
            assert "decision" in result["labels"]
            assert "spec" in result["labels"]

            # Check index file
            index_path = vault_dir / "_index.md"
            assert index_path.exists()
            index_content = index_path.read_text()
            assert "Choose framework" in index_content
            assert "Write spec" in index_content

            # Check label directories
            assert (vault_dir / "decision").is_dir()
            assert (vault_dir / "spec").is_dir()

    def test_export_with_project_filter(self, memory):
        memory.store_card(label="a", buffers=[], owner_self="target")
        memory.store_card(label="b", buffers=[], owner_self="other")

        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = __import__("pathlib").Path(tmpdir) / "vault"
            result = export_vault(memory, vault_dir, project="target")

            assert result["exported"] == 1

    def test_export_empty_memory(self, memory):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_dir = __import__("pathlib").Path(tmpdir) / "vault"
            result = export_vault(memory, vault_dir)

            assert result["exported"] == 0
            assert (vault_dir / "_index.md").exists()
