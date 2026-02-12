"""Exhaustive scenario coverage for FoT + team/hierarchy flows."""

from __future__ import annotations

from itertools import product
from pathlib import Path

import pytest

from teams.meta_orchestrator import DeveloperTeam, DeveloperTeamFactory, OrgHierarchyRunner
from teams.nubflow import (
    Buffer,
    BufferEdge,
    BufferGraph,
    BufferNode,
    BufferStatus,
    FlowOfTimeEngine,
    FoTState,
    NubContext,
    Overlord,
    RouteBounds,
    new_sid,
)
from teams.nubflow.types import LedgerCursor, TransformResult

PROFILES = ("startup", "growth", "enterprise", "agency", "open_source")
TEAM_KEYS = ("company_guidance", "startup_backend_dev", "gfx_subagent_design")
APPROVAL_MODES = ("defaults", "missing_peer", "missing_human", "no_approvals", "missing_release_manager")
DEPLOY_TARGETS = ("staging", "prod")


def _approvals_for_mode(mode: str) -> dict[str, bool] | None:
    if mode == "defaults":
        return None
    if mode == "missing_peer":
        return {
            "PeerReviewSignoff": False,
            "HumanApprovalGate": True,
            "ReleaseManagerSignoffIfProd": True,
            "role:CTO": True,
        }
    if mode == "missing_human":
        return {
            "PeerReviewSignoff": True,
            "HumanApprovalGate": False,
            "ReleaseManagerSignoffIfProd": True,
            "role:CTO": True,
        }
    if mode == "missing_release_manager":
        return {
            "PeerReviewSignoff": True,
            "HumanApprovalGate": True,
            "ReleaseManagerSignoffIfProd": False,
            "role:CTO": False,
        }
    return {
        "PeerReviewSignoff": False,
        "HumanApprovalGate": False,
        "ReleaseManagerSignoffIfProd": False,
        "role:CTO": False,
        "role:PM": False,
    }


def _expected_status(profile: str, mode: str, deploy_target: str) -> str:
    if mode in {"missing_peer", "missing_human", "no_approvals"}:
        return "hold"
    if deploy_target == "prod":
        if mode == "missing_release_manager":
            return "hold"
        if mode == "defaults" and profile != "enterprise":
            return "hold"
    return "completed"


TEAM_MATRIX_SCENARIOS = [
    {
        "profile": profile,
        "team_key": team_key,
        "approval_mode": approval_mode,
        "deploy_target": deploy_target,
    }
    for profile, team_key, approval_mode, deploy_target in product(
        PROFILES,
        TEAM_KEYS,
        APPROVAL_MODES,
        DEPLOY_TARGETS,
    )
]


@pytest.mark.parametrize(
    "scenario",
    TEAM_MATRIX_SCENARIOS,
    ids=[
        f"{scenario['profile']}::{scenario['team_key']}::{scenario['approval_mode']}::{scenario['deploy_target']}"
        for scenario in TEAM_MATRIX_SCENARIOS
    ],
)
def test_exhaustive_team_matrix(scenario: dict[str, str]) -> None:
    profile = scenario["profile"]
    team_key = scenario["team_key"]
    approval_mode = scenario["approval_mode"]
    deploy_target = scenario["deploy_target"]

    team_set = DeveloperTeamFactory.build_company_team_set(
        profile=profile,
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
    )

    blueprint = team_set.teams[team_key]
    team = DeveloperTeam(blueprint)

    result = team.run_objective(
        blueprint.starter_objectives[0],
        approvals=_approvals_for_mode(approval_mode),
        extra_context={"deploy_target": deploy_target},
    )

    expected = _expected_status(profile, approval_mode, deploy_target)
    assert result.status == expected
    if expected == "hold":
        assert result.pillar_results[-1].fot_exit_pack.hold_pack is not None
    else:
        assert result.pillar_results[-1].fot_exit_pack.state == FoTState.EXIT


HIERARCHY_SCENARIOS = [
    {
        "profile": profile,
        "team_key": team_key,
        "approval_mode": approval_mode,
    }
    for profile, team_key, approval_mode in product(
        PROFILES,
        ("startup_backend_dev", "gfx_subagent_design"),
        ("defaults", "missing_peer", "missing_human"),
    )
]


