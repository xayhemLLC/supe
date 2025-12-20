"""
Mathematical Discovery: Number Theory - The Queen of Mathematics 👑

Number theory studies the properties of integers and has connections to
cryptography, algebra, and pure mathematics.

Core Concepts:
    • Divisibility: a | b means "a divides b" (b = ka for some integer k)
    • GCD: Greatest Common Divisor - largest number dividing both
    • LCM: Least Common Multiple - smallest number divisible by both
    • Prime factorization: Every integer > 1 has unique prime factorization
    • Euclidean Algorithm: Efficient method to compute GCD

Fundamental Theorem of Arithmetic:
    Every integer n > 1 can be written uniquely (up to order) as:
    n = p₁^a₁ × p₂^a₂ × ... × pₖ^aₖ
    where p₁, p₂, ..., pₖ are primes and a₁, a₂, ..., aₖ are positive integers

Beautiful Identities:
    • gcd(a,b) × lcm(a,b) = a × b
    • gcd(a,b) = gcd(b, a mod b) (Euclidean algorithm)
    • Bézout's identity: gcd(a,b) = ax + by for some integers x,y

Applications:
    • RSA encryption (relies on prime factorization)
    • Hash functions and checksums
    • Random number generation
    • Music theory (rhythm and harmony)
    • Scheduling problems

Let's LEARN number theory through exploration! 👑✨
"""

import asyncio
from supe import Supe
from ab.models import Buffer


def draw_divisibility():
    """Visualize divisibility."""
    return """
    Divisibility: a | b means "a divides b evenly"

    12 | 60 because 60 = 12 × 5

    Visual: 60 items in groups of 12

    ████████████  ████████████  ████████████
    ████████████  ████████████
        12            12            12
                  12        12

    5 groups of 12 = 60 ✓

    Notation: a | b ⟺ ∃k ∈ ℤ: b = ka
    """


def draw_gcd():
    """Visualize GCD as tiling."""
    return """
    GCD(18, 12) = 6 (largest square that tiles both)

    18 = 6 × 3:
    ┌──┬──┬──┐
    │6 │6 │6 │
    └──┴──┴──┘

    12 = 6 × 2:
    ┌──┬──┐
    │6 │6 │
    └──┴──┘

    GCD finds the largest "building block" common to both

    Properties:
    • gcd(a,b) | a and gcd(a,b) | b
    • If d | a and d | b, then d | gcd(a,b)
    • gcd(a,b) = gcd(b, a mod b) (Euclidean algorithm)
    """


def draw_euclidean_algorithm():
    """Visualize Euclidean algorithm."""
    return """
    Euclidean Algorithm: gcd(48, 18)

    48 = 2 × 18 + 12   ┌────────────────────────┐
                       │        48              │
                       │  ┌──────┬──────┐  ┌──┐│
                       │  │  18  │  18  │  │12││
                       │  └──────┴──────┘  └──┘│
                       └────────────────────────┘

    18 = 1 × 12 + 6    ┌──────────────┐
                       │     18       │
                       │  ┌──────┐ ┌─┐│
                       │  │  12  │ │6││
                       │  └──────┘ └─┘│
                       └──────────────┘

    12 = 2 × 6 + 0     ┌────────┐
                       │   12   │
                       │  ┌─┬─┐ │
                       │  │6│6│ │
                       │  └─┴─┘ │
                       └────────┘

    Stop when remainder = 0
    gcd(48, 18) = 6 ✓

    Algorithm: gcd(a,b) = gcd(b, a mod b)
    """


def draw_prime_factorization():
    """Visualize prime factorization."""
    return """
    Prime Factorization Tree: 60

             60
            /  \\
           2    30
               /  \\
              2    15
                  /  \\
                 3    5

    60 = 2² × 3 × 5

    Fundamental Theorem:
    Every integer > 1 has UNIQUE prime factorization!

    Examples:
    • 12 = 2² × 3
    • 18 = 2 × 3²
    • 100 = 2² × 5²
    • 2310 = 2 × 3 × 5 × 7 × 11 (primorial)
    """


