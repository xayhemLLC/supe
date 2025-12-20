"""
Mathematical Discovery: Abstract Algebra - The Mathematics of Structure 🔢

Abstract algebra studies algebraic structures: groups, rings, fields, and vector spaces!

Core Concepts:
    • Group (G, ∘): Set with associative operation, identity, inverses
    • Ring (R, +, ×): Group under addition, associative multiplication
    • Field (F, +, ×): Ring where every nonzero element has multiplicative inverse
    • Vector Space: Structure over a field with scalar multiplication

Properties to Discover:
    • Closure: a ∘ b ∈ G
    • Associativity: (a ∘ b) ∘ c = a ∘ (b ∘ c)
    • Identity: ∃e: e ∘ a = a ∘ e = a
    • Inverse: ∀a ∃a⁻¹: a ∘ a⁻¹ = a⁻¹ ∘ a = e
    • Commutativity (abelian): a ∘ b = b ∘ a

Let's DISCOVER abstract algebra through exploration! ∞
"""

import asyncio
from supe import Supe
from ab.models import Buffer


def draw_group_definition():
    return """
    Group (G, ∘): Algebraic structure with 4 axioms

    1. CLOSURE: ∀a,b ∈ G: a ∘ b ∈ G
       "Operation stays within the set"

    2. ASSOCIATIVITY: ∀a,b,c ∈ G: (a ∘ b) ∘ c = a ∘ (b ∘ c)
       "Order of evaluation doesn't matter"

    3. IDENTITY: ∃e ∈ G: ∀a ∈ G: e ∘ a = a ∘ e = a
       "There's a 'do nothing' element"

    4. INVERSE: ∀a ∈ G: ∃a⁻¹ ∈ G: a ∘ a⁻¹ = a⁻¹ ∘ a = e
       "Every element can be 'undone'"

    Visual (integers under addition):

         ... ← -2 ← -1 ← 0 → 1 → 2 → ...
                      ↑
                  Identity

    • Closure: -5 + 3 = -2 ∈ ℤ ✓
    • Associative: (1 + 2) + 3 = 1 + (2 + 3) = 6 ✓
    • Identity: 0 + a = a ✓
    • Inverse: 5 + (-5) = 0 ✓

    (ℤ, +) is a GROUP! ✓

    Non-example (natural numbers ℕ under addition):
    • No inverse for 5: 5 + ? = 0 has no solution in ℕ
    • NOT a group ✗
    """


def draw_abelian_group():
    return """
    Abelian Group: Group with commutativity

    "Named after Niels Henrik Abel"

    Definition: Group (G, ∘) where ∀a,b ∈ G: a ∘ b = b ∘ a

    Visual (Klein Four-Group):

              e
             ╱ ╲
            ╱   ╲
           a─────b
            ╲   ╱
             ╲ ╱
              c

    Cayley table (∘):
       │ e  a  b  c
      ─┼─────────────
       e│ e  a  b  c
       a│ a  e  c  b
       b│ b  c  e  a
       c│ c  b  a  e

    Notice: Symmetric across diagonal (commutative!)
    • a ∘ b = c = b ∘ a ✓
    • b ∘ c = a = c ∘ b ✓

    Examples of Abelian Groups:
    • (ℤ, +): Integers under addition
    • (ℚ\\{0}, ×): Non-zero rationals under multiplication
    • (ℤ/nℤ, ⊕): Integers mod n under addition
    • (ℝⁿ, +): n-dimensional vectors

    Non-Abelian Example:
    • Symmetries of a triangle (rotation vs reflection)
    • Matrix multiplication (AB ≠ BA in general)
    """


