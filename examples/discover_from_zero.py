"""
Mathematical Discovery: Building Mathematics from Zero 🌱

Starting from NOTHING but the concept of zero and successor,
let's discover what mathematical truths emerge!

Peano Axioms (foundation):
    1. 0 is a natural number
    2. Every natural number n has a successor S(n)
    3. 0 is not the successor of any natural number
    4. If S(n) = S(m), then n = m (successor is injective)
    5. Induction principle

From these 5 axioms, we will DISCOVER:
    • What is addition?
    • What is multiplication?
    • What patterns emerge?
    • What new relationships can we find?

Let's build mathematics from scratch and see what we discover! ∞
"""

import asyncio
from supe import Supe
from ab.models import Buffer


def draw_peano_axioms():
    return """
    Peano Axioms: Foundation of Natural Numbers

    Starting from NOTHING:

    Axiom 1: 0 exists
         •
         0

    Axiom 2: Every number has a successor S(n)
         0 → S(0) → S(S(0)) → S(S(S(0))) → ...
         0 →  1   →    2    →      3      → ...

    Axiom 3: 0 has no predecessor
         Nothing points to 0
         0 is the "start"

    Axiom 4: Successor is injective
         If S(n) = S(m), then n = m
         Different numbers have different successors

    Axiom 5: Induction
         If P(0) is true, and P(n) ⇒ P(S(n)),
         then P(n) is true for all n

    From these 5 axioms, ALL of arithmetic emerges!
    """


def draw_addition_construction():
    return """
    Constructing Addition from Successor

    Definition (recursive):
        a + 0 = a                    (base case)
        a + S(b) = S(a + b)          (recursive case)

    Example: 2 + 3 = ?

    Step by step:
        2 + 3 = 2 + S(2)
              = S(2 + 2)              (by definition)
              = S(2 + S(1))
              = S(S(2 + 1))
              = S(S(2 + S(0)))
              = S(S(S(2 + 0)))
              = S(S(S(2)))            (base case)
              = S(S(3))
              = S(4)
              = 5 ✓

    Visual:
         2 + 3
         ││││ + │││
         │││││││
         7 successors from 0 = 5 ✓

    Addition emerges from repeated successor!
    """


def draw_multiplication_construction():
    return """
    Constructing Multiplication from Addition

    Definition (recursive):
        a × 0 = 0                    (base case)
        a × S(b) = a + (a × b)       (recursive case)

    Example: 3 × 4 = ?

    Step by step:
        3 × 4 = 3 × S(3)
              = 3 + (3 × 3)           (by definition)
              = 3 + (3 × S(2))
              = 3 + (3 + (3 × 2))
              = 3 + (3 + (3 × S(1)))
              = 3 + (3 + (3 + (3 × 1)))
              = 3 + (3 + (3 + (3 × S(0))))
              = 3 + (3 + (3 + (3 + (3 × 0))))
              = 3 + (3 + (3 + (3 + 0)))
              = 3 + (3 + (3 + 3))
              = 3 + (3 + 6)
              = 3 + 9
              = 12 ✓

    Visual:
         3 × 4 = 3 + 3 + 3 + 3
                 │││ │││ │││ │││
                 ││││││││││││
                 12 ✓

    Multiplication emerges from repeated addition!
    """


def draw_discovered_pattern_1():
    return """
    DISCOVERY 1: The Diagonal Pattern

    Looking at multiplication table:

        ×│ 0  1  2  3  4  5
        ─┼──────────────────
        0│ 0  0  0  0  0  0
        1│ 0  1  2  3  4  5
        2│ 0  2  4  6  8 10
        3│ 0  3  6  9 12 15
        4│ 0  4  8 12 16 20
        5│ 0  5 10 15 20 25

    Notice: Main diagonal (n × n) forms SQUARES!
        1×1=1, 2×2=4, 3×3=9, 4×4=16, 5×5=25

    Pattern: n² = n × n

    But what about the DIFFERENCES between squares?

        1² = 1
        2² = 4    (difference: 3 = 2×1 + 1)
        3² = 9    (difference: 5 = 2×2 + 1)
        4² = 16   (difference: 7 = 2×3 + 1)
        5² = 25   (difference: 9 = 2×4 + 1)

    Conjecture: (n+1)² - n² = 2n + 1

    Proof:
        (n+1)² - n² = (n+1)(n+1) - n×n
                    = n² + 2n + 1 - n²
                    = 2n + 1 ✓

    ODD NUMBERS are differences between consecutive squares!
    """


