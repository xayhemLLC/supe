"""Tests for the new AB features.

This module tests the following features:
- Card stats and memory physics (strength, decay)
- Transform system (identity, len, lower_text, chains)
- Self agent system (think interface, subscribed buffers)
- Advanced search (RFS recall, semantic search)
"""

import os
import tempfile
import pytest

from ab import (
    ABMemory,
    Buffer,
    CardStats,
    apply_transform,
    transform_registry,
    decay_formula,
    apply_decay_to_all,
    Self,
    Proposal,
    PlannerSelf,
    ExecutorSelf,
    rfs_recall,
    attention_jump,
    semantic_search,
    find_similar_cards,
    cosine_similarity,
    embed_text,
)


@pytest.fixture
def memory():
    """Create a temporary in-memory database for testing."""
    # Use tempfile to create isolated test database
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    mem = ABMemory(db_path=path)
    yield mem
    mem.close()
    os.unlink(path)


# ---------------------------------------------------------------------------
# Card Stats Tests
# ---------------------------------------------------------------------------

class TestCardStats:
    """Tests for card_stats and memory physics."""

    def test_card_stats_created_on_get(self, memory):
        """Getting stats for a card initializes the stats if not present."""
        card = memory.store_card(label="test", buffers=[])
        stats = memory.get_card_stats(card.id)

        assert stats.card_id == card.id
        assert stats.strength == 1.0
        assert stats.recall_count == 0
        assert stats.last_recalled is None

    def test_recall_increases_strength(self, memory):
        """Recalling a card should increase its strength."""
        card = memory.store_card(label="test", buffers=[])

        # Initial strength is 1.0
        stats1 = memory.get_card_stats(card.id)
        assert stats1.strength == 1.0

        # Recall the card
        stats2 = memory.recall_card(card.id)

        # Strength should be: 1.0 * 0.9 + 1.0 = 1.9
        assert stats2.strength == pytest.approx(1.9, rel=0.01)
        assert stats2.recall_count == 1
        assert stats2.last_recalled is not None

    def test_multiple_recalls_accumulate(self, memory):
        """Multiple recalls should accumulate strength."""
        card = memory.store_card(label="test", buffers=[])

        # Recall 3 times
        for _ in range(3):
            memory.recall_card(card.id)

        stats = memory.get_card_stats(card.id)
        assert stats.recall_count == 3
        # Each recall: prev * 0.9 + 1.0
        # 1.0 -> 1.9 -> 2.71 -> 3.439
        assert stats.strength == pytest.approx(3.439, rel=0.01)

    def test_apply_decay_reduces_strength(self, memory):
        """apply_decay should reduce all card strengths."""
        card = memory.store_card(label="test", buffers=[])
        memory.recall_card(card.id)  # Set some strength

        stats_before = memory.get_card_stats(card.id)
        memory.apply_decay(decay_factor=0.5)
        stats_after = memory.get_card_stats(card.id)

        assert stats_after.strength == pytest.approx(stats_before.strength * 0.5, rel=0.01)

    def test_list_cards_by_strength(self, memory):
        """Cards should be returned ordered by strength."""
        card1 = memory.store_card(label="low", buffers=[])
        card2 = memory.store_card(label="high", buffers=[])

        # Recall card2 more times to increase its strength
        memory.recall_card(card2.id)
        memory.recall_card(card2.id)
        memory.recall_card(card2.id)

        top_cards = memory.list_cards_by_strength(limit=2)
        assert len(top_cards) == 2
        assert top_cards[0].card_id == card2.id
        assert top_cards[0].strength > top_cards[1].strength


# ---------------------------------------------------------------------------
# Transform Tests
# ---------------------------------------------------------------------------

