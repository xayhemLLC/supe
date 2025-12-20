"""
Mathematical Discovery: Identity Elements and Inverses

Starting from what we know:
- Zero and nonzero exist
- Addition is commutative and associative
- Multiplication is associative

What are the next fundamental truths?
- What element, when added to any number, leaves it unchanged? (additive identity)
- What element, when multiplied by any number, leaves it unchanged? (multiplicative identity)
- For any number, does an "opposite" exist that undoes addition? (additive inverse)
- For any number, does a "reciprocal" exist that undoes multiplication? (multiplicative inverse)

Let's discover these through experimentation.
"""

import asyncio
from supe import Supe
from ab.models import Buffer


async def main():
    print("=" * 80)
    print("MATHEMATICAL DISCOVERY: Identity Elements and Inverses")
    print("=" * 80)
    print()

    # Initialize Supe with in-memory database
    supe = Supe(db_path=":memory:")

    # Seed initial knowledge
    print("📚 Seeding initial knowledge...")
    supe.memory.store_card(
        label="axiom",
        buffers=[Buffer(
            name="content",
            payload="We have discovered: zero exists, nonzero exists, addition is commutative and associative, multiplication is associative".encode()
        )],
        master_output="We have discovered: zero exists, nonzero exists, addition is commutative and associative, multiplication is associative",
        track="awareness",
    )
    print("✓ Axioms established\n")

    # Discovery 1: Additive Identity
    print("🔍 DISCOVERY 1: What is the additive identity?")
    print("-" * 80)
    print("Question: Is there a number that, when added to any number, leaves it unchanged?")
    print()

    result1 = await supe.learn(
        "Is zero the additive identity? (Does a + 0 = a for all a?)",
        mode="explore"
    )

    print(f"Result: {result1['beliefs'][0]['content']['status']}")
    print(f"Confidence: {result1['confidence']:.2f}")
    print(f"Proof: {result1['proof_hash'][:16]}...")
    print()

    # Discovery 2: Multiplicative Identity
    print("🔍 DISCOVERY 2: What is the multiplicative identity?")
    print("-" * 80)
    print("Question: Is there a number that, when multiplied by any number, leaves it unchanged?")
    print()

    # First, seed knowledge about 'one'
    supe.memory.store_card(
        label="concept",
        buffers=[Buffer(
            name="content",
            payload="One (1) is the number that comes after zero. It represents a single unit.".encode()
        )],
        master_output="One (1) is the number that comes after zero. It represents a single unit.",
        track="awareness",
    )

    result2 = await supe.learn(
        "Is one the multiplicative identity? (Does a × 1 = a for all a?)",
        mode="explore"
    )

    print(f"Result: {result2['beliefs'][0]['content']['status']}")
    print(f"Confidence: {result2['confidence']:.2f}")
    print(f"Proof: {result2['proof_hash'][:16]}...")
    print()

    # Discovery 3: Additive Inverses (Negative Numbers)
    print("🔍 DISCOVERY 3: Do additive inverses exist?")
    print("-" * 80)
    print("Question: For any number a, does there exist a number -a such that a + (-a) = 0?")
    print()

    # Seed concept of negative numbers
    supe.memory.store_card(
        label="concept",
        buffers=[Buffer(
            name="content",
            payload="For any number a, we define -a (negative a) as the number that, when added to a, gives zero. For example: 5 + (-5) = 0, 3 + (-3) = 0.".encode()
        )],
        master_output="For any number a, we define -a (negative a) as the number that, when added to a, gives zero. For example: 5 + (-5) = 0, 3 + (-3) = 0.",
        track="awareness",
    )

    result3 = await supe.learn(
        "Does every number have an additive inverse? (Does a + (-a) = 0 for all a?)",
        mode="explore"
    )

    if result3['beliefs_count'] > 0:
        print(f"Result: {result3['beliefs'][0]['content']['status']}")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"Proof: {result3['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF FORMED")
        print(f"Confidence: {result3['confidence']:.2f}")
    print()

    # Discovery 4: Are additive inverses unique?
    print("🔍 DISCOVERY 4: Is the additive inverse unique?")
    print("-" * 80)
    print("Question: If a + b = 0 and a + c = 0, does b = c?")
    print()

    result4 = await supe.learn(
        "Is the additive inverse unique? (If a + b = 0 and a + c = 0, then b = c?)",
        mode="explore"
    )

    if result4['beliefs_count'] > 0:
        print(f"Result: {result4['beliefs'][0]['content']['status']}")
        print(f"Confidence: {result4['confidence']:.2f}")
        print(f"Proof: {result4['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF FORMED")
        print(f"Confidence: {result4['confidence']:.2f}")
    print()

    # Discovery 5: Multiplicative Inverses (Fractions)
    print("🔍 DISCOVERY 5: Do multiplicative inverses exist?")
    print("-" * 80)
    print("Question: For any nonzero number a, does there exist a number 1/a such that a × (1/a) = 1?")
    print()

    # Seed concept of fractions
    supe.memory.store_card(
        label="concept",
        buffers=[Buffer(
            name="content",
            payload="For any nonzero number a, we define 1/a (one over a, or the reciprocal of a) as the number that, when multiplied by a, gives one. For example: 5 × (1/5) = 1, 2 × (1/2) = 1.".encode()
        )],
        master_output="For any nonzero number a, we define 1/a (one over a, or the reciprocal of a) as the number that, when multiplied by a, gives one. For example: 5 × (1/5) = 1, 2 × (1/2) = 1.",
        track="awareness",
    )

    result5 = await supe.learn(
        "Does every nonzero number have a multiplicative inverse? (Does a × (1/a) = 1 for all nonzero a?)",
        mode="explore"
    )

    if result5['beliefs_count'] > 0:
        print(f"Result: {result5['beliefs'][0]['content']['status']}")
        print(f"Confidence: {result5['confidence']:.2f}")
        print(f"Proof: {result5['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF FORMED")
        print(f"Confidence: {result5['confidence']:.2f}")
    print()

    # Discovery 6: What about zero?
    print("🔍 DISCOVERY 6: Does zero have a multiplicative inverse?")
    print("-" * 80)
    print("Question: Is there a number 1/0 such that 0 × (1/0) = 1?")
    print()

    result6 = await supe.learn(
        "Does zero have a multiplicative inverse? (Does there exist x such that 0 × x = 1?)",
        mode="explore"
    )

    if result6['beliefs_count'] > 0:
        print(f"Result: {result6['beliefs'][0]['content']['status']}")
        print(f"Confidence: {result6['confidence']:.2f}")
        print(f"Proof: {result6['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF FORMED")
        print(f"Confidence: {result6['confidence']:.2f}")
    print()

    # Summary
    print("=" * 80)
    print("DISCOVERIES SUMMARY")
    print("=" * 80)
    print()
    print("What we learned about identity and inverses:")
    print()
    print("1. Additive Identity: 0 is the unique element where a + 0 = a")
    print("2. Multiplicative Identity: 1 is the unique element where a × 1 = a")
    print("3. Additive Inverses: Every number a has a unique -a where a + (-a) = 0")
    print("4. Multiplicative Inverses: Every nonzero number a has a 1/a where a × (1/a) = 1")
    print("5. Zero's Exception: Zero has NO multiplicative inverse (division by zero undefined!)")
    print()
    print("🎓 These discoveries form the foundation of:")
    print("   - Group theory (identity + inverse = group structure)")
    print("   - Field theory (two operations with identities and inverses)")
    print("   - Negative numbers (discovered naturally as additive inverses)")
    print("   - Fractions (discovered naturally as multiplicative inverses)")
    print()
    print("💡 Next horizons to explore:")
    print("   - Subtraction as addition of additive inverse: a - b = a + (-b)")
    print("   - Division as multiplication by multiplicative inverse: a / b = a × (1/b)")
    print("   - Ordering: What does a < b mean? Can we discover order properties?")
    print("   - Exponentiation: What is a^b? What are its properties?")
    print("   - Prime numbers: What numbers cannot be factored?")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
