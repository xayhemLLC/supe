"""Hierarchy runner for core org pillars, team pillars, and individual loops."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..nubflow.types import new_sid
from .developer_team import CompanyTeamSet, DeveloperTeam, DeveloperTeamFactory
from .executor import WorkflowExecutionResult


@dataclass
class PillarSignal:
    """Compact signal passed between hierarchy layers."""

    scope: str
    pillar_name: str
    objective: str
    decisions: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    provenance: list[str] = field(default_factory=list)
    sid: str = field(default_factory=new_sid)

    def to_input_event(self) -> dict[str, object]:
        return {
            "kind": "input",
            "source": self.scope,
            "payload": {
                "pillar_name": self.pillar_name,
                "objective": self.objective,
                "decisions": self.decisions,
                "next_actions": self.next_actions,
                "artifacts_to_produce": self.artifacts,
                "constraints": self.constraints,
                "provenance": self.provenance,
                "signal_sid": self.sid,
            },
        }


class OrgHierarchyRunner:
    """Run a parent->child pillar chain across company teams."""

    def __init__(self, team_set: CompanyTeamSet) -> None:
        self.team_set = team_set
        self.teams = {key: DeveloperTeam(blueprint) for key, blueprint in team_set.teams.items()}

    @classmethod
    def from_profile(
        cls,
        *,
        profile: str,
        company_name: str,
        developer_name: str,
        workspace: str | None = None,
    ) -> OrgHierarchyRunner:
        base_workspace = workspace or str(Path.cwd())
        team_set = DeveloperTeamFactory.build_company_team_set(
            profile=profile,
            company_name=company_name,
            developer_name=developer_name,
            workspace=base_workspace,
        )
        return cls(team_set)

    def run_core_org_pillar(
        self,
        *,
        pillar_name: str,
        objective: str,
        approvals: dict[str, bool] | None = None,
    ) -> tuple[WorkflowExecutionResult, PillarSignal]:
        """Run an organization-level pillar using company-guidance team."""
        team = self.teams["company_guidance"]
        result = team.run_objective(
            objective,
            approvals=approvals,
            extra_constraints={"core_pillar": pillar_name},
            extra_context={"team_scope": "core_org"},
        )
        signal = self._signal_from_result(
            scope="core_org",
            pillar_name=pillar_name,
            objective=objective,
            result=result,
            provenance=[team.blueprint.name],
        )
        return result, signal

    def run_team_pillar(
        self,
        *,
        team_key: str,
        parent_pillar: PillarSignal,
        team_pillar_name: str,
        team_objective: str,
        approvals: dict[str, bool] | None = None,
        extra_inputs: list[dict[str, object]] | None = None,
    ) -> tuple[WorkflowExecutionResult, PillarSignal]:
        """Run a team-level pillar that consumes one parent pillar signal."""
        if team_key not in self.teams:
            raise KeyError(f"Unknown team_key: {team_key}")

        team = self.teams[team_key]
        sys_inputs = [parent_pillar.to_input_event()]
        if extra_inputs:
            sys_inputs.extend(extra_inputs)

        result = team.run_objective(
            team_objective,
            sys_inputs=sys_inputs,
            approvals=approvals,
            extra_constraints={"parent_pillar": parent_pillar.pillar_name, "team_pillar": team_pillar_name},
            extra_context={"team_scope": f"team:{team_key}", "team_pillar": team_pillar_name},
        )

        signal = self._signal_from_result(
            scope=f"team:{team_key}",
            pillar_name=team_pillar_name,
            objective=team_objective,
            result=result,
            provenance=[parent_pillar.sid, team.blueprint.name],
        )
        return result, signal

    def run_individual_backend_dev(
        self,
        *,
        developer_alias: str,
        core_pillar: PillarSignal,
        team_pillar: PillarSignal,
        personal_pillar_name: str,
        objective: str,
        approvals: dict[str, bool] | None = None,
    ) -> tuple[WorkflowExecutionResult, PillarSignal]:
        """Run an individual backend dev loop using core + team signals."""
        team = self.teams["startup_backend_dev"]
        sys_inputs = [core_pillar.to_input_event(), team_pillar.to_input_event()]
        sys_inputs.append(
            {
                "kind": "input",
                "source": "individual",
                "payload": {
                    "developer": developer_alias,
                    "pillar_name": personal_pillar_name,
                    "objective": objective,
                },
            }
        )

        result = team.run_objective(
            objective,
            sys_inputs=sys_inputs,
            approvals=approvals,
            extra_constraints={
                "developer_alias": developer_alias,
                "personal_pillar": personal_pillar_name,
                "core_pillar": core_pillar.pillar_name,
                "team_pillar": team_pillar.pillar_name,
            },
            extra_context={"team_scope": f"individual:{developer_alias}", "developer_alias": developer_alias},
        )

        signal = self._signal_from_result(
            scope=f"individual:{developer_alias}",
            pillar_name=personal_pillar_name,
            objective=objective,
            result=result,
            provenance=[core_pillar.sid, team_pillar.sid, developer_alias],
        )
        return result, signal

    @staticmethod
    def _signal_from_result(
        *,
        scope: str,
        pillar_name: str,
        objective: str,
        result: WorkflowExecutionResult,
        provenance: list[str],
    ) -> PillarSignal:
        if not result.pillar_results:
            return PillarSignal(scope=scope, pillar_name=pillar_name, objective=objective, provenance=provenance)

        final_pack = result.pillar_results[-1].fot_exit_pack
        awareness = final_pack.awareness_track
        execution = final_pack.execution_track
        return PillarSignal(
            scope=scope,
            pillar_name=pillar_name,
            objective=awareness.objective or objective,
            decisions=list(awareness.decisions),
            next_actions=list(execution.next_actions),
            artifacts=list(execution.artifacts_to_produce),
            constraints=list(awareness.constraints),
            provenance=provenance,
        )