class TestTransforms:
    """Tests for the transform system."""

    def test_identity_transform(self):
        """Identity transform should return payload unchanged."""
        payload = b"Hello World"
        result = apply_transform("identity", payload)
        assert result == payload

    def test_len_transform(self):
        """Len transform should return length as UTF-8 string."""
        payload = b"Hello"
        result = apply_transform("len", payload)
        assert result == b"5"

    def test_lower_text_transform(self):
        """lower_text should lowercase UTF-8 text."""
        payload = b"HELLO World"
        result = apply_transform("lower_text", payload)
        assert result == b"hello world"

    def test_upper_text_transform(self):
        """upper_text should uppercase UTF-8 text."""
        payload = b"hello world"
        result = apply_transform("upper_text", payload)
        assert result == b"HELLO WORLD"

    def test_strip_transform(self):
        """strip should remove whitespace from text."""
        payload = b"  hello world  "
        result = apply_transform("strip", payload)
        assert result == b"hello world"

    def test_transform_chain(self):
        """Chained transforms should be applied in order."""
        payload = b"  HELLO WORLD  "
        result = apply_transform("strip|lower_text", payload)
        assert result == b"hello world"

    def test_unknown_transform_raises(self):
        """Unknown transform name should raise ValueError."""
        with pytest.raises(ValueError):
            apply_transform("nonexistent", b"test")

    def test_empty_exe_returns_unchanged(self):
        """Empty or None exe should return payload unchanged."""
        payload = b"test"
        assert apply_transform("", payload) == payload
        assert apply_transform(None, payload) == payload


# ---------------------------------------------------------------------------
# Decay Tests
# ---------------------------------------------------------------------------

class TestDecay:
    """Tests for the decay module."""

    def test_decay_formula_basic(self):
        """Decay formula should reduce strength over time."""
        # Half-life of 168 hours (1 week)
        strength = decay_formula(10.0, hours_since_recall=168.0, half_life_hours=168.0)
        assert strength == pytest.approx(5.0, rel=0.01)

    def test_decay_formula_zero_time(self):
        """Zero time should return unchanged strength."""
        strength = decay_formula(10.0, hours_since_recall=0)
        assert strength == 10.0

    def test_decay_formula_double_halflife(self):
        """Double half-life should reduce to quarter strength."""
        strength = decay_formula(10.0, hours_since_recall=336.0, half_life_hours=168.0)
        assert strength == pytest.approx(2.5, rel=0.01)


# ---------------------------------------------------------------------------
# Self Agent Tests
# ---------------------------------------------------------------------------

class TestSelfAgent:
    """Tests for the Self agent system."""

    def test_planner_self_returns_proposal(self, memory):
        """PlannerSelf.think() should return a Proposal."""
        planner = PlannerSelf()
        card = memory.store_card(
            label="awareness",
            buffers=[Buffer(name="prompt", payload=b"Plan the task", headers={})]
        )

        proposal = planner.think(card)

        assert isinstance(proposal, Proposal)
        assert proposal.suggestion is not None
        assert isinstance(proposal.strength, float)

    def test_executor_self_detects_actions(self, memory):
        """ExecutorSelf should detect action keywords."""
        executor = ExecutorSelf()
        card = memory.store_card(
            label="awareness",
            buffers=[Buffer(name="prompt", payload=b"Please run the tests and fix bugs", headers={})]
        )

        proposal = executor.think(card)

        assert "action" in proposal.suggestion.lower() or "execute" in proposal.suggestion.lower()
        assert proposal.metadata["action_count"] > 0

    def test_self_subscribed_buffers_filtering(self, memory):
        """Self should only see subscribed buffers."""
        planner = PlannerSelf(subscribed_buffers=["prompt"])
        card = memory.store_card(
            label="awareness",
            buffers=[
                Buffer(name="prompt", payload=b"Plan this", headers={}),
                Buffer(name="files", payload=b"file1.py", headers={}),
                Buffer(name="context", payload=b"some context", headers={}),
            ]
        )

        filtered = planner.filter_buffers(card)

        assert len(filtered) == 1
        assert filtered[0].name == "prompt"

    def test_recursive_subself_call(self, memory):
        """A self should be able to call another self."""
        planner = PlannerSelf()
        executor = ExecutorSelf()
        planner.bind_memory(memory)

        card = memory.store_card(
            label="awareness",
            buffers=[Buffer(name="prompt", payload=b"Test input", headers={})]
        )

        # Planner calls executor
        executor_proposal = planner.call_subself(executor, card)

        assert isinstance(executor_proposal, Proposal)