@pytest.mark.parametrize(
    "scenario",
    HIERARCHY_SCENARIOS,
    ids=[
        f"{scenario['profile']}::{scenario['team_key']}::{scenario['approval_mode']}"
        for scenario in HIERARCHY_SCENARIOS
    ],
)
def test_exhaustive_hierarchy_matrix(scenario: dict[str, str]) -> None:
    runner = OrgHierarchyRunner.from_profile(
        profile=scenario["profile"],
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
    )
    approvals = _approvals_for_mode(scenario["approval_mode"])

    core_result, core_signal = runner.run_core_org_pillar(
        pillar_name="ORG_CORE",
        objective=f"{scenario['profile']} core policy",
        approvals=approvals,
    )

    if scenario["approval_mode"] == "defaults":
        assert core_result.status == "completed"
    else:
        assert core_result.status == "hold"

    team_result, team_signal = runner.run_team_pillar(
        team_key=scenario["team_key"],
        parent_pillar=core_signal,
        team_pillar_name="TEAM_FLOW",
        team_objective="Team translation",
        approvals=approvals,
    )

    if scenario["approval_mode"] == "defaults":
        assert team_result.status == "completed"
    else:
        assert team_result.status == "hold"

    indiv_result, indiv_signal = runner.run_individual_backend_dev(
        developer_alias="chris",
        core_pillar=core_signal,
        team_pillar=team_signal,
        personal_pillar_name="INDIVIDUAL_LOOP",
        objective="Personal execution",
        approvals=approvals,
    )

    if scenario["approval_mode"] == "defaults":
        assert indiv_result.status == "completed"
    else:
        assert indiv_result.status == "hold"

    assert core_signal.sid in indiv_signal.provenance
    assert team_signal.sid in indiv_signal.provenance


FOT_SCENARIOS = [
    {
        "id": "user_exit",
        "engine": lambda: FlowOfTimeEngine(),
        "sys_inputs": [{"kind": "input", "source": "user", "payload": {"objective": "ship"}}],
        "expected": FoTState.EXIT,
    },
    {
        "id": "human_hold",
        "engine": lambda: FlowOfTimeEngine(),
        "sys_inputs": [{"kind": "input", "source": "user", "payload": {"requires_human_signoff": True}}],
        "expected": FoTState.HOLD,
    },
    {
        "id": "git_ledger",
        "engine": lambda: FlowOfTimeEngine(),
        "sys_inputs": [{"kind": "input", "source": "git", "payload": {"query_plan": {"limit": 2}}}],
        "expected": FoTState.EXIT,
        "pointer": "git_ledger",
    },
    {
        "id": "jira_ledger",
        "engine": lambda: FlowOfTimeEngine(),
        "sys_inputs": [
            {
                "kind": "input",
                "source": "jira",
                "payload": {"query_plan": {"items": [{"key": "PLAT-1"}], "limit": 1}},
            }
        ],
        "expected": FoTState.EXIT,
        "pointer": "jira_ledger",
    },
    {
        "id": "notion_ledger",
        "engine": lambda: FlowOfTimeEngine(),
        "sys_inputs": [
            {
                "kind": "input",
                "source": "notion",
                "payload": {"query_plan": {"pages": [{"id": "n-1", "title": "Doc"}], "limit": 1}},
            }
        ],
        "expected": FoTState.EXIT,
        "pointer": "notion_ledger",
    },
    {
        "id": "discord_ledger",
        "engine": lambda: FlowOfTimeEngine(),
        "sys_inputs": [
            {
                "kind": "input",
                "source": "discord",
                "payload": {"query_plan": {"messages": [{"id": "1", "content": "hello"}], "limit": 1}},
            }
        ],
        "expected": FoTState.EXIT,
        "pointer": "discord_ledger",
    },
    {
        "id": "web_ledger",
        "engine": lambda: FlowOfTimeEngine(),
        "sys_inputs": [{"kind": "input", "source": "web", "payload": {"query_plan": {"urls": []}}}],
        "expected": FoTState.EXIT,
        "pointer": "web_ledger",
    },
    {
        "id": "routing_budget_error",
        "engine": lambda: FlowOfTimeEngine(route_bounds=RouteBounds(max_hops=12, max_tokens=0, max_ms=8000)),
        "sys_inputs": [{"kind": "input", "source": "user", "payload": {"objective": "ship"}}],
        "expected": FoTState.ERROR,
    },
    {
        "id": "loop_hops_error",
        "engine": lambda: FlowOfTimeEngine(
            buffer_graph=_loop_graph(),
            route_bounds=RouteBounds(max_hops=1, max_tokens=50, max_ms=8000),
        ),
        "sys_inputs": [{"kind": "input", "source": "user", "payload": {"objective": "ship"}}],
        "expected": FoTState.ERROR,
    },
    {
        "id": "transform_error",
        "engine": lambda: _transform_error_engine(),
        "sys_inputs": [{"kind": "input", "source": "user", "payload": {"objective": "ship"}}],
        "expected": FoTState.ERROR,
    },
]


