"""
Mathematical Discovery: Trigonometry - The Mathematics of Angles and Waves 〰️

Trigonometry connects geometry, algebra, and analysis through circular motion!

Core Concept:
    The unit circle: (cos θ, sin θ) traces a circle as θ varies
    Every angle θ corresponds to a unique point on the unit circle

Fundamental Identities:
    • sin²θ + cos²θ = 1  (Pythagorean identity - already proven!)
    • tan θ = sin θ / cos θ
    • sin(-θ) = -sin(θ)  (odd function)
    • cos(-θ) = cos(θ)   (even function)

Sum Formulas:
    • sin(α + β) = sin(α)cos(β) + cos(α)sin(β)
    • cos(α + β) = cos(α)cos(β) - sin(α)sin(β)

Connection to Complex Numbers:
    • e^(iθ) = cos(θ) + i·sin(θ)  (Euler's formula)
    • cos(θ) = (e^(iθ) + e^(-iθ))/2
    • sin(θ) = (e^(iθ) - e^(-iθ))/2i

Applications:
    • Wave phenomena (sound, light, quantum mechanics)
    • Signal processing (Fourier analysis)
    • Navigation and surveying
    • Computer graphics and animation
    • Oscillations and periodic motion

Let's LEARN trigonometry through exploration! 〰️✨
"""

import asyncio
from supe import Supe
from ab.models import Buffer


def draw_unit_circle_trig():
    """Unit circle with trigonometric values."""
    return """
    Unit Circle with Trig Values:

                90° (π/2)
              sin=1, cos=0
                   |
        135° •     |     • 45°
             \\     |     /
              \\    |    /
    180° ------+-------+------ 0°/360°
    sin=0      |       |       sin=0
    cos=-1     |       |       cos=1
              /    |    \\
             /     |     \\
        225° •     |     • 315°
                   |
                270° (3π/2)
              sin=-1, cos=0

    Key Points:
    • 0°:   (cos,sin) = (1, 0)
    • 90°:  (cos,sin) = (0, 1)
    • 180°: (cos,sin) = (-1, 0)
    • 270°: (cos,sin) = (0, -1)
    """


def draw_right_triangle_trig():
    """Right triangle with trig ratios."""
    return """
    Right Triangle Trigonometry:

             /|
        c   / | b (opposite)
           /  |
          / θ |
         /____|
            a
        (adjacent)

    Definitions:
    • sin(θ) = opposite/hypotenuse = b/c
    • cos(θ) = adjacent/hypotenuse = a/c
    • tan(θ) = opposite/adjacent = b/a

    Reciprocals:
    • csc(θ) = 1/sin(θ) = c/b
    • sec(θ) = 1/cos(θ) = c/a
    • cot(θ) = 1/tan(θ) = a/b
    """


def draw_sine_wave():
    """ASCII art of sine wave."""
    return """
    Sine Wave: y = sin(x)

     1 •       •••
         •   •     •   •
          • •       • •
    0 ─────•─────────•─────────•────> x
            •       •
             •     •   •
              •••       •••
    -1              •

    Properties:
    • Amplitude: 1
    • Period: 2π
    • Odd function: sin(-x) = -sin(x)
    • Zero crossings: x = nπ (n ∈ ℤ)
    • Peaks at: x = π/2 + 2πn
    • Troughs at: x = -π/2 + 2πn
    """


def draw_cosine_wave():
    """ASCII art of cosine wave."""
    return """
    Cosine Wave: y = cos(x)

     1 ••         ••
          •     •  •     •
           •   •    •   •
    0 ──────•─────────•──────> x
             •       •
              •     •
               •••••

    -1

    Properties:
    • Amplitude: 1
    • Period: 2π
    • Even function: cos(-x) = cos(x)
    • Zero crossings: x = π/2 + nπ (n ∈ ℤ)
    • cos(x) = sin(x + π/2)  (phase shift)
    """


def draw_tangent_function():
    """ASCII art of tangent function."""
    return """
    Tangent Function: y = tan(x)

           |
        • || •
       •  ||  •
      •   ||   •        Asymptotes
     •    ||    •       at x = π/2 + nπ
    •     ||     •
    ──────||──────────> x
    •     ||     •
     •    ||    •
      •   ||   •
       •  ||  •
        • || •
           |

    Properties:
    • Period: π (not 2π!)
    • Odd function: tan(-x) = -tan(x)
    • Undefined at: x = π/2 + nπ
    • tan(θ) = sin(θ)/cos(θ)
    """