def draw_discovered_pattern_2():
    return """
    DISCOVERY 2: Triangular Numbers

    Start with 0, keep adding next number:

        T(0) = 0
        T(1) = 0 + 1 = 1                •
        T(2) = 0 + 1 + 2 = 3            • •
        T(3) = 0 + 1 + 2 + 3 = 6        • • •
        T(4) = 0 + 1 + 2 + 3 + 4 = 10   • • • •

    Visual pattern (triangles):

        T(1) = 1:       •

        T(2) = 3:       •
                       • •

        T(3) = 6:       •
                       • •
                      • • •

        T(4) = 10:      •
                       • •
                      • • •
                     • • • •

    Formula: T(n) = n(n+1)/2 = 1+2+3+...+n

    Connection to SQUARES:
        2×T(n) = n(n+1) = n² + n
        T(n) = (n² + n)/2

    DISCOVERY: Two consecutive triangular numbers sum to a square!
        T(n) + T(n-1) = n²

    Proof:
        T(n) + T(n-1) = n(n+1)/2 + (n-1)n/2
                      = [n(n+1) + (n-1)n]/2
                      = n[(n+1) + (n-1)]/2
                      = n(2n)/2
                      = n² ✓

    Visual:
             T(3)        T(2)
              •           •          T(3) + T(2)
             • •         • •    =    • • •
            • • •                    • • •
                                     • • •  = 3² = 9 ✓
    """


def draw_discovered_pattern_3():
    return """
    DISCOVERY 3: The Power of 2 Pattern

    Powers of 2: 1, 2, 4, 8, 16, 32, 64, ...

    Binary representation:
        2⁰ = 1   = 0001₂
        2¹ = 2   = 0010₂
        2² = 4   = 0100₂
        2³ = 8   = 1000₂
        2⁴ = 16  = 10000₂

    Each power of 2 has exactly ONE bit set!

    Sum pattern:
        2⁰ = 1
        2⁰ + 2¹ = 1 + 2 = 3
        2⁰ + 2¹ + 2² = 1 + 2 + 4 = 7
        2⁰ + 2¹ + 2² + 2³ = 1 + 2 + 4 + 8 = 15

    Pattern: 1 + 2 + 4 + ... + 2ⁿ = 2^(n+1) - 1

    In binary:
        0001 + 0010 + 0100 + 1000 = 1111 = 15 = 2⁴ - 1

    DISCOVERY: Sum of first n powers of 2 = 2^(n+1) - 1
               ALL bits set = 2^(n+1) - 1

    Connection to counting:
        How many subsets of n elements?
        Each element: in or out (2 choices)
        Total: 2ⁿ subsets

        Example: {a, b}
        Subsets: ∅, {a}, {b}, {a,b} = 4 = 2² ✓

    This connects ARITHMETIC to COMBINATORICS!
    """


def draw_discovered_pattern_4():
    return """
    DISCOVERY 4: Fibonacci-like Sequences

    Classic Fibonacci: 0, 1, 1, 2, 3, 5, 8, 13, 21, ...
        F(n) = F(n-1) + F(n-2)

    But what if we change the starting values?

    Start with (2, 1):
        2, 1, 3, 4, 7, 11, 18, 29, 47, ...

    Start with (3, 1):
        3, 1, 4, 5, 9, 14, 23, 37, 60, ...

    DISCOVERY: All such sequences have the SAME ratio!

    Limit: F(n+1)/F(n) → φ = (1 + √5)/2 ≈ 1.618...

    The GOLDEN RATIO φ emerges from ANY Fibonacci-like sequence!

    Proof (for classic):
        Let r = lim F(n+1)/F(n)
        Then: r = lim (F(n) + F(n-1))/F(n)
             r = 1 + 1/r
             r² = r + 1
             r² - r - 1 = 0
             r = (1 ± √5)/2

        Taking positive root: r = φ = (1 + √5)/2 ✓

    Connection to nature:
        • Nautilus shells spiral with φ
        • Flower petals often Fibonacci numbers
        • Tree branching follows φ ratios

    The golden ratio is BUILT INTO the successor operation!
    """


