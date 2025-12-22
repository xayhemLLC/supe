"""
Mathematical Discovery: Complex Numbers ℂ - Beyond the Real Line

Complex numbers extend the real numbers by adding the imaginary unit i where i² = -1!

Core Concept:
    z = a + bi
    where a = real part, b = imaginary part, i² = -1

Operations:
    Addition: (a + bi) + (c + di) = (a+c) + (b+d)i
    Multiplication: (a + bi)(c + di) = (ac-bd) + (ad+bc)i
    Magnitude: |z| = √(a² + b²)
    Conjugate: z̄ = a - bi

Geometric View:
    Complex plane (Argand diagram)
    - Real axis (horizontal)
    - Imaginary axis (vertical)
    - Every complex number is a 2D point!

Beautiful Properties:
    • z·z̄ = |z|²
    • e^(iθ) = cos(θ) + i·sin(θ)  (Euler's formula!)
    • e^(iπ) + 1 = 0  (Euler's identity - most beautiful equation!)

Let's LEARN complex number properties through exploration! ℂ✨
"""

import asyncio
from supe import Supe
from ab.models import Buffer


def draw_complex_plane():
    """ASCII art of the complex plane."""
    return """
    Complex Plane (Argand Diagram):

           Imaginary axis
                 i
                 |
            2i • |
                 |
             i • |
                 |
    ─────────────+─────────────  Real axis
   -2      -1    0    1    2
                 |
            -i • |
                 |
           -2i • |

    Point z = a + bi plotted at (a, b)
    Example: 3 + 2i is at coordinate (3, 2)
    """


def draw_complex_multiplication():
    """Geometric interpretation of multiplication."""
    return """
    Complex Multiplication (Geometric):

    z₁ = r₁·e^(iθ₁)    z₂ = r₂·e^(iθ₂)

    z₁·z₂ = (r₁·r₂)·e^(i(θ₁+θ₂))

    Result:
    • Magnitudes multiply: |z₁·z₂| = |z₁|·|z₂|
    • Angles add: arg(z₁·z₂) = arg(z₁) + arg(z₂)

    Multiplying by i rotates 90° counterclockwise!
    """


def draw_unit_circle_complex():
    """Unit circle in complex plane."""
    return """
    Unit Circle in ℂ:

              e^(iπ/2) = i
                   |
                •  |  •
    e^(iπ) = -1 ───+─── 1 = e^0
                •  |  •
                   |
           e^(-iπ/2) = -i

    All points: z = e^(iθ) = cos(θ) + i·sin(θ)
    Euler's formula connects e, i, trig functions!
    """


def draw_mandelbrot_connection():
    """Connection to Mandelbrot set."""
    return """
    Mandelbrot Set (using complex numbers!):

    For each c ∈ ℂ, iterate: zₙ₊₁ = zₙ² + c
    Starting with z₀ = 0

    If sequence stays bounded → c is in the set
    If sequence escapes to ∞ → c is not in set

                ▓▓▓
             ▓▓▓▓▓▓▓
            ▓▓▓▓▓▓▓▓▓
           ▓▓▓▓▓▓▓▓▓▓▓
          ▓▓▓▓▓▓▓▓▓▓▓▓▓
         ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ▓▓
        ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ ▓▓▓▓
       ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

    Infinitely complex fractal boundary!
    """


