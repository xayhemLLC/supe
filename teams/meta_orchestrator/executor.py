"""Meta-orchestrator runtime executor built on Flow of Time (FoT)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from ..nubflow.nubflow import FlowOfTimeEngine
from ..nubflow.types import FoTState, NubExitPack, new_sid
from .artifacts import artifacts_present, extract_required_inputs, merge_artifact_outputs
from .compiler import CompiledOrchestration, GoalRequest, PillarInstance, TascInstance
from .gates import GateEngine, GateEvaluation, SignoffEvaluation
from .ops_runtime import OpsRuntime
from .spec_loader import BundleSpec
from .toolforge import ToolForge, ToolForgeRequest


@dataclass
class ActionExecutionProof:
    """Execution result for one Action/Tasc."""

    tasc_sid: str
    tasc_name: str
    status: str
    outputs: dict[str, Any]
    proof_artifacts: list[str] = field(default_factory=list)
    message: str = ""
    op_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    gate_results: list[GateEvaluation] = field(default_factory=list)
    signoff_results: list[SignoffEvaluation] = field(default_factory=list)
    sid: str = field(default_factory=new_sid)


@dataclass
class PillarExecutionResult:
    """Execution summary for one pillar boundary."""

    pillar_sid: str
    pillar_name: str
    status: str
    action_proofs: list[ActionExecutionProof]
    fot_exit_pack: NubExitPack
    sid: str = field(default_factory=new_sid)


@dataclass
class WorkflowExecutionResult:
    """Overall execution summary for a compiled orchestration."""

    workflow_sid: str
    workflow_name: str
    status: str
    pillar_results: list[PillarExecutionResult]
    toolforge_requests: list[ToolForgeRequest]
    audit_records: list[str] = field(default_factory=list)
    sid: str = field(default_factory=new_sid)


class ToolLifecycleAdapter(Protocol):
    """Optional adapter to execute a Tasc through an external lifecycle."""

    def run_tasc(self, tasc: TascInstance, goal: GoalRequest, context: dict[str, Any]) -> ActionExecutionProof:
        """Execute one action instance and return proof data."""


class NoopToolLifecycleAdapter:
    """Adapter that returns a deterministic, non-invasive proof record."""

    def run_tasc(self, tasc: TascInstance, goal: GoalRequest, context: dict[str, Any]) -> ActionExecutionProof:
        outputs = {
            "goal": goal.goal,
            "objective": goal.goal,
            "decisions": [f"executed:{tasc.name}"],
            "next_actions": [f"continue:{tasc.name}"],
            "artifacts_to_produce": list(tasc.out_artifacts),
            "op": tasc.ops[0] if tasc.ops else "noop",
            "context": context,
        }
        return ActionExecutionProof(
            tasc_sid=tasc.sid,
            tasc_name=tasc.name,
            status="success",
            outputs=outputs,
            proof_artifacts=[f"proof:{tasc.sid}"],
            message="noop lifecycle execution",
        )


class MetaOrchestratorExecutor:
    """Execute compiled workflows, invoking FoT at pillar boundaries."""

    def __init__(
        self,
        bundle: BundleSpec,
        flow_of_time: FlowOfTimeEngine | None = None,
        lifecycle_adapter: ToolLifecycleAdapter | None = None,
        toolforge: ToolForge | None = None,
        ops_runtime: OpsRuntime | None = None,
        gate_engine: GateEngine | None = None,
    ) -> None:
        self.bundle = bundle
        self.flow_of_time = flow_of_time or FlowOfTimeEngine()
        self.lifecycle_adapter = lifecycle_adapter
        self.toolforge = toolforge or ToolForge()
        self.ops_runtime = ops_runtime or OpsRuntime(bundle=bundle, ledger_registry=self.flow_of_time.ledger_registry)
        self.gate_engine = gate_engine or GateEngine(bundle)

    def execute(
        self,
        compiled: CompiledOrchestration,
        *,
        sys_inputs: list[dict[str, Any]] | None = None,
        approvals: dict[str, bool] | None = None,
    ) -> WorkflowExecutionResult:
        approvals = approvals or {}
        prev_exit: NubExitPack | None = None
        status = "completed"
        pillar_results: list[PillarExecutionResult] = []
        action_records: list[dict[str, Any]] = []
        artifact_store = self._seed_artifacts(compiled.goal, sys_inputs)

        orchestrator_step_names = [step.name for step in compiled.orchestrator_tascs]
        for step in compiled.orchestrator_tascs:
            step_result = self.ops_runtime.run_op(
                "Plan",
                inputs={
                    "problem_contract": {"scope": compiled.goal.goal, "step": step.name},
                    "decision_log": [f"orchestrator_step:{step.name}"],
                    "system_map": {"components": ["orchestrator"], "interfaces": ["internal"]},
                },
                goal=compiled.goal.goal,
                tasc_id=step.sid,
                context={"workspace": compiled.goal.context.get("workspace")},
            )
            artifact_store.update(step_result)
            action_records.append(
                {
                    "status": "ok",
                    "op": step.name,
                    "message": "orchestrator step executed",
                }
            )

        for pillar in compiled.workflow.pillars:
            proofs: list[ActionExecutionProof] = []

            pre_gates = self.gate_engine.evaluate(
                pillar.gates_pre,
                phase="pre",
                record={"pillar": pillar.name, "ops": pillar.ops, "status": "pending"},
                artifact_store=artifact_store,
                approvals=approvals,
                goal_context=compiled.goal.context,
            )
            pre_signoffs = self.gate_engine.evaluate_signoffs(
                pillar.signoffs_pre,
                phase="pre",
                approvals=approvals,
                goal_context=compiled.goal.context,
            )
            hold_reasons = self.gate_engine.hold_reasons(pre_gates, pre_signoffs)
            hard_failures = self.gate_engine.failures(pre_gates, pre_signoffs)

            if not hold_reasons and not hard_failures:
                for tasc in pillar.tascs:
                    proof = self._execute_tasc(
                        tasc=tasc,
                        goal=compiled.goal,
                        pillar=pillar,
                        approvals=approvals,
                        artifact_store=artifact_store,
                    )
                    proofs.append(proof)
                    action_records.append(
                        {
                            "status": "failed" if proof.status not in {"success", "ok"} else "ok",
                            "op": str(proof.outputs.get("op") or (tasc.ops[0] if tasc.ops else "unknown")),
                            "message": proof.message,
                        }
                    )

                    if proof.status == "hold":
                        hold_reasons.append(f"tasc:{tasc.name}")
                    elif proof.status in {"failed", "error"}:
                        hard_failures.append(f"tasc:{tasc.name}:{proof.message}")

            post_gates = self.gate_engine.evaluate(
                pillar.gates_post,
                phase="post",
                record={
                    "pillar": pillar.name,
                    "ops": pillar.ops,
                    "status": "success" if not hard_failures else "failed",
                    "command": artifact_store.get("command", ""),
                },
                artifact_store=artifact_store,
                approvals=approvals,
                goal_context=compiled.goal.context,
            )
            post_signoffs = self.gate_engine.evaluate_signoffs(
                pillar.signoffs_post,
                phase="post",
                approvals=approvals,
                goal_context=compiled.goal.context,
            )

            hold_reasons.extend(self.gate_engine.hold_reasons(post_gates, post_signoffs))
            hard_failures.extend(self.gate_engine.failures(post_gates, post_signoffs))

            if hold_reasons:
                action_records.append(
                    {
                        "status": "hold",
                        "op": "human_gate",
                        "message": hold_reasons[0],
                    }
                )
            if hard_failures:
                action_records.append(
                    {
                        "status": "error",
                        "op": "policy",
                        "message": hard_failures[0],
                    }
                )

            pillar_inputs: list[dict[str, Any]] = [proof.outputs for proof in proofs]
            pillar_inputs.append(
                {
                    "objective": compiled.goal.goal,
                    "decisions": artifact_store.get("decision_log", []),
                    "next_actions": (
                        artifact_store.get("execution_plan", {}).get("steps", [])
                        if isinstance(artifact_store.get("execution_plan"), dict)
                        else []
                    ),
                    "artifacts_to_produce": (
                        artifact_store.get("rollout_plan", {}).get("stages", [])
                        if isinstance(artifact_store.get("rollout_plan"), dict)
                        else []
                    ),
                    "stop_conditions": self._derive_stop_conditions(compiled.goal),
                }
            )
            if hold_reasons:
                pillar_inputs.append(
                    {
                        "requires_human_signoff": True,
                        "hold_reason": hold_reasons[0],
                        "gates_and_signoffs": hold_reasons,
                        "objective": compiled.goal.goal,
                    }
                )

            if hard_failures:
                pillar_inputs.append(
                    {
                        "kind": "error",
                        "errors": hard_failures,
                        "objective": compiled.goal.goal,
                    }
                )

            if sys_inputs and prev_exit is None:
                pillar_inputs = list(sys_inputs) + pillar_inputs

            fot_exit = self.flow_of_time.nub_next(
                prev_nub_exit_pack=prev_exit,
                sys_inputs=pillar_inputs,
                context_ref={
                    "workflow_cursor": pillar.name,
                    "team_scope": compiled.goal.context.get("team_scope", "default"),
                },
                constraints_pack=compiled.goal.constraints_pack,
            )

            pillar_status = "completed"
            if fot_exit.state == FoTState.HOLD:
                pillar_status = "hold"
                status = "hold"
            elif fot_exit.state == FoTState.ERROR:
                pillar_status = "error"
                status = "error"

            pillar_results.append(
                PillarExecutionResult(
                    pillar_sid=pillar.sid,
                    pillar_name=pillar.name,
                    status=pillar_status,
                    action_proofs=proofs,
                    fot_exit_pack=fot_exit,
                )
            )

            prev_exit = fot_exit
            if status in {"hold", "error"}:
                break

        signals = self.toolforge.detect_pain_signals(action_records)
        requests = self.toolforge.forge(signals)

        audit_records = list(compiled.audit)
        audit_records.append(f"orchestrator_steps:{','.join(orchestrator_step_names)}")
        audit_records.append(f"execute:status={status}")
        audit_records.append(f"execute:pillars={len(pillar_results)}")
        audit_records.append(f"toolforge:requests={len(requests)}")

        return WorkflowExecutionResult(
            workflow_sid=compiled.workflow.sid,
            workflow_name=compiled.workflow.name,
            status=status,
            pillar_results=pillar_results,
            toolforge_requests=requests,
            audit_records=audit_records,
        )

    def _execute_tasc(
        self,
        *,
        tasc: TascInstance,
        goal: GoalRequest,
        pillar: PillarInstance,
        approvals: dict[str, bool],
        artifact_store: dict[str, Any],
    ) -> ActionExecutionProof:
        tasc_inputs = extract_required_inputs(artifact_store, tasc.in_artifacts)
        tasc_inputs.setdefault("goal", goal.goal)
        tasc_inputs.setdefault("constraints_pack", goal.constraints_pack)

        pre_gates = self.gate_engine.evaluate(
            tasc.gates_pre,
            phase="pre",
            record={
                "pillar": pillar.name,
                "tasc": tasc.name,
                "ops": tasc.ops,
                "status": "pending",
                "command": self._extract_candidate_command(tasc_inputs),
            },
            artifact_store=artifact_store,
            approvals=approvals,
            goal_context=goal.context,
        )
        pre_signoffs = self.gate_engine.evaluate_signoffs(
            tasc.signoffs_pre,
            phase="pre",
            approvals=approvals,
            goal_context=goal.context,
        )

        hold_reasons = self.gate_engine.hold_reasons(pre_gates, pre_signoffs)
        failures = self.gate_engine.failures(pre_gates, pre_signoffs)

        if hold_reasons:
            return ActionExecutionProof(
                tasc_sid=tasc.sid,
                tasc_name=tasc.name,
                status="hold",
                outputs={"requires_human_signoff": True, "hold_reason": hold_reasons[0]},
                message=hold_reasons[0],
                gate_results=pre_gates,
                signoff_results=pre_signoffs,
            )

        if failures:
            return ActionExecutionProof(
                tasc_sid=tasc.sid,
                tasc_name=tasc.name,
                status="failed",
                outputs={"errors": failures},
                message=failures[0],
                gate_results=pre_gates,
                signoff_results=pre_signoffs,
            )

        op_outputs: dict[str, Any] = {}
        op_results: dict[str, dict[str, Any]] = {}
        lifecycle_failure: str | None = None

        for op_name in tasc.ops:
            op_result = self.ops_runtime.run_op(
                op_name,
                inputs={**tasc_inputs, **op_outputs},
                goal=goal.goal,
                tasc_id=tasc.sid,
                context={
                    "workspace": goal.context.get("workspace"),
                    "deploy_target": goal.context.get("deploy_target", "staging"),
                    "dashboard_url": goal.context.get("dashboard_url"),
                    "execute_command": goal.context.get("execute_command"),
                    "validate_command": goal.context.get("validate_command"),
                },
            )
            op_results[op_name] = op_result
            op_outputs.update(op_result)

            artifact_store.update(merge_artifact_outputs(artifact_store, tasc.out_artifacts, op_result))

        # Optional external lifecycle adapter can contribute proof artifacts and output deltas.
        proof_artifacts: list[str] = []
        if self.lifecycle_adapter is not None:
            lifecycle_proof = self.lifecycle_adapter.run_tasc(
                tasc=tasc,
                goal=goal,
                context={"workflow": goal.context.get("workflow"), "pillar": pillar.name},
            )
            proof_artifacts.extend(lifecycle_proof.proof_artifacts)
            op_outputs.update(lifecycle_proof.outputs)
            artifact_store.update(merge_artifact_outputs(artifact_store, tasc.out_artifacts, lifecycle_proof.outputs))
            if lifecycle_proof.status not in {"success", "ok", "completed"}:
                lifecycle_failure = lifecycle_proof.message or f"lifecycle status: {lifecycle_proof.status}"

        out_ok, missing_outputs = artifacts_present(artifact_store, tasc.out_artifacts)
        status = "success" if out_ok and not lifecycle_failure else "failed"
        if lifecycle_failure:
            message = lifecycle_failure
        else:
            message = "tasc executed" if out_ok else f"missing declared outputs: {', '.join(missing_outputs)}"

        post_gates = self.gate_engine.evaluate(
            tasc.gates_post,
            phase="post",
            record={
                "pillar": pillar.name,
                "tasc": tasc.name,
                "ops": tasc.ops,
                "status": status,
                "command": op_outputs.get("command", ""),
            },
            artifact_store=artifact_store,
            approvals=approvals,
            goal_context=goal.context,
        )
        post_signoffs = self.gate_engine.evaluate_signoffs(
            tasc.signoffs_post,
            phase="post",
            approvals=approvals,
            goal_context=goal.context,
        )

        hold_reasons = self.gate_engine.hold_reasons(post_gates, post_signoffs)
        failures = self.gate_engine.failures(post_gates, post_signoffs)

        if hold_reasons:
            status = "hold"
            message = hold_reasons[0]
            op_outputs.update({"requires_human_signoff": True, "hold_reason": hold_reasons[0]})
        elif failures:
            status = "failed"
            message = failures[0]
            op_outputs.setdefault("errors", failures)

        return ActionExecutionProof(
            tasc_sid=tasc.sid,
            tasc_name=tasc.name,
            status=status,
            outputs=op_outputs,
            proof_artifacts=proof_artifacts,
            message=message,
            op_results=op_results,
            gate_results=[*pre_gates, *post_gates],
            signoff_results=[*pre_signoffs, *post_signoffs],
        )

    @staticmethod
    def _seed_artifacts(goal: GoalRequest, sys_inputs: list[dict[str, Any]] | None) -> dict[str, Any]:
        artifact_store: dict[str, Any] = {
            "ticket": {"goal": goal.goal, "context": goal.context},
            "constraints_pack": goal.constraints_pack,
            "goal": goal.goal,
        }
        if sys_inputs:
            artifact_store["sys_inputs"] = sys_inputs
            if sys_inputs:
                artifact_store["master_input"] = sys_inputs[0]
        return artifact_store

    @staticmethod
    def _extract_candidate_command(inputs: dict[str, Any]) -> str:
        approved_plan = inputs.get("approved_plan") or inputs.get("execution_plan")
        if isinstance(approved_plan, dict):
            return str(approved_plan.get("command") or "")
        return ""

    @staticmethod
    def _derive_stop_conditions(goal: GoalRequest) -> list[str]:
        stop_when = goal.constraints_pack.get("stop_when")
        if stop_when:
            return [str(stop_when)]
        return []
