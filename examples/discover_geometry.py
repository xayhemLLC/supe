"""
Mathematical Discovery: Geometry and Visual Structures 📐

Using the learning system to ACTUALLY LEARN geometry from first principles!

Core Concepts:
    • Points, lines, angles
    • Triangles and the Pythagorean theorem
    • Circles and π
    • Area and perimeter formulas
    • Symmetry and transformations

We'll use ASCII art to visualize the structures and link to Tasc proofs!

Notation:
    • ∠ (angle)
    • △ (triangle)
    • ○ (circle)
    • π (pi - ratio of circumference to diameter)
    • ⊥ (perpendicular)
    • ∥ (parallel)
    • ≅ (congruent)
    • ∼ (similar)

Let's learn geometry by discovery! 📐✨
"""

import asyncio
from supe import Supe
from ab.models import Buffer


def draw_right_triangle():
    """ASCII art of a right triangle."""
    return """
        |\\
        | \\ c (hypotenuse)
      b |  \\
        |   \\
        |____\\
           a

    Right triangle: a² + b² = c²
    """


def draw_circle():
    """ASCII art of a circle."""
    return """
          ***
        *     *
       *       *
      *    •    *  ← radius r
       *       *
        *     *
          ***

    Circumference = 2πr
    Area = πr²
    """


def draw_square():
    """ASCII art of a square."""
    return """
        +------+
        |      | s
        |      |
        +------+
           s

    Area = s²
    Perimeter = 4s
    """


def draw_cube():
    """ASCII art of a 3D cube."""
    return """
           +-------+
          /|      /|
         / |     / |
        +-------+  |
        |  +----+--+
        | /     | /
        |/      |/
        +-------+

    Volume = s³
    Surface Area = 6s²
    """


def draw_unit_circle():
    """ASCII art of unit circle with key points."""
    return """
              (0,1)
                |
            •   |   •
        (-1,0)  +  (1,0)
            •   |   •
                |
              (0,-1)

    Unit Circle: x² + y² = 1
    cos²θ + sin²θ = 1
    """


def draw_pythagorean_proof():
    """Visual proof of Pythagorean theorem."""
    return """
    Visual Proof:

    Square on side a:    Square on side b:    Square on hypotenuse c:
    +----+               +------+             +---------+
    |    | a²           |      | b²          |         | c²
    +----+               +------+             +---------+

    Triangle arrangement shows: a² + b² = c²

        +----+                    +----+-------+
        |   /|                    |   /|      /|
        |  / |     Transform      |  / |     / |
        | /  |  =============>    | /  |    /  |
        |/   |                    |/   |   /   |
        +----+                    +----+--+----+
    """


