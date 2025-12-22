"""
Mathematical Discovery: Topology - The Mathematics of Continuous Spaces 🌐

Topology studies properties preserved under continuous deformations!

Core Concepts:
    • Topological Space (X, τ): Set X with collection τ of "open sets"
    • Continuous Function: Preimages of open sets are open
    • Homeomorphism: Continuous bijection with continuous inverse
    • Connectedness: Cannot be separated into disjoint open sets
    • Compactness: Every open cover has finite subcover

Properties to Discover:
    • Empty set and X are open
    • Arbitrary unions of open sets are open
    • Finite intersections of open sets are open
    • Continuous functions preserve connectedness
    • Compact spaces are preserved under continuous maps

Let's DISCOVER topology through exploration! ∞
"""

import asyncio
from supe import Supe
from ab.models import Buffer


def draw_topological_space():
    return """
    Topological Space (X, τ)

    "A set X with a notion of 'nearness' defined by open sets τ"

    Example: X = {a, b, c} with discrete topology

         X = {a, b, c}

         τ = {∅, {a}, {b}, {c}, {a,b}, {a,c}, {b,c}, {a,b,c}}

         Every subset is open! (discrete topology)

    Example: X = ℝ with standard topology

         Open sets: (a, b) = {x : a < x < b}

              a          b
         ─────(──────────)─────→
              └──────────┘
               open interval

         NOT open: [a, b] (includes endpoints)

    Axioms for topology τ:
    1. ∅ ∈ τ and X ∈ τ (empty and full set are open)
    2. Arbitrary unions: ⋃ᵢ Uᵢ ∈ τ (unions preserve openness)
    3. Finite intersections: U ∩ V ∈ τ (finite intersections open)

    Visual: Open sets as "blobs" containing points

           ╭─────╮
          ╱   •a  ╲
         │    •b   │  ← Open set U
          ╲   •c  ╱
           ╰─────╯

    Points "near" each other if in same open set!
    """


def draw_continuous_function():
    return """
    Continuous Function: f: X → Y

    "Preimages of open sets are open"

    Definition: f is continuous if ∀V open in Y: f⁻¹(V) open in X

    Intuitive: "No tearing or jumping"

    Example: f(x) = 2x on ℝ

         X: ─────•──────→
                 x

         Y: ─────•──────→
                2x

         Open in Y: (2, 4)
         Preimage: f⁻¹(2, 4) = (1, 2) (open in X!) ✓

    Non-example: Step function

         │    ┌────
       1 │    │
         │────┘
       0 │
         └────────→
              1

         f(x) = { 0 if x < 1
                { 1 if x ≥ 1

         Jump at x = 1 → NOT continuous ✗

    Composition: f: X → Y, g: Y → Z continuous
                 ⇒ g ∘ f: X → Z continuous ✓

    Visual: "Rubber sheet deformation"

         Before:        After:
         ┌─────┐       ╭─────╮
         │  X  │  f    │  Y  │
         │     │ ───→  │     │
         └─────┘       ╰─────╯

       Can stretch, bend, twist - NO tearing!
    """


def draw_homeomorphism():
    return """
    Homeomorphism: "Topologically equivalent"

    Definition: f: X → Y is homeomorphism if:
    1. f is bijective (one-to-one and onto)
    2. f is continuous
    3. f⁻¹ is continuous

    Write: X ≅ Y ("X is homeomorphic to Y")

    "Same topological structure, different shape"

    Example: Circle ≅ Square

         ○           □
        / \\         / \\
       |   |  ≅    |   |
        \\ /         \\ /

       Can deform circle → square continuously!

    Example: Coffee cup ≅ Donut (torus)

         ╭─╮              ╭───╮
        │   │     ≅      ╱     ╲
        │ ● │           │   ○   │
         ╰─╯             ╲     ╱
        Coffee            ╰───╯
         cup             Donut

       Both have exactly ONE hole! (genus = 1)

    Non-example: Circle ≇ Line segment

         ○  ≇  ────

       Circle is "closed" (compact)
       Line segment has "ends" (has boundary)

    Topological Invariants (preserved under homeomorphism):
    • Number of holes (genus)
    • Connectedness
    • Compactness
    • Dimension

    "Topology doesn't care about distances, only structure!"
    """


