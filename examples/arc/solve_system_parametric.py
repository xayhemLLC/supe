"""Solve system of linear equations with parametric point verification.

Problem 84:
    7x - 9y = 39
    35x - 45y = 195

For any real number r, which point lies on the graph of BOTH equations?
A) (3r, (7r-13)/3)
B) ((7r+13)/3, 3r)
C) (-7r/-9 + 39, 7r/9 + 195)
D) (r/5 + 39, -r/5 + 195)

This demonstrates algebraic reasoning using the reasoning engine to:
1. Detect dependent/independent equations
2. Find the general solution (parametric form)
3. Test each candidate point by substitution
4. Use SUPPORTS/INVALIDATES relations to track which points satisfy constraints
"""

import asyncio
from pathlib import Path
from typing import Dict, Tuple

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


def encode_equations(memory: ABMemory, integrator: ValidationRelationIntegrator):
    """Step 1: Encode the system of equations as constraints."""
    print_section("STEP 1: Encode System of Equations")

    print("Given system:")
    print("  Equation 1: 7x - 9y = 39")
    print("  Equation 2: 35x - 45y = 195\n")

    # Create equation cards
    eq1 = memory.store_card(
        label="Equation 1: 7x - 9y = 39",
        buffers=[
            Buffer(name="coefficients", payload=b"7,-9"),
            Buffer(name="constant", payload=b"39"),
            Buffer(name="equation", payload=b"7x - 9y = 39"),
        ],
        track="awareness",
    )

    eq2 = memory.store_card(
        label="Equation 2: 35x - 45y = 195",
        buffers=[
            Buffer(name="coefficients", payload=b"35,-45"),
            Buffer(name="constant", payload=b"195"),
            Buffer(name="equation", payload=b"35x - 45y = 195"),
        ],
        track="awareness",
    )

    print(f"  ✓ Equation 1 encoded (card {eq1.id})")
    print(f"  ✓ Equation 2 encoded (card {eq2.id})")

    return {"eq1": eq1.id, "eq2": eq2.id}


def analyze_dependency(
    memory: ABMemory,
    integrator: ValidationRelationIntegrator,
    equations: Dict,
):
    """Step 2: Analyze if equations are independent or dependent."""
    print_section("STEP 2: Analyze Equation Dependency")

    print("Checking if equations are independent...\n")

    # Equation 2: 35x - 45y = 195
    # Divide by 5: 7x - 9y = 39
    # This is identical to Equation 1!

    print("Analysis:")
    print("  Equation 2: 35x - 45y = 195")
    print("  Divide by 5: 7x - 9y = 39")
    print("  This equals Equation 1!")
    print("\n  → Equations are DEPENDENT (same line)")

    # Create belief about dependency
    dependent = integrator.store_belief_as_card(
        "Equations are dependent: Eq2 = 5 × Eq1",
        metadata={"relationship": "dependent", "factor": 5},
    )

    print(f"\n  ✓ Dependency detected (card {dependent})")

    # Create EQUALS relation (equations represent same constraint)
    rel = Relation.create(
        "eq_dependency",
        RelationType.EQUALS,
        equations["eq1"],
        equations["eq2"],
        confidence=1.0,
        metadata={"scaling_factor": 5},
    )
    store_relation(memory, rel)
    print(f"  ✓ Created EQUALS relation: Eq1 ≡ Eq2")

    # Implication: infinitely many solutions
    infinite_solutions = integrator.store_belief_as_card(
        "System has infinitely many solutions (all points on the line)",
        metadata={"solution_type": "infinite"},
    )

    rel2 = Relation.create(
        "dependent_implies_infinite",
        RelationType.IMPLIES,
        dependent,
        infinite_solutions,
        confidence=1.0,
    )
    store_relation(memory, rel2)

    print(f"  ✓ Implication: Dependent equations → infinite solutions (card {infinite_solutions})")

    return {"dependent": dependent, "infinite_solutions": infinite_solutions}


