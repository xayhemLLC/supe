"""Demonstration of adaptive meta-solver that extends its own capabilities.

This shows how supe can:
1. Analyze problems to determine what reasoning is needed
2. Check if it has the required capabilities
3. Synthesize new solving strategies
4. Learn from experience
5. Extend itself with new reasoning methods
"""

import asyncio
from pathlib import Path

from ab.abdb import ABMemory
from supe.reasoning.meta_solver import MetaSolver
from supe.reasoning.problem_types import ReasoningPattern, ProblemDomain


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def demo_1_analyze_known_problems(solver: MetaSolver):
    """Demo 1: Analyze problems the system knows how to solve."""
    print_section("DEMO 1: Analyzing Known Problem Types")

    problems = [
        "Find the pattern: 3, 6, 1, 8 in the first row, what's the missing number?",
        "Factor 54x⁴ + 219x² + 105 into (k)(ax² + b)(cx² + d)",
        "Two guards at two doors, one always lies, one tells truth. What question to ask?",
    ]

    for problem in problems:
        print(f"Problem: {problem[:70]}...")
        analysis = solver.analyze_problem(problem)

        print(f"\n{analysis.reasoning}")
        print(f"\nCan solve: {'✓ YES' if analysis.can_solve else '✗ NO'}")

        if analysis.missing_capabilities:
            print(f"Missing: {[p.value for p in analysis.missing_capabilities]}")

        print("\n" + "-"*80)


def demo_2_encounter_new_problem(solver: MetaSolver):
    """Demo 2: Encounter a problem requiring new reasoning."""
    print_section("DEMO 2: Encountering New Problem Type")

    # A problem requiring combinatorial reasoning (not yet implemented)
    problem = """
    How many ways can you arrange 5 people in a row if 2 specific people
    must sit next to each other?
    """

    print(f"Problem: {problem.strip()}")
    print()

    analysis = solver.analyze_problem(problem)
    print(analysis.reasoning)
    print()

    if analysis.missing_capabilities:
        print(f"🚨 MISSING CAPABILITIES:")
        for pattern in analysis.missing_capabilities:
            print(f"  - {pattern.value}")

    print(f"\nCan solve: {'✓ YES' if analysis.can_solve else '✗ NO'}")

    if not analysis.can_solve:
        print("\n💡 System needs to learn: combinatorial reasoning")

    return analysis


def demo_3_extend_capability(solver: MetaSolver, missing_pattern: ReasoningPattern):
    """Demo 3: Extend system with new capability."""
    print_section("DEMO 3: Extending System with New Capability")

    print(f"Learning new capability: {missing_pattern.value}")
    print()

    # Define the new capability
    def combinatorial_reasoner(n, r):
        """Simple combinatorial reasoning implementation."""
        import math
        return math.factorial(n) // (math.factorial(r) * math.factorial(n - r))

    # Extend the system
    solver.extend_capability(
        name="combinatorial_reasoner",
        pattern=missing_pattern,
        domains={ProblemDomain.COMBINATORICS, ProblemDomain.UNKNOWN},
        description="Count arrangements, combinations, and permutations",
        implementation=combinatorial_reasoner,
    )

    print("✓ New capability registered!")
    print()

    # Show updated capabilities
    summary = solver.get_capabilities_summary()
    print(f"Total capabilities: {summary['total_capabilities']}")
    print(f"New capability: combinatorial_reasoner")
    print(f"  Pattern: {missing_pattern.value}")
    print(f"  Domains: combinatorics, unknown")


def demo_4_solve_after_learning(solver: MetaSolver):
    """Demo 4: Solve problem after learning new capability."""
    print_section("DEMO 4: Solving After Learning")

    problem = "How many ways can you arrange 5 people in a row?"

    print(f"Problem: {problem}")
    print()

    analysis = solver.analyze_problem(problem)
    print(analysis.reasoning)
    print()

    print(f"Can solve: {'✓ YES' if analysis.can_solve else '✗ NO'}")

    if analysis.can_solve:
        print("\n✨ System can now solve this problem!")
        print("   (acquired the necessary reasoning capability)")


