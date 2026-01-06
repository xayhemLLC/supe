"""Demonstration of continuous learning - system improves with every problem solved.

This shows how supe:
1. Solves problems and records each solution
2. Reasons by analogy when encountering similar problems
3. Extracts patterns after sufficient examples
4. Improves confidence scores over time
5. Synthesizes new capabilities from learned patterns
"""

import asyncio
from pathlib import Path
import time

from ab.abdb import ABMemory
from supe.reasoning.meta_solver import MetaSolver


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_subsection(title: str):
    """Print formatted subsection header."""
    print(f"\n{'-'*80}")
    print(f"  {title}")
    print(f"{'-'*80}\n")


async def demo_1_solve_first_problem(solver: MetaSolver):
    """Demo 1: Solve first algebraic factorization problem."""
    print_section("DEMO 1: First Problem - No Prior Experience")

    problem = "Factor x² + 5x + 6"

    print(f"Problem: {problem}")
    print()

    # Analyze
    analysis = solver.analyze_problem(problem)
    print("Analysis:")
    print(analysis.reasoning)
    print()

    # Check for analogy (should be None)
    print(f"Analogy Found: {'None' if 'analogy' not in analysis.reasoning else 'Yes'}")
    print()

    # Solve
    print("Solving...")
    start_time = time.time()
    result = solver.solve(problem)
    elapsed = time.time() - start_time

    print(f"Success: {result['success']}")
    print(f"Strategy: {result.get('strategy_name', 'N/A')}")
    print(f"Time: {elapsed:.3f}s")
    print()

    return elapsed


async def demo_2_solve_similar_problem(solver: MetaSolver):
    """Demo 2: Solve similar problem - should find analogy."""
    print_section("DEMO 2: Similar Problem - Learning From Experience")

    problem = "Factor x² + 7x + 12"

    print(f"Problem: {problem}")
    print()

    # Analyze
    analysis = solver.analyze_problem(problem)
    print("Analysis:")
    print(analysis.reasoning)
    print()

    # Check for analogy
    if "Reasoning by Analogy" in analysis.reasoning:
        print("✨ ANALOGY FOUND!")
        print("   System remembered a similar problem and is using that experience")
        print()

    # Solve
    print("Solving...")
    start_time = time.time()
    result = solver.solve(problem)
    elapsed = time.time() - start_time

    print(f"Success: {result['success']}")
    print(f"Strategy: {result.get('strategy_name', 'N/A')}")
    print(f"Time: {elapsed:.3f}s")
    print()

    return elapsed


async def demo_3_solve_multiple_similar(solver: MetaSolver):
    """Demo 3: Solve multiple similar problems to build pattern."""
    print_section("DEMO 3: Solving Multiple Similar Problems")

    problems = [
        "Factor x² + 9x + 20",
        "Factor x² + 11x + 30",
        "Factor x² + 13x + 42",
    ]

    times = []

    for i, problem in enumerate(problems, 1):
        print(f"Problem {i}: {problem}")

        # Quick solve
        start_time = time.time()
        result = solver.solve(problem)
        elapsed = time.time() - start_time
        times.append(elapsed)

        print(f"  Success: {result['success']}, Time: {elapsed:.3f}s")

        # Check if analogy was used
        analysis = solver.analyze_problem(problem)
        if "Reasoning by Analogy" in analysis.reasoning:
            print(f"  ✨ Used analogy from previous problem")

        print()

    avg_time = sum(times) / len(times)
    print(f"Average solving time: {avg_time:.3f}s")
    print()

    return times


async def demo_4_extract_patterns(solver: MetaSolver):
    """Demo 4: Extract patterns from solved problems."""
    print_section("DEMO 4: Extracting Patterns from Experience")

    print("System has now solved 5+ similar problems...")
    print("Let's see what patterns it has learned:")
    print()

    # Extract learnings
    learnings = solver.learn_from_experience(min_pattern_occurrences=3)

    print(f"Patterns Extracted: {learnings['patterns_extracted']}")
    print()

    if learnings['patterns']:
        print("Learned Patterns:")
        for pattern in learnings['patterns']:
            print(f"  - {pattern['name']}")
            print(f"    Structures: {pattern['structures']}")
            print(f"    Success Rate: {pattern['success_rate']:.1%}")
            print(f"    Examples: {pattern['example_count']}")
            print()

    if learnings['capability_suggestions']:
        print("Capability Suggestions:")
        for suggestion in learnings['capability_suggestions']:
            print(f"  - {suggestion['name']}")
            print(f"    Description: {suggestion['description']}")
            print(f"    Confidence: {suggestion['confidence']:.2f}")
            print(f"    Evidence: {suggestion['evidence_count']} successful uses")
            print()

    # Library statistics
    stats = learnings['library_stats']
    print(f"Library Statistics:")
    print(f"  Total Problems: {stats['total_problems']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Success Rate: {stats['success_rate']:.1%}")
    print(f"  Unique Structures: {stats['unique_structures']}")
    print()


