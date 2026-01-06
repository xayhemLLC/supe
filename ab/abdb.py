"""Simple SQLite-backed storage for the AB memory engine.

The ``ABMemory`` class encapsulates the persistence layer for AB
entities. It manages a SQLite database containing tables for
moments, cards and buffers. This implementation is deliberately
self-contained and does not depend on any external databases or ORM
frameworks.

Each card is associated with a moment via the ``moment_id`` foreign
key. Buffers belong to a card via the ``card_id`` foreign key. The
``headers`` of buffers are stored as JSON text.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import List, Optional

from .models import Buffer, Card, CardStats, Moment


class ABMemory:
    """A high-level manager for AB storage using SQLite."""

    def __init__(self, db_path: str = "ab_memory.sqlite") -> None:
        """Create a new ``ABMemory`` instance.

        Args:
            db_path: Path to the SQLite database file. A new file will
                be created if it does not already exist.
        """
        # Connect with row_factory to return dict-like rows.
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        """Initialise the SQLite schema if it does not exist."""
        cur = self.conn.cursor()
        # Create moments table.  Moments store the master input and
        # output for the cognitive pulse, as well as the ID of the
        # awareness card associated with that moment.  These columns
        # default to NULL and can be updated after the moment is
        # created.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS moments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                master_input TEXT,
                master_output TEXT,
                awareness_card_id INTEGER,
                -- ID of the master card associated with this moment.  Each
                -- moment may capture raw sensory and internal state data on a
                -- dedicated master card; this column stores its ID.  It is
                -- optional to support older moments created before the
                -- introduction of master cards.
                master_card_id INTEGER,
                FOREIGN KEY (awareness_card_id) REFERENCES cards (id),
                FOREIGN KEY (master_card_id) REFERENCES cards (id)
            )
            """
        )
        # Create cards table.  Cards now have optional master input and
        # master output fields analogous to moments.  These fields may
        # be used by subselves or transformations to capture
        # high-level inputs and results.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                moment_id INTEGER NOT NULL,
                owner_self TEXT,
                created_at TEXT NOT NULL,
                master_input TEXT,
                master_output TEXT,
                FOREIGN KEY (moment_id) REFERENCES moments (id)
            )
            """
        )
        # Create buffers table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS buffers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                headers TEXT,
                payload BLOB,
                exe TEXT,
                FOREIGN KEY (card_id) REFERENCES cards (id)
            )
            """
        )
        # Add table for selves (subself definitions). A self represents a cognitive agent
        # with its own lane (a card containing its own cards). Each row stores the
        # self's name, optional role (e.g., planner, coder), the card ID of its lane,
        # subscribed buffer names (JSON array), and creation timestamp.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS selves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT,
                lane_card_id INTEGER,
                subscribed_buffers TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        # Table for subscriptions. Each subscription links a subscriber card to a
        # specific buffer name on a source card. When the source buffer is
        # updated, the system can propagate the content to the subscriber. The
        # subscription also stores optional headers or configuration, stored as
        # JSON in the config column.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscriber_card_id INTEGER NOT NULL,
                source_card_id INTEGER NOT NULL,
                buffer_name TEXT NOT NULL,
                config TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (subscriber_card_id) REFERENCES cards (id),
                FOREIGN KEY (source_card_id) REFERENCES cards (id)
            )
            """
        )

        # Table for explicit connections between cards. Each connection encodes
        # a relationship from a source card to a target card (e.g., summary_of,
        # dependency_of, cites, references). The relation is a free-form string.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_card_id INTEGER NOT NULL,
                target_card_id INTEGER NOT NULL,
                relation TEXT NOT NULL,
                strength REAL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_card_id) REFERENCES cards (id),
                FOREIGN KEY (target_card_id) REFERENCES cards (id)
            )
            """
        )

        # Table for card statistics (memory physics). Each card has an entry
        # tracking its strength, recall count, and last recalled timestamp.
        # Strength is updated using the formula: strength = strength * 0.9 + 1.0
        # on each recall. This enables frequently recalled memories to dominate.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS card_stats (
                card_id INTEGER PRIMARY KEY,
                strength REAL DEFAULT 1.0,
                recall_count INTEGER DEFAULT 0,
                last_recalled TEXT,
                FOREIGN KEY (card_id) REFERENCES cards (id)
            )
            """
        )

        # Table for typed semantic relations between cards. Unlike the generic
        # 'connections' table, this stores formal typed relations (CAUSES, IMPLIES,
        # SUPPORTS, etc.) with confidence scores and structured metadata for enabling
        # sophisticated reasoning capabilities.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS relations (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                source_card_id INTEGER NOT NULL,
                target_card_id INTEGER NOT NULL,
                confidence REAL DEFAULT 1.0,
                metadata TEXT,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (source_card_id) REFERENCES cards (id),
                FOREIGN KEY (target_card_id) REFERENCES cards (id)
            )
            """
        )
        self.conn.commit()

        # Schema Migration: Add 'dna' column if missing
        self._ensure_column("cards", "dna", "TEXT")
        self._ensure_column("selves", "dna", "TEXT")
        
        # Schema Migration: Add 'track' column for dual-track memory
        # Tracks: 'awareness' (knowledge/content), 'execution' (tasc history), 'sensory' (raw input)
        self._ensure_column("cards", "track", "TEXT DEFAULT 'awareness'")
        
        # Schema Migration: Add 'forgotten' column for soft-delete forgetting
        self._ensure_column("cards", "forgotten", "INTEGER DEFAULT 0")
        self._ensure_column("cards", "forgotten_at", "TEXT")
        
        # Schema Migration: Tags and metadata for linking
        self._ensure_column("cards", "tags", "TEXT")  # JSON array
        self._ensure_column("cards", "metadata", "TEXT")  # JSON object
        self._ensure_column("cards", "parent_card_id", "INTEGER")  # For branching
        
        # Schema Migration: Moment extensions for cognitive architecture
        self._ensure_column("moments", "execution_card_id", "INTEGER")
        self._ensure_column("moments", "sensory_card_id", "INTEGER")
        self._ensure_column("moments", "overlord_narration", "TEXT")  # Final note
        
        # Create tracks table if not exists
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                name TEXT PRIMARY KEY,
                input_source TEXT,
                is_active INTEGER DEFAULT 1,
                config TEXT
            )
        """)
        
        # Create sensory_organs table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sensory_organs (
                name TEXT PRIMARY KEY,
                organ_type TEXT NOT NULL,
                config TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def _ensure_column(self, table: str, column: str, type_def: str) -> None:
        """Add a column to a table if it does not exist."""
        cur = self.conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        columns = [info[1] for info in cur.fetchall()]
        if column not in columns:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}")
            self.conn.commit()

    # ------------------------------------------------------------------
    # Moment handling
    # ------------------------------------------------------------------
    def create_moment(
        self,
        timestamp: Optional[str] = None,
        master_input: Optional[str] = None,
        master_output: Optional[str] = None,
        awareness_card_id: Optional[int] = None,
        master_card_id: Optional[int] = None,
    ) -> Moment:
        """Create a new moment and return the ``Moment`` instance.

        Args:
            timestamp: Optional ISO-8601 timestamp.  If ``None``, the
                current UTC time is used.
            master_input: Optional master input string to initialise the
                moment's input.
            master_output: Optional master output string to initialise
                the moment's output.
            awareness_card_id: Optional ID of an awareness card to
                associate with this moment.

        Returns:
            The created ``Moment`` instance with assigned ID and
            timestamp.
        """
        ts = timestamp or datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO moments (timestamp, master_input, master_output, awareness_card_id, master_card_id) VALUES (?, ?, ?, ?, ?)",
            (ts, master_input, master_output, awareness_card_id, master_card_id),
        )
        moment_id = cur.lastrowid
        self.conn.commit()
        return Moment(
            id=moment_id,
            timestamp=ts,
            master_input=master_input,
            master_output=master_output,
            awareness_card_id=awareness_card_id,
            master_card_id=master_card_id,
        )

    def get_moment(self, moment_id: int) -> Moment:
        """Retrieve a moment by its ID."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM moments WHERE id = ?", (moment_id,))
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"Moment with id {moment_id} not found")
        return Moment(
            id=row["id"],
            timestamp=row["timestamp"],
            master_input=row["master_input"],
            master_output=row["master_output"],
            awareness_card_id=row["awareness_card_id"],
            master_card_id=row["master_card_id"],
        )
    
    def get_latest_moment(self) -> Optional[Moment]:
        """Get the most recent moment (present moment).
        
        Returns:
            Most recent Moment or None if no moments exist.
        """
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM moments ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row is None:
            return None
        return Moment(
            id=row["id"],
            timestamp=row["timestamp"],
            master_input=row["master_input"],
            master_output=row["master_output"],
            awareness_card_id=row["awareness_card_id"],
            master_card_id=row["master_card_id"],
        )
    
    def get_moments(
        self, 
        direction: str = "back", 
        limit: int = 10,
    ) -> List[Moment]:
        """Get moments in chronological order.
        
        Args:
            direction: 'back' (oldest first) or 'forward' (newest first).
            limit: Maximum moments to return.
        
        Returns:
            List of Moments.
        """
        order = "DESC" if direction == "forward" else "ASC"
        cur = self.conn.cursor()
        cur.execute(f"SELECT * FROM moments ORDER BY id {order} LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [
            Moment(
                id=row["id"],
                timestamp=row["timestamp"],
                master_input=row["master_input"],
                master_output=row["master_output"],
                awareness_card_id=row["awareness_card_id"],
                master_card_id=row["master_card_id"],
            )
            for row in rows
        ]
    
    def search_cards(
        self, 
        query: str, 
        limit: int = 10,
        exact: bool = False,
        track: Optional[str] = None,
    ) -> List[Card]:
        """Search cards by text in master fields.
        
        Args:
            query: Search query.
            limit: Maximum results.
            exact: If True, exact match. If False, contains match.
            track: Filter by track ('awareness', 'execution') or None for all.
        
        Returns:
            List of matching Cards.
        """
        cur = self.conn.cursor()
        if exact:
            pattern = query
            sql = """
                SELECT * FROM cards 
                WHERE (master_input = ? OR master_output = ? OR label = ?)
            """
            params = [pattern, pattern, pattern]
        else:
            pattern = f"%{query}%"
            sql = """
                SELECT * FROM cards 
                WHERE (master_input LIKE ? OR master_output LIKE ? OR label LIKE ?)
            """
            params = [pattern, pattern, pattern]
        
        if track:
            sql += " AND track = ?"
            params.append(track)
        
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            card = self.get_card(row["id"])
            results.append(card)
        return results
    
    def get_cards_by_moment(self, moment_id: int) -> List[Card]:
        """Get all cards associated with a moment.
        
        Args:
            moment_id: Moment ID to query.
        
        Returns:
            List of Cards at that moment.
        """
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM cards WHERE moment_id = ?", (moment_id,))
        rows = cur.fetchall()
        return [self.get_card(row["id"]) for row in rows]
    
    def get_moment_connections(self, moment_id: int) -> List[int]:
        """Get connected moment IDs (for graph traversal).
        
        Moments are connected through cards that reference them.
        
        Args:
            moment_id: Starting moment ID.
        
        Returns:
            List of connected moment IDs.
        """
        # Simple implementation: adjacent moments
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id FROM moments WHERE id IN (?, ?) AND id != ?",
            (moment_id - 1, moment_id + 1, moment_id)
        )
        return [row["id"] for row in cur.fetchall()]

    # ------------------------------------------------------------------
    # Card handling
    # ------------------------------------------------------------------
    def store_card(
        self,
        label: str,
        buffers: List[Buffer],
        owner_self: Optional[str] = None,
        moment_id: Optional[int] = None,
        created_at: Optional[str] = None,
        master_input: Optional[str] = None,
        master_output: Optional[str] = None,
        dna: Optional[str] = None,
        track: str = "awareness",
    ) -> Card:
        """Persist a card and its buffers into the database.

        Args:
            label: The card label (e.g., "tasc").
            buffers: A list of ``Buffer`` objects to attach to the card.
            owner_self: Optional identifier for the self that created the card.
            moment_id: Optionally associate with an existing moment; if
                ``None``, a new moment will be created.
            created_at: Override the creation timestamp; defaults to
                ``datetime.utcnow().isoformat()``.
            dna: Optional serialized DNA string.
            track: Memory track - 'awareness' (knowledge/content), 
                   'execution' (tasc history), or 'sensory' (raw input).

        Returns:
            The stored ``Card`` with the assigned ID and moment ID.
        """
        # Ensure we have a moment id
        if moment_id is None:
            moment = self.create_moment()
            moment_id = moment.id
        ts = created_at or datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO cards (label, moment_id, owner_self, created_at, master_input, master_output, dna, track) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (label, moment_id, owner_self, ts, master_input, master_output, dna, track),
        )
        card_id = cur.lastrowid
        # Insert buffers
        for buf in buffers:
            headers_json = json.dumps(buf.headers) if buf.headers else None
            cur.execute(
                "INSERT INTO buffers (card_id, name, headers, payload, exe) VALUES (?, ?, ?, ?, ?)",
                (card_id, buf.name, headers_json, buf.payload, buf.exe),
            )
        self.conn.commit()
        
        # Initialize card stats so card appears in list_cards_by_strength
        self.init_card_stats(card_id)
        
        return Card(
            id=card_id,
            label=label,
            moment_id=moment_id,
            owner_self=owner_self,
            created_at=ts,
            buffers=buffers,
            master_input=master_input,
            master_output=master_output,
            track=track,
        )

    def get_card(self, card_id: int) -> Card:
        """Retrieve a card and its buffers by card ID."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"Card with id {card_id} not found")
        # Fetch buffers
        cur.execute(
            "SELECT * FROM buffers WHERE card_id = ? ORDER BY id ASC",
            (card_id,),
        )
        buffer_rows = cur.fetchall()
        buffers: List[Buffer] = []
        for b_row in buffer_rows:
            headers = json.loads(b_row["headers"]) if b_row["headers"] else {}
            buffer = Buffer(
                name=b_row["name"],
                headers=headers,
                payload=b_row["payload"] if b_row["payload"] is not None else b"",
                exe=b_row["exe"],
            )
            buffers.append(buffer)
        return Card(
            id=row["id"],
            label=row["label"],
            moment_id=row["moment_id"],
            owner_self=row["owner_self"],
            created_at=row["created_at"],
            buffers=buffers,
            master_input=row["master_input"],
            master_output=row["master_output"],
            dna=row["dna"] if "dna" in row.keys() else None,
            track=row["track"] if "track" in row.keys() else "awareness",
        )

    # ------------------------------------------------------------------
    # Buffer and card updates
    # ------------------------------------------------------------------
    def update_card_buffers(self, card_id: int, buffers: List[Buffer]) -> None:
        """Replace all buffers on the given card with a new list.

        Args:
            card_id: ID of the card to update.
            buffers: The new list of buffers to store on the card.

        This method deletes all existing buffers for the card and
        inserts the provided ones.  No changes are made to the card's
        label, moment or metadata.  Callers should ensure that the
        card exists prior to invoking this method.
        """
        cur = self.conn.cursor()
        # Delete existing buffers
        cur.execute(
            "DELETE FROM buffers WHERE card_id = ?",
            (card_id,),
        )
        # Insert new buffers
        for buf in buffers:
            headers_json = json.dumps(buf.headers) if buf.headers else None
            cur.execute(
                "INSERT INTO buffers (card_id, name, headers, payload, exe) VALUES (?, ?, ?, ?, ?)",
                (card_id, buf.name, headers_json, buf.payload, buf.exe),
            )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Master input/output updates
    # ------------------------------------------------------------------
    def update_card_master(
        self,
        card_id: int,
        master_input: Optional[str] = None,
        master_output: Optional[str] = None,
    ) -> None:
        """Update the master input and/or master output for a card.

        Args:
            card_id: ID of the card to update.
            master_input: New master input value, or ``None`` to leave
                unchanged.
            master_output: New master output value, or ``None`` to
                leave unchanged.
        """
        fields = []
        params: List[object] = []
        if master_input is not None:
            fields.append("master_input = ?")
            params.append(master_input)
        if master_output is not None:
            fields.append("master_output = ?")
            params.append(master_output)
        if not fields:
            return
        params.append(card_id)
        cur = self.conn.cursor()
        cur.execute(
            f"UPDATE cards SET {', '.join(fields)} WHERE id = ?",
            tuple(params),
        )
        self.conn.commit()

    def update_moment_fields(
        self,
        moment_id: int,
        master_input: Optional[str] = None,
        master_output: Optional[str] = None,
        awareness_card_id: Optional[int] = None,
        master_card_id: Optional[int] = None,
    ) -> None:
        """Update fields on a moment.

        Args:
            moment_id: ID of the moment to update.
            master_input: New master input string (optional).
            master_output: New master output string (optional).
            awareness_card_id: ID of awareness card to associate (optional).
        """
        fields = []
        params: List[object] = []
        if master_input is not None:
            fields.append("master_input = ?")
            params.append(master_input)
        if master_output is not None:
            fields.append("master_output = ?")
            params.append(master_output)
        if awareness_card_id is not None:
            fields.append("awareness_card_id = ?")
            params.append(awareness_card_id)
        if master_card_id is not None:
            fields.append("master_card_id = ?")
            params.append(master_card_id)
        if not fields:
            return
        params.append(moment_id)
        cur = self.conn.cursor()
        cur.execute(
            f"UPDATE moments SET {', '.join(fields)} WHERE id = ?",
            tuple(params),
        )
        self.conn.commit()

    def find_cards_by_label(self, label: str) -> List[Card]:
        """Return all cards with the given label."""
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM cards WHERE label = ? ORDER BY id ASC", (label,))
        card_ids = [row["id"] for row in cur.fetchall()]
        return [self.get_card(cid) for cid in card_ids]

    def close(self) -> None:
        """Close the SQLite connection."""
        self.conn.close()

    # ------------------------------------------------------------------
    # Self / subself management
    # ------------------------------------------------------------------
    def create_self(
        self,
        name: str,
        role: Optional[str] = None,
        subscribed_buffers: Optional[List[str]] = None,
        dna: Optional[str] = None,
    ) -> int:
        """Create a new subself (self) with its own lane card.

        A subself is represented by a row in the ``selves`` table and an
        associated lane card (label ``"lane"``). The lane card holds
        buffers created by the subself. The lane starts empty.

        Args:
            name: The name of the subself.
            role: Optional role (e.g., "planner", "coder").
            subscribed_buffers: Optional list of buffer names this self
                is interested in. Used for filtering input.
            dna: Optional serialized DNA string.

        Returns:
            The ID of the new subself (row in ``selves`` table).
        """
        # Create an empty lane card
        lane_card = self.store_card(label="lane", buffers=[], owner_self=name)
        subself_created_at = datetime.utcnow().isoformat()
        buffers_json = json.dumps(subscribed_buffers) if subscribed_buffers else None
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO selves (name, role, lane_card_id, subscribed_buffers, created_at, dna) VALUES (?, ?, ?, ?, ?, ?)",
            (name, role, lane_card.id, buffers_json, subself_created_at, dna),
        )
        self.conn.commit()
        return cur.lastrowid

    def list_selves(self) -> List[dict]:
        """Return a list of all subselves as dictionaries."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM selves ORDER BY id ASC")
        rows = cur.fetchall()
        selves: List[dict] = []
        for row in rows:
            buffers = json.loads(row["subscribed_buffers"]) if row["subscribed_buffers"] else []
            selves.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "role": row["role"],
                    "lane_card_id": row["lane_card_id"],
                    "subscribed_buffers": buffers,
                    "created_at": row["created_at"],
                }
            )
        return selves

    def get_self(self, self_id: int) -> dict:
        """Retrieve a subself by ID and return as a dictionary."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM selves WHERE id = ?", (self_id,))
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"Subself with id {self_id} not found")
        buffers = json.loads(row["subscribed_buffers"]) if row["subscribed_buffers"] else []
        return {
            "id": row["id"],
            "name": row["name"],
            "role": row["role"],
            "lane_card_id": row["lane_card_id"],
            "subscribed_buffers": buffers,
            "created_at": row["created_at"],
            "dna": row["dna"] if "dna" in row.keys() else None,
        }

    def delete_self(self, self_id: int) -> None:
        """Delete a subself. The lane card remains archived for history."""
        # Just remove the row from selves; do not delete lane card or its buffers
        cur = self.conn.cursor()
        cur.execute("DELETE FROM selves WHERE id = ?", (self_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Subscription management
    # ------------------------------------------------------------------
    def create_subscription(
        self,
        subscriber_card_id: int,
        source_card_id: int,
        buffer_name: str,
        config: Optional[dict] = None,
    ) -> int:
        """Create a buffer subscription.

        When the specified buffer on ``source_card_id`` is updated, the
        subscription can be used to propagate a copy or reference to the
        subscriber card. The ``config`` argument can hold JSON-serialisable
        options (e.g., filters).  Returns the subscription ID.
        """
        cfg_json = json.dumps(config) if config is not None else None
        ts = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO subscriptions (subscriber_card_id, source_card_id, buffer_name, config, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (subscriber_card_id, source_card_id, buffer_name, cfg_json, ts),
        )
        self.conn.commit()
        return cur.lastrowid

    def list_subscriptions(
        self,
        subscriber_card_id: Optional[int] = None,
        source_card_id: Optional[int] = None,
    ) -> List[dict]:
        """List subscriptions filtered by subscriber or source card IDs."""
        cur = self.conn.cursor()
        query = "SELECT * FROM subscriptions"
        params: List[int] = []
        conditions: List[str] = []
        if subscriber_card_id is not None:
            conditions.append("subscriber_card_id = ?")
            params.append(subscriber_card_id)
        if source_card_id is not None:
            conditions.append("source_card_id = ?")
            params.append(source_card_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id ASC"
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        subs: List[dict] = []
        for row in rows:
            cfg = json.loads(row["config"]) if row["config"] else None
            subs.append(
                {
                    "id": row["id"],
                    "subscriber_card_id": row["subscriber_card_id"],
                    "source_card_id": row["source_card_id"],
                    "buffer_name": row["buffer_name"],
                    "config": cfg,
                    "created_at": row["created_at"],
                }
            )
        return subs

    def remove_subscription(self, sub_id: int) -> None:
        """Remove a subscription by its ID."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------
    def create_connection(
        self, source_card_id: int, target_card_id: int, relation: str, strength: float = 1.0
    ) -> int:
        """Record a connection (relationship) between two cards.

        Args:
            source_card_id: The ID of the source card.
            target_card_id: The ID of the target card.
            relation: A string describing the type of relation (e.g.,
                "summary_of", "depends_on", "references").

        Returns:
            The ID of the new connection record.
        """
        ts = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO connections (source_card_id, target_card_id, relation, strength, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (source_card_id, target_card_id, relation, strength, ts),
        )
        self.conn.commit()
        return cur.lastrowid

    def list_connections(self, card_id: Optional[int] = None) -> List[dict]:
        """List connections for a specific card or all cards.

        Args:
            card_id: If provided, return connections where either
                ``source_card_id`` or ``target_card_id`` matches this ID.
                If ``None``, return all connections.

        Returns:
            A list of connection dictionaries.
        """
        cur = self.conn.cursor()
        if card_id is None:
            cur.execute("SELECT * FROM connections ORDER BY id ASC")
            rows = cur.fetchall()
        else:
            cur.execute(
                "SELECT * FROM connections WHERE source_card_id = ? OR target_card_id = ? ORDER BY id ASC",
                (card_id, card_id),
            )
            rows = cur.fetchall()
        conns: List[dict] = []
        for row in rows:
            conns.append(
                {
                    "id": row["id"],
                    "source_card_id": row["source_card_id"],
                    "target_card_id": row["target_card_id"],
                    "relation": row["relation"],
                    "strength": row["strength"],
                    "created_at": row["created_at"],
                }
            )
        return conns

    # ------------------------------------------------------------------
    # Typed semantic relations management
    # ------------------------------------------------------------------
    def add_relation(
        self,
        relation_id: str,
        relation_type: str,
        source_card_id: int,
        target_card_id: int,
        confidence: float = 1.0,
        metadata: Optional[dict] = None,
    ) -> None:
        """Store a typed semantic relation between two cards.

        Args:
            relation_id: Unique identifier for this relation
            relation_type: Type of relation (e.g., "causes", "implies", "supports")
            source_card_id: Source card ID
            target_card_id: Target card ID
            confidence: Confidence in this relation (0.0-1.0)
            metadata: Additional context as dictionary
        """
        created_at = int(datetime.now().timestamp() * 1000)
        metadata_json = json.dumps(metadata) if metadata else None

        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO relations (id, type, source_card_id, target_card_id, confidence, metadata, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (relation_id, relation_type, source_card_id, target_card_id, confidence, metadata_json, created_at),
        )
        self.conn.commit()

    def get_relations(
        self,
        source_card_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        relation_type: Optional[str] = None,
    ) -> List[dict]:
        """Get relations matching the specified filters.

        Args:
            source_card_id: Filter by source card (optional)
            target_card_id: Filter by target card (optional)
            relation_type: Filter by relation type (optional)

        Returns:
            List of relation dictionaries
        """
        cur = self.conn.cursor()

        # Build query dynamically based on filters
        conditions = []
        params = []

        if source_card_id is not None:
            conditions.append("source_card_id = ?")
            params.append(source_card_id)

        if target_card_id is not None:
            conditions.append("target_card_id = ?")
            params.append(target_card_id)

        if relation_type is not None:
            conditions.append("type = ?")
            params.append(relation_type)

        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        else:
            where_clause = ""

        query = f"SELECT * FROM relations{where_clause} ORDER BY created_at DESC"
        cur.execute(query, tuple(params))

        rows = cur.fetchall()
        relations = []
        for row in rows:
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            relations.append(
                {
                    "id": row["id"],
                    "type": row["type"],
                    "source_card_id": row["source_card_id"],
                    "target_card_id": row["target_card_id"],
                    "confidence": row["confidence"],
                    "metadata": metadata,
                    "created_at": row["created_at"],
                }
            )
        return relations

    def get_inverse_relations(
        self,
        card_id: int,
        relation_type: Optional[str] = None,
    ) -> List[dict]:
        """Get relations where the specified card is the target.

        Args:
            card_id: Target card ID
            relation_type: Optional filter by relation type

        Returns:
            List of relation dictionaries
        """
        return self.get_relations(target_card_id=card_id, relation_type=relation_type)

    def delete_relation(self, relation_id: str) -> None:
        """Delete a relation by ID.

        Args:
            relation_id: The relation ID to delete
        """
        cur = self.conn.cursor()
        cur.execute("DELETE FROM relations WHERE id = ?", (relation_id,))
        self.conn.commit()

    def get_relation_by_id(self, relation_id: str) -> Optional[dict]:
        """Get a specific relation by ID.

        Args:
            relation_id: The relation ID

        Returns:
            Relation dictionary or None if not found
        """
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM relations WHERE id = ?", (relation_id,))
        row = cur.fetchone()

        if row is None:
            return None

        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        return {
            "id": row["id"],
            "type": row["type"],
            "source_card_id": row["source_card_id"],
            "target_card_id": row["target_card_id"],
            "confidence": row["confidence"],
            "metadata": metadata,
            "created_at": row["created_at"],
        }

    def count_relations(
        self,
        source_card_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        relation_type: Optional[str] = None,
    ) -> int:
        """Count relations matching the specified filters.

        Args:
            source_card_id: Filter by source card (optional)
            target_card_id: Filter by target card (optional)
            relation_type: Filter by relation type (optional)

        Returns:
            Number of matching relations
        """
        cur = self.conn.cursor()

        conditions = []
        params = []

        if source_card_id is not None:
            conditions.append("source_card_id = ?")
            params.append(source_card_id)

        if target_card_id is not None:
            conditions.append("target_card_id = ?")
            params.append(target_card_id)

        if relation_type is not None:
            conditions.append("type = ?")
            params.append(relation_type)

        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        else:
            where_clause = ""

        query = f"SELECT COUNT(*) as count FROM relations{where_clause}"
        cur.execute(query, tuple(params))

        row = cur.fetchone()
        return row["count"] if row else 0

    # ------------------------------------------------------------------
    # Card stats (memory physics) management
    # ------------------------------------------------------------------
    def init_card_stats(self, card_id: int) -> None:
        """Initialize stats for a card if not already present.

        Creates a row in card_stats with default values (strength=1.0,
        recall_count=0, last_recalled=None).
        """
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO card_stats (card_id, strength, recall_count, last_recalled) "
            "VALUES (?, 1.0, 0, NULL)",
            (card_id,),
        )
        self.conn.commit()

    def get_card_stats(self, card_id: int) -> CardStats:
        """Retrieve stats for a card.

        If no stats exist, they are initialized with defaults first.
        """
        self.init_card_stats(card_id)
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM card_stats WHERE card_id = ?", (card_id,))
        row = cur.fetchone()
        return CardStats(
            card_id=row["card_id"],
            strength=row["strength"],
            recall_count=row["recall_count"],
            last_recalled=row["last_recalled"],
        )

    def recall_card(self, card_id: int) -> CardStats:
        """Recall a card and update its memory physics.

        Applies the formula: strength = strength * 0.9 + 1.0
        Increments recall_count and updates last_recalled timestamp.

        Returns:
            The updated CardStats.
        """
        self.init_card_stats(card_id)
        ts = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE card_stats SET strength = strength * 0.9 + 1.0, "
            "recall_count = recall_count + 1, last_recalled = ? WHERE card_id = ?",
            (ts, card_id),
        )
        self.conn.commit()
        return self.get_card_stats(card_id)

    def apply_decay(self, decay_factor: float = 0.95) -> int:
        """Apply decay to all card strengths.

        Multiplies all card strengths by the decay factor. Cards that
        are not recalled will gradually lose strength over time.

        Args:
            decay_factor: Multiplier for strength (default 0.95 = 5% decay).

        Returns:
            Number of cards affected.
        """
        cur = self.conn.cursor()
        cur.execute("UPDATE card_stats SET strength = strength * ?", (decay_factor,))
        affected = cur.rowcount
        self.conn.commit()
        return affected

    def list_cards_by_strength(self, limit: int = 10) -> List[CardStats]:
        """Return cards ordered by strength (highest first).

        Args:
            limit: Maximum number of cards to return.

        Returns:
            List of CardStats ordered by descending strength.
        """
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM card_stats ORDER BY strength DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [
            CardStats(
                card_id=row["card_id"],
                strength=row["strength"],
                recall_count=row["recall_count"],
                last_recalled=row["last_recalled"],
            )
            for row in rows
        ]
    
    # ------------------------------------------------------------------
    # Forgetting mechanism (cognitive memory model)
    # ------------------------------------------------------------------
    
    def forget(self, card_id: int) -> None:
        """Forget a card (soft delete).
        
        The card is marked as forgotten but can be recovered.
        
        Args:
            card_id: ID of the card to forget.
        """
        ts = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE cards SET forgotten = 1, forgotten_at = ? WHERE id = ?",
            (ts, card_id)
        )
        self.conn.commit()
    
    def recover(self, card_id: int) -> None:
        """Recover a forgotten card.
        
        Args:
            card_id: ID of the card to recover.
        """
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE cards SET forgotten = 0, forgotten_at = NULL WHERE id = ?",
            (card_id,)
        )
        self.conn.commit()
    
    def apply_forgetting(
        self,
        strength_threshold: float = 0.1,
        min_age_days: int = 7,
    ) -> int:
        """Forget cards on weak branches.
        
        Rule: If a card's strength < threshold
        AND the card is older than min_age_days
        AND the card hasn't been recalled recently,
        the card is forgotten (soft delete).
        
        This mimics biological memory consolidation.
        
        Args:
            strength_threshold: Cards below this strength are candidates.
            min_age_days: Don't forget cards newer than this.
        
        Returns:
            Number of cards forgotten.
        """
        from datetime import timedelta
        
        cutoff = (datetime.utcnow() - timedelta(days=min_age_days)).isoformat()
        
        cur = self.conn.cursor()
        
        # Find weak, old, un-recalled cards
        cur.execute("""
            SELECT c.id 
            FROM cards c
            LEFT JOIN card_stats cs ON c.id = cs.card_id
            WHERE 
                c.forgotten = 0
                AND c.created_at < ?
                AND (cs.strength IS NULL OR cs.strength < ?)
                AND (cs.last_recalled IS NULL OR cs.last_recalled < ?)
        """, (cutoff, strength_threshold, cutoff))
        
        to_forget = [row["id"] for row in cur.fetchall()]
        
        if to_forget:
            ts = datetime.utcnow().isoformat()
            cur.executemany(
                "UPDATE cards SET forgotten = 1, forgotten_at = ? WHERE id = ?",
                [(ts, card_id) for card_id in to_forget]
            )
            self.conn.commit()
        
        return len(to_forget)
    
    def list_forgotten(self, limit: int = 100) -> List[Card]:
        """List forgotten cards (for potential recovery).
        
        Args:
            limit: Maximum cards to return.
        
        Returns:
            List of forgotten Cards.
        """
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id FROM cards WHERE forgotten = 1 ORDER BY forgotten_at DESC LIMIT ?",
            (limit,)
        )
        return [self.get_card(row["id"]) for row in cur.fetchall()]