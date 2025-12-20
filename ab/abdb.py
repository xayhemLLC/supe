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
        self.conn.commit()

        # Schema Migration: Add 'dna' column if missing
        self._ensure_column("cards", "dna", "TEXT")
        self._ensure_column("selves", "dna", "TEXT")

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
            "INSERT INTO cards (label, moment_id, owner_self, created_at, master_input, master_output, dna) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (label, moment_id, owner_self, ts, master_input, master_output, dna),
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