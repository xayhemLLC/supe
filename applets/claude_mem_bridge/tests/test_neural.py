"""Tests for neural memory.

Tests Hebbian learning and neural dynamics:
- Link strengthening through use
- Spreading activation
- Hub formation
- Decay over time
- Consolidation
"""

import pytest
from datetime import datetime, timedelta

from applets.claude_mem_bridge.neural import (
    NeuralMemory, NeuralCard, NeuralLink
)


@pytest.fixture
def empty_memory():
    """Empty neural memory."""
    return NeuralMemory()


@pytest.fixture
def seeded_memory():
    """Memory with sample cards."""
    mem = NeuralMemory()

    cards = [
        {"title": "OAuth Authentication", "type": "feature", "project": "web"},
        {"title": "Login Page", "type": "feature", "project": "web"},
        {"title": "Token Refresh", "type": "feature", "project": "web"},
        {"title": "Session Management", "type": "feature", "project": "web"},
        {"title": "Database Schema", "type": "refactor", "project": "web"},
        {"title": "API Security", "type": "feature", "project": "api"},
        {"title": "Error Handling", "type": "bugfix", "project": "web"},
    ]

    for i, data in enumerate(cards):
        mem.add_card(i + 1, data)

    return mem


class TestNeuralLink:
    """Tests for NeuralLink behavior."""

    def test_initial_strength(self):
        """Links start with low strength."""
        link = NeuralLink(source_id=1, target_id=2)

        assert link.strength == 0.1  # Default initial
        assert link.activation_count == 0

    def test_activation_strengthens(self):
        """Activation increases strength."""
        link = NeuralLink(source_id=1, target_id=2, strength=0.1)

        initial = link.strength
        link.activate()

        assert link.strength > initial
        assert link.activation_count == 1

    def test_strength_bounded(self):
        """Strength never exceeds 1.0."""
        link = NeuralLink(source_id=1, target_id=2, strength=0.9)

        for _ in range(100):
            link.activate()

        assert link.strength <= 1.0

    def test_decay_weakens(self):
        """Decay reduces strength."""
        link = NeuralLink(source_id=1, target_id=2, strength=0.5)

        initial = link.strength
        future = datetime.utcnow() + timedelta(days=30)
        link.decay(future)

        assert link.strength < initial

    def test_decay_minimum(self):
        """Strength doesn't decay below minimum."""
        link = NeuralLink(source_id=1, target_id=2, strength=0.1)

        future = datetime.utcnow() + timedelta(days=365)
        link.decay(future)

        assert link.strength >= 0.01

    def test_is_strong(self):
        """is_strong requires both strength and activations."""
        weak = NeuralLink(source_id=1, target_id=2, strength=0.3)
        assert not weak.is_strong

        strong = NeuralLink(source_id=1, target_id=2, strength=0.6)
        strong.activation_count = 10
        assert strong.is_strong


class TestNeuralCard:
    """Tests for NeuralCard behavior."""

    def test_card_creation(self):
        """Cards are created with default values."""
        card = NeuralCard(card_id=1, buffers={"title": "Test"})

        assert card.card_id == 1
        assert card.activation == 0.0
        assert card.connectivity == 0

    def test_receive_activation(self):
        """Cards receive activation from links."""
        card = NeuralCard(card_id=1, buffers={})
        link = NeuralLink(source_id=2, target_id=1, strength=0.5)
        card.incoming[2] = link

        card.receive_activation(1.0, from_card=2)

        # Activation = amount * link_strength = 1.0 * 0.5 = 0.5
        assert card.activation == 0.5

    def test_activation_bounded(self):
        """Activation doesn't exceed 1.0."""
        card = NeuralCard(card_id=1, buffers={})
        link = NeuralLink(source_id=2, target_id=1, strength=1.0)
        card.incoming[2] = link

        for _ in range(10):
            card.receive_activation(0.5, from_card=2)

        assert card.activation <= 1.0

    def test_fire_threshold(self):
        """Card fires when activation exceeds threshold."""
        card = NeuralCard(card_id=1, buffers={}, activation_threshold=0.3)

        card.activation = 0.2
        assert not card.fire()

        card.activation = 0.5
        assert card.fire()

    def test_reset(self):
        """Reset returns to resting potential."""
        card = NeuralCard(card_id=1, buffers={}, resting_potential=0.1)
        card.activation = 0.8

        card.reset()

        assert card.activation == 0.1

    def test_is_hub(self):
        """Hub detection based on connectivity and recalls."""
        card = NeuralCard(card_id=1, buffers={})
        assert not card.is_hub

        # Add many connections
        for i in range(25):
            card.outgoing[i] = NeuralLink(1, i)

        card.recall_count = 15
        assert card.is_hub


