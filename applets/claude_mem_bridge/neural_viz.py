"""ASCII Visualization for Neural Memory Networks.

Beautiful terminal-based visualizations of neural connections,
hubs, pathways, and network topology.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math

# Box drawing characters
BOX = {
    'h': '─', 'v': '│',
    'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘',
    't': '┬', 'b': '┴', 'l': '├', 'r': '┤', 'x': '┼',
    'dh': '═', 'dv': '║',
    'dtl': '╔', 'dtr': '╗', 'dbl': '╚', 'dbr': '╝',
}

# Strength indicators
STRENGTH_CHARS = ['░', '▒', '▓', '█']
STRENGTH_LINES = ['╌', '─', '━', '═']

# Node symbols
NODE_SYMBOLS = {
    'hub': '◉',
    'active': '●',
    'normal': '○',
    'weak': '◌',
    'center': '◆',
}


def strength_bar(value: float, width: int = 10) -> str:
    """Create a visual strength bar."""
    filled = int(value * width)
    empty = width - filled

    if value > 0.7:
        char = '█'
    elif value > 0.4:
        char = '▓'
    elif value > 0.2:
        char = '▒'
    else:
        char = '░'

    return f"[{char * filled}{'·' * empty}]"


def render_card_node(card_id: int, title: str, is_hub: bool = False,
                     is_center: bool = False, width: int = 30) -> List[str]:
    """Render a single card as an ASCII box."""
    symbol = NODE_SYMBOLS['center'] if is_center else (NODE_SYMBOLS['hub'] if is_hub else NODE_SYMBOLS['normal'])
    title_truncated = title[:width-4] if len(title) > width-4 else title

    lines = [
        f"┌{'─' * (width-2)}┐",
        f"│ {symbol} #{card_id:<4} {'(HUB)' if is_hub else '':>6} │",
        f"│ {title_truncated:<{width-4}} │",
        f"└{'─' * (width-2)}┘",
    ]
    return lines


def render_connection_tree(center_id: int, center_title: str,
                           connections: List[Dict],
                           is_hub: bool = False) -> str:
    """Render a tree view of connections from a central node."""
    lines = []

    # Header
    lines.append("╔══════════════════════════════════════════════════════════════════╗")
    lines.append("║                     NEURAL CONNECTION TREE                       ║")
    lines.append("╚══════════════════════════════════════════════════════════════════╝")
    lines.append("")

    # Center node
    symbol = NODE_SYMBOLS['hub'] if is_hub else NODE_SYMBOLS['center']
    lines.append(f"                         ┌─────────────────────┐")
    lines.append(f"                         │ {symbol} #{center_id:<4} {'[HUB]' if is_hub else '':>8} │")
    lines.append(f"                         │ {center_title[:19]:<19} │")
    lines.append(f"                         └──────────┬──────────┘")
    lines.append(f"                                    │")

    if not connections:
        lines.append(f"                                    │")
        lines.append(f"                              (no connections)")
        return "\n".join(lines)

    # Sort by strength
    connections = sorted(connections, key=lambda x: x.get('strength', 0), reverse=True)

    # Split into left and right branches
    left = connections[:len(connections)//2]
    right = connections[len(connections)//2:]

    # Render branches
    max_rows = max(len(left), len(right))

    for i in range(max_rows):
        l_conn = left[i] if i < len(left) else None
        r_conn = right[i] if i < len(right) else None

        # Build the line
        if l_conn and r_conn:
            l_str = _format_branch_left(l_conn)
            r_str = _format_branch_right(r_conn)
            connector = "├" if i < max_rows - 1 else "└"
            lines.append(f"  {l_str} ◄──{connector}──► {r_str}")
        elif l_conn:
            l_str = _format_branch_left(l_conn)
            connector = "├" if i < max_rows - 1 else "└"
            lines.append(f"  {l_str} ◄──{connector}")
        elif r_conn:
            r_str = _format_branch_right(r_conn)
            connector = "├" if i < max_rows - 1 else "└"
            lines.append(f"                                    {connector}──► {r_str}")

    lines.append("")
    lines.append(f"  Legend: ═══ strong (>0.5)  ─── medium  ╌╌╌ weak (<0.2)")

    return "\n".join(lines)


def _format_branch_left(conn: Dict) -> str:
    """Format a left branch connection."""
    strength = conn.get('strength', 0)
    title = conn.get('title', '?')[:18]
    card_id = conn.get('target_id', 0)
    is_hub = conn.get('is_hub', False)

    symbol = NODE_SYMBOLS['hub'] if is_hub else NODE_SYMBOLS['normal']
    line = STRENGTH_LINES[min(3, int(strength * 4))]

    return f"#{card_id:<4} {title:<18} {symbol}{line * 3}"


def _format_branch_right(conn: Dict) -> str:
    """Format a right branch connection."""
    strength = conn.get('strength', 0)
    title = conn.get('title', '?')[:18]
    card_id = conn.get('target_id', 0)
    is_hub = conn.get('is_hub', False)

    symbol = NODE_SYMBOLS['hub'] if is_hub else NODE_SYMBOLS['normal']
    line = STRENGTH_LINES[min(3, int(strength * 4))]

    return f"{line * 3}{symbol} {title:<18} #{card_id}"


def render_network_map(hubs: List[Dict], total_cards: int,
                       total_links: int) -> str:
    """Render an overview map of the neural network."""
    lines = []

    lines.append("╔══════════════════════════════════════════════════════════════════════════╗")
    lines.append("║                         NEURAL NETWORK MAP                               ║")
    lines.append("╠══════════════════════════════════════════════════════════════════════════╣")
    lines.append(f"║  Total Cards: {total_cards:<6}    Total Links: {total_links:<6}    Hubs: {len(hubs):<6}         ║")
    lines.append("╠══════════════════════════════════════════════════════════════════════════╣")

    if not hubs:
        lines.append("║                         (no hubs formed yet)                              ║")
        lines.append("║              Run recall queries to build neural pathways                  ║")
        lines.append("╚══════════════════════════════════════════════════════════════════════════╝")
        return "\n".join(lines)

    # Create a visual network
    lines.append("║                                                                          ║")

    # Position hubs in a circle-like arrangement
    hub_positions = []
    center_x, center_y = 37, 4
    radius = 3

    for i, hub in enumerate(hubs[:8]):
        angle = (i / min(8, len(hubs))) * 2 * math.pi - math.pi/2
        x = int(center_x + radius * 12 * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        hub_positions.append((x, y, hub))

    # Build the visual grid
    grid_height = 10
    grid_width = 74
    grid = [[' ' for _ in range(grid_width)] for _ in range(grid_height)]

    # Draw connections between hubs
    for i, (x1, y1, hub1) in enumerate(hub_positions):
        for j, (x2, y2, hub2) in enumerate(hub_positions[i+1:], i+1):
            # Simple line between hubs
            _draw_line(grid, x1, y1, x2, y2, '·')

    # Draw hub nodes
    for x, y, hub in hub_positions:
        if 0 <= y < grid_height and 0 <= x < grid_width-2:
            connectivity = hub.get('connectivity', 0)
            symbol = '◉' if connectivity > 30 else '●'
            grid[y][x] = symbol

    # Add grid to lines
    for row in grid:
        lines.append("║ " + ''.join(row) + " ║")

    lines.append("║                                                                          ║")
    lines.append("╠══════════════════════════════════════════════════════════════════════════╣")
    lines.append("║  HUBS (most connected nodes):                                            ║")
    lines.append("║                                                                          ║")

    # List hubs with details
    for i, hub in enumerate(hubs[:6]):
        card_id = hub.get('card_id', 0)
        title = hub.get('title', '?')[:35]
        conn = hub.get('connectivity', 0)
        recalls = hub.get('recall_count', 0)
        bar = strength_bar(min(1.0, conn / 50), 8)
        lines.append(f"║  {i+1}. #{card_id:<4} {title:<35} {bar} {conn:>2}c {recalls:>2}r ║")

    lines.append("║                                                                          ║")
    lines.append("╚══════════════════════════════════════════════════════════════════════════╝")

    return "\n".join(lines)


def _draw_line(grid: List[List[str]], x1: int, y1: int, x2: int, y2: int, char: str):
    """Draw a line on the grid using Bresenham's algorithm."""
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        if 0 <= y1 < len(grid) and 0 <= x1 < len(grid[0]):
            if grid[y1][x1] == ' ':
                grid[y1][x1] = char

        if x1 == x2 and y1 == y2:
            break

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy


