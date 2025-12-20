"""Debugging and visualization utilities for AB memory.

This module provides colored console output, pretty-printing, and
visual representations of AB entities (cards, buffers, connections).
Cards are visualized as rectangular boxes with inputs on the left
and outputs on the right.

Usage:
    from ab.debug import DebugPrinter, visualize_card, trace
    
    printer = DebugPrinter()
    printer.card(card)
    printer.connection(source, target, relation)
    
    # Or use the trace decorator
    @trace
    def my_function():
        pass
"""

from __future__ import annotations

import functools
import json
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .abdb import ABMemory
    from .models import Buffer, Card, CardStats, Moment


# ---------------------------------------------------------------------------
# ANSI Color Codes
# ---------------------------------------------------------------------------

class Colors:
    """ANSI color codes for terminal output."""
    
    # Basic colors
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright foreground
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    @classmethod
    def disable(cls) -> None:
        """Disable all colors (for non-TTY output)."""
        for attr in dir(cls):
            if not attr.startswith('_') and attr.isupper():
                setattr(cls, attr, "")
    
    @classmethod
    def auto(cls) -> None:
        """Auto-detect whether to use colors based on TTY."""
        if not sys.stdout.isatty():
            cls.disable()


# Auto-detect colors on import
Colors.auto()


# ---------------------------------------------------------------------------
# Pretty Print Utilities
# ---------------------------------------------------------------------------

def colored(text: str, color: str) -> str:
    """Wrap text in color codes."""
    return f"{color}{text}{Colors.RESET}"


def bold(text: str) -> str:
    """Make text bold."""
    return colored(text, Colors.BOLD)


def dim(text: str) -> str:
    """Make text dim."""
    return colored(text, Colors.DIM)


def truncate(text: str, max_len: int = 50) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


# ---------------------------------------------------------------------------
# Card Box Visualization
# ---------------------------------------------------------------------------

def visualize_card(card: "Card", width: int = 60) -> str:
    """Create ASCII box visualization of a card.
    
    ┌─────────────────────────────────────────────────────┐
    │ Card #1: conversation                               │
    ├─────────────────────────────────────────────────────┤
    │ ◀ INPUTS                           OUTPUTS ▶        │
    │ ├── user_input (25B)              ├── (none)        │
    │ ├── ai_response (33B)                               │
    │ └── context (52B)                                   │
    ├─────────────────────────────────────────────────────┤
    │ master_input: User asked about...                   │
    │ master_output: (none)                               │
    └─────────────────────────────────────────────────────┘
    """
    lines = []
    inner_width = width - 4  # Account for box borders
    
    # Helper to pad line
    def pad(text: str) -> str:
        visible_len = len(text.replace(Colors.RESET, "").replace(Colors.BOLD, "")
                          .replace(Colors.CYAN, "").replace(Colors.GREEN, "")
                          .replace(Colors.YELLOW, "").replace(Colors.MAGENTA, "")
                          .replace(Colors.BRIGHT_BLUE, "").replace(Colors.DIM, ""))
        padding = inner_width - visible_len
        return text + " " * max(0, padding)
    
    # Top border
    lines.append(f"┌{'─' * (width - 2)}┐")
    
    # Title
    title = f"Card #{card.id}: {colored(card.label, Colors.CYAN)}"
    lines.append(f"│ {pad(title)} │")
    
    # Separator
    lines.append(f"├{'─' * (width - 2)}┤")
    
    # Buffer section header
    header = f"{colored('◀ INPUTS', Colors.GREEN)}"
    lines.append(f"│ {pad(header)} │")
    
    # Input buffers (on left side)
    for i, buf in enumerate(card.buffers):
        prefix = "└──" if i == len(card.buffers) - 1 else "├──"
        size = len(buf.payload) if buf.payload else 0
        exe_info = f" [exe:{buf.exe}]" if buf.exe else ""
        buf_line = f" {prefix} {colored(buf.name, Colors.YELLOW)} ({size}B){exe_info}"
        lines.append(f"│{pad(buf_line)} │")
    
    if not card.buffers:
        lines.append(f"│ {pad('   (no buffers)')} │")
    
    # Separator
    lines.append(f"├{'─' * (width - 2)}┤")
    
    # Master input/output
    mi = truncate(card.master_input or "(none)", inner_width - 15)
    mo = truncate(card.master_output or "(none)", inner_width - 15)
    lines.append(f"│ {pad(f'master_input: {dim(mi)}')} │")
    lines.append(f"│ {pad(f'master_output: {dim(mo)}')} │")
    
    # Bottom border
    lines.append(f"└{'─' * (width - 2)}┘")
    
    return "\n".join(lines)