async def main():
    print("=" * 80)
    print("ℂ MATHEMATICAL DISCOVERY: Complex Numbers - Beyond the Real Line")
    print("=" * 80)
    print()
    print("Using EXPLORE mode to LEARN complex number properties!")
    print("We'll discover: i² = -1, operations, magnitude, and Euler's formula!")
    print()

    supe = Supe(db_path=":memory:")

    # Seed complex number knowledge
    print("📚 Seeding complex number definitions...")

    complex_def = """Complex Numbers:

Definition: A complex number is of the form z = a + bi
where a = real part, b = imaginary part, i = imaginary unit with i² = -1

Examples:
- 3 + 4i
- -2 + 5i
- 7 (real number, b=0)
- 3i (pure imaginary, a=0)

Operations:
- Addition: (a + bi) + (c + di) = (a+c) + (b+d)i
- Subtraction: (a + bi) - (c + di) = (a-c) + (b-d)i
- Multiplication: (a + bi)(c + di) = (ac-bd) + (ad+bc)i
- Conjugate: z̄ = a - bi
- Magnitude: |z| = √(a² + b²)

Key Identity: z·z̄ = |z|²

Euler's Formula: e^(iθ) = cos(θ) + i·sin(θ)
Euler's Identity: e^(iπ) + 1 = 0"""

    supe.memory.store_card(
        label="complex_definitions",
        buffers=[Buffer(name="content", payload=complex_def.encode('utf-8'))],
        master_output="Complex number definitions and operations",
        track="awareness",
    )
    print("✓ Complex numbers defined\n")

    # Discovery 1: i² = -1
    print("🔍 DISCOVERY 1: The Imaginary Unit")
    print("-" * 80)
    print("Question: What is i²?")
    print("By definition: i² = -1")
    print("This extends the number system beyond reals!")
    print()

    result1 = await supe.learn(
        "Is i² = -1? (The defining property of the imaginary unit)",
        mode="explore"
    )

    if result1['beliefs_count'] > 0:
        status = result1['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result1['confidence']:.2f}")
        print(f"Proof Hash: {result1['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 2: Complex addition
    print("🔍 DISCOVERY 2: Complex Addition")
    print("-" * 80)
    print("Question: Is (2 + 3i) + (4 + 5i) = 6 + 8i?")
    print("Addition rule: Add real parts and imaginary parts separately")
    print("(2 + 4) + (3 + 5)i = 6 + 8i")
    print()

    result2 = await supe.learn(
        "Is (2 + 3i) + (4 + 5i) equal to 6 + 8i? (Complex addition)",
        mode="explore"
    )

    if result2['beliefs_count'] > 0:
        status = result2['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result2['confidence']:.2f}")
        print(f"Proof Hash: {result2['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Complex addition VERIFIED!")
            print("⟹ Add components independently!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 3: Complex multiplication
    print("🔍 DISCOVERY 3: Complex Multiplication")
    print("-" * 80)
    print("Question: Is (3 + 2i)(1 + 4i) = -5 + 14i?")
    print()
    print("Calculation:")
    print("(3 + 2i)(1 + 4i) = 3·1 + 3·4i + 2i·1 + 2i·4i")
    print("                 = 3 + 12i + 2i + 8i²")
    print("                 = 3 + 14i + 8(-1)")
    print("                 = 3 + 14i - 8")
    print("                 = -5 + 14i ✓")
    print()

    result3 = await supe.learn(
        "Is (3 + 2i)(1 + 4i) equal to -5 + 14i? (Complex multiplication with i²=-1)",
        mode="explore"
    )

    if result3['beliefs_count'] > 0:
        status = result3['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"Proof Hash: {result3['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Complex multiplication VERIFIED!")
            print("⟹ FOIL method works with i² = -1!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 4: Magnitude
    print("🔍 DISCOVERY 4: Complex Magnitude")
    print("-" * 80)
    print(draw_complex_plane())
    print("Question: For z = 3 + 4i, is |z| = 5?")
    print("|z| = √(a² + b²) = √(3² + 4²) = √(9 + 16) = √25 = 5 ✓")
    print("(This is the Pythagorean theorem in the complex plane!)")
    print()

    result4 = await supe.learn(
        "For z = 3 + 4i, is the magnitude |z| = 5? (Pythagorean theorem: √(3²+4²))",
        mode="explore"
    )

    if result4['beliefs_count'] > 0:
        status = result4['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result4['confidence']:.2f}")
        print(f"Proof Hash: {result4['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Complex magnitude VERIFIED!")
            print("⟹ Pythagorean theorem applies in ℂ!")
            print("⟹ Complex numbers are 2D vectors!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 5: Conjugate property
    print("🔍 DISCOVERY 5: Conjugate Property")
    print("-" * 80)
    print("For z = 3 + 4i, conjugate z̄ = 3 - 4i")
    print("Question: Is z·z̄ = |z|²?")
    print()
    print("Calculation:")
    print("z·z̄ = (3 + 4i)(3 - 4i)")
    print("    = 9 - 12i + 12i - 16i²")
    print("    = 9 - 16(-1)")
    print("    = 9 + 16 = 25")
    print()
    print("|z|² = 5² = 25 ✓")
    print()

    result5 = await supe.learn(
        "For z = 3 + 4i, is z·z̄ = 25? (Conjugate property: z·z̄ = |z|²)",
        mode="explore"
    )

    if result5['beliefs_count'] > 0:
        status = result5['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result5['confidence']:.2f}")
        print(f"Proof Hash: {result5['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Conjugate property VERIFIED!")
            print("⟹ z·z̄ = |z|² is fundamental!")
            print("⟹ This enables complex division!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Display visualizations
    print("=" * 80)
    print("🎨 COMPLEX NUMBER VISUALIZATIONS")
    print("=" * 80)
    print()
    print(draw_complex_plane())
    print()
    print(draw_unit_circle_complex())
    print()
    print(draw_complex_multiplication())
    print()
    print(draw_mandelbrot_connection())
    print()

    # Summary
    print("=" * 80)
    print("🎓 COMPLEX NUMBER DISCOVERIES")
    print("=" * 80)
    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                    COMPLEX NUMBER PROPERTIES                         ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║                                                                      ║")
    print("║  Fundamental Definition:                                             ║")
    print("║    z = a + bi, where i² = -1                                         ║")
    print("║                                                                      ║")
    print("║  Operations:                                                         ║")
    print("║    Addition:       (a+bi) + (c+di) = (a+c) + (b+d)i                 ║")
    print("║    Multiplication: (a+bi)(c+di) = (ac-bd) + (ad+bc)i                ║")
    print("║    Conjugate:      z̄ = a - bi                                       ║")
    print("║    Magnitude:      |z| = √(a² + b²)                                 ║")
    print("║                                                                      ║")
    print("║  Beautiful Identities:                                               ║")
    print("║    z·z̄ = |z|²                                                       ║")
    print("║    e^(iθ) = cos(θ) + i·sin(θ)   (Euler's formula)                   ║")
    print("║    e^(iπ) + 1 = 0                (Euler's identity)                  ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("🌟 What We Learned:")
    print(f"   • Total beliefs formed: {sum(1 for r in [result1, result2, result3, result4, result5] if r['beliefs_count'] > 0)}")
    print("   • Each discovery stored with proof hash")
    print("   • Linked to Tasc execution for traceability")
    print()
    print("🔗 Connections:")
    print("   Complex Numbers ──→ Fractals (Mandelbrot, Julia sets)")
    print("                  ──→ Quantum Mechanics (wave functions)")
    print("                  ──→ Signal Processing (Fourier transforms)")
    print("                  ──→ Control Theory (transfer functions)")
    print("                  ──→ Electrical Engineering (AC circuits)")
    print()
    print("💡 Next Complex Horizons:")
    print("   • Euler's formula deep dive: e^(iθ) = cos(θ) + i·sin(θ)")
    print("   • Complex division using conjugates")
    print("   • Polar form: z = r·e^(iθ)")
    print("   • De Moivre's Theorem: (cos θ + i sin θ)ⁿ = cos(nθ) + i sin(nθ)")
    print("   • Complex roots and polynomials")
    print("   • Mandelbrot set deep dive")
    print()
    print("🎭 Philosophy:")
    print("   Complex numbers aren't 'imaginary' - they're a 2D extension of reals!")
    print("   They unify algebra, geometry, and analysis.")
    print("   i may seem strange, but it makes mathematics complete!")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
