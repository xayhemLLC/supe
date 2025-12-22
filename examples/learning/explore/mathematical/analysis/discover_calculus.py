"""
Mathematical Discovery: Calculus - The Mathematics of Change 📈

Calculus is the study of continuous change - connecting algebra, geometry, and motion!

Core Concepts:
    • Limits: What happens as we approach a value
    • Derivatives: Instantaneous rate of change (slope)
    • Integrals: Accumulation (area under curve)
    • Fundamental Theorem: Derivatives and integrals are inverses

Properties to Discover:
    • Limit definition of derivative: f'(x) = lim[h→0] (f(x+h) - f(x))/h
    • Power rule: d/dx(x^n) = n·x^(n-1)
    • Integral as antiderivative: ∫f'(x)dx = f(x) + C
    • Fundamental theorem: ∫[a,b] f'(x)dx = f(b) - f(a)
    • Chain rule: d/dx(f(g(x))) = f'(g(x))·g'(x)

Let's DISCOVER calculus through exploration! 📊
"""

import asyncio
from supe import Supe
from ab.models import Buffer


def draw_limit_concept():
    return """
    Limit Concept: lim[x→2] f(x) = L

    As x approaches 2, f(x) approaches L:

           f(x)
            │
         L  ├─────●     ← f(x) getting closer to L
            │   ·   ·
            │  ·     ·
            │ ·       ·
            │·         ·
          ──┼─────────────── x
            0    2

    Example: lim[x→2] (x² - 4)/(x - 2)

    Direct substitution: 0/0 (indeterminate!)

    Factor: (x² - 4)/(x - 2) = (x + 2)(x - 2)/(x - 2) = x + 2

    lim[x→2] (x + 2) = 4 ✓

    Key: Limit describes behavior NEAR a point, not AT it!
    """


def draw_derivative_concept():
    return """
    Derivative: f'(x) = lim[h→0] (f(x+h) - f(x))/h

    Geometric interpretation: SLOPE of tangent line

           f(x)
            │      Curve
            │     ╱
            │    ╱    ← Tangent line (slope = f'(x))
            │   ╱╱
            │  ╱ ╱
            │ ╱  ╱
            │╱   ╱
          ──┼────────── x
            0   x

    Example: f(x) = x²

    f'(x) = lim[h→0] ((x+h)² - x²)/h
          = lim[h→0] (x² + 2xh + h² - x²)/h
          = lim[h→0] (2xh + h²)/h
          = lim[h→0] (2x + h)
          = 2x ✓

    At x=3: f'(3) = 6 (slope of tangent)
    """


def draw_power_rule():
    return """
    Power Rule: d/dx(x^n) = n·x^(n-1)

    Examples:
    • d/dx(x²) = 2x
    • d/dx(x³) = 3x²
    • d/dx(x⁴) = 4x³
    • d/dx(√x) = d/dx(x^(1/2)) = (1/2)x^(-1/2) = 1/(2√x)

    Pattern:
    x⁵  →  5x⁴   (bring down exponent, subtract 1)
    x⁴  →  4x³
    x³  →  3x²
    x²  →  2x
    x¹  →  1
    x⁰  →  0

    Visual (f(x) = x²):

         f(x)
          │        ╱
          │      ╱
          │    ╱   ← Curve: y = x²
          │  ╱
          │╱       Derivative: y' = 2x
        ──┼────────── x
          0

    Steeper as x increases!
    """


def draw_integral_concept():
    return """
    Integral: ∫f(x)dx = Area under curve

    Riemann sum approximation:

           f(x)
            │   ┌─┐
            │   │ │┌─┐
            │   │ ││ │┌─┐
            │   │ ││ ││ │
            │   │ ││ ││ │
          ──┼───┴─┴┴─┴┴─┴──── x
            a             b

    As rectangles get thinner → exact area!

    ∫[a,b] f(x)dx = lim[n→∞] Σ f(xᵢ)·Δx

    Example: ∫[0,2] x dx

    Geometric: Area of triangle
         height = 2, base = 2
         Area = (1/2)·2·2 = 2

    Analytical: ∫x dx = x²/2 + C
         ∫[0,2] x dx = [x²/2]₀² = 4/2 - 0 = 2 ✓
    """