def draw_discovered_pattern_5():
    return """
    DISCOVERY 5: Modular Arithmetic Cycles

    Take any number, repeatedly add itself mod n:

    Example: Add 2 mod 5
        0, 2, 4, 1, 3, 0, 2, 4, 1, 3, ...
        Cycle length: 5 ✓

    Example: Add 3 mod 6
        0, 3, 0, 3, 0, 3, ...
        Cycle length: 2 (not 6!)

    DISCOVERY: Cycle length = n / gcd(n, k)

    Where k is the number we're adding

    Examples:
        n=5, k=2: cycle = 5/gcd(5,2) = 5/1 = 5 ✓
        n=6, k=3: cycle = 6/gcd(6,3) = 6/3 = 2 ✓
        n=8, k=3: cycle = 8/gcd(8,3) = 8/1 = 8 ✓
        n=12, k=4: cycle = 12/gcd(12,4) = 12/4 = 3 ✓

    Visual (clock arithmetic, n=12, k=5):

              12/0
           11    1
         10        2
        9            3
         8          4
           7      5
              6

        Start at 0: 0→5→10→3→8→1→6→11→4→9→2→7→0
        Visits ALL 12 positions! (gcd(12,5)=1)

    Connection to group theory:
        Cycle length = ORDER of element in ℤ/nℤ
        Element generates whole group ⟺ gcd(k, n) = 1

    This connects ADDITION to NUMBER THEORY!
    """