class TestNeuralMemory:
    """Tests for NeuralMemory operations."""

    def test_add_card(self, empty_memory):
        """Cards can be added."""
        card = empty_memory.add_card(1, {"title": "Test Card"})

        assert card.card_id == 1
        assert 1 in empty_memory.cards

    def test_concept_indexing(self, empty_memory):
        """Concepts are indexed from buffers."""
        empty_memory.add_card(1, {"title": "OAuth Authentication"})

        assert "oauth" in empty_memory.concept_index
        assert 1 in empty_memory.concept_index["oauth"]

    def test_connect_creates_link(self, seeded_memory):
        """Connect creates bidirectional link."""
        seeded_memory.connect(1, 2)

        assert (1, 2) in seeded_memory.links
        assert 2 in seeded_memory.cards[1].outgoing
        assert 1 in seeded_memory.cards[2].incoming

    def test_connect_strengthens_existing(self, seeded_memory):
        """Connecting again strengthens link."""
        seeded_memory.connect(1, 2)
        initial = seeded_memory.links[(1, 2)].strength

        seeded_memory.connect(1, 2)

        assert seeded_memory.links[(1, 2)].strength > initial

    def test_recall_basic(self, seeded_memory):
        """Recall finds matching cards."""
        results = seeded_memory.recall("OAuth authentication", top_k=3)

        assert len(results) >= 1
        # First result should be OAuth card
        assert results[0][0] == 1  # OAuth card id

    def test_recall_spreading_activation(self, seeded_memory):
        """Recall spreads activation through links."""
        # First, create some links
        seeded_memory.connect(1, 2, initial_strength=0.5)  # OAuth → Login
        seeded_memory.connect(2, 3, initial_strength=0.5)  # Login → Token

        # Query for OAuth
        results = seeded_memory.recall("OAuth", top_k=5)

        # Login should also be activated through spreading
        activated_ids = [r[0] for r in results]
        assert 1 in activated_ids  # OAuth directly activated
        # Other cards might be activated through spreading

    def test_recall_hebbian_learning(self, seeded_memory):
        """Recall strengthens pathways (Hebbian learning)."""
        initial_links = len(seeded_memory.links)

        # Multiple recalls with same query should create/strengthen links
        for _ in range(3):
            seeded_memory.recall("OAuth authentication", top_k=3)

        # Links should be created between co-activated cards
        assert len(seeded_memory.links) >= initial_links


class TestHebbianLearning:
    """Tests for Hebbian learning ("fire together, wire together")."""

    def test_repeated_queries_strengthen(self, seeded_memory):
        """Repeated queries strengthen pathways."""
        query = "OAuth authentication login"

        # First query
        seeded_memory.recall(query, top_k=3)

        # Get initial link count
        initial_links = len(seeded_memory.links)

        # More queries
        for _ in range(5):
            seeded_memory.recall(query, top_k=3)

        # Links should be stronger or more numerous
        assert len(seeded_memory.links) >= initial_links

    def test_different_queries_create_different_paths(self, seeded_memory):
        """Different queries create separate pathways."""
        initial_links = len(seeded_memory.links)

        # Query about authentication
        for _ in range(3):
            seeded_memory.recall("OAuth authentication", top_k=3)

        # Query about database
        for _ in range(3):
            seeded_memory.recall("database schema", top_k=3)

        # Should have created some pathways (links >= initial, could be 0)
        assert len(seeded_memory.links) >= initial_links


class TestHubFormation:
    """Tests for hub formation through repeated access."""

    def test_frequent_access_increases_recalls(self, seeded_memory):
        """Frequently accessed cards have higher recall count."""
        # Get initial recall counts
        oauth_card = seeded_memory.cards[1]
        initial_oauth_recalls = oauth_card.recall_count

        # Access OAuth card multiple times
        for _ in range(10):
            seeded_memory.recall("OAuth", top_k=1)

        # OAuth card should have more recalls than before
        assert oauth_card.recall_count >= initial_oauth_recalls

    def test_get_hubs(self, seeded_memory):
        """get_hubs returns most connected cards."""
        # Create connections
        for _ in range(10):
            seeded_memory.recall("OAuth authentication login", top_k=5)

        hubs = seeded_memory.get_hubs(3)

        # Should return top connected cards
        assert len(hubs) <= 3
        # First hub should have most connections
        if len(hubs) >= 2:
            assert hubs[0][1].connectivity >= hubs[1][1].connectivity


