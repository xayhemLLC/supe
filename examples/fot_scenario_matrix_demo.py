"""Run a broad scenario matrix and print summary outcomes."""

from __future__ import annotations

from pathlib import Path

from teams.meta_orchestrator import DeveloperTeam, DeveloperTeamFactory, OrgHierarchyRunner
from teams.nubflow import FlowOfTimeEngine


def run_team_matrix() -> list[tuple[str, str]]:
    outputs: list[tuple[str, str]] = []
    for profile in ("startup", "growth", "enterprise", "agency", "open_source"):
        team_set = DeveloperTeamFactory.build_company_team_set(
            profile=profile,
            company_name="Acme",
            developer_name="chris",
            workspace=str(Path.cwd()),
        )
        for key, blueprint in team_set.teams.items():
            result = DeveloperTeam(blueprint).run_objective(blueprint.starter_objectives[0])
            outputs.append((f"team:{profile}:{key}", result.status))
    return outputs


def run_hierarchy_matrix() -> list[tuple[str, str]]:
    outputs: list[tuple[str, str]] = []
    for profile in ("startup", "growth", "enterprise", "agency", "open_source"):
        runner = OrgHierarchyRunner.from_profile(
            profile=profile,
            company_name="Acme",
            developer_name="chris",
            workspace=str(Path.cwd()),
        )
        core_result, core_signal = runner.run_core_org_pillar(
            pillar_name="ORG_CORE",
            objective=f"{profile} core objective",
        )
        team_result, team_signal = runner.run_team_pillar(
            team_key="startup_backend_dev",
            parent_pillar=core_signal,
            team_pillar_name="TEAM_BACKEND",
            team_objective=f"{profile} backend objective",
        )
        indiv_result, _ = runner.run_individual_backend_dev(
            developer_alias="chris",
            core_pillar=core_signal,
            team_pillar=team_signal,
            personal_pillar_name="INDIVIDUAL_BACKEND",
            objective=f"{profile} individual objective",
        )
        outputs.extend(
            [
                (f"hierarchy:{profile}:core", core_result.status),
                (f"hierarchy:{profile}:team", team_result.status),
                (f"hierarchy:{profile}:individual", indiv_result.status),
            ]
        )
    return outputs


def run_fot_matrix() -> list[tuple[str, str]]:
    outputs: list[tuple[str, str]] = []
    engine = FlowOfTimeEngine()
    scenarios = {
        "user": [{"kind": "input", "source": "user", "payload": {"objective": "ship"}}],
        "hold": [{"kind": "input", "source": "user", "payload": {"requires_human_signoff": True}}],
        "git": [{"kind": "input", "source": "git", "payload": {"query_plan": {"limit": 2}}}],
        "jira": [{"kind": "input", "source": "jira", "payload": {"query_plan": {"items": [{"k": 1}]}}}],
        "notion": [{"kind": "input", "source": "notion", "payload": {"query_plan": {"pages": [{"id": "x"}]}}}],
        "discord": [{"kind": "input", "source": "discord", "payload": {"query_plan": {"messages": [{"id": "x"}]}}}],
        "web": [{"kind": "input", "source": "web", "payload": {"query_plan": {"urls": []}}}],
    }
    for name, inputs in scenarios.items():
        result = engine.nub_next(prev_nub_exit_pack=None, sys_inputs=inputs)
        outputs.append((f"fot:{name}", result.state.value))
    return outputs


def main() -> None:
    results = []
    results.extend(run_team_matrix())
    results.extend(run_hierarchy_matrix())
    results.extend(run_fot_matrix())

    print("Scenario matrix results:")
    for name, status in results:
        print(f"- {name}: {status}")


if __name__ == "__main__":
    main()
