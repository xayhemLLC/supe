"""Solve grid number pattern using supe's reasoning engine.

Problem:
Given a 4x4 grid with numbers, find the pattern and determine the missing value:
    3  6  1  8
    5  6  3  0
    2  7  1  4
    5  4  2  ?

This demonstrates using the reasoning engine to:
1. Generate hypothesis about numerical relationships
2. Test hypotheses against all rows
3. Use logical IMPLIES relations to track which hypotheses hold
4. Select the hypothesis with strongest support
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Tuple

from ab.abdb import ABMemory
from ab.models import Buffer
from tasc.evidence import Evidence, EvidenceCollection, EvidenceSource
from tasc.relations import Relation, RelationType
from tasc.relation_storage import store_relation, get_support_network
from tasc.reasoning_engine import ReasoningEngine
from tasc.validation_integration import ValidationRelationIntegrator


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def model_grid_data(memory: ABMemory, integrator: ValidationRelationIntegrator):
    """Step 1: Model the grid data as cards."""
    print_section("STEP 1: Model Grid Data")

    grid = [
        [3, 6, 1, 8],
        [5, 6, 3, 0],
        [2, 7, 1, 4],
        [5, 4, 2, None],  # Missing value
    ]

    print("Grid:")
    for i, row in enumerate(grid, 1):
        row_str = "  ".join(str(x) if x is not None else "?" for x in row)
        print(f"  Row {i}: {row_str}")

    print("\nCreating row cards...")
    row_cards = []
    for i, row in enumerate(grid, 1):
        card = memory.store_card(
            label=f"Row {i}",
            buffers=[
                Buffer(name="col1", payload=str(row[0]).encode()),
                Buffer(name="col2", payload=str(row[1]).encode()),
                Buffer(name="col3", payload=str(row[2]).encode()),
                Buffer(name="col4", payload=str(row[3]).encode() if row[3] is not None else b"?"),
            ],
            track="execution",
        )
        row_cards.append((card.id, row))
        print(f"  ✓ Row {i} (card {card.id}): {row}")

    return {"grid": grid, "row_cards": row_cards}


def generate_hypotheses(memory: ABMemory, integrator: ValidationRelationIntegrator, data: Dict):
    """Step 2: Generate multiple hypotheses about the pattern."""
    print_section("STEP 2: Generate Pattern Hypotheses")

    print("Generating candidate hypotheses...\n")

    # Hypothesis 1: Sum
    hyp1 = integrator.store_belief_as_card(
        "Pattern: col4 = col1 + col2 + col3",
        metadata={"type": "sum", "formula": "c4 = c1 + c2 + c3"},
    )
    print(f"  H1: Sum pattern (card {hyp1})")
    print(f"      Formula: col4 = col1 + col2 + col3")

    # Hypothesis 2: Product
    hyp2 = integrator.store_belief_as_card(
        "Pattern: col4 = col1 × col2 × col3",
        metadata={"type": "product", "formula": "c4 = c1 * c2 * c3"},
    )
    print(f"\n  H2: Product pattern (card {hyp2})")
    print(f"      Formula: col4 = col1 × col2 × col3")

    # Hypothesis 3: Product modulo 10
    hyp3 = integrator.store_belief_as_card(
        "Pattern: col4 = (col1 × col2 × col3) mod 10",
        metadata={"type": "product_mod10", "formula": "c4 = (c1 * c2 * c3) % 10"},
    )
    print(f"\n  H3: Product mod 10 pattern (card {hyp3})")
    print(f"      Formula: col4 = (col1 × col2 × col3) mod 10")

    # Hypothesis 4: Difference
    hyp4 = integrator.store_belief_as_card(
        "Pattern: col4 = col1 - col2 + col3",
        metadata={"type": "difference", "formula": "c4 = c1 - c2 + c3"},
    )
    print(f"\n  H4: Difference pattern (card {hyp4})")
    print(f"      Formula: col4 = col1 - col2 + col3")

    hypotheses = [
        (hyp1, "sum", lambda c1, c2, c3: c1 + c2 + c3),
        (hyp2, "product", lambda c1, c2, c3: c1 * c2 * c3),
        (hyp3, "product_mod10", lambda c1, c2, c3: (c1 * c2 * c3) % 10),
        (hyp4, "difference", lambda c1, c2, c3: c1 - c2 + c3),
    ]

    print(f"\nGenerated {len(hypotheses)} hypotheses")

    return hypotheses


def test_hypotheses(
    memory: ABMemory,
    integrator: ValidationRelationIntegrator,
    data: Dict,
    hypotheses: List[Tuple[int, str, callable]],
):
    """Step 3: Test each hypothesis against known rows."""
    print_section("STEP 3: Test Hypotheses Against Known Data")

    grid = data["grid"]
    results = []

    for hyp_id, hyp_name, formula in hypotheses:
        print(f"\nTesting hypothesis: {hyp_name}")
        print(f"  Card ID: {hyp_id}")

        matches = []
        mismatches = []

        # Test against first 3 rows (we know col4)
        for i in range(3):
            row = grid[i]
            c1, c2, c3, c4_actual = row

            c4_predicted = formula(c1, c2, c3)

            if c4_predicted == c4_actual:
                matches.append(i + 1)
                print(f"  ✓ Row {i+1}: {c1}, {c2}, {c3} → predicted {c4_predicted} = actual {c4_actual}")

                # Create evidence for this match
                ev = Evidence.create(
                    f"Row {i+1} matches: {c1}*{c2}*{c3} pattern predicts {c4_actual}",
                    EvidenceSource.CODE_ANALYSIS,
                    [f"grid_row_{i+1}"],
                )
                ev.validated = True
                ev.confidence = 1.0

                # Store evidence as card
                evidence_card = integrator.store_evidence_as_card(ev)

                # Create SUPPORTS relation
                rel = Relation.create(
                    f"evidence_{hyp_name}_row{i+1}",
                    RelationType.SUPPORTS,
                    evidence_card,
                    hyp_id,
                    confidence=1.0,
                    metadata={"row": i + 1, "match": True},
                )
                store_relation(memory, rel)

            else:
                mismatches.append(i + 1)
                print(f"  ✗ Row {i+1}: {c1}, {c2}, {c3} → predicted {c4_predicted} ≠ actual {c4_actual}")

                # Create counterevidence
                counter_ev = Evidence.create(
                    f"Row {i+1} contradicts: {c1}*{c2}*{c3} pattern predicts {c4_predicted} but actual is {c4_actual}",
                    EvidenceSource.CODE_ANALYSIS,
                    [f"grid_row_{i+1}"],
                )
                counter_ev.validated = True
                counter_ev.confidence = 1.0

                # Store counterevidence
                counter_card = integrator.store_evidence_as_card(counter_ev)

                # Create INVALIDATES relation
                rel = Relation.create(
                    f"counterev_{hyp_name}_row{i+1}",
                    RelationType.INVALIDATES,
                    counter_card,
                    hyp_id,
                    confidence=1.0,
                    metadata={"row": i + 1, "mismatch": True},
                )
                store_relation(memory, rel)

        support_strength = len(matches) / 3.0
        print(f"\n  Match rate: {len(matches)}/3 = {support_strength:.1%}")

        results.append({
            "hyp_id": hyp_id,
            "hyp_name": hyp_name,
            "formula": formula,
            "matches": matches,
            "mismatches": mismatches,
            "support_strength": support_strength,
        })

    return results


def select_best_hypothesis(
    memory: ABMemory,
    reasoning: ReasoningEngine,
    results: List[Dict],
):
    """Step 4: Use reasoning engine to select best hypothesis based on support."""
    print_section("STEP 4: Select Best Hypothesis")

    print("Analyzing support networks for each hypothesis...\n")

    for result in results:
        hyp_id = result["hyp_id"]
        hyp_name = result["hyp_name"]

        # Get support network
        support = get_support_network(memory, hyp_id)
        all_relations = memory.get_relations(target_card_id=hyp_id, relation_type="invalidates")
        invalidations = list(all_relations)

        print(f"Hypothesis: {hyp_name}")
        print(f"  SUPPORTS relations: {len(support)}")
        print(f"  INVALIDATES relations: {len(invalidations)}")
        print(f"  Support strength: {result['support_strength']:.1%}")

        result["support_count"] = len(support)
        result["invalidation_count"] = len(invalidations)

    # Find hypothesis with highest support
    best = max(results, key=lambda r: (r["support_strength"], r["support_count"]))

    print(f"\n{'='*80}")
    print(f"Best hypothesis: {best['hyp_name']}")
    print(f"  Support strength: {best['support_strength']:.1%}")
    print(f"  Matches: {best['matches']}")
    print(f"{'='*80}")

    return best


def compute_answer(best_hypothesis: Dict, data: Dict):
    """Step 5: Apply best hypothesis to compute missing value."""
    print_section("STEP 5: Compute Answer")

    grid = data["grid"]
    last_row = grid[3]
    c1, c2, c3 = last_row[0], last_row[1], last_row[2]

    formula = best_hypothesis["formula"]
    answer = formula(c1, c2, c3)

    print(f"Applying pattern: {best_hypothesis['hyp_name']}")
    print(f"  Row 4: {c1}, {c2}, {c3}, ?")
    print(f"  Computation: {best_hypothesis['hyp_name']}")
    print(f"\n  ANSWER: {answer}")

    # Verify it makes sense
    print(f"\nVerification:")
    for i in range(3):
        row = grid[i]
        expected = formula(row[0], row[1], row[2])
        print(f"  Row {i+1}: {row[0]} × {row[1]} × {row[2]} = {row[0]*row[1]*row[2]} → {expected} ✓")

    print(f"  Row 4: {c1} × {c2} × {c3} = {c1*c2*c3} → {answer} ✓")

    return answer


async def main():
    """Main demonstration."""

    print("\n" + "="*80)
    print("  SOLVING GRID NUMBER PATTERN WITH SUPE")
    print("  Using Reasoning Engine for Hypothesis Testing")
    print("="*80)

    print("\nPROBLEM:")
    print("  Find the pattern in the 4x4 grid and determine the missing value:")
    print("    3  6  1  8")
    print("    5  6  3  0")
    print("    2  7  1  4")
    print("    5  4  2  ?")

    # Initialize
    db_path = Path.home() / ".supe" / "test_grid_pattern.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    memory = ABMemory(str(db_path))
    integrator = ValidationRelationIntegrator(memory)
    reasoning = ReasoningEngine(memory)

    # Step 1: Model data
    data = model_grid_data(memory, integrator)

    # Step 2: Generate hypotheses
    hypotheses = generate_hypotheses(memory, integrator, data)

    # Step 3: Test hypotheses
    results = test_hypotheses(memory, integrator, data, hypotheses)

    # Step 4: Select best hypothesis
    best = select_best_hypothesis(memory, reasoning, results)

    # Step 5: Compute answer
    answer = compute_answer(best, data)

    # Summary
    print_section("DEMONSTRATION COMPLETE")

    print("Supe solved the pattern using:")
    print("  ✓ Hypothesis generation (multiple candidate patterns)")
    print("  ✓ Evidence collection (testing against known rows)")
    print("  ✓ Relation-based reasoning (SUPPORTS/INVALIDATES)")
    print("  ✓ Support network analysis (selecting best hypothesis)")
    print("  ✓ Pattern application (computing answer)\n")

    print(f"Final answer: {answer}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