def draw_lcm():
    """Visualize LCM."""
    return """
    LCM(6, 8) = 24 (smallest common multiple)

    Multiples of 6: 6, 12, 18, 24, 30, 36...
                              ^^
    Multiples of 8: 8, 16, 24, 32, 40...
                         ^^

    First overlap: 24

    Visual timeline:
    6:  •─────•─────•─────•─────•
        0     6     12    18    24

    8:  •───────•───────•───────•
        0       8       16      24

    Both align at 24!

    Formula: lcm(a,b) = (a × b) / gcd(a,b)
    """


def draw_bezout():
    """Visualize Bézout's identity."""
    return """
    Bézout's Identity: gcd(a,b) = ax + by

    Example: gcd(18, 12) = 6
    Can we write 6 = 18x + 12y?

    18 = 1 × 12 + 6
    ⟹ 6 = 18 - 1 × 12
    ⟹ 6 = 18(1) + 12(-1)  ✓

    So: x = 1, y = -1

    Visual (using 18 and 12 as lengths):
    18 - 12 = 6
    ├──────────────────┤
    ├────────────┤ ├────┤
         12         6

    Applications:
    • Solving linear Diophantine equations
    • Finding modular inverses
    • Extended Euclidean algorithm
    """


def draw_chinese_remainder():
    """Visualize Chinese Remainder Theorem."""
    return """
    Chinese Remainder Theorem (CRT)

    Find x such that:
    x ≡ 2 (mod 3)  →  x ∈ {2, 5, 8, 11, 14, 17, 20, 23...}
    x ≡ 3 (mod 5)  →  x ∈ {3, 8, 13, 18, 23, 28...}

    Visual (mod 3):
    0  1  2  3  4  5  6  7  8  9  10 11 12 13 14
    •     •     •     •     •     •      •     •

    Visual (mod 5):
    0  1  2  3  4  5  6  7  8  9  10 11 12 13 14
    •        •        •        •         •

    Overlap: x = 8, 23, 38... (general: x = 8 + 15k)

    CRT: If gcd(m,n) = 1, system has unique solution mod mn
    """


def draw_perfect_numbers():
    """Show perfect numbers."""
    return """
    Perfect Numbers: n equals sum of its proper divisors

    6 is perfect:
    Divisors: 1, 2, 3, 6
    Proper divisors: 1, 2, 3
    Sum: 1 + 2 + 3 = 6 ✓

    Visual:
    1 • + 2 •• + 3 ••• = 6 ••••••

    28 is perfect:
    1 + 2 + 4 + 7 + 14 = 28 ✓

    Known perfect numbers:
    • 6 = 2¹(2² - 1)
    • 28 = 2²(2³ - 1)
    • 496 = 2⁴(2⁵ - 1)
    • 8128 = 2⁶(2⁷ - 1)

    Euclid-Euler: 2^(p-1)(2^p - 1) is perfect when 2^p - 1 is prime!
    """


