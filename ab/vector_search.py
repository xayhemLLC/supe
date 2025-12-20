"""Vector similarity search for AB memory.

This module implements basic semantic search using bag-of-words
vectors and cosine similarity. No external dependencies are required;
this is a simple implementation suitable for small to medium card
collections.

For production use with large collections, consider replacing the
embedding function with a proper embedding model (e.g., sentence
transformers) and using a vector database.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple

from .abdb import ABMemory
from .models import Card


def tokenize(text: str) -> List[str]:
    """Simple tokenizer: lowercase and split on non-alphanumeric."""
    text = text.lower()
    tokens = re.findall(r"\b[a-z0-9]+\b", text)
    return tokens


def embed_text(text: str, vocabulary: Optional[Set[str]] = None) -> Dict[str, float]:
    """Create a bag-of-words embedding for text.

    Args:
        text: The text to embed.
        vocabulary: Optional set of vocabulary terms to restrict to.

    Returns:
        Dict mapping terms to their normalized frequency.
    """
    tokens = tokenize(text)
    if not tokens:
        return {}

    counts = Counter(tokens)

    if vocabulary:
        counts = {k: v for k, v in counts.items() if k in vocabulary}

    # Normalize to unit vector
    total = sum(v * v for v in counts.values())
    if total == 0:
        return {}

    norm = math.sqrt(total)
    return {k: v / norm for k, v in counts.items()}


def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Calculate cosine similarity between two sparse vectors.

    Args:
        vec1: First vector (term -> weight).
        vec2: Second vector (term -> weight).

    Returns:
        Cosine similarity in range [0, 1].
    """
    if not vec1 or not vec2:
        return 0.0

    # Get all keys present in either vector
    all_keys = set(vec1.keys()) | set(vec2.keys())
    if not all_keys:
        return 0.0

    # Compute dot product
    dot_product = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in all_keys)
    
    # Compute magnitudes
    mag1 = math.sqrt(sum(v * v for v in vec1.values()))
    mag2 = math.sqrt(sum(v * v for v in vec2.values()))
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    return dot_product / (mag1 * mag2)


def extract_card_text(card: Card) -> str:
    """Extract all text content from a card's buffers.

    Decodes buffer payloads as UTF-8 and concatenates them.
    """
    texts = []
    texts.append(card.label)

    if card.master_input:
        texts.append(card.master_input)
    if card.master_output:
        texts.append(card.master_output)

    for buf in card.buffers:
        try:
            text = buf.payload.decode("utf-8", errors="ignore")
            texts.append(text)
        except Exception:
            pass

        # Also include header values
        for val in buf.headers.values():
            if isinstance(val, str):
                texts.append(val)

    return " ".join(texts)


def build_vocabulary(memory: ABMemory, min_freq: int = 2) -> Set[str]:
    """Build vocabulary from all cards in memory.

    Args:
        memory: The AB memory instance.
        min_freq: Minimum frequency for a term to be included.

    Returns:
        Set of vocabulary terms.
    """
    cur = memory.conn.cursor()
    cur.execute("SELECT id FROM cards")
    card_ids = [row["id"] for row in cur.fetchall()]

    term_counts: Counter = Counter()
    for card_id in card_ids:
        card = memory.get_card(card_id)
        text = extract_card_text(card)
        tokens = tokenize(text)
        term_counts.update(set(tokens))  # Count document frequency

    return {term for term, count in term_counts.items() if count >= min_freq}


def semantic_search(
    memory: ABMemory,
    query: str,
    top_k: int = 10,
    vocabulary: Optional[Set[str]] = None,
    label_filter: Optional[str] = None,
) -> List[Tuple[Card, float]]:
    """Search for cards semantically similar to a query.

    Uses bag-of-words cosine similarity for matching.

    Args:
        memory: The AB memory instance.
        query: The search query text.
        top_k: Maximum number of results to return.
        vocabulary: Optional vocabulary to restrict matching.
        label_filter: Optional filter by card label.

    Returns:
        List of (card, similarity_score) tuples, sorted by score descending.
    """
    query_vec = embed_text(query, vocabulary)
    if not query_vec:
        return []

    cur = memory.conn.cursor()
    if label_filter:
        cur.execute("SELECT id FROM cards WHERE label = ?", (label_filter,))
    else:
        cur.execute("SELECT id FROM cards")
    card_ids = [row["id"] for row in cur.fetchall()]

    results: List[Tuple[Card, float]] = []
    for card_id in card_ids:
        card = memory.get_card(card_id)
        card_text = extract_card_text(card)
        card_vec = embed_text(card_text, vocabulary)

        similarity = cosine_similarity(query_vec, card_vec)
        if similarity > 0:
            results.append((card, similarity))

    # Sort by similarity descending
    results.sort(key=lambda x: x[1], reverse=True)

    # Recall top results to update memory physics
    for card, _ in results[:top_k]:
        memory.recall_card(card.id)

    return results[:top_k]


def find_similar_cards(
    memory: ABMemory,
    source_card_id: int,
    top_k: int = 5,
    vocabulary: Optional[Set[str]] = None,
) -> List[Tuple[Card, float]]:
    """Find cards similar to a given card.

    Args:
        memory: The AB memory instance.
        source_card_id: The card to find similar cards to.
        top_k: Maximum number of results to return.
        vocabulary: Optional vocabulary to restrict matching.

    Returns:
        List of (card, similarity_score) tuples, excluding the source card.
    """
    source_card = memory.get_card(source_card_id)
    source_text = extract_card_text(source_card)
    source_vec = embed_text(source_text, vocabulary)

    if not source_vec:
        return []

    cur = memory.conn.cursor()
    cur.execute("SELECT id FROM cards WHERE id != ?", (source_card_id,))
    card_ids = [row["id"] for row in cur.fetchall()]

    results: List[Tuple[Card, float]] = []
    for card_id in card_ids:
        card = memory.get_card(card_id)
        card_text = extract_card_text(card)
        card_vec = embed_text(card_text, vocabulary)

        similarity = cosine_similarity(source_vec, card_vec)
        if similarity > 0:
            results.append((card, similarity))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]