def render_pathway(cards: List[Dict], title: str = "NEURAL PATHWAY") -> str:
    """Render a linear pathway through connected cards."""
    lines = []

    width = 70
    lines.append(f"╔{'═' * (width-2)}╗")
    lines.append(f"║{title:^{width-2}}║")
    lines.append(f"╚{'═' * (width-2)}╝")
    lines.append("")

    if not cards:
        lines.append("  (empty pathway)")
        return "\n".join(lines)

    for i, card in enumerate(cards):
        card_id = card.get('card_id', card.get('id', 0))
        card_title = card.get('title', '?')[:40]
        strength = card.get('strength', 0)
        is_hub = card.get('is_hub', False)

        symbol = NODE_SYMBOLS['hub'] if is_hub else NODE_SYMBOLS['normal']
        bar = strength_bar(strength, 6) if strength else ""

        # Card box
        lines.append(f"  ┌{'─' * 50}┐")
        lines.append(f"  │ {symbol} #{card_id:<4} {card_title:<38} │")
        if bar:
            lines.append(f"  │   strength: {bar} {strength:.2f}{' (HUB)' if is_hub else '':>10} │")
        lines.append(f"  └{'─' * 50}┘")

        # Connector to next
        if i < len(cards) - 1:
            next_strength = cards[i+1].get('strength', 0.5)
            line_char = STRENGTH_LINES[min(3, int(next_strength * 4))]
            lines.append(f"           │")
            lines.append(f"           {line_char * 3}▼")
            lines.append(f"           │")

    return "\n".join(lines)


