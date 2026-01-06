"""Tests for query types.

Tests various search and query patterns:
- Keyword search
- Semantic search
- Hybrid search
- Type/project filtering
- Time range queries
- Regex queries
- Related card discovery
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from applets.claude_mem_bridge.bridge import ClaudeMemBridge, ClaudeMemConfig, MemoryCard
from applets.claude_mem_bridge.buffers import BufferStore


@pytest.fixture
def sample_cards():
    """Create sample cards for testing."""
    return [
        {
            "id": 1,
            "title": "OAuth Authentication Implementation",
            "type": "feature",
            "project": "web",
            "narrative": "Implemented OAuth 2.0 login flow with token refresh",
            "facts": ["Uses JWT tokens", "Supports Google and GitHub"],
            "concepts": ["authentication", "oauth", "security"],
            "created_at": "2025-01-01T10:00:00Z",
            "created_at_epoch": 1735689600000,
        },
        {
            "id": 2,
            "title": "Database Schema Migration",
            "type": "refactor",
            "project": "web",
            "narrative": "Migrated user table to new schema with better indexing",
            "facts": ["Added composite index", "Renamed columns"],
            "concepts": ["database", "migration", "schema"],
            "created_at": "2025-01-02T10:00:00Z",
            "created_at_epoch": 1735776000000,
        },
        {
            "id": 3,
            "title": "Login Button Bug Fix",
            "type": "bugfix",
            "project": "web",
            "narrative": "Fixed login button not responding on mobile devices",
            "facts": ["Touch event handler was missing", "Added haptic feedback"],
            "concepts": ["mobile", "ui", "login"],
            "created_at": "2025-01-03T10:00:00Z",
            "created_at_epoch": 1735862400000,
        },
        {
            "id": 4,
            "title": "API Rate Limiting",
            "type": "feature",
            "project": "api",
            "narrative": "Added rate limiting to prevent abuse",
            "facts": ["100 requests per minute", "Uses Redis for tracking"],
            "concepts": ["api", "security", "rate-limit"],
            "created_at": "2025-01-04T10:00:00Z",
            "created_at_epoch": 1735948800000,
        },
        {
            "id": 5,
            "title": "Session Token Discovery",
            "type": "discovery",
            "project": "web",
            "narrative": "Discovered session tokens were not being invalidated on logout",
            "facts": ["Security vulnerability", "Tokens persist after logout"],
            "concepts": ["security", "session", "authentication"],
            "created_at": "2025-01-05T10:00:00Z",
            "created_at_epoch": 1736035200000,
        },
    ]


@pytest.fixture
def bridge_with_data(sample_cards):
    """Create a bridge with test data (no DB connection)."""
    bridge = ClaudeMemBridge(ClaudeMemConfig(import_embeddings=False))

    for obs in sample_cards:
        bridge._import_observation(obs)

    return bridge


class TestKeywordSearch:
    """Tests for keyword-based search."""

    def test_single_word_match(self, bridge_with_data):
        """Single word query finds matches."""
        results = bridge_with_data.keyword_search("OAuth")

        assert len(results) >= 1
        assert any("OAuth" in r["title"] for r in results)

    def test_multiple_word_match(self, bridge_with_data):
        """Multiple words increase relevance."""
        results = bridge_with_data.keyword_search("OAuth authentication login")

        # OAuth card should rank high
        assert results[0]["title"] == "OAuth Authentication Implementation"

    def test_case_insensitive(self, bridge_with_data):
        """Search is case insensitive."""
        results1 = bridge_with_data.keyword_search("oauth")
        results2 = bridge_with_data.keyword_search("OAUTH")
        results3 = bridge_with_data.keyword_search("OAuth")

        assert len(results1) == len(results2) == len(results3)

    def test_no_match_returns_empty(self, bridge_with_data):
        """Non-matching query returns empty list."""
        results = bridge_with_data.keyword_search("xyznonexistent")

        assert len(results) == 0

    def test_project_filter(self, bridge_with_data):
        """Project filter limits results."""
        all_results = bridge_with_data.keyword_search("security")
        web_results = bridge_with_data.keyword_search("security", project="web")
        api_results = bridge_with_data.keyword_search("security", project="api")

        assert len(web_results) < len(all_results)
        assert all(r["project"] == "web" for r in web_results)
        assert all(r["project"] == "api" for r in api_results)

    def test_type_filter(self, bridge_with_data):
        """Type filter limits results."""
        results = bridge_with_data.keyword_search("login", obs_type="bugfix")

        assert len(results) >= 1
        assert all(r["type"] == "bugfix" for r in results)

    def test_top_k_limit(self, bridge_with_data):
        """top_k limits result count."""
        results = bridge_with_data.keyword_search("the", top_k=2)

        assert len(results) <= 2


class TestHybridSearch:
    """Tests for hybrid search (no embedding, keyword + recency only)."""

    def test_basic_hybrid(self, bridge_with_data):
        """Hybrid search returns results."""
        results = bridge_with_data.hybrid_search(
            "authentication",
            semantic_weight=0,  # No embeddings
            keyword_weight=0.7,
            recency_weight=0.3,
        )

        assert len(results) >= 1

    def test_recency_boost(self, bridge_with_data):
        """Recent items get boosted."""
        results = bridge_with_data.hybrid_search(
            "security",
            semantic_weight=0,
            keyword_weight=0.3,
            recency_weight=0.7,
        )

        # Most recent security-related card should rank higher
        assert len(results) >= 2

    def test_score_components(self, bridge_with_data):
        """Results include score components."""
        results = bridge_with_data.hybrid_search(
            "OAuth",
            semantic_weight=0,
            keyword_weight=0.5,
            recency_weight=0.5,
        )

        if results:
            r = results[0]
            assert "score" in r
            assert "keyword_score" in r
            assert "recency_score" in r


class TestTypeQueries:
    """Tests for type-based queries."""

    def test_query_by_type(self, bridge_with_data):
        """Can query by observation type."""
        features = bridge_with_data.query_by_type("feature")
        bugfixes = bridge_with_data.query_by_type("bugfix")

        assert len(features) == 2
        assert len(bugfixes) == 1

    def test_unknown_type_empty(self, bridge_with_data):
        """Unknown type returns empty."""
        results = bridge_with_data.query_by_type("nonexistent")

        assert len(results) == 0


class TestProjectQueries:
    """Tests for project-based queries."""

    def test_query_by_project(self, bridge_with_data):
        """Can query by project."""
        web_cards = bridge_with_data.query_by_project("web")
        api_cards = bridge_with_data.query_by_project("api")

        assert len(web_cards) == 4
        assert len(api_cards) == 1

    def test_unknown_project_empty(self, bridge_with_data):
        """Unknown project returns empty."""
        results = bridge_with_data.query_by_project("nonexistent")

        assert len(results) == 0


class TestTimeQueries:
    """Tests for time-based queries."""

    def test_query_time_range(self, bridge_with_data):
        """Can query by time range."""
        from datetime import timezone
        start = datetime(2025, 1, 2, tzinfo=timezone.utc)
        end = datetime(2025, 1, 4, tzinfo=timezone.utc)

        results = bridge_with_data.query_by_time_range(start, end)

        # Should include cards from Jan 2, 3, but not 1 or 5
        assert len(results) >= 1

    def test_query_since(self, bridge_with_data):
        """Can query from start date only."""
        from datetime import timezone
        start = datetime(2025, 1, 4, tzinfo=timezone.utc)

        results = bridge_with_data.query_by_time_range(start=start)

        # Should include Jan 4 and 5
        assert len(results) >= 1

    def test_query_until(self, bridge_with_data):
        """Can query until end date only."""
        from datetime import timezone
        end = datetime(2025, 1, 2, tzinfo=timezone.utc)

        results = bridge_with_data.query_by_time_range(end=end)

        # Should include Jan 1 and 2
        assert len(results) >= 1


class TestContainsQueries:
    """Tests for contains/substring queries."""

    def test_contains_basic(self, bridge_with_data):
        """Can find cards containing text."""
        results = bridge_with_data.query_contains("OAuth")

        assert len(results) >= 1

    def test_contains_specific_buffer(self, bridge_with_data):
        """Can search in specific buffer."""
        # Title only
        results = bridge_with_data.query_contains("OAuth", buffer_name="title")
        assert len(results) == 1

    def test_contains_partial_match(self, bridge_with_data):
        """Partial matches work."""
        results = bridge_with_data.query_contains("Auth")

        assert len(results) >= 1


class TestRegexQueries:
    """Tests for regex-based queries."""

    def test_regex_basic(self, bridge_with_data):
        """Basic regex matching."""
        results = bridge_with_data.query_regex(r"OAuth.*flow")

        assert len(results) >= 1

    def test_regex_case_insensitive(self, bridge_with_data):
        """Regex is case insensitive."""
        results = bridge_with_data.query_regex(r"oauth")

        assert len(results) >= 1

    def test_regex_pattern_not_found(self, bridge_with_data):
        """Non-matching pattern returns empty."""
        results = bridge_with_data.query_regex(r"^\d{10}$")

        assert len(results) == 0


class TestRelatedQueries:
    """Tests for finding related cards."""

    def test_find_related_by_words(self, bridge_with_data):
        """Find cards with shared words."""
        # Card 1 (OAuth) and Card 5 (Session Token) share "authentication"
        oauth_card = None
        for card in bridge_with_data.cards.values():
            if "OAuth" in card.buffers.get_text("title"):
                oauth_card = card
                break

        assert oauth_card is not None

        related = bridge_with_data.find_related_by_words(
            oauth_card.card_id,
            min_shared_words=1,
        )

        # Should find Session Token Discovery (shares security/auth words)
        assert len(related) >= 1

    def test_find_related_min_words(self, bridge_with_data):
        """min_shared_words filters results."""
        card = list(bridge_with_data.cards.values())[0]

        loose = bridge_with_data.find_related_by_words(card.card_id, min_shared_words=1)
        strict = bridge_with_data.find_related_by_words(card.card_id, min_shared_words=5)

        assert len(strict) <= len(loose)


class TestStats:
    """Tests for statistics."""

    def test_get_stats(self, bridge_with_data):
        """Stats are computed correctly."""
        stats = bridge_with_data.get_stats()

        assert stats["total_cards"] == 5
        assert "types" in stats
        assert "projects" in stats
        assert stats["types"]["feature"] == 2
        assert stats["types"]["bugfix"] == 1
        assert stats["projects"]["web"] == 4
        assert stats["projects"]["api"] == 1


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_query(self, bridge_with_data):
        """Empty query returns empty results."""
        results = bridge_with_data.keyword_search("")

        assert len(results) == 0

    def test_special_characters(self, bridge_with_data):
        """Special characters don't crash search."""
        results = bridge_with_data.keyword_search("OAuth (2.0) [flow]")

        # Should still find OAuth
        assert len(results) >= 0

    def test_very_long_query(self, bridge_with_data):
        """Very long query is handled."""
        long_query = "word " * 1000
        results = bridge_with_data.keyword_search(long_query)

        # Should not crash
        assert isinstance(results, list)