def draw_ring_definition():
    return """
    Ring (R, +, ×): Structure with TWO operations

    Axioms:
    1. (R, +) is an abelian group
       • Closure, associativity, identity (0), inverses (-a)
       • Commutativity: a + b = b + a

    2. (R, ×) is a monoid (associative with identity)
       • Closure: a × b ∈ R
       • Associativity: (a × b) × c = a × (b × c)
       • Identity: ∃1 ∈ R: 1 × a = a × 1 = a

    3. Distributivity:
       • a × (b + c) = (a × b) + (a × c) (left distributive)
       • (a + b) × c = (a × c) + (b × c) (right distributive)

    Visual (ℤ under + and ×):

         Addition group          Multiplication
        ... -2  -1  0  1  2 ...     (no inverses!)
                    ↑              1 is identity
                Identity 0

    Examples:
    • (ℤ, +, ×): Integers ✓
    • (ℚ, +, ×): Rationals ✓
    • (ℤ/nℤ, ⊕, ⊗): Integers mod n ✓
    • (M_n(ℝ), +, ×): n×n matrices ✓

    Almost a ring: (ℕ, +, ×)
    • No additive inverses → NOT a ring ✗
    """


def draw_field_definition():
    return """
    Field (F, +, ×): Ring where every nonzero element has multiplicative inverse

    "Can add, subtract, multiply, AND divide (except by zero)"

    Axioms:
    1. (F, +, ×) is a ring
    2. (F\\{0}, ×) is an abelian group
       • Every nonzero element has multiplicative inverse

    Visual (ℚ):

         Additive group          Multiplicative group
        ... -2  -1  0  1  2 ...    ... 1/2  1  2  3 ...
                    ↑                      ↑
                Identity 0              Identity 1

    Every fraction a/b has inverse b/a!

    Examples:
    • ℚ: Rationals ✓
    • ℝ: Real numbers ✓
    • ℂ: Complex numbers ✓
    • ℤ/pℤ: Integers mod p (p prime) ✓
    • Finite fields: 𝔽_q (q = p^n)

    NOT fields:
    • ℤ: 2 has no multiplicative inverse in ℤ ✗
    • ℤ/6ℤ: 2 × 3 = 0 (zero divisors) ✗

    Applications:
    • Cryptography (finite fields)
    • Error correction (Reed-Solomon codes)
    • Algebraic geometry
    • Number theory
    """


def draw_lagranges_theorem():
    return """
    Lagrange's Theorem (Group Theory)

    "Subgroup order divides group order"

    Theorem: If H is subgroup of finite group G, then |H| divides |G|

    |G| = |H| × [G:H]

    Where [G:H] is the index (number of cosets)

    Visual (ℤ/6ℤ):

           G = ℤ/6ℤ = {0, 1, 2, 3, 4, 5}
           |G| = 6

           H = {0, 3}  (subgroup)
           |H| = 2

           Cosets:
           • 0 + H = {0, 3}  ─┐
           • 1 + H = {1, 4}   ├─ Partition G
           • 2 + H = {2, 5}  ─┘

           [G:H] = 3 cosets

    Check: |G| = |H| × [G:H]
           6 = 2 × 3 ✓

    Consequence: In group of order n, element order divides n
    • G = ℤ/12ℤ: possible orders = {1, 2, 3, 4, 6, 12}
    • Element of order 5? IMPOSSIBLE! (5 ∤ 12)

    Example: Symmetries of square (8 elements)
    • Possible subgroup sizes: {1, 2, 4, 8}
    • Subgroup of size 3? IMPOSSIBLE! (3 ∤ 8)
    """


def draw_isomorphism():
    return """
    Isomorphism: "Same structure, different representation"

    Definition: φ: G → H is isomorphism if:
    1. φ is bijective (one-to-one and onto)
    2. φ(a ∘ b) = φ(a) * φ(b) (preserves operation)

    Write: G ≅ H ("G is isomorphic to H")

    Example: (ℤ/4ℤ, ⊕) ≅ ({1, i, -1, -i}, ×)

    ℤ/4ℤ:  0  1  2  3        ℂ:  1  i  -1  -i
           ↓  ↓  ↓  ↓             ↓  ↓   ↓   ↓
    φ:     1  i -1 -i        Multiply

    Addition table (ℤ/4ℤ):
      ⊕│ 0  1  2  3
      ─┼───────────
       0│ 0  1  2  3
       1│ 1  2  3  0
       2│ 2  3  0  1
       3│ 3  0  1  2

    Multiplication table (complex):
      ×│ 1  i  -1  -i
      ─┼─────────────
       1│ 1  i  -1  -i
       i│ i  -1 -i  1
      -1│-1  -i  1  i
      -i│-i  1  i  -1

    Same structure! φ(1 ⊕ 2) = φ(3) = -i
                    φ(1) × φ(2) = i × -1 = -i ✓

    "Mathematics doesn't care about labels, only structure"

    Classic isomorphisms:
    • (ℝ, +) ≅ (ℝ⁺, ×) via φ(x) = eˣ
    • (ℤ, +) ≅ (2ℤ, +) via φ(x) = 2x
    • Vector spaces of same dimension
    """


