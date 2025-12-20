"""
Mathematical Discovery: Prime Numbers ℙ

From what we know:
- Natural numbers: 0, 1, 2, 3, 4, 5, ...
- Multiplication exists and is commutative & associative
- We can test divisibility

Question: What are the building blocks of multiplication?
- Which numbers can be factored?
- Which numbers are "atomic" (cannot be broken down)?
- Are there infinitely many primes? ∞
- How are primes distributed?

Let's discover primes through experimentation! 🔢
"""

import asyncio
from supe import Supe
from ab.models import Buffer


async def main():
    print("=" * 80)
    print("🔢 MATHEMATICAL DISCOVERY: Prime Numbers ℙ")
    print("=" * 80)
    print()

    supe = Supe(db_path=":memory:")

    # Seed basic knowledge
    print("📚 Seeding knowledge...")
    prime_def = """Prime number: A natural number > 1 that has no positive divisors other than 1 and itself.

Examples:
- 2 is prime (only divisors: 1, 2)
- 3 is prime (only divisors: 1, 3)
- 4 is NOT prime (divisors: 1, 2, 4) - we say 4 = 2 x 2
- 5 is prime (only divisors: 1, 5)
- 6 is NOT prime (6 = 2 x 3)
- 7 is prime
- 8 is NOT prime (8 = 2 x 2 x 2)
- 9 is NOT prime (9 = 3 x 3)

Composite number: A natural number > 1 that is NOT prime (can be factored)."""

    supe.memory.store_card(
        label="definition",
        buffers=[Buffer(
            name="content",
            payload=prime_def.encode('utf-8')
        )],
        master_output="Prime numbers defined with examples",
        track="awareness",
    )
    print("✓ Primes defined\n")

    # Discovery 1: Is 2 the only even prime?
    print("🔍 DISCOVERY 1: Is 2 the only even prime?")
    print("-" * 80)
    print("Question: Are all even numbers > 2 composite?")
    print("Test cases: 4 = 2×2, 6 = 2×3, 8 = 2×4, 10 = 2×5, ...")
    print()

    result1 = await supe.learn(
        "Is 2 the only even prime? (Are all even numbers > 2 composite?)",
        mode="explore"
    )

    if result1['beliefs_count'] > 0:
        status = result1['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result1['confidence']:.2f}")
        if status == 'PROVEN':
            print("⟹ Every even number n > 2 can be written as n = 2k for some k > 1")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 2: Fundamental theorem - every number has prime factorization
    print("🔍 DISCOVERY 2: Can every composite be factored into primes?")
    print("-" * 80)
    print("Question: Does every composite number have a unique prime factorization?")
    print("Examples:")
    print("  12 = 2 × 2 × 3 = 2² × 3")
    print("  30 = 2 × 3 × 5")
    print("  100 = 2 × 2 × 5 × 5 = 2² × 5²")
    print()

    result2 = await supe.learn(
        "Can 12 be factored into primes? (12 = 2 × 2 × 3?)",
        mode="explore"
    )

    if result2['beliefs_count'] > 0:
        status = result2['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result2['confidence']:.2f}")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 3: Prime gaps - can we find consecutive numbers both composite?
    print("🔍 DISCOVERY 3: Can we find large gaps between primes?")
    print("-" * 80)
    print("Question: Can we find two consecutive odd numbers that are both composite?")
    print("Example: 9 and 11 → 9 is composite (3×3), but 11 is prime")
    print("What about: 21 and 23 → 21 = 3×7 (composite), 23 is prime")
    print("What about: 25 and 27 → 25 = 5×5, 27 = 3³ → BOTH composite! ✓")
    print()

    result3 = await supe.learn(
        "Are 25 and 27 both composite? (25 = 5×5 and 27 = 3×3×3?)",
        mode="explore"
    )

    if result3['beliefs_count'] > 0:
        status = result3['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result3['confidence']:.2f}")
        if status == 'PROVEN':
            print("⟹ Prime gaps exist! Primes become sparser as numbers grow larger")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 4: Twin primes
    print("🔍 DISCOVERY 4: Do twin primes exist?")
    print("-" * 80)
    print("Twin primes: Two primes that differ by 2")
    print("Examples: (3,5), (5,7), (11,13), (17,19), (29,31), (41,43)...")
    print("Question: Are 11 and 13 both prime?")
    print()

    result4 = await supe.learn(
        "Are 11 and 13 both prime? (Twin primes?)",
        mode="explore"
    )

    if result4['beliefs_count'] > 0:
        status = result4['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result4['confidence']:.2f}")
        if status == 'PROVEN':
            print("⟹ Twin primes exist!")
            print("Open question: Are there infinitely many twin primes? (Unsolved!)")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 5: Is 1 prime?
    print("🔍 DISCOVERY 5: Is 1 a prime number?")
    print("-" * 80)
    print("Question: Does 1 satisfy the definition of prime?")
    print("Definition: 'A prime is > 1 and has no divisors except 1 and itself'")
    print("1's divisors: only 1")
    print()

    result5 = await supe.learn(
        "Is 1 a prime number? (Does 1 satisfy the definition?)",
        mode="explore"
    )

    if result5['beliefs_count'] > 0:
        status = result5['beliefs'][0]['content']['status']
        print(f"Result: {status}")
        print(f"Confidence: {result5['confidence']:.2f}")
        if status == 'DISPROVEN':
            print("⟹ 1 is NOT prime! (Definition requires n > 1)")
            print("⟹ This keeps unique prime factorization working")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 6: Sum of two primes
    print("🔍 DISCOVERY 6: Can even numbers be expressed as sum of two primes?")
    print("-" * 80)
    print("Goldbach's Conjecture: Every even integer > 2 is the sum of two primes")
    print("Examples:")
    print("  4 = 2 + 2")
    print("  6 = 3 + 3")
    print("  8 = 3 + 5")
    print("  10 = 3 + 7 = 5 + 5")
    print("  12 = 5 + 7")
    print()
    print("Question: Can 10 be written as the sum of two primes?")
    print()

    result6 = await supe.learn(
        "Can 10 be written as 5 + 5, where both are prime?",
        mode="explore"
    )

    if result6['beliefs_count'] > 0:
        status = result6['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result6['confidence']:.2f}")
        if status == 'PROVEN':
            print("⟹ At least some even numbers can be expressed as sum of two primes!")
            print("⟹ Goldbach's Conjecture remains unproven for ALL even numbers")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Summary
    print("=" * 80)
    print("🎓 PRIME NUMBER DISCOVERIES")
    print("=" * 80)
    print()
    print("What we explored:")
    print()
    print("1️⃣  Unique Even Prime: 2 is the only even prime")
    print("2️⃣  Prime Factorization: Every composite has a prime factorization")
    print("3️⃣  Prime Gaps: Gaps between primes can be arbitrarily large")
    print("4️⃣  Twin Primes: Pairs of primes that differ by 2 (e.g., 11, 13)")
    print("5️⃣  One is Not Prime: 1 doesn't count as prime (by definition)")
    print("6️⃣  Goldbach's Observation: Some evens = sum of two primes")
    print()
    print("🏆 Famous Open Problems:")
    print("  • Twin Prime Conjecture: Infinitely many twin primes?")
    print("  • Goldbach's Conjecture: Every even > 2 = sum of two primes?")
    print("  • Riemann Hypothesis: Distribution of primes (ζ(s) zeros)")
    print()
    print("💡 Next Horizons:")
    print("  • Prime density: π(n) ~ n/ln(n)")
    print("  • Mersenne primes: 2ᵖ - 1")
    print("  • Perfect numbers: σ(n) = 2n")
    print("  • Modular arithmetic: ℤ/nℤ")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