def _loop_graph() -> BufferGraph:
    graph = BufferGraph()
    graph.add_node(BufferNode(name="master_input", kind="input"))
    graph.add_edge(BufferEdge(from_node="master_input", to_node="master_input", max_hops=1, weight=1.0))
    return graph


def _transform_error_engine() -> FlowOfTimeEngine:
    engine = FlowOfTimeEngine()
    node = engine.buffer_graph.node("master_input")
    assert node is not None

    def _raise(*_args, **_kwargs):
        raise RuntimeError("forced_transform_error")

    node.transform = _raise
    return engine


@pytest.mark.parametrize("scenario", FOT_SCENARIOS, ids=[scenario["id"] for scenario in FOT_SCENARIOS])
def test_exhaustive_fot_matrix(scenario: dict[str, object]) -> None:
    engine_factory = scenario["engine"]
    assert callable(engine_factory)
    engine = engine_factory()

    exit_pack = engine.nub_next(prev_nub_exit_pack=None, sys_inputs=scenario["sys_inputs"])
    assert exit_pack.state == scenario["expected"]

    pointer = scenario.get("pointer")
    if pointer:
        assert pointer in exit_pack.awareness_track.ledger_pointers


def _fanout_graph() -> BufferGraph:
    graph = BufferGraph()
    graph.add_node(BufferNode(name="master_input", kind="input"))
    graph.add_node(BufferNode(name="branch", kind="input"))
    graph.add_node(BufferNode(name="overlord_inbox", kind="inbox", is_terminal=True))
    graph.add_node(BufferNode(name="audit_sink", kind="sink", is_terminal=True))
    graph.add_edge(BufferEdge(from_node="master_input", to_node="branch", weight=1.0))
    graph.add_edge(BufferEdge(from_node="branch", to_node="overlord_inbox", condition=lambda *_: True, weight=1.0))
    graph.add_edge(BufferEdge(from_node="branch", to_node="audit_sink", condition=lambda *_: True, weight=0.5))
    return graph


def _condition_exception_graph() -> BufferGraph:
    graph = BufferGraph()
    graph.add_node(BufferNode(name="master_input", kind="input"))
    graph.add_node(BufferNode(name="good_terminal", kind="inbox", is_terminal=True))
    graph.add_node(BufferNode(name="bad_terminal", kind="inbox", is_terminal=True))

    def _boom(*_args, **_kwargs):
        raise RuntimeError("edge_condition_failed")

    graph.add_edge(BufferEdge(from_node="master_input", to_node="bad_terminal", condition=_boom, weight=2.0))
    graph.add_edge(BufferEdge(from_node="master_input", to_node="good_terminal", condition=lambda *_: True, weight=1.0))
    return graph


def _edge_cap_graph() -> BufferGraph:
    graph = BufferGraph()
    graph.add_node(BufferNode(name="master_input", kind="input"))
    graph.add_node(BufferNode(name="next", kind="inbox", is_terminal=True))
    graph.add_edge(BufferEdge(from_node="master_input", to_node="next", max_hops=0, weight=1.0))
    return graph


def _context(*, budget: int, constraints: dict[str, object] | None = None) -> NubContext:
    return NubContext(
        nub_sid=new_sid(),
        start_time="2026-02-12T00:00:00",
        budget=budget,
        constraints=dict(constraints or {}),
    )


def test_fot_budget_exhaustion_marks_skipped_buffers() -> None:
    engine = FlowOfTimeEngine(route_bounds=RouteBounds(max_hops=12, max_tokens=0, max_ms=8000))
    exit_pack = engine.nub_next(
        prev_nub_exit_pack=None,
        sys_inputs=[{"kind": "input", "source": "user", "payload": {"objective": "ship"}}],
    )

    assert exit_pack.state == FoTState.ERROR
    assert any(
        buffer.error == "routing_budget_exhausted" and buffer.status == BufferStatus.SKIPPED
        for buffer in exit_pack.output_buffers
    )


