"""Concrete op runtime implementations for YAML-defined meta-orchestrator ops."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Protocol

from ..nubflow.ledgers import LedgerRegistry
from .artifacts import artifact_aliases
from .spec_loader import BundleSpec
from .toolforge import ToolForge


@dataclass
class CommandResult:
    """Normalized command execution result."""

    status: str
    command: str
    exit_code: int
    summary: str
    evidence_paths: list[str]


class CommandExecutor(Protocol):
    """Command execution contract used by Execute/Validate ops."""

    def run(self, *, command: str, cwd: str, tasc_id: str) -> CommandResult:
        """Run a command and return a normalized result."""


class DryRunCommandExecutor:
    """Default command executor that never mutates the system."""

    def run(self, *, command: str, cwd: str, tasc_id: str) -> CommandResult:
        summary = f"dry-run: skipped command '{command}' in {cwd}"
        return CommandResult(
            status="success",
            command=command,
            exit_code=0,
            summary=summary,
            evidence_paths=[],
        )


class TascerCommandExecutor:
    """Execute commands through Tascer's lifecycle runner for proof generation."""

    def __init__(self, *, output_dir: str = "./tascer_output") -> None:
        self.output_dir = output_dir

    def run(self, *, command: str, cwd: str, tasc_id: str) -> CommandResult:
        from tascer.runner import TascRunner

        runner = TascRunner(output_dir=self.output_dir, repo_root=cwd)
        report = runner.run_command(
            tasc_id=tasc_id,
            command=command,
            cwd=cwd,
            timeout_sec=120,
            shell=True,
        )

        return CommandResult(
            status="success" if report.overall_status == "pass" else "failed",
            command=command,
            exit_code=int(report.action_result.op_result) if isinstance(report.action_result.op_result, int) else 1,
            summary=report.summary,
            evidence_paths=list(report.evidence_index.values()),
        )


