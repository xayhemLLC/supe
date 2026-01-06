"""Debug algebraic factorization."""

import asyncio
from pathlib import Path

from ab.abdb import ABMemory
from supe.reasoning.meta_solver import MetaSolver


async def main():
    # Initialize
    db_path = Path.home() / ".supe" / "debug_factorization.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    memory = ABMemory(str(db_path))
    solver = MetaSolver(memory)

    problem = "Factor x² + 5x + 6"

    print("="*80)
    print(f"Problem: {problem}")
    print("="*80)

    # Analyze
    analysis = solver.analyze_problem(problem)
    print("\nAnalysis:")
    print(analysis.reasoning)

    if analysis.suggested_strategy:
        print(f"\nStrategy: {analysis.suggested_strategy.name}")
        print(f"Steps: {len(analysis.suggested_strategy.steps)}")
        print("\nStrategy steps:")
        for i, step in enumerate(analysis.suggested_strategy.steps):
            print(f"  Step {i+1}: {step}")

    # Solve
    print("\n" + "="*80)
    print("Solving...")
    print("="*80)

    result = solver.solve(problem)

    print(f"\nSuccess: {result['success']}")
    print(f"Strategy: {result.get('strategy_name')}")

    if 'error' in result:
        print(f"Error: {result['error']}")

    if 'steps_completed' in result:
        print(f"\nSteps completed: {len(result['steps_completed'])}")
        for i, step in enumerate(result['steps_completed']):
            print(f"\nStep {i+1}:")
            print(f"  Success: {step.get('success')}")
            print(f"  Action: {step.get('action')}")
            print(f"  Pattern: {step.get('pattern')}")
            if 'error' in step:
                print(f"  Error: {step['error']}")
            if 'result' in step:
                print(f"  Result: {step['result']}")


if __name__ == "__main__":
    asyncio.run(main())