def draw_fundamental_theorem():
    return """
    Fundamental Theorem of Calculus

    Part 1: d/dx(∫[a,x] f(t)dt) = f(x)
    (Derivative of integral = original function)

    Part 2: ∫[a,b] f'(x)dx = f(b) - f(a)
    (Integral of derivative = net change)

    Connection:

    DERIVATIVE        INTEGRAL
        │               │
        │   inverse     │
        │◄──────────────┤
        │               │
        │   inverse     │
        ├──────────────►│
        │               │
      SLOPE           AREA

    Example:
    f(x) = x³
    f'(x) = 3x²    ← Derivative

    ∫[0,2] 3x² dx = [x³]₀² = 8 - 0 = 8 ✓

    Net change in f from 0 to 2!
    """


def draw_chain_rule():
    return """
    Chain Rule: d/dx(f(g(x))) = f'(g(x))·g'(x)

    Composition of functions:

    x ──→ g(x) ──→ f(g(x))
      g        f

    Rates multiply!

    Example: h(x) = (x² + 1)³

    Outer function: f(u) = u³
    Inner function: g(x) = x² + 1

    h'(x) = f'(g(x))·g'(x)
          = 3(x² + 1)²·2x
          = 6x(x² + 1)² ✓

    Intuition: "derivative of outside × derivative of inside"

    Another example: sin(x²)
    d/dx(sin(x²)) = cos(x²)·2x
    """


def draw_optimization():
    return """
    Optimization: Finding Maxima and Minima

    Critical points: Where f'(x) = 0 or undefined

           f(x)
            │     Maximum
            │       ●
            │      ╱ ╲
            │     ╱   ╲
            │    ╱     ╲
            │   ╱       ╲ Minimum
            │  ╱         ●
          ──┼──────────────── x
            a    c₁    c₂   b

    Test: f''(x) < 0 → maximum (concave down)
          f''(x) > 0 → minimum (concave up)

    Example: f(x) = -x² + 4x - 1
    f'(x) = -2x + 4 = 0
    x = 2 (critical point)

    f''(x) = -2 < 0 → MAXIMUM at x = 2 ✓
    f(2) = -4 + 8 - 1 = 3

    Applications:
    • Minimize cost
    • Maximize profit
    • Minimize distance
    • Maximize efficiency
    """


def draw_mean_value_theorem():
    return """
    Mean Value Theorem

    If f is continuous on [a,b] and differentiable on (a,b),
    then ∃c ∈ (a,b) such that:

    f'(c) = (f(b) - f(a))/(b - a)

    Geometric: There exists a point where tangent is parallel to secant!

           f(x)
            │       ● f(b)
            │      ╱
            │     ╱ ╱  ← Tangent at c
            │    ╱ ╱
            │   ╱ ╱
            │  ╱ ╱
            │ ●╱    f(a)
          ──┼────────── x
            a  c    b

    Secant slope: (f(b) - f(a))/(b - a)
    Tangent slope at c: f'(c)

    They're equal for some c!

    Consequence: If f'(x) = 0 everywhere, then f is constant.
    """


