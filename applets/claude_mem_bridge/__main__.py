"""Run the memory card viewer.

Usage:
    python -m applets.claude_mem_bridge tui           # Terminal UI
    python -m applets.claude_mem_bridge web           # Web UI (default)
    python -m applets.claude_mem_bridge               # Web UI

Neural Visualization:
    python -m applets.claude_mem_bridge neural        # Stats dashboard
    python -m applets.claude_mem_bridge neural map    # Network map
    python -m applets.claude_mem_bridge neural tree 54  # Connection tree for card
    python -m applets.claude_mem_bridge neural branches # Fundamental branches
    python -m applets.claude_mem_bridge neural recall "query"  # Run recall & show results
"""

import sys


def neural_cli(args):
    """Neural memory visualization CLI."""
    from .neural import NeuralMemory
    from .bridge import ClaudeMemBridge
    from . import neural_viz

    # Initialize bridge and neural memory
    print("Loading neural memory...")
    bridge = ClaudeMemBridge()
    bridge.import_all(limit=2000)

    neural = NeuralMemory()

    # Add cards to neural memory
    for card_id, card in bridge.cards.items():
        # Convert MemoryCard to buffer dict for neural memory
        buffers = {
            'title': card.buffers.get_text('title'),
            'type': card.buffers.get_text('type'),
            'narrative': card.buffers.get_text('narrative'),
            'project': card.buffers.get_text('project'),
        }
        neural.add_card(card_id, buffers)

    # Wire up persisted links to cards
    neural._load_from_db()

    print(f"Loaded {len(neural.cards)} cards, {len(neural.links)} persisted links")
    print()

    if not args or args[0] == "stats":
        # Default: show stats dashboard
        print(neural_viz.show_stats(neural))

    elif args[0] == "map":
        # Network overview map
        print(neural_viz.show_map(neural))

    elif args[0] == "tree":
        # Connection tree for a specific card
        if len(args) < 2:
            print("Usage: neural tree <card_id>")
            return
        card_id = int(args[1])
        print(neural_viz.show_tree(neural, card_id))

    elif args[0] == "branches":
        # Fundamental branches
        print(neural_viz.show_branches(neural))

    elif args[0] == "recall":
        # Run a recall query and show results
        if len(args) < 2:
            print("Usage: neural recall <query>")
            return

        query = " ".join(args[1:])
        print(f"Running recall: '{query}'")
        print()

        results = neural.recall(query, top_k=10)

        # Show results as pathway
        pathway_cards = []
        for card_id, activation in results:
            card = neural.cards.get(card_id)
            if card:
                pathway_cards.append({
                    'card_id': card_id,
                    'title': card.buffers.get('title', '?'),
                    'strength': activation,
                    'is_hub': card.is_hub,
                })

        print(neural_viz.render_pathway(pathway_cards, f"RECALL: {query[:30]}"))
        print()
        print(f"Neural links after recall: {len(neural.links)}")
        print(f"Persisted to: {neural.db_path}")

    elif args[0] == "hubs":
        # Show hub cards
        hubs = neural.get_hubs(10)
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║                         HUB CARDS                                ║")
        print("║                 (most connected memory nodes)                    ║")
        print("╠══════════════════════════════════════════════════════════════════╣")
        for card_id, card in hubs:
            title = card.buffers.get('title', '?')[:40]
            conn = card.connectivity
            recalls = card.recall_count
            bar = neural_viz.strength_bar(min(1.0, conn / 50), 10)
            print(f"║  #{card_id:<4} {title:<40} {bar} {conn:>2}c ║")
        print("╚══════════════════════════════════════════════════════════════════╝")

    elif args[0] == "persist":
        # Show persistence stats
        stats = neural.get_stats()
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║                      PERSISTENCE STATUS                          ║")
        print("╠══════════════════════════════════════════════════════════════════╣")
        print(f"║  Database:        {stats['db_path']:<45} ║")
        print(f"║  Persisted links: {stats['persisted_links']:<45} ║")
        print(f"║  Persisted cards: {stats['persisted_cards']:<45} ║")
        print(f"║  Strong links:    {stats['strong_links']:<45} ║")
        print(f"║  Total queries:   {stats['total_queries']:<45} ║")
        print("╚══════════════════════════════════════════════════════════════════╝")

    else:
        print(f"Unknown neural command: {args[0]}")
        print("Available: stats, map, tree <id>, branches, recall <query>, hubs, persist")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "web"

    if mode == "tui":
        from .tui import main as tui_main
        tui_main()
    elif mode == "web":
        from .web import main as web_main
        web_main()
    elif mode == "neural":
        neural_cli(sys.argv[2:])
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python -m applets.claude_mem_bridge [tui|web|neural]")
        print()
        print("Neural commands:")
        print("  neural              # Stats dashboard")
        print("  neural map          # Network overview")
        print("  neural tree <id>    # Connection tree for card")
        print("  neural branches     # Strongest pathways")
        print("  neural recall <q>   # Run recall query")
        print("  neural hubs         # Hub cards")
        print("  neural persist      # Persistence status")
        sys.exit(1)


if __name__ == "__main__":
    main()
