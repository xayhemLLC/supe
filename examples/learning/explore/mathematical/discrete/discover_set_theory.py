"""
Mathematical Discovery: Set Theory - The Foundation of Mathematics ∪∩⊆

Set theory provides the fundamental language for all of mathematics!

Core Concepts:
    • Sets: Collections of distinct objects
    • Elements: x ∈ A means "x is in set A"
    • Subsets: A ⊆ B means "every element of A is in B"
    • Empty set: ∅ = {} (set with no elements)
    • Universal set: U (all objects under consideration)

Operations:
    • Union: A ∪ B = {x : x ∈ A or x ∈ B}
    • Intersection: A ∩ B = {x : x ∈ A and x ∈ B}
    • Difference: A \ B = {x : x ∈ A and x ∉ B}
    • Complement: A' = {x ∈ U : x ∉ A}
    • Cartesian product: A × B = {(a,b) : a ∈ A, b ∈ B}

Properties:
    • Union is commutative: A ∪ B = B ∪ A
    • Union is associative: (A ∪ B) ∪ C = A ∪ (B ∪ C)
    • Intersection is distributive over union: A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)
    • De Morgan's Laws: (A ∪ B)' = A' ∩ B'

Applications:
    • Logic and Boolean algebra
    • Probability (event spaces)
    • Databases (relational algebra)
    • Computer science (data structures)
    • Type theory (programming languages)

Let's LEARN set theory through exploration! ∪∩✨
"""

import asyncio
from supe import Supe
from ab.models import Buffer


def draw_venn_2_sets():
    """Venn diagram for 2 sets."""
    return """
    Two Sets: A and B

           A         B
         •••••     •••••
        ••   ••   ••   ••
       ••     •••••     ••
       •      █████      •
       •      █████      •
       ••     •••••     ••
        ••   ••   ••   ••
         •••••     •••••

    Regions:
    • A only: A \ B (left crescent)
    • Both: A ∩ B (middle █)
    • B only: B \ A (right crescent)
    • Neither: (A ∪ B)' (outside)
    """


def draw_venn_3_sets():
    """Venn diagram for 3 sets."""
    return """
    Three Sets: A, B, C

              A
            •••••
           ••   ••
          ••  ╔══╗  ••
         •• B ║  ║ C ••
         •  ╔═╩══╩═╗  •
         • ╔╝ ████  ╚╗ •
         • ║  ████   ║ •
         •  ╚═════════╝  •
          ••           ••
           ••         ••
            •••••••••••

    Center region: A ∩ B ∩ C (all three)
    7 regions total:
    - A only, B only, C only
    - A∩B only, A∩C only, B∩C only
    - A∩B∩C (all three)
    """


def draw_subset_relation():
    """Visualize subset."""
    return """
    Subset: A ⊆ B

         B (larger)
       •••••••••••
      ••         ••
     ••    A      ••
     ••  •••••    ••
     •  ••   ••    •
     •  ••   ••    •
     •  •••••••    •
     ••           ••
      ••         ••
       •••••••••••

    Every element of A is in B
    A ⊆ B ⟹ A ∩ B = A
    """


def draw_union():
    """Visualize union operation."""
    return """
    Union: A ∪ B (everything in either set)

       A         B
     █████     █████
    ██   ██   ██   ██
    ██    ███████    ██
    ██    ███████    ██
    ██   ██   ██   ██
     █████     █████

    A ∪ B = {x : x ∈ A or x ∈ B}

    Example:
    A = {1, 2, 3}
    B = {3, 4, 5}
    A ∪ B = {1, 2, 3, 4, 5}
    """


def draw_intersection():
    """Visualize intersection operation."""
    return """
    Intersection: A ∩ B (only shared elements)

       A         B
     •••••     •••••
    ••   ••   ••   ██
    ••    •••••    ██
    •      ███      •
    ••    •••••    ██
    ••   ••   ••   ██
     •••••     •••••

    A ∩ B = {x : x ∈ A and x ∈ B}

    Example:
    A = {1, 2, 3}
    B = {3, 4, 5}
    A ∩ B = {3}
    """


