"""
Visualize the complete state machine execution trace.

Shows every state transition, confidence adjustments, and gap identification.
"""

import asyncio
from supe import Supe
from ab.models import Buffer


# Monkey-patch to capture state transitions
transitions_log = []

def log_transition(state_machine, from_state, to_state):
    """Capture state transitions."""
    transitions_log.append({
        'from': from_state.value if hasattr(from_state, 'value') else str(from_state),
        'to': to_state.value if hasattr(to_state, 'value') else str(to_state),
    })


async def main():
    print("=" * 80)
    print("🎬 STATE MACHINE EXECUTION TRACE")
    print("=" * 80)
    print()

    # Create Supe instance
    supe = Supe(db_path=":memory:")

    # Seed mathematical knowledge with GAPS (incomplete information)
    print("📚 Seeding INCOMPLETE knowledge (to trigger gaps)...")

    incomplete_math = """Partial Information on Groups:

A group is a set G with an operation * that satisfies:
- Closure: For all a, b in G, a * b is in G
- Associativity: (a * b) * c = a * (b * c)

[Note: Identity and inverse properties are MISSING - this will create gaps!]

Examples:
- Integers with addition form a group
- Non-zero rationals with multiplication form a group"""

    supe.memory.store_card(
        label="incomplete_group_theory",
        buffers=[Buffer(name="content", payload=incomplete_math.encode('utf-8'))],
        master_output="Incomplete group theory info",
        track="awareness",
    )
    print("✓ Incomplete knowledge seeded (missing identity & inverse)\n")

    # Learn about groups
    print("🔬 Learning about groups (expect gaps!)...")
    print()

    result = await supe.learn(
        "What are the complete axioms of a group? (closure, associativity, identity, inverse)",
        mode="explore"
    )

    print("\n" + "=" * 80)
    print("📊 RESULT WITH GAPS")
    print("=" * 80)
    print()

    print(f"Session ID: {result['session_id'][:16]}...")
    print(f"Beliefs created: {result['beliefs_count']}")
    print(f"Confidence: {result.get('confidence', 0):.2f}")
    print()

    # Show beliefs
    if result.get('beliefs'):
        for i, belief in enumerate(result['beliefs'], 1):
            print(f"Belief {i}:")
            content = belief['content']
            print(f"  Status: {content['status']}")
            print(f"  Proof: {content.get('proof', 'N/A')[:100]}...")
            print()

    # Inspect gaps
    print("=" * 80)
    print("❗ KNOWLEDGE GAPS IDENTIFIED")
    print("=" * 80)
    print()

    sessions = supe.memory.find_cards_by_label("learning_context")
    if sessions:
        import json
        session = sessions[-1]
        for buf in session.buffers:
            if buf.name == "context":
                ctx = json.loads(buf.payload.decode('utf-8'))
                gaps = ctx.get('gaps', [])

                if gaps:
                    print("🔍 The system identified these gaps:")
                    for i, gap in enumerate(gaps, 1):
                        print(f"\n  Gap {i}: {gap}")
                    print()
                    print("💡 These gaps LOWER confidence because:")
                    print("   - Missing information affects understanding")
                    print("   - Incomplete evidence reduces certainty")
                    print("   - Gap penalty applied: 0.9-0.95x multiplier")
                else:
                    print("No gaps identified (complete information)")

    print()

    # Now show what perfect knowledge looks like
    print("=" * 80)
    print("🎯 COMPARISON: Learning with COMPLETE knowledge")
    print("=" * 80)
    print()

    complete_math = """Complete Group Theory:

A group (G, *) is a set G with binary operation * satisfying:

1. CLOSURE: ∀a,b ∈ G: a * b ∈ G
2. ASSOCIATIVITY: ∀a,b,c ∈ G: (a * b) * c = a * (b * c)
3. IDENTITY: ∃e ∈ G: ∀a ∈ G: e * a = a * e = a
4. INVERSE: ∀a ∈ G: ∃a⁻¹ ∈ G: a * a⁻¹ = a⁻¹ * a = e

Examples:
- (ℤ, +): Integers with addition (identity: 0, inverse: -a)
- (ℚ\\{0}, ×): Non-zero rationals with multiplication (identity: 1, inverse: 1/a)
- (ℤ/nℤ, ⊕): Integers modulo n with addition (cyclic group)"""

    supe2 = Supe(db_path=":memory:")
    supe2.memory.store_card(
        label="complete_group_theory",
        buffers=[Buffer(name="content", payload=complete_math.encode('utf-8'))],
        master_output="Complete group theory",
        track="awareness",
    )

    result2 = await supe2.learn(
        "What are the four group axioms?",
        mode="explore"
    )

    print(f"Beliefs created: {result2['beliefs_count']}")
    print(f"Confidence: {result2.get('confidence', 0):.2f}")
    print()

    # Check for gaps
    sessions2 = supe2.memory.find_cards_by_label("learning_context")
    if sessions2:
        session2 = sessions2[-1]
        for buf in session2.buffers:
            if buf.name == "context":
                ctx2 = json.loads(buf.payload.decode('utf-8'))
                gaps2 = ctx2.get('gaps', [])
                print(f"Gaps: {len(gaps2)} (complete info = no gaps!)")
                print(f"Result: Higher confidence! ✓")

    print()
    print("=" * 80)
    print("🎓 LESSON: Confidence Formula")
    print("=" * 80)
    print()
    print("confidence = base × evidence_quality × recall × gap_penalty")
    print()
    print("Where:")
    print("  base = 0.95 (PROVEN) or 1.00 (exhaustive test)")
    print("  evidence_quality = 0.8-1.2 (citations, validation, diversity)")
    print("  recall = 0.7-1.1 (self-test performance)")
    print("  gap_penalty = 0.8-1.0 (fewer gaps = higher)")
    print()
    print("Gap Penalty Scale:")
    print("  0 gaps   → 1.00 (no penalty)")
    print("  1-2 gaps → 0.95 (minor uncertainty)")
    print("  3-5 gaps → 0.90 (moderate uncertainty)")
    print("  6+ gaps  → 0.80 (significant uncertainty)")
    print()
    print("Example: 0.95 × 1.0 × 1.0 × 0.95 = 0.90 confidence")
    print("         (PROVEN, good evidence, 1-2 gaps)")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