# ---------------------------------------------------------------------------
# Advanced Search Tests
# ---------------------------------------------------------------------------

class TestAdvancedSearch:
    """Tests for RFS recall and semantic search."""

    def test_attention_jump_outgoing(self, memory):
        """attention_jump should find outgoing connections."""
        card1 = memory.store_card(label="a", buffers=[])
        card2 = memory.store_card(label="b", buffers=[])
        memory.create_connection(card1.id, card2.id, "references", strength=2.0)

        jumps = attention_jump(memory, card1.id, direction="outgoing")

        assert len(jumps) == 1
        assert jumps[0][0] == card2.id
        assert jumps[0][1] == "references"
        assert jumps[0][2] == 2.0

    def test_rfs_recall_multihop(self, memory):
        """rfs_recall should traverse multiple hops."""
        card1 = memory.store_card(label="a", buffers=[])
        card2 = memory.store_card(label="b", buffers=[])
        card3 = memory.store_card(label="c", buffers=[])

        memory.create_connection(card1.id, card2.id, "refs", strength=1.0)
        memory.create_connection(card2.id, card3.id, "refs", strength=1.0)

        results = rfs_recall(memory, card1.id, max_hops=3, strengthen_path=False)

        # Should find card2 and card3
        found_ids = [r[0].id for r in results]
        assert card2.id in found_ids
        assert card3.id in found_ids

    def test_semantic_search_basic(self, memory):
        """semantic_search should find cards by content similarity."""
        memory.store_card(
            label="doc",
            buffers=[Buffer(name="text", payload=b"Python programming language", headers={})]
        )
        memory.store_card(
            label="doc",
            buffers=[Buffer(name="text", payload=b"JavaScript web development", headers={})]
        )

        results = semantic_search(memory, "Python code programming")

        assert len(results) > 0
        # First result should be the Python card
        assert b"Python" in results[0][0].buffers[0].payload

    def test_cosine_similarity_identical(self):
        """Identical vectors should have similarity of 1.0."""
        vec = {"a": 0.5, "b": 0.5}
        similarity = cosine_similarity(vec, vec)
        assert similarity == pytest.approx(1.0, rel=0.01)

    def test_cosine_similarity_orthogonal(self):
        """Orthogonal vectors should have similarity of 0."""
        vec1 = {"a": 1.0}
        vec2 = {"b": 1.0}
        similarity = cosine_similarity(vec1, vec2)
        assert similarity == 0.0

    def test_embed_text_basic(self):
        """embed_text should create normalized bag-of-words."""
        embedding = embed_text("hello world hello")

        assert "hello" in embedding
        assert "world" in embedding
        # "hello" appears twice, should have higher weight
        assert embedding["hello"] > embedding["world"]


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------

class TestIntegration:
    """Integration tests combining multiple features."""

    def test_recall_uses_card_stats(self, memory):
        """recall_cards should use card_stats for ranking."""
        from ab.recall import recall_cards

        # Create cards with searchable content
        card1 = memory.store_card(
            label="doc",
            buffers=[Buffer(name="text", payload=b"Hello world test", headers={})]
        )
        card2 = memory.store_card(
            label="doc",
            buffers=[Buffer(name="text", payload=b"Hello universe test", headers={})]
        )

        # Boost card2's strength
        for _ in range(5):
            memory.recall_card(card2.id)

        # Search for "Hello" - card2 should rank higher due to strength
        results = recall_cards(memory, "Hello", top_k=2, use_card_stats=True)

        assert len(results) == 2
        assert results[0][0].id == card2.id  # Higher strength = higher rank

    def test_self_with_subscribed_buffers_in_db(self, memory):
        """Selves should store and retrieve subscribed_buffers from DB."""
        self_id = memory.create_self(
            name="test_planner",
            role="planner",
            subscribed_buffers=["prompt", "context"]
        )

        retrieved = memory.get_self(self_id)

        assert retrieved["subscribed_buffers"] == ["prompt", "context"]
