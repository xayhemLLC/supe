#!/usr/bin/env python3
"""Test plan generation with different goal types.

Usage:
    export ANTHROPIC_API_KEY="your-key"
    python scripts/test_plan_generation.py

Or test a single goal:
    python scripts/test_plan_generation.py "add user authentication"
"""

import json
import sys
import os

# Test goals covering different types of tasks
TEST_GOALS = [
    # Feature implementation
    "add rate limiting to API endpoints",
    "implement user authentication with JWT",
    "add dark mode toggle to the UI",

    # Bug fixes
    "fix the memory leak in the connection pool",
    "fix race condition in async task queue",

    # Refactoring
    "refactor the database layer to use async/await",
    "split the monolithic User class into smaller components",

    # Infrastructure
    "add CI/CD pipeline with GitHub Actions",
    "containerize the application with Docker",

    # Testing
    "add integration tests for the payment flow",
    "increase test coverage to 80%",
]


def test_plan_generation(goal: str, verbose: bool = True) -> dict:
    """Generate a plan for a goal and return the result."""
    try:
        from tascer import generate_plan
    except ImportError:
        print("Error: Install anthropic first: pip install anthropic")
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEYY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Set ANTHROPIC_API_KEYY or ANTHROPIC_API_KEY environment variable")
        sys.exit(1)
    os.environ["ANTHROPIC_API_KEY"] = api_key  # Set for the SDK

    print(f"\n{'='*60}")
    print(f"Goal: {goal}")
    print('='*60)

    try:
        result = generate_plan(
            goal=goal,
            max_tascs=8,
            require_approval=False,
            temperature=0.7,
        )

        plan_data = {
            "goal": goal,
            "title": result.plan.title,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "tascs": [
                {
                    "id": t.id,
                    "title": t.title,
                    "testing": t.testing_instructions,
                    "dependencies": t.dependencies,
                }
                for t in result.plan.tascs
            ],
        }

        if verbose:
            print(f"\nTitle: {result.plan.title}")
            print(f"Confidence: {result.confidence:.0%}")
            print(f"Reasoning: {result.reasoning}")
            print(f"\nTasks ({len(result.plan.tascs)}):")
            for i, tasc in enumerate(result.plan.tascs, 1):
                deps = f" [after: {', '.join(tasc.dependencies)}]" if tasc.dependencies else ""
                print(f"  {i}. {tasc.title}{deps}")
                if tasc.testing_instructions:
                    print(f"     Test: {tasc.testing_instructions[:60]}...")

        return plan_data

    except Exception as e:
        print(f"Error: {e}")
        return {"goal": goal, "error": str(e)}


def main():
    if len(sys.argv) > 1:
        # Single goal from command line
        goal = " ".join(sys.argv[1:])
        result = test_plan_generation(goal)
        print(f"\n{json.dumps(result, indent=2)}")
    else:
        # Run all test goals
        results = []
        for goal in TEST_GOALS:
            result = test_plan_generation(goal)
            results.append(result)

        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print('='*60)

        for r in results:
            if "error" in r:
                print(f"❌ {r['goal'][:40]}: {r['error'][:30]}")
            else:
                print(f"✅ {r['goal'][:40]}: {len(r['tascs'])} tasks, {r['confidence']:.0%} confidence")

        # Save full results
        output_path = ".supe/plan_test_results.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nFull results saved to: {output_path}")


if __name__ == "__main__":
    main()