def visualize_buffer(buf: "Buffer", width: int = 50) -> str:
    """Create ASCII visualization of a buffer."""
    lines = []
    inner = width - 4
    
    def pad(text: str) -> str:
        return text + " " * max(0, inner - len(text))
    
    lines.append(f"┌{'─' * (width - 2)}┐")
    lines.append(f"│ {pad(colored(buf.name, Colors.YELLOW))} │")
    lines.append(f"├{'─' * (width - 2)}┤")
    
    # Headers
    for key, val in buf.headers.items():
        line = f"  {key}: {truncate(str(val), 30)}"
        lines.append(f"│ {pad(line)} │")
    
    # Payload preview
    if buf.payload:
        try:
            preview = buf.payload[:100].decode("utf-8", errors="replace")
            preview = truncate(preview, inner - 2)
        except Exception:
            preview = f"<{len(buf.payload)} bytes>"
        lines.append(f"├{'─' * (width - 2)}┤")
        lines.append(f"│ {pad(dim(preview))} │")
    
    lines.append(f"└{'─' * (width - 2)}┘")
    return "\n".join(lines)


def visualize_connection(
    source_id: int,
    target_id: int,
    relation: str,
    strength: float = 1.0,
) -> str:
    """Create ASCII visualization of a connection."""
    # Strength bar
    bar_len = int(min(strength, 5) * 4)
    bar = "█" * bar_len + "░" * (20 - bar_len)
    
    arrow = f"{colored(str(source_id), Colors.CYAN)} ─────{colored(relation, Colors.MAGENTA)}─────▶ {colored(str(target_id), Colors.CYAN)}"
    strength_line = f"Strength: [{bar}] {strength:.2f}"
    
    return f"{arrow}\n{dim(strength_line)}"


def visualize_stats(stats: "CardStats") -> str:
    """Visualize card statistics."""
    # Strength gauge
    strength_bar = int(min(stats.strength, 10) * 2)
    strength_viz = colored("█" * strength_bar, Colors.GREEN) + dim("░" * (20 - strength_bar))
    
    lines = [
        f"Card #{stats.card_id} Stats:",
        f"  Strength:   [{strength_viz}] {stats.strength:.2f}",
        f"  Recalls:    {stats.recall_count}",
        f"  Last:       {stats.last_recalled or 'Never'}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Debug Printer
# ---------------------------------------------------------------------------

class DebugPrinter:
    """Pretty printer for AB entities with color support."""
    
    def __init__(self, output=None, colors: bool = True):
        """Initialize the debug printer.
        
        Args:
            output: Output stream (defaults to stdout).
            colors: Whether to use colors.
        """
        self.output = output or sys.stdout
        if not colors:
            Colors.disable()
    
    def _print(self, text: str) -> None:
        """Print to output stream."""
        print(text, file=self.output)
    
    def header(self, text: str) -> None:
        """Print a section header."""
        self._print(f"\n{colored('═' * 60, Colors.CYAN)}")
        self._print(f"{colored(' ' + text, Colors.BOLD + Colors.CYAN)}")
        self._print(f"{colored('═' * 60, Colors.CYAN)}")
    
    def subheader(self, text: str) -> None:
        """Print a subsection header."""
        self._print(f"\n{colored('─── ' + text + ' ───', Colors.BRIGHT_BLUE)}")
    
    def card(self, card: "Card", width: int = 60) -> None:
        """Print a card visualization."""
        self._print(visualize_card(card, width))
    
    def buffer(self, buf: "Buffer", width: int = 50) -> None:
        """Print a buffer visualization."""
        self._print(visualize_buffer(buf, width))
    
    def connection(
        self,
        source_id: int,
        target_id: int,
        relation: str,
        strength: float = 1.0,
    ) -> None:
        """Print a connection visualization."""
        self._print(visualize_connection(source_id, target_id, relation, strength))
    
    def stats(self, stats: "CardStats") -> None:
        """Print card statistics."""
        self._print(visualize_stats(stats))
    
    def moment(self, moment: "Moment") -> None:
        """Print a moment."""
        self._print(f"{colored('⏱', Colors.YELLOW)} Moment #{moment.id}")
        self._print(f"  Timestamp: {moment.timestamp}")
        self._print(f"  Master Input: {truncate(moment.master_input or '(none)', 50)}")
        self._print(f"  Master Output: {truncate(moment.master_output or '(none)', 50)}")
    
    def info(self, message: str) -> None:
        """Print an info message."""
        self._print(f"{colored('ℹ', Colors.BLUE)} {message}")
    
    def success(self, message: str) -> None:
        """Print a success message."""
        self._print(f"{colored('✓', Colors.GREEN)} {message}")
    
    def warning(self, message: str) -> None:
        """Print a warning message."""
        self._print(f"{colored('⚠', Colors.YELLOW)} {message}")
    
    def error(self, message: str) -> None:
        """Print an error message."""
        self._print(f"{colored('✗', Colors.RED)} {message}")
    
    def table(self, headers: List[str], rows: List[List[Any]]) -> None:
        """Print a formatted table."""
        if not rows:
            return
        
        # Calculate column widths
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))
        
        # Print header
        header_line = " │ ".join(
            colored(h.ljust(widths[i]), Colors.BOLD)
            for i, h in enumerate(headers)
        )
        self._print(f"│ {header_line} │")
        
        # Separator
        sep = "─┼─".join("─" * w for w in widths)
        self._print(f"├─{sep}─┤")
        
        # Print rows
        for row in rows:
            row_line = " │ ".join(
                str(cell).ljust(widths[i])
                for i, cell in enumerate(row)
            )
            self._print(f"│ {row_line} │")
    
    def graph(self, memory: "ABMemory", center_card_id: int, depth: int = 2) -> None:
        """Print a connection graph around a card."""
        from .rfs_recall import get_connection_graph
        
        graph = get_connection_graph(memory, center_card_id, depth)
        
        self.subheader(f"Connection Graph (center={center_card_id}, depth={depth})")
        
        for card_id, connections in graph.items():
            card = memory.get_card(card_id)
            marker = colored("●", Colors.GREEN) if card_id == center_card_id else colored("○", Colors.CYAN)
            self._print(f"  {marker} Card #{card_id} ({card.label})")
            for target_id, relation in connections:
                self._print(f"      └─{colored(relation, Colors.MAGENTA)}─▶ #{target_id}")