def draw_quotient_group():
    return """
    Quotient Group: G/H = "Group modulo subgroup"

    Construction:
    1. Take normal subgroup H of G
    2. Form cosets: gH = {gh : h ∈ H}
    3. Define operation: (g₁H)(g₂H) = (g₁g₂)H

    Visual (ℤ/3ℤ = ℤ modulo 3ℤ):

    ℤ:  ... -6  -3   0   3   6 ...
             ╲   │   ╱   │   ╱
              ╲  │  ╱    │  ╱
               ╲ │ ╱     │ ╱
         3ℤ = {... -3, 0, 3, 6 ...}  ← Subgroup

    Cosets partition ℤ:
    • 0 + 3ℤ = {..., -3, 0, 3, 6, ...}   ≡ [0]
    • 1 + 3ℤ = {..., -2, 1, 4, 7, ...}   ≡ [1]
    • 2 + 3ℤ = {..., -1, 2, 5, 8, ...}   ≡ [2]

    Quotient group: ℤ/3ℤ = {[0], [1], [2]}

    Addition table:
      +│[0] [1] [2]
      ─┼──────────
      [0]│[0] [1] [2]
      [1]│[1] [2] [0]
      [2]│[2] [0] [1]

    This IS ℤ/3ℤ! ✓

    First Isomorphism Theorem:
    φ: G → H homomorphism
    ⇒ G/ker(φ) ≅ Im(φ)

    "Quotient by kernel = image"
    """


