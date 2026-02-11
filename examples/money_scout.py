#!/usr/bin/env python3
"""Money Scout: Find low-lift money-making opportunities.

This agent scans for opportunities and ranks them by:
- Potential revenue
- Effort required (lower is better)
- Competition level
- Your existing skills/assets

Usage:
    python examples/money_scout.py "I know Python and have a small Twitter following"
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


# =============================================================================
# OPPORTUNITY MODEL
# =============================================================================

class EffortLevel(Enum):
    """How much work to get started."""
    WEEKEND = "weekend"      # < 2 days
    WEEK = "week"            # 2-7 days
    MONTH = "month"          # 1-4 weeks
    QUARTER = "quarter"      # 1-3 months


class RevenueType(Enum):
    """How money comes in."""
    ONE_TIME = "one_time"           # Single sale
    RECURRING = "recurring"         # Subscription
    PASSIVE = "passive"             # After initial work
    ACTIVE = "active"               # Ongoing effort


@dataclass
class Opportunity:
    """A money-making opportunity."""

    id: str
    title: str
    description: str

    # Scoring dimensions
    effort: EffortLevel = EffortLevel.WEEK
    revenue_type: RevenueType = RevenueType.ONE_TIME
    revenue_potential_monthly: int = 0  # USD estimate
    competition: int = 5                # 1=none, 10=saturated
    skill_match: int = 5                # 1=new skills, 10=perfect fit

    # Metadata
    source: str = ""                    # Where we found it
    evidence: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)

    def score(self) -> float:
        """Calculate opportunity score. Higher = better."""
        # Effort multiplier (weekend=4x, quarter=0.5x)
        effort_mult = {
            EffortLevel.WEEKEND: 4.0,
            EffortLevel.WEEK: 2.0,
            EffortLevel.MONTH: 1.0,
            EffortLevel.QUARTER: 0.5,
        }[self.effort]

        # Revenue type multiplier
        rev_mult = {
            RevenueType.PASSIVE: 2.0,
            RevenueType.RECURRING: 1.5,
            RevenueType.ONE_TIME: 1.0,
            RevenueType.ACTIVE: 0.8,
        }[self.revenue_type]

        # Competition penalty (high competition = lower score)
        comp_mult = (11 - self.competition) / 10  # 1.0 to 0.1

        # Skill match bonus
        skill_mult = self.skill_match / 5  # 0.2 to 2.0

        # Base score from revenue potential
        base = min(self.revenue_potential_monthly / 100, 100)

        return base * effort_mult * rev_mult * comp_mult * skill_mult

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "effort": self.effort.value,
            "revenue_type": self.revenue_type.value,
            "revenue_potential_monthly": self.revenue_potential_monthly,
            "competition": self.competition,
            "skill_match": self.skill_match,
            "score": round(self.score(), 2),
            "source": self.source,
        }


# =============================================================================
# OPPORTUNITY SOURCES
# =============================================================================

# These are patterns the scout looks for
OPPORTUNITY_PATTERNS = [
    # Digital products
    {
        "category": "Digital Products",
        "patterns": [
            "notion template for {niche}",
            "figma ui kit for {niche}",
            "chatgpt prompt pack for {niche}",
            "obsidian plugin for {niche}",
            "vscode extension for {niche}",
        ],
        "effort": EffortLevel.WEEKEND,
        "revenue_type": RevenueType.PASSIVE,
    },
    # Micro-SaaS
    {
        "category": "Micro-SaaS",
        "patterns": [
            "{niche} dashboard",
            "{niche} automation tool",
            "{niche} analytics",
            "api for {niche}",
        ],
        "effort": EffortLevel.MONTH,
        "revenue_type": RevenueType.RECURRING,
    },
    # Content/Audience
    {
        "category": "Content",
        "patterns": [
            "{niche} newsletter",
            "{niche} youtube tutorial",
            "{niche} course",
            "{niche} ebook",
        ],
        "effort": EffortLevel.WEEK,
        "revenue_type": RevenueType.PASSIVE,
    },
    # Services
    {
        "category": "Services",
        "patterns": [
            "{niche} consulting",
            "{niche} audit service",
            "done-for-you {niche}",
        ],
        "effort": EffortLevel.WEEKEND,
        "revenue_type": RevenueType.ACTIVE,
    },
]


# =============================================================================
# SCOUT AGENT
# =============================================================================

class MoneyScout:
    """Agent that discovers money-making opportunities."""

    def __init__(self, profile: str = ""):
        """
        Args:
            profile: Your skills/assets, e.g. "Python dev, 5k Twitter followers"
        """
        self.profile = profile
        self.opportunities: List[Opportunity] = []
        self._supe_agent = None
        self._opp_counter = 0

    def _get_supe(self):
        """Get supe agent for validation and memory."""
        if self._supe_agent is None:
            try:
                from ab import ABMemory
                from tascer.sdk_wrapper import (
                    TascerAgent,
                    TascerAgentOptions,
                    RecallConfig,
                )

                db_path = os.path.expanduser("~/.supe/memory.sqlite")
                os.makedirs(os.path.dirname(db_path), exist_ok=True)

                self._supe_agent = TascerAgent(
                    tascer_options=TascerAgentOptions(
                        recall_config=RecallConfig(
                            enabled=True,
                            auto_context=True,
                            auto_context_limit=5,
                        ),
                        generate_proofs=True,
                        store_to_ab=True,
                    ),
                    ab_memory=ABMemory(db_path),
                )
            except ImportError:
                pass
        return self._supe_agent

    def _next_id(self) -> str:
        self._opp_counter += 1
        return f"opp_{self._opp_counter:03d}"

    def _extract_skills(self) -> List[str]:
        """Extract skills from profile."""
        profile_lower = self.profile.lower()

        skills = []
        skill_keywords = [
            "python", "javascript", "typescript", "react", "node",
            "design", "figma", "ui", "ux", "writing", "marketing",
            "sales", "data", "ml", "ai", "devops", "mobile", "ios",
            "android", "video", "audio", "music", "photo",
        ]

        for skill in skill_keywords:
            if skill in profile_lower:
                skills.append(skill)

        return skills

    def _extract_assets(self) -> Dict[str, Any]:
        """Extract assets from profile."""
        profile_lower = self.profile.lower()

        assets = {}

        # Twitter following
        if "twitter" in profile_lower or "x.com" in profile_lower:
            import re
            match = re.search(r'(\d+)k?\s*(twitter|x\.com|followers)', profile_lower)
            if match:
                followers = int(match.group(1))
                if 'k' in profile_lower[match.start():match.end()]:
                    followers *= 1000
                assets["twitter_followers"] = followers

        # Newsletter
        if "newsletter" in profile_lower or "substack" in profile_lower:
            assets["has_newsletter"] = True

        # Existing product
        if "saas" in profile_lower or "product" in profile_lower:
            assets["has_product"] = True

        return assets

    async def discover_from_niches(
        self,
        niches: List[str],
        use_web_search: bool = False,
    ) -> List[Opportunity]:
        """Discover opportunities in specific niches.

        Args:
            niches: List of niches like ["developer tools", "productivity"]
            use_web_search: Whether to search web for validation
        """
        skills = self._extract_skills()
        assets = self._extract_assets()

        for niche in niches:
            for pattern_group in OPPORTUNITY_PATTERNS:
                for pattern in pattern_group["patterns"]:
                    title = pattern.format(niche=niche)

                    # Calculate skill match
                    skill_match = 5
                    if "python" in skills and "api" in title.lower():
                        skill_match = 9
                    elif "python" in skills and ("tool" in title or "automation" in title):
                        skill_match = 8
                    elif "design" in skills and ("template" in title or "kit" in title):
                        skill_match = 9
                    elif "writing" in skills and ("newsletter" in title or "ebook" in title):
                        skill_match = 9

                    # Boost if has audience
                    if assets.get("twitter_followers", 0) > 1000:
                        skill_match = min(10, skill_match + 1)

                    opp = Opportunity(
                        id=self._next_id(),
                        title=title.title(),
                        description=f"{pattern_group['category']}: {title}",
                        effort=pattern_group["effort"],
                        revenue_type=pattern_group["revenue_type"],
                        revenue_potential_monthly=self._estimate_revenue(
                            pattern_group["category"],
                            assets,
                        ),
                        competition=6,  # Default medium
                        skill_match=skill_match,
                        source="pattern_match",
                    )

                    self.opportunities.append(opp)

        return self.opportunities

    def _estimate_revenue(self, category: str, assets: Dict) -> int:
        """Estimate monthly revenue potential."""
        base = {
            "Digital Products": 500,
            "Micro-SaaS": 2000,
            "Content": 1000,
            "Services": 3000,
        }.get(category, 500)

        # Audience multiplier
        followers = assets.get("twitter_followers", 0)
        if followers > 10000:
            base *= 2
        elif followers > 1000:
            base *= 1.5

        return int(base)

    async def discover_from_problems(
        self,
        problems: List[str],
    ) -> List[Opportunity]:
        """Discover opportunities from problems people have.

        Args:
            problems: List like ["developers waste time on boilerplate"]
        """
        try:
            import anthropic
        except ImportError:
            # Fallback without API
            for problem in problems:
                opp = Opportunity(
                    id=self._next_id(),
                    title=f"Solve: {problem[:50]}",
                    description=problem,
                    source="problem",
                )
                self.opportunities.append(opp)
            return self.opportunities

        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEYY")
        if not api_key:
            return self.opportunities

        client = anthropic.Anthropic(api_key=api_key)

        skills = self._extract_skills()

        prompt = f"""Given these problems and my skills, suggest money-making solutions.