def draw_euler_formula_connection():
    """Connect Euler's formula to trig."""
    return """
    Euler's Formula: e^(iθ) = cos(θ) + i·sin(θ)

    Unit Circle in Complex Plane:
                 i
                 |
             •   |   •
         •       |       •
     •           +           •  Real axis
         •       |       •
             •   |   •
                 |
                -i

    As θ goes from 0 to 2π:
    • e^(iθ) traces the unit circle
    • Real part = cos(θ)
    • Imaginary part = sin(θ)

    Beautiful Consequences:
    • e^(iπ) = -1  (θ = π gives cos(π) + i·sin(π) = -1 + 0i)
    • e^(iπ) + 1 = 0  (Euler's identity!)
    • cos(θ) = (e^(iθ) + e^(-iθ))/2
    • sin(θ) = (e^(iθ) - e^(-iθ))/(2i)
    """


def draw_wave_interference():
    """Show wave superposition."""
    return """
    Wave Interference: sin(x) + sin(2x)

        ••
       •  •
      •    •   ••
     •      • •  •
    •        •    •         Constructive
    ─────────────────────>  interference
    •        •    •         (waves add)
     •      • •  •
      •    •   ••
       •  •
        ••

    Applications:
    • Sound waves (harmony, beats)
    • Light waves (diffraction patterns)
    • Quantum mechanics (wave functions)
    • Signal processing (Fourier analysis)
    """