def draw_difference():
    """Visualize set difference."""
    return """
    Difference: A \ B (in A but not B)

       A         B
     █████     •••••
    ██   ██   ••   ••
    ██    •••••     ••
    ██              •
    ██    •••••     ••
    ██   ██   ••   ••
     █████     •••••

    A \ B = {x : x ∈ A and x ∉ B}

    Example:
    A = {1, 2, 3}
    B = {3, 4, 5}
    A \ B = {1, 2}
    """


def draw_complement():
    """Visualize complement."""
    return """
    Complement: A' (everything NOT in A)

    Universe U
    ████████████████████
    ████ A ██████████████
    ████•••••████████████
    ███••   ••███████████
    ███••   ••███████████
    ████•••••████████████
    ████████████████████
    ████████████████████

    A' = {x ∈ U : x ∉ A}
    A ∪ A' = U
    A ∩ A' = ∅
    """


def draw_cartesian_product():
    """Visualize Cartesian product."""
    return """
    Cartesian Product: A × B (ordered pairs)

    B (y-axis)
    3 • (a,3)  (b,3)  (c,3)
      │
    2 • (a,2)  (b,2)  (c,2)
      │
    1 • (a,1)  (b,1)  (c,1)
      │
    0 └─────────────────→ A (x-axis)
        a      b      c

    A × B = {(a,b) : a ∈ A, b ∈ B}

    Example:
    A = {a, b, c}
    B = {1, 2, 3}
    A × B = {(a,1), (a,2), (a,3),
             (b,1), (b,2), (b,3),
             (c,1), (c,2), (c,3)}
    |A × B| = |A| · |B| = 3 · 3 = 9
    """


def draw_power_set():
    """Visualize power set."""
    return """
    Power Set: 𝒫(A) (all subsets of A)

    A = {a, b, c}

    𝒫(A) = {
        ∅,           (empty set)
        {a}, {b}, {c},  (singletons)
        {a,b}, {a,c}, {b,c},  (pairs)
        {a,b,c}      (whole set)
    }

    |𝒫(A)| = 2^|A| = 2^3 = 8 subsets

    Tree structure:
              {a,b,c}
            /    |    \\
        {a,b}  {a,c}  {b,c}
        / | \\  / | \\  / | \\
      {a}{b}{c} ...
        \\ | /
          ∅
    """