def draw_connectedness():
    return """
    Connectedness: "Cannot be separated"

    Definition: X is connected if NOT union of disjoint open sets

    X = A ∪ B with A ∩ B = ∅, both open ⇒ X disconnected

    Example: Connected spaces

         Interval [0, 1]:  ────────
                           0      1

         Cannot separate without "cutting"! ✓

         Circle: ○  Cannot separate! ✓

    Example: Disconnected spaces

         {0} ∪ {1}:  •     •
                     0     1

         Two separate components! ✗

         Open intervals union: (0,1) ∪ (2,3)
                               ──── ────
                               0  1 2  3

         Gap between them! ✗

    Path-Connected (stronger):
         "Any two points can be joined by continuous path"

              a •─────────• b
                   path

         [0,1] is path-connected ✓
         Circle is path-connected ✓

    Visual: Connected vs Disconnected

         Connected:           Disconnected:
         ╭────────╮          ╭────╮  ╭────╮
         │        │          │    │  │    │
         │   X    │          │ A  │  │ B  │
         │        │          │    │  │    │
         ╰────────╯          ╰────╯  ╰────╯

    Theorem: Continuous image of connected is connected
    f: X → Y continuous, X connected ⇒ f(X) connected ✓
    """


def draw_compactness():
    return """
    Compactness: "Every open cover has finite subcover"

    Definition: X compact if for any open cover {Uᵢ}:
                ∃ finite subcover {Uᵢ₁, ..., Uᵢₙ}

    Open cover: X ⊆ ⋃ᵢ Uᵢ (open sets covering X)
    Finite subcover: X ⊆ Uᵢ₁ ∪ ... ∪ Uᵢₙ (finitely many suffice)

    Example: [0, 1] is compact (Heine-Borel)

         Cover with: (−1/n, 1 + 1/n) for n = 1, 2, 3, ...

         ────(───────────)────  n=1: (−1, 2)
            (─────────)         n=2: (−1/2, 3/2)
          (───────)             n=3: (−1/3, 4/3)
         ──────────────────→

         Finite subcover: Just use n=1! ✓

    Non-example: (0, 1) is NOT compact

         Cover with: (1/n, 1) for n = 2, 3, 4, ...

              (──────────────)  n=2: (1/2, 1)
            (────────────────)  n=3: (1/3, 1)
          (──────────────────)  n=4: (1/4, 1)
         ──────────────────→

         Need infinitely many! Gets arbitrarily close to 0 ✗

    Heine-Borel Theorem (ℝⁿ):
         X compact ⟺ X closed and bounded

         [0, 1]: closed ✓, bounded ✓ → compact ✓
         (0, 1): NOT closed ✗ → NOT compact ✗
         [0, ∞): NOT bounded ✗ → NOT compact ✗

    Properties:
    • Closed subset of compact → compact
    • Continuous image of compact → compact
    • Compact in Hausdorff space → closed

    Visual: Compactness as "finite-ness"

         Compact:             Non-compact:
         [─────]              (─────)
         0     1              0     1
         finite cover         infinite cover needed
    """


def draw_hausdorff_space():
    return """
    Hausdorff Space (T₂): "Distinct points can be separated"

    Definition: ∀x ≠ y: ∃U, V open: x ∈ U, y ∈ V, U ∩ V = ∅

    "Any two points have disjoint neighborhoods"

    Visual:

           ╭──U──╮        ╭──V──╮
          │  •x  │      │  •y  │
           ╰─────╯        ╰─────╯
              ↑              ↑
           Disjoint!    No overlap

    Example: ℝ with standard topology is Hausdorff

         x ≠ y: take ε = |x − y|/2

         U = (x − ε, x + ε)    V = (y − ε, y + ε)

            x          y
         ──(──)────(──)──→
           U        V

         U ∩ V = ∅ ✓

    Non-example: Trivial topology {∅, X}

         Only open sets: ∅ and X

         Can't separate points! ✗
         (All neighborhoods contain everything)

    Properties:
    • Sequences have unique limits
    • Compact subsets are closed
    • Most "nice" spaces are Hausdorff

    Separation Axioms (hierarchy):
    • T₀: Kolmogorov (can distinguish points)
    • T₁: Points are closed
    • T₂: Hausdorff (separate with open sets)
    • T₃: Regular (separate point from closed set)
    • T₄: Normal (separate disjoint closed sets)

    ℝ, ℝⁿ, metric spaces are all Hausdorff ✓
    """


