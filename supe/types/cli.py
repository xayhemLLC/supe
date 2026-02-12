"""CLI entrypoints for "supe types".

These are ergonomic, role-style wrappers around the FoT meta-orchestrator demos.
They exist so users can run `supe type backend-engineer ...` instead of `uv run python examples/...`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import click
from rich import box
from rich.console import Console
from rich.table import Table

from supe.types.registry import list_supe_types

console = Console()


def _default_company() -> str:
    return os.getenv("SUPE_COMPANY", "Acme")


def _default_developer() -> str:
    return os.getenv("SUPE_DEVELOPER", os.getenv("USER", "backend-dev"))


@click.group(name="type")
def type_group() -> None:
    """Run a role-style "supe type" workflow (backend engineer, PM, gfx designer)."""


@type_group.command("list")
def list_types_cmd() -> None:
    """List available supe types."""
    table = Table(title="Supe Types", box=box.ROUNDED)
    table.add_column("Key", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Description", style="dim")

    for spec in list_supe_types():
        table.add_row(spec.key, spec.title, spec.description)

    console.print(table)


def _emit_summary(summary: dict[str, Any], *, pretty: bool) -> None:
    if pretty:
        console.print_json(json.dumps(summary, sort_keys=True))
    else:
        click.echo(json.dumps(summary, indent=2))


def _exit_for_status(status: str) -> None:
    if status == "completed":
        return
    if status == "hold":
        raise SystemExit(2)
    raise SystemExit(1)


def _approvals_from_flags(
    *,
    deploy_target: str,
    no_peer_review: bool,
    no_human_approval: bool,
    release_manager: bool,
    cto_signoff: bool,
) -> dict[str, bool]:
    approvals: dict[str, bool] = {
        "PeerReviewSignoff": not no_peer_review,
        "HumanApprovalGate": not no_human_approval,
    }
    if deploy_target == "prod":
        approvals["ReleaseManagerSignoffIfProd"] = bool(release_manager)
        approvals["role:CTO"] = bool(cto_signoff)
    return approvals


def _run_company_team_objective(
    *,
    company: str,
    developer: str,
    profile: str,
    workspace: str,
    objective: str,
    team_key: str,
    deploy_target: str,
    query_limit: int,
    include_git: bool,
    include_jira: bool,
    include_notion: bool,
    include_discord: bool,
    include_web: bool,
    web_urls: tuple[str, ...],
    approvals: dict[str, bool],
    pretty: bool,
) -> None:
    from teams.meta_orchestrator import DeveloperTeam, DeveloperTeamFactory
    from teams.meta_orchestrator.daily_backend_loop import (
        DailyBackendLoopConfig,
        build_daily_backend_sys_inputs,
        summarize_daily_backend_result,
    )

    team_set = DeveloperTeamFactory.build_company_team_set(
        profile=profile,
        company_name=company,
        developer_name=developer,
        workspace=workspace,
    )
    blueprint = team_set.teams[team_key]
    team = DeveloperTeam(blueprint)

    sys_inputs = build_daily_backend_sys_inputs(
        DailyBackendLoopConfig(
            company_name=company,
            developer_name=developer,
            profile=profile,
            workspace=workspace,
            objective=objective,
            deploy_target=deploy_target,
            include_git=include_git,
            include_jira=include_jira,
            include_notion=include_notion,
            include_discord=include_discord,
            include_web=include_web,
            web_urls=list(web_urls),
            query_limit=max(1, int(query_limit)),
            approvals=approvals,
        )
    )

    result = team.run_objective(
        objective,
        sys_inputs=sys_inputs,
        approvals=approvals,
        extra_context={"workspace": workspace, "deploy_target": deploy_target},
    )
    summary = summarize_daily_backend_result(result)
    _emit_summary(summary, pretty=pretty)
    _exit_for_status(result.status)


@type_group.command("backend-engineer")
@click.option("--company", default=_default_company, show_default="env:SUPE_COMPANY|Acme")
@click.option("--developer", default=_default_developer, show_default="env:SUPE_DEVELOPER|$USER")
@click.option(
    "--profile",
    type=click.Choice(["startup", "growth", "enterprise", "agency", "open_source"]),
    default="startup",
)
@click.option("--workspace", default=lambda: str(Path.cwd()))
@click.option("--objective", required=True)
@click.option("--ticket", default="")
@click.option("--deploy-target", type=click.Choice(["staging", "prod"]), default="staging")
@click.option("--execute-command", default="git status --short")
@click.option("--validate-command", default="uv run pytest -q tests/test_meta_orchestrator.py")
@click.option("--run-commands", is_flag=True, help="Run execute/validate commands via Tascer proofs")
@click.option("--query-limit", type=int, default=5)
@click.option("--no-git", is_flag=True, help="Disable git input source")
@click.option("--no-jira", is_flag=True, help="Disable jira input source")
@click.option("--with-notion", is_flag=True, help="Enable notion input source")
@click.option("--with-discord", is_flag=True, help="Enable discord input source")
@click.option("--with-web", is_flag=True, help="Enable web input source")
@click.option("--web-url", multiple=True, help="Web URL to fetch (repeatable)")
@click.option("--no-peer-review", is_flag=True, help="Disable peer review approval")
@click.option("--no-human-approval", is_flag=True, help="Disable human approval gate")
@click.option("--release-manager", is_flag=True, help="Set production release manager signoff to true")
@click.option("--cto-signoff", is_flag=True, help="Set production CTO role signoff to true")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON via rich")
def backend_engineer_cmd(
    company: str,
    developer: str,
    profile: str,
    workspace: str,
    objective: str,
    ticket: str,
    deploy_target: str,
    execute_command: str,
    validate_command: str,
    run_commands: bool,
    query_limit: int,
    no_git: bool,
    no_jira: bool,
    with_notion: bool,
    with_discord: bool,
    with_web: bool,
    web_url: tuple[str, ...],
    no_peer_review: bool,
    no_human_approval: bool,
    release_manager: bool,
    cto_signoff: bool,
    pretty: bool,
) -> None:
    """Run the daily backend developer loop."""
    from teams.meta_orchestrator.daily_backend_loop import (
        DailyBackendLoopConfig,
        run_daily_backend_loop,
        summarize_daily_backend_result,
    )

    approvals = _approvals_from_flags(
        deploy_target=deploy_target,
        no_peer_review=no_peer_review,
        no_human_approval=no_human_approval,
        release_manager=release_manager,
        cto_signoff=cto_signoff,
    )

    config = DailyBackendLoopConfig(
        company_name=company,
        developer_name=developer,
        profile=profile,
        workspace=workspace,
        objective=objective,
        ticket_key=ticket or None,
        deploy_target=deploy_target,
        execute_command=execute_command,
        validate_command=validate_command,
        run_commands=run_commands,
        include_git=not no_git,
        include_jira=not no_jira,
        include_notion=bool(with_notion),
        include_discord=bool(with_discord),
        include_web=bool(with_web),
        web_urls=list(web_url),
        query_limit=max(1, int(query_limit)),
        approvals=approvals,
    )

    result = run_daily_backend_loop(config)
    summary = summarize_daily_backend_result(result)
    _emit_summary(summary, pretty=pretty)
    _exit_for_status(result.status)


@type_group.command("qa-engineer")
@click.option("--company", default=_default_company, show_default="env:SUPE_COMPANY|Acme")
@click.option("--developer", default=_default_developer, show_default="env:SUPE_DEVELOPER|$USER")
@click.option(
    "--profile",
    type=click.Choice(["startup", "growth", "enterprise", "agency", "open_source"]),
    default="startup",
)
@click.option("--workspace", default=lambda: str(Path.cwd()))
@click.option("--objective", required=True)
@click.option("--ticket", default="")
@click.option("--deploy-target", type=click.Choice(["staging", "prod"]), default="staging")
@click.option("--validate-command", default="uv run pytest -q")
@click.option("--run-commands", is_flag=True, help="Run validate command via Tascer proofs")
@click.option("--query-limit", type=int, default=5)
@click.option("--no-git", is_flag=True, help="Disable git input source")
@click.option("--no-jira", is_flag=True, help="Disable jira input source")
@click.option("--with-notion", is_flag=True, help="Enable notion input source")
@click.option("--with-discord", is_flag=True, help="Enable discord input source")
@click.option("--with-web", is_flag=True, help="Enable web input source")
@click.option("--web-url", multiple=True, help="Web URL to fetch (repeatable)")
@click.option("--no-peer-review", is_flag=True, help="Disable peer review approval")
@click.option("--no-human-approval", is_flag=True, help="Disable human approval gate")
@click.option("--release-manager", is_flag=True, help="Set production release manager signoff to true")
@click.option("--cto-signoff", is_flag=True, help="Set production CTO role signoff to true")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON via rich")
def qa_engineer_cmd(
    company: str,
    developer: str,
    profile: str,
    workspace: str,
    objective: str,
    ticket: str,
    deploy_target: str,
    validate_command: str,
    run_commands: bool,
    query_limit: int,
    no_git: bool,
    no_jira: bool,
    with_notion: bool,
    with_discord: bool,
    with_web: bool,
    web_url: tuple[str, ...],
    no_peer_review: bool,
    no_human_approval: bool,
    release_manager: bool,
    cto_signoff: bool,
    pretty: bool,
) -> None:
    """Run a QA-first loop (validation and release readiness)."""
    from teams.meta_orchestrator.daily_backend_loop import (
        DailyBackendLoopConfig,
        run_daily_backend_loop,
        summarize_daily_backend_result,
    )

    approvals = _approvals_from_flags(
        deploy_target=deploy_target,
        no_peer_review=no_peer_review,
        no_human_approval=no_human_approval,
        release_manager=release_manager,
        cto_signoff=cto_signoff,
    )

    config = DailyBackendLoopConfig(
        company_name=company,
        developer_name=developer,
        profile=profile,
        workspace=workspace,
        objective=objective,
        ticket_key=ticket or None,
        deploy_target=deploy_target,
        execute_command="",
        validate_command=validate_command,
        run_commands=run_commands,
        include_git=not no_git,
        include_jira=not no_jira,
        include_notion=bool(with_notion),
        include_discord=bool(with_discord),
        include_web=bool(with_web),
        web_urls=list(web_url),
        query_limit=max(1, int(query_limit)),
        approvals=approvals,
    )

    result = run_daily_backend_loop(config)
    summary = summarize_daily_backend_result(result)
    _emit_summary(summary, pretty=pretty)
    _exit_for_status(result.status)


@type_group.command("pm")
@click.option("--company", default=_default_company, show_default="env:SUPE_COMPANY|Acme")
@click.option("--developer", default=_default_developer, show_default="env:SUPE_DEVELOPER|$USER")
@click.option(
    "--profile",
    type=click.Choice(["startup", "growth", "enterprise", "agency", "open_source"]),
    default="growth",
)
@click.option("--workspace", default=lambda: str(Path.cwd()))
@click.option("--objective", required=True)
@click.option("--deploy-target", type=click.Choice(["staging", "prod"]), default="staging")
@click.option("--query-limit", type=int, default=5)
@click.option("--no-jira", is_flag=True, help="Disable jira input source")
@click.option("--with-notion", is_flag=True, help="Enable notion input source")
@click.option("--with-web", is_flag=True, help="Enable web input source")
@click.option("--web-url", multiple=True, help="Web URL to fetch (repeatable)")
@click.option("--no-peer-review", is_flag=True, help="Disable peer review approval")
@click.option("--no-human-approval", is_flag=True, help="Disable human approval gate")
@click.option("--release-manager", is_flag=True, help="Set production release manager signoff to true")
@click.option("--cto-signoff", is_flag=True, help="Set production CTO role signoff to true")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON via rich")
def pm_cmd(
    company: str,
    developer: str,
    profile: str,
    workspace: str,
    objective: str,
    deploy_target: str,
    query_limit: int,
    no_jira: bool,
    with_notion: bool,
    with_web: bool,
    web_url: tuple[str, ...],
    no_peer_review: bool,
    no_human_approval: bool,
    release_manager: bool,
    cto_signoff: bool,
    pretty: bool,
) -> None:
    """Run a PM-style objective synthesis loop (company guidance team)."""
    approvals = _approvals_from_flags(
        deploy_target=deploy_target,
        no_peer_review=no_peer_review,
        no_human_approval=no_human_approval,
        release_manager=release_manager,
        cto_signoff=cto_signoff,
    )
    _run_company_team_objective(
        company=company,
        developer=developer,
        profile=profile,
        workspace=workspace,
        objective=objective,
        team_key="company_guidance",
        deploy_target=deploy_target,
        query_limit=query_limit,
        include_git=False,
        include_jira=not no_jira,
        include_notion=bool(with_notion),
        include_discord=False,
        include_web=bool(with_web),
        web_urls=web_url,
        approvals=approvals,
        pretty=pretty,
    )


@type_group.command("staff-engineer")
@click.option("--company", default=_default_company, show_default="env:SUPE_COMPANY|Acme")
@click.option("--developer", default=_default_developer, show_default="env:SUPE_DEVELOPER|$USER")
@click.option(
    "--profile",
    type=click.Choice(["startup", "growth", "enterprise", "agency", "open_source"]),
    default="growth",
)
@click.option("--workspace", default=lambda: str(Path.cwd()))
@click.option("--objective", required=True)
@click.option("--deploy-target", type=click.Choice(["staging", "prod"]), default="staging")
@click.option("--query-limit", type=int, default=5)
@click.option("--no-git", is_flag=True, help="Disable git input source")
@click.option("--no-jira", is_flag=True, help="Disable jira input source")
@click.option("--with-notion", is_flag=True, help="Enable notion input source")
@click.option("--with-discord", is_flag=True, help="Enable discord input source")
@click.option("--with-web", is_flag=True, help="Enable web input source")
@click.option("--web-url", multiple=True, help="Web URL to fetch (repeatable)")
@click.option("--no-peer-review", is_flag=True, help="Disable peer review approval")
@click.option("--no-human-approval", is_flag=True, help="Disable human approval gate")
@click.option("--release-manager", is_flag=True, help="Set production release manager signoff to true")
@click.option("--cto-signoff", is_flag=True, help="Set production CTO role signoff to true")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON via rich")
def staff_engineer_cmd(
    company: str,
    developer: str,
    profile: str,
    workspace: str,
    objective: str,
    deploy_target: str,
    query_limit: int,
    no_git: bool,
    no_jira: bool,
    with_notion: bool,
    with_discord: bool,
    with_web: bool,
    web_url: tuple[str, ...],
    no_peer_review: bool,
    no_human_approval: bool,
    release_manager: bool,
    cto_signoff: bool,
    pretty: bool,
) -> None:
    """Run a staff-engineer style loop (architecture and technical direction)."""
    approvals = _approvals_from_flags(
        deploy_target=deploy_target,
        no_peer_review=no_peer_review,
        no_human_approval=no_human_approval,
        release_manager=release_manager,
        cto_signoff=cto_signoff,
    )
    _run_company_team_objective(
        company=company,
        developer=developer,
        profile=profile,
        workspace=workspace,
        objective=objective,
        team_key="company_guidance",
        deploy_target=deploy_target,
        query_limit=query_limit,
        include_git=not no_git,
        include_jira=not no_jira,
        include_notion=bool(with_notion),
        include_discord=bool(with_discord),
        include_web=bool(with_web),
        web_urls=web_url,
        approvals=approvals,
        pretty=pretty,
    )


@type_group.command("sre")
@click.option("--company", default=_default_company, show_default="env:SUPE_COMPANY|Acme")
@click.option("--developer", default=_default_developer, show_default="env:SUPE_DEVELOPER|$USER")
@click.option(
    "--profile",
    type=click.Choice(["startup", "growth", "enterprise", "agency", "open_source"]),
    default="growth",
)
@click.option("--workspace", default=lambda: str(Path.cwd()))
@click.option("--objective", required=True)
@click.option("--deploy-target", type=click.Choice(["staging", "prod"]), default="staging")
@click.option("--query-limit", type=int, default=5)
@click.option("--no-git", is_flag=True, help="Disable git input source")
@click.option("--no-jira", is_flag=True, help="Disable jira input source")
@click.option("--with-notion", is_flag=True, help="Enable notion input source")
@click.option("--with-discord", is_flag=True, help="Enable discord input source")
@click.option("--with-web", is_flag=True, help="Enable web input source")
@click.option("--web-url", multiple=True, help="Web URL to fetch (repeatable)")
@click.option("--no-peer-review", is_flag=True, help="Disable peer review approval")
@click.option("--no-human-approval", is_flag=True, help="Disable human approval gate")
@click.option("--release-manager", is_flag=True, help="Set production release manager signoff to true")
@click.option("--cto-signoff", is_flag=True, help="Set production CTO role signoff to true")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON via rich")
def sre_cmd(
    company: str,
    developer: str,
    profile: str,
    workspace: str,
    objective: str,
    deploy_target: str,
    query_limit: int,
    no_git: bool,
    no_jira: bool,
    with_notion: bool,
    with_discord: bool,
    with_web: bool,
    web_url: tuple[str, ...],
    no_peer_review: bool,
    no_human_approval: bool,
    release_manager: bool,
    cto_signoff: bool,
    pretty: bool,
) -> None:
    """Run an SRE-style reliability loop."""
    approvals = _approvals_from_flags(
        deploy_target=deploy_target,
        no_peer_review=no_peer_review,
        no_human_approval=no_human_approval,
        release_manager=release_manager,
        cto_signoff=cto_signoff,
    )
    _run_company_team_objective(
        company=company,
        developer=developer,
        profile=profile,
        workspace=workspace,
        objective=objective,
        team_key="company_guidance",
        deploy_target=deploy_target,
        query_limit=query_limit,
        include_git=not no_git,
        include_jira=not no_jira,
        include_notion=bool(with_notion),
        include_discord=bool(with_discord),
        include_web=bool(with_web),
        web_urls=web_url,
        approvals=approvals,
        pretty=pretty,
    )


@type_group.command("security-reviewer")
@click.option("--company", default=_default_company, show_default="env:SUPE_COMPANY|Acme")
@click.option("--developer", default=_default_developer, show_default="env:SUPE_DEVELOPER|$USER")
@click.option(
    "--profile",
    type=click.Choice(["startup", "growth", "enterprise", "agency", "open_source"]),
    default="enterprise",
)
@click.option("--workspace", default=lambda: str(Path.cwd()))
@click.option("--objective", required=True)
@click.option("--deploy-target", type=click.Choice(["staging", "prod"]), default="staging")
@click.option("--query-limit", type=int, default=5)
@click.option("--no-git", is_flag=True, help="Disable git input source")
@click.option("--no-jira", is_flag=True, help="Disable jira input source")
@click.option("--with-notion", is_flag=True, help="Enable notion input source")
@click.option("--with-discord", is_flag=True, help="Enable discord input source")
@click.option("--with-web", is_flag=True, help="Enable web input source")
@click.option("--web-url", multiple=True, help="Web URL to fetch (repeatable)")
@click.option("--no-peer-review", is_flag=True, help="Disable peer review approval")
@click.option("--no-human-approval", is_flag=True, help="Disable human approval gate")
@click.option("--release-manager", is_flag=True, help="Set production release manager signoff to true")
@click.option("--cto-signoff", is_flag=True, help="Set production CTO role signoff to true")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON via rich")
def security_reviewer_cmd(
    company: str,
    developer: str,
    profile: str,
    workspace: str,
    objective: str,
    deploy_target: str,
    query_limit: int,
    no_git: bool,
    no_jira: bool,
    with_notion: bool,
    with_discord: bool,
    with_web: bool,
    web_url: tuple[str, ...],
    no_peer_review: bool,
    no_human_approval: bool,
    release_manager: bool,
    cto_signoff: bool,
    pretty: bool,
) -> None:
    """Run a security reviewer loop (evidence-driven security/risk triage)."""
    approvals = _approvals_from_flags(
        deploy_target=deploy_target,
        no_peer_review=no_peer_review,
        no_human_approval=no_human_approval,
        release_manager=release_manager,
        cto_signoff=cto_signoff,
    )
    _run_company_team_objective(
        company=company,
        developer=developer,
        profile=profile,
        workspace=workspace,
        objective=objective,
        team_key="company_guidance",
        deploy_target=deploy_target,
        query_limit=query_limit,
        include_git=not no_git,
        include_jira=not no_jira,
        include_notion=bool(with_notion),
        include_discord=bool(with_discord),
        include_web=bool(with_web),
        web_urls=web_url,
        approvals=approvals,
        pretty=pretty,
    )


@type_group.command("release-manager")
@click.option("--company", default=_default_company, show_default="env:SUPE_COMPANY|Acme")
@click.option("--developer", default=_default_developer, show_default="env:SUPE_DEVELOPER|$USER")
@click.option(
    "--profile",
    type=click.Choice(["startup", "growth", "enterprise", "agency", "open_source"]),
    default="enterprise",
)
@click.option("--workspace", default=lambda: str(Path.cwd()))
@click.option("--objective", required=True)
@click.option("--deploy-target", type=click.Choice(["staging", "prod"]), default="staging")
@click.option("--query-limit", type=int, default=5)
@click.option("--no-git", is_flag=True, help="Disable git input source")
@click.option("--no-jira", is_flag=True, help="Disable jira input source")
@click.option("--with-notion", is_flag=True, help="Enable notion input source")
@click.option("--with-discord", is_flag=True, help="Enable discord input source")
@click.option("--with-web", is_flag=True, help="Enable web input source")
@click.option("--web-url", multiple=True, help="Web URL to fetch (repeatable)")
@click.option("--no-peer-review", is_flag=True, help="Disable peer review approval")
@click.option("--no-human-approval", is_flag=True, help="Disable human approval gate")
@click.option("--release-manager", is_flag=True, help="Set production release manager signoff to true")
@click.option("--cto-signoff", is_flag=True, help="Set production CTO role signoff to true")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON via rich")
def release_manager_cmd(
    company: str,
    developer: str,
    profile: str,
    workspace: str,
    objective: str,
    deploy_target: str,
    query_limit: int,
    no_git: bool,
    no_jira: bool,
    with_notion: bool,
    with_discord: bool,
    with_web: bool,
    web_url: tuple[str, ...],
    no_peer_review: bool,
    no_human_approval: bool,
    release_manager: bool,
    cto_signoff: bool,
    pretty: bool,
) -> None:
    """Run a release manager loop (release readiness and signoffs)."""
    approvals = _approvals_from_flags(
        deploy_target=deploy_target,
        no_peer_review=no_peer_review,
        no_human_approval=no_human_approval,
        release_manager=release_manager,
        cto_signoff=cto_signoff,
    )
    _run_company_team_objective(
        company=company,
        developer=developer,
        profile=profile,
        workspace=workspace,
        objective=objective,
        team_key="company_guidance",
        deploy_target=deploy_target,
        query_limit=query_limit,
        include_git=not no_git,
        include_jira=not no_jira,
        include_notion=bool(with_notion),
        include_discord=bool(with_discord),
        include_web=bool(with_web),
        web_urls=web_url,
        approvals=approvals,
        pretty=pretty,
    )


@type_group.command("gfx-designer")
@click.option("--company", default=_default_company, show_default="env:SUPE_COMPANY|Acme")
@click.option("--developer", default=_default_developer, show_default="env:SUPE_DEVELOPER|$USER")
@click.option(
    "--profile",
    type=click.Choice(["startup", "growth", "enterprise", "agency", "open_source"]),
    default="growth",
)
@click.option("--workspace", default=lambda: str(Path.cwd()))
@click.option("--objective", required=True)
@click.option("--deploy-target", type=click.Choice(["staging", "prod"]), default="staging")
@click.option("--query-limit", type=int, default=5)
@click.option("--no-git", is_flag=True, help="Disable git input source")
@click.option("--no-jira", is_flag=True, help="Disable jira input source")
@click.option("--with-notion", is_flag=True, help="Enable notion input source")
@click.option("--with-discord", is_flag=True, help="Enable discord input source")
@click.option("--with-web", is_flag=True, help="Enable web input source")
@click.option("--web-url", multiple=True, help="Web URL to fetch (repeatable)")
@click.option("--no-peer-review", is_flag=True, help="Disable peer review approval")
@click.option("--no-human-approval", is_flag=True, help="Disable human approval gate")
@click.option("--release-manager", is_flag=True, help="Set production release manager signoff to true")
@click.option("--cto-signoff", is_flag=True, help="Set production CTO role signoff to true")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON via rich")
def gfx_designer_cmd(
    company: str,
    developer: str,
    profile: str,
    workspace: str,
    objective: str,
    deploy_target: str,
    query_limit: int,
    no_git: bool,
    no_jira: bool,
    with_notion: bool,
    with_discord: bool,
    with_web: bool,
    web_url: tuple[str, ...],
    no_peer_review: bool,
    no_human_approval: bool,
    release_manager: bool,
    cto_signoff: bool,
    pretty: bool,
) -> None:
    """Run a gfx-designer style loop (gfx agent lab team)."""
    approvals = _approvals_from_flags(
        deploy_target=deploy_target,
        no_peer_review=no_peer_review,
        no_human_approval=no_human_approval,
        release_manager=release_manager,
        cto_signoff=cto_signoff,
    )
    _run_company_team_objective(
        company=company,
        developer=developer,
        profile=profile,
        workspace=workspace,
        objective=objective,
        team_key="gfx_subagent_design",
        deploy_target=deploy_target,
        query_limit=query_limit,
        include_git=not no_git,
        include_jira=not no_jira,
        include_notion=bool(with_notion),
        include_discord=bool(with_discord),
        include_web=bool(with_web),
        web_urls=web_url,
        approvals=approvals,
        pretty=pretty,
    )


@type_group.command("founder")
@click.option("--company", default=_default_company, show_default="env:SUPE_COMPANY|Acme")
@click.option("--developer", default=_default_developer, show_default="env:SUPE_DEVELOPER|$USER")
@click.option(
    "--profile",
    type=click.Choice(["startup", "growth", "enterprise", "agency", "open_source"]),
    default="startup",
)
@click.option("--workspace", default=lambda: str(Path.cwd()))
@click.option("--objective", required=True)
@click.option("--deploy-target", type=click.Choice(["staging", "prod"]), default="staging")
@click.option("--query-limit", type=int, default=5)
@click.option("--no-jira", is_flag=True, help="Disable jira input source")
@click.option("--with-notion", is_flag=True, help="Enable notion input source")
@click.option("--with-discord", is_flag=True, help="Enable discord input source")
@click.option("--with-web", is_flag=True, help="Enable web input source")
@click.option("--web-url", multiple=True, help="Web URL to fetch (repeatable)")
@click.option("--no-peer-review", is_flag=True, help="Disable peer review approval")
@click.option("--no-human-approval", is_flag=True, help="Disable human approval gate")
@click.option("--release-manager", is_flag=True, help="Set production release manager signoff to true")
@click.option("--cto-signoff", is_flag=True, help="Set production CTO role signoff to true")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON via rich")
def founder_cmd(
    company: str,
    developer: str,
    profile: str,
    workspace: str,
    objective: str,
    deploy_target: str,
    query_limit: int,
    no_jira: bool,
    with_notion: bool,
    with_discord: bool,
    with_web: bool,
    web_url: tuple[str, ...],
    no_peer_review: bool,
    no_human_approval: bool,
    release_manager: bool,
    cto_signoff: bool,
    pretty: bool,
) -> None:
    """Run a founder loop (priorities, constraints, decisions, next actions)."""
    approvals = _approvals_from_flags(
        deploy_target=deploy_target,
        no_peer_review=no_peer_review,
        no_human_approval=no_human_approval,
        release_manager=release_manager,
        cto_signoff=cto_signoff,
    )
    _run_company_team_objective(
        company=company,
        developer=developer,
        profile=profile,
        workspace=workspace,
        objective=objective,
        team_key="company_guidance",
        deploy_target=deploy_target,
        query_limit=query_limit,
        include_git=False,
        include_jira=not no_jira,
        include_notion=bool(with_notion),
        include_discord=bool(with_discord),
        include_web=bool(with_web),
        web_urls=web_url,
        approvals=approvals,
        pretty=pretty,
    )