async def main():
    print("=" * 80)
    print("〰️  MATHEMATICAL DISCOVERY: Trigonometry - Angles, Waves, and Circles")
    print("=" * 80)
    print()
    print("Using EXPLORE mode to discover trigonometric identities!")
    print("Connecting geometry → complex numbers → wave phenomena")
    print()

    supe = Supe(db_path=":memory:")

    # Seed trigonometric knowledge
    print("📚 Seeding trigonometric definitions...")

    trig_def = """Trigonometry: Mathematics of Angles and Periodic Functions

Core Definitions (Right Triangle):
- sine(θ) = opposite/hypotenuse
- cosine(θ) = adjacent/hypotenuse
- tangent(θ) = opposite/adjacent = sin(θ)/cos(θ)

Unit Circle Definition:
- Point on unit circle at angle θ: (cos θ, sin θ)
- This extends trig functions to all real numbers!

Fundamental Identity:
- sin²θ + cos²θ = 1 (Pythagorean identity)

Reciprocal Functions:
- cosecant(θ) = 1/sin(θ)
- secant(θ) = 1/cos(θ)
- cotangent(θ) = 1/tan(θ) = cos(θ)/sin(θ)

Symmetry:
- sin(-θ) = -sin(θ)  (odd function)
- cos(-θ) = cos(θ)   (even function)
- tan(-θ) = -tan(θ)  (odd function)

Periodicity:
- sin(θ + 2π) = sin(θ)
- cos(θ + 2π) = cos(θ)
- tan(θ + π) = tan(θ)

Sum Formulas:
- sin(α + β) = sin(α)cos(β) + cos(α)sin(β)
- cos(α + β) = cos(α)cos(β) - sin(α)sin(β)

Euler's Formula:
- e^(iθ) = cos(θ) + i·sin(θ)"""

    supe.memory.store_card(
        label="trig_definitions",
        buffers=[Buffer(name="content", payload=trig_def.encode('utf-8'))],
        master_output="Trigonometric definitions and identities",
        track="awareness",
    )
    print("✓ Trigonometric concepts defined\n")

    # Discovery 1: Pythagorean identity (we already proved this with unit circle!)
    print("🔍 DISCOVERY 1: Pythagorean Identity")
    print("-" * 80)
    print(draw_unit_circle_trig())
    print("Question: For angle θ = 30° (π/6), is sin²θ + cos²θ = 1?")
    print()
    print("Values: sin(30°) = 0.5, cos(30°) ≈ 0.866")
    print("Check: (0.5)² + (0.866)² = 0.25 + 0.75 = 1.0 ✓")
    print()

    result1 = await supe.learn(
        "For angle 30° with sin(30°)=0.5 and cos(30°)≈0.866, is sin²(30°) + cos²(30°) = 1? (Pythagorean identity)",
        mode="explore"
    )

    if result1['beliefs_count'] > 0:
        status = result1['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result1['confidence']:.2f}")
        print(f"Proof Hash: {result1['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Pythagorean identity VERIFIED!")
            print("⟹ This connects to unit circle: x² + y² = 1")
            print("⟹ Fundamental to ALL of trigonometry!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 2: Tangent definition
    print("🔍 DISCOVERY 2: Tangent as Ratio")
    print("-" * 80)
    print(draw_right_triangle_trig())
    print("Question: Is tan(θ) = sin(θ) / cos(θ)?")
    print()
    print("For θ = 45° (π/4):")
    print("  sin(45°) = cos(45°) = √2/2 ≈ 0.707")
    print("  tan(45°) = 1")
    print("  sin/cos = 0.707/0.707 = 1 ✓")
    print()

    result2 = await supe.learn(
        "Is tan(45°) = sin(45°)/cos(45°)? (Test: 1 = 0.707/0.707)",
        mode="explore"
    )

    if result2['beliefs_count'] > 0:
        status = result2['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result2['confidence']:.2f}")
        print(f"Proof Hash: {result2['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Tangent definition VERIFIED!")
            print("⟹ tan(θ) = sin(θ)/cos(θ) is fundamental!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 3: Sine is odd function
    print("🔍 DISCOVERY 3: Sine is Odd Function")
    print("-" * 80)
    print(draw_sine_wave())
    print("Question: Is sin(-θ) = -sin(θ)? (Odd function property)")
    print()
    print("For θ = 30°:")
    print("  sin(30°) = 0.5")
    print("  sin(-30°) = -0.5")
    print("  Therefore: sin(-30°) = -sin(30°) ✓")
    print()

    result3 = await supe.learn(
        "Is sin(-30°) = -sin(30°)? (Test: -0.5 = -0.5, odd function)",
        mode="explore"
    )

    if result3['beliefs_count'] > 0:
        status = result3['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"Proof Hash: {result3['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 4: Cosine is even function
    print("🔍 DISCOVERY 4: Cosine is Even Function")
    print("-" * 80)
    print(draw_cosine_wave())
    print("Question: Is cos(-θ) = cos(θ)? (Even function property)")
    print()
    print("For θ = 60°:")
    print("  cos(60°) = 0.5")
    print("  cos(-60°) = 0.5")
    print("  Therefore: cos(-60°) = cos(60°) ✓")
    print()

    result4 = await supe.learn(
        "Is cos(-60°) = cos(60°)? (Test: 0.5 = 0.5, even function)",
        mode="explore"
    )

    if result4['beliefs_count'] > 0:
        status = result4['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result4['confidence']:.2f}")
        print(f"Proof Hash: {result4['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 5: Sum formula for sine
    print("🔍 DISCOVERY 5: Sine Sum Formula")
    print("-" * 80)
    print("Question: Is sin(30° + 60°) = sin(30°)cos(60°) + cos(30°)sin(60°)?")
    print()
    print("Left side:  sin(90°) = 1")
    print("Right side: (0.5)(0.5) + (0.866)(0.866)")
    print("          = 0.25 + 0.75 = 1.0 ✓")
    print()

    result5 = await supe.learn(
        "Is sin(30° + 60°) = sin(30°)cos(60°) + cos(30°)sin(60°)? (Sum formula: 1 = 0.25 + 0.75)",
        mode="explore"
    )

    if result5['beliefs_count'] > 0:
        status = result5['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result5['confidence']:.2f}")
        print(f"Proof Hash: {result5['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Sine sum formula VERIFIED!")
            print("⟹ sin(α + β) = sin(α)cos(β) + cos(α)sin(β)")
            print("⟹ This is fundamental for wave analysis!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 6: Euler's formula connection
    print("🔍 DISCOVERY 6: Euler's Formula at θ = π")
    print("-" * 80)
    print(draw_euler_formula_connection())
    print("Question: Does e^(iπ) = cos(π) + i·sin(π) = -1?")
    print()
    print("Calculation:")
    print("  cos(π) = -1")
    print("  sin(π) = 0")
    print("  cos(π) + i·sin(π) = -1 + 0i = -1 ✓")
    print()
    print("This gives: e^(iπ) + 1 = 0 (Euler's identity!)")
    print()

    result6 = await supe.learn(
        "Is e^(iπ) equal to -1? (Euler's formula: cos(π) + i·sin(π) = -1 + 0i)",
        mode="explore"
    )

    if result6['beliefs_count'] > 0:
        status = result6['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result6['confidence']:.2f}")
        print(f"Proof Hash: {result6['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Euler's formula VERIFIED at θ = π!")
            print("⟹ This connects trig to complex exponentials!")
            print("⟹ Foundation of Fourier analysis!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Display visualizations
    print("=" * 80)
    print("🎨 TRIGONOMETRIC VISUALIZATIONS")
    print("=" * 80)
    print()
    print("🔺 Unit Circle:")
    print(draw_unit_circle_trig())
    print()
    print("📐 Right Triangle:")
    print(draw_right_triangle_trig())
    print()
    print("〰️  Sine Wave:")
    print(draw_sine_wave())
    print()
    print("〰️  Cosine Wave:")
    print(draw_cosine_wave())
    print()
    print("📊 Tangent Function:")
    print(draw_tangent_function())
    print()
    print("🌊 Wave Interference:")
    print(draw_wave_interference())
    print()

    # Summary
    print("=" * 80)
    print("🎓 TRIGONOMETRIC DISCOVERIES")
    print("=" * 80)
    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                    TRIGONOMETRY FUNDAMENTALS                         ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║                                                                      ║")
    print("║  Core Identities:                                                    ║")
    print("║    • sin²θ + cos²θ = 1  (Pythagorean identity)                      ║")
    print("║    • tan θ = sin θ / cos θ                                          ║")
    print("║    • 1 + tan²θ = sec²θ                                              ║")
    print("║                                                                      ║")
    print("║  Symmetry:                                                           ║")
    print("║    • sin(-θ) = -sin(θ)  (odd function)                              ║")
    print("║    • cos(-θ) = cos(θ)   (even function)                             ║")
    print("║                                                                      ║")
    print("║  Sum Formulas:                                                       ║")
    print("║    • sin(α + β) = sin(α)cos(β) + cos(α)sin(β)                      ║")
    print("║    • cos(α + β) = cos(α)cos(β) - sin(α)sin(β)                      ║")
    print("║                                                                      ║")
    print("║  Euler Connection:                                                   ║")
    print("║    • e^(iθ) = cos(θ) + i·sin(θ)                                     ║")
    print("║    • e^(iπ) + 1 = 0  (Euler's identity)                             ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("🌟 What We Learned:")
    print(f"   • Total beliefs formed: {sum(1 for r in [result1, result2, result3, result4, result5, result6] if r['beliefs_count'] > 0)}")
    print("   • Each discovery stored with proof hash")
    print("   • Linked to Tasc execution for traceability")
    print()
    print("🔗 Connections:")
    print("   Trigonometry ──→ Geometry (right triangles, unit circle)")
    print("                ──→ Complex Numbers (Euler's formula)")
    print("                ──→ Waves (sine, cosine as oscillations)")
    print("                ──→ Fourier Analysis (decompose signals)")
    print("                ──→ Physics (oscillations, waves, quantum mechanics)")
    print()
    print("💡 Next Trigonometric Horizons:")
    print("   • Double angle formulas: sin(2θ) = 2sin(θ)cos(θ)")
    print("   • Half angle formulas: sin²(θ/2) = (1 - cos θ)/2")
    print("   • Product-to-sum formulas")
    print("   • Inverse trig functions: arcsin, arccos, arctan")
    print("   • Hyperbolic functions: sinh, cosh, tanh")
    print("   • Fourier series: decompose periodic functions")
    print()
    print("🎭 Philosophy:")
    print("   Trigonometry reveals that circular motion is the foundation of waves!")
    print("   The unit circle unifies geometry and periodic phenomena.")
    print("   Euler's formula shows trig functions are exponentials in disguise.")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