class OpsRuntime:
    """Data-driven op runtime honoring YAML ``Ops`` contracts."""

    def __init__(
        self,
        bundle: BundleSpec,
        *,
        ledger_registry: LedgerRegistry | None = None,
        command_executor: CommandExecutor | None = None,
        toolforge: ToolForge | None = None,
    ) -> None:
        self.bundle = bundle
        self.ledger_registry = ledger_registry or LedgerRegistry.with_defaults()
        self.command_executor = command_executor or DryRunCommandExecutor()
        self.toolforge = toolforge or ToolForge()

    def run_op(
        self,
        op_name: str,
        *,
        inputs: dict[str, Any],
        goal: str,
        tasc_id: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute one op and return output fields according to contract."""
        op_name = str(op_name)

        if op_name == "Ask":
            outputs = self._op_ask(inputs=inputs, goal=goal)
        elif op_name == "Search":
            outputs = self._op_search(inputs=inputs, goal=goal, context=context)
        elif op_name == "ShaveContext":
            outputs = self._op_shave_context(inputs=inputs, goal=goal)
        elif op_name == "Simplify":
            outputs = self._op_simplify(inputs=inputs)
        elif op_name == "Plan":
            outputs = self._op_plan(inputs=inputs, goal=goal, context=context)
        elif op_name == "Execute":
            outputs = self._op_execute(inputs=inputs, context=context, tasc_id=tasc_id)
        elif op_name == "Validate":
            outputs = self._op_validate(inputs=inputs, context=context, tasc_id=tasc_id)
        elif op_name == "Ship":
            outputs = self._op_ship(inputs=inputs, context=context)
        elif op_name == "Outtake":
            outputs = self._op_outtake(inputs=inputs)
        elif op_name == "ToolForge":
            outputs = self._op_toolforge(inputs=inputs)
        else:
            outputs = {"error": f"unknown_op:{op_name}"}

        return self._apply_contract_defaults(op_name, outputs)

    def _op_ask(self, *, inputs: dict[str, Any], goal: str) -> dict[str, Any]:
        question = str(inputs.get("question") or f"How should we satisfy '{goal}'?")
        constraints = self._as_list(inputs.get("constraints") or inputs.get("constraints_pack"))
        answers = [
            f"Focus scope on goal: {goal}",
            f"Primary question considered: {question}",
        ]
        decisions = self._as_list(inputs.get("decision_log") or inputs.get("decisions"))
        if not decisions:
            decisions = [f"resolve:{question[:80]}"]
        constraints_delta = constraints[:3] or ["no_unbounded_scope"]
        return {
            "answers": answers,
            "decisions": decisions,
            "constraints_delta": constraints_delta,
            "decision_log": decisions,
        }

    def _op_search(self, *, inputs: dict[str, Any], goal: str, context: dict[str, Any]) -> dict[str, Any]:
        query_plan = inputs.get("query_plan") or {"goal": goal, "limit": 5}
        if not isinstance(query_plan, dict):
            query_plan = {"goal": goal, "query": str(query_plan), "limit": 5}

        ledger_kind = str(inputs.get("ledger_kind") or query_plan.get("ledger_kind") or "GitLedger")
        if not ledger_kind.endswith("Ledger"):
            ledger_kind = f"{ledger_kind.capitalize()}Ledger"

        adapter = self.ledger_registry.get(ledger_kind)
        if adapter is None:
            evidence = {
                "ledger_kind": ledger_kind,
                "query_plan": query_plan,
                "items": [],
                "reason": "adapter_not_registered",
            }
            return {
                "evidence_pack": evidence,
                "pointers": [],
                "cursor_delta": {},
                "system_map": {"components": [], "interfaces": []},
            }

        from ..nubflow.types import LedgerCursor

        cursor = LedgerCursor(ledger_sid=adapter.sid, query_plan=query_plan)
        result = adapter.query(query_plan=query_plan, cursor=cursor, budget=int(query_plan.get("limit", 5)))
        summary = adapter.summarize(items=result.items, goal=goal, budget=5)

        cursor_delta = {
            "ledger_sid": adapter.sid,
            "next_cursor": result.next_cursor,
            "last_seen_items": len(result.items),
        }

        system_map = {
            "components": [item.get("component") for item in result.items if isinstance(item, dict) and item.get("component")],
            "interfaces": [item.get("interface") for item in result.items if isinstance(item, dict) and item.get("interface")],
            "summary": summary.summary_artifact,
        }

        return {
            "evidence_pack": result.evidence_pack,
            "pointers": summary.pointers,
            "cursor_delta": cursor_delta,
            "system_map": system_map,
        }

    def _op_shave_context(self, *, inputs: dict[str, Any], goal: str) -> dict[str, Any]:
        constraints = self._as_list(inputs.get("constraints") or inputs.get("constraints_pack"))
        objective = str(inputs.get("objective") or goal)

        tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9_]+", objective) if len(token) > 2]
        keywords = sorted(set(tokens))[:8]
        query_plan = {
            "goal": objective,
            "keywords": keywords,
            "limit": 10,
            "ledger_kind": "GitLedger",
        }

        context_slices = [
            "goal_scope",
            "constraints",
            "known_components",
            "risk_hotspots",
        ]

        return {
            "context_slices": context_slices,
            "query_plan": query_plan,
            "constraints_pack": constraints or ["keep_changes_small"],
        }

    def _op_simplify(self, *, inputs: dict[str, Any]) -> dict[str, Any]:
        artifacts = inputs.get("artifacts")
        if artifacts is None:
            artifacts = {
                "decision_log": inputs.get("decision_log", []),
                "system_map": inputs.get("system_map", {}),
            }

        reduced = {
            "keys": sorted(list(artifacts.keys())) if isinstance(artifacts, dict) else ["artifact"],
            "summary": str(artifacts)[:500],
        }

        decision_log = self._as_list(inputs.get("decision_log") or inputs.get("decisions"))
        system_map = inputs.get("system_map") if isinstance(inputs.get("system_map"), dict) else {
            "components": [],
            "interfaces": []
        }
        problem_contract = {
            "scope": str(inputs.get("goal") or inputs.get("objective") or "unspecified"),
            "assumptions": decision_log[:3],
            "system_impact": system_map,
        }

        return {
            "reduced_artifacts": reduced,
            "problem_contract": problem_contract,
            "decision_log": decision_log,
            "system_map": system_map,
        }

    def _op_plan(self, *, inputs: dict[str, Any], goal: str, context: dict[str, Any]) -> dict[str, Any]:
        problem = inputs.get("problem_contract") or {"scope": goal}
        constraints = self._as_list(inputs.get("constraints_pack") or inputs.get("constraints"))
        execute_command = str(
            context.get("execute_command")
            or inputs.get("execute_command")
            or ""
        )
        validate_command = str(
            context.get("validate_command")
            or inputs.get("validate_command")
            or ""
        )

        execution_plan = {
            "steps": [
                "implement_changes",
                "run_tests",
                "prepare_release_artifacts",
            ],
            "problem": problem,
            "constraints": constraints,
            "command": execute_command,
        }
        validation_plan = {
            "checks": ["unit_tests", "lint", "smoke_tests"],
            "thresholds": {"tests_pass": True, "lint_pass": True},
            "validate_command": validate_command,
        }
        rollout_plan = {
            "strategy": "canary",
            "stages": ["staging", "prod"],
            "rollback": "git_revert",
        }
        return {
            "execution_plan": execution_plan,
            "validation_plan": validation_plan,
            "rollout_plan": rollout_plan,
            "approved_plan": execution_plan,
        }

    def _op_execute(self, *, inputs: dict[str, Any], context: dict[str, Any], tasc_id: str) -> dict[str, Any]:
        approved_plan = inputs.get("approved_plan") or inputs.get("execution_plan") or {}
        validation_plan = inputs.get("validation_plan") or {}
        cwd = str(context.get("workspace") or os.getcwd())

        command = str(approved_plan.get("command") or "") if isinstance(approved_plan, dict) else ""
        proofs: list[dict[str, Any]] = []
        changed_files: list[str] = []
        status = "success"

        if command:
            cmd_result = self.command_executor.run(command=command, cwd=cwd, tasc_id=tasc_id)
            status = cmd_result.status
            proofs.append(
                {
                    "command": cmd_result.command,
                    "exit_code": cmd_result.exit_code,
                    "summary": cmd_result.summary,
                    "evidence_paths": cmd_result.evidence_paths,
                }
            )
        else:
            proofs.append({"summary": "no command provided; synthesized dry execute"})

        if isinstance(approved_plan, dict):
            changed_files = self._as_list(approved_plan.get("files") or approved_plan.get("changed_files"))

        changeset = {
            "status": status,
            "changed_files": changed_files,
            "plan_snapshot": approved_plan,
            "validate_command": (
                validation_plan.get("validate_command")
                if isinstance(validation_plan, dict)
                else ""
            ),
        }

        return {
            "changeset": changeset,
            "change_set": changeset,
            "proofs": proofs,
            "op_status": status,
            "command": command,
        }

    def _op_validate(self, *, inputs: dict[str, Any], context: dict[str, Any], tasc_id: str) -> dict[str, Any]:
        changeset = inputs.get("changeset") or inputs.get("change_set") or {}
        validate_command = ""
        if isinstance(changeset, dict):
            validate_command = str(changeset.get("validate_command") or "")

        cwd = str(context.get("workspace") or os.getcwd())
        pass_fail = True
        evidence_paths: list[str] = []
        summary = "validation synthesized"

        if validate_command:
            cmd_result = self.command_executor.run(command=validate_command, cwd=cwd, tasc_id=f"{tasc_id}_validate")
            pass_fail = cmd_result.status == "success"
            evidence_paths.extend(cmd_result.evidence_paths)
            summary = cmd_result.summary

        validation_report = {
            "pass_fail": pass_fail,
            "summary": summary,
            "evidence_paths": evidence_paths,
            "changed_files": changeset.get("changed_files", []) if isinstance(changeset, dict) else [],
        }

        return {
            "validation_report": validation_report,
            "pass_fail": pass_fail,
        }

    def _op_ship(self, *, inputs: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        validation_report = inputs.get("validation_report") or {}
        rollout_plan = inputs.get("rollout_plan") or {}
        deploy_target = str(context.get("deploy_target") or "staging")

        deployment = {
            "target": deploy_target,
            "strategy": rollout_plan.get("strategy", "canary") if isinstance(rollout_plan, dict) else "canary",
            "status": "deployed" if validation_report.get("pass_fail", False) else "blocked",
            "observability": {
                "checks": ["error_rate", "latency", "throughput"],
                "dashboard": context.get("dashboard_url", "local://dashboard"),
            },
        }

        release_notes = {
            "summary": "Automated release package",
            "deployment_target": deploy_target,
            "validation": validation_report,
        }

        return {
            "deployment": deployment,
            "release_notes": release_notes,
        }

    def _op_outtake(self, *, inputs: dict[str, Any]) -> dict[str, Any]:
        deployment = inputs.get("deployment") or {}
        validation_report = inputs.get("validation_report") or {}

        learning_note = {
            "what_happened": deployment.get("status", "unknown"),
            "quality": "pass" if validation_report.get("pass_fail") else "review_needed",
            "next_iteration_focus": "reduce cycle time",
        }

        return {
            "learning_note": learning_note,
            "tool_forge_requests": [],
        }

    def _op_toolforge(self, *, inputs: dict[str, Any]) -> dict[str, Any]:
        pain_signal = str(inputs.get("pain_signal") or "unclassified_pain")
        examples = self._as_list(inputs.get("examples"))
        desired = str(inputs.get("desired_constraint") or "improve_runtime_resilience")

        requests = self.toolforge.forge(
            self.toolforge.detect_pain_signals(
                [
                    {
                        "status": "failed",
                        "op": pain_signal,
                        "message": ";".join(examples) if examples else desired,
                    },
                    {
                        "status": "failed",
                        "op": pain_signal,
                        "message": desired,
                    },
                ]
            )
        )

        if requests:
            req = requests[0]
            return {
                "new_template": req.new_template,
                "new_gate": req.new_gate,
                "new_constraint": req.new_constraint,
                "new_op": req.new_op,
                "tool_forge_requests": [req.__dict__],
            }

        return {
            "new_template": f"Template_{pain_signal}",
            "new_gate": f"Gate_{pain_signal}",
            "new_constraint": desired,
            "new_op": f"Op_{pain_signal}",
            "tool_forge_requests": [],
        }

    def _apply_contract_defaults(self, op_name: str, outputs: dict[str, Any]) -> dict[str, Any]:
        contract = self.bundle.op_index().get(op_name) or {}
        required = [str(name) for name in contract.get("OUT") or []]
        normalized = dict(outputs)

        for field_name in required:
            if field_name in normalized:
                continue
            normalized[field_name] = self._default_value_for_contract_field(field_name)

        # Mirror contract field aliases into artifact-oriented names where useful.
        for field_name in required:
            if field_name in normalized:
                for alias in artifact_aliases(field_name):
                    normalized.setdefault(alias, normalized[field_name])

        return normalized

    @staticmethod
    def _default_value_for_contract_field(field_name: str) -> Any:
        if field_name.endswith("s") or field_name.endswith("_paths"):
            return []
        if field_name.endswith("_pack") or field_name.endswith("_plan") or field_name.endswith("_report"):
            return {}
        if field_name.endswith("_delta"):
            return {}
        if field_name in {"pass_fail"}:
            return False
        return ""

    @staticmethod
    def _as_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, tuple):
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, str):
            return [value] if value.strip() else []
        return [str(value)]
