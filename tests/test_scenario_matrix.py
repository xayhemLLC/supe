"""Broad scenario matrix tests for FoT + meta-orchestrator hierarchy."""

from __future__ import annotations

from pathlib import Path

import pytest

from teams.meta_orchestrator import DeveloperTeam, DeveloperTeamFactory, OrgHierarchyRunner
from teams.nubflow import FlowOfTimeEngine, FoTState

TEAM_SCENARIOS = [
    {
        "id": "startup_company_default",
        "profile": "startup",
        "team_key": "company_guidance",
        "expected_status": "completed",
    },
    {
        "id": "startup_backend_default",
        "profile": "startup",
        "team_key": "startup_backend_dev",
        "expected_status": "completed",
    },
    {
        "id": "growth_gfx_default",
        "profile": "growth",
        "team_key": "gfx_subagent_design",
        "expected_status": "completed",
    },
    {
        "id": "enterprise_company_default",
        "profile": "enterprise",
        "team_key": "company_guidance",
        "expected_status": "completed",
    },
    {
        "id": "enterprise_backend_default",
        "profile": "enterprise",
        "team_key": "startup_backend_dev",
        "expected_status": "completed",
    },
    {
        "id": "agency_company_default",
        "profile": "agency",
        "team_key": "company_guidance",
        "expected_status": "completed",
    },
    {
        "id": "agency_backend_default",
        "profile": "agency",
        "team_key": "startup_backend_dev",
        "expected_status": "completed",
    },
    {
        "id": "agency_gfx_default",
        "profile": "agency",
        "team_key": "gfx_subagent_design",
        "expected_status": "completed",
    },
    {
        "id": "open_source_company_default",
        "profile": "open_source",
        "team_key": "company_guidance",
        "expected_status": "completed",
    },
    {
        "id": "open_source_backend_default",
        "profile": "open_source",
        "team_key": "startup_backend_dev",
        "expected_status": "completed",
    },
    {
        "id": "startup_backend_forced_hold",
        "profile": "startup",
        "team_key": "startup_backend_dev",
        "approvals": {"PeerReviewSignoff": False, "HumanApprovalGate": False},
        "expected_status": "hold",
    },
    {
        "id": "enterprise_company_forced_hold",
        "profile": "enterprise",
        "team_key": "company_guidance",
        "approvals": {
            "PeerReviewSignoff": False,
            "HumanApprovalGate": False,
            "ReleaseManagerSignoffIfProd": False,
            "role:CTO": False,
        },
        "expected_status": "hold",
    },
]


@pytest.mark.parametrize("scenario", TEAM_SCENARIOS, ids=[scenario["id"] for scenario in TEAM_SCENARIOS])
def test_company_team_scenario_matrix(scenario: dict[str, object]) -> None:
    team_set = DeveloperTeamFactory.build_company_team_set(
        profile=str(scenario["profile"]),
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
    )

    blueprint = team_set.teams[str(scenario["team_key"])]
    team = DeveloperTeam(blueprint)
    objective = blueprint.starter_objectives[0]

    result = team.run_objective(
        objective,
        approvals=scenario.get("approvals") if isinstance(scenario.get("approvals"), dict) else None,
    )

    assert result.status == scenario["expected_status"]


@pytest.mark.parametrize("profile", ["startup", "growth", "enterprise", "agency", "open_source"])
def test_hierarchy_propagation_matrix(profile: str) -> None:
    runner = OrgHierarchyRunner.from_profile(
        profile=profile,
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
    )

    core_result, core_signal = runner.run_core_org_pillar(
        pillar_name="ORG_CORE",
        objective=f"{profile} core policy",
    )
    assert core_result.status == "completed"

    team_result, team_signal = runner.run_team_pillar(
        team_key="startup_backend_dev",
        parent_pillar=core_signal,
        team_pillar_name="TEAM_BACKEND",
        team_objective=f"{profile} backend translation",
    )
    assert team_result.status == "completed"
    assert core_signal.sid in team_signal.provenance

    indiv_result, indiv_signal = runner.run_individual_backend_dev(
        developer_alias="chris",
        core_pillar=core_signal,
        team_pillar=team_signal,
        personal_pillar_name="INDIVIDUAL_BACKEND",
        objective=f"{profile} personal execution",
    )
    assert indiv_result.status == "completed"
    assert core_signal.sid in indiv_signal.provenance
    assert team_signal.sid in indiv_signal.provenance


FOT_SCENARIOS = [
    {
        "id": "user_input_exit",
        "sys_inputs": [{"kind": "input", "source": "user", "payload": {"objective": "ship"}}],
        "expected_state": FoTState.EXIT,
    },
    {
        "id": "human_gate_hold",
        "sys_inputs": [
            {
                "kind": "input",
                "source": "user",
                "payload": {"requires_human_signoff": True, "hold_reason": "manual_approval_needed"},
            }
        ],
        "expected_state": FoTState.HOLD,
    },
    {
        "id": "git_ledger_flow",
        "sys_inputs": [{"kind": "input", "source": "git", "payload": {"query_plan": {"limit": 2}}}],
        "expected_state": FoTState.EXIT,
        "expected_pointer": "git_ledger",
    },
    {
        "id": "jira_ledger_seeded_flow",
        "sys_inputs": [
            {
                "kind": "input",
                "source": "jira",
                "payload": {"query_plan": {"items": [{"key": "PLAT-1"}], "limit": 1}},
            }
        ],
        "expected_state": FoTState.EXIT,
        "expected_pointer": "jira_ledger",
    },
    {
        "id": "notion_ledger_seeded_flow",
        "sys_inputs": [
            {
                "kind": "input",
                "source": "notion",
                "payload": {"query_plan": {"pages": [{"id": "page-1", "title": "Doc"}], "limit": 1}},
            }
        ],
        "expected_state": FoTState.EXIT,
        "expected_pointer": "notion_ledger",
    },
    {
        "id": "discord_ledger_seeded_flow",
        "sys_inputs": [
            {
                "kind": "input",
                "source": "discord",
                "payload": {"query_plan": {"messages": [{"id": "1", "content": "hi"}], "limit": 1}},
            }
        ],
        "expected_state": FoTState.EXIT,
        "expected_pointer": "discord_ledger",
    },
    {
        "id": "web_ledger_empty_urls",
        "sys_inputs": [{"kind": "input", "source": "web", "payload": {"query_plan": {"urls": [], "limit": 1}}}],
        "expected_state": FoTState.EXIT,
        "expected_pointer": "web_ledger",
    },
    {
        "id": "prev_pack_plus_new_inputs",
        "sys_inputs": [{"kind": "input", "source": "user", "payload": {"goal": "next"}}],
        "expected_state": FoTState.EXIT,
        "use_prev_pack": True,
    },
]


@pytest.mark.parametrize("scenario", FOT_SCENARIOS, ids=[scenario["id"] for scenario in FOT_SCENARIOS])
def test_fot_scenario_matrix(scenario: dict[str, object]) -> None:
    engine = FlowOfTimeEngine()

    prev_pack = None
    if scenario.get("use_prev_pack"):
        prev_pack = engine.nub_next(
            prev_nub_exit_pack=None,
            sys_inputs=[{"kind": "input", "source": "user", "payload": {"goal": "first"}}],
        )

    exit_pack = engine.nub_next(
        prev_nub_exit_pack=prev_pack,
        sys_inputs=scenario["sys_inputs"],
    )

    assert exit_pack.state == scenario["expected_state"]
    expected_pointer = scenario.get("expected_pointer")
    if expected_pointer:
        assert expected_pointer in exit_pack.awareness_track.ledger_pointers
