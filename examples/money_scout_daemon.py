#!/usr/bin/env python3
"""Money Scout Daemon: Continuous opportunity discovery.

Runs 24/7, scanning multiple sources for opportunities:
- Product Hunt (trending products, market gaps)
- Hacker News (Show HN, Ask HN, pain points)
- Reddit (problems in target subreddits)
- GitHub (trending repos, high-star projects)
- Twitter/X (people asking for tools, "I'd pay for")
- Indie Hackers (revenue milestones, validated markets)
- Gumroad (what's actually selling, price points)
- Google Trends (rising topics, early opportunities)

Stores findings to AB Memory for recall across sessions.
Sends desktop notifications for high-score opportunities.

Usage:
    # Run in foreground
    python examples/money_scout_daemon.py

    # Run in background with nohup
    nohup python examples/money_scout_daemon.py > ~/.supe/scout.log 2>&1 &

    # Run with screen
    screen -S scout python examples/money_scout_daemon.py

    # Check findings anytime
    supe memory search "opportunity"
"""

import asyncio
import json
import os
import subprocess
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import urllib.request
import urllib.parse


# =============================================================================
# CONFIG
# =============================================================================

@dataclass
class ScoutConfig:
    """Configuration for the scout daemon."""

    # Your profile
    profile: str = "Python developer"
    skills: List[str] = field(default_factory=lambda: ["python"])
    interests: List[str] = field(default_factory=lambda: ["developer tools", "AI", "automation"])

    # Scanning schedule (seconds between scans)
    scan_interval: int = 3600  # 1 hour

    # Sources to scan
    scan_product_hunt: bool = True
    scan_hacker_news: bool = True
    scan_reddit: bool = True
    scan_github: bool = True
    scan_twitter: bool = True
    scan_indie_hackers: bool = True
    scan_gumroad: bool = True
    scan_google_trends: bool = True

    # Reddit subreddits to monitor
    subreddits: List[str] = field(default_factory=lambda: [
        "SideProject",
        "startups",
        "Entrepreneur",
        "SaaS",
        "indiehackers",
    ])

    # Twitter/X search queries
    twitter_queries: List[str] = field(default_factory=lambda: [
        "need a tool for",
        "wish there was an app",
        "looking for software",
        "anyone built",
        "I'd pay for",
    ])

    # Indie Hackers categories
    ih_categories: List[str] = field(default_factory=lambda: [
        "product-feedback",
        "growth",
        "landing-page-feedback",
    ])

    # Thresholds
    min_score_to_notify: float = 50.0
    min_score_to_store: float = 20.0

    # Storage
    db_path: str = "~/.supe/memory.sqlite"
    findings_path: str = "~/.supe/scout_findings.json"


# =============================================================================
# OPPORTUNITY MODEL (same as before, extended)
# =============================================================================

class EffortLevel(Enum):
    WEEKEND = "weekend"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"


class RevenueType(Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    PASSIVE = "passive"
    ACTIVE = "active"


@dataclass
class Opportunity:
    id: str
    title: str
    description: str
    source: str
    source_url: str = ""

    effort: EffortLevel = EffortLevel.WEEK
    revenue_type: RevenueType = RevenueType.ONE_TIME
    revenue_potential_monthly: int = 500
    competition: int = 5
    skill_match: int = 5
    demand_signal: int = 5  # 1-10, evidence of people wanting this

    evidence: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)

    def score(self) -> float:
        effort_mult = {
            EffortLevel.WEEKEND: 4.0,
            EffortLevel.WEEK: 2.0,
            EffortLevel.MONTH: 1.0,
            EffortLevel.QUARTER: 0.5,
        }[self.effort]

        rev_mult = {
            RevenueType.PASSIVE: 2.0,
            RevenueType.RECURRING: 1.5,
            RevenueType.ONE_TIME: 1.0,
            RevenueType.ACTIVE: 0.8,
        }[self.revenue_type]

        comp_mult = (11 - self.competition) / 10
        skill_mult = self.skill_match / 5
        demand_mult = self.demand_signal / 5  # Boost high-demand opportunities

        base = min(self.revenue_potential_monthly / 100, 100)
        return base * effort_mult * rev_mult * comp_mult * skill_mult * demand_mult

    def fingerprint(self) -> str:
        """Unique identifier for deduplication."""
        content = f"{self.title.lower()}:{self.source}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "source_url": self.source_url,
            "effort": self.effort.value,
            "revenue_type": self.revenue_type.value,
            "revenue_potential_monthly": self.revenue_potential_monthly,
            "competition": self.competition,
            "skill_match": self.skill_match,
            "demand_signal": self.demand_signal,
            "score": round(self.score(), 2),
            "discovered_at": self.discovered_at.isoformat(),
            "evidence": self.evidence,
        }