def render_cluster_view(clusters: Dict[str, List[int]],
                        card_titles: Dict[int, str]) -> str:
    """Render semantic clusters of cards."""
    lines = []

    lines.append("╔══════════════════════════════════════════════════════════════════╗")
    lines.append("║                      SEMANTIC CLUSTERS                           ║")
    lines.append("╠══════════════════════════════════════════════════════════════════╣")

    for topic, card_ids in list(clusters.items())[:6]:
        lines.append(f"║                                                                  ║")
        lines.append(f"║  ┌─ {topic[:40]:<40} ─────────────────┐  ║")

        # Show cards in cluster
        for card_id in card_ids[:4]:
            title = card_titles.get(card_id, '?')[:35]
            lines.append(f"║  │   ○ #{card_id:<4} {title:<35}      │  ║")

        if len(card_ids) > 4:
            lines.append(f"║  │   ... and {len(card_ids)-4} more                              │  ║")

        lines.append(f"║  └────────────────────────────────────────────────────────┘  ║")

    lines.append("║                                                                  ║")
    lines.append("╚══════════════════════════════════════════════════════════════════╝")

    return "\n".join(lines)


def render_stats_dashboard(stats: Dict) -> str:
    """Render a dashboard of neural memory statistics."""
    lines = []

    lines.append("╔══════════════════════════════════════════════════════════════════════════╗")
    lines.append("║                      NEURAL MEMORY DASHBOARD                             ║")
    lines.append("╠════════════════════════════════╦═════════════════════════════════════════╣")

    # Left column - counts
    total_cards = stats.get('total_cards', 0)
    total_links = stats.get('total_links', 0)
    persisted_links = stats.get('persisted_links', 0)
    strong_links = stats.get('strong_links', 0)
    queries = stats.get('queries', stats.get('total_queries', 0))

    lines.append(f"║  NETWORK TOPOLOGY              ║  PERSISTENCE                            ║")
    lines.append(f"║  ─────────────────             ║  ───────────                            ║")
    lines.append(f"║  Cards loaded:  {total_cards:<6}         ║  Persisted links:  {persisted_links:<6}              ║")
    lines.append(f"║  Active links:  {total_links:<6}         ║  Strong links:     {strong_links:<6}              ║")
    lines.append(f"║  Total queries: {queries:<6}         ║  Persisted cards:  {stats.get('persisted_cards', 0):<6}              ║")
    lines.append(f"║                                ║                                         ║")

    # Network density visualization
    if total_cards > 0:
        density = total_links / total_cards
        density_bar = strength_bar(min(1.0, density / 10), 20)
        lines.append(f"║  Density: {density_bar} {density:.1f}   ║  DB: ~/.claude-mem/neural.db            ║")

    lines.append("╠════════════════════════════════╩═════════════════════════════════════════╣")

    # Hebbian learning visualization
    lines.append("║  HEBBIAN LEARNING                                                        ║")
    lines.append("║  ─────────────────                                                       ║")
    lines.append("║                                                                          ║")
    lines.append("║    Query activates cards → Co-activated cards link → Links strengthen   ║")
    lines.append("║                                                                          ║")
    lines.append("║    ┌─────┐    ┌─────┐         ┌─────┐═══┌─────┐                          ║")
    lines.append("║    │  A  │    │  B  │   →→→   │  A  │   │  B  │                          ║")
    lines.append("║    └─────┘    └─────┘         └─────┘═══└─────┘                          ║")
    lines.append("║      ↑          ↑                ↑          ↑                            ║")
    lines.append("║    query      query           linked!    linked!                         ║")
    lines.append("║                                                                          ║")
    lines.append("╚══════════════════════════════════════════════════════════════════════════╝")

    return "\n".join(lines)


