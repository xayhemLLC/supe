"""Tests for core->team->individual hierarchy runner."""

from __future__ import annotations

from pathlib import Path

from teams.meta_orchestrator import OrgHierarchyRunner


def test_org_hierarchy_core_to_team_to_individual_flow() -> None:
    runner = OrgHierarchyRunner.from_profile(
        profile="growth",
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
    )

    core_result, core_signal = runner.run_core_org_pillar(
        pillar_name="ORG_CORE",
        objective="Set organization delivery policy",
    )
    assert core_result.status == "completed"
    assert core_signal.scope == "core_org"

    team_result, team_signal = runner.run_team_pillar(
        team_key="startup_backend_dev",
        parent_pillar=core_signal,
        team_pillar_name="TEAM_BACKEND",
        team_objective="Translate org policy to backend flow",
    )
    assert team_result.status == "completed"
    assert team_signal.scope == "team:startup_backend_dev"
    assert core_signal.sid in team_signal.provenance

    indiv_result, indiv_signal = runner.run_individual_backend_dev(
        developer_alias="chris",
        core_pillar=core_signal,
        team_pillar=team_signal,
        personal_pillar_name="INDIVIDUAL_BACKEND",
        objective="Implement scoped backend task",
    )
    assert indiv_result.status == "completed"
    assert indiv_signal.scope == "individual:chris"
    assert core_signal.sid in indiv_signal.provenance
    assert team_signal.sid in indiv_signal.provenance
