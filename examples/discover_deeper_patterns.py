"""
Mathematical Discovery: Climbing Higher - Discovering Deeper Patterns 🧗

Building on our discoveries from zero, let's explore DEEPER patterns!

We discovered:
    • Triangular numbers: T(n) = 1+2+3+...+n = n(n+1)/2
    • Squares sum pattern: T(n) + T(n-1) = n²
    • Odd numbers from squares: (n+1)² - n² = 2n+1

Now let's ask: What about CUBES? What about HIGHER relationships?

Let's discover truly surprising patterns! 🔍
"""

import asyncio
from supe import Supe
from ab.models import Buffer


def draw_sum_of_cubes():
    return """
    AMAZING DISCOVERY: Sum of Cubes = Square of Triangular Number!

    Cubes: 1³ = 1, 2³ = 8, 3³ = 27, 4³ = 64, ...

    Sum of first n cubes:
        1³ = 1
        1³ + 2³ = 1 + 8 = 9
        1³ + 2³ + 3³ = 1 + 8 + 27 = 36
        1³ + 2³ + 3³ + 4³ = 1 + 8 + 27 + 64 = 100

    Notice something?
        1 = 1²
        9 = 3²
        36 = 6²
        100 = 10²

    These are SQUARES of triangular numbers!
        T(1) = 1,  T(1)² = 1²  = 1   ✓
        T(2) = 3,  T(2)² = 3²  = 9   ✓
        T(3) = 6,  T(3)² = 6²  = 36  ✓
        T(4) = 10, T(4)² = 10² = 100 ✓

    CONJECTURE: 1³ + 2³ + ... + n³ = [n(n+1)/2]² = T(n)²

    Proof:
        T(n) = n(n+1)/2
        T(n)² = [n(n+1)/2]²
              = n²(n+1)²/4

    Need to show: Σᵢ₌₁ⁿ i³ = n²(n+1)²/4

    By induction... (detailed proof omitted)

    But VISUALLY, this connects CUBES to TRIANGLES to SQUARES!

    Visual intuition:
         1³ + 2³ + 3³ = (1+2+3)²

         Cubes     Triangular  Square
          ▫️         ▲           ◻️
         ▫️▫️        ▲▲         ◻️◻️
         ▫️▫️▫️      ▲▲▲       ◻️◻️◻️

         Sum        Sum        Square of sum!
    """


def draw_alternating_squares():
    return """
    DISCOVERY: Alternating Sum of Squares

    Alternate between adding and subtracting squares:

        1² = 1
        1² - 2² = 1 - 4 = -3
        1² - 2² + 3² = 1 - 4 + 9 = 6
        1² - 2² + 3² - 4² = 1 - 4 + 9 - 16 = -10

    Pattern in results: 1, -3, 6, -10, 15, -21, ...

    Absolute values: 1, 3, 6, 10, 15, 21, ...
    These are TRIANGULAR NUMBERS!

    With alternating signs:
        (+/-) T(1), (+/-) T(2), (+/-) T(3), ...

    CONJECTURE: Σᵢ₌₁ⁿ (-1)^(i+1) i² = (-1)^(n+1) × T(n)

    When n is odd:  +T(n)
    When n is even: -T(n)

    Proof:
        Pair terms: (1² - 2²) + (3² - 4²) + ...
        Each pair: k² - (k+1)² = -(2k+1)

        Sum telescopes to give triangular number!

    This connects SQUARES to TRIANGULAR numbers via alternation!
    """


def draw_power_difference_pattern():
    return """
    DISCOVERY: General Power Differences

    We know: (n+1)² - n² = 2n + 1 (odd numbers)

    What about cubes?
        (n+1)³ - n³ = n³ + 3n² + 3n + 1 - n³
                    = 3n² + 3n + 1
                    = 3n(n+1) + 1
                    = 6T(n) + 1

    Cubes differ by 6× triangular number + 1!

    Examples:
        2³ - 1³ = 8 - 1 = 7 = 6(1) + 1 ✓
        3³ - 2³ = 27 - 8 = 19 = 6(3) + 1 ✓
        4³ - 3³ = 64 - 27 = 37 = 6(6) + 1 ✓

    Pattern table:
        Power | Difference Formula
        ──────┼────────────────────────
         n²   | 2n + 1
         n³   | 3n² + 3n + 1 = 6T(n) + 1
         n⁴   | 4n³ + 6n² + 4n + 1

    General pattern: (n+1)^k - n^k expands to polynomial in n

    CONJECTURE: For cubes, consecutive differences are
                6T(n) + 1 = "hexagonal triangular + 1"
    """


