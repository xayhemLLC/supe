"""Practical daily backend loop setup on top of FoT developer teams."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .developer_team import DeveloperTeam, DeveloperTeamFactory
from .executor import MetaOrchestratorExecutor, WorkflowExecutionResult
from .ops_runtime import DryRunCommandExecutor, OpsRuntime, TascerCommandExecutor
from .spec_loader import load_bundle


@dataclass
class DailyBackendLoopConfig:
    """Configuration for one backend developer daily loop run."""

    company_name: str = "Acme"
    developer_name: str = "backend-dev"
    workspace: str = field(default_factory=lambda: str(Path.cwd()))
    profile: str = "startup"
    objective: str = "Deliver today's highest-priority backend ticket safely"
    ticket_key: str | None = None
    deploy_target: str = "staging"
    execute_command: str = "git status --short"
    validate_command: str = "uv run pytest -q tests/test_meta_orchestrator.py"
    run_commands: bool = False
    include_git: bool = True
    include_jira: bool = True
    include_notion: bool = False
    include_discord: bool = False
    include_web: bool = False
    web_urls: list[str] = field(default_factory=list)
    query_limit: int = 5
    approvals: dict[str, bool] = field(default_factory=dict)

    def resolved_approvals(self) -> dict[str, bool]:
        """Resolve approval defaults with deployment-aware production rules."""
        merged = {
            "PeerReviewSignoff": True,
            "HumanApprovalGate": True,
        }
        if self.deploy_target.lower() == "prod":
            merged.update(
                {
                    "ReleaseManagerSignoffIfProd": False,
                    "role:CTO": False,
                }
            )
        merged.update(self.approvals)
        return merged


def build_daily_backend_sys_inputs(config: DailyBackendLoopConfig) -> list[dict[str, Any]]:
    """Build practical daily routing inputs for FoT from common backend sources."""
    inputs: list[dict[str, Any]] = [
        {
            "kind": "input",
            "source": "user",
            "payload": {
                "objective": config.objective,
                "ticket_key": config.ticket_key,
                "deploy_target": config.deploy_target,
            },
        }
    ]

    if config.include_git:
        inputs.append(
            {
                "kind": "input",
                "source": "git",
                "payload": {
                    "goal": config.objective,
                    "query_plan": {
                        "repo_path": config.workspace,
                        "limit": config.query_limit,
                        "include_diff": True,
                    },
                },
            }
        )

    if config.include_jira:
        jira_query_plan: dict[str, Any] = {
            "limit": config.query_limit,
            "jql": "assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC",
        }
        if config.ticket_key:
            jira_query_plan["jql"] = f"key = {config.ticket_key} ORDER BY updated DESC"
            jira_query_plan["items"] = [{"key": config.ticket_key}]
        inputs.append(
            {
                "kind": "input",
                "source": "jira",
                "payload": {
                    "goal": config.objective,
                    "query_plan": jira_query_plan,
                },
            }
        )

    if config.include_notion:
        inputs.append(
            {
                "kind": "input",
                "source": "notion",
                "payload": {
                    "goal": config.objective,
                    "query_plan": {
                        "query": config.objective,
                        "limit": config.query_limit,
                    },
                },
            }
        )

    if config.include_discord:
        inputs.append(
            {
                "kind": "input",
                "source": "discord",
                "payload": {
                    "goal": config.objective,
                    "query_plan": {
                        "limit": config.query_limit,
                    },
                },
            }
        )

    if config.include_web:
        inputs.append(
            {
                "kind": "input",
                "source": "web",
                "payload": {
                    "goal": config.objective,
                    "query_plan": {
                        "urls": list(config.web_urls),
                        "limit": config.query_limit,
                    },
                },
            }
        )

    return inputs


def run_daily_backend_loop(config: DailyBackendLoopConfig) -> WorkflowExecutionResult:
    """Run one full backend daily loop with practical defaults."""
    bundle = load_bundle()
    command_executor = TascerCommandExecutor() if config.run_commands else DryRunCommandExecutor()
    ops_runtime = OpsRuntime(bundle=bundle, command_executor=command_executor)
    executor = MetaOrchestratorExecutor(bundle=bundle, ops_runtime=ops_runtime)

    team_set = DeveloperTeamFactory.build_company_team_set(
        profile=config.profile,
        company_name=config.company_name,
        developer_name=config.developer_name,
        workspace=config.workspace,
    )
    blueprint = deepcopy(team_set.teams["startup_backend_dev"])
    blueprint.default_context.update(
        {
            "workspace": config.workspace,
            "deploy_target": config.deploy_target,
            "execute_command": config.execute_command,
            "validate_command": config.validate_command,
        }
    )
    team = DeveloperTeam(blueprint=blueprint, bundle=bundle, executor=executor)

    sys_inputs = build_daily_backend_sys_inputs(config)
    result = team.run_objective(
        config.objective,
        sys_inputs=sys_inputs,
        approvals=config.resolved_approvals(),
        extra_constraints={
            "objective": config.objective,
            "ticket_key": config.ticket_key,
            "deploy_target": config.deploy_target,
        },
        extra_context={
            "workspace": config.workspace,
            "deploy_target": config.deploy_target,
            "execute_command": config.execute_command,
            "validate_command": config.validate_command,
        },
    )
    return result


def summarize_daily_backend_result(result: WorkflowExecutionResult) -> dict[str, Any]:
    """Return a compact summary payload for terminal output."""
    summary: dict[str, Any] = {
        "workflow": result.workflow_name,
        "status": result.status,
        "pillars": [
            {
                "name": pillar.pillar_name,
                "status": pillar.status,
            }
            for pillar in result.pillar_results
        ],
        "toolforge_requests": len(result.toolforge_requests),
    }

    if not result.pillar_results:
        return summary

    final_pack = result.pillar_results[-1].fot_exit_pack
    summary["awareness"] = final_pack.awareness_track.__dict__
    summary["execution"] = final_pack.execution_track.__dict__
    summary["hold_reason"] = final_pack.hold_pack.reason if final_pack.hold_pack else None
    summary["error"] = final_pack.error_pack.message if final_pack.error_pack else None
    return summary
