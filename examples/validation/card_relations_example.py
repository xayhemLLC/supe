"""Example: Card Relations in AB Memory

This demonstrates how typed relations between cards would enable
sophisticated reasoning, causal analysis, and knowledge graphs.

This is a PROPOSAL/PROTOTYPE - relations are not yet implemented in AB Memory.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional


class RelationType(Enum):
    """Types of relations between cards."""
    CAUSES = "causes"              # A caused B
    IMPLIES = "implies"            # If A then B
    CONTRADICTS = "contradicts"    # A and B cannot both be true
    EQUALS = "equals"              # A and B are the same thing
    TRANSFORMS = "transforms"      # A evolved into B
    SUPPORTS = "supports"          # A provides evidence for B
    DEPENDS_ON = "depends_on"      # B requires A
    REFINES = "refines"           # B adds detail to A
    INVALIDATES = "invalidates"    # B makes A obsolete
    GENERALIZES = "generalizes"    # B is general case of A


@dataclass
class Relation:
    """A typed relation between two cards."""
    id: str
    type: RelationType
    source_card_id: int
    target_card_id: int
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))

    def __repr__(self):
        return f"Relation({self.source_card_id} --{self.type.value}-> {self.target_card_id}, conf={self.confidence})"


# Mock card class for demonstration
@dataclass
class MockCard:
    id: int
    label: str


def example_1_causal_debugging():
    """Example 1: Causal chain in debugging."""
    print("=" * 70)
    print("EXAMPLE 1: CAUSAL CHAIN IN DEBUGGING")
    print("=" * 70)

    # Create cards representing debugging process
    cards = {
        1: MockCard(1, "Code Change: Removed null check in SessionManager"),
        2: MockCard(2, "Merged PR #456"),
        3: MockCard(3, "Deployed to production"),
        4: MockCard(4, "User Report: App crashes on logout"),
        5: MockCard(5, "Investigation: Null pointer in cleanup()"),
        6: MockCard(6, "Root Cause: Missing null check"),
        7: MockCard(7, "Fix: Re-added null check"),
        8: MockCard(8, "Regression Test: test_logout_with_expired_session()"),
    }

    # Build causal chain
    relations = [
        Relation("r1", RelationType.CAUSES, 1, 2, confidence=1.0),
        Relation("r2", RelationType.CAUSES, 2, 3, confidence=1.0),
        Relation("r3", RelationType.CAUSES, 3, 4, confidence=0.9),
        Relation("r4", RelationType.CAUSES, 4, 5, confidence=1.0),
        Relation("r5", RelationType.CAUSES, 5, 6, confidence=0.95),
        Relation("r6", RelationType.CAUSES, 6, 7, confidence=1.0),
        Relation("r7", RelationType.CAUSES, 7, 8, confidence=1.0),
    ]

    print("\n📊 Causal Graph:")
    for r in relations:
        source = cards[r.source_card_id]
        target = cards[r.target_card_id]
        print(f"\n  {source.label}")
        print(f"    ↓ {r.type.value.upper()} (conf={r.confidence})")
        print(f"  {target.label}")

    # Trace back to root cause
    print("\n\n🔍 Root Cause Analysis:")
    print(f"   Starting from: {cards[4].label}")
    print(f"   Tracing back through CAUSES relations...")

    current_id = 4
    depth = 0
    while current_id in [r.target_card_id for r in relations]:
        # Find relation that targets current card
        rel = next((r for r in relations if r.target_card_id == current_id), None)
        if not rel:
            break
        depth += 1
        print(f"   {'  ' * depth}← Caused by: {cards[rel.source_card_id].label}")
        current_id = rel.source_card_id

    print(f"\n   ✓ Root Cause: {cards[1].label}")


def example_2_logical_inference():
    """Example 2: Logical inference chain."""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 2: LOGICAL INFERENCE CHAIN")
    print("=" * 70)

    cards = {
        10: MockCard(10, "Requirement: Support 10,000 users"),
        11: MockCard(11, "Implication: Need horizontal scaling"),
        12: MockCard(12, "Implication: Need load balancer"),
        13: MockCard(13, "Implication: Need stateless architecture"),
        14: MockCard(14, "Implication: Need distributed sessions"),
        15: MockCard(15, "Design Decision: Use Redis for sessions"),
    }

    relations = [
        Relation("i1", RelationType.IMPLIES, 10, 11, confidence=0.95),
        Relation("i2", RelationType.IMPLIES, 11, 12, confidence=0.9),
        Relation("i3", RelationType.IMPLIES, 11, 13, confidence=0.85),
        Relation("i4", RelationType.IMPLIES, 13, 14, confidence=0.9),
        Relation("i5", RelationType.IMPLIES, 14, 15, confidence=0.8),
    ]

    print("\n📊 Inference Chain:")
    print(f"\n  Given: {cards[10].label}")

    # Build inference tree
    def find_implications(card_id, depth=0):
        implications = [r for r in relations if r.source_card_id == card_id]
        for rel in implications:
            target = cards[rel.target_card_id]
            print(f"  {'  ' * depth}→ IMPLIES: {target.label} (conf={rel.confidence})")
            find_implications(rel.target_card_id, depth + 1)

    find_implications(10)

    # Calculate transitive confidence
    print("\n\n🎯 Transitive Inference:")
    print(f"   From: {cards[10].label}")
    print(f"   To: {cards[15].label}")

    # Path: 10 → 11 → 13 → 14 → 15
    path_confidence = 0.95 * 0.85 * 0.9 * 0.8
    print(f"   Path confidence: {path_confidence:.2%}")
    print(f"   ✓ Therefore: {cards[15].label} (with {path_confidence:.2%} confidence)")


def example_3_contradiction_detection():
    """Example 3: Detecting contradictions."""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 3: CONTRADICTION DETECTION")
    print("=" * 70)

    cards = {
        20: MockCard(20, "Belief: API latency is <100ms"),
        21: MockCard(21, "Measurement: Actual latency is 250ms"),
        22: MockCard(22, "Design: Synchronous processing"),
        23: MockCard(23, "Requirement: Must handle 1M requests/sec"),
        24: MockCard(24, "Hypothesis: Bug is in database query"),
        25: MockCard(25, "Evidence: All database queries pass tests"),
    }

    contradictions = [
        Relation("c1", RelationType.CONTRADICTS, 20, 21, confidence=0.95, metadata={"detected": "2024-01-15"}),
        Relation("c2", RelationType.CONTRADICTS, 22, 23, confidence=0.9, metadata={"detected": "2024-01-16"}),
        Relation("c3", RelationType.CONTRADICTS, 24, 25, confidence=0.85, metadata={"detected": "2024-01-17"}),
    ]

    print("\n⚠️  Detected Contradictions:\n")

    for rel in contradictions:
        source = cards[rel.source_card_id]
        target = cards[rel.target_card_id]
        print(f"  ❌ Contradiction #{rel.id}:")
        print(f"     Card A: {source.label}")
        print(f"     Card B: {target.label}")
        print(f"     Confidence: {rel.confidence:.2%}")
        print(f"     → Requires belief revision!\n")

    print("  💡 Resolution Actions:")
    print("     1. Update belief based on new measurement")
    print("     2. Revise design to meet requirements")
    print("     3. Eliminate hypothesis, form new one")


def example_4_evidence_support_network():
    """Example 4: Evidence supporting beliefs."""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 4: EVIDENCE SUPPORT NETWORK")
    print("=" * 70)

    cards = {
        30: MockCard(30, "Belief: Caching improves performance"),
        31: MockCard(31, "Evidence: Benchmark shows 60% reduction"),
        32: MockCard(32, "Evidence: Load test: 50k req/sec"),
        33: MockCard(33, "Evidence: User survey: 90% satisfied"),
        34: MockCard(34, "Evidence: Metrics: Cache hit rate 85%"),
        35: MockCard(35, "Evidence: Profiling: 70% time saved"),
    }

    support_relations = [
        Relation("s1", RelationType.SUPPORTS, 31, 30, confidence=0.95),
        Relation("s2", RelationType.SUPPORTS, 32, 30, confidence=0.9),
        Relation("s3", RelationType.SUPPORTS, 33, 30, confidence=0.7),
        Relation("s4", RelationType.SUPPORTS, 34, 30, confidence=0.85),
        Relation("s5", RelationType.SUPPORTS, 35, 30, confidence=0.9),
    ]

    print(f"\n💡 Belief: {cards[30].label}")
    print(f"\n📊 Supporting Evidence:\n")

    total_support = 0
    for rel in support_relations:
        source = cards[rel.source_card_id]
        print(f"   ✓ {source.label}")
        print(f"     Support strength: {rel.confidence:.2%}\n")
        total_support += rel.confidence

    avg_support = total_support / len(support_relations)
    print(f"   Average support: {avg_support:.2%}")
    print(f"   Number of sources: {len(support_relations)}")
    print(f"   Overall confidence: {min(0.99, avg_support * 1.1):.2%}")


def example_5_task_dependencies():
    """Example 5: Task dependency graph."""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 5: TASK DEPENDENCY GRAPH")
    print("=" * 70)

    cards = {
        40: MockCard(40, "Task: Design architecture"),
        41: MockCard(41, "Task: Write tests"),
        42: MockCard(42, "Task: Implement feature"),
        43: MockCard(43, "Task: Code review"),
        44: MockCard(44, "Task: Deploy to staging"),
        45: MockCard(45, "Task: QA testing"),
        46: MockCard(46, "Task: Deploy to production"),
    }

    dependencies = [
        Relation("d1", RelationType.DEPENDS_ON, 41, 40),
        Relation("d2", RelationType.DEPENDS_ON, 42, 40),
        Relation("d3", RelationType.DEPENDS_ON, 42, 41),
        Relation("d4", RelationType.DEPENDS_ON, 43, 42),
        Relation("d5", RelationType.DEPENDS_ON, 44, 43),
        Relation("d6", RelationType.DEPENDS_ON, 45, 44),
        Relation("d7", RelationType.DEPENDS_ON, 46, 45),
    ]

    print("\n📋 Task Dependency Graph:\n")

    # Topological sort
    def topological_sort(cards, relations):
        # Build adjacency list
        in_degree = {cid: 0 for cid in cards}
        adj = {cid: [] for cid in cards}

        for rel in relations:
            adj[rel.target_card_id].append(rel.source_card_id)
            in_degree[rel.source_card_id] += 1

        # Find nodes with no dependencies
        queue = [cid for cid, deg in in_degree.items() if deg == 0]
        order = []

        while queue:
            current = queue.pop(0)
            order.append(current)

            # Remove edges
            for neighbor in adj[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return order

    execution_order = topological_sort(cards, dependencies)

    print("  Execution Order:")
    for i, card_id in enumerate(execution_order, 1):
        card = cards[card_id]
        deps = [r.target_card_id for r in dependencies if r.source_card_id == card_id]
        if deps:
            dep_labels = [cards[d].label for d in deps]
            print(f"  {i}. {card.label}")
            print(f"     ↑ depends on: {', '.join(dep_labels)}")
        else:
            print(f"  {i}. {card.label} (no dependencies)")


def example_6_knowledge_evolution():
    """Example 6: Knowledge transformation over time."""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 6: KNOWLEDGE EVOLUTION")
    print("=" * 70)

    cards = {
        50: MockCard(50, "Initial Hypothesis: Bug is in frontend"),
        51: MockCard(51, "Revised Hypothesis: Bug is in API"),
        52: MockCard(52, "Final Understanding: Bug is in database"),
        53: MockCard(53, "Root Cause: Missing index on users table"),
        54: MockCard(54, "Solution: Add composite index"),
    }

    transformations = [
        Relation("t1", RelationType.TRANSFORMS, 50, 51, metadata={"reason": "Frontend tests all pass"}),
        Relation("t2", RelationType.TRANSFORMS, 51, 52, metadata={"reason": "API logs show slow queries"}),
        Relation("t3", RelationType.REFINES, 52, 53, metadata={"reason": "Query profiling"}),
        Relation("t4", RelationType.CAUSES, 53, 54, metadata={"reason": "Index improves query 10x"}),
    ]

    print("\n🔄 Evolution Chain:\n")

    current_id = 50
    for i, rel in enumerate(transformations, 1):
        source = cards[rel.source_card_id]
        target = cards[rel.target_card_id]
        reason = rel.metadata.get("reason", "N/A")

        print(f"  Step {i}: {source.label}")
        print(f"     ↓ {rel.type.value.upper()}: {reason}")
        print(f"  → {target.label}\n")

    print("  💡 Key Insight: Knowledge evolved from vague hypothesis")
    print("     to specific solution through iterative refinement")


def main():
    """Run all relation examples."""
    example_1_causal_debugging()
    example_2_logical_inference()
    example_3_contradiction_detection()
    example_4_evidence_support_network()
    example_5_task_dependencies()
    example_6_knowledge_evolution()

    print("\n\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("""
Typed relations between cards enable:

1. ✅ Causal Reasoning - Trace causes to root sources
2. ✅ Logical Inference - Derive new knowledge from implications
3. ✅ Contradiction Detection - Find inconsistencies automatically
4. ✅ Evidence Networks - Quantify belief support strength
5. ✅ Dependency Management - Order tasks, detect cycles
6. ✅ Knowledge Evolution - Track how understanding changes

This transforms AB Memory from a flat card store into a rich
semantic network capable of sophisticated reasoning.

Next Steps:
- Implement Relation as Atom type (pindex=12)
- Add relation storage to ABMemory
- Build query API (get_relations, find_path, etc.)
- Integrate with evidence-based validation
- Create visualization tools
    """)
    print("=" * 70)


if __name__ == "__main__":
    main()