async def main():
    print("=" * 80)
    print("∪∩ MATHEMATICAL DISCOVERY: Set Theory - Foundation of Mathematics")
    print("=" * 80)
    print()
    print("Using EXPLORE mode to discover set theory properties!")
    print("Beautiful Venn diagrams and fundamental laws")
    print()

    supe = Supe(db_path=":memory:")

    # Seed set theory knowledge
    print("📚 Seeding set theory definitions...")

    set_def = """Set Theory: Foundation of Modern Mathematics

Sets: Collections of distinct objects
- Notation: A = {1, 2, 3}
- Element notation: x ∈ A (x is in A)
- Empty set: ∅ = {}
- Universal set: U

Basic Operations:
- Union: A ∪ B = {x : x ∈ A or x ∈ B}
- Intersection: A ∩ B = {x : x ∈ A and x ∈ B}
- Difference: A \\ B = {x : x ∈ A and x ∉ B}
- Complement: A' = {x ∈ U : x ∉ A}

Relations:
- Subset: A ⊆ B means ∀x(x ∈ A ⟹ x ∈ B)
- Proper subset: A ⊂ B means A ⊆ B and A ≠ B
- Equality: A = B means A ⊆ B and B ⊆ A

Properties:
- Union is commutative: A ∪ B = B ∪ A
- Union is associative: (A ∪ B) ∪ C = A ∪ (B ∪ C)
- Intersection is commutative: A ∩ B = B ∩ A
- Intersection is associative: (A ∩ B) ∩ C = A ∩ (B ∩ C)
- Distributive: A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)
- De Morgan's: (A ∪ B)' = A' ∩ B'

Cardinality:
- |A| = number of elements in A
- |A ∪ B| = |A| + |B| - |A ∩ B|
- |A × B| = |A| · |B|
- |𝒫(A)| = 2^|A| (power set)"""

    supe.memory.store_card(
        label="set_theory_definitions",
        buffers=[Buffer(name="content", payload=set_def.encode('utf-8'))],
        master_output="Set theory definitions and properties",
        track="awareness",
    )
    print("✓ Set theory concepts defined\n")

    # Discovery 1: Union is commutative
    print("🔍 DISCOVERY 1: Union is Commutative")
    print("-" * 80)
    print(draw_union())
    print("Question: Is A ∪ B = B ∪ A?")
    print()
    print("Test: A = {1, 2}, B = {2, 3}")
    print("  A ∪ B = {1, 2, 3}")
    print("  B ∪ A = {1, 2, 3} ✓")
    print()

    result1 = await supe.learn(
        "Is set union commutative? (Is A ∪ B = B ∪ A?)",
        mode="explore"
    )

    if result1['beliefs_count'] > 0:
        status = result1['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result1['confidence']:.2f}")
        print(f"Proof Hash: {result1['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Union is commutative!")
            print("⟹ Order doesn't matter in set union!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 2: Intersection is commutative
    print("🔍 DISCOVERY 2: Intersection is Commutative")
    print("-" * 80)
    print(draw_intersection())
    print("Question: Is A ∩ B = B ∩ A?")
    print()
    print("Test: A = {1, 2, 3}, B = {2, 3, 4}")
    print("  A ∩ B = {2, 3}")
    print("  B ∩ A = {2, 3} ✓")
    print()

    result2 = await supe.learn(
        "Is set intersection commutative? (Is A ∩ B = B ∩ A?)",
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

    # Discovery 3: Distributive property
    print("🔍 DISCOVERY 3: Intersection Distributes Over Union")
    print("-" * 80)
    print(draw_venn_3_sets())
    print("Question: Is A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)?")
    print()
    print("Test: A = {1, 2}, B = {2, 3}, C = {3, 4}")
    print("  Left: A ∩ (B ∪ C) = {1,2} ∩ {2,3,4} = {2}")
    print("  Right: (A ∩ B) ∪ (A ∩ C) = {2} ∪ ∅ = {2} ✓")
    print()

    result3 = await supe.learn(
        "Is intersection distributive over union? Test: A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)",
        mode="explore"
    )

    if result3['beliefs_count'] > 0:
        status = result3['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"Proof Hash: {result3['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Distributive property VERIFIED!")
            print("⟹ Analogous to a·(b+c) = a·b + a·c in algebra!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 4: Cardinality formula
    print("🔍 DISCOVERY 4: Cardinality of Union")
    print("-" * 80)
    print(draw_venn_2_sets())
    print("Question: Is |A ∪ B| = |A| + |B| - |A ∩ B|?")
    print()
    print("Test: A = {1, 2, 3}, B = {3, 4, 5}")
    print("  |A| = 3, |B| = 3, |A ∩ B| = 1")
    print("  |A ∪ B| = 5 (elements: 1,2,3,4,5)")
    print("  3 + 3 - 1 = 5 ✓")
    print()

    result4 = await supe.learn(
        "For sets with |A|=3, |B|=3, |A∩B|=1, is |A∪B| = 3+3-1 = 5? (Inclusion-exclusion)",
        mode="explore"
    )

    if result4['beliefs_count'] > 0:
        status = result4['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result4['confidence']:.2f}")
        print(f"Proof Hash: {result4['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Inclusion-exclusion principle VERIFIED!")
            print("⟹ Must subtract overlap to avoid double-counting!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 5: Power set cardinality
    print("🔍 DISCOVERY 5: Power Set Cardinality")
    print("-" * 80)
    print(draw_power_set())
    print("Question: For |A| = 3, is |𝒫(A)| = 2³ = 8?")
    print()
    print("A = {a, b, c}")
    print("𝒫(A) = {∅, {a}, {b}, {c}, {a,b}, {a,c}, {b,c}, {a,b,c}}")
    print("Count: 8 subsets ✓")
    print()

    result5 = await supe.learn(
        "For a set with 3 elements, does the power set have 2³ = 8 subsets? (Power set cardinality)",
        mode="explore"
    )

    if result5['beliefs_count'] > 0:
        status = result5['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result5['confidence']:.2f}")
        print(f"Proof Hash: {result5['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Power set formula VERIFIED!")
            print("⟹ |𝒫(A)| = 2^|A| (each element: in or out)")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Display visualizations
    print("=" * 80)
    print("🎨 SET THEORY VISUALIZATIONS")
    print("=" * 80)
    print()
    print("⊆ Subset Relation:")
    print(draw_subset_relation())
    print()
    print("∪ Union:")
    print(draw_union())
    print()
    print("∩ Intersection:")
    print(draw_intersection())
    print()
    print("\ Difference:")
    print(draw_difference())
    print()
    print("' Complement:")
    print(draw_complement())
    print()
    print("× Cartesian Product:")
    print(draw_cartesian_product())
    print()
    print("𝒫 Power Set:")
    print(draw_power_set())
    print()

    # Summary
    print("=" * 80)
    print("🎓 SET THEORY DISCOVERIES")
    print("=" * 80)
    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                    SET THEORY FUNDAMENTALS                           ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║                                                                      ║")
    print("║  Basic Operations:                                                   ║")
    print("║    • Union: A ∪ B (everything in either)                            ║")
    print("║    • Intersection: A ∩ B (only shared elements)                     ║")
    print("║    • Difference: A \\ B (in A but not B)                             ║")
    print("║    • Complement: A' (everything not in A)                           ║")
    print("║                                                                      ║")
    print("║  Properties:                                                         ║")
    print("║    • Union is commutative: A ∪ B = B ∪ A                            ║")
    print("║    • Intersection is commutative: A ∩ B = B ∩ A                     ║")
    print("║    • Distributive: A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)                 ║")
    print("║    • De Morgan's: (A ∪ B)' = A' ∩ B'                                ║")
    print("║                                                                      ║")
    print("║  Cardinality:                                                        ║")
    print("║    • |A ∪ B| = |A| + |B| - |A ∩ B| (inclusion-exclusion)            ║")
    print("║    • |A × B| = |A| · |B| (product rule)                             ║")
    print("║    • |𝒫(A)| = 2^|A| (power set)                                     ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("🌟 What We Learned:")
    print(f"   • Total beliefs formed: {sum(1 for r in [result1, result2, result3, result4, result5] if r['beliefs_count'] > 0)}")
    print("   • Each discovery stored with proof hash")
    print("   • Linked to Tasc execution for traceability")
    print()
    print("🔗 Connections:")
    print("   Set Theory ──→ Logic (Boolean algebra: ∪ is OR, ∩ is AND)")
    print("              ──→ Probability (events are sets)")
    print("              ──→ Databases (relational algebra)")
    print("              ──→ Type Theory (types as sets)")
    print("              ──→ Topology (open sets, closed sets)")
    print()
    print("💡 Next Set Theory Horizons:")
    print("   • Relations: R ⊆ A × B (functions, equivalence relations)")
    print("   • Functions: f: A → B (injective, surjective, bijective)")
    print("   • Infinite sets: Cantor's diagonal argument")
    print("   • Cardinality: ℵ₀ (countable) vs ℵ₁ (uncountable)")
    print("   • Zermelo-Fraenkel axioms (ZFC)")
    print("   • Russell's paradox: {x : x ∉ x}")
    print()
    print("🎭 Philosophy:")
    print("   Set theory is the language of mathematics!")
    print("   Everything can be built from sets: numbers, functions, structures.")
    print("   \"God made the integers, all else is the work of man\" - Kronecker")
    print("   But actually, sets came first! ∈")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
