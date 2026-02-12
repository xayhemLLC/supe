"""Real-world demo: run FoT meta-orchestrator for a backend delivery workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from teams.meta_orchestrator import (
    DryRunCommandExecutor,
    GoalRequest,
    MetaOrchestratorCompiler,
    MetaOrchestratorExecutor,
    OpsRuntime,
    TascerCommandExecutor,
    load_bundle,
)


def build_executor(run_commands: bool) -> tuple[MetaOrchestratorExecutor, str]:
    bundle = load_bundle()
    command_mode = "tascer" if run_commands else "dry-run"
    command_executor = TascerCommandExecutor() if run_commands else DryRunCommandExecutor()
    ops_runtime = OpsRuntime(bundle, command_executor=command_executor)
    executor = MetaOrchestratorExecutor(bundle=bundle, ops_runtime=ops_runtime)
    return executor, command_mode


def main() -> None:
    parser = argparse.ArgumentParser(description="FoT repo delivery demo")
    parser.add_argument("--run-commands", action="store_true", help="Run execute/validate commands through Tascer")
    args = parser.parse_args()

    workspace = str(Path.cwd())
    goal_text = "Prepare backend release package for the current repository state"

    bundle = load_bundle()
    compiler = MetaOrchestratorCompiler(bundle)
    goal = GoalRequest(
        goal=goal_text,
        constraints_pack={
            "objective": goal_text,
            "stop_when": "release_notes_generated",
        },
        context={
            "workspace": workspace,
            "deploy_target": "staging",
            "dashboard_url": "local://observability",
            "execute_command": "git status --short",
            "validate_command": "uv run pytest -q tests/test_meta_orchestrator.py",
        },
    )

    compiled = compiler.compile_goal(goal)
    executor, mode = build_executor(args.run_commands)

    sys_inputs = [
        {
            "kind": "input",
            "source": "git",
            "payload": {
                "goal": goal_text,
                "query_plan": {
                    "repo_path": workspace,
                    "limit": 5,
                    "include_diff": True,
                },
            },
        },
        {
            "kind": "input",
            "source": "web",
            "payload": {
                "goal": goal_text,
                "query_plan": {
                    "urls": ["https://github.com/openai"],
                    "limit": 1,
                },
            },
        },
    ]

    approvals = {
        "PeerReviewSignoff": True,
        "HumanApprovalGate": True,
    }

    result = executor.execute(compiled, sys_inputs=sys_inputs, approvals=approvals)

    print(f"Mode: {mode}")
    print(f"Workflow: {result.workflow_name}")
    print(f"Status: {result.status}")
    print("Pillar statuses:")
    for item in result.pillar_results:
        print(f"  - {item.pillar_name}: {item.status}")

    if result.pillar_results:
        final_pack = result.pillar_results[-1].fot_exit_pack
        print("\nFinal Awareness Track:")
        print(json.dumps(final_pack.awareness_track.__dict__, indent=2))
        print("\nFinal Execution Track:")
        print(json.dumps(final_pack.execution_track.__dict__, indent=2))

    if result.toolforge_requests:
        print("\nToolForge suggestions:")
        for request in result.toolforge_requests:
            print(f"  - {request.new_template} | {request.new_gate} | {request.new_op}")


if __name__ == "__main__":
    main()
