"""
Debug the learning process to understand gaps and state transitions.

This runs a simple mathematical discovery with full debug output to show:
- Exact state transitions
- Knowledge gaps identified
- Confidence calculations
- AB Memory storage
"""

import asyncio
from supe import Supe
from ab.models import Buffer


async def main():
    print("=" * 80)
    print("🔍 DEBUG: Learning Process Analysis")
    print("=" * 80)
    print()

    # Use persistent database to inspect later
    db_path = ".tascer/debug_learning.db"
    supe = Supe(db_path=db_path)

    print(f"📁 Database: {db_path}")
    print()

    # Seed some mathematical knowledge
    print("📚 Seeding mathematical knowledge...")

    math_def = """Set Theory: Foundation of Mathematics

Sets: Collections of distinct objects
- Notation: A = {1, 2, 3}
- Empty set: ∅ = {}
- Universal set: U (all objects under consideration)

Set Operations:
- Union: A ∪ B = {x : x ∈ A or x ∈ B}
- Intersection: A ∩ B = {x : x ∈ A and x ∈ B}
- Difference: A - B = {x : x ∈ A and x ∉ B}
- Complement: A' = {x : x ∈ U and x ∉ A}

Properties:
- Commutative: A ∪ B = B ∪ A
- Associative: (A ∪ B) ∪ C = A ∪ (B ∪ C)
- Distributive: A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)
- De Morgan's Laws: (A ∪ B)' = A' ∩ B'

Subset: A ⊆ B means every element of A is in B
Proper subset: A ⊂ B means A ⊆ B and A ≠ B"""

    supe.memory.store_card(
        label="set_theory_basics",
        buffers=[Buffer(name="content", payload=math_def.encode('utf-8'))],
        master_output="Set theory definitions",
        track="awareness",
    )
    print("✓ Set theory seeded\n")

    # Now learn with EXPLORE mode
    print("🔬 Starting EXPLORE mode learning...")
    print("Question: Is set union commutative?")
    print()

    result = await supe.learn(
        "Is set union commutative? (Is A ∪ B = B ∪ A?)",
        mode="explore"
    )

    print("\n" + "=" * 80)
    print("📊 LEARNING RESULT")
    print("=" * 80)
    print()
    print(f"Session ID: {result['session_id']}")
    print(f"Beliefs created: {result['beliefs_count']}")
    print()

    if result['beliefs_count'] > 0:
        for i, belief in enumerate(result['beliefs'], 1):
            print(f"Belief {i}:")
            content = belief['content']
            print(f"  Status: {content['status']}")
            print(f"  Confidence: {result['confidence']:.2f}")
            print(f"  Statement: {content.get('statement', 'N/A')[:80]}...")
            print(f"  Proof: {content.get('proof', 'N/A')[:80]}...")
            print()

    # Now inspect the AB Memory
    print("=" * 80)
    print("💾 AB MEMORY INSPECTION")
    print("=" * 80)
    print()

    # Query for learning artifacts
    print("📋 Learning Sessions:")
    sessions = supe.memory.find_cards_by_label("learning_context")
    print(f"  Found {len(sessions)} sessions")

    print("\n📝 Questions:")
    questions = supe.memory.find_cards_by_label("learning_question")
    print(f"  Found {len(questions)} questions")

    print("\n🔬 Evidence:")
    evidence = supe.memory.find_cards_by_label("learning_evidence")
    print(f"  Found {len(evidence)} evidence items")

    print("\n💡 Beliefs:")
    beliefs = supe.memory.find_cards_by_label("learning_belief")
    print(f"  Found {len(beliefs)} beliefs")
    print()

    # Examine the most recent session in detail
    if sessions:
        print("=" * 80)
        print("🔍 DETAILED SESSION INSPECTION")
        print("=" * 80)
        print()

        session = sessions[-1]
        print(f"Session Card ID: {session.id}")
        print(f"Created: {session.created_at}")
        print()

        # Decode session data
        import json
        for buf in session.buffers:
            if buf.name == "context":
                try:
                    ctx = json.loads(buf.payload.decode('utf-8'))

                    print(f"📍 Session ID: {ctx['session_id'][:16]}...")
                    print(f"🎯 Mode: {ctx['mode']}")
                    print(f"⚡ State: {ctx['current_state']}")
                    print()

                    print("❗ KNOWLEDGE GAPS:")
                    gaps = ctx.get('gaps', [])
                    if gaps:
                        for i, gap in enumerate(gaps, 1):
                            print(f"  {i}. {gap}")
                    else:
                        print("  None identified")
                    print()

                    print("❓ QUESTION QUEUE:")
                    queue = ctx.get('question_queue', [])
                    print(f"  {len(queue)} questions pending")
                    for i, q in enumerate(queue[:3], 1):
                        print(f"  {i}. {q['text'][:60]}...")
                    print()

                    print("💭 BELIEFS CREATED:")
                    beliefs_data = ctx.get('beliefs_created', [])
                    print(f"  {len(beliefs_data)} beliefs")
                    for i, b in enumerate(beliefs_data, 1):
                        print(f"  {i}. Confidence: {b.get('confidence', 0):.2f}")
                        print(f"     Evidence IDs: {len(b.get('evidence_ids', []))}")
                    print()

                    print("🔬 EVIDENCE COLLECTED:")
                    evidence_data = ctx.get('evidence_collected', [])
                    print(f"  {len(evidence_data)} evidence items")
                    for i, e in enumerate(evidence_data, 1):
                        print(f"  {i}. Source: {e.get('source', 'unknown')}")
                        print(f"     Validated: {e.get('validated', False)}")
                        print(f"     Text: {e.get('text', '')[:60]}...")
                    print()

                    print("📊 METADATA:")
                    metadata = ctx.get('metadata', {})
                    if 'explore_claim' in metadata:
                        claim = metadata['explore_claim']
                        print(f"  Property: {claim.get('property', 'N/A')}")
                        print(f"  Operation: {claim.get('operation', 'N/A')}")
                        print(f"  Hypothesis: {claim.get('hypothesis', 'N/A')[:60]}...")
                    if 'experiment_results' in metadata:
                        results = metadata['experiment_results']
                        print(f"  Experiments run: {len(results)}")
                        passed = sum(1 for r in results if r.get('passed', False))
                        print(f"  Tests passed: {passed}/{len(results)}")

                except Exception as e:
                    print(f"Error decoding session: {e}")
                    import traceback
                    traceback.print_exc()

    print()
    print("=" * 80)
    print("✅ Debug inspection complete!")
    print(f"💾 Database persisted at: {db_path}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
