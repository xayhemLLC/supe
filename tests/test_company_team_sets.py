"""Tests for company profile team sets."""

from __future__ import annotations

from pathlib import Path

import pytest

from teams.meta_orchestrator import DeveloperTeam, DeveloperTeamFactory


@pytest.mark.parametrize("profile", ["startup", "growth", "enterprise", "agency", "open_source"])
def test_company_team_set_contains_three_teams(profile: str) -> None:
    team_set = DeveloperTeamFactory.build_company_team_set(
        profile=profile,
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
    )

    assert team_set.profile == profile
    assert team_set.teams.keys() == {
        "company_guidance",
        "startup_backend_dev",
        "gfx_subagent_design",
    }


@pytest.mark.parametrize("profile", ["startup", "growth", "enterprise", "agency", "open_source"])
@pytest.mark.parametrize("team_key", ["company_guidance", "startup_backend_dev", "gfx_subagent_design"])
def test_company_profile_team_executes_objective(profile: str, team_key: str) -> None:
    team_set = DeveloperTeamFactory.build_company_team_set(
        profile=profile,
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
    )

    blueprint = team_set.teams[team_key]
    team = DeveloperTeam(blueprint)
    objective = blueprint.starter_objectives[0]

    result = team.run_objective(objective)

    assert result.status == "completed"
    assert result.pillar_results
    assert result.pillar_results[-1].fot_exit_pack.awareness_track.objective