# =============================================================================
# DISCOVERY SOURCES
# =============================================================================

class DiscoverySource:
    """Base class for discovery sources."""

    def __init__(self, config: ScoutConfig):
        self.config = config
        self._opp_counter = 0

    def _next_id(self, prefix: str) -> str:
        self._opp_counter += 1
        return f"{prefix}_{self._opp_counter:04d}"

    def _skill_match(self, text: str) -> int:
        """Calculate skill match from text."""
        text_lower = text.lower()
        matches = sum(1 for skill in self.config.skills if skill in text_lower)
        interest_matches = sum(1 for i in self.config.interests if i.lower() in text_lower)
        return min(10, 3 + matches * 2 + interest_matches)

    async def discover(self) -> List[Opportunity]:
        raise NotImplementedError


class ProductHuntSource(DiscoverySource):
    """Discover opportunities from Product Hunt."""

    async def discover(self) -> List[Opportunity]:
        """Scan Product Hunt for trending products and gaps."""
        opportunities = []

        # Use the unofficial API endpoint for trending
        try:
            url = "https://www.producthunt.com/frontend/graphql"
            # Simplified: just fetch the homepage HTML and extract patterns
            # In production, you'd use proper GraphQL queries

            # For now, use common PH patterns to generate ideas
            ph_patterns = [
                ("AI writing assistant for {niche}", "AI tools trending on PH"),
                ("No-code {tool} builder", "No-code tools popular"),
                ("{niche} analytics dashboard", "Analytics SaaS trending"),
                ("Chrome extension for {task}", "Browser extensions popular"),
            ]

            niches = ["developers", "marketers", "founders", "designers"]
            tasks = ["productivity", "research", "automation", "scheduling"]

            for pattern, evidence in ph_patterns:
                for niche in niches:
                    for task in tasks:
                        title = pattern.format(niche=niche, tool=task, task=task)

                        opp = Opportunity(
                            id=self._next_id("ph"),
                            title=title,
                            description=f"Inspired by Product Hunt trends: {evidence}",
                            source="product_hunt",
                            source_url="https://www.producthunt.com",
                            effort=EffortLevel.MONTH,
                            revenue_type=RevenueType.RECURRING,
                            revenue_potential_monthly=1500,
                            competition=7,  # PH is competitive
                            skill_match=self._skill_match(title),
                            demand_signal=7,  # Validated by PH launches
                            evidence=[evidence],
                        )

                        if opp.score() > self.config.min_score_to_store:
                            opportunities.append(opp)
                            if len(opportunities) >= 10:
                                return opportunities

        except Exception as e:
            print(f"  ProductHunt error: {e}")

        return opportunities


class HackerNewsSource(DiscoverySource):
    """Discover opportunities from Hacker News discussions."""

    async def discover(self) -> List[Opportunity]:
        """Scan HN for pain points and tool requests."""
        opportunities = []

        try:
            # Fetch top stories
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            with urllib.request.urlopen(url, timeout=10) as response:
                story_ids = json.loads(response.read().decode())[:30]

            # Analyze stories for opportunities
            for story_id in story_ids[:10]:  # Limit API calls
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                try:
                    with urllib.request.urlopen(story_url, timeout=5) as response:
                        story = json.loads(response.read().decode())

                    title = story.get("title", "")
                    story_type = story.get("type", "")

                    # Look for "Show HN" or "Ask HN" patterns
                    if "Show HN" in title:
                        # Someone built something - look for gaps
                        opp = Opportunity(
                            id=self._next_id("hn"),
                            title=f"Improve on: {title.replace('Show HN:', '').strip()[:50]}",
                            description=f"HN Show: {title}. Look for feature gaps or niche versions.",
                            source="hacker_news",
                            source_url=f"https://news.ycombinator.com/item?id={story_id}",
                            effort=EffortLevel.MONTH,
                            revenue_type=RevenueType.RECURRING,
                            revenue_potential_monthly=2000,
                            competition=6,
                            skill_match=self._skill_match(title),
                            demand_signal=8,  # Validated by HN interest
                            evidence=[f"HN story: {story.get('score', 0)} points"],
                        )
                        opportunities.append(opp)

                    elif "Ask HN" in title and any(kw in title.lower() for kw in
                            ["tool", "app", "how do you", "what do you use", "recommend"]):
                        # Someone asking for solutions - direct demand
                        opp = Opportunity(
                            id=self._next_id("hn"),
                            title=f"Solve: {title.replace('Ask HN:', '').strip()[:50]}",
                            description=f"Direct demand from HN: {title}",
                            source="hacker_news",
                            source_url=f"https://news.ycombinator.com/item?id={story_id}",
                            effort=EffortLevel.WEEK,
                            revenue_type=RevenueType.ONE_TIME,
                            revenue_potential_monthly=1000,
                            competition=4,  # Less competition for niche asks
                            skill_match=self._skill_match(title),
                            demand_signal=9,  # Direct ask = high demand
                            evidence=[f"Direct ask on HN"],
                        )
                        opportunities.append(opp)

                except Exception:
                    continue

        except Exception as e:
            print(f"  HackerNews error: {e}")

        return opportunities


