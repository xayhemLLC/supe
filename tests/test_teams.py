"""Tests for supe.teams module."""

import pytest
import asyncio
from supe.teams import (
    # Config
    TeamConfig,
    TeamStyle,
    AgentRole,
    # Team Styles
    StartupTeam,
    EnterpriseTeam,
    ResearchTeam,
    SoloDevTeam,
    PairTeam,
    MobTeam,
    OpenSourceTeam,
    AgencyTeam,
    # Agents
    ValidatedAgent,
    LeadAgent,
    DeveloperAgent,
    ReviewerAgent,
    QAAgent,
)
from supe.teams.base import (
    CeremonyConfig,
    CeremonyType,
    ValidationConfig,
    TaskAssignment,
    MessageBus,
)


class TestTeamConfig:
    """Test TeamConfig dataclass."""

    def test_create_config(self):
        config = TeamConfig(
            name="test-team",
            style=TeamStyle.STARTUP,
            roles={AgentRole.DEVELOPER: 2},
        )
        assert config.name == "test-team"
        assert config.style == TeamStyle.STARTUP
        assert config.total_agents() == 2

    def test_has_role(self):
        config = TeamConfig(
            name="test",
            style=TeamStyle.STARTUP,
            roles={
                AgentRole.DEVELOPER: 2,
                AgentRole.QA: 1,
            },
        )
        assert config.has_role(AgentRole.DEVELOPER)
        assert config.has_role(AgentRole.QA)
        assert not config.has_role(AgentRole.ARCHITECT)

    def test_validation_config_defaults(self):
        val = ValidationConfig()
        assert val.require_review is True
        assert val.require_tests is True
        assert val.proof_generation is True


class TestTaskAssignment:
    """Test TaskAssignment."""

    def test_create_task(self):
        task = TaskAssignment(title="Test task")
        assert task.status == "pending"
        assert task.assigned_to is None

    def test_start_task(self):
        task = TaskAssignment(title="Test task")
        task.start("dev-1")
        assert task.status == "in_progress"
        assert task.assigned_to == "dev-1"
        assert task.started_at is not None

    def test_complete_task(self):
        task = TaskAssignment(title="Test task")
        task.start("dev-1")
        task.complete(proof_hash="abc123")
        assert task.status == "done"
        assert task.proof_hash == "abc123"
        assert task.completed_at is not None


class TestMessageBus:
    """Test MessageBus."""

    @pytest.mark.asyncio
    async def test_send_receive(self):
        bus = MessageBus()
        bus.register("agent-1")
        bus.register("agent-2")

        await bus.send("agent-1", "agent-2", {"hello": "world"})
        msg = await bus.receive("agent-2", timeout=1.0)

        assert msg is not None
        assert msg["content"]["hello"] == "world"
        assert msg["sender"] == "agent-1"

    @pytest.mark.asyncio
    async def test_broadcast(self):
        bus = MessageBus()
        bus.register("agent-1")
        bus.register("agent-2")
        bus.register("agent-3")

        await bus.broadcast("agent-1", {"type": "announcement"})

        # agent-2 and agent-3 should receive
        msg2 = await bus.receive("agent-2", timeout=1.0)
        msg3 = await bus.receive("agent-3", timeout=1.0)

        assert msg2 is not None
        assert msg3 is not None

        # agent-1 should not receive own broadcast
        msg1 = await bus.receive("agent-1", timeout=0.1)
        assert msg1 is None


class TestStartupTeam:
    """Test StartupTeam style."""

    def test_create_startup_team(self):
        team = StartupTeam(name="mvp-squad", developer_count=2)
        assert team.config.style == TeamStyle.STARTUP
        assert team.config.name == "mvp-squad"
        assert len(team.agents) == 3  # 1 lead + 2 devs

    def test_startup_has_minimal_ceremonies(self):
        team = StartupTeam()
        assert len(team.config.ceremonies) == 1
        assert team.config.ceremonies[0].ceremony_type == CeremonyType.STANDUP

    def test_startup_allows_auto_merge(self):
        team = StartupTeam()
        assert team.config.validation.auto_merge is True

    def test_add_task(self):
        team = StartupTeam()
        task = team.add_task("Build landing page", priority=1)
        assert task.id in team.tasks
        assert team.tasks[task.id].title == "Build landing page"


class TestEnterpriseTeam:
    """Test EnterpriseTeam style."""

    def test_create_enterprise_team(self):
        team = EnterpriseTeam(name="platform-team")
        assert team.config.style == TeamStyle.ENTERPRISE
        assert len(team.agents) >= 6  # lead, architect, reviewer, qa, devs

    def test_enterprise_has_full_ceremonies(self):
        team = EnterpriseTeam()
        ceremony_types = [c.ceremony_type for c in team.config.ceremonies]
        assert CeremonyType.STANDUP in ceremony_types
        assert CeremonyType.PLANNING in ceremony_types
        assert CeremonyType.REVIEW in ceremony_types
        assert CeremonyType.RETRO in ceremony_types

    def test_enterprise_no_auto_merge(self):
        team = EnterpriseTeam()
        assert team.config.validation.auto_merge is False

    def test_enterprise_requires_multiple_reviewers(self):
        team = EnterpriseTeam()
        assert team.config.validation.min_reviewers >= 2