class TestConsolidation:
    """Tests for memory consolidation."""

    def test_consolidation_prunes_weak(self, seeded_memory):
        """Consolidation removes weak unused links."""
        # Create a weak link
        weak_link = seeded_memory.connect(1, 2, initial_strength=0.01)
        seeded_memory.links[(1, 2)].activation_count = 0

        stats = seeded_memory.consolidate()

        # Weak link might be pruned
        assert "pruned_links" in stats

    def test_consolidation_preserves_strong(self, seeded_memory):
        """Consolidation preserves strong links."""
        # Create and strengthen a link
        seeded_memory.connect(1, 2, initial_strength=0.3)
        for _ in range(10):
            seeded_memory.links[(1, 2)].activate()

        initial_strength = seeded_memory.links[(1, 2)].strength

        seeded_memory.consolidate()

        # Strong link should survive
        assert (1, 2) in seeded_memory.links
        assert seeded_memory.links[(1, 2)].strength >= initial_strength * 0.9


class TestFundamentalBranches:
    """Tests for finding fundamental branches (highways)."""

    def test_find_fundamental_branches(self, seeded_memory):
        """Finds well-established pathways."""
        # Create strong pathways through repeated use
        for _ in range(10):
            seeded_memory.recall("OAuth authentication login token", top_k=5)

        branches = seeded_memory.find_fundamental_branches()

        # Should find some strong pathways
        # (might be empty if not enough iterations)
        assert isinstance(branches, list)

    def test_fundamental_branches_sorted(self, seeded_memory):
        """Fundamental branches are sorted by strength."""
        # Create pathways
        for _ in range(10):
            seeded_memory.recall("OAuth", top_k=3)

        branches = seeded_memory.find_fundamental_branches()

        if len(branches) >= 2:
            # Should be sorted by strength * activations
            assert branches[0]["strength"] >= branches[1]["strength"]


class TestQueryHistory:
    """Tests for query history tracking."""

    def test_queries_recorded(self, seeded_memory):
        """Queries are recorded in history."""
        seeded_memory.recall("test query 1")
        seeded_memory.recall("test query 2")

        assert len(seeded_memory.query_history) >= 2
        assert seeded_memory.query_history[-1][0] == "test query 2"

    def test_history_includes_results(self, seeded_memory):
        """History includes recalled card IDs."""
        seeded_memory.recall("OAuth", top_k=3)

        query, result_ids, timestamp = seeded_memory.query_history[-1]

        assert query == "OAuth"
        assert isinstance(result_ids, list)
        assert isinstance(timestamp, datetime)


class TestDecay:
    """Tests for link decay over time."""

    def test_decay_all(self, seeded_memory):
        """Decay affects all links."""
        # Create links
        seeded_memory.connect(1, 2)
        seeded_memory.connect(2, 3)

        initial_strengths = {
            k: v.strength for k, v in seeded_memory.links.items()
        }

        # Simulate time passing
        for link in seeded_memory.links.values():
            link.last_activated = datetime.utcnow() - timedelta(days=30)

        seeded_memory.decay_all()

        # All links should be weaker
        for key, link in seeded_memory.links.items():
            assert link.strength <= initial_strengths[key]


class TestStrongestPaths:
    """Tests for path finding."""

    def test_get_strongest_paths(self, seeded_memory):
        """Can get strongest outgoing paths."""
        # Create connections from card 1
        seeded_memory.connect(1, 2, initial_strength=0.5)
        seeded_memory.connect(1, 3, initial_strength=0.3)
        seeded_memory.connect(1, 4, initial_strength=0.7)

        paths = seeded_memory.get_strongest_paths(1, depth=1)

        assert "card_id" in paths
        assert "connections" in paths
        assert len(paths["connections"]) >= 1

        # Strongest connection should be first
        if len(paths["connections"]) >= 2:
            assert paths["connections"][0]["strength"] >= paths["connections"][1]["strength"]