class RedditSource(DiscoverySource):
    """Discover opportunities from Reddit discussions."""

    async def discover(self) -> List[Opportunity]:
        """Scan subreddits for problems and requests."""
        opportunities = []

        for subreddit in self.config.subreddits[:3]:  # Limit subreddits
            try:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
                req = urllib.request.Request(url, headers={"User-Agent": "MoneyScout/1.0"})

                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())

                posts = data.get("data", {}).get("children", [])

                for post in posts:
                    post_data = post.get("data", {})
                    title = post_data.get("title", "")
                    selftext = post_data.get("selftext", "")[:500]
                    score = post_data.get("score", 0)
                    permalink = post_data.get("permalink", "")

                    # Look for problem/request patterns
                    problem_keywords = [
                        "looking for", "need help", "any tools", "how do you",
                        "struggling with", "wish there was", "anyone know",
                        "is there a", "what do you use for",
                    ]

                    is_problem = any(kw in title.lower() or kw in selftext.lower()
                                    for kw in problem_keywords)

                    if is_problem and score > 5:
                        opp = Opportunity(
                            id=self._next_id("reddit"),
                            title=f"r/{subreddit}: {title[:50]}",
                            description=f"{title}\n\n{selftext[:200]}",
                            source=f"reddit/{subreddit}",
                            source_url=f"https://reddit.com{permalink}",
                            effort=EffortLevel.WEEK,
                            revenue_type=RevenueType.ONE_TIME,
                            revenue_potential_monthly=800,
                            competition=5,
                            skill_match=self._skill_match(title + selftext),
                            demand_signal=min(10, 5 + score // 20),  # Higher score = more demand
                            evidence=[f"Reddit score: {score}", f"Subreddit: r/{subreddit}"],
                        )
                        opportunities.append(opp)

            except Exception as e:
                print(f"  Reddit r/{subreddit} error: {e}")

        return opportunities


class GitHubSource(DiscoverySource):
    """Discover opportunities from GitHub trends."""

    async def discover(self) -> List[Opportunity]:
        """Scan GitHub for trending repos and issues."""
        opportunities = []

        try:
            # Search for repos with "paid" or "sponsor" or high stars in relevant topics
            topics = ["cli", "developer-tools", "automation", "productivity"]

            for topic in topics[:2]:  # Limit API calls
                url = f"https://api.github.com/search/repositories?q=topic:{topic}&sort=stars&order=desc&per_page=5"
                req = urllib.request.Request(url, headers={"User-Agent": "MoneyScout/1.0"})

                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode())

                    repos = data.get("items", [])

                    for repo in repos:
                        name = repo.get("name", "")
                        description = repo.get("description", "") or ""
                        stars = repo.get("stargazers_count", 0)
                        html_url = repo.get("html_url", "")

                        # High-star repos = validated demand
                        if stars > 1000:
                            opp = Opportunity(
                                id=self._next_id("gh"),
                                title=f"Build on: {name} ({stars:,} stars)",
                                description=f"Popular repo: {description}. Consider: SaaS version, better UX, niche variant.",
                                source="github",
                                source_url=html_url,
                                effort=EffortLevel.MONTH,
                                revenue_type=RevenueType.RECURRING,
                                revenue_potential_monthly=2000,
                                competition=6,
                                skill_match=self._skill_match(name + description),
                                demand_signal=min(10, 5 + stars // 2000),
                                evidence=[f"GitHub stars: {stars:,}", f"Topic: {topic}"],
                            )
                            opportunities.append(opp)

                except Exception:
                    continue

        except Exception as e:
            print(f"  GitHub error: {e}")

        return opportunities


class TwitterSource(DiscoverySource):
    """Discover opportunities from Twitter/X.

    Searches for people expressing needs, frustrations, or willingness to pay.
    Uses nitter instances for public access (no API key needed).
    """

    async def discover(self) -> List[Opportunity]:
        """Scan Twitter for opportunity signals."""
        opportunities = []

        # Nitter instances for scraping (no API needed)
        nitter_instances = [
            "nitter.net",
            "nitter.privacydev.net",
            "nitter.poast.org",
        ]

        # High-signal search queries
        queries = self.config.twitter_queries + [
            '"shut up and take my money"',
            '"would pay for"',
            '"why is there no"',
            '"someone should build"',
            '"frustrated with"',
        ]

        for query in queries[:5]:  # Limit queries
            for instance in nitter_instances[:1]:  # Try first instance
                try:
                    encoded_query = urllib.parse.quote(query)
                    url = f"https://{instance}/search?f=tweets&q={encoded_query}"

                    req = urllib.request.Request(url, headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                    })

                    # Note: This may not work on all instances
                    # In production, use official Twitter API
                    with urllib.request.urlopen(req, timeout=10) as response:
                        html = response.read().decode()

                    # Simple pattern matching for tweet content
                    # In production, use proper HTML parsing
                    import re
                    tweets = re.findall(r'class="tweet-content[^"]*"[^>]*>([^<]+)', html)

                    for tweet_text in tweets[:5]:
                        if len(tweet_text) > 20:
                            opp = Opportunity(
                                id=self._next_id("tw"),
                                title=f"Twitter: {tweet_text[:50]}...",
                                description=f"Twitter signal: {tweet_text[:200]}",
                                source="twitter",
                                source_url=f"https://twitter.com/search?q={encoded_query}",
                                effort=EffortLevel.WEEK,
                                revenue_type=RevenueType.ONE_TIME,
                                revenue_potential_monthly=1000,
                                competition=5,
                                skill_match=self._skill_match(tweet_text),
                                demand_signal=8,  # Direct expression of need
                                evidence=[f"Query: {query}"],
                            )
                            opportunities.append(opp)
                    break  # Success, don't try other instances

                except Exception:
                    continue  # Try next instance

        # Fallback: Generate from common Twitter patterns if scraping fails
        if not opportunities:
            twitter_patterns = [
                ("Twitter API wrapper with better DX", "Developers complain about Twitter API"),
                ("Social media scheduler for small teams", "Creators need affordable tools"),
                ("Thread unroller as a service", "Popular tweets often ask for this"),
                ("Twitter analytics for indie hackers", "IH community active on Twitter"),
            ]

            for title, evidence in twitter_patterns:
                opp = Opportunity(
                    id=self._next_id("tw"),
                    title=title,
                    description=f"Common Twitter request: {title}",
                    source="twitter_pattern",
                    source_url="https://twitter.com",
                    effort=EffortLevel.WEEK,
                    revenue_type=RevenueType.RECURRING,
                    revenue_potential_monthly=1500,
                    competition=6,
                    skill_match=self._skill_match(title),
                    demand_signal=7,
                    evidence=[evidence],
                )
                opportunities.append(opp)

        return opportunities


