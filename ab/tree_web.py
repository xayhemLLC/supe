"""Tree-Web Card Structure for Temporal-Conceptual Memory Traversal.

This module implements a tree-web structure where:
- Moments form the temporal backbone (tree trunk)
- Cards branch off moments (tree branches)
- Cards link to other cards via concepts/relations (web connections)

Traversal strategies:
- Temporal: Forward/backward through moments
- Conceptual: Follow concept links between cards
- Causal: Follow dependency/evidence chains
- Semantic: Jump to similar cards via embeddings

Visual structure:

    TIME →

    M1 ─────────── M2 ─────────── M3 ─────────── M4
    │              │              │              │
    ├─ C1         ├─ C4         ├─ C7         ├─ C10
    │  ├─[concept]──────────────────┤            │
    │  └─[causes]─────┤              │            │
    ├─ C2         ├─ C5─[similar]───────────────┤
    │              │  └─[cites]────┤              │
    └─ C3         └─ C6         └─ C8         └─ C11
                                   └─ C9

    Legend:
    ─── temporal (moment sequence)
    ─┤  branches (cards from moment)
    [x] web links (conceptual/causal/semantic)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Iterator
from uuid import uuid4


class LinkType(Enum):
    """Types of web connections between cards."""
    CONCEPT = "concept"      # Shared concept/topic
    CAUSES = "causes"        # Causal relationship
    CITES = "cites"          # Citation/reference
    SIMILAR = "similar"      # Semantic similarity
    DEPENDS = "depends"      # Dependency
    CONTRADICTS = "contradicts"  # Conflicting information
    EXTENDS = "extends"      # Builds upon
    ANSWERS = "answers"      # Answer to question


class TraversalDirection(Enum):
    """Direction for temporal traversal."""
    FORWARD = "forward"
    BACKWARD = "backward"
    BOTH = "both"


@dataclass
class CardLink:
    """A web link between two cards."""
    source_id: int
    target_id: int
    link_type: LinkType
    strength: float = 1.0  # 0.0-1.0, higher = stronger connection
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TreeNode:
    """A moment in the tree with its branching cards."""
    moment_id: int
    timestamp: str
    card_ids: List[int] = field(default_factory=list)

    # Links to adjacent moments (temporal)
    prev_moment_id: Optional[int] = None
    next_moment_id: Optional[int] = None


@dataclass
class WebNode:
    """A card with its web connections."""
    card_id: int
    moment_id: int
    label: str

    # Buffers stored as dict for quick access
    buffers: Dict[str, Any] = field(default_factory=dict)

    # Web connections
    outgoing_links: List[CardLink] = field(default_factory=list)
    incoming_links: List[CardLink] = field(default_factory=list)

    # Embedding for semantic traversal
    embedding: Optional[List[float]] = None

    # Memory physics
    strength: float = 1.0
    recall_count: int = 0


class TreeWebMemory:
    """Tree-Web memory structure for temporal-conceptual traversal.

    The tree-web combines:
    1. Tree structure: Moments → Cards (temporal hierarchy)
    2. Web structure: Cards ↔ Cards (conceptual connections)

    This enables multi-dimensional memory traversal:
    - Walk through time (temporal)
    - Jump between related concepts (conceptual)
    - Follow cause-effect chains (causal)
    - Find similar memories (semantic)
    """

    def __init__(self, ab_memory=None):
        """Initialize tree-web memory.

        Args:
            ab_memory: Optional ABMemory instance for persistence.
        """
        self.ab_memory = ab_memory

        # In-memory indices (can be rebuilt from ABMemory)
        self.moments: Dict[int, TreeNode] = {}
        self.cards: Dict[int, WebNode] = {}
        self.links: List[CardLink] = []

        # Concept index for fast lookup
        self.concept_index: Dict[str, Set[int]] = {}  # concept → card_ids

        # Timeline (ordered moment IDs)
        self.timeline: List[int] = []

    # =========================================================================
    # Tree Operations (Temporal)
    # =========================================================================

    def add_moment(self, moment_id: int, timestamp: str) -> TreeNode:
        """Add a moment to the timeline."""
        node = TreeNode(moment_id=moment_id, timestamp=timestamp)

        # Link to previous moment
        if self.timeline:
            prev_id = self.timeline[-1]
            node.prev_moment_id = prev_id
            self.moments[prev_id].next_moment_id = moment_id

        self.moments[moment_id] = node
        self.timeline.append(moment_id)
        return node

    def attach_card(self, card_id: int, moment_id: int, label: str,
                    buffers: Dict[str, Any] = None,
                    embedding: List[float] = None) -> WebNode:
        """Attach a card to a moment (create a branch)."""
        if moment_id not in self.moments:
            raise ValueError(f"Moment {moment_id} not found")

        node = WebNode(
            card_id=card_id,
            moment_id=moment_id,
            label=label,
            buffers=buffers or {},
            embedding=embedding,
        )

        # Add to moment's branches
        self.moments[moment_id].card_ids.append(card_id)
        self.cards[card_id] = node

        # Index concepts
        concepts = buffers.get("concepts", []) if buffers else []
        for concept in concepts:
            if concept not in self.concept_index:
                self.concept_index[concept] = set()
            self.concept_index[concept].add(card_id)

        return node

    # =========================================================================
    # Web Operations (Conceptual)
    # =========================================================================

    def link_cards(self, source_id: int, target_id: int,
                   link_type: LinkType, strength: float = 1.0,
                   metadata: Dict[str, Any] = None) -> CardLink:
        """Create a web link between two cards."""
        if source_id not in self.cards or target_id not in self.cards:
            raise ValueError("Both cards must exist")

        link = CardLink(
            source_id=source_id,
            target_id=target_id,
            link_type=link_type,
            strength=strength,
            metadata=metadata or {},
        )

        self.cards[source_id].outgoing_links.append(link)
        self.cards[target_id].incoming_links.append(link)
        self.links.append(link)

        return link

    def auto_link_by_concepts(self, card_id: int, min_shared: int = 2) -> List[CardLink]:
        """Automatically create concept links to related cards."""
        if card_id not in self.cards:
            return []

        card = self.cards[card_id]
        concepts = card.buffers.get("concepts", [])

        # Find cards sharing concepts
        related_counts: Dict[int, int] = {}
        for concept in concepts:
            for other_id in self.concept_index.get(concept, set()):
                if other_id != card_id:
                    related_counts[other_id] = related_counts.get(other_id, 0) + 1

        # Create links for cards with enough shared concepts
        new_links = []
        for other_id, count in related_counts.items():
            if count >= min_shared:
                strength = min(count / len(concepts), 1.0)
                link = self.link_cards(
                    card_id, other_id,
                    LinkType.CONCEPT,
                    strength=strength,
                    metadata={"shared_concepts": count}
                )
                new_links.append(link)

        return new_links

    def auto_link_by_similarity(self, card_id: int, threshold: float = 0.8,
                                 max_links: int = 5) -> List[CardLink]:
        """Create semantic links to similar cards via embeddings."""
        if card_id not in self.cards:
            return []

        card = self.cards[card_id]
        if not card.embedding:
            return []

        # Compute similarities
        similarities = []
        for other_id, other_card in self.cards.items():
            if other_id != card_id and other_card.embedding:
                sim = self._cosine_similarity(card.embedding, other_card.embedding)
                if sim >= threshold:
                    similarities.append((other_id, sim))

        # Sort by similarity, take top N
        similarities.sort(key=lambda x: x[1], reverse=True)

        new_links = []
        for other_id, sim in similarities[:max_links]:
            # Check if link already exists
            existing = any(
                l.target_id == other_id and l.link_type == LinkType.SIMILAR
                for l in card.outgoing_links
            )
            if not existing:
                link = self.link_cards(
                    card_id, other_id,
                    LinkType.SIMILAR,
                    strength=sim,
                    metadata={"similarity": sim}
                )
                new_links.append(link)

        return new_links

    # =========================================================================
    # Traversal Strategies
    # =========================================================================

    def traverse_temporal(self, start_moment_id: int,
                          direction: TraversalDirection = TraversalDirection.FORWARD,
                          max_steps: int = 10,
                          include_cards: bool = True) -> Iterator[Dict]:
        """Traverse through time along the moment backbone.

        Yields:
            Dict with moment info and optionally its cards.
        """
        current_id = start_moment_id
        steps = 0
        visited = set()

        while current_id and steps < max_steps and current_id not in visited:
            visited.add(current_id)
            moment = self.moments.get(current_id)
            if not moment:
                break

            result = {
                "moment_id": moment.moment_id,
                "timestamp": moment.timestamp,
                "step": steps,
                "direction": direction.value,
            }

            if include_cards:
                result["cards"] = [
                    self.cards[cid] for cid in moment.card_ids
                    if cid in self.cards
                ]

            yield result

            steps += 1
            if direction == TraversalDirection.FORWARD:
                current_id = moment.next_moment_id
            elif direction == TraversalDirection.BACKWARD:
                current_id = moment.prev_moment_id
            else:  # BOTH - alternate
                if steps % 2 == 1:
                    current_id = moment.next_moment_id
                else:
                    current_id = moment.prev_moment_id

    def traverse_conceptual(self, start_card_id: int,
                            link_types: List[LinkType] = None,
                            max_depth: int = 3,
                            min_strength: float = 0.5) -> Iterator[Dict]:
        """Traverse the web following concept/causal links.

        Uses BFS to explore connected cards.

        Yields:
            Dict with card info, path, and depth.
        """
        if start_card_id not in self.cards:
            return

        link_types = link_types or list(LinkType)
        visited = {start_card_id}
        queue = [(start_card_id, 0, [start_card_id])]  # (card_id, depth, path)

        while queue:
            card_id, depth, path = queue.pop(0)
            card = self.cards[card_id]

            yield {
                "card_id": card_id,
                "card": card,
                "depth": depth,
                "path": path,
            }

            if depth >= max_depth:
                continue

            # Follow outgoing links
            for link in card.outgoing_links:
                if (link.link_type in link_types and
                    link.strength >= min_strength and
                    link.target_id not in visited):
                    visited.add(link.target_id)
                    queue.append((
                        link.target_id,
                        depth + 1,
                        path + [link.target_id]
                    ))

    def traverse_causal(self, card_id: int,
                        direction: str = "effects") -> Iterator[Dict]:
        """Traverse causal chains (causes → effects or effects → causes).

        Args:
            card_id: Starting card
            direction: "effects" (what this caused) or "causes" (what caused this)
        """
        causal_types = [LinkType.CAUSES, LinkType.DEPENDS, LinkType.EXTENDS]

        if direction == "effects":
            # Follow outgoing CAUSES links
            yield from self.traverse_conceptual(
                card_id,
                link_types=causal_types,
                max_depth=5
            )
        else:
            # Follow incoming CAUSES links (reverse traversal)
            visited = {card_id}
            queue = [(card_id, 0)]

            while queue:
                cid, depth = queue.pop(0)
                card = self.cards.get(cid)
                if not card:
                    continue

                yield {"card_id": cid, "card": card, "depth": depth}

                if depth >= 5:
                    continue

                for link in card.incoming_links:
                    if (link.link_type in causal_types and
                        link.source_id not in visited):
                        visited.add(link.source_id)
                        queue.append((link.source_id, depth + 1))

    def traverse_semantic(self, query_embedding: List[float],
                          top_k: int = 10,
                          threshold: float = 0.7) -> List[Dict]:
        """Find semantically similar cards via embedding search.

        Args:
            query_embedding: Query vector
            top_k: Max results
            threshold: Min similarity

        Returns:
            List of cards sorted by similarity.
        """
        results = []

        for card_id, card in self.cards.items():
            if card.embedding:
                sim = self._cosine_similarity(query_embedding, card.embedding)
                if sim >= threshold:
                    results.append({
                        "card_id": card_id,
                        "card": card,
                        "similarity": sim,
                    })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    # =========================================================================
    # Smart Search (Multi-Strategy)
    # =========================================================================

    def smart_search(self, query: str, query_embedding: List[float] = None,
                     filters: Dict[str, Any] = None,
                     strategy: str = "hybrid") -> List[Dict]:
        """Multi-strategy search combining all traversal methods.

        Args:
            query: Text query for keyword matching
            query_embedding: Optional embedding for semantic search
            filters: Buffer filters (type, project, concepts)
            strategy: "keyword", "semantic", or "hybrid"

        Returns:
            Scored and ranked results.
        """
        results: Dict[int, Dict] = {}

        # Layer 1: Buffer filtering
        candidates = self._filter_by_buffers(filters or {})

        # Layer 2: Keyword matching
        if strategy in ("keyword", "hybrid"):
            keywords = query.lower().split()
            for card_id in candidates:
                card = self.cards[card_id]
                score = self._keyword_score(card, keywords)
                if score > 0:
                    results[card_id] = {
                        "card_id": card_id,
                        "card": card,
                        "keyword_score": score,
                        "semantic_score": 0.0,
                    }

        # Layer 3: Semantic matching
        if strategy in ("semantic", "hybrid") and query_embedding:
            semantic_results = self.traverse_semantic(query_embedding)
            for res in semantic_results:
                card_id = res["card_id"]
                if card_id in candidates:
                    if card_id in results:
                        results[card_id]["semantic_score"] = res["similarity"]
                    else:
                        results[card_id] = {
                            "card_id": card_id,
                            "card": res["card"],
                            "keyword_score": 0.0,
                            "semantic_score": res["similarity"],
                        }

        # Layer 4: Compute final scores
        for card_id, res in results.items():
            card = res["card"]

            # Hybrid score formula
            keyword_weight = 0.3 if strategy == "hybrid" else 1.0
            semantic_weight = 0.5 if strategy == "hybrid" else 0.0
            strength_weight = 0.1
            recency_weight = 0.1

            res["final_score"] = (
                res["keyword_score"] * keyword_weight +
                res["semantic_score"] * semantic_weight +
                (card.strength / 10.0) * strength_weight +
                (card.recall_count / 100.0) * recency_weight
            )

        # Sort by final score
        sorted_results = sorted(
            results.values(),
            key=lambda x: x["final_score"],
            reverse=True
        )

        return sorted_results

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def _filter_by_buffers(self, filters: Dict[str, Any]) -> Set[int]:
        """Filter cards by buffer values."""
        if not filters:
            return set(self.cards.keys())

        candidates = set(self.cards.keys())

        for key, value in filters.items():
            matching = set()
            for card_id, card in self.cards.items():
                card_value = card.buffers.get(key)
                if card_value == value:
                    matching.add(card_id)
                elif isinstance(value, list) and card_value in value:
                    matching.add(card_id)
                elif isinstance(card_value, list) and value in card_value:
                    matching.add(card_id)
            candidates &= matching

        return candidates

    def _keyword_score(self, card: WebNode, keywords: List[str]) -> float:
        """Score card by keyword matches in buffers."""
        score = 0.0
        searchable = ["title", "narrative", "facts", "subtitle"]

        for key in searchable:
            value = card.buffers.get(key, "")
            if isinstance(value, list):
                value = " ".join(str(v) for v in value)
            value = str(value).lower()

            for kw in keywords:
                if kw in value:
                    # Title matches worth more
                    weight = 2.0 if key == "title" else 1.0
                    score += weight

        # Normalize by keyword count
        return score / len(keywords) if keywords else 0.0

    # =========================================================================
    # Persistence (ABMemory Integration)
    # =========================================================================

    def save_link(self, link: CardLink) -> None:
        """Save a card link to ABMemory."""
        if not self.ab_memory:
            return

        # Store as a special "link" card
        from .models import Card, Buffer

        link_card = Card(
            label="card_link",
            buffers=[
                Buffer(name="source_id", payload=str(link.source_id).encode()),
                Buffer(name="target_id", payload=str(link.target_id).encode()),
                Buffer(name="link_type", payload=link.link_type.value.encode()),
                Buffer(name="strength", payload=str(link.strength).encode()),
            ],
            track="execution",
        )
        self.ab_memory.store_card(link_card)

    def load_from_ab(self) -> None:
        """Rebuild tree-web indices from ABMemory."""
        if not self.ab_memory:
            return

        # Load all moments
        # ... implementation depends on ABMemory API
        pass

    # =========================================================================
    # Visualization
    # =========================================================================

    # =========================================================================
    # Flexible Filtering
    # =========================================================================

    def filter_by_time(
        self,
        start: datetime = None,
        end: datetime = None,
        include_cards: bool = True
    ) -> List[Dict]:
        """Filter moments/cards by timestamp range.

        Args:
            start: Start of time window (None = beginning of time)
            end: End of time window (None = now)
            include_cards: Include cards in results

        Returns:
            List of moments (with optional cards) in time range.

        Example:
            # Get memories from last 24 hours
            results = memory.filter_by_time(
                start=datetime.now() - timedelta(hours=24)
            )

            # Get memories from specific date
            results = memory.filter_by_time(
                start=datetime(2025, 12, 28),
                end=datetime(2025, 12, 29)
            )
        """
        results = []

        for moment_id in self.timeline:
            moment = self.moments[moment_id]

            # Parse moment timestamp
            try:
                moment_time = datetime.fromisoformat(moment.timestamp.replace('Z', '+00:00'))
                # Make timezone-naive for comparison
                if moment_time.tzinfo is not None:
                    moment_time = moment_time.replace(tzinfo=None)
            except ValueError:
                continue

            # Check time bounds (ensure both are naive)
            start_cmp = start.replace(tzinfo=None) if start and hasattr(start, 'tzinfo') and start.tzinfo else start
            end_cmp = end.replace(tzinfo=None) if end and hasattr(end, 'tzinfo') and end.tzinfo else end
            if start_cmp and moment_time < start_cmp:
                continue
            if end_cmp and moment_time > end_cmp:
                continue

            result = {
                "moment_id": moment_id,
                "timestamp": moment.timestamp,
                "datetime": moment_time,
            }

            if include_cards:
                result["cards"] = [
                    self.cards[cid] for cid in moment.card_ids
                    if cid in self.cards
                ]

            results.append(result)

        return results

    def filter_by_buffer(
        self,
        buffer_name: str,
        value: Any = None,
        contains: str = None,
        regex: str = None,
        exists: bool = None
    ) -> List[WebNode]:
        """Filter cards by buffer value with flexible matching.

        Args:
            buffer_name: Name of buffer to filter on (e.g., "type", "project", "title")
            value: Exact value match
            contains: Substring match (case-insensitive)
            regex: Regex pattern match
            exists: True = buffer must exist, False = must not exist

        Returns:
            List of matching cards.

        Examples:
            # All feature cards
            memory.filter_by_buffer("type", value="feature")

            # Cards with "ComfyUI" in title
            memory.filter_by_buffer("title", contains="ComfyUI")

            # Cards with "error" or "bug" in narrative
            memory.filter_by_buffer("narrative", regex=r"error|bug")

            # Cards that have an embedding
            memory.filter_by_buffer("embedding", exists=True)
        """
        import re as regex_module

        results = []

        for card_id, card in self.cards.items():
            buf_value = card.buffers.get(buffer_name)

            # Check existence
            if exists is not None:
                has_value = buf_value is not None and buf_value != ""
                if exists != has_value:
                    continue
                if exists and buf_value is None:
                    continue
                if not exists and buf_value is not None:
                    continue

            # Convert to string for text matching
            buf_str = str(buf_value).lower() if buf_value else ""

            # Exact value match
            if value is not None:
                if isinstance(buf_value, list):
                    if value not in buf_value:
                        continue
                elif buf_value != value:
                    continue

            # Contains match (case-insensitive)
            if contains is not None:
                if contains.lower() not in buf_str:
                    continue

            # Regex match
            if regex is not None:
                if not regex_module.search(regex, buf_str, regex_module.IGNORECASE):
                    continue

            results.append(card)

        return results

    def filter_compound(
        self,
        filters: List[Dict[str, Any]],
        operator: str = "AND"
    ) -> List[WebNode]:
        """Apply multiple filters with AND/OR logic.

        Args:
            filters: List of filter specs, each a dict with:
                - buffer: Buffer name
                - value/contains/regex/exists: Match criteria
            operator: "AND" (all must match) or "OR" (any can match)

        Returns:
            List of matching cards.

        Example:
            # ComfyUI features from December 2025
            memory.filter_compound([
                {"buffer": "project", "value": "ComfyUI"},
                {"buffer": "type", "value": "feature"},
                {"buffer": "timestamp", "contains": "2025-12"},
            ], operator="AND")
        """
        if not filters:
            return list(self.cards.values())

        result_sets = []

        for f in filters:
            buffer_name = f.get("buffer")
            if not buffer_name:
                continue

            matches = self.filter_by_buffer(
                buffer_name,
                value=f.get("value"),
                contains=f.get("contains"),
                regex=f.get("regex"),
                exists=f.get("exists"),
            )
            result_sets.append(set(c.card_id for c in matches))

        if not result_sets:
            return []

        if operator == "AND":
            final_ids = result_sets[0]
            for s in result_sets[1:]:
                final_ids &= s
        else:  # OR
            final_ids = set()
            for s in result_sets:
                final_ids |= s

        return [self.cards[cid] for cid in final_ids if cid in self.cards]

    # =========================================================================
    # Word-Based Auto-Linking
    # =========================================================================

    def build_word_index(self, buffers: List[str] = None) -> Dict[str, Set[int]]:
        """Build inverted index of words → card IDs.

        Args:
            buffers: Which buffers to index (default: title, narrative, facts)

        Returns:
            Dict mapping words to sets of card IDs containing them.
        """
        buffers = buffers or ["title", "narrative", "facts", "subtitle"]
        word_index: Dict[str, Set[int]] = {}

        # Stopwords to ignore
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "can", "this", "that", "these",
            "those", "it", "its", "they", "them", "their", "we", "our", "you",
            "your", "i", "my", "me", "he", "she", "his", "her", "what", "which",
            "who", "when", "where", "why", "how", "all", "each", "every", "both",
            "few", "more", "most", "some", "any", "no", "not", "only", "same",
        }

        for card_id, card in self.cards.items():
            words = set()

            for buf_name in buffers:
                buf_value = card.buffers.get(buf_name, "")

                if isinstance(buf_value, list):
                    text = " ".join(str(v) for v in buf_value)
                else:
                    text = str(buf_value)

                # Extract words (alphanumeric, min 3 chars)
                import re
                tokens = re.findall(r'[a-zA-Z0-9_-]{3,}', text.lower())
                words.update(t for t in tokens if t not in stopwords)

            # Add to index
            for word in words:
                if word not in word_index:
                    word_index[word] = set()
                word_index[word].add(card_id)

        return word_index

    def find_related_by_words(
        self,
        card_id: int,
        min_shared_words: int = 2,
        buffers: List[str] = None
    ) -> List[Dict]:
        """Find cards related by shared significant words.

        Args:
            card_id: Source card
            min_shared_words: Minimum words in common
            buffers: Which buffers to check

        Returns:
            List of related cards with shared word info.

        Example:
            # Find all cards related to ComfyUI workflow card
            related = memory.find_related_by_words(card_id=6828)
            # Returns cards containing "ComfyUI", "SDXL", "inpainting", etc.
        """
        if card_id not in self.cards:
            return []

        buffers = buffers or ["title", "narrative", "facts", "subtitle", "project"]

        # Get words from source card
        source_card = self.cards[card_id]
        source_words = set()

        import re
        stopwords = {"the", "a", "an", "and", "or", "is", "are", "was", "were", "be"}

        for buf_name in buffers:
            buf_value = source_card.buffers.get(buf_name, "")
            if isinstance(buf_value, list):
                text = " ".join(str(v) for v in buf_value)
            else:
                text = str(buf_value)

            tokens = re.findall(r'[a-zA-Z0-9_-]{3,}', text.lower())
            source_words.update(t for t in tokens if t not in stopwords)

        # Find cards with shared words
        related: Dict[int, Dict] = {}

        for other_id, other_card in self.cards.items():
            if other_id == card_id:
                continue

            other_words = set()
            for buf_name in buffers:
                buf_value = other_card.buffers.get(buf_name, "")
                if isinstance(buf_value, list):
                    text = " ".join(str(v) for v in buf_value)
                else:
                    text = str(buf_value)

                tokens = re.findall(r'[a-zA-Z0-9_-]{3,}', text.lower())
                other_words.update(t for t in tokens if t not in stopwords)

            # Find shared words
            shared = source_words & other_words

            if len(shared) >= min_shared_words:
                related[other_id] = {
                    "card_id": other_id,
                    "card": other_card,
                    "shared_words": list(shared),
                    "shared_count": len(shared),
                    "similarity": len(shared) / len(source_words | other_words),
                }

        # Sort by shared count
        return sorted(related.values(), key=lambda x: x["shared_count"], reverse=True)

    def auto_link_by_words(
        self,
        card_id: int,
        min_shared_words: int = 2,
        max_links: int = 10
    ) -> List[CardLink]:
        """Automatically create word-based links to related cards.

        Args:
            card_id: Source card
            min_shared_words: Minimum shared words to create link
            max_links: Maximum links to create

        Returns:
            List of newly created CardLinks.
        """
        related = self.find_related_by_words(card_id, min_shared_words)
        new_links = []

        for rel in related[:max_links]:
            other_id = rel["card_id"]

            # Check if link already exists
            card = self.cards[card_id]
            existing = any(
                l.target_id == other_id
                for l in card.outgoing_links
            )

            if not existing:
                link = self.link_cards(
                    card_id,
                    other_id,
                    LinkType.CONCEPT,
                    strength=rel["similarity"],
                    metadata={
                        "shared_words": rel["shared_words"],
                        "link_method": "word_match",
                    }
                )
                new_links.append(link)

        return new_links

    def search_by_keyword(
        self,
        keyword: str,
        buffers: List[str] = None,
        case_sensitive: bool = False
    ) -> List[WebNode]:
        """Search for cards containing a specific keyword.

        Args:
            keyword: Word to search for
            buffers: Which buffers to search (default: all text buffers)
            case_sensitive: Case-sensitive matching

        Returns:
            List of matching cards.

        Example:
            # Find all ComfyUI-related cards
            cards = memory.search_by_keyword("ComfyUI")
        """
        buffers = buffers or ["title", "narrative", "facts", "subtitle", "project"]
        results = []

        search_term = keyword if case_sensitive else keyword.lower()

        for card_id, card in self.cards.items():
            for buf_name in buffers:
                buf_value = card.buffers.get(buf_name, "")

                if isinstance(buf_value, list):
                    text = " ".join(str(v) for v in buf_value)
                else:
                    text = str(buf_value)

                compare_text = text if case_sensitive else text.lower()

                if search_term in compare_text:
                    results.append(card)
                    break  # Don't add same card twice

        return results

    # =========================================================================
    # Combined Search
    # =========================================================================

    def advanced_search(
        self,
        query: str = None,
        time_start: datetime = None,
        time_end: datetime = None,
        filters: List[Dict] = None,
        embedding: List[float] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Advanced multi-criteria search.

        Combines:
        - Time filtering
        - Buffer filtering
        - Keyword search
        - Semantic similarity

        Args:
            query: Text query for keyword matching
            time_start: Start of time window
            time_end: End of time window
            filters: Buffer filter specs
            embedding: Query embedding for semantic search
            limit: Max results

        Returns:
            Scored and ranked results.

        Example:
            # Find ComfyUI features from last week
            results = memory.advanced_search(
                query="inpainting workflow",
                time_start=datetime.now() - timedelta(days=7),
                filters=[{"buffer": "project", "value": "ComfyUI"}],
            )
        """
        # Start with all cards
        candidates = set(self.cards.keys())

        # Apply time filter
        if time_start or time_end:
            time_moments = self.filter_by_time(time_start, time_end, include_cards=True)
            time_card_ids = set()
            for m in time_moments:
                for card in m.get("cards", []):
                    time_card_ids.add(card.card_id)
            candidates &= time_card_ids

        # Apply buffer filters
        if filters:
            filtered = self.filter_compound(filters, operator="AND")
            filter_ids = set(c.card_id for c in filtered)
            candidates &= filter_ids

        # Score remaining candidates
        scored_results = []

        for card_id in candidates:
            card = self.cards[card_id]
            score = 0.0

            # Keyword score
            if query:
                keywords = query.lower().split()
                keyword_score = self._keyword_score(card, keywords)
                score += keyword_score * 0.4

            # Semantic score
            if embedding and card.embedding:
                semantic_score = self._cosine_similarity(embedding, card.embedding)
                score += semantic_score * 0.4

            # Recency boost (newer = higher)
            score += 0.1  # Base score

            # Strength boost
            score += (card.strength / 20.0) * 0.1

            scored_results.append({
                "card_id": card_id,
                "card": card,
                "score": score,
            })

        # Sort by score
        scored_results.sort(key=lambda x: x["score"], reverse=True)

        return scored_results[:limit]

    def to_ascii_tree(self, max_moments: int = 5) -> str:
        """Generate ASCII visualization of the tree-web."""
        lines = ["", "TREE-WEB MEMORY STRUCTURE", "=" * 50, ""]
        lines.append("TIME →")
        lines.append("")

        # Moment backbone
        moment_line = ""
        for i, mid in enumerate(self.timeline[:max_moments]):
            moment = self.moments[mid]
            moment_line += f"M{mid}"
            if i < len(self.timeline[:max_moments]) - 1:
                moment_line += " ─────── "
        lines.append(moment_line)

        # Cards branching from moments
        for i, mid in enumerate(self.timeline[:max_moments]):
            moment = self.moments[mid]
            prefix = "│" + " " * (10 * i)

            for j, cid in enumerate(moment.card_ids[:3]):
                card = self.cards.get(cid)
                if card:
                    branch = "├─" if j < len(moment.card_ids) - 1 else "└─"
                    label = card.label[:15]
                    lines.append(f"{prefix}{branch} C{cid}:{label}")

                    # Show links
                    for link in card.outgoing_links[:2]:
                        link_str = f"   └─[{link.link_type.value}]→ C{link.target_id}"
                        lines.append(f"{prefix}{link_str}")

        lines.append("")
        lines.append(f"Total: {len(self.moments)} moments, {len(self.cards)} cards, {len(self.links)} links")

        return "\n".join(lines)
