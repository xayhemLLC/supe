"""Tests for FoT meta-orchestrator compilation and execution."""

from __future__ import annotations

from teams.meta_orchestrator.compiler import MetaOrchestratorCompiler
from teams.meta_orchestrator.executor import (
    ActionExecutionProof,
    MetaOrchestratorExecutor,
    NoopToolLifecycleAdapter,
)
from teams.meta_orchestrator.spec_loader import load_bundle


def test_bundle_loads_with_flow_of_time_name() -> None:
    bundle = load_bundle()
    assert bundle.bundle["version"] == "0.0.0"
    assert bundle.flow_of_time_spec["name"] == "Flow of Time (FoT)"


def test_compile_goal_builds_primary_workflow_instances() -> None:
    bundle = load_bundle()
    compiler = MetaOrchestratorCompiler(bundle)

    compiled = compiler.compile_goal("Implement feature flags")

    assert compiled.workflow.name == "Workflow_BE_Primary"
    assert [pillar.name for pillar in compiled.workflow.pillars] == [
        "INTAKE",
        "PLAN",
        "REVIEW",
        "EXECUTE",
        "VALIDATE",
        "SHIP",
        "OUTTAKE",
    ]
    assert len(compiled.orchestrator_tascs) >= 1


def test_executor_holds_when_required_signoff_missing() -> None:
    bundle = load_bundle()
    compiler = MetaOrchestratorCompiler(bundle)
    compiled = compiler.compile_goal("Deliver API endpoint")

    executor = MetaOrchestratorExecutor(bundle=bundle, lifecycle_adapter=NoopToolLifecycleAdapter())
    result = executor.execute(compiled, approvals={})

    assert result.status == "hold"
    assert result.pillar_results[-1].pillar_name == "PLAN"
    assert result.pillar_results[-1].fot_exit_pack.hold_pack is not None


def test_executor_completes_when_required_approvals_are_present() -> None:
    bundle = load_bundle()
    compiler = MetaOrchestratorCompiler(bundle)
    compiled = compiler.compile_goal("Deliver API endpoint")

    executor = MetaOrchestratorExecutor(bundle=bundle, lifecycle_adapter=NoopToolLifecycleAdapter())
    result = executor.execute(
        compiled,
        approvals={
            "PeerReviewSignoff": True,
            "HumanApprovalGate": True,
        },
    )

    assert result.status == "completed"
    assert len(result.pillar_results) == 7


class FlakyAdapter(NoopToolLifecycleAdapter):
    """Always fail to create repeated pain signals for ToolForge."""

    def run_tasc(self, tasc, goal, context):
        return ActionExecutionProof(
            tasc_sid=tasc.sid,
            tasc_name=tasc.name,
            status="failed",
            outputs={
                "op": "flaky_op",
                "objective": goal.goal,
                "decisions": [f"failed:{tasc.name}"],
                "next_actions": ["retry"],
            },
            message="transient failure",
        )


def test_executor_generates_toolforge_requests_for_repeated_pain() -> None:
    bundle = load_bundle()
    compiler = MetaOrchestratorCompiler(bundle)
    compiled = compiler.compile_goal("Stabilize deployment pipeline")

    executor = MetaOrchestratorExecutor(bundle=bundle, lifecycle_adapter=FlakyAdapter())
    result = executor.execute(
        compiled,
        approvals={
            "PeerReviewSignoff": True,
            "HumanApprovalGate": True,
        },
    )

    assert result.toolforge_requests
    assert any(request.new_template and "failed_flaky_op" in request.new_template for request in result.toolforge_requests)
