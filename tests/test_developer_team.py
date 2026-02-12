"""Tests for DeveloperTeam starter blueprints and execution."""

from __future__ import annotations

from pathlib import Path

from teams.meta_orchestrator import DeveloperTeam, DeveloperTeamFactory


def test_developer_team_factory_starter_pack_contains_requested_teams() -> None:
    pack = DeveloperTeamFactory.starter_pack(
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
    )

    assert set(pack.keys()) == {
        "company_guidance",
        "startup_backend_dev",
        "gfx_subagent_design",
    }

    assert pack["company_guidance"].members
    assert pack["startup_backend_dev"].members
    assert pack["gfx_subagent_design"].members


def test_company_team_executes_objective() -> None:
    blueprint = DeveloperTeamFactory.company_guidance_team(
        company_name="Acme",
        workspace=str(Path.cwd()),
    )
    team = DeveloperTeam(blueprint)

    result = team.run_objective("Prioritize next release")

    assert result.status == "completed"
    assert result.pillar_results


def test_backend_team_executes_with_context_overrides() -> None:
    blueprint = DeveloperTeamFactory.startup_backend_dev_team(
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
    )
    team = DeveloperTeam(blueprint)

    result = team.run_objective(
        "Validate API rollout plan",
        extra_context={"deploy_target": "prod"},
        approvals={"role:CTO": True},
    )

    assert result.status == "completed"
    assert result.pillar_results[-1].fot_exit_pack.execution_track.next_actions


def test_gfx_team_executes_design_objective() -> None:
    blueprint = DeveloperTeamFactory.gfx_subagent_design_team(
        company_name="Acme",
        workspace=str(Path.cwd()),
    )
    team = DeveloperTeam(blueprint)

    result = team.run_objective("Design gfx subagent interfaces")

    assert result.status == "completed"
    assert result.pillar_results[-1].fot_exit_pack.awareness_track.objective
