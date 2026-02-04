"""Pre-configured team styles for different development contexts.

Each style is optimized for specific scenarios:

| Style       | Best For                          | Agents | Ceremony  |
|-------------|-----------------------------------|--------|-----------|
| Startup     | MVPs, rapid iteration             | 2-3    | Minimal   |
| Enterprise  | Regulated, audit-heavy            | 5-8    | Full      |
| Research    | Exploration, hypothesis-driven    | 2-4    | Async     |
| Solo        | Individual dev with AI assist     | 1      | None      |
| Pair        | Driver/navigator pattern          | 2      | Continuous|
| Mob         | Whole team on one task            | 3-5    | Continuous|
| OpenSource  | Async, distributed contributors   | N/A    | PR-based  |
| Agency      | Client work, deliverable-focused  | 3-5    | Sprint    |
"""

import asyncio
from dataclasses import field
from typing import Dict, List, Optional, Any

from .base import (
    BaseTeam,
    TeamConfig,
    TeamStyle,
    AgentRole,
    CeremonyConfig,
    CeremonyType,
    ValidationConfig,
    TaskAssignment,
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


class StartupTeam(BaseTeam):
    """Fast-moving startup team. Minimal process, maximum velocity.

    Characteristics:
    - Small team (2-3 devs)
    - Minimal ceremonies (quick daily sync only)
    - Fast review cycles
    - Auto-merge enabled for passing PRs
    - Focus on shipping over perfection

    Example:
        team = StartupTeam(name="mvp-squad")
        team.add_task("Build landing page")
        team.add_task("Add signup flow")
        await team.run(max_cycles=100)
    """

    def __init__(
        self,
        name: str = "startup-team",
        developer_count: int = 2,
        has_lead: bool = True,
    ):
        config = TeamConfig(
            name=name,
            style=TeamStyle.STARTUP,
            roles={
                AgentRole.LEAD: 1 if has_lead else 0,
                AgentRole.DEVELOPER: developer_count,
            },
            ceremonies=[
                CeremonyConfig(
                    ceremony_type=CeremonyType.STANDUP,
                    frequency="daily",
                    duration_minutes=10,
                    required_roles=[AgentRole.DEVELOPER],
                ),
            ],
            validation=ValidationConfig(
                require_review=True,
                require_tests=True,
                require_docs=False,
                min_reviewers=1,
                auto_merge=True,  # Fast iteration
                proof_generation=True,
                pre_commit_gates=["lint"],  # Minimal gates
                pre_merge_gates=["tests_pass"],
            ),
            max_concurrent_tasks=3,
            max_wip_per_agent=2,  # Higher WIP for speed
            iteration_length_days=7,  # Short sprints
            async_first=True,
            decision_timeout_hours=4,  # Fast decisions
        )
        super().__init__(config)
        self._create_agents()

    def _create_agents(self) -> None:
        """Create startup team agents."""
        if self.config.roles.get(AgentRole.LEAD, 0) > 0:
            lead = LeadAgent("lead-1", message_bus=self.message_bus)
            self.agents[lead.agent_id] = lead
            self.message_bus.register(lead.agent_id)

        for i in range(self.config.roles.get(AgentRole.DEVELOPER, 0)):
            dev = DeveloperAgent(f"dev-{i+1}", message_bus=self.message_bus)
            self.agents[dev.agent_id] = dev
            self.message_bus.register(dev.agent_id)


class EnterpriseTeam(BaseTeam):
    """Enterprise team with full governance. Audit trails, compliance, security.

    Characteristics:
    - Larger team (5-8 agents)
    - Full SCRUM ceremonies
    - Multiple review gates
    - No auto-merge (human approval)
    - Complete audit trails
    - Security gates

    Example:
        team = EnterpriseTeam(name="platform-team")
        team.add_task("Migrate auth to OAuth2", priority=1)
        await team.run()
    """

    def __init__(
        self,
        name: str = "enterprise-team",
        developer_count: int = 3,
    ):
        config = TeamConfig(
            name=name,
            style=TeamStyle.ENTERPRISE,
            roles={
                AgentRole.LEAD: 1,
                AgentRole.ARCHITECT: 1,
                AgentRole.DEVELOPER: developer_count,
                AgentRole.REVIEWER: 1,
                AgentRole.QA: 1,
                AgentRole.SECURITY: 1,
            },
            ceremonies=[
                CeremonyConfig(
                    ceremony_type=CeremonyType.STANDUP,
                    frequency="daily",
                    duration_minutes=15,
                    required_roles=[AgentRole.DEVELOPER, AgentRole.QA],
                ),
                CeremonyConfig(
                    ceremony_type=CeremonyType.PLANNING,
                    frequency="sprint",
                    duration_minutes=120,
                    required_roles=[AgentRole.LEAD, AgentRole.ARCHITECT],
                ),
                CeremonyConfig(
                    ceremony_type=CeremonyType.REVIEW,
                    frequency="sprint",
                    duration_minutes=60,
                    required_roles=[AgentRole.LEAD],
                ),
                CeremonyConfig(
                    ceremony_type=CeremonyType.RETRO,
                    frequency="sprint",
                    duration_minutes=60,
                    required_roles=[AgentRole.DEVELOPER],
                ),
            ],
            validation=ValidationConfig(
                require_review=True,
                require_tests=True,
                require_docs=True,  # Docs required
                min_reviewers=2,    # Multiple reviewers
                auto_merge=False,   # No auto-merge
                proof_generation=True,
                store_to_memory=True,
                pre_commit_gates=["lint", "type_check", "secrets_scan"],
                pre_merge_gates=["tests_pass", "review_approved", "security_scan"],
                post_deploy_gates=["smoke_tests", "monitoring_check"],
            ),
            max_concurrent_tasks=5,
            max_wip_per_agent=1,  # Strict WIP
            iteration_length_days=14,
            async_first=False,  # Sync-heavy
            decision_timeout_hours=48,  # Deliberate decisions
        )
        super().__init__(config)
        self._create_agents()

    def _create_agents(self) -> None:
        """Create enterprise team agents."""
        self.agents["lead-1"] = LeadAgent("lead-1", message_bus=self.message_bus)
        self.agents["architect-1"] = ArchitectAgent("architect-1", message_bus=self.message_bus)
        self.agents["reviewer-1"] = ReviewerAgent("reviewer-1", message_bus=self.message_bus)
        self.agents["qa-1"] = QAAgent("qa-1", message_bus=self.message_bus)

        for i in range(self.config.roles.get(AgentRole.DEVELOPER, 0)):
            dev_id = f"dev-{i+1}"
            self.agents[dev_id] = DeveloperAgent(dev_id, message_bus=self.message_bus)

        for agent_id in self.agents:
            self.message_bus.register(agent_id)


class ResearchTeam(BaseTeam):
    """Research-focused team. Exploration, hypothesis-driven, learning.

    Characteristics:
    - Small research team (2-4)
    - Async-first communication
    - Hypothesis-result tracking
    - Heavy memory recall usage
    - Documented findings
    - Spike-oriented

    Example:
        team = ResearchTeam(name="ml-research")
        team.add_research_question("How can we improve recall latency?")
        await team.run()
    """

    def __init__(
        self,
        name: str = "research-team",
        researcher_count: int = 2,
    ):
        config = TeamConfig(
            name=name,
            style=TeamStyle.RESEARCH,
            roles={
                AgentRole.LEAD: 1,  # Principal investigator
                AgentRole.RESEARCHER: researcher_count,
            },
            ceremonies=[
                CeremonyConfig(
                    ceremony_type=CeremonyType.SYNC,
                    frequency="weekly",
                    duration_minutes=30,
                    required_roles=[AgentRole.RESEARCHER],
                ),
            ],
            validation=ValidationConfig(
                require_review=False,  # Research is exploratory
                require_tests=False,   # POCs don't need tests
                require_docs=True,     # But must document findings
                min_reviewers=0,
                auto_merge=True,
                proof_generation=True,  # Track experiments
                store_to_memory=True,   # Heavy memory use
                pre_commit_gates=[],
                pre_merge_gates=[],
            ),
            max_concurrent_tasks=4,
            max_wip_per_agent=2,  # Parallel investigations
            iteration_length_days=7,
            async_first=True,
            decision_timeout_hours=72,  # Research takes time
        )
        super().__init__(config)
        self.hypotheses: List[Dict[str, Any]] = []
        self.findings: List[Dict[str, Any]] = []
        self._create_agents()

    def _create_agents(self) -> None:
        """Create research team agents."""
        self.agents["pi-1"] = LeadAgent("pi-1", message_bus=self.message_bus)

        for i in range(self.config.roles.get(AgentRole.RESEARCHER, 0)):
            researcher_id = f"researcher-{i+1}"
            self.agents[researcher_id] = ResearcherAgent(
                researcher_id, message_bus=self.message_bus
            )

        for agent_id in self.agents:
            self.message_bus.register(agent_id)

    def add_research_question(
        self,
        question: str,
        hypothesis: str = None,
        priority: int = 5,
    ) -> TaskAssignment:
        """Add a research question to investigate."""
        task = self.add_task(
            title=f"Research: {question[:50]}",
            description=question,
            priority=priority,
        )
        if hypothesis:
            self.hypotheses.append({
                "task_id": task.id,
                "hypothesis": hypothesis,
                "status": "pending",
            })
        return task

    async def discover_from_problem(
        self,
        problem: str,
        max_questions: int = 5,
    ) -> List[TaskAssignment]:
        """Auto-discover research questions from a problem statement.

        Uses LLM to generate hypotheses and research questions.

        Args:
            problem: Problem statement like "CTR dropped 15%"
            max_questions: Max questions to generate

        Returns:
            List of created TaskAssignment objects

        Example:
            tasks = await team.discover_from_problem(
                "API latency increased after last deploy"
            )
        """
        try:
            import anthropic
            import os
        except ImportError:
            # Fallback: single question from problem
            return [self.add_research_question(f"Investigate: {problem}")]

        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEYY")
        if not api_key:
            return [self.add_research_question(f"Investigate: {problem}")]

        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Given this problem, generate {max_questions} research questions with hypotheses.

Problem: {problem}

For each question, provide:
1. A specific, testable research question
2. A hypothesis that could explain it
3. Priority (1=critical, 5=nice-to-have)

Format as JSON array:
[{{"question": "...", "hypothesis": "...", "priority": 1}}]

Only output the JSON array, nothing else."""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            import json
            questions = json.loads(response.content[0].text)
        except Exception:
            return [self.add_research_question(f"Investigate: {problem}")]

        created = []
        for q in questions[:max_questions]:
            task = self.add_research_question(
                question=q.get("question", problem),
                hypothesis=q.get("hypothesis"),
                priority=q.get("priority", 5),
            )
            created.append(task)

        return created

    def record_finding(
        self,
        task_id: str,
        finding: str,
        evidence: List[str] = None,
    ) -> None:
        """Record a research finding."""
        self.findings.append({
            "task_id": task_id,
            "finding": finding,
            "evidence": evidence or [],
        })


class SoloDevTeam(BaseTeam):
    """Solo developer with AI assistance. One person + agents.

    Characteristics:
    - Single human dev
    - AI agents for review, testing, research
    - No ceremonies (self-managed)
    - Direct task execution
    - Personal productivity focus

    Example:
        team = SoloDevTeam(name="my-project")
        team.add_task("Implement feature X")
        await team.run()
    """

    def __init__(self, name: str = "solo-dev"):
        config = TeamConfig(
            name=name,
            style=TeamStyle.SOLO,
            roles={
                AgentRole.DEVELOPER: 1,
                AgentRole.REVIEWER: 1,  # AI reviewer
            },
            ceremonies=[],  # No ceremonies
            validation=ValidationConfig(
                require_review=True,  # AI review
                require_tests=True,
                require_docs=False,
                min_reviewers=1,
                auto_merge=True,
                proof_generation=True,
            ),
            max_concurrent_tasks=1,
            max_wip_per_agent=1,
            iteration_length_days=1,  # Daily cadence
            async_first=True,
        )
        super().__init__(config)
        self._create_agents()

    def _create_agents(self) -> None:
        """Create solo dev assistants."""
        self.agents["dev-1"] = DeveloperAgent("dev-1", message_bus=self.message_bus)
        self.agents["reviewer-1"] = ReviewerAgent("reviewer-1", message_bus=self.message_bus)

        for agent_id in self.agents:
            self.message_bus.register(agent_id)


class PairTeam(BaseTeam):
    """Pair programming team. Driver/navigator pattern.

    Characteristics:
    - Two developers rotating roles
    - Continuous code review
    - Shared context
    - Tight collaboration

    Example:
        team = PairTeam(name="pair-1")
        team.add_task("Build authentication system")
        await team.run()
    """

    def __init__(self, name: str = "pair-team"):
        config = TeamConfig(
            name=name,
            style=TeamStyle.PAIR,
            roles={
                AgentRole.DEVELOPER: 2,
            },
            ceremonies=[
                CeremonyConfig(
                    ceremony_type=CeremonyType.SYNC,
                    frequency="hourly",  # Frequent rotation
                    duration_minutes=5,
                ),
            ],
            validation=ValidationConfig(
                require_review=False,  # Continuous review
                require_tests=True,
                require_docs=False,
                min_reviewers=0,
                auto_merge=True,
                proof_generation=True,
            ),
            max_concurrent_tasks=1,  # One task at a time
            max_wip_per_agent=1,
            iteration_length_days=1,
            async_first=False,  # Synchronous
        )
        super().__init__(config)
        self.driver: Optional[str] = None
        self.navigator: Optional[str] = None
        self._create_agents()

    def _create_agents(self) -> None:
        """Create pair agents."""
        self.agents["driver"] = DeveloperAgent("driver", message_bus=self.message_bus)
        self.agents["navigator"] = DeveloperAgent("navigator", message_bus=self.message_bus)
        self.driver = "driver"
        self.navigator = "navigator"

        for agent_id in self.agents:
            self.message_bus.register(agent_id)

    def rotate(self) -> None:
        """Rotate driver/navigator roles."""
        self.driver, self.navigator = self.navigator, self.driver


class MobTeam(BaseTeam):
    """Mob programming team. Whole team, one task.

    Characteristics:
    - 3-5 developers
    - One task at a time
    - Rotating roles
    - Maximum knowledge sharing
    - Collective ownership

    Example:
        team = MobTeam(name="mob-squad", mob_size=4)
        team.add_task("Refactor payment system")
        await team.run()
    """

    def __init__(self, name: str = "mob-team", mob_size: int = 4):
        config = TeamConfig(
            name=name,
            style=TeamStyle.MOB,
            roles={
                AgentRole.DEVELOPER: mob_size,
            },
            ceremonies=[
                CeremonyConfig(
                    ceremony_type=CeremonyType.SYNC,
                    frequency="continuous",
                    duration_minutes=0,  # Always syncing
                ),
            ],
            validation=ValidationConfig(
                require_review=False,  # Mob is the review
                require_tests=True,
                require_docs=True,
                min_reviewers=0,
                auto_merge=True,
                proof_generation=True,
            ),
            max_concurrent_tasks=1,  # Mob = one task
            max_wip_per_agent=1,
            iteration_length_days=1,
            async_first=False,  # Synchronous mob
        )
        super().__init__(config)
        self._create_agents()

    def _create_agents(self) -> None:
        """Create mob agents."""
        for i in range(self.config.roles.get(AgentRole.DEVELOPER, 0)):
            agent_id = f"mob-{i+1}"
            self.agents[agent_id] = DeveloperAgent(agent_id, message_bus=self.message_bus)
            self.message_bus.register(agent_id)


class OpenSourceTeam(BaseTeam):
    """Open source project team. Async, distributed, PR-based.

    Characteristics:
    - Variable contributor count
    - Async-first (distributed)
    - PR-based workflow
    - Public issue tracking
    - Community governance

    Example:
        team = OpenSourceTeam(name="oss-project")
        team.add_task("Fix issue #123")
        await team.run()
    """

    def __init__(self, name: str = "oss-team", maintainer_count: int = 2):
        config = TeamConfig(
            name=name,
            style=TeamStyle.OPEN_SOURCE,
            roles={
                AgentRole.LEAD: maintainer_count,  # Maintainers
                AgentRole.REVIEWER: maintainer_count,
                AgentRole.DEVELOPER: 0,  # Contributors join dynamically
            },
            ceremonies=[
                CeremonyConfig(
                    ceremony_type=CeremonyType.SYNC,
                    frequency="weekly",
                    duration_minutes=60,
                    required_roles=[AgentRole.LEAD],
                ),
            ],
            validation=ValidationConfig(
                require_review=True,
                require_tests=True,
                require_docs=True,
                min_reviewers=1,
                auto_merge=False,  # Maintainer approval
                proof_generation=True,
                store_to_memory=True,
                pre_commit_gates=["lint", "type_check"],
                pre_merge_gates=["tests_pass", "review_approved", "cla_signed"],
            ),
            max_concurrent_tasks=10,  # Many parallel PRs
            max_wip_per_agent=3,
            iteration_length_days=7,
            async_first=True,
            decision_timeout_hours=168,  # Week for decisions
        )
        super().__init__(config)
        self._create_agents()

    def _create_agents(self) -> None:
        """Create maintainer agents."""
        for i in range(self.config.roles.get(AgentRole.LEAD, 0)):
            maintainer_id = f"maintainer-{i+1}"
            self.agents[maintainer_id] = LeadAgent(maintainer_id, message_bus=self.message_bus)
            self.message_bus.register(maintainer_id)

            reviewer_id = f"reviewer-{i+1}"
            self.agents[reviewer_id] = ReviewerAgent(reviewer_id, message_bus=self.message_bus)
            self.message_bus.register(reviewer_id)


class AgencyTeam(BaseTeam):
    """Agency/consulting team. Client-facing, deliverable-focused.

    Characteristics:
    - Project-based work
    - Client communication
    - Milestone tracking
    - Deliverable focus
    - Time/budget tracking

    Example:
        team = AgencyTeam(name="client-project")
        team.add_milestone("MVP", deadline="2025-03-01")
        team.add_task("Design mockups", milestone="MVP")
        await team.run()
    """

    def __init__(self, name: str = "agency-team"):
        config = TeamConfig(
            name=name,
            style=TeamStyle.AGENCY,
            roles={
                AgentRole.LEAD: 1,          # Project lead
                AgentRole.DEVELOPER: 2,
                AgentRole.REVIEWER: 1,
                AgentRole.QA: 1,
            },
            ceremonies=[
                CeremonyConfig(
                    ceremony_type=CeremonyType.STANDUP,
                    frequency="daily",
                    duration_minutes=15,
                ),
                CeremonyConfig(
                    ceremony_type=CeremonyType.REVIEW,
                    frequency="weekly",  # Client demos
                    duration_minutes=60,
                    required_roles=[AgentRole.LEAD],
                ),
            ],
            validation=ValidationConfig(
                require_review=True,
                require_tests=True,
                require_docs=True,  # Client docs
                min_reviewers=1,
                auto_merge=False,
                proof_generation=True,
                store_to_memory=True,
            ),
            max_concurrent_tasks=4,
            max_wip_per_agent=1,
            iteration_length_days=7,
            async_first=True,
            decision_timeout_hours=24,  # Fast client response
        )
        super().__init__(config)
        self.milestones: Dict[str, Dict[str, Any]] = {}
        self._create_agents()

    def _create_agents(self) -> None:
        """Create agency team agents."""
        self.agents["lead-1"] = LeadAgent("lead-1", message_bus=self.message_bus)
        self.agents["dev-1"] = DeveloperAgent("dev-1", message_bus=self.message_bus)
        self.agents["dev-2"] = DeveloperAgent("dev-2", message_bus=self.message_bus)
        self.agents["reviewer-1"] = ReviewerAgent("reviewer-1", message_bus=self.message_bus)
        self.agents["qa-1"] = QAAgent("qa-1", message_bus=self.message_bus)

        for agent_id in self.agents:
            self.message_bus.register(agent_id)

    def add_milestone(
        self,
        name: str,
        deadline: str = None,
        deliverables: List[str] = None,
    ) -> None:
        """Add a project milestone."""
        self.milestones[name] = {
            "deadline": deadline,
            "deliverables": deliverables or [],
            "status": "pending",
        }

    def add_task(
        self,
        title: str,
        description: str = "",
        priority: int = 5,
        milestone: str = None,
    ) -> TaskAssignment:
        """Add task with optional milestone assignment."""
        task = super().add_task(title, description, priority)
        if milestone and milestone in self.milestones:
            self.milestones[milestone]["deliverables"].append(task.id)
        return task
