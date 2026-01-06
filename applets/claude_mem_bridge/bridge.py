"""Claude-Mem Bridge - Connect claude-mem database to Tree-Web memory.

This module bridges the claude-mem SQLite database with Tree-Web memory
structures for advanced memory traversal and search.

Claude-mem schema:
- observations: type, title, subtitle, narrative, facts, concepts, project
- user_prompts: prompt_text, prompt_number
- session_summaries: investigated, learned, completed

Tree-Web structure:
- Moments: Points in time
- Cards: Memory units with buffers
- Links: Conceptual connections
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .buffers import BufferStore, BufferValue, normalize_observation


@dataclass
class ClaudeMemConfig:
    """Configuration for claude-mem connection."""
    db_path: str = "~/.claude-mem/claude-mem.db"
    auto_link: bool = True
    auto_link_min_words: int = 2
    import_embeddings: bool = True
    embedding_provider: str = "tfidf"
    embedding_model: str = "all-MiniLM-L6-v2"


@dataclass
class MemoryCard:
    """A memory card with properly normalized buffers."""
    card_id: int
    observation_id: int
    buffers: BufferStore
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None

    # Link tracking
    outgoing_links: List[int] = field(default_factory=list)
    incoming_links: List[int] = field(default_factory=list)

    # Neural properties
    recall_count: int = 0
    link_strength: Dict[int, float] = field(default_factory=dict)


class ClaudeMemBridge:
    """Bridge between claude-mem and Tree-Web memory."""

    def __init__(self, config: ClaudeMemConfig = None):
        self.config = config or ClaudeMemConfig()
        self.db_path = Path(self.config.db_path).expanduser()

        # Card storage
        self.cards: Dict[int, MemoryCard] = {}
        self._obs_to_card: Dict[int, int] = {}  # observation_id → card_id

        # Index structures
        self.word_index: Dict[str, Set[int]] = {}  # word → card_ids
        self.type_index: Dict[str, Set[int]] = {}  # type → card_ids
        self.project_index: Dict[str, Set[int]] = {}  # project → card_ids

        # Embedder (lazy loaded)
        self._embedder = None

    def connect(self) -> sqlite3.Connection:
        """Get database connection."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    @property
    def embedder(self):
        """Lazy-load embedder."""
        if self._embedder is None and self.config.import_embeddings:
            try:
                from ab.embeddings import CardEmbedder, CardEmbedderConfig
                embed_config = CardEmbedderConfig(
                    provider=self.config.embedding_provider,
                    model_name=self.config.embedding_model,
                    use_cache=True,
                )
                self._embedder = CardEmbedder(embed_config)
            except ImportError:
                pass
        return self._embedder

    # =========================================================================
    # Import
    # =========================================================================

    def import_all(
        self,
        project: str = None,
        obs_type: str = None,
        limit: int = None,
        since_days: int = None,
    ) -> Dict[str, int]:
        """Import observations from claude-mem.

        Args:
            project: Filter by project
            obs_type: Filter by type (bugfix, feature, etc.)
            limit: Max observations to import
            since_days: Only import from last N days

        Returns:
            Stats dict with counts
        """
        conn = self.connect()
        cursor = conn.cursor()

        # Build query
        sql = """
            SELECT id, sdk_session_id, project, type, title, subtitle,
                   narrative, facts, concepts, created_at, created_at_epoch
            FROM observations
            WHERE 1=1
        """
        params = []

        if project:
            sql += " AND project = ?"
            params.append(project)

        if obs_type:
            sql += " AND type = ?"
            params.append(obs_type)

        if since_days:
            cutoff = int((datetime.now().timestamp() - since_days * 86400) * 1000)
            sql += " AND created_at_epoch >= ?"
            params.append(cutoff)

        sql += " ORDER BY id DESC"

        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        cursor.execute(sql, params)

        imported = 0
        links_created = 0

        for row in cursor.fetchall():
            card = self._import_observation(dict(row))
            if card:
                imported += 1

                # Auto-link by shared words
                if self.config.auto_link:
                    links = self._auto_link_card(card.card_id)
                    links_created += links

        conn.close()

        return {
            "imported": imported,
            "links_created": links_created,
            "total_cards": len(self.cards),
        }

    def _import_observation(self, obs: Dict[str, Any]) -> Optional[MemoryCard]:
        """Import a single observation as a card."""
        obs_id = obs["id"]

        # Skip if already imported
        if obs_id in self._obs_to_card:
            return None

        # Parse JSON fields
        for field in ['facts', 'concepts']:
            if obs.get(field) and isinstance(obs[field], str):
                try:
                    obs[field] = json.loads(obs[field])
                except json.JSONDecodeError:
                    pass

        # Create buffer store
        buffers = BufferStore({
            "title": obs.get("title", ""),
            "subtitle": obs.get("subtitle", ""),
            "narrative": obs.get("narrative", ""),
            "type": obs.get("type", ""),
            "project": obs.get("project", ""),
            "facts": obs.get("facts", []),
            "concepts": obs.get("concepts", []),
            "observation_id": obs_id,
            "session_id": obs.get("sdk_session_id", ""),
            "created_at_epoch": obs.get("created_at_epoch", 0),
        })

        # Generate embedding
        embedding = None
        if self.embedder:
            embedding = self.embedder.embed_card(buffers.to_dict())

        # Parse timestamp
        created_at = None
        if obs.get("created_at"):
            try:
                created_at = datetime.fromisoformat(
                    obs["created_at"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        # Create card
        card_id = len(self.cards) + 1
        card = MemoryCard(
            card_id=card_id,
            observation_id=obs_id,
            buffers=buffers,
            embedding=embedding,
            created_at=created_at,
        )

        # Store
        self.cards[card_id] = card
        self._obs_to_card[obs_id] = card_id

        # Update indices
        self._index_card(card)

        return card

    def _index_card(self, card: MemoryCard):
        """Add card to search indices."""
        # Word index
        for word in card.buffers.all_words():
            if word not in self.word_index:
                self.word_index[word] = set()
            self.word_index[word].add(card.card_id)

        # Type index
        obs_type = card.buffers.get_text("type")
        if obs_type:
            if obs_type not in self.type_index:
                self.type_index[obs_type] = set()
            self.type_index[obs_type].add(card.card_id)

        # Project index
        project = card.buffers.get_text("project")
        if project:
            if project not in self.project_index:
                self.project_index[project] = set()
            self.project_index[project].add(card.card_id)

    def _auto_link_card(self, card_id: int) -> int:
        """Create links based on shared words."""
        card = self.cards.get(card_id)
        if not card:
            return 0

        card_words = card.buffers.all_words()
        if len(card_words) < self.config.auto_link_min_words:
            return 0

        # Find cards with shared words
        candidates: Dict[int, int] = {}  # card_id → shared_word_count

        for word in card_words:
            for other_id in self.word_index.get(word, []):
                if other_id != card_id:
                    candidates[other_id] = candidates.get(other_id, 0) + 1

        # Create links for cards with enough shared words
        links_created = 0
        for other_id, shared_count in candidates.items():
            if shared_count >= self.config.auto_link_min_words:
                # Bidirectional links
                if other_id not in card.outgoing_links:
                    card.outgoing_links.append(other_id)
                    links_created += 1

                other = self.cards.get(other_id)
                if other and card_id not in other.incoming_links:
                    other.incoming_links.append(card_id)

        return links_created

    # =========================================================================
    # Search
    # =========================================================================

    def keyword_search(
        self,
        query: str,
        project: str = None,
        obs_type: str = None,
        top_k: int = 10,
    ) -> List[Dict]:
        """Search by keyword matching."""
        query_words = BufferValue._extract_words(query.lower())
        if not query_words:
            return []

        # Score each card
        scores: Dict[int, float] = {}

        for word in query_words:
            for card_id in self.word_index.get(word, []):
                scores[card_id] = scores.get(card_id, 0) + 1

        # Normalize scores
        max_score = max(scores.values()) if scores else 1
        for card_id in scores:
            scores[card_id] /= max_score

        # Filter and format
        results = []
        for card_id, score in sorted(scores.items(), key=lambda x: -x[1])[:top_k]:
            card = self.cards[card_id]

            # Apply filters
            if project and card.buffers.get_text("project") != project:
                continue
            if obs_type and card.buffers.get_text("type") != obs_type:
                continue

            results.append({
                "card_id": card_id,
                "observation_id": card.observation_id,
                "title": card.buffers.get_text("title"),
                "type": card.buffers.get_text("type"),
                "project": card.buffers.get_text("project"),
                "score": score,
                "search_type": "keyword",
            })

        return results

    def semantic_search(
        self,
        query: str,
        project: str = None,
        obs_type: str = None,
        top_k: int = 10,
        threshold: float = 0.1,
    ) -> List[Dict]:
        """Search by semantic similarity."""
        if not self.embedder:
            return []

        query_embedding = self.embedder.embed_query(query)

        # Score each card
        scores = []
        for card_id, card in self.cards.items():
            if not card.embedding:
                continue

            # Apply filters
            if project and card.buffers.get_text("project") != project:
                continue
            if obs_type and card.buffers.get_text("type") != obs_type:
                continue

            # Cosine similarity
            sim = self._cosine_similarity(query_embedding, card.embedding)
            if sim >= threshold:
                scores.append((card_id, sim))

        # Sort and format
        scores.sort(key=lambda x: -x[1])

        results = []
        for card_id, sim in scores[:top_k]:
            card = self.cards[card_id]
            results.append({
                "card_id": card_id,
                "observation_id": card.observation_id,
                "title": card.buffers.get_text("title"),
                "type": card.buffers.get_text("type"),
                "project": card.buffers.get_text("project"),
                "score": sim,
                "search_type": "semantic",
            })

        return results

    def hybrid_search(
        self,
        query: str,
        project: str = None,
        obs_type: str = None,
        top_k: int = 10,
        semantic_weight: float = 0.5,
        keyword_weight: float = 0.3,
        recency_weight: float = 0.2,
    ) -> List[Dict]:
        """Combined semantic + keyword + recency search."""
        scores: Dict[int, Dict] = {}

        # Semantic scores
        if self.embedder and semantic_weight > 0:
            query_embedding = self.embedder.embed_query(query)
            for card_id, card in self.cards.items():
                if card.embedding:
                    sim = self._cosine_similarity(query_embedding, card.embedding)
                    scores[card_id] = {"semantic": sim, "keyword": 0, "recency": 0}

        # Keyword scores
        if keyword_weight > 0:
            query_words = BufferValue._extract_words(query.lower())
            for word in query_words:
                for card_id in self.word_index.get(word, []):
                    if card_id not in scores:
                        scores[card_id] = {"semantic": 0, "keyword": 0, "recency": 0}
                    scores[card_id]["keyword"] += 1

            # Normalize keyword scores
            max_kw = max((s["keyword"] for s in scores.values()), default=1) or 1
            for s in scores.values():
                s["keyword"] /= max_kw

        # Recency scores
        if recency_weight > 0 and scores:
            epochs = []
            for card_id in scores:
                card = self.cards[card_id]
                epoch = card.buffers.get_raw("created_at_epoch") or 0
                epochs.append((card_id, epoch))

            if epochs:
                min_e = min(e for _, e in epochs)
                max_e = max(e for _, e in epochs)
                range_e = max_e - min_e if max_e != min_e else 1

                for card_id, epoch in epochs:
                    scores[card_id]["recency"] = (epoch - min_e) / range_e

        # Combine scores
        results = []
        for card_id, s in scores.items():
            card = self.cards[card_id]

            # Apply filters
            if project and card.buffers.get_text("project") != project:
                continue
            if obs_type and card.buffers.get_text("type") != obs_type:
                continue

            final = (
                s["semantic"] * semantic_weight +
                s["keyword"] * keyword_weight +
                s["recency"] * recency_weight
            )

            results.append({
                "card_id": card_id,
                "observation_id": card.observation_id,
                "title": card.buffers.get_text("title"),
                "type": card.buffers.get_text("type"),
                "project": card.buffers.get_text("project"),
                "score": final,
                "semantic_score": s["semantic"],
                "keyword_score": s["keyword"],
                "recency_score": s["recency"],
                "search_type": "hybrid",
            })

        results.sort(key=lambda x: -x["score"])
        return results[:top_k]

    def find_similar(
        self,
        card_id: int,
        top_k: int = 10,
        threshold: float = 0.3,
    ) -> List[Dict]:
        """Find cards similar to a given card."""
        card = self.cards.get(card_id)
        if not card or not card.embedding:
            return []

        scores = []
        for other_id, other in self.cards.items():
            if other_id == card_id or not other.embedding:
                continue

            sim = self._cosine_similarity(card.embedding, other.embedding)
            if sim >= threshold:
                scores.append((other_id, sim))

        scores.sort(key=lambda x: -x[1])

        results = []
        for other_id, sim in scores[:top_k]:
            other = self.cards[other_id]
            results.append({
                "card_id": other_id,
                "observation_id": other.observation_id,
                "title": other.buffers.get_text("title"),
                "type": other.buffers.get_text("type"),
                "project": other.buffers.get_text("project"),
                "similarity": sim,
            })

        return results

    def find_related_by_words(
        self,
        card_id: int,
        min_shared_words: int = 3,
    ) -> List[Dict]:
        """Find cards with shared words (not embedding-based)."""
        card = self.cards.get(card_id)
        if not card:
            return []

        card_words = card.buffers.all_words()

        # Count shared words with each other card
        shared_counts: Dict[int, Set[str]] = {}

        for word in card_words:
            for other_id in self.word_index.get(word, []):
                if other_id != card_id:
                    if other_id not in shared_counts:
                        shared_counts[other_id] = set()
                    shared_counts[other_id].add(word)

        # Filter and format
        results = []
        for other_id, shared_words in shared_counts.items():
            if len(shared_words) >= min_shared_words:
                other = self.cards[other_id]
                results.append({
                    "card_id": other_id,
                    "observation_id": other.observation_id,
                    "title": other.buffers.get_text("title"),
                    "type": other.buffers.get_text("type"),
                    "project": other.buffers.get_text("project"),
                    "shared_words": list(shared_words),
                    "shared_count": len(shared_words),
                })

        results.sort(key=lambda x: -x["shared_count"])
        return results

    # =========================================================================
    # Query Types
    # =========================================================================

    def query_by_type(self, obs_type: str) -> List[MemoryCard]:
        """Get all cards of a specific type."""
        card_ids = self.type_index.get(obs_type, set())
        return [self.cards[cid] for cid in card_ids if cid in self.cards]

    def query_by_project(self, project: str) -> List[MemoryCard]:
        """Get all cards for a project."""
        card_ids = self.project_index.get(project, set())
        return [self.cards[cid] for cid in card_ids if cid in self.cards]

    def query_by_time_range(
        self,
        start: datetime = None,
        end: datetime = None,
    ) -> List[MemoryCard]:
        """Get cards within a time range."""
        results = []
        for card in self.cards.values():
            if card.created_at:
                if start and card.created_at < start:
                    continue
                if end and card.created_at > end:
                    continue
                results.append(card)

        results.sort(key=lambda c: c.created_at or datetime.min)
        return results

    def query_contains(
        self,
        text: str,
        buffer_name: str = None,
    ) -> List[MemoryCard]:
        """Find cards containing specific text."""
        results = []
        for card in self.cards.values():
            if card.buffers.contains(text, buffer_name):
                results.append(card)
        return results

    def query_regex(
        self,
        pattern: str,
        buffer_name: str = None,
    ) -> List[MemoryCard]:
        """Find cards matching a regex pattern."""
        results = []
        for card in self.cards.values():
            if card.buffers.matches_regex(pattern, buffer_name):
                results.append(card)
        return results

    # =========================================================================
    # Stats
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics."""
        type_counts = {}
        for t, ids in self.type_index.items():
            type_counts[t] = len(ids)

        project_counts = {}
        for p, ids in self.project_index.items():
            project_counts[p] = len(ids)

        return {
            "total_cards": len(self.cards),
            "unique_words": len(self.word_index),
            "types": type_counts,
            "projects": project_counts,
            "cards_with_embeddings": sum(
                1 for c in self.cards.values() if c.embedding
            ),
        }

    # =========================================================================
    # Utilities
    # =========================================================================

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity."""
        if len(a) != len(b):
            return 0.0

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)
