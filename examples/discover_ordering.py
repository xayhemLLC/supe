"""
Mathematical Discovery: Ordering and Comparison

From what we know:
- Zero and nonzero exist
- Addition and multiplication exist
- We've proven commutativity and associativity

Next fundamental question: Can we order numbers?
- What does "less than" mean?
- Is ordering transitive? (if a < b and b < c, then a < c?)
- Is ordering antisymmetric? (if a < b, then NOT b < a?)
- Total order? (for any a, b: either a < b, a = b, or a > b?)

Let's discover order properties through experimentation with cool symbols! ⊕ ⊗ ≺ ≻ ⊆ ⊇
"""

import asyncio
from supe import Supe
from ab.models import Buffer


async def main():
    print("=" * 80)
    print("🔢 MATHEMATICAL DISCOVERY: Ordering and Comparison")
    print("=" * 80)
    print()
    print("Using symbols: ≺ (less than), ≻ (greater than), ⊕ (addition), ⊗ (multiplication)")
    print()

    supe = Supe(db_path=":memory:")

    # Seed knowledge about ordering
    print("📚 Seeding knowledge about numbers and ordering...")
    supe.memory.store_card(
        label="axiom",
        buffers=[Buffer(
            name="content",
            payload=b"Natural numbers: 0, 1, 2, 3, 4, 5, ... We say a < b (a is less than b) if there exists a positive number k such that a + k = b."
        )],
        master_output="Natural numbers and less-than relation defined",
        track="awareness",
    )
    print("✓ Number system established\n")

    # Discovery 1: Is < transitive?
    print("🔍 DISCOVERY 1: Is ordering transitive?")
    print("-" * 80)
    print("Question: If a ≺ b and b ≺ c, then is a ≺ c?")
    print("Symbolic: (a ≺ b) ∧ (b ≺ c) ⟹ (a ≺ c)?")
    print()

    result1 = await supe.learn(
        "Is the less-than relation transitive? (If 2 < 5 and 5 < 9, then 2 < 9?)",
        mode="explore"
    )

    if result1['beliefs_count'] > 0:
        status = result1['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result1['confidence']:.2f}")
    else:
        print("Result: NO BELIEF FORMED ⚠️")
    print()

    # Discovery 2: Asymmetry
    print("🔍 DISCOVERY 2: Is ordering asymmetric?")
    print("-" * 80)
    print("Question: If a ≺ b, then is it true that NOT (b ≺ a)?")
    print("Symbolic: (a ≺ b) ⟹ ¬(b ≺ a)?")
    print()

    result2 = await supe.learn(
        "Is less-than asymmetric? (If 3 < 7, then NOT 7 < 3?)",
        mode="explore"
    )

    if result2['beliefs_count'] > 0:
        status = result2['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result2['confidence']:.2f}")
    else:
        print("Result: NO BELIEF FORMED ⚠️")
    print()

    # Discovery 3: Trichotomy (total order)
    print("🔍 DISCOVERY 3: Does trichotomy hold?")
    print("-" * 80)
    print("Question: For any two numbers, exactly one is true: a ≺ b, a = b, or a ≻ b?")
    print("Symbolic: ∀a,b: (a ≺ b) ⊕ (a = b) ⊕ (b ≺ a)  [exactly one is true]")
    print()

    result3 = await supe.learn(
        "Does trichotomy hold? (For any two numbers a and b, exactly one is true: a < b, a = b, or a > b?)",
        mode="explore"
    )

    if result3['beliefs_count'] > 0:
        status = result3['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result3['confidence']:.2f}")
    else:
        print("Result: NO BELIEF FORMED ⚠️")
    print()

    # Discovery 4: Addition preserves order
    print("🔍 DISCOVERY 4: Does addition preserve order?")
    print("-" * 80)
    print("Question: If a ≺ b, then is (a ⊕ c) ≺ (b ⊕ c) for any c?")
    print("Symbolic: (a ≺ b) ⟹ (a ⊕ c ≺ b ⊕ c)?")
    print()

    result4 = await supe.learn(
        "Does addition preserve order? (If 2 < 5, then 2 + 10 < 5 + 10?)",
        mode="explore"
    )

    if result4['beliefs_count'] > 0:
        status = result4['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result4['confidence']:.2f}")
    else:
        print("Result: NO BELIEF FORMED ⚠️")
    print()

    # Discovery 5: Multiplication by positive preserves order
    print("🔍 DISCOVERY 5: Does multiplication by positive preserve order?")
    print("-" * 80)
    print("Question: If a ≺ b and c ≻ 0, then is (a ⊗ c) ≺ (b ⊗ c)?")
    print("Symbolic: (a ≺ b) ∧ (c ≻ 0) ⟹ (a ⊗ c ≺ b ⊗ c)?")
    print()

    result5 = await supe.learn(
        "Does multiplication by positive preserve order? (If 2 < 5 and k > 0, then 2 × k < 5 × k?)",
        mode="explore"
    )

    if result5['beliefs_count'] > 0:
        status = result5['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result5['confidence']:.2f}")
    else:
        print("Result: NO BELIEF FORMED ⚠️")
    print()

    # Discovery 6: Can we compare sums?
    print("🔍 DISCOVERY 6: Comparison of sums")
    print("-" * 80)
    print("Question: If a ≺ b and c ≺ d, then is (a ⊕ c) ≺ (b ⊕ d)?")
    print("Symbolic: (a ≺ b) ∧ (c ≺ d) ⟹ (a ⊕ c ≺ b ⊕ d)?")
    print()

    result6 = await supe.learn(
        "Are sums monotonic? (If 2 < 5 and 3 < 7, then 2 + 3 < 5 + 7?)",
        mode="explore"
    )

    if result6['beliefs_count'] > 0:
        status = result6['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result6['confidence']:.2f}")
    else:
        print("Result: NO BELIEF FORMED ⚠️")
    print()

    # Summary
    print("=" * 80)
    print("🎓 ORDERING DISCOVERIES")
    print("=" * 80)
    print()
    print("Order Properties Explored:")
    print()
    print("1️⃣  Transitivity: (a ≺ b) ∧ (b ≺ c) ⟹ (a ≺ c)")
    print("2️⃣  Asymmetry: (a ≺ b) ⟹ ¬(b ≺ a)")
    print("3️⃣  Trichotomy: Exactly one of {a ≺ b, a = b, b ≺ a} is true")
    print("4️⃣  Addition Preservation: (a ≺ b) ⟹ (a ⊕ c ≺ b ⊕ c)")
    print("5️⃣  Multiplication Preservation: (a ≺ b) ∧ (c ≻ 0) ⟹ (a ⊗ c ≺ b ⊗ c)")
    print("6️⃣  Sum Monotonicity: (a ≺ b) ∧ (c ≺ d) ⟹ (a ⊕ c ≺ b ⊕ d)")
    print()
    print("💡 These properties define a TOTALLY ORDERED FIELD!")
    print()
    print("Next Horizons:")
    print("  🔹 Well-ordering principle: Every nonempty set has a least element")
    print("  🔹 Completeness: Does every bounded set have a supremum?")
    print("  🔹 Density: Between any two numbers, is there another?")
    print("  🔹 Archimedean property: For any a, b > 0, ∃n such that n·a > b")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