def test_fot_fanout_routes_to_multiple_terminals() -> None:
    engine = FlowOfTimeEngine(buffer_graph=_fanout_graph())
    exit_pack = engine.nub_next(
        prev_nub_exit_pack=None,
        sys_inputs=[{"kind": "input", "source": "user", "payload": {"objective": "ship"}}],
    )

    assert exit_pack.state == FoTState.EXIT
    destinations = {buffer.destination for buffer in exit_pack.output_buffers if buffer.name != "overlord_outbox"}
    assert "overlord_inbox" in destinations
    assert "audit_sink" in destinations


def test_fot_edge_condition_exception_is_ignored() -> None:
    engine = FlowOfTimeEngine(buffer_graph=_condition_exception_graph())
    exit_pack = engine.nub_next(
        prev_nub_exit_pack=None,
        sys_inputs=[{"kind": "input", "source": "user", "payload": {"objective": "ship"}}],
    )

    assert exit_pack.state == FoTState.EXIT
    destinations = {buffer.destination for buffer in exit_pack.output_buffers if buffer.name != "overlord_outbox"}
    assert "good_terminal" in destinations
    assert "bad_terminal" not in destinations


def test_fot_edge_hop_cap_surfaces_error() -> None:
    engine = FlowOfTimeEngine(buffer_graph=_edge_cap_graph())
    exit_pack = engine.nub_next(
        prev_nub_exit_pack=None,
        sys_inputs=[{"kind": "input", "source": "user", "payload": {"objective": "ship"}}],
    )

    assert exit_pack.state == FoTState.ERROR
    assert any(buffer.error == "edge_max_hops_exceeded" for buffer in exit_pack.output_buffers)


def test_fot_transform_not_applicable_pass_through() -> None:
    engine = FlowOfTimeEngine()
    node = engine.buffer_graph.node("master_input")
    assert node is not None

    node.transform = lambda *_: TransformResult(applicable=False, buffers=[])
    exit_pack = engine.nub_next(
        prev_nub_exit_pack=None,
        sys_inputs=[{"kind": "input", "source": "user", "payload": {"objective": "ship"}}],
    )

    assert exit_pack.state == FoTState.EXIT
    assert any(buffer.name == "master_input" and buffer.status == BufferStatus.OK for buffer in exit_pack.output_buffers)


def test_fot_transform_empty_buffer_list_defaults_to_passthrough() -> None:
    engine = FlowOfTimeEngine()
    node = engine.buffer_graph.node("master_input")
    assert node is not None

    node.transform = lambda *_: TransformResult(applicable=True, buffers=[])
    exit_pack = engine.nub_next(
        prev_nub_exit_pack=None,
        sys_inputs=[{"kind": "input", "source": "user", "payload": {"objective": "ship"}}],
    )

    assert exit_pack.state == FoTState.EXIT
    assert any(buffer.name == "master_input" and buffer.status == BufferStatus.OK for buffer in exit_pack.output_buffers)


def test_fot_prev_exit_pack_dict_is_absorbed() -> None:
    engine = FlowOfTimeEngine()
    exit_pack = engine.nub_next(
        prev_nub_exit_pack={"output_buffers": [{"name": "prev", "kind": "outbox", "payload": {"x": 1}}]},
        sys_inputs=None,
    )

    assert exit_pack.state == FoTState.EXIT
    assert any(
        isinstance(buffer.payload, dict) and buffer.payload.get("name") == "prev"
        for buffer in exit_pack.output_buffers
    )


def test_overlord_commit_dedupes_tracks_and_stop_conditions() -> None:
    overlord = Overlord()
    context = _context(
        budget=12,
        constraints={"objective": "Fallback objective", "stop_when": "release_ready", "priority": "p1"},
    )
    context.budget_used = 5

    commit = overlord.commit(
        context=context,
        final_buffers=[
            Buffer(
                name="master_input",
                kind="input",
                payload={
                    "objective": "Ship API",
                    "decisions": ["a", "a", "b"],
                    "constraints": ["latency<100ms"],
                    "next_actions": ["open_pr"],
                    "artifacts_to_produce": ["release_notes"],
                },
                status=BufferStatus.OK,
            ),
            Buffer(
                name="sensory_input",
                kind="input",
                payload={
                    "decisions": ["b", "c"],
                    "constraints_delta": ["latency<100ms", "budget<=2h"],
                    "top_risks": ["rollback_complexity", "rollback_complexity"],
                    "open_questions": ["need_cache_invalidation?"],
                },
                status=BufferStatus.OK,
            ),
        ],
    )

    assert commit.awareness_track.objective == "Ship API"
    assert commit.awareness_track.decisions == ["a", "b", "c"]
    assert "latency<100ms" in commit.awareness_track.constraints
    assert "budget<=2h" in commit.awareness_track.constraints
    assert "priority=p1" in commit.awareness_track.constraints
    assert commit.execution_track.next_actions == ["open_pr"]
    assert commit.execution_track.artifacts_to_produce == ["release_notes"]
    assert commit.execution_track.stop_conditions == ["release_ready"]
    assert commit.execution_track.wip_budget == 7