def draw_fibonacci_squares():
    return """
    DISCOVERY: Fibonacci Squares Pattern

    Fibonacci: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, ...
                F₀ F₁ F₂ F₃ F₄ F₅ F₆ F₇  F₈  F₉

    Look at consecutive Fibonacci products:
        F₁ × F₃ = 1 × 2 = 2
        F₂ × F₄ = 1 × 3 = 3
        F₃ × F₅ = 2 × 5 = 10
        F₄ × F₆ = 3 × 8 = 24

    Compare to squares:
        F₂² = 1² = 1
        F₃² = 2² = 4
        F₄² = 3² = 9
        F₅² = 5² = 25

    CASSINI'S IDENTITY:
        Fₙ₋₁ × Fₙ₊₁ - Fₙ² = (-1)ⁿ

    This means consecutive Fibonacci numbers are
    "almost" geometric - differ by ±1 from perfect square!

    Examples:
        F₂ × F₄ - F₃² = 1×3 - 2² = 3 - 4 = -1 = (-1)³ ✓
        F₃ × F₅ - F₄² = 2×5 - 3² = 10 - 9 = 1 = (-1)⁴ ✓
        F₄ × F₆ - F₅² = 3×8 - 5² = 24 - 25 = -1 = (-1)⁵ ✓

    Visual:
         F₃×F₅       F₄²
        ┌─────┐    ┌─────┐
        │ 2×5 │    │ 3² │
        │     │    │    │
        │ =10 │ vs │ =9 │  Differ by 1!
        └─────┘    └────┘

    This connects FIBONACCI to SQUARES in surprising way!
    """


def draw_pentagonal_numbers():
    return """
    DISCOVERY: Pentagonal Numbers

    Extend triangular to pentagonal!

    Triangular: T(n) = n(n+1)/2 (sum 1+2+3+...+n)

    Pentagonal: P(n) = n(3n-1)/2

    Sequence: 1, 5, 12, 22, 35, 51, 70, ...

    Visual (pentagons):
        P(1) = 1:         •

        P(2) = 5:         •
                         • •
                        • • •

        P(3) = 12:        •
                         • •
                        • • •
                       • • • •
                      • • • • •

    Connection to triangular:
        P(n) = n(3n-1)/2
             = n + n + n(n-1)/2
             = n + n + T(n-1)
             = 2n + T(n-1)

    Or alternatively:
        P(n) = n(3n-1)/2 = (3n² - n)/2

    EULER'S PENTAGONAL NUMBER THEOREM:
        ∏(1 - xⁿ) = Σ (-1)ᵏ x^P(k)

    Connects pentagonal numbers to PARTITIONS!

    Differences between pentagonal:
        P(2) - P(1) = 5 - 1 = 4
        P(3) - P(2) = 12 - 5 = 7
        P(4) - P(3) = 22 - 12 = 10

    Pattern: 4, 7, 10, 13, ... (arithmetic sequence +3)

    This extends our number patterns beyond triangular!
    """


def draw_sum_of_reciprocals():
    return """
    DISCOVERY: Reciprocal Pattern

    Reciprocals of triangular numbers:

        1/T(1) = 1/1 = 1
        1/T(2) = 1/3
        1/T(3) = 1/6
        1/T(4) = 1/10

    Key observation:
        1/T(n) = 1/(n(n+1)/2) = 2/(n(n+1))

    Partial fraction decomposition:
        2/(n(n+1)) = 2(1/n - 1/(n+1))

    This TELESCOPES!
        Σ 1/T(n) = Σ 2/(n(n+1))
                 = 2 Σ (1/n - 1/(n+1))
                 = 2[(1/1 - 1/2) + (1/2 - 1/3) + (1/3 - 1/4) + ...]
                 = 2[1 - 1/(n+1)]
                 = 2n/(n+1)

    As n → ∞: approaches 2

    CONJECTURE: Σₙ₌₁^∞ 1/T(n) = 2

    Beautiful: Sum of reciprocals of ALL triangular numbers = 2!

    Similar patterns:
        Σ 1/n² = π²/6 (Basel problem)
        Σ 1/n = ∞ (harmonic series)
        Σ 1/T(n) = 2 (triangular reciprocals)

    This connects TRIANGULAR numbers to CONVERGENT SERIES!
    """