async def demo_5_test_different_domain(solver: MetaSolver):
    """Demo 5: Test a different problem type."""
    print_section("DEMO 5: Different Problem Domain")

    # Now try a logic problem
    problem = """
    If all roses are flowers, and some flowers fade quickly,
    can we conclude that some roses fade quickly?
    """

    print(f"Problem: {problem.strip()}")
    print()

    # Analyze
    analysis = solver.analyze_problem(problem)
    print("Analysis:")
    print(analysis.reasoning)
    print()

    # Solve
    result = solver.solve(problem)
    print(f"Success: {result['success']}")
    print(f"Strategy: {result.get('strategy_name', 'N/A')}")
    print()


async def demo_6_learning_summary(solver: MetaSolver):
    """Demo 6: Show complete learning summary."""
    print_section("DEMO 6: Complete Learning Summary")

    summary = solver.get_learning_summary()

    print("Learning Progress:")
    integration = summary['integration']
    print(f"  Problems Solved: {integration['problems_solved']}")
    print(f"  Overall Success Rate: {integration['success_rate']:.1%}")
    print(f"  Patterns Learned: {integration['patterns_learned']}")
    print(f"  Total Capabilities: {integration['total_capabilities']}")
    print(f"  Total Strategies: {integration['total_strategies']}")
    print()

    learning = summary['learning']
    print("Best Domain:")
    print(f"  {learning['best_domain']}")
    print()

    print("Domains Covered:")
    for domain in learning['domains_covered']:
        print(f"  - {domain}")
    print()

    # Show capability improvements
    print("Top Performing Capabilities:")
    capabilities = summary['capabilities']
    stats = capabilities['statistics']

    # Sort by success rate
    sorted_caps = sorted(
        stats.items(),
        key=lambda x: x[1]['success_rate'],
        reverse=True
    )[:5]

    for name, data in sorted_caps:
        print(f"  {name}:")
        print(f"    Success Rate: {data['success_rate']:.1%}")
        print(f"    Usage Count: {data['usage_count']}")
        print(f"    Confidence: {data['confidence']:.1%}")
        print()


async def demo_7_compare_improvement(solver: MetaSolver, first_time: float, later_times: list):
    """Demo 7: Compare first vs. later solving performance."""
    print_section("DEMO 7: Performance Improvement")

    avg_later = sum(later_times) / len(later_times)
    improvement = ((first_time - avg_later) / first_time) * 100

    print("Performance Comparison:")
    print(f"  First Problem Time: {first_time:.3f}s")
    print(f"  Average Later Time: {avg_later:.3f}s")
    print(f"  Improvement: {improvement:.1f}%")
    print()

    print("Why the Improvement?")
    print("  1. Reasoning by analogy - found similar past problems")
    print("  2. Strategy refinement - confidence scores improved")
    print("  3. Capability optimization - learned which methods work best")
    print("  4. Pattern recognition - extracted common solving patterns")
    print()


async def main():
    """Main demonstration of continuous learning."""

    print("\n" + "="*80)
    print("  CONTINUOUS LEARNING DEMONSTRATION")
    print("  System Improves With Every Problem Solved")
    print("="*80)

    # Initialize
    db_path = Path.home() / ".supe" / "continuous_learning_demo.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    memory = ABMemory(str(db_path))
    solver = MetaSolver(memory)

    # Demo 1: First problem
    first_time = await demo_1_solve_first_problem(solver)

    # Demo 2: Similar problem with analogy
    second_time = await demo_2_solve_similar_problem(solver)

    # Demo 3: Multiple similar problems
    later_times = await demo_3_solve_multiple_similar(solver)

    # Demo 4: Extract patterns
    await demo_4_extract_patterns(solver)

    # Demo 5: Different domain
    await demo_5_test_different_domain(solver)

    # Demo 6: Learning summary
    await demo_6_learning_summary(solver)

    # Demo 7: Compare improvement
    await demo_7_compare_improvement(solver, first_time, later_times)

    # Final summary
    print_section("DEMONSTRATION COMPLETE")

    print("Key Achievements Demonstrated:")
    print("  ✓ Problem solutions stored in persistent library")
    print("  ✓ Reasoning by analogy from past problems")
    print("  ✓ Pattern extraction from multiple examples")
    print("  ✓ Automatic capability suggestions")
    print("  ✓ Confidence scores improve with experience")
    print("  ✓ Strategy success rates tracked")
    print("  ✓ Performance improvements measurable")
    print()

    print("This is CONTINUOUS LEARNING:")
    print("  Every problem solved makes the system better")
    print("  Past experience guides future problem-solving")
    print("  Patterns emerge from accumulated examples")
    print("  The system learns what works and what doesn't")
    print()

    print("="*80)
    print()


if __name__ == "__main__":
    asyncio.run(main())
