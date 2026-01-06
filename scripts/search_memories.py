#!/usr/bin/env python3
"""Search Claude Memories - Ready-to-run script.

Usage:
    python scripts/search_memories.py "your search query"
    python scripts/search_memories.py --semantic "OAuth authentication"
    python scripts/search_memories.py --hybrid "error handling"
    python scripts/search_memories.py --project utils.gg --type bugfix
    python scripts/search_memories.py --similar 95  # Find cards similar to ID 95
    python scripts/search_memories.py --file "settings/page.tsx"
    python scripts/search_memories.py --session 720cb3e4-1ee5...
    python scripts/search_memories.py --stats
"""

import argparse
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ab.claude_mem_bridge import ClaudeMemBridge, ClaudeMemConfig


def main():
    parser = argparse.ArgumentParser(description="Search Claude Memories")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--semantic", action="store_true", help="Use semantic search")
    parser.add_argument("--hybrid", action="store_true", help="Use hybrid search (semantic + keyword + recency)")
    parser.add_argument("--project", "-p", help="Filter by project")
    parser.add_argument("--type", "-t", help="Filter by type (feature, bugfix, discovery, etc.)")
    parser.add_argument("--similar", type=int, help="Find cards similar to this card ID")
    parser.add_argument("--file", "-f", help="Search by file path pattern")
    parser.add_argument("--session", "-s", help="Get all cards from a session")
    parser.add_argument("--tags", help="Filter by tags (comma-separated)")
    parser.add_argument("--limit", "-n", type=int, default=10, help="Max results")
    parser.add_argument("--stats", action="store_true", help="Show database stats")
    parser.add_argument("--threshold", type=float, default=0.15, help="Similarity threshold")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Initialize bridge
    config = ClaudeMemConfig(
        auto_link=True,
        auto_link_min_words=3,
        import_embeddings=True,
        embedding_provider="tfidf"
    )

    print("Loading memories...", end=" ", flush=True)
    bridge = ClaudeMemBridge(config)
    result = bridge.import_all(project=args.project, limit=5000)
    print(f"Done ({result['imported']} cards, {result['links_created']} links)")
    print()

    # Stats mode
    if args.stats:
        show_stats(bridge)
        return

    # Session mode
    if args.session:
        search_by_session(bridge, args.session, args.verbose)
        return

    # File search mode
    if args.file:
        search_by_file(bridge, args.file, args.limit, args.verbose)
        return

    # Similar cards mode
    if args.similar:
        find_similar(bridge, args.similar, args.limit, args.threshold, args.verbose)
        return

    # Query required for other modes
    if not args.query:
        parser.print_help()
        return

    # Hybrid search (default for queries)
    if args.hybrid or (not args.semantic):
        hybrid_search(bridge, args.query, args.project, args.limit, args.verbose)

    # Semantic search
    elif args.semantic:
        semantic_search(bridge, args.query, args.project, args.limit, args.threshold, args.verbose)