class IndieHackersSource(DiscoverySource):
    """Discover opportunities from Indie Hackers.

    Mines:
    - Product discussions for gaps
    - Revenue milestones for proven markets
    - "Roast my landing page" for improvement ideas
    """

    async def discover(self) -> List[Opportunity]:
        """Scan Indie Hackers for opportunities."""
        opportunities = []

        try:
            # IH doesn't have a public API, but we can scrape the JSON feed
            url = "https://www.indiehackers.com/feed"
            req = urllib.request.Request(url, headers={
                "User-Agent": "MoneyScout/1.0",
                "Accept": "application/json",
            })

            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    # Try to parse as JSON, fall back to patterns
                    data = json.loads(response.read().decode())
                    posts = data.get("posts", [])

                    for post in posts[:10]:
                        title = post.get("title", "")
                        body = post.get("body", "")[:300]

                        # Look for milestone posts (validated markets)
                        if any(kw in title.lower() for kw in ["$", "mrr", "arr", "revenue", "milestone"]):
                            opp = Opportunity(
                                id=self._next_id("ih"),
                                title=f"Market validated: {title[:50]}",
                                description=f"IH milestone: {title}. This market has paying customers.",
                                source="indie_hackers",
                                source_url="https://www.indiehackers.com",
                                effort=EffortLevel.MONTH,
                                revenue_type=RevenueType.RECURRING,
                                revenue_potential_monthly=2000,
                                competition=6,
                                skill_match=self._skill_match(title + body),
                                demand_signal=9,  # Proven revenue
                                evidence=["IH milestone post"],
                            )
                            opportunities.append(opp)

                        # Look for feedback requests (gaps to fill)
                        elif any(kw in title.lower() for kw in ["feedback", "roast", "review", "thoughts"]):
                            opp = Opportunity(
                                id=self._next_id("ih"),
                                title=f"Improve on: {title[:50]}",
                                description=f"IH asks for feedback: {body[:200]}. Build a better version.",
                                source="indie_hackers",
                                source_url="https://www.indiehackers.com",
                                effort=EffortLevel.MONTH,
                                revenue_type=RevenueType.RECURRING,
                                revenue_potential_monthly=1500,
                                competition=5,
                                skill_match=self._skill_match(title + body),
                                demand_signal=6,
                                evidence=["IH feedback request"],
                            )
                            opportunities.append(opp)

            except Exception:
                pass

        except Exception as e:
            print(f"  IndieHackers API error: {e}")

        # Fallback patterns from common IH discussions
        if not opportunities:
            ih_patterns = [
                ("Micro-SaaS for freelancers", "Freelancer tools popular on IH", 2000),
                ("Boilerplate/starter kit", "Devs buy to save time", 1500),
                ("Chrome extension monetization", "Common IH success story", 1000),
                ("Newsletter to paid community", "Many IH founders do this", 800),
                ("API as a service", "Devs pay for convenience", 2500),
                ("No-code tool for specific niche", "No-code is hot on IH", 1800),
            ]

            for title, evidence, revenue in ih_patterns:
                opp = Opportunity(
                    id=self._next_id("ih"),
                    title=title,
                    description=f"Common IH pattern: {title}",
                    source="indie_hackers_pattern",
                    source_url="https://www.indiehackers.com",
                    effort=EffortLevel.MONTH,
                    revenue_type=RevenueType.RECURRING,
                    revenue_potential_monthly=revenue,
                    competition=6,
                    skill_match=self._skill_match(title),
                    demand_signal=8,
                    evidence=[evidence],
                )
                opportunities.append(opp)

        return opportunities