async def main():
    print("=" * 80)
    print("📈 MATHEMATICAL DISCOVERY: Calculus - Mathematics of Change")
    print("=" * 80)
    print()
    print("Using EXPLORE mode to discover calculus fundamentals!")
    print("From limits to derivatives to integrals!")
    print()

    # Use in-memory database for exploration
    supe = Supe(db_path=":memory:")

    # Seed calculus knowledge
    print("📚 Seeding calculus definitions...")

    calculus_defs = """Calculus: The Mathematics of Continuous Change

Foundation - Limits:
    Definition: lim[x→a] f(x) = L means f(x) approaches L as x approaches a
    Notation: lim[x→a] f(x)
    Properties:
        • lim[x→a] (f(x) + g(x)) = lim[x→a] f(x) + lim[x→a] g(x)
        • lim[x→a] c·f(x) = c·lim[x→a] f(x)
        • lim[x→a] f(x)·g(x) = (lim[x→a] f(x))·(lim[x→a] g(x))

Differential Calculus - Derivatives:
    Definition: f'(x) = lim[h→0] (f(x+h) - f(x))/h
    Notation: f'(x), df/dx, d/dx f(x)
    Interpretation: Instantaneous rate of change (slope of tangent)

    Rules:
        • Power Rule: d/dx(x^n) = n·x^(n-1)
        • Sum Rule: d/dx(f + g) = f' + g'
        • Product Rule: d/dx(f·g) = f'·g + f·g'
        • Quotient Rule: d/dx(f/g) = (f'·g - f·g')/g²
        • Chain Rule: d/dx(f(g(x))) = f'(g(x))·g'(x)

    Common Derivatives:
        • d/dx(sin x) = cos x
        • d/dx(cos x) = -sin x
        • d/dx(e^x) = e^x
        • d/dx(ln x) = 1/x

Integral Calculus - Integrals:
    Definition: ∫[a,b] f(x)dx = lim[n→∞] Σ f(xᵢ)·Δx (Riemann sum)
    Notation: ∫f(x)dx (indefinite), ∫[a,b] f(x)dx (definite)
    Interpretation: Area under curve, accumulation

    Rules:
        • ∫(f + g)dx = ∫f dx + ∫g dx
        • ∫c·f dx = c·∫f dx
        • ∫x^n dx = x^(n+1)/(n+1) + C (n ≠ -1)

    Common Integrals:
        • ∫sin x dx = -cos x + C
        • ∫cos x dx = sin x + C
        • ∫e^x dx = e^x + C
        • ∫1/x dx = ln|x| + C

Fundamental Theorem of Calculus:
    Part 1: d/dx(∫[a,x] f(t)dt) = f(x)
    Part 2: ∫[a,b] f'(x)dx = f(b) - f(a)

    Consequence: Differentiation and integration are inverse operations!

Applications:
    • Physics: velocity, acceleration, work, energy
    • Optimization: maximize profit, minimize cost
    • Probability: continuous distributions (PDF, CDF)
    • Economics: marginal analysis
    • Machine Learning: gradient descent, backpropagation
    • Engineering: circuits, heat transfer, fluid dynamics"""

    supe.memory.store_card(
        label="calculus_fundamentals",
        buffers=[Buffer(name="content", payload=calculus_defs.encode('utf-8'))],
        master_output="Calculus fundamentals: limits, derivatives, integrals",
        track="awareness",
    )
    print("✓ Calculus concepts defined\n")

    # Discovery 1: Power Rule
    print("🔍 DISCOVERY 1: Power Rule")
    print("-" * 80)
    print(draw_power_rule())

    result1 = await supe.learn(
        "Is d/dx(x^n) = n·x^(n-1)? (Power rule for derivatives)",
        mode="explore"
    )

    print(f"Question: Is d/dx(x^n) = n·x^(n-1)?")
    print()
    print("Example: d/dx(x³) = 3x²")
    print("  f(x) = x³")
    print("  f(x+h) = (x+h)³ = x³ + 3x²h + 3xh² + h³")
    print("  (f(x+h) - f(x))/h = (3x²h + 3xh² + h³)/h = 3x² + 3xh + h²")
    print("  lim[h→0] (3x² + 3xh + h²) = 3x² ✓")
    print()

    if result1['beliefs_count'] > 0:
        belief = result1['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result1['confidence']:.2f}")
        print(f"Proof Hash: {result1['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 2: Fundamental Theorem Part 2
    print("🔍 DISCOVERY 2: Fundamental Theorem of Calculus (Part 2)")
    print("-" * 80)
    print(draw_fundamental_theorem())

    result2 = await supe.learn(
        "Is ∫[a,b] f'(x)dx = f(b) - f(a)? (Fundamental theorem of calculus)",
        mode="explore"
    )

    print(f"Question: Is ∫[a,b] f'(x)dx = f(b) - f(a)?")
    print()
    print("Example: f(x) = x², f'(x) = 2x")
    print("  ∫[1,3] 2x dx = [x²]₁³ = 9 - 1 = 8")
    print("  f(3) - f(1) = 9 - 1 = 8 ✓")
    print()

    if result2['beliefs_count'] > 0:
        belief = result2['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result2['confidence']:.2f}")
        print(f"Proof Hash: {result2['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 3: Chain Rule
    print("🔍 DISCOVERY 3: Chain Rule")
    print("-" * 80)
    print(draw_chain_rule())

    result3 = await supe.learn(
        "Is d/dx(f(g(x))) = f'(g(x))·g'(x)? (Chain rule for composition)",
        mode="explore"
    )

    print(f"Question: Is d/dx(f(g(x))) = f'(g(x))·g'(x)?")
    print()
    print("Example: h(x) = (x² + 1)³")
    print("  f(u) = u³, f'(u) = 3u²")
    print("  g(x) = x² + 1, g'(x) = 2x")
    print("  h'(x) = 3(x² + 1)²·2x = 6x(x² + 1)² ✓")
    print()

    if result3['beliefs_count'] > 0:
        belief = result3['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"Proof Hash: {result3['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 4: Derivative of sine
    print("🔍 DISCOVERY 4: Derivative of Sine")
    print("-" * 80)
    print("""
    Derivative of sin(x): d/dx(sin x) = cos x

    Proof sketch using limit definition:

    d/dx(sin x) = lim[h→0] (sin(x+h) - sin x)/h

    Using angle addition: sin(x+h) = sin x cos h + cos x sin h

    = lim[h→0] (sin x cos h + cos x sin h - sin x)/h
    = lim[h→0] (sin x(cos h - 1) + cos x sin h)/h
    = sin x·lim[h→0] (cos h - 1)/h + cos x·lim[h→0] sin h/h
    = sin x·0 + cos x·1
    = cos x ✓

    Key limits:
    • lim[h→0] sin h/h = 1
    • lim[h→0] (cos h - 1)/h = 0

    Visual connection to unit circle!
    """)

    result4 = await supe.learn(
        "Is d/dx(sin x) = cos x? (Derivative of sine function)",
        mode="explore"
    )

    print(f"Question: Is d/dx(sin x) = cos x?")
    print()
    print("At x = 0: sin'(0) = cos(0) = 1")
    print("At x = π/2: sin'(π/2) = cos(π/2) = 0")
    print("At x = π: sin'(π) = cos(π) = -1 ✓")
    print()

    if result4['beliefs_count'] > 0:
        belief = result4['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result4['confidence']:.2f}")
        print(f"Proof Hash: {result4['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 5: Product Rule
    print("🔍 DISCOVERY 5: Product Rule")
    print("-" * 80)
    print("""
    Product Rule: d/dx(f·g) = f'·g + f·g'

    "Derivative of product = first' × second + first × second'"

    Proof from limit definition:

    d/dx(f(x)g(x)) = lim[h→0] (f(x+h)g(x+h) - f(x)g(x))/h

    Add and subtract f(x+h)g(x):
    = lim[h→0] (f(x+h)g(x+h) - f(x+h)g(x) + f(x+h)g(x) - f(x)g(x))/h
    = lim[h→0] [f(x+h)(g(x+h) - g(x))/h + g(x)(f(x+h) - f(x))/h]
    = f(x)·g'(x) + g(x)·f'(x) ✓

    Example: d/dx(x²·sin x)
    f(x) = x², f'(x) = 2x
    g(x) = sin x, g'(x) = cos x

    (x²·sin x)' = 2x·sin x + x²·cos x ✓
    """)

    result5 = await supe.learn(
        "Is d/dx(f·g) = f'·g + f·g'? (Product rule for derivatives)",
        mode="explore"
    )

    print(f"Question: Is d/dx(f·g) = f'·g + f·g'?")
    print()
    print("Example: d/dx(x·e^x)")
    print("  f = x, f' = 1")
    print("  g = e^x, g' = e^x")
    print("  (x·e^x)' = 1·e^x + x·e^x = e^x(1 + x) ✓")
    print()

    if result5['beliefs_count'] > 0:
        belief = result5['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result5['confidence']:.2f}")
        print(f"Proof Hash: {result5['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Visualizations
    print("=" * 80)
    print("🎨 CALCULUS VISUALIZATIONS")
    print("=" * 80)
    print()

    print("📍 Limit Concept:")
    print(draw_limit_concept())
    print()

    print("📊 Derivative (Tangent Slope):")
    print(draw_derivative_concept())
    print()

    print("∫ Integral (Area Under Curve):")
    print(draw_integral_concept())
    print()

    print("🔗 Fundamental Theorem:")
    print(draw_fundamental_theorem())
    print()

    print("🎯 Optimization:")
    print(draw_optimization())
    print()

    print("📐 Mean Value Theorem:")
    print(draw_mean_value_theorem())
    print()

    # Summary
    print("=" * 80)
    print("🎓 CALCULUS DISCOVERIES")
    print("=" * 80)
    print()

    total_beliefs = sum(r['beliefs_count'] for r in [result1, result2, result3, result4, result5])

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                    CALCULUS FUNDAMENTALS                             ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║                                                                      ║")
    print("║  Limits:                                                             ║")
    print("║    lim[x→a] f(x) = L                                                ║")
    print("║                                                                      ║")
    print("║  Derivatives:                                                        ║")
    print("║    • Definition: f'(x) = lim[h→0] (f(x+h) - f(x))/h                 ║")
    print("║    • Power Rule: d/dx(x^n) = n·x^(n-1)                              ║")
    print("║    • Chain Rule: d/dx(f(g(x))) = f'(g(x))·g'(x)                     ║")
    print("║    • Product Rule: d/dx(f·g) = f'·g + f·g'                          ║")
    print("║    • d/dx(sin x) = cos x                                            ║")
    print("║                                                                      ║")
    print("║  Integrals:                                                          ║")
    print("║    • ∫f(x)dx = antiderivative of f                                  ║")
    print("║    • ∫[a,b] f(x)dx = area under curve                               ║")
    print("║                                                                      ║")
    print("║  Fundamental Theorem:                                                ║")
    print("║    ∫[a,b] f'(x)dx = f(b) - f(a)                                     ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    print(f"🌟 What We Learned:")
    print(f"   • Total beliefs formed: {total_beliefs}")
    print(f"   • Each discovery stored with proof hash")
    print(f"   • Linked to Tasc execution for traceability")
    print()

    print("🔗 Connections:")
    print("   Calculus ──→ Physics (motion, forces, energy)")
    print("            ──→ Optimization (ML, economics)")
    print("            ──→ Probability (continuous distributions)")
    print("            ──→ Geometry (curves, surfaces)")
    print("            ──→ Differential Equations (modeling)")
    print()

    print("💡 Next Calculus Horizons:")
    print("   • Multivariable calculus (partial derivatives)")
    print("   • Vector calculus (gradient, divergence, curl)")
    print("   • Differential equations (ODEs, PDEs)")
    print("   • Taylor series (polynomial approximations)")
    print("   • Laplace transforms")
    print()

    print("🎭 Philosophy:")
    print("   Calculus makes infinity rigorous!")
    print("   Instantaneous rate = limit of average rates.")
    print("   Integration = infinite sum of infinitesimals.")
    print("   FTC: Differentiation and integration are inverses!")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
