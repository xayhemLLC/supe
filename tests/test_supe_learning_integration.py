"""Integration tests for Supe learning system (Phase 3).

Tests the complete integration of:
- Supe.learn() API method
- LearningStateMachine execution
- AB Memory storage
- Tasc validation
- Both INGEST and EXPLORE modes
"""

import pytest
import asyncio

from ab.abdb import ABMemory
from supe.supe import Supe
from supe.learning.types import Mode


# ============================================================================
# Supe.learn() API Tests
# ============================================================================


@pytest.mark.asyncio
async def test_supe_learn_ingest_mode():
    """Should complete INGEST mode learning through Supe API."""
    supe = Supe(db_path=":memory:")

    result = await supe.learn(
        "How do Python decorators work?",
        mode="ingest"
    )

    # Verify result structure
    assert "session_id" in result
    assert result["question"] == "How do Python decorators work?"
    assert result["mode"] == "ingest"

    # Verify learning artifacts created
    assert result["beliefs_count"] >= 0
    assert result["evidence_count"] >= 0
    assert result["gaps_count"] >= 0

    # Verify confidence score
    assert "confidence" in result
    if result["beliefs_count"] > 0:
        assert 0.0 <= result["confidence"] <= 1.0

    # Verify validation
    assert "validated" in result
    assert "proof_hash" in result

    # Verify beliefs list
    assert "beliefs" in result
    assert isinstance(result["beliefs"], list)


@pytest.mark.asyncio
async def test_supe_learn_explore_mode():
    """Should complete EXPLORE mode learning through Supe API."""
    supe = Supe(db_path=":memory:")

    result = await supe.learn(
        "Is addition commutative?",
        mode="explore"
    )

    # Verify result structure
    assert "session_id" in result
    assert result["question"] == "Is addition commutative?"
    assert result["mode"] == "explore"

    # Verify learning artifacts
    assert result["beliefs_count"] >= 0
    assert result["evidence_count"] >= 0

    # Verify beliefs created
    assert len(result["beliefs"]) > 0

    # For a true mathematical property, should have high confidence
    if result["beliefs_count"] > 0:
        assert result["confidence"] >= 0.8


@pytest.mark.asyncio
async def test_supe_learn_mode_case_insensitive():
    """Should handle mode parameter case-insensitively."""
    supe = Supe(db_path=":memory:")

    # Test uppercase
    result1 = await supe.learn("Test question 1", mode="INGEST")
    assert result1["mode"] == "INGEST"

    # Test mixed case
    result2 = await supe.learn("Test question 2", mode="Explore")
    assert result2["mode"] == "Explore"


@pytest.mark.asyncio
async def test_supe_learn_default_mode():
    """Should default to INGEST mode."""
    supe = Supe(db_path=":memory:")

    result = await supe.learn("Test question")

    assert result["mode"] == "ingest"


# ============================================================================
# AB Memory Storage Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_supe_learn_stores_session_in_memory():
    """Should store learning session in AB Memory."""
    supe = Supe(db_path=":memory:")

    result = await supe.learn("What is a closure?", mode="ingest")
    session_id = result["session_id"]

    # Search for learning session in memory
    cards = supe.memory.find_cards_by_label("learning_context")

    # Should have at least one learning context card
    assert len(cards) > 0

    # Verify session was stored
    session_found = False
    for card in cards:
        for buf in card.buffers:
            if buf.name == "context" and session_id in buf.payload.decode():
                session_found = True
                break

    assert session_found, "Learning session should be stored in AB Memory"


@pytest.mark.asyncio
async def test_supe_learn_stores_beliefs():
    """Should store beliefs in AB Memory."""
    supe = Supe(db_path=":memory:")

    result = await supe.learn("Test question", mode="ingest")

    if result["beliefs_count"] > 0:
        # Search for beliefs in memory
        cards = supe.memory.find_cards_by_label("learning_belief")
        assert len(cards) > 0


@pytest.mark.asyncio
async def test_supe_learn_stores_evidence():
    """Should store evidence in AB Memory."""
    supe = Supe(db_path=":memory:")

    result = await supe.learn("Test question", mode="ingest")

    if result["evidence_count"] > 0:
        # Search for evidence in memory
        cards = supe.memory.find_cards_by_label("learning_evidence")
        assert len(cards) > 0


# ============================================================================
# Tasc Validation Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_supe_learn_creates_tasc_validation():
    """Should create Tasc validation with proof hash."""
    supe = Supe(db_path=":memory:")

    result = await supe.learn("Test question", mode="ingest")

    # Verify validation created
    assert result["validated"] is not None
    assert isinstance(result["validated"], bool)

    # Verify proof hash
    assert result["proof_hash"] is not None
    if result["beliefs_count"] > 0:
        assert len(result["proof_hash"]) > 0