# ---------------------------------------------------------------------------
# Tracing Decorator
# ---------------------------------------------------------------------------

def trace(func: Callable = None, *, show_args: bool = True, show_result: bool = True):
    """Decorator to trace function calls with timing.
    
    Usage:
        @trace
        def my_function():
            pass
        
        @trace(show_args=False)
        def my_other_function():
            pass
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            name = f"{f.__module__}.{f.__name__}"
            
            # Print entry
            if show_args:
                args_str = ", ".join(
                    [repr(a)[:30] for a in args] +
                    [f"{k}={repr(v)[:20]}" for k, v in kwargs.items()]
                )
                print(f"{colored('→', Colors.CYAN)} {colored(name, Colors.BOLD)}({args_str})")
            else:
                print(f"{colored('→', Colors.CYAN)} {colored(name, Colors.BOLD)}()")
            
            # Execute
            start = time.perf_counter()
            try:
                result = f(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                
                # Print exit
                if show_result and result is not None:
                    result_str = truncate(repr(result), 50)
                    print(f"{colored('←', Colors.GREEN)} {name} = {result_str} {dim(f'({elapsed:.2f}ms)')}")
                else:
                    print(f"{colored('←', Colors.GREEN)} {name} {dim(f'({elapsed:.2f}ms)')}")
                
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                print(f"{colored('✗', Colors.RED)} {name} raised {type(e).__name__}: {e} {dim(f'({elapsed:.2f}ms)')}")
                raise
        
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator


# ---------------------------------------------------------------------------
# Memory Inspector
# ---------------------------------------------------------------------------

class MemoryInspector:
    """Interactive inspector for AB memory state."""
    
    def __init__(self, memory: "ABMemory"):
        self.memory = memory
        self.printer = DebugPrinter()
    
    def summary(self) -> None:
        """Print a summary of memory contents."""
        self.printer.header("Memory Summary")
        
        # Count entities
        cur = self.memory.conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM moments")
        moments = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM cards")
        cards = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM buffers")
        buffers = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM connections")
        connections = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM selves")
        selves = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM subscriptions")
        subscriptions = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM card_stats")
        stats = cur.fetchone()[0]
        
        self.printer.table(
            ["Entity", "Count"],
            [
                ["Moments", moments],
                ["Cards", cards],
                ["Buffers", buffers],
                ["Connections", connections],
                ["Selves", selves],
                ["Subscriptions", subscriptions],
                ["Card Stats", stats],
            ]
        )
    
    def list_cards(self, label: Optional[str] = None, limit: int = 10) -> None:
        """List cards with optional filtering."""
        self.printer.subheader(f"Cards (label={label or 'all'}, limit={limit})")
        
        cur = self.memory.conn.cursor()
        if label:
            cur.execute(
                "SELECT id, label, owner_self FROM cards WHERE label = ? LIMIT ?",
                (label, limit)
            )
        else:
            cur.execute("SELECT id, label, owner_self FROM cards LIMIT ?", (limit,))
        
        rows = cur.fetchall()
        self.printer.table(
            ["ID", "Label", "Owner"],
            [[r["id"], r["label"], r["owner_self"] or "-"] for r in rows]
        )
    
    def inspect_card(self, card_id: int) -> None:
        """Detailed inspection of a single card."""
        card = self.memory.get_card(card_id)
        self.printer.card(card)
        
        # Show connections
        connections = self.memory.list_connections(card_id=card_id)
        if connections:
            self.printer.subheader("Connections")
            for conn in connections:
                self.printer.connection(
                    conn["source_card_id"],
                    conn["target_card_id"],
                    conn["relation"],
                    conn["strength"]
                )
        
        # Show stats
        stats = self.memory.get_card_stats(card_id)
        self.printer.subheader("Memory Stats")
        self.printer.stats(stats)


# Global printer instance for convenience
printer = DebugPrinter()
