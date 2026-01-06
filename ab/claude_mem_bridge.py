"""Claude-Mem Integration Bridge for Tree-Web Memory.

This module bridges the claude-mem SQLite database with the Tree-Web
memory structure, enabling:

1. Import: Load observations/sessions from claude-mem into Tree-Web
2. Export: Save Tree-Web cards back to claude-mem
3. Sync: Keep both systems in sync
4. Search: Unified search across both systems

Claude-mem schema:
- sdk_sessions: Session tracking
- session_summaries: What was investigated/learned
- observations: Discoveries, features, bugfixes, etc.
- user_prompts: User input history (FTS5 indexed)

Tree-Web structure:
- Moments: Points in time (map to sessions/prompts)
- Cards: Memory units with buffers (map to observations)
- Links: Conceptual connections between cards
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .tree_web import TreeWebMemory, WebNode, TreeNode, CardLink, LinkType
from .comparators import (
    Filter, BufferComparator, TextComparator, CompareOp,
    extract_words, extract_text
)


@dataclass
class ClaudeMemConfig:
    """Configuration for claude-mem connection."""
    db_path: str = "~/.claude-mem/claude-mem.db"
    auto_link: bool = True           # Auto-create word-based links on import
    auto_link_min_words: int = 2     # Min shared words for auto-linking
    import_embeddings: bool = True   # Compute embeddings on import
    embedding_provider: str = "tfidf"  # "tfidf", "sentence-transformers", "openai"
    embedding_model: str = "all-MiniLM-L6-v2"  # For sentence-transformers
    sync_interval_sec: int = 60      # Auto-sync interval (0 = disabled)


class ClaudeMemBridge:
    """Bridge between claude-mem and Tree-Web memory."""

    def __init__(self, config: ClaudeMemConfig = None, tree_web: TreeWebMemory = None):
        """Initialize bridge.

        Args:
            config: Configuration options
            tree_web: Existing TreeWebMemory instance (creates new if None)
        """
        self.config = config or ClaudeMemConfig()
        self.tree_web = tree_web or TreeWebMemory()

        # Expand path
        self.db_path = Path(self.config.db_path).expanduser()

        # Mapping caches
        self._session_to_moment: Dict[str, int] = {}  # sdk_session_id → moment_id
        self._obs_to_card: Dict[int, int] = {}        # observation.id → card_id
        self._last_sync_epoch: int = 0

        # Initialize embedder if enabled
        self.embedder = None
        if self.config.import_embeddings:
            from .embeddings import CardEmbedder, CardEmbedderConfig
            embed_config = CardEmbedderConfig(
                provider=self.config.embedding_provider,
                model_name=self.config.embedding_model,
                use_cache=True,
            )
            self.embedder = CardEmbedder(embed_config)

    def connect(self) -> sqlite3.Connection:
        """Get database connection."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Claude-mem database not found: {self.db_path}")

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # Import: Claude-Mem → Tree-Web
    # =========================================================================

    def import_all(
        self,
        project: str = None,
        since_epoch: int = None,
        limit: int = None
    ) -> Dict[str, int]:
        """Import observations from claude-mem into Tree-Web.

        Args:
            project: Filter by project name
            since_epoch: Only import after this epoch (ms)
            limit: Max observations to import

        Returns:
            Dict with import stats.
        """
        conn = self.connect()
        cursor = conn.cursor()

        # Build query
        query = """
            SELECT
                o.id, o.sdk_session_id, o.project, o.type, o.title, o.subtitle,
                o.facts, o.narrative, o.concepts, o.files_read, o.files_modified,
                o.prompt_number, o.created_at, o.created_at_epoch, o.discovery_tokens
            FROM observations o
            WHERE 1=1
        """
        params = []

        if project:
            query += " AND o.project = ?"
            params.append(project)

        if since_epoch:
            query += " AND o.created_at_epoch > ?"
            params.append(since_epoch)

        query += " ORDER BY o.created_at_epoch ASC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        stats = {"imported": 0, "skipped": 0, "links_created": 0}

        for row in rows:
            obs_id = row["id"]

            # Skip if already imported
            if obs_id in self._obs_to_card:
                stats["skipped"] += 1
                continue

            # Ensure moment exists for this session
            moment_id = self._ensure_moment(row["sdk_session_id"], row["created_at"])

            # Create card from observation
            card = self._observation_to_card(dict(row), moment_id)

            # Auto-link if enabled
            if self.config.auto_link:
                links = self.tree_web.auto_link_by_words(
                    card.card_id,
                    min_shared_words=self.config.auto_link_min_words
                )
                stats["links_created"] += len(links)

            self._obs_to_card[obs_id] = card.card_id
            stats["imported"] += 1

        conn.close()
        return stats

    def import_observation(self, obs_id: int) -> Optional[WebNode]:
        """Import a single observation by ID.

        Args:
            obs_id: Observation ID from claude-mem

        Returns:
            Created WebNode or None if not found.
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM observations WHERE id = ?
        """, (obs_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        moment_id = self._ensure_moment(row["sdk_session_id"], row["created_at"])
        return self._observation_to_card(dict(row), moment_id)

    def _ensure_moment(self, sdk_session_id: str, timestamp: str) -> int:
        """Ensure a moment exists for the given session.

        Args:
            sdk_session_id: Session ID from claude-mem
            timestamp: ISO timestamp

        Returns:
            Moment ID in Tree-Web.
        """
        if sdk_session_id in self._session_to_moment:
            return self._session_to_moment[sdk_session_id]

        # Create new moment
        # Use hash of session_id as moment_id for consistency
        moment_id = abs(hash(sdk_session_id)) % (10 ** 9)

        node = self.tree_web.add_moment(moment_id, timestamp)
        self._session_to_moment[sdk_session_id] = moment_id

        return moment_id

    def _observation_to_card(self, obs: Dict, moment_id: int) -> WebNode:
        """Convert claude-mem observation to Tree-Web card.

        Args:
            obs: Observation row as dict
            moment_id: Parent moment ID

        Returns:
            Created WebNode.
        """
        # Parse JSON fields
        facts = self._parse_json(obs.get("facts", "[]"))
        concepts = self._parse_json(obs.get("concepts", "[]"))
        files_read = self._parse_json(obs.get("files_read", "[]"))
        files_modified = self._parse_json(obs.get("files_modified", "[]"))

        # Build buffers dict (matching claude-mem schema)
        buffers = {
            "type": obs.get("type", "discovery"),
            "title": obs.get("title", ""),
            "subtitle": obs.get("subtitle", ""),
            "facts": facts,
            "narrative": obs.get("narrative", ""),
            "concepts": concepts,
            "files_read": files_read,
            "files_modified": files_modified,
            "project": obs.get("project", ""),
            "prompt_number": obs.get("prompt_number"),
            "created_at": obs.get("created_at"),
            "created_at_epoch": obs.get("created_at_epoch"),
            "discovery_tokens": obs.get("discovery_tokens", 0),
            "sdk_session_id": obs.get("sdk_session_id"),
            "observation_id": obs.get("id"),  # Original ID for reference
        }

        # Compute embedding if enabled
        embedding = None
        if self.embedder:
            embedding = self.embedder.embed_card(buffers)

        # Create card
        card_id = obs.get("id")  # Use original observation ID as card ID
        card = self.tree_web.attach_card(
            card_id=card_id,
            moment_id=moment_id,
            label="observation",
            buffers=buffers,
            embedding=embedding,
        )

        return card

    def _parse_json(self, value: str) -> Any:
        """Safely parse JSON string."""
        if not value:
            return []
        try:
            return json.loads(value)
        except:
            return []

    # =========================================================================
    # Search: Unified Search Across Both Systems
    # =========================================================================

    def search(
        self,
        query: str = None,
        project: str = None,
        obs_type: str = None,
        time_start: datetime = None,
        time_end: datetime = None,
        concepts: List[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Search across claude-mem and Tree-Web.

        Args:
            query: Text search query
            project: Filter by project
            obs_type: Filter by observation type
            time_start: Start of time range
            time_end: End of time range
            concepts: Required concepts
            limit: Max results

        Returns:
            List of results with scores.
        """
        results = []

        # Search Tree-Web (in-memory, fast)
        tree_results = self._search_tree_web(
            query, project, obs_type, time_start, time_end, concepts, limit
        )
        results.extend(tree_results)

        # Search claude-mem directly (for unimported data)
        db_results = self._search_claude_mem(
            query, project, obs_type, time_start, time_end, concepts, limit
        )

        # Merge results (avoid duplicates)
        seen_ids = {r.get("observation_id") for r in results if r.get("observation_id")}
        for r in db_results:
            if r.get("observation_id") not in seen_ids:
                results.append(r)
                seen_ids.add(r.get("observation_id"))

        # Sort by score
        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return results[:limit]

    def _search_tree_web(
        self,
        query: str = None,
        project: str = None,
        obs_type: str = None,
        time_start: datetime = None,
        time_end: datetime = None,
        concepts: List[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Search Tree-Web memory."""
        filters = []

        if project:
            filters.append({"buffer": "project", "value": project})

        if obs_type:
            filters.append({"buffer": "type", "value": obs_type})

        results = self.tree_web.advanced_search(
            query=query,
            time_start=time_start,
            time_end=time_end,
            filters=filters if filters else None,
            limit=limit
        )

        # Convert to common format
        formatted = []
        for r in results:
            card = r["card"]
            formatted.append({
                "source": "tree_web",
                "card_id": r["card_id"],
                "observation_id": card.buffers.get("observation_id"),
                "type": card.buffers.get("type"),
                "title": card.buffers.get("title"),
                "subtitle": card.buffers.get("subtitle"),
                "project": card.buffers.get("project"),
                "score": r["score"],
                "card": card,
            })

        return formatted

    def _search_claude_mem(
        self,
        query: str = None,
        project: str = None,
        obs_type: str = None,
        time_start: datetime = None,
        time_end: datetime = None,
        concepts: List[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Search claude-mem database directly."""
        conn = self.connect()
        cursor = conn.cursor()

        # Build query
        sql = """
            SELECT id, type, title, subtitle, project, narrative, concepts,
                   created_at, created_at_epoch
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

        if time_start:
            sql += " AND created_at_epoch >= ?"
            params.append(int(time_start.timestamp() * 1000))

        if time_end:
            sql += " AND created_at_epoch <= ?"
            params.append(int(time_end.timestamp() * 1000))

        if query:
            # Use LIKE for basic search (FTS would be better but requires different table)
            sql += " AND (title LIKE ? OR narrative LIKE ? OR subtitle LIKE ?)"
            like_query = f"%{query}%"
            params.extend([like_query, like_query, like_query])

        sql += " ORDER BY created_at_epoch DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            # Score based on query match quality
            score = 0.5  # Base score
            if query:
                title = row["title"] or ""
                if query.lower() in title.lower():
                    score += 0.3
                narrative = row["narrative"] or ""
                if query.lower() in narrative.lower():
                    score += 0.2

            results.append({
                "source": "claude_mem",
                "observation_id": row["id"],
                "type": row["type"],
                "title": row["title"],
                "subtitle": row["subtitle"],
                "project": row["project"],
                "score": score,
            })

        return results

    # =========================================================================
    # Find Related
    # =========================================================================

    def find_related(
        self,
        card_id: int = None,
        observation_id: int = None,
        min_shared_words: int = 2,
        limit: int = 10
    ) -> List[Dict]:
        """Find cards/observations related by shared words.

        Args:
            card_id: Tree-Web card ID
            observation_id: Claude-mem observation ID
            min_shared_words: Minimum shared words
            limit: Max results

        Returns:
            List of related items with shared word info.
        """
        # Get source card
        if observation_id and observation_id not in self._obs_to_card:
            # Import the observation first
            self.import_observation(observation_id)
            card_id = self._obs_to_card.get(observation_id)

        if card_id is None:
            return []

        # Use Tree-Web word matching
        related = self.tree_web.find_related_by_words(
            card_id,
            min_shared_words=min_shared_words
        )

        # Format results
        results = []
        for r in related[:limit]:
            card = r["card"]
            results.append({
                "card_id": r["card_id"],
                "observation_id": card.buffers.get("observation_id"),
                "title": card.buffers.get("title"),
                "type": card.buffers.get("type"),
                "project": card.buffers.get("project"),
                "shared_words": r["shared_words"],
                "shared_count": r["shared_count"],
                "similarity": r["similarity"],
            })

        return results

    # =========================================================================
    # Traversal
    # =========================================================================

    def get_session_timeline(self, sdk_session_id: str) -> List[Dict]:
        """Get all observations from a session in order.

        Args:
            sdk_session_id: Session ID

        Returns:
            List of observations in temporal order.
        """
        moment_id = self._session_to_moment.get(sdk_session_id)
        if moment_id is None:
            # Not imported - fetch from DB
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM observations
                WHERE sdk_session_id = ?
                ORDER BY prompt_number ASC, created_at_epoch ASC
            """, (sdk_session_id,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]

        # Get from Tree-Web
        moment = self.tree_web.moments.get(moment_id)
        if not moment:
            return []

        results = []
        for card_id in moment.card_ids:
            card = self.tree_web.cards.get(card_id)
            if card:
                results.append({
                    "card_id": card_id,
                    "observation_id": card.buffers.get("observation_id"),
                    "title": card.buffers.get("title"),
                    "type": card.buffers.get("type"),
                    "prompt_number": card.buffers.get("prompt_number"),
                })

        # Sort by prompt_number
        results.sort(key=lambda x: x.get("prompt_number") or 0)
        return results

    def traverse_concept_web(
        self,
        start_card_id: int,
        max_depth: int = 3
    ) -> List[Dict]:
        """Traverse concept links from a starting card.

        Args:
            start_card_id: Starting card ID
            max_depth: Max traversal depth

        Returns:
            List of visited cards with depth info.
        """
        visited = []

        for item in self.tree_web.traverse_conceptual(
            start_card_id,
            link_types=[LinkType.CONCEPT, LinkType.SIMILAR],
            max_depth=max_depth
        ):
            card = item["card"]
            visited.append({
                "card_id": item["card_id"],
                "depth": item["depth"],
                "path": item["path"],
                "title": card.buffers.get("title"),
                "type": card.buffers.get("type"),
                "project": card.buffers.get("project"),
            })

        return visited

    # =========================================================================
    # Semantic Search
    # =========================================================================

    def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.3,
        project: str = None,
        obs_type: str = None,
    ) -> List[Dict]:
        """Search cards by semantic similarity.

        Args:
            query: Natural language query
            top_k: Max results
            threshold: Min similarity threshold (0-1)
            project: Optional project filter
            obs_type: Optional observation type filter

        Returns:
            List of results with similarity scores.

        Example:
            # Find cards semantically similar to a concept
            results = bridge.semantic_search("error handling and validation")
            results = bridge.semantic_search("ComfyUI image processing", project="ComfyUI")
        """
        if not self.embedder:
            raise ValueError("Embeddings not enabled. Set import_embeddings=True in config.")

        # Embed query
        query_embedding = self.embedder.embed_query(query)

        # Collect card embeddings
        card_embeddings = {}
        for card_id, card in self.tree_web.cards.items():
            # Apply filters
            if project and card.buffers.get("project") != project:
                continue
            if obs_type and card.buffers.get("type") != obs_type:
                continue

            if card.embedding:
                card_embeddings[card_id] = card.embedding

        if not card_embeddings:
            return []

        # Search
        from .embeddings import semantic_search
        results = semantic_search(
            query_embedding,
            card_embeddings,
            top_k=top_k,
            threshold=threshold
        )

        # Format results
        formatted = []
        for card_id, similarity in results:
            card = self.tree_web.cards[card_id]
            formatted.append({
                "card_id": card_id,
                "observation_id": card.buffers.get("observation_id"),
                "title": card.buffers.get("title"),
                "subtitle": card.buffers.get("subtitle"),
                "type": card.buffers.get("type"),
                "project": card.buffers.get("project"),
                "similarity": similarity,
                "card": card,
            })

        return formatted

    def find_similar_cards(
        self,
        card_id: int,
        top_k: int = 10,
        threshold: float = 0.5
    ) -> List[Dict]:
        """Find cards semantically similar to a given card.

        Args:
            card_id: Source card ID
            top_k: Max results
            threshold: Min similarity threshold

        Returns:
            List of similar cards with scores.
        """
        if card_id not in self.tree_web.cards:
            return []

        card = self.tree_web.cards[card_id]
        if not card.embedding:
            return []

        # Search using card's embedding
        card_embeddings = {
            cid: c.embedding
            for cid, c in self.tree_web.cards.items()
            if c.embedding and cid != card_id
        }

        if not card_embeddings:
            return []

        from .embeddings import semantic_search
        results = semantic_search(
            card.embedding,
            card_embeddings,
            top_k=top_k,
            threshold=threshold
        )

        # Format
        formatted = []
        for cid, similarity in results:
            c = self.tree_web.cards[cid]
            formatted.append({
                "card_id": cid,
                "title": c.buffers.get("title"),
                "type": c.buffers.get("type"),
                "project": c.buffers.get("project"),
                "similarity": similarity,
            })

        return formatted

    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.3,
        recency_weight: float = 0.1,
        project: str = None,
    ) -> List[Dict]:
        """Hybrid search combining semantic + keyword + recency.

        Args:
            query: Search query
            top_k: Max results
            semantic_weight: Weight for semantic similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)
            recency_weight: Weight for recency (0-1)
            project: Optional project filter

        Returns:
            List of results with combined scores.
        """
        results: Dict[int, Dict] = {}

        # 1. Semantic search
        if self.embedder and semantic_weight > 0:
            query_emb = self.embedder.embed_query(query)
            for card_id, card in self.tree_web.cards.items():
                if project and card.buffers.get("project") != project:
                    continue
                if card.embedding:
                    from .embeddings import cosine_similarity
                    sim = cosine_similarity(query_emb, card.embedding)
                    results[card_id] = {
                        "card_id": card_id,
                        "card": card,
                        "semantic_score": sim,
                        "keyword_score": 0.0,
                        "recency_score": 0.0,
                    }

        # 2. Keyword search
        if keyword_weight > 0:
            keywords = query.lower().split()
            for card_id, card in self.tree_web.cards.items():
                if project and card.buffers.get("project") != project:
                    continue

                # Score keywords in title, narrative, facts
                score = 0.0
                title = str(card.buffers.get("title", "")).lower()
                narrative = str(card.buffers.get("narrative", "")).lower()
                facts = " ".join(str(f) for f in card.buffers.get("facts", [])).lower()

                for kw in keywords:
                    if kw in title:
                        score += 2.0
                    if kw in narrative:
                        score += 1.0
                    if kw in facts:
                        score += 0.5

                if score > 0:
                    score = min(score / (len(keywords) * 2), 1.0)  # Normalize

                    if card_id in results:
                        results[card_id]["keyword_score"] = score
                    else:
                        results[card_id] = {
                            "card_id": card_id,
                            "card": card,
                            "semantic_score": 0.0,
                            "keyword_score": score,
                            "recency_score": 0.0,
                        }

        # 3. Recency score (based on created_at_epoch)
        if recency_weight > 0 and results:
            epochs = [
                r["card"].buffers.get("created_at_epoch", 0)
                for r in results.values()
            ]
            max_epoch = max(epochs) if epochs else 1
            min_epoch = min(epochs) if epochs else 0
            epoch_range = max_epoch - min_epoch if max_epoch != min_epoch else 1

            for r in results.values():
                epoch = r["card"].buffers.get("created_at_epoch", 0)
                r["recency_score"] = (epoch - min_epoch) / epoch_range

        # 4. Combine scores
        for r in results.values():
            r["final_score"] = (
                r["semantic_score"] * semantic_weight +
                r["keyword_score"] * keyword_weight +
                r["recency_score"] * recency_weight
            )

        # Sort and format
        sorted_results = sorted(
            results.values(),
            key=lambda x: x["final_score"],
            reverse=True
        )[:top_k]

        return [
            {
                "card_id": r["card_id"],
                "title": r["card"].buffers.get("title"),
                "type": r["card"].buffers.get("type"),
                "project": r["card"].buffers.get("project"),
                "final_score": r["final_score"],
                "semantic_score": r["semantic_score"],
                "keyword_score": r["keyword_score"],
                "recency_score": r["recency_score"],
            }
            for r in sorted_results
        ]

    # =========================================================================
    # Stats
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about both memory systems."""
        stats = {
            "tree_web": {
                "moments": len(self.tree_web.moments),
                "cards": len(self.tree_web.cards),
                "links": len(self.tree_web.links),
            },
            "mappings": {
                "sessions_mapped": len(self._session_to_moment),
                "observations_mapped": len(self._obs_to_card),
            },
        }

        # Get claude-mem stats
        try:
            conn = self.connect()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM observations")
            stats["claude_mem"] = {"observations": cursor.fetchone()[0]}

            cursor.execute("SELECT COUNT(*) FROM sdk_sessions")
            stats["claude_mem"]["sessions"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT project) FROM observations")
            stats["claude_mem"]["projects"] = cursor.fetchone()[0]

            conn.close()
        except:
            stats["claude_mem"] = {"error": "Could not connect"}

        return stats


# =============================================================================
# Convenience Functions
# =============================================================================

def create_bridge(db_path: str = None, auto_import: bool = True) -> ClaudeMemBridge:
    """Create a bridge with optional auto-import.

    Args:
        db_path: Path to claude-mem database
        auto_import: Import all observations on creation

    Returns:
        Configured ClaudeMemBridge.
    """
    config = ClaudeMemConfig()
    if db_path:
        config.db_path = db_path

    bridge = ClaudeMemBridge(config)

    if auto_import:
        bridge.import_all()

    return bridge


def quick_search(query: str, project: str = None, limit: int = 10) -> List[Dict]:
    """Quick search across claude-mem.

    Args:
        query: Search query
        project: Optional project filter
        limit: Max results

    Returns:
        Search results.
    """
    bridge = ClaudeMemBridge()
    return bridge.search(query=query, project=project, limit=limit)