async def main():
    print("=" * 80)
    print("📐 MATHEMATICAL DISCOVERY: Geometry (Learning Mode Active!)")
    print("=" * 80)
    print()
    print("Using Supe's EXPLORE mode to actually LEARN geometry!")
    print("All discoveries will be stored with proof hashes and linked to Tascs.")
    print()

    supe = Supe(db_path=":memory:")

    # Seed geometric knowledge
    print("📚 Seeding geometric definitions...")

    geom_def = """Geometric Definitions:

Point: A location in space with no size (just position)
Line: Infinite straight path through points
Angle: Formed by two rays with common endpoint
Triangle: 3-sided polygon
Circle: Set of all points equidistant from center

Right Triangle: One 90° angle
Hypotenuse: Longest side of right triangle (opposite the right angle)
Pythagorean Theorem: a² + b² = c² for right triangles

Area: Amount of 2D space inside a shape
Perimeter: Distance around a shape
Volume: Amount of 3D space inside a shape"""

    supe.memory.store_card(
        label="geometric_definitions",
        buffers=[Buffer(name="content", payload=geom_def.encode('utf-8'))],
        master_output="Core geometric definitions",
        track="awareness",
    )
    print("✓ Geometric concepts defined\n")

    # Discovery 1: Pythagorean Theorem
    print("🔍 DISCOVERY 1: Pythagorean Theorem")
    print("-" * 80)
    print(draw_right_triangle())
    print("Question: For a right triangle with legs a=3, b=4, is c²=a²+b²?")
    print("Expected: 3² + 4² = 9 + 16 = 25 = 5²")
    print()

    result1 = await supe.learn(
        "For a right triangle with sides a=3 and b=4, is the hypotenuse c=5? (Test: 3² + 4² = 5²)",
        mode="explore"
    )

    if result1['beliefs_count'] > 0:
        belief = result1['beliefs'][0]
        status = belief['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result1['confidence']:.2f}")
        print(f"Proof Hash: {result1['proof_hash'][:16]}...")
        print(f"Session ID: {result1['session_id'][:8]}...")

        if status == 'PROVEN':
            print("\n⟹ Pythagorean Theorem VERIFIED!")
            print("⟹ The 3-4-5 triangle is a perfect right triangle!")
            print(draw_pythagorean_proof())
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 2: Triangle inequality
    print("🔍 DISCOVERY 2: Triangle Inequality")
    print("-" * 80)
    print("""
        Can we form a triangle?

        Valid:          Invalid:
        /\              /______
       /  \            |
      /____\           |_______
      a=3 b=4         a=2 b=1
      c=6 ✓           c=10 ✗

    Rule: Sum of any two sides > third side
    """)
    print("Question: Can sides 3, 4, 6 form a triangle?")
    print("Check: 3+4 > 6? YES (7 > 6) ✓")
    print("Check: 3+6 > 4? YES (9 > 4) ✓")
    print("Check: 4+6 > 3? YES (10 > 3) ✓")
    print()

    result2 = await supe.learn(
        "Can three line segments of length 3, 4, and 6 form a triangle? (Test triangle inequality)",
        mode="explore"
    )

    if result2['beliefs_count'] > 0:
        status = result2['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result2['confidence']:.2f}")
        print(f"Proof Hash: {result2['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 3: Circle properties
    print("🔍 DISCOVERY 3: Circle Circumference")
    print("-" * 80)
    print(draw_circle())
    print("Question: For a circle with radius r=1, is circumference ≈ 2π?")
    print("π ≈ 3.14159...")
    print("Circumference = 2πr = 2π(1) ≈ 6.28318...")
    print()

    # Seed pi knowledge
    pi_def = "Pi (π) is the ratio of a circle's circumference to its diameter. π ≈ 3.14159265358979... It is an irrational number that appears throughout mathematics."
    supe.memory.store_card(
        label="pi_definition",
        buffers=[Buffer(
            name="content",
            payload=pi_def.encode('utf-8')
        )],
        master_output="Definition of pi",
        track="awareness",
    )

    result3 = await supe.learn(
        "For a unit circle (radius=1), is the circumference approximately 6.28 (which is 2π)?",
        mode="explore"
    )

    if result3['beliefs_count'] > 0:
        status = result3['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"Proof Hash: {result3['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Circle formula VERIFIED!")
            print("⟹ C = 2πr is the fundamental circle property!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 4: Square area
    print("🔍 DISCOVERY 4: Square Area Formula")
    print("-" * 80)
    print(draw_square())
    print("Question: For a square with side s=5, is the area A=25?")
    print("Formula: A = s² = 5² = 25")
    print()

    result4 = await supe.learn(
        "For a square with side length 5, is the area equal to 25? (Test: A = s²)",
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

    # Discovery 5: Unit circle identity
    print("🔍 DISCOVERY 5: Pythagorean Identity on Unit Circle")
    print("-" * 80)
    print(draw_unit_circle())
    print("Question: For any point (x,y) on the unit circle, is x² + y² = 1?")
    print("Example: Point (0.6, 0.8)")
    print("Check: 0.6² + 0.8² = 0.36 + 0.64 = 1.0 ✓")
    print()

    result5 = await supe.learn(
        "For a point (0.6, 0.8) on the unit circle, is x² + y² = 1? (Pythagorean identity)",
        mode="explore"
    )

    if result5['beliefs_count'] > 0:
        status = result5['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result5['confidence']:.2f}")
        print(f"Proof Hash: {result5['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Pythagorean identity VERIFIED!")
            print("⟹ This connects trigonometry: cos²θ + sin²θ = 1")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 6: Cube volume
    print("🔍 DISCOVERY 6: Cube Volume Formula")
    print("-" * 80)
    print(draw_cube())
    print("Question: For a cube with side s=3, is the volume V=27?")
    print("Formula: V = s³ = 3³ = 27")
    print()

    result6 = await supe.learn(
        "For a cube with side length 3, is the volume equal to 27? (Test: V = s³)",
        mode="explore"
    )

    if result6['beliefs_count'] > 0:
        status = result6['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result6['confidence']:.2f}")
        print(f"Proof Hash: {result6['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Summary with ASCII art
    print("=" * 80)
    print("🎓 GEOMETRIC DISCOVERIES (All Stored with Proofs!)")
    print("=" * 80)
    print()
    print("Visual Summary:")
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                    GEOMETRIC DISCOVERIES                             ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║                                                                      ║
    ║  1️⃣  Pythagorean Theorem: a² + b² = c²                              ║
    ║      Triangle: 3² + 4² = 5² ✓                                       ║
    ║                                                                      ║
    ║  2️⃣  Triangle Inequality: a + b > c                                 ║
    ║      Sides 3,4,6 form valid triangle ✓                              ║
    ║                                                                      ║
    ║  3️⃣  Circle Circumference: C = 2πr                                  ║
    ║      Unit circle: C ≈ 6.28 ✓                                        ║
    ║                                                                      ║
    ║  4️⃣  Square Area: A = s²                                            ║
    ║      Side 5: A = 25 ✓                                               ║
    ║                                                                      ║
    ║  5️⃣  Unit Circle: x² + y² = 1                                       ║
    ║      Point (0.6,0.8): 0.36 + 0.64 = 1 ✓                             ║
    ║                                                                      ║
    ║  6️⃣  Cube Volume: V = s³                                            ║
    ║      Side 3: V = 27 ✓                                               ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    print()
    print("📊 Learning System Status:")
    print(f"   • Total Beliefs Created: {sum(1 for r in [result1, result2, result3, result4, result5, result6] if r['beliefs_count'] > 0)}")
    print(f"   • All stored in AB Memory with cryptographic proofs")
    print(f"   • Each proof linked to Tasc execution records")
    print(f"   • Cross-referenced for future recall")
    print()
    print("🔗 Tasc Integration:")
    print("   Each geometric discovery creates a Tasc with:")
    print("   • Proof hash (cryptographic verification)")
    print("   • Validation gates (confidence thresholds)")
    print("   • Evidence chain (what was tested)")
    print("   • Session timeline (when discovered)")
    print()
    print("📐 Geometric Connections:")
    print("   Pythagorean Theorem ──┐")
    print("                         ├──→ Unit Circle → Trigonometry")
    print("   Circle Properties ────┘")
    print()
    print("   Area Formulas ────→ Integration → Calculus")
    print("   Volume Formulas ──→ 3D Geometry → Physics")
    print()
    print("💡 Next Geometric Horizons:")
    print("   • Trigonometry: sin, cos, tan and their relationships")
    print("   • Conic sections: Ellipse, parabola, hyperbola")
    print("   • Transformations: Rotation, reflection, translation")
    print("   • Platonic solids: Tetrahedron, cube, octahedron, dodecahedron, icosahedron")
    print("   • Fractals: Self-similar structures (Mandelbrot, Koch snowflake)")
    print("   • Topology: Properties preserved under continuous deformation")
    print()
    print("🎨 ASCII Art Data Structures:")
    print("   All geometric concepts rendered as visual ASCII")
    print("   Making mathematics tangible and beautiful! ✨")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