def show_stats(bridge):
    """Show database statistics."""
    stats = bridge.get_stats()

    print("=== Memory Statistics ===")
    print(f"Cards loaded:     {stats['tree_web']['cards']}")
    print(f"Concept links:    {stats['tree_web']['links']}")
    print(f"Moments (time):   {stats['tree_web']['moments']}")

    if "claude_mem" in stats:
        print(f"Total in DB:      {stats['claude_mem'].get('observations', 'N/A')}")

    # Type breakdown
    type_counts = {}
    project_counts = {}
    for card in bridge.tree_web.cards.values():
        t = card.buffers.get("type", "unknown")
        p = card.buffers.get("project", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
        project_counts[p] = project_counts.get(p, 0) + 1

    print("\n=== By Type ===")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t:15} {count}")

    print("\n=== By Project ===")
    for p, count in sorted(project_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {p:20} {count}")


def hybrid_search(bridge, query, project, limit, verbose):
    """Run hybrid search."""
    print(f"=== Hybrid Search: '{query}' ===")
    if project:
        print(f"    Project filter: {project}")
    print()

    results = bridge.hybrid_search(query, top_k=limit, project=project)

    for r in results:
        title = r.get("title", "N/A")
        obs_type = r.get("type", "?")
        proj = r.get("project", "?")
        final = r.get("final_score", 0)

        print(f"[{obs_type:10}] {title[:60]}")
        print(f"             Project: {proj} | Score: {final:.3f}")

        if verbose:
            sem = r.get("semantic_score", 0)
            kw = r.get("keyword_score", 0)
            rec = r.get("recency_score", 0)
            print(f"             (semantic={sem:.2f} keyword={kw:.2f} recency={rec:.2f})")
        print()


def semantic_search(bridge, query, project, limit, threshold, verbose):
    """Run semantic search."""
    print(f"=== Semantic Search: '{query}' ===")
    print(f"    Threshold: {threshold}")
    if project:
        print(f"    Project: {project}")
    print()

    results = bridge.semantic_search(query, top_k=limit, threshold=threshold, project=project)

    for r in results:
        title = r.get("title", "N/A")
        obs_type = r.get("obs_type", "?")
        sim = r.get("similarity", 0)
        proj = r.get("project", "?")

        print(f"[{obs_type:10}] {title[:60]}")
        print(f"             Project: {proj} | Similarity: {sim:.3f}")
        print()


def find_similar(bridge, card_id, limit, threshold, verbose):
    """Find similar cards."""
    if card_id not in bridge._obs_to_card:
        # Try direct card ID
        if card_id not in bridge.tree_web.cards:
            print(f"Card ID {card_id} not found")
            return
        internal_id = card_id
    else:
        internal_id = bridge._obs_to_card[card_id]

    card = bridge.tree_web.cards.get(internal_id)
    if not card:
        print(f"Card {card_id} not found in tree-web")
        return

    ref_title = card.buffers.get("title", "N/A")
    print(f"=== Cards Similar To ===")
    print(f"    [{card_id}] {ref_title[:60]}")
    print()

    results = bridge.find_similar_cards(internal_id, top_k=limit, threshold=threshold)

    for r in results:
        title = r.get("title", "N/A")
        sim = r.get("similarity", 0)
        proj = r.get("project", "?")

        print(f"  {sim:.3f} | {title[:55]}")
        if verbose:
            print(f"         Project: {proj}")


def search_by_file(bridge, file_pattern, limit, verbose):
    """Search by file path."""
    print(f"=== Files Matching: '{file_pattern}' ===")
    print()

    matches = []
    for card_id, card in bridge.tree_web.cards.items():
        files = card.buffers.get("files_modified", [])
        if isinstance(files, str):
            files = [files]

        for f in files:
            if file_pattern.lower() in f.lower():
                matches.append((card_id, card, f))

    # Sort by timestamp
    matches.sort(key=lambda x: x[1].buffers.get("created_at_epoch", 0), reverse=True)

    for card_id, card, matched_file in matches[:limit]:
        title = card.buffers.get("title", "N/A")
        obs_type = card.buffers.get("type", "?")
        created = card.buffers.get("created_at", "?")[:10]

        print(f"[{obs_type:10}] {title[:50]}")
        print(f"             File: {matched_file}")
        print(f"             Date: {created}")
        print()


def search_by_session(bridge, session_id, verbose):
    """Get all cards from a session."""
    print(f"=== Session: {session_id[:20]}... ===")
    print()

    matches = []
    for card_id, card in bridge.tree_web.cards.items():
        if session_id in str(card.buffers.get("session", "")):
            matches.append((card_id, card))

    # Sort by timestamp
    matches.sort(key=lambda x: x[1].buffers.get("created_at_epoch", 0))

    print(f"Found {len(matches)} cards in session")
    print()

    for card_id, card in matches:
        title = card.buffers.get("title", "N/A")
        obs_type = card.buffers.get("type", "?")
        created = card.buffers.get("created_at", "?")[11:19]  # Time only

        print(f"  {created} [{obs_type:10}] {title[:50]}")


if __name__ == "__main__":
    main()
