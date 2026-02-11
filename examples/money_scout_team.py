#!/usr/bin/env python3
"""Money Scout Team: Autonomous opportunity discovery.

Uses ResearchTeam to:
1. Scout opportunities from multiple sources
2. Validate with market research
3. Rank by effort/reward ratio
4. Generate actionable report

Usage:
    python examples/money_scout_team.py
"""

import asyncio
import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supe.teams import ResearchTeam


async def main():
    # Your profile - customize this!
    profile = "Python developer, basic design skills, 5k Twitter followers"

    print(f"\n{'='*60}")
    print("MONEY SCOUT TEAM")
    print(f"{'='*60}")
    print(f"Profile: {profile}\n")

    # Create research team for opportunity discovery
    team = ResearchTeam(name="money-scout", researcher_count=2)

    # Auto-discover research questions from problems
    await team.discover_from_problem(
        "I want to make money on the side with minimal time investment. "
        f"My skills: {profile}"
    )

    # Add specific opportunity hypotheses
    team.add_research_question(
        "What low-code tools can I build in a weekend?",
        hypothesis="Weekend projects with existing skills have highest ROI",
        priority=1,
    )

    team.add_research_question(
        "What digital products sell well for developers?",
        hypothesis="Templates and toolkits have low effort, passive income",
        priority=2,
    )

    team.add_research_question(
        "What consulting services are underpriced?",
        hypothesis="Active income can bootstrap while building passive",
        priority=3,
    )

    # Run the research
    print(f"Research questions: {len(team.tasks)}")
    print("Running autonomous research...\n")

    await team.run(max_cycles=5)

    # Show results
    print(f"\n{'='*60}")
    print("RESEARCH FINDINGS")
    print(f"{'='*60}")

    for h in team.hypotheses:
        print(f"\nHypothesis: {h['hypothesis']}")
        print(f"Status: {h['status']}")

        # Find related findings
        related = [f for f in team.findings if f['task_id'] == h['task_id']]
        if related:
            for finding in related:
                print(f"  Finding: {finding['finding']}")

    # Quick action items
    print(f"\n{'='*60}")
    print("RECOMMENDED ACTIONS")
    print(f"{'='*60}")

    actions = [
        "1. Start with a weekend project (Notion template, CLI tool)",
        "2. Document the process → content for Twitter",
        "3. Offer consulting to validate demand",
        "4. Convert learnings into a paid course/guide",
    ]

    for action in actions:
        print(f"  {action}")

    print()


if __name__ == "__main__":
    asyncio.run(main())
