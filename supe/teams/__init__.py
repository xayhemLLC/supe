"""Supe Teams - Pre-configured autonomous development team styles.

Experiment with different team compositions and working styles:

    from supe.teams import StartupTeam, EnterpriseTeam, ResearchTeam

    # Quick iteration, minimal ceremony
    team = StartupTeam(name="mvp-squad")

    # Full governance, audit trails
    team = EnterpriseTeam(name="platform-team")

    # Exploration-focused, hypothesis-driven
    team = ResearchTeam(name="ml-research")

All teams integrate with supe's validation gates and proof-of-work.
"""

from .base import TeamConfig, TeamStyle, AgentRole
from .styles import (
    StartupTeam,
    EnterpriseTeam,
    ResearchTeam,
    SoloDevTeam,
    PairTeam,
    MobTeam,
    OpenSourceTeam,
    AgencyTeam,
)
from .agents import (
    ValidatedAgent,
    LeadAgent,
    DeveloperAgent,
    ReviewerAgent,
    QAAgent,
    ArchitectAgent,
    ResearcherAgent,
)

__all__ = [
    # Config
    "TeamConfig",
    "TeamStyle",
    "AgentRole",
    # Team Styles
    "StartupTeam",
    "EnterpriseTeam",
    "ResearchTeam",
    "SoloDevTeam",
    "PairTeam",
    "MobTeam",
    "OpenSourceTeam",
    "AgencyTeam",
    # Agents
    "ValidatedAgent",
    "LeadAgent",
    "DeveloperAgent",
    "ReviewerAgent",
    "QAAgent",
    "ArchitectAgent",
    "ResearcherAgent",
]
