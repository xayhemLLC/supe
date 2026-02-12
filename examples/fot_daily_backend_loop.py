"""CLI for running a practical daily backend loop."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from teams.meta_orchestrator.daily_backend_loop import (
    DailyBackendLoopConfig,
    run_daily_backend_loop,
    summarize_daily_backend_result,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a daily backend loop via FoT teams")
    parser.add_argument("--company", default="Acme", help="Company name used for team blueprints")
    parser.add_argument("--developer", default="backend-dev", help="Developer name/alias")
    parser.add_argument("--profile", default="startup", help="Company profile: startup/growth/enterprise/agency/open_source")
    parser.add_argument("--workspace", default=str(Path.cwd()), help="Workspace/repo path")
    parser.add_argument("--objective", required=True, help="Main daily objective")
    parser.add_argument("--ticket", default="", help="Primary ticket key (example: API-123)")
    parser.add_argument("--deploy-target", default="staging", choices=("staging", "prod"), help="Deployment target")
    parser.add_argument("--execute-command", default="git status --short", help="Command for Execute op")
    parser.add_argument(
        "--validate-command",
        default="uv run pytest -q tests/test_meta_orchestrator.py",
        help="Command for Validate op",
    )
    parser.add_argument("--run-commands", action="store_true", help="Run execute/validate via Tascer proofs")
    parser.add_argument("--query-limit", type=int, default=5, help="Ledger query limit per source")
    parser.add_argument("--no-git", action="store_true", help="Disable git input source")
    parser.add_argument("--no-jira", action="store_true", help="Disable jira input source")
    parser.add_argument("--with-notion", action="store_true", help="Enable notion input source")
    parser.add_argument("--with-discord", action="store_true", help="Enable discord input source")
    parser.add_argument("--with-web", action="store_true", help="Enable web input source")
    parser.add_argument("--web-url", action="append", default=[], help="Web URL to fetch (repeatable)")
    parser.add_argument("--no-peer-review", action="store_true", help="Disable peer review approval")
    parser.add_argument("--no-human-approval", action="store_true", help="Disable human approval gate")
    parser.add_argument("--release-manager", action="store_true", help="Set production release manager signoff to true")
    parser.add_argument("--cto-signoff", action="store_true", help="Set production CTO role signoff to true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    approvals = {
        "PeerReviewSignoff": not args.no_peer_review,
        "HumanApprovalGate": not args.no_human_approval,
    }
    if args.deploy_target == "prod":
        approvals["ReleaseManagerSignoffIfProd"] = bool(args.release_manager)
        approvals["role:CTO"] = bool(args.cto_signoff)

    config = DailyBackendLoopConfig(
        company_name=args.company,
        developer_name=args.developer,
        profile=args.profile,
        workspace=args.workspace,
        objective=args.objective,
        ticket_key=args.ticket or None,
        deploy_target=args.deploy_target,
        execute_command=args.execute_command,
        validate_command=args.validate_command,
        run_commands=args.run_commands,
        include_git=not args.no_git,
        include_jira=not args.no_jira,
        include_notion=bool(args.with_notion),
        include_discord=bool(args.with_discord),
        include_web=bool(args.with_web),
        web_urls=list(args.web_url or []),
        query_limit=max(1, args.query_limit),
        approvals=approvals,
    )

    result = run_daily_backend_loop(config)
    summary = summarize_daily_backend_result(result)
    print(json.dumps(summary, indent=2))

    if result.status == "hold":
        sys.exit(2)
    if result.status == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