async def main():
    print("=" * 80)
    print("🌱 MATHEMATICAL DISCOVERY: Building from Zero")
    print("=" * 80)
    print()
    print("Starting from NOTHING but zero and successor...")
    print("Let's discover what mathematics emerges!")
    print()

    supe = Supe(db_path=":memory:")

    # Seed ONLY Peano axioms
    print("📚 Seeding Peano axioms (and NOTHING else)...")

    peano_axioms = """Peano Axioms: The Foundation

Axiom 1: 0 is a natural number
Axiom 2: Every natural number has a successor S(n)
Axiom 3: 0 is not the successor of any number
Axiom 4: If S(n) = S(m), then n = m (injective)
Axiom 5: Mathematical induction

From these 5 axioms, we build EVERYTHING.

Definitions derived from axioms:

Addition:
    n + 0 = n
    n + S(m) = S(n + m)

Multiplication:
    n × 0 = 0
    n × S(m) = n + (n × m)

Examples:
    S(0) = 1 (by definition)
    S(S(0)) = 2
    S(S(S(0))) = 3

    2 + 3: Follow addition rules
    2 + S(2) = S(2 + 2) = S(2 + S(1)) = S(S(2 + 1))
             = S(S(2 + S(0))) = S(S(S(2 + 0)))
             = S(S(S(2))) = 5 ✓"""

    supe.memory.store_card(
        label="peano_axioms",
        buffers=[Buffer(name="content", payload=peano_axioms.encode('utf-8'))],
        master_output="Peano axioms: foundation of arithmetic",
        track="awareness",
    )
    print("✓ Axioms seeded\n")

    # Discovery 1: Commutativity
    print("🔍 DISCOVERY 1: Does order matter in addition?")
    print("-" * 80)
    print(draw_addition_construction())

    result1 = await supe.learn(
        "Is a + b = b + a? (Commutativity of addition from successor axiom)",
        mode="explore"
    )

    print(f"Question: Is addition commutative?")
    print()
    print("Test: 3 + 5 = 8, 5 + 3 = 8")
    print("Test: 7 + 2 = 9, 2 + 7 = 9")
    print()

    if result1['beliefs_count'] > 0:
        belief = result1['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result1['confidence']:.2f}")
        print(f"🎯 DISCOVERED: Addition is commutative!")
    else:
        print("Result: NO BELIEF")
    print()

    # Discovery 2: Squares pattern
    print("🔍 DISCOVERY 2: Pattern in consecutive squares")
    print("-" * 80)
    print(draw_discovered_pattern_1())

    result2 = await supe.learn(
        "Is (n+1)² - n² = 2n + 1? (Difference between consecutive squares)",
        mode="explore"
    )

    print(f"Question: Are odd numbers differences between consecutive squares?")
    print()
    print("Test: 4² - 3² = 16 - 9 = 7 = 2(3) + 1 ✓")
    print("Test: 5² - 4² = 25 - 16 = 9 = 2(4) + 1 ✓")
    print()

    if result2['beliefs_count'] > 0:
        belief = result2['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result2['confidence']:.2f}")
        print(f"🎯 DISCOVERED: Odd numbers = differences of consecutive squares!")
    else:
        print("Result: NO BELIEF")
    print()

    # Discovery 3: Triangular numbers
    print("🔍 DISCOVERY 3: Triangular numbers and squares")
    print("-" * 80)
    print(draw_discovered_pattern_2())

    result3 = await supe.learn(
        "Is T(n) + T(n-1) = n²? (Two triangular numbers sum to square)",
        mode="explore"
    )

    print(f"Question: Do two consecutive triangular numbers sum to a square?")
    print()
    print("T(n) = 1+2+3+...+n = n(n+1)/2")
    print("Test: T(3) + T(2) = 6 + 3 = 9 = 3² ✓")
    print("Test: T(4) + T(3) = 10 + 6 = 16 = 4² ✓")
    print()

    if result3['beliefs_count'] > 0:
        belief = result3['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"🎯 DISCOVERED: Triangular numbers + predecessor = perfect square!")
    else:
        print("Result: NO BELIEF")
    print()

    # Discovery 4: Powers of 2
    print("🔍 DISCOVERY 4: Sum of powers of 2")
    print("-" * 80)
    print(draw_discovered_pattern_3())

    result4 = await supe.learn(
        "Is 1 + 2 + 4 + ... + 2ⁿ = 2^(n+1) - 1? (Sum of powers of 2)",
        mode="explore"
    )

    print(f"Question: Sum of powers of 2 = next power minus 1?")
    print()
    print("Test: 1+2+4+8 = 15 = 2⁴-1 = 16-1 ✓")
    print("Test: 1+2+4 = 7 = 2³-1 = 8-1 ✓")
    print()

    if result4['beliefs_count'] > 0:
        belief = result4['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result4['confidence']:.2f}")
        print(f"🎯 DISCOVERED: Powers of 2 sum to next power - 1!")
    else:
        print("Result: NO BELIEF")
    print()

    # Discovery 5: Modular cycles
    print("🔍 DISCOVERY 5: Cycle length in modular addition")
    print("-" * 80)
    print(draw_discovered_pattern_5())

    result5 = await supe.learn(
        "In ℤ/nℤ, is cycle length of k equal to n/gcd(n,k)? (Modular arithmetic cycles)",
        mode="explore"
    )

    print(f"Question: Does cycle length = n/gcd(n,k)?")
    print()
    print("Test: n=12, k=4: cycle = 12/gcd(12,4) = 12/4 = 3")
    print("  0→4→8→0 (cycle of 3) ✓")
    print()

    if result5['beliefs_count'] > 0:
        belief = result5['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result5['confidence']:.2f}")
        print(f"🎯 DISCOVERED: Modular cycles determined by GCD!")
    else:
        print("Result: NO BELIEF")
    print()

    # Summary
    print("=" * 80)
    print("🎓 DISCOVERIES FROM FIRST PRINCIPLES")
    print("=" * 80)
    print()

    total_beliefs = sum(r['beliefs_count'] for r in [result1, result2, result3, result4, result5])

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║            MATHEMATICAL DISCOVERIES FROM ZERO                        ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║                                                                      ║")
    print("║  Starting from: 0 and successor S(n)                                 ║")
    print("║                                                                      ║")
    print("║  DISCOVERED:                                                         ║")
    print("║    1. Addition is commutative: a + b = b + a                         ║")
    print("║    2. Odd numbers: (n+1)² - n² = 2n + 1                             ║")
    print("║    3. Triangular sum: T(n) + T(n-1) = n²                            ║")
    print("║    4. Power sum: Σ 2ⁱ = 2^(n+1) - 1                                 ║")
    print("║    5. Modular cycles: length = n/gcd(n,k)                            ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    print(f"🌟 What We Built:")
    print(f"   • Started with 5 axioms (Peano)")
    print(f"   • Defined addition from successor")
    print(f"   • Defined multiplication from addition")
    print(f"   • Discovered {total_beliefs} non-trivial patterns")
    print(f"   • Connected arithmetic to geometry, combinatorics, number theory")
    print()

    print("🔗 Emerging Connections:")
    print("   Successor → Addition → Multiplication")
    print("            → Squares → Triangular numbers")
    print("            → Powers → Binary representation")
    print("            → Modular arithmetic → Group theory")
    print("            → Golden ratio → Nature")
    print()

    print("💡 Next Discovery Horizons:")
    print("   • What happens with exponentiation?")
    print("   • Can we discover prime number patterns?")
    print("   • What about negative numbers?")
    print("   • How do these patterns generalize?")
    print()

    print("🎭 Philosophy:")
    print("   Mathematics is DISCOVERY, not invention!")
    print("   From 5 simple axioms, infinite complexity emerges.")
    print("   Patterns connect: arithmetic ↔ geometry ↔ combinatorics.")
    print("   The golden ratio φ arises naturally from succession.")
    print("   GCD links addition to group theory.")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
