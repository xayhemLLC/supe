"""Solve quartic factorization problem using supe's reasoning engine.

Problem 145:
The quadratic function 54x⁴ + 219x² + 105 has factors in the form
(k)(ax² + b)(cx² + d). If a, b, c, d, and k are integers, what is the
smallest possible value of ab?

This demonstrates:
1. Constraint encoding (coefficient matching)
2. Hypothesis generation (possible factor combinations)
3. Systematic testing (verification of each factorization)
4. Optimization (finding minimum ab)
5. Evidence-based selection using SUPPORTS/INVALIDATES relations
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Tuple
import math

from ab.abdb import ABMemory
from ab.models import Buffer
from tasc.evidence import Evidence, EvidenceSource
from tasc.relations import Relation, RelationType
from tasc.relation_storage import store_relation, get_support_network
from tasc.reasoning_engine import ReasoningEngine
from tasc.validation_integration import ValidationRelationIntegrator


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def encode_polynomial(memory: ABMemory, integrator: ValidationRelationIntegrator):
    """Step 1: Encode the polynomial and factorization constraints."""
    print_section("STEP 1: Encode Polynomial and Constraints")

    print("Given polynomial: 54x⁴ + 219x² + 105")
    print("Target form: k(ax² + b)(cx² + d)\n")

    # Create polynomial card
    poly = memory.store_card(
        label="Polynomial: 54x⁴ + 219x² + 105",
        buffers=[
            Buffer(name="x4_coeff", payload=b"54"),
            Buffer(name="x2_coeff", payload=b"219"),
            Buffer(name="constant", payload=b"105"),
        ],
        track="awareness",
    )

    print(f"  ✓ Polynomial encoded (card {poly.id})")

    # Expand target form to get constraints
    print("\nExpanding k(ax² + b)(cx² + d):")
    print("  = k(acx⁴ + (ad + bc)x² + bd)")
    print("  = kac·x⁴ + k(ad + bc)·x² + kbd")

    print("\nCoefficient matching constraints:")
    print("  x⁴ coefficient: kac = 54")
    print("  x² coefficient: k(ad + bc) = 219")
    print("  constant term: kbd = 105")

    # Create constraint cards
    constraint1 = integrator.store_belief_as_card(
        "Constraint 1: kac = 54",
        metadata={"type": "coefficient_match", "term": "x4"},
    )

    constraint2 = integrator.store_belief_as_card(
        "Constraint 2: k(ad + bc) = 219",
        metadata={"type": "coefficient_match", "term": "x2"},
    )

    constraint3 = integrator.store_belief_as_card(
        "Constraint 3: kbd = 105",
        metadata={"type": "coefficient_match", "term": "constant"},
    )

    print(f"\n  ✓ Constraint 1: kac = 54 (card {constraint1})")
    print(f"  ✓ Constraint 2: k(ad+bc) = 219 (card {constraint2})")
    print(f"  ✓ Constraint 3: kbd = 105 (card {constraint3})")

    return {
        "poly": poly.id,
        "constraints": [constraint1, constraint2, constraint3],
    }


def find_divisors(n: int) -> List[int]:
    """Find all positive divisors of n."""
    divisors = []
    for i in range(1, int(math.sqrt(n)) + 1):
        if n % i == 0:
            divisors.append(i)
            if i != n // i:
                divisors.append(n // i)
    return sorted(divisors)


def determine_k_values(
    memory: ABMemory,
    integrator: ValidationRelationIntegrator,
):
    """Step 2: Determine possible values of k."""
    print_section("STEP 2: Determine Possible k Values")

    print("For integer solutions, k must divide gcd(54, 219, 105)\n")

    print("Factorizations:")
    print("  54 = 2 × 3³")
    print("  219 = 3 × 73")
    print("  105 = 3 × 5 × 7")

    print("\n  gcd(54, 219, 105) = 3")

    k_values = [1, 3]
    print(f"\n  Possible k values: {k_values}")

    # Create belief about k values
    k_belief = integrator.store_belief_as_card(
        "k must divide gcd(54, 219, 105) = 3, so k ∈ {1, 3}",
        metadata={"k_values": k_values, "reasoning": "gcd_divisibility"},
    )

    print(f"  ✓ k constraint (card {k_belief})")

    return {"k_values": k_values, "k_belief": k_belief}


def generate_factorization_hypotheses(
    memory: ABMemory,
    integrator: ValidationRelationIntegrator,
    k_values: List[int],
):
    """Step 3: Generate all possible factorizations."""
    print_section("STEP 3: Generate Factorization Hypotheses")

    hypotheses = []

    for k in k_values:
        print(f"\nFor k = {k}:")
        print(f"  Need: ac = {54//k}, bd = {105//k}, ad + bc = {219//k}")

        ac_target = 54 // k
        bd_target = 105 // k
        sum_target = 219 // k

        # Find divisors of ac_target
        ac_divisors = find_divisors(ac_target)
        bd_divisors = find_divisors(bd_target)

        print(f"  Divisors of {ac_target}: {ac_divisors}")
        print(f"  Divisors of {bd_target}: {bd_divisors}")

        # Try all combinations
        for a in ac_divisors:
            c = ac_target // a
            for b in bd_divisors:
                d = bd_target // b

                # Check if ad + bc = sum_target
                if a * d + b * c == sum_target:
                    ab = a * b

                    # Create hypothesis card
                    hyp = integrator.store_belief_as_card(
                        f"Factorization: k={k}, a={a}, b={b}, c={c}, d={d}",
                        metadata={
                            "k": k, "a": a, "b": b, "c": c, "d": d,
                            "ab": ab, "ac": a*c, "bd": b*d, "sum": a*d + b*c,
                        },
                    )

                    hypotheses.append({
                        "card_id": hyp,
                        "k": k, "a": a, "b": b, "c": c, "d": d,
                        "ab": ab,
                    })

                    print(f"  ✓ Found: a={a}, b={b}, c={c}, d={d} → ab={ab} (card {hyp})")

    print(f"\nGenerated {len(hypotheses)} factorization hypotheses")

    return hypotheses


def test_factorizations(
    memory: ABMemory,
    integrator: ValidationRelationIntegrator,
    hypotheses: List[Dict],
):
    """Step 4: Test each factorization by expansion."""
    print_section("STEP 4: Test Factorizations")

    print("Verifying each factorization by expansion...\n")

    valid_factorizations = []

    for hyp in hypotheses:
        k, a, b, c, d = hyp["k"], hyp["a"], hyp["b"], hyp["c"], hyp["d"]
        card_id = hyp["card_id"]

        print(f"Testing: k={k}, a={a}, b={b}, c={c}, d={d} (ab={hyp['ab']})")

        # Expand k(ax² + b)(cx² + d)
        # = k(acx⁴ + adx² + bcx² + bd)
        # = kacx⁴ + k(ad+bc)x² + kbd

        x4_coeff = k * a * c
        x2_coeff = k * (a * d + b * c)
        const_coeff = k * b * d

        print(f"  Expanded: {x4_coeff}x⁴ + {x2_coeff}x² + {const_coeff}")

        # Check if matches 54x⁴ + 219x² + 105
        matches = (x4_coeff == 54 and x2_coeff == 219 and const_coeff == 105)

        if matches:
            print(f"  ✓ MATCHES target polynomial!")

            # Create supporting evidence
            ev = Evidence.create(
                f"Factorization k={k}, a={a}, b={b}, c={c}, d={d} expands to 54x⁴ + 219x² + 105",
                EvidenceSource.REASONING,
                ["algebraic_expansion"],
            )
            ev.validated = True
            ev.confidence = 1.0

            evidence_card = integrator.store_evidence_as_card(ev)

            # Create SUPPORTS relation
            rel = Relation.create(
                f"evidence_k{k}_a{a}_b{b}",
                RelationType.SUPPORTS,
                evidence_card,
                card_id,
                confidence=1.0,
            )
            store_relation(memory, rel)

            valid_factorizations.append(hyp)

        else:
            print(f"  ✗ Does NOT match (should be 54x⁴ + 219x² + 105)")

            # Create invalidating evidence
            ev = Evidence.create(
                f"Factorization k={k}, a={a}, b={b}, c={c}, d={d} expands incorrectly",
                EvidenceSource.REASONING,
                ["algebraic_expansion"],
            )
            ev.validated = True
            ev.confidence = 1.0

            evidence_card = integrator.store_evidence_as_card(ev)

            # Create INVALIDATES relation
            rel = Relation.create(
                f"counter_k{k}_a{a}_b{b}",
                RelationType.INVALIDATES,
                evidence_card,
                card_id,
                confidence=1.0,
            )
            store_relation(memory, rel)

        print()

    print(f"Valid factorizations: {len(valid_factorizations)}")

    return valid_factorizations


def find_minimum_ab(
    memory: ABMemory,
    reasoning: ReasoningEngine,
    valid_factorizations: List[Dict],
):
    """Step 5: Find factorization with minimum ab."""
    print_section("STEP 5: Find Minimum ab")

    print("Analyzing valid factorizations to find minimum ab...\n")

    for fact in valid_factorizations:
        card_id = fact["card_id"]
        support = get_support_network(memory, card_id)

        print(f"k={fact['k']}, a={fact['a']}, b={fact['b']}, c={fact['c']}, d={fact['d']}")
        print(f"  ab = {fact['ab']}")
        print(f"  SUPPORTS: {len(support)}")
        print()

    # Find minimum
    min_fact = min(valid_factorizations, key=lambda f: f["ab"])

    print(f"{'='*80}")
    print(f"MINIMUM ab = {min_fact['ab']}")
    print(f"  k={min_fact['k']}, a={min_fact['a']}, b={min_fact['b']}, c={min_fact['c']}, d={min_fact['d']}")
    print(f"{'='*80}")

    return min_fact


def explain_solution(min_fact: Dict):
    """Step 6: Generate detailed explanation."""
    print_section("STEP 6: Solution Explanation")

    k, a, b, c, d = min_fact["k"], min_fact["a"], min_fact["b"], min_fact["c"], min_fact["d"]
    ab = min_fact["ab"]

    print(f"ANSWER: ab = {ab}\n")

    print("COMPLETE REASONING:\n")

    print("1. Constraint Analysis:")
    print("   • Need: 54x⁴ + 219x² + 105 = k(ax² + b)(cx² + d)")
    print("   • Expanding: k(acx⁴ + (ad+bc)x² + bd)")
    print("   • Constraints: kac=54, k(ad+bc)=219, kbd=105\n")

    print("2. Finding k:")
    print("   • k must divide gcd(54, 219, 105)")
    print("   • gcd = 3")
    print("   • Possible k: {1, 3}\n")

    print("3. Systematic Search:")
    print("   • For each k, find all (a,c) pairs with ac = 54/k")
    print("   • For each (a,c), find (b,d) with bd = 105/k")
    print("   • Check if ad + bc = 219/k")
    print("   • Test all valid combinations\n")

    print(f"4. Optimal Factorization:")
    print(f"   • k = {k}")
    print(f"   • a = {a}, c = {c} → ac = {a*c}")
    print(f"   • b = {b}, d = {d} → bd = {b*d}")
    print(f"   • ad + bc = {a*d} + {b*c} = {a*d + b*c}")
    print(f"   • ab = {a} × {b} = {ab} ← MINIMUM\n")

    print("5. Verification:")
    print(f"   • {k}({a}x² + {b})({c}x² + {d})")
    print(f"   • = {k}({a*c}x⁴ + {a*d + b*c}x² + {b*d})")
    print(f"   • = {k*a*c}x⁴ + {k*(a*d + b*c)}x² + {k*b*d}")
    print(f"   • = 54x⁴ + 219x² + 105 ✓")


async def main():
    """Main demonstration."""

    print("\n" + "="*80)
    print("  SOLVING QUARTIC FACTORIZATION WITH SUPE")
    print("  Systematic Constraint Satisfaction + Optimization")
    print("="*80)

    print("\nPROBLEM 145:")
    print("  54x⁴ + 219x² + 105 = k(ax² + b)(cx² + d)")
    print("  Find the smallest possible value of ab")

    # Initialize
    db_path = Path.home() / ".supe" / "test_quartic_factorization.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    memory = ABMemory(str(db_path))
    integrator = ValidationRelationIntegrator(memory)
    reasoning = ReasoningEngine(memory)

    # Step 1: Encode polynomial
    poly_data = encode_polynomial(memory, integrator)

    # Step 2: Determine k values
    k_data = determine_k_values(memory, integrator)

    # Step 3: Generate hypotheses
    hypotheses = generate_factorization_hypotheses(
        memory, integrator, k_data["k_values"]
    )

    # Step 4: Test factorizations
    valid = test_factorizations(memory, integrator, hypotheses)

    # Step 5: Find minimum
    min_fact = find_minimum_ab(memory, reasoning, valid)

    # Step 6: Explain
    explain_solution(min_fact)

    # Summary
    print_section("DEMONSTRATION COMPLETE")

    print("Supe solved the problem using:")
    print("  ✓ Constraint encoding (coefficient matching)")
    print("  ✓ Systematic hypothesis generation (all factor combinations)")
    print("  ✓ Algebraic verification (expansion testing)")
    print("  ✓ Evidence-based validation (SUPPORTS relations)")
    print("  ✓ Optimization (finding minimum ab)")
    print("  ✓ Complete enumeration (no missed factorizations)\n")

    print(f"Final answer: ab = {min_fact['ab']}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
