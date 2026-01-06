"""Memory Card Viewer TUI.

A terminal UI for browsing and searching memory cards from claude-mem.

Usage:
    python -m applets.claude_mem_bridge.tui
    # or
    cd applets/claude_mem_bridge && python tui.py
"""

from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Input, ListView, ListItem,
    Label, Rule, Markdown, TabbedContent, TabPane
)
from textual.reactive import reactive
from textual import events

from .bridge import ClaudeMemBridge, ClaudeMemConfig, MemoryCard


class CardPreview(Static):
    """Shows preview of selected card."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.card: Optional[MemoryCard] = None

    def set_card(self, card: MemoryCard):
        """Update the displayed card."""
        self.card = card
        self.refresh_content()

    def refresh_content(self):
        """Render the card content."""
        if not self.card:
            self.update("[dim]Select a card to view details[/dim]")
            return

        card = self.card
        title = card.buffers.get_text('title') or "Untitled"
        obs_type = card.buffers.get_text('type') or "unknown"
        project = card.buffers.get_text('project') or "none"
        narrative = card.buffers.get_text('narrative') or ""
        facts = card.buffers.get_lines('facts')
        concepts = card.buffers.get_lines('concepts')

        # Type colors
        type_colors = {
            'bugfix': 'red',
            'feature': 'green',
            'discovery': 'cyan',
            'decision': 'yellow',
            'change': 'blue',
            'refactor': 'magenta',
        }
        type_color = type_colors.get(obs_type, 'white')

        # Build content
        lines = [
            f"[bold]{title}[/bold]",
            "",
            f"[{type_color}]● {obs_type}[/{type_color}]  [dim]|[/dim]  [blue]{project}[/blue]  [dim]|[/dim]  ID: {card.card_id}",
            "",
        ]

        if card.created_at:
            lines.append(f"[dim]Created: {card.created_at.strftime('%Y-%m-%d %H:%M')}[/dim]")
            lines.append("")

        if narrative:
            lines.append("[bold]Narrative[/bold]")
            lines.append("─" * 40)
            # Wrap long narratives
            for para in narrative.split('\n'):
                lines.append(para)
            lines.append("")

        if facts:
            lines.append(f"[bold]Facts[/bold] ({len(facts)})")
            lines.append("─" * 40)
            for fact in facts[:10]:
                lines.append(f"  • {fact}")
            if len(facts) > 10:
                lines.append(f"  [dim]... and {len(facts) - 10} more[/dim]")
            lines.append("")

        if concepts:
            lines.append("[bold]Concepts[/bold]")
            lines.append("─" * 40)
            lines.append("  " + ", ".join(concepts[:20]))
            lines.append("")

        self.update("\n".join(lines))


class CardListItem(ListItem):
    """A list item representing a memory card."""

    def __init__(self, card: MemoryCard, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.card = card

    def compose(self) -> ComposeResult:
        title = self.card.buffers.get_text('title') or "Untitled"
        obs_type = self.card.buffers.get_text('type') or "?"
        project = self.card.buffers.get_text('project') or ""

        # Type emoji
        type_emoji = {
            'bugfix': '🔴',
            'feature': '🟢',
            'discovery': '🔵',
            'decision': '🟡',
            'change': '⚪',
            'refactor': '🟣',
        }.get(obs_type, '⚫')

        # Truncate title
        if len(title) > 60:
            title = title[:57] + "..."

        yield Static(f"{type_emoji} {title}")


class MemoryViewerApp(App):
    """TUI for browsing memory cards."""

    CSS = """
    #main-container {
        layout: horizontal;
    }

    #card-list-container {
        width: 50%;
        border-right: solid $primary;
    }

    #card-preview-container {
        width: 50%;
        padding: 1 2;
    }

    #search-input {
        margin: 1;
    }

    #card-list {
        height: 100%;
    }

    #stats-bar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }

    CardPreview {
        height: 100%;
    }

    .filter-bar {
        height: 3;
        padding: 0 1;
    }

    #type-filter {
        width: 20;
    }

    #project-filter {
        width: 20;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("/", "focus_search", "Search"),
        Binding("r", "refresh", "Refresh"),
        Binding("escape", "clear_search", "Clear"),
        Binding("t", "cycle_type", "Type Filter"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    search_query = reactive("")
    type_filter = reactive("")
    project_filter = reactive("")

    def __init__(self):
        super().__init__()
        self.bridge: Optional[ClaudeMemBridge] = None
        self.all_cards: list[MemoryCard] = []
        self.filtered_cards: list[MemoryCard] = []
        self.type_options = ["", "bugfix", "feature", "discovery", "decision", "change", "refactor"]
        self.type_index = 0

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="main-container"):
            with Vertical(id="card-list-container"):
                yield Input(placeholder="Search cards...", id="search-input")
                yield ListView(id="card-list")

            with ScrollableContainer(id="card-preview-container"):
                yield CardPreview(id="card-preview")

        yield Static(id="stats-bar")
        yield Footer()

    async def on_mount(self) -> None:
        """Load data when app starts."""
        self.title = "Memory Card Viewer"
        self.sub_title = "Loading..."

        # Load data in background
        self.load_data()

    def load_data(self) -> None:
        """Load cards from claude-mem."""
        config = ClaudeMemConfig(
            db_path="~/.claude-mem/claude-mem.db",
            import_embeddings=False,
        )

        self.bridge = ClaudeMemBridge(config)
        stats = self.bridge.import_all()

        self.all_cards = list(self.bridge.cards.values())
        # Sort by created_at descending
        self.all_cards.sort(
            key=lambda c: c.created_at or datetime.min,
            reverse=True
        )

        self.filtered_cards = self.all_cards
        self.refresh_list()
        self.update_stats()
        self.sub_title = f"{len(self.all_cards)} cards loaded"

    def refresh_list(self) -> None:
        """Refresh the card list with current filters."""
        list_view = self.query_one("#card-list", ListView)
        list_view.clear()

        for card in self.filtered_cards[:500]:  # Limit for performance
            list_view.append(CardListItem(card))

    def update_stats(self) -> None:
        """Update the stats bar."""
        stats_bar = self.query_one("#stats-bar", Static)
        showing = len(self.filtered_cards)
        total = len(self.all_cards)
        type_str = f" | Type: {self.type_filter}" if self.type_filter else ""
        stats_bar.update(f"Showing {showing}/{total} cards{type_str}")

    def apply_filters(self) -> None:
        """Apply search and type filters."""
        query = self.search_query.lower().strip()
        type_f = self.type_filter

        self.filtered_cards = []
        for card in self.all_cards:
            # Type filter
            if type_f and card.buffers.get_text('type') != type_f:
                continue

            # Search filter
            if query:
                text = card.buffers.all_text().lower()
                if query not in text:
                    continue

            self.filtered_cards.append(card)

        self.refresh_list()
        self.update_stats()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.search_query = event.value
            self.apply_filters()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle card selection."""
        if isinstance(event.item, CardListItem):
            preview = self.query_one("#card-preview", CardPreview)
            preview.set_card(event.item.card)

    def action_focus_search(self) -> None:
        """Focus the search input."""
        self.query_one("#search-input", Input).focus()

    def action_clear_search(self) -> None:
        """Clear search and filters."""
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self.search_query = ""
        self.type_filter = ""
        self.type_index = 0
        self.apply_filters()

    def action_cycle_type(self) -> None:
        """Cycle through type filters."""
        self.type_index = (self.type_index + 1) % len(self.type_options)
        self.type_filter = self.type_options[self.type_index]
        self.apply_filters()

    def action_refresh(self) -> None:
        """Reload data."""
        self.load_data()

    def action_cursor_down(self) -> None:
        """Move cursor down in list."""
        list_view = self.query_one("#card-list", ListView)
        list_view.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in list."""
        list_view = self.query_one("#card-list", ListView)
        list_view.action_cursor_up()


def main():
    """Run the TUI app."""
    app = MemoryViewerApp()
    app.run()


if __name__ == "__main__":
    main()
