#!/usr/bin/env python3
"""List all problem solver capabilities."""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from supe.reasoning.scripts.capability_manager import CapabilityManager


def main():
    """List all capabilities."""
    manager = CapabilityManager()

    capabilities = manager.list_capabilities()
    stats = manager.get_stats()

    print("=" * 70)
    print("PROBLEM SOLVER CAPABILITIES")
    print("=" * 70)

    if not capabilities:
        print("\n  No capabilities registered yet.")
        print("\n  To register capabilities, run:")
        print("    python -m supe.reasoning.scripts.register_capability")
        return

    print(f"\n  Total: {stats['total']}")
    print(f"  Average Success Rate: {stats['avg_success_rate']*100:.1f}%")
    print(f"  Total Usage: {stats['total_usage']}")
    if stats['most_used']:
        print(f"  Most Used: {stats['most_used']}")

    print("\n" + "-" * 70)
    print("REGISTERED CAPABILITIES")
    print("-" * 70)

    for i, cap in enumerate(capabilities, 1):
        print(f"\n{i}. {cap.name}")
        print(f"   ID: {cap.id}")
        print(f"   Description: {cap.description}")
        print(f"   Tags: {', '.join(cap.tags)}")
        print(f"   Matches: {', '.join(cap.problem_patterns[:5])}", end="")
        if len(cap.problem_patterns) > 5:
            print(f" ... (+{len(cap.problem_patterns)-5} more)")
        else:
            print()
        print(f"   Usage: {cap.usage_count} times | Success Rate: {cap.success_rate*100:.1f}%")
        if cap.last_used:
            print(f"   Last Used: {cap.last_used}")

    print("\n" + "=" * 70)

    # Show stats by tag
    if stats['by_tag']:
        print("\nBY CATEGORY:")
        for tag, count in sorted(stats['by_tag'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {tag}: {count}")

    print()


if __name__ == "__main__":
    main()