def test_overlord_commit_collects_cursor_updates_and_query_seeds() -> None:
    overlord = Overlord()
    context = _context(budget=8, constraints={"objective": "Sync ledgers"})

    git_cursor = LedgerCursor(
        ledger_sid="git_sid",
        query_plan={"limit": 9},
        paging_cursor="git-cursor",
    )
    jira_cursor = LedgerCursor(
        ledger_sid="jira_sid",
        query_plan={"jql": "project = PLAT ORDER BY updated DESC"},
        paging_cursor="jira-cursor",
    )

    commit = overlord.commit(
        context=context,
        final_buffers=[
            Buffer(
                name="git_ledger",
                kind="ledger",
                payload={"query_plan": {"limit": 3}},
                status=BufferStatus.OK,
                cursor=git_cursor,
            ),
            Buffer(
                name="jira_ledger",
                kind="ledger",
                payload={},
                status=BufferStatus.OK,
                cursor=jira_cursor,
            ),
        ],
    )

    assert commit.updated_ledger_cursors["git_ledger"].paging_cursor == "git-cursor"
    assert commit.updated_ledger_cursors["jira_ledger"].paging_cursor == "jira-cursor"
    assert commit.next_query_plan_seeds["git_ledger"] == {"limit": 3}
    assert commit.next_query_plan_seeds["jira_ledger"] == {"jql": "project = PLAT ORDER BY updated DESC"}


def test_overlord_commit_propagates_holds_and_errors() -> None:
    overlord = Overlord()
    context = _context(budget=6, constraints={"objective": "Deploy service"})

    commit = overlord.commit(
        context=context,
        final_buffers=[
            Buffer(
                name="master_input",
                kind="input",
                payload={"objective": "Deploy service"},
                status=BufferStatus.OK,
            )
        ],
        hold_reasons=["gate:HumanApprovalGate"],
        error_messages=["transient_failure"],
    )

    assert "hold:gate:HumanApprovalGate" in commit.execution_track.gates_and_signoffs
    assert "retry_failed_buffers" in commit.execution_track.next_actions

    outbox = next(buffer for buffer in commit.output_buffers if buffer.name == "overlord_outbox")
    assert outbox.payload["holds"] == ["gate:HumanApprovalGate"]
    assert outbox.payload["errors"] == ["transient_failure"]


def test_company_team_set_rejects_unknown_profile() -> None:
    with pytest.raises(ValueError):
        DeveloperTeamFactory.build_company_team_set(
            profile="unknown",
            company_name="Acme",
            developer_name="chris",
            workspace=str(Path.cwd()),
        )


def test_hierarchy_runner_rejects_unknown_team_key() -> None:
    runner = OrgHierarchyRunner.from_profile(
        profile="startup",
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
    )
    _, core_signal = runner.run_core_org_pillar(
        pillar_name="ORG_CORE",
        objective="Set startup policy",
    )

    with pytest.raises(KeyError):
        runner.run_team_pillar(
            team_key="unknown_team",
            parent_pillar=core_signal,
            team_pillar_name="TEAM_UNKNOWN",
            team_objective="Should fail",
        )


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("team_key", TEAM_KEYS)
def test_hierarchy_accepts_extra_inputs(profile: str, team_key: str) -> None:
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
        team_key=team_key,
        parent_pillar=core_signal,
        team_pillar_name="TEAM_FLOW",
        team_objective="Translate org objective",
        extra_inputs=[
            {
                "kind": "sensory",
                "source": "ui_snapshot",
                "payload": {
                    "objective": "Visual status",
                    "decisions": ["ui_signal_seen"],
                },
            }
        ],
    )

    assert team_result.status == "completed"
    assert core_signal.sid in team_signal.provenance
