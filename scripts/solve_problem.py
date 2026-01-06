#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI for running the Supe reasoning pipeline.

Usage:
    python scripts/solve_problem.py "Find f(g(2)) where f(x)=x²+1, g(x)=x-2"
    python scripts/solve_problem.py "What is 2+2?" --options "A=3,B=4,C=5,D=6"
    python scripts/solve_problem.py problem.txt --file
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ab.abdb import ABMemory
from supe.reasoning.subagents import ReasoningPipeline


def parse_options(options_str: str) -> dict:
    """Parse options string like 'A=1,B=5,C=-1,D=0' into dict."""
    if not options_str:
        return {}

    options = {}
    for pair in options_str.split(","):
        if "=" in pair:
            key, value = pair.split("=", 1)
            key = key.strip()
            value = value.strip()
            # Try to convert to number
            try:
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass  # Keep as string
            options[key] = value
    return options


async def solve(
    problem_text: str,
    options: dict = None,
    given: list = None,
    find: str = None,
    verbose: bool = False,
) -> None:
    """Run the reasoning pipeline on a problem."""

    # Initialize memory (in-memory for CLI usage)
    memory = ABMemory(":memory:")

    # Create pipeline
    pipeline = ReasoningPipeline(memory)

    if verbose:
        print("=" * 60)
        print("SUPE REASONING PIPELINE")
        print("=" * 60)
        print(f"\nProblem: {problem_text[:100]}...")
        if options:
            print(f"Options: {options}")
        print("\nRunning pipeline...\n")

    # Run pipeline
    result = await pipeline.run(
        problem_text=problem_text,
        options=options,
        given=given,
        find=find,
    )

    # Print results
    print(result.to_ascii())

    if verbose:
        print("\n" + "=" * 60)
        print("RAW DATA")
        print("=" * 60)
        import json
        print(json.dumps(result.to_dict(), indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(
        description="Solve problems using Supe reasoning pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Find f(g(2)) where f(x)=x²+1, g(x)=x-2"
  %(prog)s "What is 2+2?" --options "A=3,B=4,C=5,D=6"
  %(prog)s problem.txt --file
  %(prog)s "Solve: x² - 5x + 6 = 0" --given "x is real" --find "x"
        """
    )

    parser.add_argument(
        "problem",
        help="Problem text or path to file (with --file)"
    )

    parser.add_argument(
        "--file", "-f",
        action="store_true",
        help="Read problem from file"
    )

    parser.add_argument(
        "--options", "-o",
        help="Answer options (e.g., 'A=1,B=5,C=-1,D=0')"
    )

    parser.add_argument(
        "--given", "-g",
        action="append",
        help="Given information (can be specified multiple times)"
    )

    parser.add_argument(
        "--find",
        help="What to find/solve for"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output including raw JSON"
    )

    args = parser.parse_args()

    # Get problem text
    if args.file:
        problem_path = Path(args.problem)
        if not problem_path.exists():
            print(f"Error: File not found: {args.problem}", file=sys.stderr)
            sys.exit(1)
        problem_text = problem_path.read_text()
    else:
        problem_text = args.problem

    # Parse options
    options = parse_options(args.options) if args.options else None

    # Run solver
    asyncio.run(solve(
        problem_text=problem_text,
        options=options,
        given=args.given,
        find=args.find,
        verbose=args.verbose,
    ))


if __name__ == "__main__":
    main()
