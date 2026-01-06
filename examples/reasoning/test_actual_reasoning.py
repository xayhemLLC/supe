"""Test the actual reasoning capability implementations."""

import asyncio
from pathlib import Path

from ab.abdb import ABMemory
from supe.reasoning.meta_solver import MetaSolver


async def test_algebraic_factorization():
    """Test algebraic factorization capability."""
    print("\n" + "="*80)
    print("  TEST 1: Algebraic Factorization")
    print("="*80 + "\n")

    # Initialize
    db_path = Path.home() / ".supe" / "test_reasoning.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    memory = ABMemory(str(db_path))
    solver = MetaSolver(memory)

    # Test problems
    problems = [
        ("Factor x² + 5x + 6", "(x+2)(x+3)"),
        ("Factor x² + 7x + 12", "(x+3)(x+4)"),
        ("Factor x² + 9x + 20", "(x+4)(x+5)"),
    ]

    for problem, expected in problems:
        print(f"Problem: {problem}")
        print(f"Expected: {expected}")

        # Solve
        result = solver.solve(problem)

        print(f"Success: {result['success']}")

        if result['success']:
            # Look for factorization in steps
            for step in result.get('steps_completed', []):
                if 'result' in step and 'factorization' in step['result']:
                    print(f"Found: {step['result']['factorization']}")

        print()

    # Check learning
    summary = solver.get_learning_summary()
    print(f"Problems solved: {summary['integration']['problems_solved']}")
    print(f"Success rate: {summary['integration']['success_rate']:.1%}")


async def test_pattern_matching():
    """Test pattern matching capability."""
    print("\n" + "="*80)
    print("  TEST 2: Pattern Matching")
    print("="*80 + "\n")

    from supe.reasoning.capabilities.pattern import PatternMatcher

    matcher = PatternMatcher()

    # Test numeric sequence
    sequence = [2, 4, 6, 8, 10]
    print(f"Sequence: {sequence}")

    result = matcher.execute("", {"data": sequence})

    if result['success']:
        print("Patterns detected:")
        for pattern in result['patterns']:
            print(f"  Type: {pattern['type']}")
            if 'next_value' in pattern:
                print(f"  Next value: {pattern['next_value']}")
            if 'formula' in pattern:
                print(f"  Formula: {pattern['formula']}")

    print()

    # Test grid pattern
    grid = [
        [3, 6, 1, 8],
        [2, 1, 4, 8],
        [5, 4, 2, 0],
    ]

    print("Grid:")
    for row in grid:
        print(f"  {row}")

    result = matcher.execute("", {"data": grid})

    if result['success']:
        print("\nPatterns detected:")
        for pattern in result['patterns']:
            print(f"  Type: {pattern['type']}")
            if 'formula' in pattern:
                print(f"  Formula: {pattern['formula']}")


async def test_hypothesis_testing():
    """Test hypothesis testing capability."""
    print("\n" + "="*80)
    print("  TEST 3: Hypothesis Testing")
    print("="*80 + "\n")

    from supe.reasoning.capabilities.hypothesis import Hypothesis, HypothesisTesting

    tester = HypothesisTesting()

    # Test data: grid from pattern problem
    grid = [
        [3, 6, 1, 8],
        [2, 1, 4, 8],
        [5, 4, 2, 0],
    ]

    # Generate hypotheses
    hypotheses = [
        Hypothesis(
            name="sum_pattern",
            description="First three values sum to fourth",
            test_function=lambda row: len(row) >= 4 and row[0] + row[1] + row[2] == row[3],
        ),
        Hypothesis(
            name="product_mod_10",
            description="First two multiply mod 10 to give third",
            test_function=lambda row: len(row) >= 3 and (row[0] * row[1]) % 10 == row[2],
        ),
    ]

    print("Testing hypotheses on grid:")
    for row in grid:
        print(f"  {row}")

    result = tester.execute("", {
        "hypotheses": hypotheses,
        "test_data": grid,
    })

    if result['success']:
        print("\nResults:")
        for hyp_result in result['all_results']:
            print(f"  {hyp_result['hypothesis']}:")
            print(f"    Supporting: {hyp_result['supporting']}")
            print(f"    Contradicting: {hyp_result['contradicting']}")
            print(f"    Confidence: {hyp_result['confidence']:.1%}")
            print(f"    Verdict: {hyp_result['verdict']}")

        print(f"\nBest hypothesis: {result['best_hypothesis']['hypothesis']}")
        print(f"  Confidence: {result['best_hypothesis']['confidence']:.1%}")


async def test_deductive_reasoning():
    """Test deductive reasoning capability."""
    print("\n" + "="*80)
    print("  TEST 4: Deductive Reasoning (Two Guards Puzzle)")
    print("="*80 + "\n")

    from supe.reasoning.capabilities.deductive import DeductiveReasoner

    reasoner = DeductiveReasoner()

    # Solve two guards puzzle
    result = reasoner.two_guards_puzzle({})

    print("Two Guards Puzzle Solution:")
    print(f"Question: {result['solution']['question']}")
    print(f"Strategy: {result['solution']['strategy']}")
    print("\nReasoning:")
    for step in result['solution']['reasoning']:
        print(f"  • {step}")

    print("\nProof:")
    for step in result['solution']['proof']:
        print(f"  {step}")


async def test_optimizer():
    """Test optimization capability."""
    print("\n" + "="*80)
    print("  TEST 5: Optimization")
    print("="*80 + "\n")

    from supe.reasoning.capabilities.optimizer import Optimizer

    opt = Optimizer()

    # Find minimum ab for factorization: 54x⁴ + 219x² + 105 = k(ax² + b)(cx² + d)
    # Try different factorizations
    candidates = []

    # Generate factor pairs for 54 and 105
    for a in range(1, 55):
        if 54 % a == 0:
            c = 54 // a
            for b in range(1, 106):
                if 105 % b == 0:
                    d = 105 // b
                    candidates.append((a, b, c, d))

    print(f"Testing {len(candidates)} candidate factorizations...")

    # Objective: minimize a*b
    def objective(candidate):
        a, b, c, d = candidate
        return a * b

    result = opt.find_minimum(candidates, objective)

    print(f"\nOptimal factorization found:")
    print(f"  (a, b, c, d) = {result.optimal_value}")
    print(f"  a * b = {result.optimal_score}")
    print(f"  Candidates evaluated: {result.candidates_evaluated}")


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("  TESTING ACTUAL REASONING CAPABILITIES")
    print("="*80)

    await test_algebraic_factorization()
    await test_pattern_matching()
    await test_hypothesis_testing()
    await test_deductive_reasoning()
    await test_optimizer()

    print("\n" + "="*80)
    print("  ALL TESTS COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
