"""Agent Abilities - Tascers that create TascPlans.

Abilities are higher-level patterns that:
1. Plan work by creating TascPlans
2. Execute work using plugins
3. Store results in AB Memory (dual-track)

Each ability is a Tascer - an entity that creates structured,
validated work plans.
"""

from .base import Ability
from .web_scraper import WebScraperAbility

__all__ = [
    "Ability",
    "WebScraperAbility",
]