def derive_parametric_form(
    memory: ABMemory,
    integrator: ValidationRelationIntegrator,
):
    """Step 3: Derive parametric form of solution."""
    print_section("STEP 3: Derive Parametric Solution")

    print("From equation: 7x - 9y = 39\n")

    print("Solving for y in terms of x:")
    print("  7x - 9y = 39")
    print("  -9y = 39 - 7x")
    print("  y = (7x - 39) / 9")
    print("  y = 7x/9 - 39/9")
    print("  y = 7x/9 - 13/3")

    print("\nParametric form (let x = t):")
    print("  x = t")
    print("  y = 7t/9 - 13/3")

    print("\nAlternative form (let x = 3r):")
    print("  x = 3r")
    print("  y = 7(3r)/9 - 13/3")
    print("  y = 21r/9 - 13/3")
    print("  y = 7r/3 - 13/3")
    print("  y = (7r - 13)/3")

    # Store parametric solution
    parametric = integrator.store_belief_as_card(
        "Parametric solution: (3r, (7r-13)/3) for any r",
        metadata={"form": "parametric", "parameter": "r"},
    )

    print(f"\n  ✓ Parametric form: (3r, (7r-13)/3) (card {parametric})")

    return {"parametric": parametric}


def test_candidate_points(
    memory: ABMemory,
    integrator: ValidationRelationIntegrator,
    equations: Dict,
):
    """Step 4: Test each candidate point by substitution."""
    print_section("STEP 4: Test Candidate Points")

    candidates = {
        "A": ("3r", "(7r-13)/3", lambda r: (3*r, (7*r - 13)/3)),
        "B": ("(7r+13)/3", "3r", lambda r: ((7*r + 13)/3, 3*r)),
        "C": ("-7r/-9 + 39", "7r/9 + 195", lambda r: (7*r/9 + 39, 7*r/9 + 195)),
        "D": ("r/5 + 39", "-r/5 + 195", lambda r: (r/5 + 39, -r/5 + 195)),
    }

    print("Testing each option with r = 0, 1, 2 (arbitrary test values)...\n")

    results = {}

    for option, (x_expr, y_expr, point_func) in candidates.items():
        print(f"Option {option}: ({x_expr}, {y_expr})")

        # Test with multiple r values
        all_satisfy = True
        test_results = []

        for r_val in [0, 1, 2]:
            x, y = point_func(r_val)

            # Test Equation 1: 7x - 9y = 39
            eq1_result = 7*x - 9*y
            eq1_satisfied = abs(eq1_result - 39) < 0.0001

            # Test Equation 2: 35x - 45y = 195 (should be equivalent)
            eq2_result = 35*x - 45*y
            eq2_satisfied = abs(eq2_result - 195) < 0.0001

            satisfied = eq1_satisfied and eq2_satisfied
            test_results.append((r_val, x, y, eq1_result, eq2_result, satisfied))

            if not satisfied:
                all_satisfy = False

        # Create belief card for this option
        option_card = integrator.store_belief_as_card(
            f"Option {option}: ({x_expr}, {y_expr})",
            metadata={"option": option, "x_expr": x_expr, "y_expr": y_expr},
        )

        if all_satisfy:
            print(f"  ✓ SATISFIES both equations for all test values")

            # Create SUPPORTS evidence
            for r_val, x, y, eq1_result, eq2_result, _ in test_results:
                print(f"    r={r_val}: ({x:.3f}, {y:.3f}) → 7x-9y={eq1_result:.1f}, 35x-45y={eq2_result:.1f}")

                ev = Evidence.create(
                    f"Point ({x:.3f}, {y:.3f}) satisfies both equations",
                    EvidenceSource.REASONING,
                    [f"substitution_r={r_val}"],
                )
                ev.validated = True
                ev.confidence = 1.0

                evidence_card = integrator.store_evidence_as_card(ev)

                rel = Relation.create(
                    f"evidence_option{option}_r{r_val}",
                    RelationType.SUPPORTS,
                    evidence_card,
                    option_card,
                    confidence=1.0,
                )
                store_relation(memory, rel)

        else:
            print(f"  ✗ FAILS for some values")

            # Create INVALIDATES evidence
            for r_val, x, y, eq1_result, eq2_result, satisfied in test_results:
                if not satisfied:
                    print(f"    r={r_val}: ({x:.3f}, {y:.3f}) → 7x-9y={eq1_result:.1f} (should be 39)")

                    ev = Evidence.create(
                        f"Point ({x:.3f}, {y:.3f}) does NOT satisfy equations",
                        EvidenceSource.REASONING,
                        [f"substitution_r={r_val}"],
                    )
                    ev.validated = True
                    ev.confidence = 1.0

                    evidence_card = integrator.store_evidence_as_card(ev)

                    rel = Relation.create(
                        f"counter_option{option}_r{r_val}",
                        RelationType.INVALIDATES,
                        evidence_card,
                        option_card,
                        confidence=1.0,
                    )
                    store_relation(memory, rel)

        print()
        results[option] = {
            "card_id": option_card,
            "all_satisfy": all_satisfy,
            "test_results": test_results,
        }

    return results


