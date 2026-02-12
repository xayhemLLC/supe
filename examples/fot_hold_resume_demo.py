"""Demo: FoT hold gate then resume with human approvals."""

from __future__ import annotations

from teams.meta_orchestrator import (
    GoalRequest,
    MetaOrchestratorCompiler,
    MetaOrchestratorExecutor,
    load_bundle,
)


def run_once(approvals: dict[str, bool]) -> tuple[str, str | None]:
    bundle = load_bundle()
    compiler = MetaOrchestratorCompiler(bundle)
    goal = GoalRequest(
        goal="Ship validated backend patch",
        constraints_pack={"objective": "Ship validated backend patch"},
        context={"workspace": ".", "deploy_target": "staging"},
    )

    compiled = compiler.compile_goal(goal)
    executor = MetaOrchestratorExecutor(bundle)
    result = executor.execute(compiled, approvals=approvals)

    hold_reason = None
    if result.pillar_results:
        last = result.pillar_results[-1].fot_exit_pack
        if last.hold_pack is not None:
            hold_reason = last.hold_pack.reason

    return result.status, hold_reason


def main() -> None:
    status_one, hold_reason = run_once(approvals={})
    print(f"Run #1 status: {status_one}")
    if hold_reason:
        print(f"Hold reason: {hold_reason}")

    status_two, hold_reason_two = run_once(
        approvals={
            "PeerReviewSignoff": True,
            "HumanApprovalGate": True,
        }
    )
    print(f"Run #2 status: {status_two}")
    if hold_reason_two:
        print(f"Unexpected hold reason: {hold_reason_two}")


if __name__ == "__main__":
    main()
