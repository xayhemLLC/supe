"""Tests for `supe type ...` CLI commands."""

from __future__ import annotations

import json

from click.testing import CliRunner

from supe.cli import cli


def test_supe_type_list_contains_expected_types() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["type", "list"])

    assert result.exit_code == 0
    assert "backend-engineer" in result.output
    assert "qa-engineer" in result.output
    assert "pm" in result.output
    assert "staff-engineer" in result.output
    assert "sre" in result.output
    assert "security-reviewer" in result.output
    assert "release-manager" in result.output
    assert "gfx-designer" in result.output
    assert "founder" in result.output


def test_supe_type_backend_engineer_staging_completes() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "type",
            "backend-engineer",
            "--objective",
            "Implement daily loop test objective",
            "--deploy-target",
            "staging",
            "--no-jira",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "completed"
    assert payload["workflow"] == "Workflow_BE_Primary"


def test_supe_type_backend_engineer_prod_holds_without_release_signoffs() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "type",
            "backend-engineer",
            "--objective",
            "Ship prod patch",
            "--deploy-target",
            "prod",
            "--no-jira",
        ],
    )

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["status"] == "hold"
    assert isinstance(payload.get("hold_reason"), str)


def test_supe_type_backend_engineer_prod_completes_with_release_signoffs() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "type",
            "backend-engineer",
            "--objective",
            "Ship prod patch",
            "--deploy-target",
            "prod",
            "--release-manager",
            "--cto-signoff",
            "--no-jira",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "completed"


def test_supe_type_pm_completes() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "type",
            "pm",
            "--objective",
            "Draft next sprint goals",
            "--no-jira",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "completed"


def test_supe_type_staff_engineer_completes() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "type",
            "staff-engineer",
            "--objective",
            "Review architecture risk",
            "--no-jira",
            "--no-git",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "completed"


def test_supe_type_sre_completes() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "type",
            "sre",
            "--objective",
            "Assess rollout risk and observability",
            "--no-jira",
            "--no-git",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "completed"


def test_supe_type_security_reviewer_completes() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "type",
            "security-reviewer",
            "--objective",
            "Perform security review",
            "--no-jira",
            "--no-git",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "completed"


def test_supe_type_release_manager_completes() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "type",
            "release-manager",
            "--objective",
            "Prepare release readiness report",
            "--no-jira",
            "--no-git",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "completed"


def test_supe_type_founder_completes() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "type",
            "founder",
            "--objective",
            "Set company priorities for the week",
            "--no-jira",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "completed"


def test_supe_type_gfx_designer_completes() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "type",
            "gfx-designer",
            "--objective",
            "Design gfx subagent contract",
            "--no-jira",
            "--no-git",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "completed"
