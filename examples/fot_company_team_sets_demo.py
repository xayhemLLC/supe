"""Demo: run all company profile team sets with one objective per team."""

from __future__ import annotations

from pathlib import Path

from teams.meta_orchestrator import DeveloperTeam, DeveloperTeamFactory


def main() -> None:
    profiles = DeveloperTeamFactory.company_sets(
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
    )

    for profile, team_set in profiles.items():
        print(f"\n[{profile}] {team_set.description}")
        for team_key, blueprint in team_set.teams.items():
            team = DeveloperTeam(blueprint)
            objective = blueprint.starter_objectives[0]
            result = team.run_objective(objective)
            print(f"  - {team_key}: {result.status} | objective='{objective}'")


if __name__ == "__main__":
    main()