class TestResearchTeam:
    """Test ResearchTeam style."""

    def test_create_research_team(self):
        team = ResearchTeam(name="ml-research", researcher_count=3)
        assert team.config.style == TeamStyle.RESEARCH
        assert len(team.agents) == 4  # PI + 3 researchers

    def test_research_question(self):
        team = ResearchTeam()
        task = team.add_research_question(
            "How does X affect Y?",
            hypothesis="X increases Y",
        )
        assert task is not None
        assert len(team.hypotheses) == 1

    def test_record_finding(self):
        team = ResearchTeam()
        task = team.add_research_question("Test question")
        team.record_finding(task.id, "X does increase Y", evidence=["exp1", "exp2"])
        assert len(team.findings) == 1
        assert team.findings[0]["finding"] == "X does increase Y"


class TestSoloDevTeam:
    """Test SoloDevTeam style."""

    def test_create_solo_team(self):
        team = SoloDevTeam(name="my-project")
        assert team.config.style == TeamStyle.SOLO
        assert len(team.agents) == 2  # dev + AI reviewer

    def test_solo_no_ceremonies(self):
        team = SoloDevTeam()
        assert len(team.config.ceremonies) == 0


class TestPairTeam:
    """Test PairTeam style."""

    def test_create_pair_team(self):
        team = PairTeam(name="pair-1")
        assert team.config.style == TeamStyle.PAIR
        assert len(team.agents) == 2

    def test_pair_has_driver_navigator(self):
        team = PairTeam()
        assert team.driver is not None
        assert team.navigator is not None
        assert team.driver != team.navigator

    def test_rotate_roles(self):
        team = PairTeam()
        original_driver = team.driver
        original_navigator = team.navigator
        team.rotate()
        assert team.driver == original_navigator
        assert team.navigator == original_driver


class TestMobTeam:
    """Test MobTeam style."""

    def test_create_mob_team(self):
        team = MobTeam(name="mob-squad", mob_size=4)
        assert team.config.style == TeamStyle.MOB
        assert len(team.agents) == 4

    def test_mob_single_task(self):
        team = MobTeam()
        assert team.config.max_concurrent_tasks == 1


class TestOpenSourceTeam:
    """Test OpenSourceTeam style."""

    def test_create_oss_team(self):
        team = OpenSourceTeam(name="oss-project", maintainer_count=2)
        assert team.config.style == TeamStyle.OPEN_SOURCE
        assert len(team.agents) == 4  # 2 maintainers + 2 reviewers

    def test_oss_async_first(self):
        team = OpenSourceTeam()
        assert team.config.async_first is True


class TestAgencyTeam:
    """Test AgencyTeam style."""

    def test_create_agency_team(self):
        team = AgencyTeam(name="client-project")
        assert team.config.style == TeamStyle.AGENCY
        assert len(team.agents) == 5

    def test_add_milestone(self):
        team = AgencyTeam()
        team.add_milestone("MVP", deadline="2025-03-01", deliverables=["spec", "ui"])
        assert "MVP" in team.milestones

    def test_add_task_with_milestone(self):
        team = AgencyTeam()
        team.add_milestone("MVP")
        task = team.add_task("Design mockups", milestone="MVP")
        assert task.id in team.milestones["MVP"]["deliverables"]


class TestAgents:
    """Test agent classes."""

    def test_lead_agent(self):
        agent = LeadAgent("lead-1")
        assert agent.role == AgentRole.LEAD
        assert "architecture" in agent.config.capabilities

    def test_developer_agent(self):
        agent = DeveloperAgent("dev-1")
        assert agent.role == AgentRole.DEVELOPER
        assert "code" in agent.config.capabilities

    def test_reviewer_agent(self):
        agent = ReviewerAgent("reviewer-1")
        assert agent.role == AgentRole.REVIEWER

    def test_qa_agent(self):
        agent = QAAgent("qa-1")
        assert agent.role == AgentRole.QA


class TestTeamExecution:
    """Test team execution flow."""

    @pytest.mark.asyncio
    async def test_run_cycle(self):
        team = StartupTeam(developer_count=1)
        team.add_task("Task 1")
        team.add_task("Task 2")

        result = await team.run_cycle()
        assert result["cycle"] == 1
        assert len(result["assignments"]) > 0

    @pytest.mark.asyncio
    async def test_run_limited_cycles(self):
        team = StartupTeam(developer_count=1)
        team.add_task("Task 1")

        status = await team.run(max_cycles=3)
        assert status["cycles"] == 3

    def test_get_status(self):
        team = StartupTeam()
        team.add_task("Task 1")
        team.add_task("Task 2")

        status = team.get_status()
        assert status["name"] == "startup-team"
        assert status["style"] == "startup"
        assert status["tasks"]["total"] == 2