def render_fundamental_branches(branches: List[Dict]) -> str:
    """Render the strongest pathways (fundamental branches)."""
    lines = []

    lines.append("╔══════════════════════════════════════════════════════════════════════════╗")
    lines.append("║                      FUNDAMENTAL BRANCHES                                ║")
    lines.append("║                    (strongest memory highways)                           ║")
    lines.append("╠══════════════════════════════════════════════════════════════════════════╣")

    if not branches:
        lines.append("║                                                                          ║")
        lines.append("║  No fundamental branches yet. Keep querying to build strong pathways!   ║")
        lines.append("║                                                                          ║")
    else:
        lines.append("║                                                                          ║")

        for i, branch in enumerate(branches[:10]):
            from_title = branch.get('from', '?')[:20]
            to_title = branch.get('to', '?')[:20]
            strength = branch.get('strength', 0)
            activations = branch.get('activations', 0)
            is_hub = branch.get('is_hub_connection', False)

            # Strength-based line
            if strength > 0.7:
                line = "═══════"
                marker = "◉" if is_hub else "●"
            elif strength > 0.4:
                line = "───────"
                marker = "●"
            else:
                line = "╌╌╌╌╌╌╌"
                marker = "○"

            bar = strength_bar(strength, 6)
            lines.append(f"║  {marker} {from_title:<20} {line}► {to_title:<20} {bar}  ║")

        lines.append("║                                                                          ║")

    lines.append("╚══════════════════════════════════════════════════════════════════════════╝")

    return "\n".join(lines)


# Quick access functions for CLI
def show_tree(neural_memory, card_id: int) -> str:
    """Show connection tree for a card."""
    if card_id not in neural_memory.cards:
        return f"Card #{card_id} not found"

    card = neural_memory.cards[card_id]
    connections = []

    for target_id, link in card.outgoing.items():
        target = neural_memory.cards.get(target_id)
        if target:
            connections.append({
                'target_id': target_id,
                'title': target.buffers.get('title', '?'),
                'strength': link.strength,
                'activations': link.activation_count,
                'is_hub': target.is_hub,
            })

    return render_connection_tree(
        card_id,
        card.buffers.get('title', '?')[:20],
        connections,
        is_hub=card.is_hub
    )


def show_map(neural_memory) -> str:
    """Show network overview map."""
    hubs = []
    for card_id, card in neural_memory.get_hubs(8):
        hubs.append({
            'card_id': card_id,
            'title': card.buffers.get('title', '?'),
            'connectivity': card.connectivity,
            'recall_count': card.recall_count,
        })

    return render_network_map(
        hubs,
        len(neural_memory.cards),
        len(neural_memory.links)
    )


def show_stats(neural_memory) -> str:
    """Show stats dashboard."""
    stats = neural_memory.get_stats()
    stats['total_cards'] = len(neural_memory.cards)
    stats['total_links'] = len(neural_memory.links)
    stats['queries'] = len(neural_memory.query_history)

    return render_stats_dashboard(stats)


def show_branches(neural_memory) -> str:
    """Show fundamental branches."""
    branches = neural_memory.find_fundamental_branches()
    return render_fundamental_branches(branches)


if __name__ == "__main__":
    # Demo
    print(render_stats_dashboard({
        'total_cards': 2000,
        'total_links': 584,
        'persisted_links': 584,
        'persisted_cards': 150,
        'strong_links': 42,
        'queries': 15,
    }))
    print()
    print(render_network_map([
        {'card_id': 157, 'title': 'OAuth Authentication', 'connectivity': 50, 'recall_count': 45},
        {'card_id': 173, 'title': 'Auth Context', 'connectivity': 50, 'recall_count': 45},
        {'card_id': 54, 'title': 'Memory Card Viewer', 'connectivity': 36, 'recall_count': 45},
        {'card_id': 58, 'title': 'Memory TUI', 'connectivity': 36, 'recall_count': 45},
    ], 2000, 584))
