"""Gate and signoff evaluation for YAML-driven meta-orchestrator execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .artifacts import artifacts_present
from .spec_loader import BundleSpec


@dataclass
class GateEvaluation:
    """Evaluation result for one gate."""

    gate_name: str
    phase: str
    passed: bool
    message: str
    validator_type: str
    hold: bool = False
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SignoffEvaluation:
    """Evaluation result for one signoff requirement."""

    signoff_name: str
    phase: str
    required: bool
    passed: bool
    message: str
    approvers: list[str] = field(default_factory=list)
    hold: bool = False


class GateEngine:
    """Evaluate code/policy/human gates defined in the YAML bundle."""

    def __init__(self, bundle: BundleSpec) -> None:
        self.bundle = bundle

    def evaluate(
        self,
        gate_names: list[str],
        *,
        phase: str,
        record: dict[str, Any],
        artifact_store: dict[str, Any],
        approvals: dict[str, bool],
        goal_context: dict[str, Any],
    ) -> list[GateEvaluation]:
        results: list[GateEvaluation] = []
        gate_index = self.bundle.gate_index()

        for gate_name in gate_names:
            gate = gate_index.get(gate_name)
            if not gate:
                results.append(
                    GateEvaluation(
                        gate_name=gate_name,
                        phase=phase,
                        passed=False,
                        message="unknown gate",
                        validator_type="unknown",
                        hold=False,
                    )
                )
                continue

            validator = gate.get("validator") or {}
            validator_type = str(validator.get("type") or "unknown")
            hold_on_fail = "hold" in (gate.get("decisions") or [])

            if validator_type == "human":
                approved = approvals.get(gate_name, False) or approvals.get(str(validator.get("ref")), False)
                passed = bool(approved)
                message = "human approval present" if passed else "human approval required"
                results.append(
                    GateEvaluation(
                        gate_name=gate_name,
                        phase=phase,
                        passed=passed,
                        message=message,
                        validator_type=validator_type,
                        hold=(not passed) and (hold_on_fail or True),
                        details={"ref": validator.get("ref")},
                    )
                )
                continue

            if validator_type == "code":
                passed, message, details = self._run_code_validator(
                    ref=str(validator.get("ref") or ""),
                    record=record,
                    artifact_store=artifact_store,
                    goal_context=goal_context,
                )
                results.append(
                    GateEvaluation(
                        gate_name=gate_name,
                        phase=phase,
                        passed=passed,
                        message=message,
                        validator_type=validator_type,
                        hold=(not passed) and hold_on_fail,
                        details=details,
                    )
                )
                continue

            if validator_type == "policy":
                passed, message, details = self._run_policy_validator(
                    ref=str(validator.get("ref") or ""),
                    artifact_store=artifact_store,
                    goal_context=goal_context,
                )
                results.append(
                    GateEvaluation(
                        gate_name=gate_name,
                        phase=phase,
                        passed=passed,
                        message=message,
                        validator_type=validator_type,
                        hold=(not passed) and hold_on_fail,
                        details=details,
                    )
                )
                continue

            results.append(
                GateEvaluation(
                    gate_name=gate_name,
                    phase=phase,
                    passed=False,
                    message=f"unsupported validator type: {validator_type}",
                    validator_type=validator_type,
                    hold=False,
                )
            )

        return results

    def evaluate_signoffs(
        self,
        signoff_names: list[str],
        *,
        phase: str,
        approvals: dict[str, bool],
        goal_context: dict[str, Any],
    ) -> list[SignoffEvaluation]:
        """Evaluate signoff requirements and quorum semantics."""
        results: list[SignoffEvaluation] = []
        signoff_index = self.bundle.signoff_index()

        for signoff_name in signoff_names:
            signoff = signoff_index.get(signoff_name)
            if not signoff:
                results.append(
                    SignoffEvaluation(
                        signoff_name=signoff_name,
                        phase=phase,
                        required=True,
                        passed=False,
                        message="unknown signoff",
                        hold=True,
                    )
                )
                continue

            approvers = [str(item) for item in signoff.get("approvers") or []]
            mode = str(signoff.get("mode") or "any_one")
            quorum = int(signoff.get("quorum") or 1)
            required = self._is_signoff_required(signoff_name=signoff_name, signoff=signoff, goal_context=goal_context)

            approvals_count = 0
            if approvals.get(signoff_name, False):
                approvals_count += 1
            for approver in approvers:
                if approvals.get(approver, False):
                    approvals_count += 1

            if not required:
                results.append(
                    SignoffEvaluation(
                        signoff_name=signoff_name,
                        phase=phase,
                        required=False,
                        passed=True,
                        message="signoff optional in current context",
                        approvers=approvers,
                        hold=False,
                    )
                )
                continue

            if mode == "all":
                target = max(quorum, len(approvers), 1)
            else:
                target = max(quorum, 1)

            passed = approvals_count >= target
            message = "signoff quorum satisfied" if passed else f"signoff requires quorum {target}"
            results.append(
                SignoffEvaluation(
                    signoff_name=signoff_name,
                    phase=phase,
                    required=True,
                    passed=passed,
                    message=message,
                    approvers=approvers,
                    hold=not passed,
                )
            )

        return results

    @staticmethod
    def hold_reasons(gates: list[GateEvaluation], signoffs: list[SignoffEvaluation]) -> list[str]:
        reasons: list[str] = []
        for gate in gates:
            if gate.hold:
                reasons.append(f"gate:{gate.gate_name}")
        for signoff in signoffs:
            if signoff.hold:
                reasons.append(f"signoff:{signoff.signoff_name}")
        return reasons

    @staticmethod
    def failures(gates: list[GateEvaluation], signoffs: list[SignoffEvaluation]) -> list[str]:
        failures: list[str] = []
        for gate in gates:
            if not gate.passed:
                failures.append(f"gate:{gate.gate_name}:{gate.message}")
        for signoff in signoffs:
            if not signoff.passed and signoff.required:
                failures.append(f"signoff:{signoff.signoff_name}:{signoff.message}")
        return failures

    def _run_code_validator(
        self,
        *,
        ref: str,
        record: dict[str, Any],
        artifact_store: dict[str, Any],
        goal_context: dict[str, Any],
    ) -> tuple[bool, str, dict[str, Any]]:
        if ref == "gate_safe_actions":
            return self._gate_safe_actions(record=record, goal_context=goal_context)
        if ref == "gate_post_checks":
            return self._gate_post_checks(record=record, artifact_store=artifact_store)
        return False, f"unknown code validator: {ref}", {}

    def _run_policy_validator(
        self,
        *,
        ref: str,
        artifact_store: dict[str, Any],
        goal_context: dict[str, Any],
    ) -> tuple[bool, str, dict[str, Any]]:
        if ref == "policy:intake_sufficiency_v1":
            return self._policy_intake_sufficiency(artifact_store)
        if ref == "policy:plan_quality_v1":
            return self._policy_plan_quality(artifact_store)
        if ref == "policy:release_ready_v1":
            return self._policy_release_ready(artifact_store, goal_context)
        if ref == "policy:observability_ok_v1":
            return self._policy_observability_ok(artifact_store)
        return False, f"unknown policy validator: {ref}", {}

    @staticmethod
    def _is_signoff_required(signoff_name: str, signoff: dict[str, Any], goal_context: dict[str, Any]) -> bool:
        required = bool(signoff.get("required", False))

        lower_name = signoff_name.lower()
        if "ifprod" in lower_name and str(goal_context.get("deploy_target", "")).lower() == "prod":
            return True
        if "ifneeded" in lower_name and bool(goal_context.get("scope_changed", False)):
            return True

        return required

    @staticmethod
    def _gate_safe_actions(record: dict[str, Any], goal_context: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        ops = [str(op) for op in record.get("ops") or []]
        if "Execute" not in ops:
            return True, "no execute op in this step", {}

        allow_mutations = bool(goal_context.get("allow_mutations", False))
        command = str(record.get("command") or "")
        dangerous_tokens = ("rm -rf", "git reset --hard", "DROP TABLE", "shutdown")
        if any(token in command for token in dangerous_tokens):
            return False, "blocked dangerous command", {"command": command}

        if not allow_mutations and command:
            return False, "mutating command requires allow_mutations", {"command": command}

        return True, "safe action gate passed", {"command": command}

    @staticmethod
    def _gate_post_checks(record: dict[str, Any], artifact_store: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        status = str(record.get("status") or "")
        if status and status not in {"success", "ok", "completed"}:
            return False, f"action status not successful: {status}", {"status": status}

        report = artifact_store.get("validation_report")
        if isinstance(report, dict) and "pass_fail" in report and not bool(report.get("pass_fail")):
            return False, "validation report indicates failure", report

        return True, "post checks passed", {}

    @staticmethod
    def _policy_intake_sufficiency(artifact_store: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        required = ["ProblemContract", "DecisionLog", "SystemMap", "ConstraintsPack", "QueryPlan"]
        ok, missing = artifacts_present(artifact_store, required)
        if ok:
            return True, "intake sufficiency satisfied", {}
        return False, "missing intake artifacts", {"missing": missing}

    @staticmethod
    def _policy_plan_quality(artifact_store: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        required = ["ExecutionPlan", "ValidationPlan", "RolloutPlan"]
        ok, missing = artifacts_present(artifact_store, required)
        if not ok:
            return False, "missing plan artifacts", {"missing": missing}

        execution_plan = artifact_store.get("execution_plan") or {}
        if isinstance(execution_plan, dict) and not execution_plan.get("steps"):
            return False, "execution plan has no steps", {}

        return True, "plan quality satisfied", {}

    @staticmethod
    def _policy_release_ready(
        artifact_store: dict[str, Any], goal_context: dict[str, Any]
    ) -> tuple[bool, str, dict[str, Any]]:
        report = artifact_store.get("validation_report")
        if not isinstance(report, dict):
            return False, "validation report missing", {}

        if not bool(report.get("pass_fail", False)):
            return False, "validation report failed", report

        deploy_target = str(goal_context.get("deploy_target") or "staging")
        return True, "release ready", {"deploy_target": deploy_target}

    @staticmethod
    def _policy_observability_ok(artifact_store: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        deployment = artifact_store.get("deployment")
        if not isinstance(deployment, dict):
            return False, "deployment artifact missing", {}

        observability = deployment.get("observability")
        if not isinstance(observability, dict):
            return False, "deployment observability metadata missing", {}

        if not observability.get("checks", []):
            return False, "no observability checks configured", {}

        return True, "observability checks configured", observability
