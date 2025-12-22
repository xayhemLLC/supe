"""
Mathematical Discovery: Modular Arithmetic and Clock Math ⌚

Modular arithmetic is arithmetic "with wraparound" - like a clock!

Core Concept:
    a ≡ b (mod n)  means  "a and b have the same remainder when divided by n"

Example:
    14 ≡ 2 (mod 12)  because 14 = 1×12 + 2
    This is why 2pm and 14:00 are the same time on a 12-hour clock!

Notation:
    ≡ (congruence)
    ℤ/nℤ (integers modulo n)
    [a]ₙ (equivalence class of a mod n)
    ⊕ₙ (addition mod n)
    ⊗ₙ (multiplication mod n)

Questions to Discover:
    • Does clock arithmetic form a group?
    • Do the usual properties (commutativity, associativity) still hold?
    • What about multiplicative inverses? (Division in clock arithmetic)
    • Fermat's Little Theorem: aᵖ⁻¹ ≡ 1 (mod p) for prime p?
    • Chinese Remainder Theorem: Can we solve simultaneous congruences?

Let's discover the structure of ℤ/nℤ! 🕐
"""

import asyncio
from supe import Supe
from ab.models import Buffer


async def main():
    print("=" * 80)
    print("⌚ MATHEMATICAL DISCOVERY: Modular Arithmetic and Clock Math")
    print("=" * 80)
    print()
    print("Notation: a ≡ b (mod n) means 'a and b have the same remainder mod n'")
    print("Example: 14 ≡ 2 (mod 12) because both have remainder 2 when divided by 12")
    print()

    supe = Supe(db_path=":memory:")

    # Seed knowledge about modular arithmetic
    print("📚 Seeding knowledge about modular arithmetic...")

    mod_def = """Modular Arithmetic (Clock Math):

Definition: a ≡ b (mod n) if a and b have the same remainder when divided by n.
Equivalently: n divides (a - b).

Examples with mod 12 (12-hour clock):
- 14 ≡ 2 (mod 12) because 14 = 1×12 + 2
- 26 ≡ 2 (mod 12) because 26 = 2×12 + 2
- 3 + 10 ≡ 1 (mod 12) because 3 + 10 = 13 ≡ 1 (mod 12)
- 2pm is the same as 14:00 on a clock

Operations:
- Addition: (a + b) mod n
- Multiplication: (a × b) mod n
- Subtraction: (a - b) mod n

The set Z/nZ = {0, 1, 2, ..., n-1} with these operations."""

    supe.memory.store_card(
        label="definition",
        buffers=[Buffer(name="content", payload=mod_def.encode('utf-8'))],
        master_output="Modular arithmetic defined with clock examples",
        track="awareness",
    )
    print("✓ Modular arithmetic defined\n")

    # Discovery 1: Is addition commutative in clock arithmetic?
    print("🔍 DISCOVERY 1: Is clock addition commutative?")
    print("-" * 80)
    print("Question: In mod 12, is (a ⊕₁₂ b) = (b ⊕₁₂ a)?")
    print("Test: 3 + 10 ≡ 10 + 3 (mod 12)?")
    print("      3 + 10 = 13 ≡ 1 (mod 12)")
    print("      10 + 3 = 13 ≡ 1 (mod 12)")
    print()

    result1 = await supe.learn(
        "Is addition commutative in modular arithmetic? (Is 3 + 10 ≡ 10 + 3 mod 12?)",
        mode="explore"
    )

    if result1['beliefs_count'] > 0:
        status = result1['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result1['confidence']:.2f}")
        if status == 'PROVEN':
            print("⟹ Clock addition is commutative! (a ⊕ₙ b) = (b ⊕ₙ a)")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 2: Is multiplication commutative?
    print("🔍 DISCOVERY 2: Is clock multiplication commutative?")
    print("-" * 80)
    print("Question: In mod 12, is (a ⊗₁₂ b) = (b ⊗₁₂ a)?")
    print("Test: 3 × 5 ≡ 5 × 3 (mod 12)?")
    print("      3 × 5 = 15 ≡ 3 (mod 12)")
    print("      5 × 3 = 15 ≡ 3 (mod 12)")
    print()

    result2 = await supe.learn(
        "Is multiplication commutative mod 12? (Is 3 × 5 ≡ 5 × 3 mod 12?)",
        mode="explore"
    )

    if result2['beliefs_count'] > 0:
        status = result2['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result2['confidence']:.2f}")
        if status == 'PROVEN':
            print("⟹ Clock multiplication is commutative! (a ⊗ₙ b) = (b ⊗ₙ a)")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 3: Additive identity in clock arithmetic
    print("🔍 DISCOVERY 3: What is the additive identity in ℤ/12ℤ?")
    print("-" * 80)
    print("Question: Is 0 the additive identity? (a ⊕₁₂ 0 = a?)")
    print("Test: 7 + 0 ≡ 7 (mod 12)?")
    print()

    result3 = await supe.learn(
        "Is 0 the additive identity mod 12? (Is 7 + 0 ≡ 7 mod 12?)",
        mode="explore"
    )

    if result3['beliefs_count'] > 0:
        status = result3['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result3['confidence']:.2f}")
        if status == 'PROVEN':
            print("⟹ Zero is the additive identity in ℤ/nℤ!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 4: Additive inverses (negative numbers in clock arithmetic)
    print("🔍 DISCOVERY 4: Do additive inverses exist in clock math?")
    print("-" * 80)
    print("Question: For any a in ℤ/12ℤ, does there exist b such that a ⊕₁₂ b ≡ 0?")
    print("Test: What is the inverse of 5 mod 12?")
    print("      5 + ? ≡ 0 (mod 12)")
    print("      5 + 7 = 12 ≡ 0 (mod 12) ✓")
    print("      So the inverse of 5 is 7!")
    print()

    result4 = await supe.learn(
        "Does 5 have an additive inverse mod 12? (Is 5 + 7 ≡ 0 mod 12?)",
        mode="explore"
    )

    if result4['beliefs_count'] > 0:
        status = result4['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result4['confidence']:.2f}")
        if status == 'PROVEN':
            print("⟹ Every element in ℤ/nℤ has an additive inverse!")
            print("⟹ The inverse of a is (n - a) mod n")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 5: Multiplicative inverses (when do they exist?)
    print("🔍 DISCOVERY 5: Which elements have multiplicative inverses?")
    print("-" * 80)
    print("Question: Does 5 have a multiplicative inverse mod 12?")
    print("Looking for: 5 × ? ≡ 1 (mod 12)")
    print()
    print("Testing:")
    print("  5 × 1 = 5 (mod 12) ✗")
    print("  5 × 2 = 10 (mod 12) ✗")
    print("  5 × 3 = 15 ≡ 3 (mod 12) ✗")
    print("  5 × 5 = 25 ≡ 1 (mod 12) ✓")
    print()
    print("So 5⁻¹ ≡ 5 (mod 12)! 5 is its own multiplicative inverse!")
    print()

    result5 = await supe.learn(
        "Does 5 have a multiplicative inverse mod 12? (Is 5 × 5 ≡ 1 mod 12?)",
        mode="explore"
    )

    if result5['beliefs_count'] > 0:
        status = result5['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result5['confidence']:.2f}")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 6: What about 6 mod 12? (gcd matters!)
    print("🔍 DISCOVERY 6: Does 6 have a multiplicative inverse mod 12?")
    print("-" * 80)
    print("Question: Does there exist x such that 6 × x ≡ 1 (mod 12)?")
    print()
    print("Testing all possibilities:")
    print("  6 × 1 = 6 (mod 12)")
    print("  6 × 2 = 12 ≡ 0 (mod 12)")
    print("  6 × 3 = 18 ≡ 6 (mod 12)")
    print("  6 × 4 = 24 ≡ 0 (mod 12)")
    print("  6 × 5 = 30 ≡ 6 (mod 12)")
    print("  ... all multiples of 6 are either 0 or 6 (mod 12), never 1!")
    print()
    print("Why? gcd(6, 12) = 6 ≠ 1 → no inverse exists!")
    print()

    result6 = await supe.learn(
        "Does 6 have a multiplicative inverse mod 12? (Can we find x where 6x ≡ 1 mod 12?)",
        mode="explore"
    )

    if result6['beliefs_count'] > 0:
        status = result6['beliefs'][0]['content']['status']
        print(f"Result: {status}")
        print(f"Confidence: {result6['confidence']:.2f}")
        if status == 'DISPROVEN':
            print("⟹ 6 has NO multiplicative inverse mod 12!")
            print("⟹ Rule: a has an inverse mod n ⟺ gcd(a, n) = 1")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 7: Mod 7 is special (prime modulus)
    print("🔍 DISCOVERY 7: What's special about mod 7? (prime modulus)")
    print("-" * 80)
    print("Question: Does every nonzero element have an inverse mod 7?")
    print()
    print("ℤ/7ℤ = {0, 1, 2, 3, 4, 5, 6}")
    print()
    print("Inverse table:")
    print("  1 × 1 ≡ 1 (mod 7) → 1⁻¹ = 1")
    print("  2 × 4 ≡ 8 ≡ 1 (mod 7) → 2⁻¹ = 4")
    print("  3 × 5 ≡ 15 ≡ 1 (mod 7) → 3⁻¹ = 5")
    print("  6 × 6 ≡ 36 ≡ 1 (mod 7) → 6⁻¹ = 6")
    print()
    print("Every nonzero element has an inverse!")
    print()

    result7 = await supe.learn(
        "Does 2 have a multiplicative inverse mod 7? (Is 2 × 4 ≡ 1 mod 7?)",
        mode="explore"
    )

    if result7['beliefs_count'] > 0:
        status = result7['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result7['confidence']:.2f}")
        if status == 'PROVEN':
            print("⟹ When n is prime, ℤ/nℤ* forms a FIELD!")
            print("⟹ Every nonzero element has a multiplicative inverse")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 8: Fermat's Little Theorem hint
    print("🔍 DISCOVERY 8: Fermat's Little Theorem (glimpse)")
    print("-" * 80)
    print("Fermat's Little Theorem: If p is prime and gcd(a, p) = 1, then:")
    print("    aᵖ⁻¹ ≡ 1 (mod p)")
    print()
    print("Test with p = 7, a = 2:")
    print("    2⁶ ≡ ? (mod 7)")
    print("    2¹ = 2")
    print("    2² = 4")
    print("    2³ = 8 ≡ 1 (mod 7)")
    print("    2⁶ = (2³)² ≡ 1² ≡ 1 (mod 7) ✓")
    print()

    result8 = await supe.learn(
        "Does 2^6 ≡ 1 (mod 7)? (Fermat's Little Theorem)",
        mode="explore"
    )

    if result8['beliefs_count'] > 0:
        status = result8['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✓' if status == 'PROVEN' else '✗'}")
        print(f"Confidence: {result8['confidence']:.2f}")
        if status == 'PROVEN':
            print("⟹ Fermat's Little Theorem verified!")
            print("⟹ This is the foundation of RSA cryptography!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Summary
    print("=" * 80)
    print("🎓 MODULAR ARITHMETIC DISCOVERIES")
    print("=" * 80)
    print()
    print("Structure of ℤ/nℤ (Integers mod n):")
    print()
    print("1️⃣  Addition Properties:")
    print("    • Commutative: a ⊕ b = b ⊕ a")
    print("    • Associative: (a ⊕ b) ⊕ c = a ⊕ (b ⊕ c)")
    print("    • Identity: 0 (a ⊕ 0 = a)")
    print("    • Inverses: Every element has additive inverse")
    print("    ⟹ (ℤ/nℤ, ⊕) is an ABELIAN GROUP!")
    print()
    print("2️⃣  Multiplication Properties:")
    print("    • Commutative: a ⊗ b = b ⊗ a")
    print("    • Associative: (a ⊗ b) ⊗ c = a ⊗ (b ⊗ c)")
    print("    • Identity: 1 (a ⊗ 1 = a)")
    print("    • Inverses: a has inverse ⟺ gcd(a, n) = 1")
    print()
    print("3️⃣  Special Case - Prime Modulus:")
    print("    • When n = p (prime), every nonzero element has inverse")
    print("    • (ℤ/pℤ, ⊕, ⊗) is a FINITE FIELD!")
    print("    • Notation: 𝔽ₚ or GF(p)")
    print()
    print("4️⃣  Fermat's Little Theorem:")
    print("    • If p is prime and gcd(a, p) = 1:")
    print("    • Then aᵖ⁻¹ ≡ 1 (mod p)")
    print("    • Foundation of RSA encryption!")
    print()
    print("🔐 Applications:")
    print("    • Cryptography: RSA, Diffie-Hellman, elliptic curves")
    print("    • Hash functions: Checksums, hash tables")
    print("    • Random number generation: Linear congruential generators")
    print("    • Error correction: Cyclic redundancy checks (CRC)")
    print("    • Computer graphics: Texture mapping, color quantization")
    print()
    print("💡 Next Discoveries:")
    print("    • Chinese Remainder Theorem: Solving simultaneous congruences")
    print("    • Quadratic residues: Is x² ≡ a (mod p) solvable?")
    print("    • Primitive roots: Generators of ℤ/pℤ*")
    print("    • Elliptic curves: Points on y² = x³ + ax + b (mod p)")
    print()
    print("🎨 Beautiful Patterns:")
    print("    • Multiplication table mod 7 has perfect symmetry")
    print("    • Powers cycle: 2¹, 2², 2³, ... eventually repeat mod n")
    print("    • Wilson's Theorem: (p-1)! ≡ -1 (mod p) for prime p")
    print()
    print("=" * 80)
    print()
    print("⌚ Clock arithmetic isn't just about time - it's a complete")
    print("   mathematical structure with deep connections to number theory,")
    print("   algebra, and cryptography!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
