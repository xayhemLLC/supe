#!/usr/bin/env python3
"""Tasc TUI: lightweight terminal dashboard."""

from __future__ import annotations

import os
from pathlib import Path

from ab.abdb import ABMemory
from ab.models import Buffer


def _box(title: str, content: str, width: int = 70) -> str:
    lines = content.split("\n")
    result = [f"┌─ {title} " + "─" * max(1, width - len(title) - 4) + "┐"]
    for line in lines:
        result.append(f"│ {line[: width - 4].ljust(width - 4)} │")
    result.append("└" + "─" * (width - 2) + "┘")
    return "\n".join(result)


class TascTUI:
    """Simple terminal UI for browsing and saving cards."""

    def __init__(self) -> None:
        self.db_path = os.environ.get("TASC_DB", "tasc.sqlite")
        self.running = True

    def _memory(self) -> ABMemory:
        return ABMemory(self.db_path)

    def clear(self) -> None:
        os.system("clear" if os.name != "nt" else "cls")

    def _stats(self) -> dict[str, int]:
        mem = self._memory()
        conn = mem.conn
        return {
            "cards": conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0],
            "moments": conn.execute("SELECT COUNT(*) FROM moments").fetchone()[0],
        }

    def render_dashboard(self) -> None:
        stats = self._stats()
        self.clear()
        print(
            _box(
                "Tasc Dashboard",
                (
                    f"Database: {self.db_path}\n"
                    f"Cards:    {stats['cards']}\n"
                    f"Moments:  {stats['moments']}\n\n"
                    "[1] List cards   [2] Save card   [3] Search   [4] Stats   [q] Quit"
                ),
            )
        )

    def render_cards(self, limit: int = 20) -> None:
        mem = self._memory()
        rows = mem.conn.execute(
            "SELECT id, label, owner_self, created_at FROM cards ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        content = []
        for row in rows:
            owner = row[2] or "-"
            content.append(f"[{row[0]:4}] {row[1]:12} {owner:12} {row[3]}")
        print(_box("Recent Cards", "\n".join(content) if content else "No cards found."))

    def render_stats(self) -> None:
        stats = self._stats()
        print(
            _box(
                "Stats",
                f"Cards:   {stats['cards']}\nMoments: {stats['moments']}",
            )
        )

    def save_card(self) -> None:
        title = input("Title: ").strip()
        if not title:
            return
        mem = self._memory()
        moment = mem.create_moment(master_input=f"TUI save: {title}", master_output="saved")
        card = mem.store_card(
            label="tasc",
            buffers=[Buffer(name="title", payload=title.encode("utf-8"))],
            owner_self="TUI",
            moment_id=moment.id,
        )
        print(_box("Saved", f"Created card {card.id}"))

    def search(self) -> None:
        query = input("Search query: ").strip()
        if not query:
            return
        mem = self._memory()
        rows = mem.conn.execute(
            """
            SELECT DISTINCT c.id, c.label, b.name, b.payload
            FROM cards c
            JOIN buffers b ON c.id = b.card_id
            WHERE b.payload LIKE ?
            ORDER BY c.id DESC
            LIMIT 20
            """,
            (f"%{query}%",),
        ).fetchall()
        lines = []
        for row in rows:
            payload = row[3] if isinstance(row[3], str) else str(row[3])
            lines.append(f"[{row[0]}] {row[1]}/{row[2]}: {payload[:80]}")
        print(_box("Search Results", "\n".join(lines) if lines else "No matches found."))

    def run(self) -> None:
        while self.running:
            self.render_dashboard()
            choice = input("\nSelect: ").strip().lower()
            if choice == "q":
                self.running = False
            elif choice == "1":
                self.render_cards()
                input("\nPress Enter...")
            elif choice == "2":
                self.save_card()
                input("\nPress Enter...")
            elif choice == "3":
                self.search()
                input("\nPress Enter...")
            elif choice == "4":
                self.render_stats()
                input("\nPress Enter...")


def main() -> None:
    # Ensure local project imports work when launched directly.
    if str(Path.cwd()) not in os.sys.path:
        os.sys.path.insert(0, str(Path.cwd()))
    TascTUI().run()


if __name__ == "__main__":
    main()