Problems:
{chr(10).join(f'- {p}' for p in problems)}

My skills: {', '.join(skills) if skills else 'general'}

For each opportunity, provide:
- title: Short name
- description: What to build/sell
- effort: weekend/week/month/quarter
- revenue_type: one_time/recurring/passive/active
- revenue_potential_monthly: USD estimate
- competition: 1-10 (10=saturated)

Output as JSON array. Only output JSON, nothing else."""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )

            opps = json.loads(response.content[0].text)

            for o in opps:
                opp = Opportunity(
                    id=self._next_id(),
                    title=o.get("title", "Untitled"),
                    description=o.get("description", ""),
                    effort=EffortLevel(o.get("effort", "week")),
                    revenue_type=RevenueType(o.get("revenue_type", "one_time")),
                    revenue_potential_monthly=o.get("revenue_potential_monthly", 500),
                    competition=o.get("competition", 5),
                    skill_match=8,  # High since based on our skills
                    source="problem_solving",
                )
                self.opportunities.append(opp)

        except Exception as e:
            print(f"API error: {e}")

        return self.opportunities

    async def discover_from_trends(self) -> List[Opportunity]:
        """Discover opportunities from current trends.

        Looks at what's hot and finds gaps.
        """
        # Trend-based opportunity templates
        trends = [
            ("AI/LLM tools", [
                "GPT wrapper for {specific_use}",
                "AI agent for {task}",
                "Prompt library for {profession}",
            ]),
            ("Creator economy", [
                "Analytics for {platform}",
                "Scheduling tool for {platform}",
                "Monetization for {content_type}",
            ]),
            ("Remote work", [
                "Async standup tool",
                "Time zone coordinator",
                "Virtual office for {team_size}",
            ]),
        ]

        skills = self._extract_skills()

        for trend_name, templates in trends:
            for template in templates:
                # Pick a specific instance
                specifics = {
                    "{specific_use}": "code review",
                    "{task}": "email triage",
                    "{profession}": "developers",
                    "{platform}": "Twitter",
                    "{content_type}": "newsletters",
                    "{team_size}": "small teams",
                }

                title = template
                for key, value in specifics.items():
                    title = title.replace(key, value)

                skill_match = 5
                if "python" in skills and ("tool" in title.lower() or "api" in title.lower()):
                    skill_match = 8

                opp = Opportunity(
                    id=self._next_id(),
                    title=title.title(),
                    description=f"{trend_name}: {title}",
                    effort=EffortLevel.MONTH,
                    revenue_type=RevenueType.RECURRING,
                    revenue_potential_monthly=1500,
                    competition=7,  # Trends are competitive
                    skill_match=skill_match,
                    source="trend",
                )
                self.opportunities.append(opp)

        return self.opportunities

    async def validate_with_search(self, opp: Opportunity) -> Opportunity:
        """Validate opportunity with web search for competition/demand signals.

        Looks for:
        - Existing competitors (raises competition score)
        - People asking for solutions (demand signal)
        - Pricing data (refines revenue estimate)
        """
        try:
            import anthropic
        except ImportError:
            return opp

        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEYY")
        if not api_key:
            return opp

        # In a real implementation, you'd use web search here
        # For now, we'll use Claude to estimate based on knowledge

        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Analyze this business opportunity:

Title: {opp.title}
Description: {opp.description}

Estimate:
1. competition: 1-10 (10=saturated market)
2. demand: 1-10 (10=huge unmet demand)
3. realistic_monthly_revenue: USD for solo founder
4. existing_players: list 2-3 competitors if any

Output as JSON only."""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            data = json.loads(response.content[0].text)

            opp.competition = data.get("competition", opp.competition)
            opp.revenue_potential_monthly = data.get(
                "realistic_monthly_revenue",
                opp.revenue_potential_monthly
            )
            opp.evidence.append(f"Competitors: {data.get('existing_players', [])}")

        except Exception:
            pass

        return opp

    def rank(self, top_n: int = 10) -> List[Opportunity]:
        """Rank opportunities by score."""
        ranked = sorted(self.opportunities, key=lambda o: o.score(), reverse=True)
        return ranked[:top_n]

    def report(self, top_n: int = 10) -> str:
        """Generate a report of top opportunities."""
        ranked = self.rank(top_n)

        lines = [
            "=" * 60,
            "MONEY SCOUT REPORT",
            "=" * 60,
            f"Profile: {self.profile}",
            f"Skills: {', '.join(self._extract_skills())}",
            f"Opportunities analyzed: {len(self.opportunities)}",
            "",
            "TOP OPPORTUNITIES (by score):",
            "-" * 60,
        ]

        for i, opp in enumerate(ranked, 1):
            lines.append(f"\n{i}. {opp.title}")
            lines.append(f"   Score: {opp.score():.1f}")
            lines.append(f"   Effort: {opp.effort.value} | Revenue: ${opp.revenue_potential_monthly}/mo ({opp.revenue_type.value})")
            lines.append(f"   Competition: {opp.competition}/10 | Skill match: {opp.skill_match}/10")
            lines.append(f"   Source: {opp.source}")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    def to_json(self) -> str:
        """Export opportunities as JSON."""
        ranked = self.rank(len(self.opportunities))
        return json.dumps([o.to_dict() for o in ranked], indent=2)


# =============================================================================
# MAIN
# =============================================================================

async def main():
    import sys

    # Get profile from args or use default
    if len(sys.argv) > 1:
        profile = " ".join(sys.argv[1:])
    else:
        profile = "Python developer with basic design skills"

    print(f"\nScanning opportunities for: {profile}\n")

    scout = MoneyScout(profile=profile)

    # Discover from multiple sources
    await scout.discover_from_niches([
        "developer tools",
        "productivity",
        "AI/ML",
    ])

    await scout.discover_from_trends()

    await scout.discover_from_problems([
        "developers waste time writing boilerplate",
        "non-technical founders can't validate ideas quickly",
        "content creators struggle with consistency",
    ])

    # Print report
    print(scout.report(top_n=10))

    # Save to file
    output_path = ".supe/money_scout_report.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(scout.to_json())
    print(f"\nFull report saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
