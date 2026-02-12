"""Tests for practical daily backend loop configuration and execution."""

from __future__ import annotations

from pathlib import Path

from teams.meta_orchestrator import (
    DailyBackendLoopConfig,
    build_daily_backend_sys_inputs,
    run_daily_backend_loop,
    summarize_daily_backend_result,
)


def test_build_daily_backend_sys_inputs_includes_primary_sources() -> None:
    config = DailyBackendLoopConfig(
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
        objective="Implement API caching policy",
        ticket_key="API-123",
    )

    inputs = build_daily_backend_sys_inputs(config)
    sources = [item["source"] for item in inputs]

    assert "user" in sources
    assert "git" in sources
    assert "jira" in sources

    jira_event = next(item for item in inputs if item["source"] == "jira")
    query_plan = jira_event["payload"]["query_plan"]
    assert query_plan["jql"].startswith("key = API-123")


def test_build_daily_backend_sys_inputs_includes_web_when_enabled() -> None:
    config = DailyBackendLoopConfig(
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
        objective="Check docs",
        include_web=True,
        web_urls=["https://example.com"],
    )

    inputs = build_daily_backend_sys_inputs(config)
    web_event = next(item for item in inputs if item["source"] == "web")
    query_plan = web_event["payload"]["query_plan"]
    assert query_plan["urls"] == ["https://example.com"]


def test_daily_backend_loop_staging_completes() -> None:
    config = DailyBackendLoopConfig(
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
        objective="Ship staging-safe backend patch",
        deploy_target="staging",
    )

    result = run_daily_backend_loop(config)
    summary = summarize_daily_backend_result(result)

    assert result.status == "completed"
    assert summary["status"] == "completed"
    assert summary["hold_reason"] is None


def test_daily_backend_loop_prod_holds_without_release_signoff() -> None:
    config = DailyBackendLoopConfig(
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
        objective="Ship production backend patch",
        deploy_target="prod",
        approvals={
            "PeerReviewSignoff": True,
            "HumanApprovalGate": True,
        },
    )

    result = run_daily_backend_loop(config)
    summary = summarize_daily_backend_result(result)

    assert result.status == "hold"
    assert isinstance(summary["hold_reason"], str)
    assert "ReleaseManagerSignoffIfProd" in summary["hold_reason"]


def test_daily_backend_loop_prod_completes_with_release_signoff() -> None:
    config = DailyBackendLoopConfig(
        company_name="Acme",
        developer_name="chris",
        workspace=str(Path.cwd()),
        objective="Ship production backend patch",
        deploy_target="prod",
        approvals={
            "PeerReviewSignoff": True,
            "HumanApprovalGate": True,
            "ReleaseManagerSignoffIfProd": True,
            "role:CTO": True,
        },
    )

    result = run_daily_backend_loop(config)
    summary = summarize_daily_backend_result(result)

    assert result.status == "completed"
    assert summary["status"] == "completed"
    assert summary["hold_reason"] is None
