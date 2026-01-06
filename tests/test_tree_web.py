"""Tests for Tree-Web memory structure and comparators."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

# Import modules under test
import sys
sys.path.insert(0, str(__file__).rsplit("/tests", 1)[0])

from ab.tree_web import (
    TreeWebMemory, TreeNode, WebNode, CardLink, LinkType,
    TraversalDirection
)
from ab.comparators import (
    Filter, CompareOp, CompareResult,
    TextComparator, NumericComparator, TemporalComparator,
    CollectionComparator, ExistenceComparator, HashComparator,
    SemanticComparator, WordOverlapComparator, JSONPathComparator,
    AndComparator, OrComparator, NotComparator,
    extract_value, extract_text, extract_words
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def tree_web():
    """Create a TreeWebMemory with sample data."""
    tw = TreeWebMemory()

    # Add moments (timeline)
    tw.add_moment(1, "2025-12-28T10:00:00Z")
    tw.add_moment(2, "2025-12-28T11:00:00Z")
    tw.add_moment(3, "2025-12-28T12:00:00Z")

    # Add cards to moment 1
    tw.attach_card(
        card_id=101,
        moment_id=1,
        label="observation",
        buffers={
            "type": "feature",
            "title": "SDXL Inpainting Workflow Created",
            "project": "ComfyUI",
            "narrative": "Built complete ComfyUI workflow for SDXL inpainting",
            "concepts": ["how-it-works", "pattern"],
            "created_at_epoch": 1735380000000,
        }
    )
    tw.attach_card(
        card_id=102,
        moment_id=1,
        label="observation",
        buffers={
            "type": "discovery",
            "title": "Rate Limiting Implementation",
            "project": "API",
            "narrative": "Discovered rate limiting uses token bucket algorithm",
            "concepts": ["how-it-works"],
        }
    )

    # Add cards to moment 2
    tw.attach_card(
        card_id=201,
        moment_id=2,
        label="observation",
        buffers={
            "type": "bugfix",
            "title": "Fixed ComfyUI Memory Leak",
            "project": "ComfyUI",
            "narrative": "Fixed memory leak in image processing pipeline",
            "concepts": ["what-changed", "bugfix"],
        }
    )

    # Add cards to moment 3
    tw.attach_card(
        card_id=301,
        moment_id=3,
        label="observation",
        buffers={
            "type": "feature",
            "title": "SDXL ControlNet Integration",
            "project": "ComfyUI",
            "narrative": "Added ControlNet support for SDXL models",
            "concepts": ["how-it-works", "feature"],
        },
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5]  # Sample embedding
    )

    return tw


# =============================================================================
# Tree Structure Tests
# =============================================================================

class TestTreeStructure:
    """Test tree (temporal) structure operations."""

    def test_add_moment(self):
        """Test adding moments to timeline."""
        tw = TreeWebMemory()

        m1 = tw.add_moment(1, "2025-12-28T10:00:00Z")
        m2 = tw.add_moment(2, "2025-12-28T11:00:00Z")

        assert len(tw.moments) == 2
        assert len(tw.timeline) == 2
        assert tw.timeline == [1, 2]

        # Check linking
        assert m1.next_moment_id == 2
        assert m2.prev_moment_id == 1

    def test_attach_card(self, tree_web):
        """Test attaching cards to moments."""
        moment = tree_web.moments[1]

        assert len(moment.card_ids) == 2
        assert 101 in moment.card_ids
        assert 102 in moment.card_ids

        card = tree_web.cards[101]
        assert card.label == "observation"
        assert card.buffers["title"] == "SDXL Inpainting Workflow Created"

    def test_temporal_traversal_forward(self, tree_web):
        """Test forward temporal traversal."""
        results = list(tree_web.traverse_temporal(
            start_moment_id=1,
            direction=TraversalDirection.FORWARD,
            max_steps=10
        ))

        assert len(results) == 3
        assert results[0]["moment_id"] == 1
        assert results[1]["moment_id"] == 2
        assert results[2]["moment_id"] == 3

    def test_temporal_traversal_backward(self, tree_web):
        """Test backward temporal traversal."""
        results = list(tree_web.traverse_temporal(
            start_moment_id=3,
            direction=TraversalDirection.BACKWARD,
            max_steps=10
        ))

        assert len(results) == 3
        assert results[0]["moment_id"] == 3
        assert results[1]["moment_id"] == 2
        assert results[2]["moment_id"] == 1


# =============================================================================
# Web Structure Tests
# =============================================================================

class TestWebStructure:
    """Test web (conceptual) structure operations."""

    def test_link_cards(self, tree_web):
        """Test creating links between cards."""
        link = tree_web.link_cards(
            source_id=101,
            target_id=201,
            link_type=LinkType.CONCEPT,
            strength=0.8
        )

        assert link.source_id == 101
        assert link.target_id == 201
        assert link.link_type == LinkType.CONCEPT

        # Check card has link
        card = tree_web.cards[101]
        assert len(card.outgoing_links) == 1

        target = tree_web.cards[201]
        assert len(target.incoming_links) == 1

    def test_auto_link_by_concepts(self, tree_web):
        """Test automatic concept-based linking."""
        # Card 101 and 301 both have "how-it-works" concept
        links = tree_web.auto_link_by_concepts(101, min_shared=1)

        assert len(links) >= 1
        target_ids = [l.target_id for l in links]
        # Should link to cards with shared concepts
        assert any(tid in [102, 301] for tid in target_ids)

    def test_conceptual_traversal(self, tree_web):
        """Test BFS traversal through concept links."""
        # Create some links first
        tree_web.link_cards(101, 201, LinkType.CONCEPT)
        tree_web.link_cards(201, 301, LinkType.CONCEPT)

        results = list(tree_web.traverse_conceptual(
            start_card_id=101,
            max_depth=3
        ))

        assert len(results) >= 1
        assert results[0]["card_id"] == 101
        assert results[0]["depth"] == 0


# =============================================================================
# Filtering Tests
# =============================================================================

class TestFiltering:
    """Test flexible filtering capabilities."""

    def test_filter_by_time(self, tree_web):
        """Test time-based filtering."""
        start = datetime(2025, 12, 28, 10, 30)
        end = datetime(2025, 12, 28, 11, 30)

        results = tree_web.filter_by_time(start=start, end=end)

        # Should only get moment 2 (11:00)
        assert len(results) == 1
        assert results[0]["moment_id"] == 2

    def test_filter_by_buffer_value(self, tree_web):
        """Test exact value buffer filtering."""
        results = tree_web.filter_by_buffer("type", value="feature")

        assert len(results) == 2  # Cards 101 and 301
        types = [c.buffers["type"] for c in results]
        assert all(t == "feature" for t in types)

    def test_filter_by_buffer_contains(self, tree_web):
        """Test substring buffer filtering."""
        results = tree_web.filter_by_buffer("title", contains="ComfyUI")

        assert len(results) == 1
        assert results[0].buffers["title"] == "Fixed ComfyUI Memory Leak"

    def test_filter_by_buffer_regex(self, tree_web):
        """Test regex buffer filtering."""
        results = tree_web.filter_by_buffer("title", regex=r"SDXL.*")

        assert len(results) == 2  # 101 and 301
        for card in results:
            assert "SDXL" in card.buffers["title"]

    def test_filter_compound_and(self, tree_web):
        """Test compound AND filtering."""
        results = tree_web.filter_compound([
            {"buffer": "project", "value": "ComfyUI"},
            {"buffer": "type", "value": "feature"},
        ], operator="AND")

        assert len(results) == 2  # 101 and 301

    def test_filter_compound_or(self, tree_web):
        """Test compound OR filtering."""
        results = tree_web.filter_compound([
            {"buffer": "type", "value": "feature"},
            {"buffer": "type", "value": "bugfix"},
        ], operator="OR")

        assert len(results) == 3  # 101, 201, 301

    def test_search_by_keyword(self, tree_web):
        """Test keyword search."""
        results = tree_web.search_by_keyword("SDXL")

        assert len(results) == 2
        for card in results:
            assert "SDXL" in card.buffers["title"]


# =============================================================================
# Word-Based Linking Tests
# =============================================================================

class TestWordBasedLinking:
    """Test word-based auto-linking."""

    def test_find_related_by_words(self, tree_web):
        """Test finding related cards by shared words."""
        # Card 101 has: SDXL, Inpainting, Workflow, ComfyUI
        # Card 301 has: SDXL, ControlNet, ComfyUI
        # Should find 301 as related (shares SDXL, ComfyUI)

        related = tree_web.find_related_by_words(101, min_shared_words=2)

        assert len(related) >= 1
        # Find card 301 in results
        related_ids = [r["card_id"] for r in related]
        assert 301 in related_ids

        # Check shared words
        for r in related:
            if r["card_id"] == 301:
                assert "sdxl" in [w.lower() for w in r["shared_words"]]
                assert "comfyui" in [w.lower() for w in r["shared_words"]]

    def test_auto_link_by_words(self, tree_web):
        """Test automatic word-based linking."""
        links = tree_web.auto_link_by_words(101, min_shared_words=2)

        assert len(links) >= 1
        assert all(l.link_type == LinkType.CONCEPT for l in links)


# =============================================================================
# Comparator Tests
# =============================================================================

class TestComparators:
    """Test universal buffer comparators."""

    def test_text_comparator_eq(self):
        """Test text equality comparison."""
        comp = TextComparator(CompareOp.EQ, "hello")

        assert comp.compare("hello").matched
        assert not comp.compare("world").matched

    def test_text_comparator_contains(self):
        """Test text contains comparison."""
        comp = TextComparator(CompareOp.CONTAINS, "world")

        assert comp.compare("hello world").matched
        assert not comp.compare("hello").matched

    def test_text_comparator_regex(self):
        """Test regex comparison."""
        comp = TextComparator(CompareOp.REGEX, r"error|bug|fix")

        assert comp.compare("fixed a bug").matched
        assert comp.compare("error occurred").matched
        assert not comp.compare("all good").matched

    def test_numeric_comparator(self):
        """Test numeric comparisons."""
        assert NumericComparator(CompareOp.GT, 5).compare(10).matched
        assert NumericComparator(CompareOp.LT, 5).compare(3).matched
        assert NumericComparator(CompareOp.BETWEEN, 5, 10).compare(7).matched
        assert not NumericComparator(CompareOp.BETWEEN, 5, 10).compare(3).matched

    def test_temporal_comparator(self):
        """Test temporal comparisons."""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        comp = TemporalComparator(CompareOp.BETWEEN, yesterday, tomorrow)

        assert comp.compare(now).matched
        assert comp.compare(now.isoformat()).matched
        assert not comp.compare(now - timedelta(days=5)).matched

    def test_collection_comparator(self):
        """Test collection comparisons."""
        comp = CollectionComparator(CompareOp.IN, ["a", "b", "c"])

        assert comp.compare("a").matched
        assert comp.compare(["a", "d"]).matched  # overlaps
        assert not comp.compare("x").matched

    def test_existence_comparator(self):
        """Test existence comparisons."""
        exists_comp = ExistenceComparator(CompareOp.EXISTS)
        not_exists_comp = ExistenceComparator(CompareOp.NOT_EXISTS)

        assert exists_comp.compare("value").matched
        assert not exists_comp.compare(None).matched
        assert not exists_comp.compare("").matched

        assert not_exists_comp.compare(None).matched
        assert not not_exists_comp.compare("value").matched

    def test_word_overlap_comparator(self):
        """Test word overlap comparison."""
        comp = WordOverlapComparator({"sdxl", "comfyui", "inpainting"}, min_overlap=2)

        assert comp.compare("SDXL workflow for ComfyUI").matched
        assert not comp.compare("just some text").matched

        result = comp.compare("SDXL ControlNet ComfyUI support")
        assert result.matched
        assert result.metadata["shared_count"] >= 2

    def test_semantic_comparator(self):
        """Test semantic similarity comparison."""
        embedding1 = [0.1, 0.2, 0.3, 0.4, 0.5]
        embedding2 = [0.1, 0.2, 0.3, 0.4, 0.5]  # Identical
        embedding3 = [-0.1, -0.2, -0.3, -0.4, -0.5]  # Opposite

        comp = SemanticComparator(embedding1, threshold=0.9)

        assert comp.compare(embedding2).matched
        assert comp.compare(embedding2).score > 0.99
        assert not comp.compare(embedding3).matched

    def test_jsonpath_comparator(self):
        """Test JSONPath comparison."""
        data = {"status": "success", "data": {"count": 42}}

        comp1 = JSONPathComparator("$.status", CompareOp.EQ, "success")
        comp2 = JSONPathComparator("$.data.count", CompareOp.GT, 40)

        assert comp1.compare(data).matched
        assert comp2.compare(data).matched

    def test_composite_and(self):
        """Test AND composite comparator."""
        comp = AndComparator([
            TextComparator(CompareOp.CONTAINS, "error"),
            TextComparator(CompareOp.CONTAINS, "fix"),
        ])

        assert comp.compare("fixed the error").matched
        assert not comp.compare("just an error").matched

    def test_composite_or(self):
        """Test OR composite comparator."""
        comp = OrComparator([
            TextComparator(CompareOp.CONTAINS, "error"),
            TextComparator(CompareOp.CONTAINS, "warning"),
        ])

        assert comp.compare("error occurred").matched
        assert comp.compare("warning issued").matched
        assert not comp.compare("all good").matched

    def test_composite_not(self):
        """Test NOT composite comparator."""
        comp = NotComparator(TextComparator(CompareOp.CONTAINS, "error"))

        assert comp.compare("all good").matched
        assert not comp.compare("error here").matched


# =============================================================================
# Filter Builder Tests
# =============================================================================

class TestFilterBuilder:
    """Test fluent filter builder API."""

    def test_filter_eq(self):
        """Test filter eq builder."""
        name, comp = Filter("type").eq("feature").build()

        assert name == "type"
        assert comp.compare("feature").matched

    def test_filter_contains(self):
        """Test filter contains builder."""
        name, comp = Filter("title").contains("ComfyUI").build()

        assert name == "title"
        assert comp.compare("Fixed ComfyUI bug").matched

    def test_filter_chained(self):
        """Test chained filter conditions."""
        name, comp = Filter("value").gt(5).lt(15).build()

        assert name == "value"
        assert comp.compare("10").matched  # Between 5 and 15
        assert not comp.compare("3").matched
        assert not comp.compare("20").matched


# =============================================================================
# Value Extraction Tests
# =============================================================================

class TestValueExtraction:
    """Test value extraction utilities."""

    def test_extract_text_from_string(self):
        """Test text extraction from string."""
        assert extract_text("hello world") == "hello world"

    def test_extract_text_from_bytes(self):
        """Test text extraction from bytes."""
        assert extract_text(b"hello") == "hello"

    def test_extract_text_from_list(self):
        """Test text extraction from list."""
        result = extract_text(["hello", "world"])
        assert "hello" in result
        assert "world" in result

    def test_extract_text_from_dict(self):
        """Test text extraction from dict."""
        result = extract_text({"key": "value", "num": 42})
        assert "key" in result
        assert "value" in result
        assert "42" in result

    def test_extract_words(self):
        """Test word extraction."""
        words = extract_words("The quick brown fox jumps over the lazy dog")

        assert "quick" in words
        assert "brown" in words
        assert "fox" in words
        # Common stopwords removed
        assert "the" not in words
        # "over" is 4 chars and may pass filter - just check significant words are extracted
        assert len(words) >= 5  # At least 5 significant words


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple features."""

    def test_advanced_search(self, tree_web):
        """Test advanced multi-criteria search."""
        results = tree_web.advanced_search(
            query="SDXL workflow",
            filters=[{"buffer": "project", "value": "ComfyUI"}],
            limit=10
        )

        assert len(results) >= 1
        # Should find SDXL cards
        titles = [r["card"].buffers["title"] for r in results]
        assert any("SDXL" in t for t in titles)

    def test_ascii_visualization(self, tree_web):
        """Test ASCII tree visualization."""
        ascii_tree = tree_web.to_ascii_tree(max_moments=3)

        assert "TREE-WEB" in ascii_tree
        assert "M1" in ascii_tree
        assert "moments" in ascii_tree.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