def demo_5_strategy_synthesis(solver: MetaSolver):
    """Demo 5: System synthesizes new strategy."""
    print_section("DEMO 5: Synthesizing New Solving Strategy")

    # A geometry problem that needs a new strategy
    problem = """
    In a circle with diameter 132, a chord AB has length √363.
    Find the ratio BC/BD where D is the foot of perpendicular from A.
    """

    print(f"Problem: {problem.strip()}")
    print()

    print("Analyzing problem...")
    analysis = solver.analyze_problem(problem)

    print(f"Domain: {analysis.signature.domain.value}")
    print(f"Required patterns: {[p.value for p in analysis.signature.required_patterns]}")
    print()

    if analysis.suggested_strategy:
        print(f"Strategy: {analysis.suggested_strategy.name}")
        print(f"Confidence: {analysis.suggested_strategy.confidence:.2f}")
        print(f"Steps: {len(analysis.suggested_strategy.steps)}")

        if analysis.suggested_strategy.name.startswith("synthesized_"):
            print("\n✨ This is a SYNTHESIZED strategy!")
            print("   System created it by combining available capabilities")
    else:
        print("No existing strategy found")


def demo_6_learning_from_experience(solver: MetaSolver):
    """Demo 6: System learns from solving experience."""
    print_section("DEMO 6: Learning From Experience")

    print("System tracks success/failure of strategies and capabilities")
    print()

    # Get initial statistics
    summary = solver.get_capabilities_summary()

    print("Capability Statistics:")
    stats = summary["statistics"]

    for name, data in list(stats.items())[:5]:  # Show first 5
        print(f"  {name}:")
        print(f"    Pattern: {data['pattern']}")
        print(f"    Usage: {data['usage_count']} times")
        print(f"    Success rate: {data['success_rate']:.1%}")
        print(f"    Confidence: {data['confidence']:.1%}")
        print()

    print("Strategy Statistics:")
    for name, data in summary["strategies"].items():
        print(f"  {name}:")
        print(f"    Steps: {data['steps']}")
        print(f"    Confidence: {data['confidence']:.2f}")
        print(f"    Success rate: {data['success_rate']:.1%}")
        print()


async def main():
    """Main demonstration of adaptive meta-solver."""

    print("\n" + "="*80)
    print("  ADAPTIVE META-SOLVER DEMONSTRATION")
    print("  Supe Extends Its Own Cognitive Capabilities")
    print("="*80)

    # Initialize
    db_path = Path.home() / ".supe" / "adaptive_solver_demo.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    memory = ABMemory(str(db_path))
    solver = MetaSolver(memory)

    # Demo 1: Analyze known problems
    demo_1_analyze_known_problems(solver)

    # Demo 2: Encounter new problem type
    analysis = demo_2_encounter_new_problem(solver)

    # Demo 3: Extend with new capability
    if analysis.missing_capabilities:
        missing = list(analysis.missing_capabilities)[0]
        demo_3_extend_capability(solver, missing)

        # Demo 4: Solve after learning
        demo_4_solve_after_learning(solver)

    # Demo 5: Strategy synthesis
    demo_5_strategy_synthesis(solver)

    # Demo 6: Learning from experience
    demo_6_learning_from_experience(solver)

    # Summary
    print_section("DEMONSTRATION COMPLETE")

    summary = solver.get_capabilities_summary()

    print("System State:")
    print(f"  Total Capabilities: {summary['total_capabilities']}")
    print(f"  Total Strategies: {len(summary['strategies'])}")
    print()

    print("Key Capabilities Demonstrated:")
    print("  ✓ Problem classification (identify what reasoning is needed)")
    print("  ✓ Capability checking (know what it can/can't do)")
    print("  ✓ Gap detection (identify missing reasoning patterns)")
    print("  ✓ Self-extension (learn new capabilities)")
    print("  ✓ Strategy synthesis (create new solving approaches)")
    print("  ✓ Learning from experience (improve over time)")
    print()

    print("This is META-COGNITION:")
    print("  The system reasons about its own reasoning")
    print("  It knows what it knows and what it doesn't know")
    print("  It can extend itself with new capabilities")
    print("  It learns which strategies work best")
    print()

    print("="*80)
    print()


if __name__ == "__main__":
    asyncio.run(main())