class GumroadSource(DiscoverySource):
    """Discover opportunities from Gumroad trending products.

    See what's actually selling to validate demand.
    """

    async def discover(self) -> List[Opportunity]:
        """Scan Gumroad for trending products."""
        opportunities = []

        # Gumroad discover page categories
        categories = [
            "software",
            "design",
            "writing",
            "education",
            "business",
        ]

        try:
            for category in categories[:3]:
                url = f"https://gumroad.com/discover?category={category}"
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                })

                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        html = response.read().decode()

                    # Simple pattern to extract product data
                    # In production, use proper HTML parsing
                    import re

                    # Look for product cards with prices
                    products = re.findall(
                        r'class="product-card[^"]*"[^>]*>.*?<h3[^>]*>([^<]+)</h3>.*?\$(\d+)',
                        html, re.DOTALL
                    )

                    for name, price in products[:5]:
                        price_int = int(price)
                        if price_int >= 20:  # Focus on higher-priced items
                            opp = Opportunity(
                                id=self._next_id("gr"),
                                title=f"Create: {name[:50]} (sells for ${price})",
                                description=f"Gumroad product selling at ${price}. Create your version.",
                                source="gumroad",
                                source_url=f"https://gumroad.com/discover?category={category}",
                                effort=EffortLevel.WEEK,
                                revenue_type=RevenueType.PASSIVE,
                                revenue_potential_monthly=price_int * 20,  # Estimate 20 sales/mo
                                competition=5,
                                skill_match=self._skill_match(name),
                                demand_signal=9,  # Already selling
                                evidence=[f"Selling on Gumroad for ${price}", f"Category: {category}"],
                            )
                            opportunities.append(opp)

                except Exception:
                    continue

        except Exception as e:
            print(f"  Gumroad error: {e}")

        # Fallback: Known Gumroad success patterns
        if not opportunities:
            gumroad_patterns = [
                ("Notion template pack", "Templates sell well", 500, EffortLevel.WEEKEND),
                ("Icon pack for developers", "Design assets passive income", 800, EffortLevel.WEEK),
                ("Landing page templates", "Startup founders buy these", 1000, EffortLevel.WEEK),
                ("Email templates for SaaS", "B2B templates high value", 600, EffortLevel.WEEKEND),
                ("Code snippets collection", "Devs pay for quality code", 400, EffortLevel.WEEKEND),
            ]

            for title, evidence, revenue, effort in gumroad_patterns:
                opp = Opportunity(
                    id=self._next_id("gr"),
                    title=title,
                    description=f"Proven Gumroad category: {title}",
                    source="gumroad_pattern",
                    source_url="https://gumroad.com",
                    effort=effort,
                    revenue_type=RevenueType.PASSIVE,
                    revenue_potential_monthly=revenue,
                    competition=6,
                    skill_match=self._skill_match(title),
                    demand_signal=8,
                    evidence=[evidence],
                )
                opportunities.append(opp)

        return opportunities