async def main():
    print("=" * 80)
    print("👑 MATHEMATICAL DISCOVERY: Number Theory - The Queen of Mathematics")
    print("=" * 80)
    print()
    print("Using EXPLORE mode to discover number-theoretic properties!")
    print("GCD, LCM, prime factorization, and beautiful identities")
    print()

    supe = Supe(db_path=":memory:")

    # Seed number theory knowledge
    print("📚 Seeding number theory definitions...")

    nt_def = """Number Theory: Study of Integers

Divisibility:
- a | b means ∃k ∈ ℤ: b = ka
- Properties: reflexive, transitive, antisymmetric (on ℕ)

Greatest Common Divisor (GCD):
- gcd(a,b) is the largest d such that d | a and d | b
- Computed via Euclidean algorithm: gcd(a,b) = gcd(b, a mod b)
- Base case: gcd(a, 0) = a

Least Common Multiple (LCM):
- lcm(a,b) is the smallest m such that a | m and b | m
- Formula: lcm(a,b) = (a × b) / gcd(a,b)

Euclidean Algorithm:
To compute gcd(a,b):
1. If b = 0, return a
2. Otherwise, return gcd(b, a mod b)

Fundamental Theorem of Arithmetic:
Every integer n > 1 has unique prime factorization:
n = p₁^a₁ × p₂^a₂ × ... × pₖ^aₖ

Bézout's Identity:
For any integers a,b: gcd(a,b) = ax + by for some x,y ∈ ℤ

Chinese Remainder Theorem:
System x ≡ aᵢ (mod mᵢ) has unique solution mod ∏mᵢ when gcd(mᵢ,mⱼ)=1

Perfect Numbers:
n is perfect if n equals sum of its proper divisors
Example: 6 = 1 + 2 + 3"""

    supe.memory.store_card(
        label="number_theory_definitions",
        buffers=[Buffer(name="content", payload=nt_def.encode('utf-8'))],
        master_output="Number theory definitions and theorems",
        track="awareness",
    )
    print("✓ Number theory concepts defined\n")

    # Discovery 1: GCD-LCM relationship
    print("🔍 DISCOVERY 1: GCD-LCM Product Identity")
    print("-" * 80)
    print(draw_gcd())
    print()
    print(draw_lcm())
    print("Question: Is gcd(a,b) × lcm(a,b) = a × b?")
    print()
    print("Test: a = 12, b = 18")
    print("  gcd(12, 18) = 6")
    print("  lcm(12, 18) = 36")
    print("  gcd × lcm = 6 × 36 = 216")
    print("  a × b = 12 × 18 = 216 ✓")
    print()

    result1 = await supe.learn(
        "Is gcd(12,18) × lcm(12,18) = 12 × 18? (Test: 6 × 36 = 216 = 12 × 18)",
        mode="explore"
    )

    if result1['beliefs_count'] > 0:
        status = result1['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result1['confidence']:.2f}")
        print(f"Proof Hash: {result1['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ GCD-LCM identity VERIFIED!")
            print("⟹ gcd(a,b) × lcm(a,b) = a × b")
            print("⟹ This connects GCD and LCM beautifully!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 2: Euclidean algorithm
    print("🔍 DISCOVERY 2: Euclidean Algorithm Step")
    print("-" * 80)
    print(draw_euclidean_algorithm())
    print("Question: Is gcd(48, 18) = gcd(18, 48 mod 18)?")
    print()
    print("Calculation:")
    print("  48 mod 18 = 12  (48 = 2×18 + 12)")
    print("  gcd(48, 18) = gcd(18, 12)")
    print()
    print("Continue:")
    print("  gcd(18, 12) = gcd(12, 6)")
    print("  gcd(12, 6) = gcd(6, 0) = 6 ✓")
    print()

    result2 = await supe.learn(
        "Is gcd(48, 18) equal to gcd(18, 12)? (Euclidean algorithm: 48 mod 18 = 12)",
        mode="explore"
    )

    if result2['beliefs_count'] > 0:
        status = result2['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result2['confidence']:.2f}")
        print(f"Proof Hash: {result2['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Euclidean algorithm VERIFIED!")
            print("⟹ gcd(a,b) = gcd(b, a mod b)")
            print("⟹ Most efficient GCD algorithm!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 3: Divisibility transitivity
    print("🔍 DISCOVERY 3: Divisibility is Transitive")
    print("-" * 80)
    print(draw_divisibility())
    print("Question: If a | b and b | c, then a | c?")
    print()
    print("Test: 3 | 12 and 12 | 60")
    print("  12 = 3 × 4 ✓")
    print("  60 = 12 × 5 ✓")
    print("  Does 3 | 60?")
    print("  60 = 3 × 20 ✓")
    print()

    result3 = await supe.learn(
        "If 3 | 12 and 12 | 60, does 3 | 60? (Transitivity: 60 = 3 × 20)",
        mode="explore"
    )

    if result3['beliefs_count'] > 0:
        status = result3['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"Proof Hash: {result3['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Divisibility transitivity VERIFIED!")
            print("⟹ Fundamental property for factorization")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 4: Bézout's identity example
    print("🔍 DISCOVERY 4: Bézout's Identity")
    print("-" * 80)
    print(draw_bezout())
    print("Question: Can gcd(18, 12) = 6 be written as 18x + 12y?")
    print()
    print("From Euclidean algorithm backwards:")
    print("  18 = 1 × 12 + 6")
    print("  6 = 18 - 1 × 12")
    print("  6 = 18(1) + 12(-1) ✓")
    print()

    result4 = await supe.learn(
        "Can 6 be written as 18(1) + 12(-1)? (Bézout's identity: 18 - 12 = 6)",
        mode="explore"
    )

    if result4['beliefs_count'] > 0:
        status = result4['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result4['confidence']:.2f}")
        print(f"Proof Hash: {result4['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Bézout's identity VERIFIED!")
            print("⟹ gcd can be expressed as linear combination!")
            print("⟹ Foundation for extended Euclidean algorithm")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 5: Perfect number
    print("🔍 DISCOVERY 5: Perfect Number Property")
    print("-" * 80)
    print(draw_perfect_numbers())
    print("Question: Is 6 a perfect number?")
    print()
    print("Proper divisors of 6: 1, 2, 3")
    print("Sum: 1 + 2 + 3 = 6 ✓")
    print()

    result5 = await supe.learn(
        "Is 6 a perfect number? (Sum of proper divisors: 1 + 2 + 3 = 6)",
        mode="explore"
    )

    if result5['beliefs_count'] > 0:
        status = result5['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result5['confidence']:.2f}")
        print(f"Proof Hash: {result5['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ 6 is perfect VERIFIED!")
            print("⟹ Smallest perfect number")
            print("⟹ Next: 28, 496, 8128...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Display visualizations
    print("=" * 80)
    print("🎨 NUMBER THEORY VISUALIZATIONS")
    print("=" * 80)
    print()
    print("÷ Divisibility:")
    print(draw_divisibility())
    print()
    print("🔢 GCD (Tiling):")
    print(draw_gcd())
    print()
    print("📐 Euclidean Algorithm:")
    print(draw_euclidean_algorithm())
    print()
    print("🌳 Prime Factorization:")
    print(draw_prime_factorization())
    print()
    print("⭐ Bézout's Identity:")
    print(draw_bezout())
    print()
    print("🇨🇳 Chinese Remainder Theorem:")
    print(draw_chinese_remainder())
    print()

    # Summary
    print("=" * 80)
    print("🎓 NUMBER THEORY DISCOVERIES")
    print("=" * 80)
    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                    NUMBER THEORY FUNDAMENTALS                        ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║                                                                      ║")
    print("║  Divisibility:                                                       ║")
    print("║    • a | b means b = ka for some integer k                          ║")
    print("║    • Transitive: (a|b) ∧ (b|c) ⟹ (a|c)                             ║")
    print("║    • Antisymmetric: (a|b) ∧ (b|a) ⟹ a = ±b                         ║")
    print("║                                                                      ║")
    print("║  GCD and LCM:                                                        ║")
    print("║    • gcd(a,b) × lcm(a,b) = a × b                                    ║")
    print("║    • gcd(a,b) = gcd(b, a mod b) (Euclidean algorithm)               ║")
    print("║    • gcd(a,b) = ax + by (Bézout's identity)                         ║")
    print("║                                                                      ║")
    print("║  Fundamental Theorem:                                                ║")
    print("║    • Every n > 1 has unique prime factorization                     ║")
    print("║    • n = p₁^a₁ × p₂^a₂ × ... × pₖ^aₖ                               ║")
    print("║                                                                      ║")
    print("║  Perfect Numbers:                                                    ║")
    print("║    • n equals sum of proper divisors                                ║")
    print("║    • 6, 28, 496, 8128, ...                                          ║")
    print("║    • Related to Mersenne primes                                     ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("🌟 What We Learned:")
    print(f"   • Total beliefs formed: {sum(1 for r in [result1, result2, result3, result4, result5] if r['beliefs_count'] > 0)}")
    print("   • Each discovery stored with proof hash")
    print("   • Linked to Tasc execution for traceability")
    print()
    print("🔗 Connections:")
    print("   Number Theory ──→ Cryptography (RSA, Diffie-Hellman)")
    print("                 ──→ Modular Arithmetic (ℤ/nℤ)")
    print("                 ──→ Algebra (rings, fields, domains)")
    print("                 ──→ Computer Science (hashing, scheduling)")
    print("                 ──→ Music Theory (rhythm, harmony)")
    print()
    print("💡 Next Number Theory Horizons:")
    print("   • Diophantine equations: ax + by = c")
    print("   • Fermat's Little Theorem: a^(p-1) ≡ 1 (mod p)")
    print("   • Quadratic reciprocity")
    print("   • Goldbach's conjecture")
    print("   • Twin primes and prime gaps")
    print("   • Riemann hypothesis (distribution of primes)")
    print()
    print("🎭 Philosophy:")
    print("   \"Mathematics is the queen of sciences and number theory is")
    print("    the queen of mathematics.\" - Gauss")
    print()
    print("   Simple questions about integers lead to the deepest truths!")
    print("   GCD algorithm: ancient but powers modern cryptography.")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