async def main():
    print("=" * 80)
    print("🔢 MATHEMATICAL DISCOVERY: Abstract Algebra - Mathematics of Structure")
    print("=" * 80)
    print()
    print("Using EXPLORE mode to discover abstract algebra fundamentals!")
    print("From groups to rings to fields!")
    print()

    # Use in-memory database
    supe = Supe(db_path=":memory:")

    # Seed abstract algebra knowledge
    print("📚 Seeding abstract algebra definitions...")

    algebra_defs = """Abstract Algebra: The Study of Algebraic Structures

Core Structures:

    Group (G, ∘):
        Axioms:
            1. Closure: a ∘ b ∈ G
            2. Associativity: (a ∘ b) ∘ c = a ∘ (b ∘ c)
            3. Identity: ∃e: e ∘ a = a
            4. Inverse: ∀a ∃a⁻¹: a ∘ a⁻¹ = e

        Abelian (commutative): a ∘ b = b ∘ a

        Examples:
            • (ℤ, +): Integers under addition
            • (ℚ\\{0}, ×): Rationals under multiplication
            • (ℤ/nℤ, ⊕): Integers modulo n
            • Permutations (symmetric group S_n)

    Ring (R, +, ×):
        Axioms:
            1. (R, +) is abelian group
            2. (R, ×) is monoid (associative, has identity)
            3. Distributivity: a(b + c) = ab + ac

        Examples:
            • (ℤ, +, ×): Integers
            • (ℚ, +, ×): Rationals
            • (M_n(ℝ), +, ×): n×n matrices
            • Polynomials ℝ[x]

    Field (F, +, ×):
        Axioms:
            1. (F, +, ×) is a ring
            2. (F\\{0}, ×) is abelian group

        Examples:
            • ℚ, ℝ, ℂ: Rationals, reals, complex numbers
            • ℤ/pℤ for prime p: Finite fields
            • ℚ(√2): Algebraic number fields

    Vector Space V over field F:
        • (V, +) is abelian group (vector addition)
        • Scalar multiplication: F × V → V
        • Distributivity and compatibility axioms

Fundamental Theorems:

    Lagrange's Theorem:
        For finite group G and subgroup H:
        |H| divides |G|

        Consequence: Element order divides group order

    Isomorphism Theorems:
        1st: G/ker(φ) ≅ Im(φ)
        2nd: (G/H)/(K/H) ≅ G/K
        3rd: Correspondence between subgroups

    Cayley's Theorem:
        Every group is isomorphic to permutation group
        (Groups = symmetries!)

    Fundamental Theorem of Finitely Generated Abelian Groups:
        G ≅ ℤ^r × ℤ/n₁ℤ × ... × ℤ/n_kℤ
        (Classification of finite abelian groups!)

Applications:
    • Cryptography (RSA uses modular arithmetic, finite fields)
    • Error correction (Reed-Solomon codes use finite fields)
    • Physics (symmetry groups, representation theory)
    • Chemistry (molecular symmetry groups)
    • Rubik's cube (group theory of permutations)
    • Galois theory (solvability of polynomials)

Key Insights:
    • Abstraction reveals common structure
    • Different objects share same algebraic properties
    • Isomorphisms identify "essentially same" structures
    • Quotient structures give new perspectives
    • Homomorphisms preserve structure"""

    supe.memory.store_card(
        label="abstract_algebra_fundamentals",
        buffers=[Buffer(name="content", payload=algebra_defs.encode('utf-8'))],
        master_output="Abstract algebra: groups, rings, fields",
        track="awareness",
    )
    print("✓ Abstract algebra concepts defined\n")

    # Discovery 1: Group Closure
    print("🔍 DISCOVERY 1: Group Closure Property")
    print("-" * 80)
    print(draw_group_definition())

    result1 = await supe.learn(
        "For group (G, ∘), is a ∘ b ∈ G for all a, b ∈ G? (Closure property)",
        mode="explore"
    )

    print(f"Question: Is a ∘ b ∈ G? (Closure)")
    print()
    print("Example: (ℤ, +)")
    print("  5 + 7 = 12 ∈ ℤ ✓")
    print("  -3 + 10 = 7 ∈ ℤ ✓")
    print()

    if result1['beliefs_count'] > 0:
        belief = result1['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result1['confidence']:.2f}")
        print(f"Proof Hash: {result1['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 2: Group Identity
    print("🔍 DISCOVERY 2: Group Identity Element")
    print("-" * 80)
    print("""
    Identity Axiom: ∃e ∈ G: ∀a ∈ G: e ∘ a = a ∘ e = a

    "There exists a 'do nothing' element"

    Examples:
    • (ℤ, +): identity = 0 (0 + a = a)
    • (ℚ\\{0}, ×): identity = 1 (1 × a = a)
    • (ℤ/nℤ, ⊕): identity = [0]
    • String concatenation: identity = "" (empty string)
    """)

    result2 = await supe.learn(
        "Does every group have an identity element e where e ∘ a = a? (Identity property)",
        mode="explore"
    )

    print(f"Question: Does every group have identity e where e ∘ a = a?")
    print()
    print("Example: (ℤ, +) has identity 0")
    print("  0 + 5 = 5 ✓")
    print("  0 + (-3) = -3 ✓")
    print()

    if result2['beliefs_count'] > 0:
        belief = result2['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result2['confidence']:.2f}")
        print(f"Proof Hash: {result2['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 3: Abelian Property
    print("🔍 DISCOVERY 3: Abelian (Commutative) Groups")
    print("-" * 80)
    print(draw_abelian_group())

    result3 = await supe.learn(
        "Is (ℤ, +) abelian? (Does a + b = b + a?)",
        mode="explore"
    )

    print(f"Question: Is (ℤ, +) abelian (commutative)?")
    print()
    print("Test: 3 + 5 = 8 = 5 + 3 ✓")
    print("Test: -2 + 7 = 5 = 7 + (-2) ✓")
    print()

    if result3['beliefs_count'] > 0:
        belief = result3['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"Proof Hash: {result3['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 4: Lagrange's Theorem
    print("🔍 DISCOVERY 4: Lagrange's Theorem")
    print("-" * 80)
    print(draw_lagranges_theorem())

    result4 = await supe.learn(
        "For finite group G and subgroup H, does |H| divide |G|? (Lagrange's theorem)",
        mode="explore"
    )

    print(f"Question: Does subgroup order divide group order?")
    print()
    print("Example: ℤ/6ℤ with subgroup H = {0, 3}")
    print("  |G| = 6, |H| = 2")
    print("  2 divides 6 ✓")
    print()

    if result4['beliefs_count'] > 0:
        belief = result4['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result4['confidence']:.2f}")
        print(f"Proof Hash: {result4['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 5: Ring Distributivity
    print("🔍 DISCOVERY 5: Ring Distributivity")
    print("-" * 80)
    print(draw_ring_definition())

    result5 = await supe.learn(
        "In ring (R, +, ×), is a × (b + c) = (a × b) + (a × c)? (Distributivity)",
        mode="explore"
    )

    print(f"Question: Is multiplication distributive over addition?")
    print()
    print("Example: 3 × (4 + 5) = 3 × 9 = 27")
    print("         (3 × 4) + (3 × 5) = 12 + 15 = 27 ✓")
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
    print("🎨 ABSTRACT ALGEBRA VISUALIZATIONS")
    print("=" * 80)
    print()

    print("🔗 Field Structure:")
    print(draw_field_definition())
    print()

    print("≅ Isomorphism:")
    print(draw_isomorphism())
    print()

    print("/ Quotient Groups:")
    print(draw_quotient_group())
    print()

    # Summary
    print("=" * 80)
    print("🎓 ABSTRACT ALGEBRA DISCOVERIES")
    print("=" * 80)
    print()

    total_beliefs = sum(r['beliefs_count'] for r in [result1, result2, result3, result4, result5])

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                  ABSTRACT ALGEBRA FUNDAMENTALS                       ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║                                                                      ║")
    print("║  Group (G, ∘):                                                       ║")
    print("║    • Closure: a ∘ b ∈ G                                             ║")
    print("║    • Associativity: (a ∘ b) ∘ c = a ∘ (b ∘ c)                       ║")
    print("║    • Identity: ∃e: e ∘ a = a                                        ║")
    print("║    • Inverse: ∀a ∃a⁻¹: a ∘ a⁻¹ = e                                  ║")
    print("║                                                                      ║")
    print("║  Abelian: a ∘ b = b ∘ a                                             ║")
    print("║                                                                      ║")
    print("║  Ring (R, +, ×):                                                     ║")
    print("║    • (R, +) is abelian group                                        ║")
    print("║    • (R, ×) is monoid                                               ║")
    print("║    • Distributivity: a(b + c) = ab + ac                             ║")
    print("║                                                                      ║")
    print("║  Lagrange's Theorem:                                                 ║")
    print("║    |H| divides |G| for subgroup H                                   ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    print(f"🌟 What We Learned:")
    print(f"   • Total beliefs formed: {total_beliefs}")
    print(f"   • Each discovery stored with proof hash")
    print(f"   • Linked to Tasc execution for traceability")
    print()

    print("🔗 Connections:")
    print("   Abstract Algebra ──→ Number Theory (modular arithmetic)")
    print("                    ──→ Linear Algebra (vector spaces)")
    print("                    ──→ Cryptography (RSA, finite fields)")
    print("                    ──→ Physics (symmetry groups)")
    print("                    ──→ Chemistry (molecular symmetry)")
    print("                    ──→ Galois Theory (polynomial solvability)")
    print()

    print("💡 Next Abstract Algebra Horizons:")
    print("   • Representation theory (group actions)")
    print("   • Galois theory (field extensions)")
    print("   • Module theory (generalized vector spaces)")
    print("   • Category theory (arrows between structures)")
    print("   • Homological algebra")
    print()

    print("🎭 Philosophy:")
    print("   Structure matters more than objects!")
    print("   Isomorphic structures are 'the same'.")
    print("   Abstraction reveals deep patterns.")
    print("   Symmetry is formalized via group theory.")
    print("   Quotients give new perspectives on structure.")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