def draw_fundamental_group():
    return """
    Fundamental Group π₁(X, x₀): "Loops up to homotopy"

    "Count holes by measuring loops that can't contract"

    Idea:
    1. Draw loops based at x₀
    2. Two loops equivalent if continuously deformable
    3. Compose loops: go around one, then the other
    4. Forms a GROUP!

    Example: Circle S¹

              x₀
               •
              ╱│╲
             ╱ │ ╲
            │  •  │  ← Loop once around
             ╲   ╱
              ╲ ╱
               •

         π₁(S¹) ≅ ℤ (integers!)

         n loops around = element n ∈ ℤ
         • 1 loop: 1 ∈ ℤ
         • 2 loops: 2 ∈ ℤ
         • Backwards: −1 ∈ ℤ

    Example: Plane ℝ²

         All loops can contract to point!

         π₁(ℝ²) = {0} (trivial group)

    Example: Torus (donut)

              ╭───╮
             ╱  a  ╲
            │   ○   │  ← Two independent loops
             ╲  b  ╱     a (around hole)
              ╰───╯      b (through hole)

         π₁(Torus) ≅ ℤ × ℤ

    Example: Sphere S²

         All loops contract!
         π₁(S²) = {0}

    Homotopy Equivalence:
         X ≃ Y if can continuously deform one to other
         ⇒ π₁(X) ≅ π₁(Y) (same fundamental group!)

    Applications:
    • Classify surfaces (genus = number of holes)
    • Robotics (configuration spaces)
    • String theory (loop spaces)
    """


def draw_euler_characteristic():
    return """
    Euler Characteristic χ: Topological invariant

    For simplicial complex: χ = V − E + F

    (V = vertices, E = edges, F = faces)

    Sphere:
              ●
             ╱│╲
            ╱ │ ╲
           ●──●──●
            ╲ │ ╱
             ╲│╱
              ●

         Octahedron: V=6, E=12, F=8
         χ = 6 − 12 + 8 = 2 ✓

    Torus (donut):
              ╭───╮
             ╱     ╲
            │   ○   │
             ╲     ╱
              ╰───╯

         Square with opposite sides glued:
         V = 1 (all corners identified)
         E = 2 (top/bottom = 1, left/right = 1)
         F = 1 (the square)
         χ = 1 − 2 + 1 = 0 ✓

    Klein Bottle:
         Non-orientable surface
         χ = 0

    Classification of Surfaces:
    • Sphere: χ = 2 (genus 0)
    • Torus: χ = 0 (genus 1)
    • Two-holed torus: χ = −2 (genus 2)
    • n-holed torus: χ = 2 − 2n (genus n)

    Gauss-Bonnet Theorem:
         ∫∫_S K dA = 2πχ(S)

         (curvature integral = topology!)

    Euler characteristic:
    • Homeomorphism invariant
    • Additive: χ(X ∪ Y) = χ(X) + χ(Y) − χ(X ∩ Y)
    • Generalizes to higher dimensions

    Examples:
    • Disk: χ = 1
    • Cylinder: χ = 0
    • Möbius strip: χ = 0
    • Projective plane ℝℙ²: χ = 1
    """