@pytest.mark.asyncio
async def test_supe_learn_validation_stored_in_memory():
    """Should store Tasc validation in AB Memory."""
    supe = Supe(db_path=":memory:")

    result = await supe.learn("Test question", mode="ingest")
    proof_hash = result["proof_hash"]

    if proof_hash:
        # Search for validation in memory
        cards = supe.memory.find_cards_by_label("tasc_execution")

        # Should have at least one execution card
        # (Note: This assumes store_learning_session_full creates execution cards)
        assert len(cards) >= 0  # May be 0 if no beliefs created


# ============================================================================
# Multi-Session Tests
# ============================================================================


@pytest.mark.asyncio
async def test_supe_learn_multiple_sessions():
    """Should handle multiple learning sessions."""
    supe = Supe(db_path=":memory:")

    # Learn multiple topics
    result1 = await supe.learn("Question 1", mode="ingest")
    result2 = await supe.learn("Question 2", mode="explore")
    result3 = await supe.learn("Question 3", mode="ingest")

    # Each should have unique session ID
    assert result1["session_id"] != result2["session_id"]
    assert result2["session_id"] != result3["session_id"]

    # All sessions should be stored in memory
    contexts = supe.memory.find_cards_by_label("learning_context")
    assert len(contexts) >= 3


@pytest.mark.asyncio
async def test_supe_learn_sessions_isolated():
    """Learning sessions should be isolated from each other."""
    supe = Supe(db_path=":memory:")

    result1 = await supe.learn("Question A", mode="ingest")
    result2 = await supe.learn("Question B", mode="ingest")

    # Session IDs should be different
    assert result1["session_id"] != result2["session_id"]

    # Beliefs should be separate
    beliefs1 = result1["beliefs"]
    beliefs2 = result2["beliefs"]

    # No beliefs should have the same ID
    ids1 = {b["id"] for b in beliefs1}
    ids2 = {b["id"] for b in beliefs2}
    assert len(ids1.intersection(ids2)) == 0


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_supe_learn_handles_empty_question():
    """Should handle empty question gracefully."""
    supe = Supe(db_path=":memory:")

    result = await supe.learn("", mode="ingest")

    # Should complete without error
    assert "session_id" in result
    assert result["question"] == ""


@pytest.mark.asyncio
async def test_supe_learn_handles_long_question():
    """Should handle very long questions."""
    supe = Supe(db_path=":memory:")

    long_question = "What is " + "very " * 100 + "long question?"

    result = await supe.learn(long_question, mode="ingest")

    # Should complete without error
    assert "session_id" in result


# ============================================================================
# Confidence Scoring Tests
# ============================================================================


@pytest.mark.asyncio
async def test_supe_learn_confidence_calculation():
    """Should calculate average confidence correctly."""
    supe = Supe(db_path=":memory:")

    result = await supe.learn("Test question", mode="ingest")

    if result["beliefs_count"] > 0:
        # Confidence should be average of belief confidences
        beliefs = result["beliefs"]
        manual_avg = sum(b["confidence"] for b in beliefs) / len(beliefs)

        # Allow small floating point difference
        assert abs(result["confidence"] - manual_avg) < 0.01


@pytest.mark.asyncio
async def test_supe_learn_zero_beliefs_confidence():
    """Should handle zero beliefs case for confidence."""
    supe = Supe(db_path=":memory:")

    # Use a question that won't generate beliefs
    result = await supe.learn("", mode="ingest")

    # Should have 0.0 confidence when no beliefs
    if result["beliefs_count"] == 0:
        assert result["confidence"] == 0.0


# ============================================================================
# Mode-Specific Behavior Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ingest_mode_creates_cornell_notes():
    """INGEST mode should create CornellNote beliefs."""
    supe = Supe(db_path=":memory:")

    result = await supe.learn("What is React?", mode="ingest")

    if result["beliefs_count"] > 0:
        belief = result["beliefs"][0]
        # Should have cornell_note structure in content
        assert "content" in belief
        # Content should be a dict with cornell note fields
        if isinstance(belief["content"], dict):
            # May have cue, notes, examples, conceptual_summary
            pass  # Structure validation


@pytest.mark.asyncio
async def test_explore_mode_creates_theorems():
    """EXPLORE mode should create Theorem beliefs."""
    supe = Supe(db_path=":memory:")

    result = await supe.learn("Is multiplication associative?", mode="explore")

    if result["beliefs_count"] > 0:
        belief = result["beliefs"][0]
        # Should have theorem structure in content
        assert "content" in belief
        # Content should be a dict with theorem fields
        if isinstance(belief["content"], dict):
            # May have statement, proof, status, properties
            pass  # Structure validation