class GoogleTrendsSource(DiscoverySource):
    """Discover opportunities from Google Trends.

    Find rising topics that need tools/solutions.
    """

    async def discover(self) -> List[Opportunity]:
        """Scan Google Trends for rising topics."""
        opportunities = []

        try:
            # Google Trends daily trends RSS
            url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
            req = urllib.request.Request(url, headers={
                "User-Agent": "MoneyScout/1.0"
            })

            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    xml = response.read().decode()

                # Simple XML parsing
                import re
                titles = re.findall(r'<title>([^<]+)</title>', xml)

                # Skip first (feed title) and process trends
                for trend in titles[1:10]:
                    # Filter for business/tech relevant trends
                    tech_keywords = [
                        "ai", "app", "software", "tool", "startup",
                        "crypto", "nft", "web", "cloud", "api",
                    ]

                    if any(kw in trend.lower() for kw in tech_keywords):
                        opp = Opportunity(
                            id=self._next_id("gt"),
                            title=f"Trending: Build for '{trend}'",
                            description=f"'{trend}' is trending on Google. Build tools, content, or services around it.",
                            source="google_trends",
                            source_url=f"https://trends.google.com/trends/explore?q={urllib.parse.quote(trend)}",
                            effort=EffortLevel.WEEK,
                            revenue_type=RevenueType.ONE_TIME,
                            revenue_potential_monthly=1000,
                            competition=7,  # Trends attract competition
                            skill_match=self._skill_match(trend),
                            demand_signal=9,  # Currently trending
                            evidence=["Google Trends daily trending"],
                        )
                        opportunities.append(opp)

            except Exception:
                pass

        except Exception as e:
            print(f"  Google Trends error: {e}")

        # Rising tech topics that often need tools
        if not opportunities:
            rising_topics = [
                ("AI agent frameworks", "Agents are the new apps"),
                ("Local-first software", "Privacy-focused tools rising"),
                ("Vertical SaaS", "Niche beats horizontal"),
                ("Creator monetization", "Creator economy growing"),
                ("API-first products", "Developers are buyers"),
            ]

            for topic, evidence in rising_topics:
                opp = Opportunity(
                    id=self._next_id("gt"),
                    title=f"Rising: {topic}",
                    description=f"Emerging category: {topic}. Early mover advantage.",
                    source="google_trends_pattern",
                    source_url="https://trends.google.com",
                    effort=EffortLevel.MONTH,
                    revenue_type=RevenueType.RECURRING,
                    revenue_potential_monthly=2000,
                    competition=4,  # Early = less competition
                    skill_match=self._skill_match(topic),
                    demand_signal=8,
                    evidence=[evidence],
                )
                opportunities.append(opp)

        return opportunities


# =============================================================================
# SCOUT DAEMON
# =============================================================================

