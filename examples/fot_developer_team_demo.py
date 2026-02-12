"""Demo: create and run three starter developer teams with FoT."""

from __future__ import annotations

import json
from pathlib import Path

from teams.meta_orchestrator import DeveloperTeam, DeveloperTeamFactory


def run_team(label: str, team: DeveloperTeam) -> None:
    objective = team.blueprint.starter_objectives[0]
    result = team.run_objective(objective)

    print(f"\n[{label}] {team.blueprint.name}")
    print(f"Mission: {team.blueprint.mission}")
    print("Members:")
    for member in team.blueprint.members:
        tools = ", ".join(member.tools)
        print(f"  - {member.role}: {member.focus} ({tools})")

    print(f"Objective: {objective}")
    print(f"Result: {result.status}")

    if result.pillar_results:
        final_pack = result.pillar_results[-1].fot_exit_pack
        summary = {
            "awareness": final_pack.awareness_track.__dict__,
            "execution": final_pack.execution_track.__dict__,
        }
        print(json.dumps(summary, indent=2))


def main() -> None:
    pack = DeveloperTeamFactory.starter_pack(
        company_name="Acme",
        developer_name="backend-dev",
        workspace=str(Path.cwd()),
    )

    teams = {key: DeveloperTeam(value) for key, value in pack.items()}

    run_team("1. Company", teams["company_guidance"])
    run_team("2. Startup Backend", teams["startup_backend_dev"])
    run_team("3. GFX Subagent", teams["gfx_subagent_design"])


if __name__ == "__main__":
    main()