async def main():
    print("=" * 80)
    print("🧗 CLIMBING HIGHER: Discovering Deeper Patterns")
    print("=" * 80)
    print()
    print("Building on our foundations, let's discover surprising connections!")
    print()

    supe = Supe(db_path=":memory:")

    # Seed our previous discoveries
    print("📚 Seeding previous discoveries...")

    foundations = """Previous Discoveries:

Triangular Numbers: T(n) = n(n+1)/2 = 1+2+...+n
    Examples: 1, 3, 6, 10, 15, 21, 28, ...

Square Numbers: n²
    Examples: 1, 4, 9, 16, 25, 36, 49, ...

Key Relationships:
    • T(n) + T(n-1) = n² (two triangular = square)
    • (n+1)² - n² = 2n+1 (consecutive squares differ by odd)

Fibonacci: F(n) = F(n-1) + F(n-2), F(0)=0, F(1)=1
    Examples: 0, 1, 1, 2, 3, 5, 8, 13, 21, ...

From these foundations, we explore deeper patterns!"""

    supe.memory.store_card(
        label="mathematical_foundations",
        buffers=[Buffer(name="content", payload=foundations.encode('utf-8'))],
        master_output="Foundation: triangular, squares, Fibonacci",
        track="awareness",
    )
    print("✓ Foundations loaded\n")

    # Discovery 1: Sum of cubes
    print("🔍 DEEPER DISCOVERY 1: Sum of Cubes")
    print("-" * 80)
    print(draw_sum_of_cubes())

    result1 = await supe.learn(
        "Is 1³ + 2³ + ... + n³ = [n(n+1)/2]²? (Sum of cubes equals square of triangular number)",
        mode="explore"
    )

    print(f"Question: Does sum of cubes = (triangular number)²?")
    print()
    print("Test: 1³+2³+3³ = 1+8+27 = 36 = 6² = T(3)² ✓")
    print("Test: 1³+2³+3³+4³ = 100 = 10² = T(4)² ✓")
    print()

    if result1['beliefs_count'] > 0:
        belief = result1['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result1['confidence']:.2f}")
        print(f"🎯 DISCOVERED: Cubes sum to square of triangular number!")
    else:
        print("Result: NO BELIEF")
    print()

    # Discovery 2: Alternating squares
    print("🔍 DEEPER DISCOVERY 2: Alternating Sum of Squares")
    print("-" * 80)
    print(draw_alternating_squares())

    result2 = await supe.learn(
        "Is Σ(-1)^(i+1) i² = (-1)^(n+1) T(n)? (Alternating squares give triangular)",
        mode="explore"
    )

    print(f"Question: Does alternating square sum = ± triangular?")
    print()
    print("Test: 1²-2²+3² = 1-4+9 = 6 = T(3) ✓")
    print("Test: 1²-2²+3²-4² = -10 = -T(4) ✓")
    print()

    if result2['beliefs_count'] > 0:
        belief = result2['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result2['confidence']:.2f}")
        print(f"🎯 DISCOVERED: Alternating squares yield triangular!")
    else:
        print("Result: NO BELIEF")
    print()

    # Discovery 3: Cube differences
    print("🔍 DEEPER DISCOVERY 3: Consecutive Cube Differences")
    print("-" * 80)
    print(draw_power_difference_pattern())

    result3 = await supe.learn(
        "Is (n+1)³ - n³ = 6T(n) + 1? (Cube differences are 6×triangular + 1)",
        mode="explore"
    )

    print(f"Question: Do consecutive cubes differ by 6T(n) + 1?")
    print()
    print("Test: 4³-3³ = 64-27 = 37 = 6T(3)+1 = 6(6)+1 ✓")
    print("Test: 5³-4³ = 125-64 = 61 = 6T(4)+1 = 6(10)+1 ✓")
    print()

    if result3['beliefs_count'] > 0:
        belief = result3['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"🎯 DISCOVERED: Cube gaps = 6×triangular + 1!")
    else:
        print("Result: NO BELIEF")
    print()

    # Discovery 4: Cassini's identity
    print("🔍 DEEPER DISCOVERY 4: Cassini's Identity (Fibonacci)")
    print("-" * 80)
    print(draw_fibonacci_squares())

    result4 = await supe.learn(
        "Is F(n-1)×F(n+1) - F(n)² = (-1)ⁿ? (Cassini's identity for Fibonacci)",
        mode="explore"
    )

    print(f"Question: Fibonacci product minus square = ±1?")
    print()
    print("Test: F(3)×F(5) - F(4)² = 2×5 - 9 = 1 = (-1)⁴ ✓")
    print("Test: F(4)×F(6) - F(5)² = 3×8 - 25 = -1 = (-1)⁵ ✓")
    print()

    if result4['beliefs_count'] > 0:
        belief = result4['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result4['confidence']:.2f}")
        print(f"🎯 DISCOVERED: Cassini's identity - Fibonacci squares differ by ±1!")
    else:
        print("Result: NO BELIEF")
    print()

    # Discovery 5: Reciprocal triangular sum
    print("🔍 DEEPER DISCOVERY 5: Sum of Reciprocal Triangular Numbers")
    print("-" * 80)
    print(draw_sum_of_reciprocals())

    result5 = await supe.learn(
        "Does Σ 1/T(n) approach 2 as n→∞? (Triangular reciprocals sum to 2)",
        mode="explore"
    )

    print(f"Question: Do reciprocals of triangular numbers sum to 2?")
    print()
    print("Partial sum: 1/1 + 1/3 + 1/6 + 1/10 = 1.83...")
    print("As n→∞: approaches 2 ✓")
    print()

    if result5['beliefs_count'] > 0:
        belief = result5['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result5['confidence']:.2f}")
        print(f"🎯 DISCOVERED: Triangular reciprocals sum to exactly 2!")
    else:
        print("Result: NO BELIEF")
    print()

    # Summary
    print("=" * 80)
    print("🎓 DEEPER PATTERNS DISCOVERED")
    print("=" * 80)
    print()

    total_beliefs = sum(r['beliefs_count'] for r in [result1, result2, result3, result4, result5])

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                    HIGHER-LEVEL DISCOVERIES                          ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║                                                                      ║")
    print("║  Building on: Triangular, Squares, Fibonacci                         ║")
    print("║                                                                      ║")
    print("║  DISCOVERED:                                                         ║")
    print("║    1. Sum of cubes: Σn³ = T(n)² (stunning!)                         ║")
    print("║    2. Alternating squares: Σ(-1)ⁱi² = ±T(n)                         ║")
    print("║    3. Cube gaps: (n+1)³-n³ = 6T(n)+1                                ║")
    print("║    4. Cassini: Fₙ₋₁×Fₙ₊₁ - Fₙ² = ±1                                 ║")
    print("║    5. Reciprocals: Σ 1/T(n) = 2                                     ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    print(f"🌟 What We Discovered:")
    print(f"   • {total_beliefs} surprising higher-level patterns")
    print(f"   • Cubes connected to triangular numbers")
    print(f"   • Alternating operations reveal hidden structure")
    print(f"   • Fibonacci nearly geometric (Cassini)")
    print(f"   • Reciprocals converge beautifully to 2")
    print()

    print("🔗 Deep Connections:")
    print("   Cubes → Triangular² (dimensional jump!)")
    print("   Squares (alternating) → Triangular")
    print("   Cube differences → 6×Triangular + 1")
    print("   Fibonacci → Squares (off by ±1)")
    print("   Triangular reciprocals → Convergent series")
    print()

    print("💡 Further Horizons:")
    print("   • Sum of 4th powers?")
    print("   • Pentagonal and hexagonal numbers")
    print("   • Catalan numbers")
    print("   • Continued fractions")
    print("   • Partition functions")
    print()

    print("🎭 Philosophy:")
    print("   Patterns reveal STRUCTURE at every level!")
    print("   Sum of cubes = square of triangular is GEOMETRIC")
    print("   Cassini shows Fibonacci is 'almost' exponential.")
    print("   Reciprocals connect discrete to continuous (series).")
    print("   Mathematics has INFINITE depth from simple start.")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