class MoneyScoutDaemon:
    """Continuous opportunity discovery daemon."""

    def __init__(self, config: ScoutConfig = None):
        self.config = config or ScoutConfig()
        self.sources: List[DiscoverySource] = []
        self.seen_fingerprints: Set[str] = set()
        self.all_opportunities: List[Opportunity] = []
        self._running = False
        self._scan_count = 0
        self._supe_agent = None

        # Initialize sources
        if self.config.scan_product_hunt:
            self.sources.append(ProductHuntSource(self.config))
        if self.config.scan_hacker_news:
            self.sources.append(HackerNewsSource(self.config))
        if self.config.scan_reddit:
            self.sources.append(RedditSource(self.config))
        if self.config.scan_github:
            self.sources.append(GitHubSource(self.config))
        if self.config.scan_twitter:
            self.sources.append(TwitterSource(self.config))
        if self.config.scan_indie_hackers:
            self.sources.append(IndieHackersSource(self.config))
        if self.config.scan_gumroad:
            self.sources.append(GumroadSource(self.config))
        if self.config.scan_google_trends:
            self.sources.append(GoogleTrendsSource(self.config))

        # Load existing fingerprints
        self._load_seen()

    def _get_supe(self):
        """Get supe agent for memory storage."""
        if self._supe_agent is None:
            try:
                from ab import ABMemory
                from tascer.sdk_wrapper import TascerAgent, TascerAgentOptions, RecallConfig

                db_path = os.path.expanduser(self.config.db_path)
                os.makedirs(os.path.dirname(db_path), exist_ok=True)

                self._supe_agent = TascerAgent(
                    tascer_options=TascerAgentOptions(
                        recall_config=RecallConfig(enabled=True, auto_context=True),
                        generate_proofs=True,
                        store_to_ab=True,
                    ),
                    ab_memory=ABMemory(db_path),
                )
            except ImportError:
                pass
        return self._supe_agent

    def _load_seen(self):
        """Load previously seen opportunities."""
        path = os.path.expanduser(self.config.findings_path)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                    for opp in data.get("opportunities", []):
                        # Recreate fingerprint
                        fp = hashlib.md5(f"{opp['title'].lower()}:{opp['source']}".encode()).hexdigest()[:12]
                        self.seen_fingerprints.add(fp)
            except Exception:
                pass

    def _save_findings(self):
        """Save findings to disk."""
        path = os.path.expanduser(self.config.findings_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        data = {
            "last_scan": datetime.now().isoformat(),
            "scan_count": self._scan_count,
            "total_opportunities": len(self.all_opportunities),
            "opportunities": [o.to_dict() for o in sorted(
                self.all_opportunities,
                key=lambda x: x.score(),
                reverse=True
            )[:100]],  # Keep top 100
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _notify(self, opp: Opportunity):
        """Send notification for high-score opportunity."""
        # macOS notification
        try:
            subprocess.run([
                "osascript", "-e",
                f'display notification "{opp.title[:50]}" with title "Money Scout" subtitle "Score: {opp.score():.0f}"'
            ], check=False, capture_output=True)
        except Exception:
            pass

        # Also print to console
        print(f"\n  🔔 HIGH SCORE: {opp.title}")
        print(f"     Score: {opp.score():.1f} | Source: {opp.source}")
        print(f"     URL: {opp.source_url}")

    def _store_to_memory(self, opp: Opportunity):
        """Store opportunity to AB Memory."""
        try:
            from ab import ABMemory
            db_path = os.path.expanduser(self.config.db_path)
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            ab = ABMemory(db_path)
            ab.store(
                label="opportunity",
                content={
                    "title": opp.title,
                    "score": opp.score(),
                    "source": opp.source,
                    "url": opp.source_url,
                    "effort": opp.effort.value,
                    "revenue": opp.revenue_potential_monthly,
                },
            )
        except Exception:
            pass

    async def scan_once(self) -> List[Opportunity]:
        """Run one scan cycle."""
        self._scan_count += 1
        new_opportunities = []

        print(f"\n{'='*60}")
        print(f"SCAN #{self._scan_count} - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}")

        for source in self.sources:
            source_name = source.__class__.__name__
            print(f"\n  Scanning {source_name}...")

            try:
                opps = await source.discover()

                for opp in opps:
                    fp = opp.fingerprint()

                    # Skip if already seen
                    if fp in self.seen_fingerprints:
                        continue

                    self.seen_fingerprints.add(fp)

                    # Check score threshold
                    if opp.score() >= self.config.min_score_to_store:
                        self.all_opportunities.append(opp)
                        new_opportunities.append(opp)
                        self._store_to_memory(opp)

                        print(f"    + {opp.title[:50]} (score: {opp.score():.1f})")

                        # Notify if high score
                        if opp.score() >= self.config.min_score_to_notify:
                            self._notify(opp)

                print(f"    Found {len(opps)} opportunities, {len([o for o in opps if o.fingerprint() not in self.seen_fingerprints])} new")

            except Exception as e:
                print(f"    Error: {e}")

        # Save after each scan
        self._save_findings()

        # Summary
        print(f"\n  Scan complete: {len(new_opportunities)} new opportunities")
        print(f"  Total tracked: {len(self.all_opportunities)}")

        return new_opportunities

    async def run_forever(self):
        """Run continuously."""
        self._running = True

        print(f"\n{'='*60}")
        print("MONEY SCOUT DAEMON STARTING")
        print(f"{'='*60}")
        print(f"Profile: {self.config.profile}")
        print(f"Skills: {', '.join(self.config.skills)}")
        print(f"Interests: {', '.join(self.config.interests)}")
        print(f"Scan interval: {self.config.scan_interval}s")
        print(f"Sources: {len(self.sources)}")
        print(f"Min score to notify: {self.config.min_score_to_notify}")
        print(f"\nFindings saved to: {self.config.findings_path}")
        print(f"Press Ctrl+C to stop\n")

        try:
            while self._running:
                await self.scan_once()

                # Wait for next scan
                print(f"\n  Next scan in {self.config.scan_interval}s...")
                await asyncio.sleep(self.config.scan_interval)

        except KeyboardInterrupt:
            print("\n\nShutting down...")

        finally:
            self._running = False
            self._save_findings()
            print(f"Final report saved to: {self.config.findings_path}")

    def stop(self):
        """Stop the daemon."""
        self._running = False

    def get_top_opportunities(self, n: int = 10) -> List[Opportunity]:
        """Get top N opportunities by score."""
        return sorted(self.all_opportunities, key=lambda o: o.score(), reverse=True)[:n]

    def report(self) -> str:
        """Generate text report."""
        top = self.get_top_opportunities(10)

        lines = [
            f"{'='*60}",
            "MONEY SCOUT REPORT",
            f"{'='*60}",
            f"Scans completed: {self._scan_count}",
            f"Opportunities tracked: {len(self.all_opportunities)}",
            "",
            "TOP 10 OPPORTUNITIES:",
            "-" * 60,
        ]

        for i, opp in enumerate(top, 1):
            lines.append(f"\n{i}. {opp.title}")
            lines.append(f"   Score: {opp.score():.1f} | {opp.source}")
            lines.append(f"   Effort: {opp.effort.value} | ${opp.revenue_potential_monthly}/mo")
            lines.append(f"   URL: {opp.source_url}")

        return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Money Scout Daemon")
    parser.add_argument("--profile", default="Python developer", help="Your skills profile")
    parser.add_argument("--interval", type=int, default=3600, help="Scan interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--report", action="store_true", help="Show report and exit")
    args = parser.parse_args()

    config = ScoutConfig(
        profile=args.profile,
        skills=["python"],  # Extracted from profile
        interests=["developer tools", "AI", "automation"],
        scan_interval=args.interval,
    )

    daemon = MoneyScoutDaemon(config)

    if args.report:
        daemon._load_seen()
        # Load existing opportunities
        path = os.path.expanduser(config.findings_path)
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
                for o in data.get("opportunities", []):
                    opp = Opportunity(
                        id=o["id"],
                        title=o["title"],
                        description=o.get("description", ""),
                        source=o["source"],
                        source_url=o.get("source_url", ""),
                        effort=EffortLevel(o.get("effort", "week")),
                        revenue_type=RevenueType(o.get("revenue_type", "one_time")),
                        revenue_potential_monthly=o.get("revenue_potential_monthly", 500),
                        competition=o.get("competition", 5),
                        skill_match=o.get("skill_match", 5),
                        demand_signal=o.get("demand_signal", 5),
                    )
                    daemon.all_opportunities.append(opp)
        print(daemon.report())
    elif args.once:
        await daemon.scan_once()
        print(daemon.report())
    else:
        await daemon.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
