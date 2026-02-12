"""Walkthrough demo for org pillars, team pillars, and individual backend dev loops."""

from __future__ import annotations

import json
from pathlib import Path

from teams.meta_orchestrator import OrgHierarchyRunner


def _print_result(title: str, result, signal) -> None:
    print(f"\n{title}")
    print(f"Status: {result.status}")
    if result.pillar_results:
        final_pack = result.pillar_results[-1].fot_exit_pack
        print("Awareness:")
        print(json.dumps(final_pack.awareness_track.__dict__, indent=2))
        print("Execution:")
        print(json.dumps(final_pack.execution_track.__dict__, indent=2))
    print("Signal:")
    print(json.dumps(signal.__dict__, indent=2))


def main() -> None:
    runner = OrgHierarchyRunner.from_profile(
        profile="growth",
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
    )

    # 1) Core org pillar with subteams for different flows.
    core_result, core_signal = runner.run_core_org_pillar(
        pillar_name="ORG_DELIVERY_AND_RELIABILITY",
        objective="Define cross-team delivery + reliability policy for the next release train",
    )
    _print_result("1) CORE ORG PILLAR", core_result, core_signal)

    backend_team_result, backend_team_signal = runner.run_team_pillar(
        team_key="startup_backend_dev",
        parent_pillar=core_signal,
        team_pillar_name="TEAM_BACKEND_DELIVERY_FLOW",
        team_objective="Translate org policy into backend API rollout and validation flow",
    )
    _print_result("1a) BACKEND TEAM SUBFLOW", backend_team_result, backend_team_signal)

    gfx_team_result, gfx_team_signal = runner.run_team_pillar(
        team_key="gfx_subagent_design",
        parent_pillar=core_signal,
        team_pillar_name="TEAM_GFX_AGENT_FLOW",
        team_objective="Translate org policy into gfx subagent architecture and interface constraints",
    )
    _print_result("1b) GFX TEAM SUBFLOW", gfx_team_result, gfx_team_signal)

    # 2) Team interacting with parent/core pillar + own team pillar + team roles.
    print("\n2) TEAM ROLE INTERACTION")
    print("Backend team roles:")
    for member in runner.teams["startup_backend_dev"].blueprint.members:
        print(f"- {member.role}: {member.focus} | tools={', '.join(member.tools)}")

    print("GFX team roles:")
    for member in runner.teams["gfx_subagent_design"].blueprint.members:
        print(f"- {member.role}: {member.focus} | tools={', '.join(member.tools)}")

    # 3) Individual backend dev interaction with core + team pillars.
    indiv_result, indiv_signal = runner.run_individual_backend_dev(
        developer_alias="chris",
        core_pillar=core_signal,
        team_pillar=backend_team_signal,
        personal_pillar_name="INDIVIDUAL_BACKEND_EXECUTION_PILLAR",
        objective="Implement and validate the highest-priority backend item from team flow",
    )
    _print_result("3) INDIVIDUAL BACKEND DEV LOOP", indiv_result, indiv_signal)

    print("\nHierarchy chain summary:")
    print(f"core signal sid: {core_signal.sid}")
    print(f"backend team signal sid: {backend_team_signal.sid}")
    print(f"gfx team signal sid: {gfx_team_signal.sid}")
    print(f"individual signal sid: {indiv_signal.sid}")


if __name__ == "__main__":
    main()