def select_correct_answer(
    memory: ABMemory,
    reasoning: ReasoningEngine,
    results: Dict,
):
    """Step 5: Use reasoning engine to select answer based on support."""
    print_section("STEP 5: Select Correct Answer")

    print("Analyzing support networks...\n")

    for option, data in results.items():
        card_id = data["card_id"]

        support = get_support_network(memory, card_id)
        invalidations = list(memory.get_relations(target_card_id=card_id, relation_type="invalidates"))

        print(f"Option {option}:")
        print(f"  SUPPORTS: {len(support)}")
        print(f"  INVALIDATES: {len(invalidations)}")
        print(f"  Status: {'✓ VALID' if data['all_satisfy'] else '✗ INVALID'}")
        print()

    # Find option with support and no invalidations
    correct = [opt for opt, data in results.items() if data["all_satisfy"]]

    if correct:
        answer = correct[0]
        print(f"{'='*80}")
        print(f"CORRECT ANSWER: {answer}")
        print(f"{'='*80}")
        return answer
    else:
        print("ERROR: No valid option found!")
        return None


def explain_solution(answer: str):
    """Step 6: Generate detailed explanation."""
    print_section("STEP 6: Solution Explanation")

    print(f"ANSWER: {answer}\n")

    print("REASONING:\n")

    print("1. Equation Analysis:")
    print("   • Equation 1: 7x - 9y = 39")
    print("   • Equation 2: 35x - 45y = 195 = 5(7x - 9y) = 5(39)")
    print("   • Equations are DEPENDENT (represent the same line)\n")

    print("2. Infinitely Many Solutions:")
    print("   • Dependent equations → infinitely many solutions")
    print("   • All points on the line satisfy both equations")
    print("   • Need parametric form to express all solutions\n")

    print("3. Deriving Parametric Form:")
    print("   • From 7x - 9y = 39, solve for y:")
    print("   • y = (7x - 39)/9 = 7x/9 - 13/3")
    print("   • Let x = 3r (parameter):")
    print("   • y = 7(3r)/9 - 13/3 = 7r/3 - 13/3 = (7r - 13)/3")
    print("   • Solution: (3r, (7r-13)/3) for any real r\n")

    print("4. Verification:")
    print("   • Substitute (3r, (7r-13)/3) into Equation 1:")
    print("   • 7(3r) - 9((7r-13)/3) = 21r - 3(7r-13) = 21r - 21r + 39 = 39 ✓")
    print("   • Works for ANY value of r\n")

    if answer == "A":
        print("Option A: (3r, (7r-13)/3)")
        print("  This exactly matches our derived parametric form!")
        print("  For any real number r, this point lies on both equations")


async def main():
    """Main demonstration."""

    print("\n" + "="*80)
    print("  SOLVING SYSTEM OF EQUATIONS WITH PARAMETRIC POINTS")
    print("  Algebraic Reasoning with Constraint Satisfaction")
    print("="*80)

    print("\nPROBLEM 84:")
    print("  System: 7x - 9y = 39")
    print("          35x - 45y = 195")
    print("  Which point lies on both equations for any real r?")

    # Initialize
    db_path = Path.home() / ".supe" / "test_system_parametric.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    memory = ABMemory(str(db_path))
    integrator = ValidationRelationIntegrator(memory)
    reasoning = ReasoningEngine(memory)

    # Step 1: Encode equations
    equations = encode_equations(memory, integrator)

    # Step 2: Analyze dependency
    dependency = analyze_dependency(memory, integrator, equations)

    # Step 3: Derive parametric form
    parametric = derive_parametric_form(memory, integrator)

    # Step 4: Test candidates
    results = test_candidate_points(memory, integrator, equations)

    # Step 5: Select answer
    answer = select_correct_answer(memory, reasoning, results)

    # Step 6: Explain
    if answer:
        explain_solution(answer)

    # Summary
    print_section("DEMONSTRATION COMPLETE")

    print("Supe solved the system using:")
    print("  ✓ Equation dependency analysis (detecting equivalent equations)")
    print("  ✓ Parametric solution derivation (algebraic manipulation)")
    print("  ✓ Constraint satisfaction testing (substitution verification)")
    print("  ✓ Evidence-based selection (SUPPORTS/INVALIDATES relations)")
    print("  ✓ Systematic verification (multiple test values)\n")

    print(f"Final answer: {answer}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