async def main():
    print("=" * 80)
    print("🌐 MATHEMATICAL DISCOVERY: Topology - Mathematics of Continuous Spaces")
    print("=" * 80)
    print()
    print("Using EXPLORE mode to discover topology fundamentals!")
    print("From open sets to homeomorphisms to invariants!")
    print()

    # Use in-memory database
    supe = Supe(db_path=":memory:")

    # Seed topology knowledge
    print("📚 Seeding topology definitions...")

    topology_defs = """Topology: The Study of Continuous Spaces

Core Definitions:

    Topological Space (X, τ):
        • X: Set (the "space")
        • τ: Collection of subsets of X (the "topology")

        Axioms:
        1. ∅ ∈ τ and X ∈ τ
        2. Arbitrary unions: ⋃ᵢ Uᵢ ∈ τ
        3. Finite intersections: U ∩ V ∈ τ

        Elements of τ called "open sets"

    Continuous Function f: X → Y:
        ∀V open in Y: f⁻¹(V) open in X

        Intuition: "No tearing or jumping"

    Homeomorphism:
        Bijective continuous function with continuous inverse
        X ≅ Y if homeomorphic
        "Topologically equivalent"

    Connectedness:
        X connected if NOT union of disjoint non-empty open sets
        Intuition: "In one piece"

    Path-Connected:
        Any two points connected by continuous path
        Path-connected ⇒ connected

    Compactness:
        Every open cover has finite subcover
        In ℝⁿ: compact ⟺ closed and bounded (Heine-Borel)
        Intuition: "Finite in some sense"

    Hausdorff Space (T₂):
        Distinct points have disjoint neighborhoods
        "Nice" separation property

Fundamental Theorems:

    Heine-Borel Theorem (ℝⁿ):
        X compact ⟺ X closed and bounded

    Intermediate Value Theorem:
        f: [a,b] → ℝ continuous
        f(a) < c < f(b) ⇒ ∃x: f(x) = c

        Consequence of connectedness!

    Extreme Value Theorem:
        f: K → ℝ continuous, K compact
        ⇒ f attains max and min

        Compactness guarantees extrema!

    Continuous Image Properties:
        • f continuous: connected → connected
        • f continuous: compact → compact
        • f continuous closed map: T₂ compact → T₂

    Tietze Extension Theorem:
        Normal space: can extend continuous functions
        from closed subsets to whole space

Topological Invariants:

    Homeomorphism Invariants (preserved under ≅):
    • Connectedness
    • Path-connectedness
    • Compactness
    • Hausdorff property
    • Dimension
    • Euler characteristic χ = V − E + F
    • Fundamental group π₁(X)
    • Homology groups Hₙ(X)
    • Genus (number of holes)

    Examples:
    • Circle ≅ Square (both χ = 0)
    • Coffee cup ≅ Donut (both genus 1)
    • ℝⁿ ≅ ℝᵐ ⟺ n = m (dimension)

Applications:

    • Physics: Phase spaces, manifolds
    • Robotics: Configuration spaces
    • Data analysis: Topological data analysis (TDA)
    • Computer graphics: Surface representation
    • Neuroscience: Brain connectivity
    • Economics: Fixed point theorems

Examples of Spaces:

    • ℝⁿ: Euclidean space (Hausdorff, connected)
    • Sⁿ: n-sphere (compact, connected)
    • Tⁿ: n-torus (compact, abelian fundamental group)
    • ℝℙⁿ: Projective space (non-orientable for n even)
    • Klein bottle: Non-orientable surface

Key Insights:
    • Topology abstracts "nearness" without metrics
    • Homeomorphism = "same shape" topologically
    • Continuous functions preserve structure
    • Compactness generalizes finiteness
    • Algebraic topology uses algebra to study topology"""

    supe.memory.store_card(
        label="topology_fundamentals",
        buffers=[Buffer(name="content", payload=topology_defs.encode('utf-8'))],
        master_output="Topology: spaces, continuity, invariants",
        track="awareness",
    )
    print("✓ Topology concepts defined\n")

    # Discovery 1: Union of Open Sets
    print("🔍 DISCOVERY 1: Union of Open Sets is Open")
    print("-" * 80)
    print(draw_topological_space())

    result1 = await supe.learn(
        "Is the union of open sets open? (Topology axiom)",
        mode="explore"
    )

    print(f"Question: Is ⋃ᵢ Uᵢ open if each Uᵢ is open?")
    print()
    print("Example: ℝ with intervals")
    print("  (0,1) ∪ (0.5, 1.5) = (0, 1.5) is open ✓")
    print("  Union of open intervals is open ✓")
    print()

    if result1['beliefs_count'] > 0:
        belief = result1['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result1['confidence']:.2f}")
        print(f"Proof Hash: {result1['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 2: Continuous Functions
    print("🔍 DISCOVERY 2: Composition of Continuous Functions")
    print("-" * 80)
    print(draw_continuous_function())

    result2 = await supe.learn(
        "Is the composition of continuous functions continuous? (f: X→Y, g: Y→Z continuous ⇒ g∘f continuous)",
        mode="explore"
    )

    print(f"Question: Is g ∘ f continuous if f and g are continuous?")
    print()
    print("Example: f(x) = 2x, g(x) = x²")
    print("  Both continuous")
    print("  g(f(x)) = (2x)² = 4x² continuous ✓")
    print()

    if result2['beliefs_count'] > 0:
        belief = result2['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result2['confidence']:.2f}")
        print(f"Proof Hash: {result2['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 3: Connected Spaces
    print("🔍 DISCOVERY 3: Continuous Image of Connected is Connected")
    print("-" * 80)
    print(draw_connectedness())

    result3 = await supe.learn(
        "Does a continuous function map connected spaces to connected spaces? (f: X→Y continuous, X connected ⇒ f(X) connected)",
        mode="explore"
    )

    print(f"Question: Does f(connected) = connected?")
    print()
    print("Example: f: [0,1] → ℝ continuous")
    print("  [0,1] is connected")
    print("  f([0,1]) is connected (interval) ✓")
    print()

    if result3['beliefs_count'] > 0:
        belief = result3['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"Proof Hash: {result3['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 4: Compact Spaces
    print("🔍 DISCOVERY 4: Continuous Image of Compact is Compact")
    print("-" * 80)
    print(draw_compactness())

    result4 = await supe.learn(
        "Does a continuous function map compact spaces to compact spaces? (f: X→Y continuous, X compact ⇒ f(X) compact)",
        mode="explore"
    )

    print(f"Question: Does f(compact) = compact?")
    print()
    print("Example: f: [0,1] → ℝ continuous")
    print("  [0,1] is compact (closed, bounded)")
    print("  f([0,1]) is compact ✓")
    print()

    if result4['beliefs_count'] > 0:
        belief = result4['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result4['confidence']:.2f}")
        print(f"Proof Hash: {result4['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 5: Hausdorff Property
    print("🔍 DISCOVERY 5: Subspace of Hausdorff is Hausdorff")
    print("-" * 80)
    print(draw_hausdorff_space())

    result5 = await supe.learn(
        "Is a subspace of a Hausdorff space also Hausdorff? (X Hausdorff ⇒ subspace Hausdorff)",
        mode="explore"
    )

    print(f"Question: Is subspace of Hausdorff space also Hausdorff?")
    print()
    print("Example: (0,1) ⊂ ℝ")
    print("  ℝ is Hausdorff")
    print("  (0,1) inherits Hausdorff property ✓")
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
    print("🎨 TOPOLOGY VISUALIZATIONS")
    print("=" * 80)
    print()

    print("≅ Homeomorphism:")
    print(draw_homeomorphism())
    print()

    print("π₁ Fundamental Group:")
    print(draw_fundamental_group())
    print()

    print("χ Euler Characteristic:")
    print(draw_euler_characteristic())
    print()

    # Summary
    print("=" * 80)
    print("🎓 TOPOLOGY DISCOVERIES")
    print("=" * 80)
    print()

    total_beliefs = sum(r['beliefs_count'] for r in [result1, result2, result3, result4, result5])

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                      TOPOLOGY FUNDAMENTALS                           ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║                                                                      ║")
    print("║  Topological Space (X, τ):                                           ║")
    print("║    • ∅, X ∈ τ                                                       ║")
    print("║    • Arbitrary unions open                                           ║")
    print("║    • Finite intersections open                                       ║")
    print("║                                                                      ║")
    print("║  Continuous Functions:                                               ║")
    print("║    • Preimages of open sets are open                                 ║")
    print("║    • Composition preserves continuity                                ║")
    print("║                                                                      ║")
    print("║  Preservation Properties:                                            ║")
    print("║    • f(connected) = connected                                        ║")
    print("║    • f(compact) = compact                                            ║")
    print("║                                                                      ║")
    print("║  Hausdorff Space:                                                    ║")
    print("║    • Distinct points separable                                       ║")
    print("║    • Subspaces inherit property                                      ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    print(f"🌟 What We Learned:")
    print(f"   • Total beliefs formed: {total_beliefs}")
    print(f"   • Each discovery stored with proof hash")
    print(f"   • Linked to Tasc execution for traceability")
    print()

    print("🔗 Connections:")
    print("   Topology ──→ Analysis (continuous functions, limits)")
    print("            ──→ Geometry (manifolds, surfaces)")
    print("            ──→ Algebra (fundamental group, homology)")
    print("            ──→ Physics (phase spaces, spacetime)")
    print("            ──→ Data Science (topological data analysis)")
    print("            ──→ Computer Science (domain theory)")
    print()

    print("💡 Next Topology Horizons:")
    print("   • Algebraic topology (homology, cohomology)")
    print("   • Differential topology (smooth manifolds)")
    print("   • Geometric topology (knot theory)")
    print("   • Point-set topology (deeper separation axioms)")
    print("   • Category theory (functors, natural transformations)")
    print()

    print("🎭 Philosophy:")
    print("   Rubber sheet geometry!")
    print("   Coffee cup = Donut (both have 1 hole).")
    print("   Topology studies 'shape' without distances.")
    print("   Continuous deformation preserves structure.")
    print("   Algebraic invariants classify spaces.")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
