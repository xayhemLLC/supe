#!/usr/bin/env python3
"""Test Neural Memory with real claude-mem data.

Usage:
    python scripts/test_neural_memory.py
    python scripts/test_neural_memory.py --query "OAuth authentication"
    python scripts/test_neural_memory.py --interactive
"""

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ab.neural_memory import NeuralMemory


def load_from_claude_mem(limit: int = 1000) -> NeuralMemory:
    """Load observations from claude-mem into neural memory."""
    db_path = Path.home() / ".claude-mem" / "claude-mem.db"

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, type, title, subtitle, narrative, concepts, project,
               created_at, created_at_epoch
        FROM observations
        ORDER BY id DESC
        LIMIT ?
    ''', (limit,))

    mem = NeuralMemory()

    for row in cursor.fetchall():
        buffers = {
            'title': row['title'] or '',
            'type': row['type'] or '',
            'subtitle': row['subtitle'] or '',
            'narrative': row['narrative'] or '',
            'concepts': row['concepts'] or '',
            'project': row['project'] or '',
            'created_at': row['created_at'] or '',
        }
        mem.add_card(row['id'], buffers)

    conn.close()
    return mem


def train_with_queries(mem: NeuralMemory, queries: list[str]):
    """Train the network by running queries."""
    print("Training neural pathways...")
    for q in queries:
        results = mem.recall(q, top_k=5)
        print(f"  '{q}' -> {len(results)} activated")
    print()


def show_results(mem: NeuralMemory):
    """Display neural memory analysis."""
    print("=" * 60)
    print("NEURAL MEMORY ANALYSIS")
    print("=" * 60)

    print(f"\nCards loaded: {len(mem.cards)}")
    print(f"Unique concepts: {len(mem.concept_index)}")
    print(f"Neural links: {len(mem.links)}")

    # Hub cards
    print("\n--- HUB CARDS (Most Connected) ---")
    for card_id, card in mem.get_hubs(5):
        title = card.buffers.get('title', '?')[:50]
        proj = card.buffers.get('project', '?')
        print(f"  [{card.connectivity:3} conn, {card.recall_count:2} recalls] {title}")
        print(f"       Project: {proj}")

    # Fundamental branches
    print("\n--- FUNDAMENTAL BRANCHES (Highways) ---")
    branches = mem.find_fundamental_branches()[:10]
    if branches:
        for b in branches:
            print(f"  {b['from'][:25]:25} <-> {b['to'][:25]:25}")
            print(f"       strength={b['strength']:.2f}, activations={b['activations']}")
    else:
        print("  (No strong pathways formed yet - try more queries)")

    # Consolidation stats
    print("\n--- CONSOLIDATION ---")
    stats = mem.consolidate()
    print(f"  Pruned {stats['pruned_links']} weak links")
    print(f"  Remaining: {stats['total_links']} links, {stats['total_cards']} cards")


def interactive_mode(mem: NeuralMemory):
    """Interactive query mode."""
    print("\nInteractive Neural Memory Search")
    print("Type 'quit' to exit, 'hubs' to see hubs, 'branches' to see highways")
    print("-" * 40)

    while True:
        try:
            query = input("\nQuery> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if not query:
            continue
        if query.lower() == 'quit':
            break
        if query.lower() == 'hubs':
            for card_id, card in mem.get_hubs(5):
                title = card.buffers.get('title', '?')[:50]
                print(f"  [{card.connectivity} conn] {title}")
            continue
        if query.lower() == 'branches':
            for b in mem.find_fundamental_branches()[:5]:
                print(f"  {b['from'][:30]} -> {b['to'][:30]} (str={b['strength']:.2f})")
            continue

        results = mem.recall(query, top_k=5)
        print(f"\nResults for '{query}':")
        for card_id, activation in results:
            card = mem.cards[card_id]
            title = card.buffers.get('title', '?')[:50]
            proj = card.buffers.get('project', '?')
            print(f"  {activation:.2f} | {title}")
            print(f"         Project: {proj}")


def main():
    parser = argparse.ArgumentParser(description="Test Neural Memory with claude-mem data")
    parser.add_argument("--limit", type=int, default=1000, help="Max observations to load")
    parser.add_argument("--query", "-q", help="Single query to run")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")

    args = parser.parse_args()

    print(f"Loading {args.limit} observations from claude-mem...")
    mem = load_from_claude_mem(args.limit)
    print(f"Loaded {len(mem.cards)} cards with {len(mem.concept_index)} unique concepts\n")

    # Default training queries to build pathways
    training_queries = [
        "OAuth authentication login",
        "authentication token refresh",
        "API endpoint security",
        "OAuth authentication",
        "database schema migration",
        "error handling debugging",
        "OAuth authentication",
        "user profile settings",
        "authentication session",
        "OAuth authentication",
        "bugfix error fix",
        "feature implementation",
        "refactor code cleanup",
    ]

    train_with_queries(mem, training_queries)

    if args.query:
        results = mem.recall(args.query, top_k=10)
        print(f"\nResults for '{args.query}':")
        for card_id, activation in results:
            card = mem.cards[card_id]
            title = card.buffers.get('title', '?')[:55]
            proj = card.buffers.get('project', '?')
            print(f"  {activation:.2f} | [{proj:12}] {title}")

    elif args.interactive:
        show_results(mem)
        interactive_mode(mem)

    else:
        show_results(mem)

        # Demo query
        print("\n--- DEMO QUERY ---")
        query = "user authentication flow"
        results = mem.recall(query, top_k=5)
        print(f"Query: '{query}'")
        for card_id, activation in results:
            card = mem.cards[card_id]
            title = card.buffers.get('title', '?')[:50]
            print(f"  {activation:.2f} | {title}")


if __name__ == "__main__":
    main()
