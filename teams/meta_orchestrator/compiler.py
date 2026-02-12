"""Goal -> workflow compiler for the FoT meta-orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..nubflow.types import new_sid
from .spec_loader import BundleSpec


@dataclass
class GoalRequest:
    """Domain-agnostic orchestration goal."""

    goal: str
    role: str = "BackendEngineer"
    constraints_pack: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    sid: str = field(default_factory=new_sid)


@dataclass
class TascInstance:
    """Atomic action template instance."""

    name: str
    kind: str
    template_name: str
    ops: list[str]
    in_artifacts: list[str]
    out_artifacts: list[str]
    gates_pre: list[str] = field(default_factory=list)
    gates_post: list[str] = field(default_factory=list)
    signoffs_pre: list[str] = field(default_factory=list)
    signoffs_post: list[str] = field(default_factory=list)
    max_execution_depth_distance: int = 1
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)
    sid: str = field(default_factory=new_sid)


@dataclass
class PillarInstance:
    """Macro template instance composed of action Tascs."""

    name: str
    tascs: list[TascInstance]
    ops: list[str]
    in_artifacts: list[str]
    out_artifacts: list[str]
    gates_pre: list[str] = field(default_factory=list)
    gates_post: list[str] = field(default_factory=list)
    signoffs_pre: list[str] = field(default_factory=list)
    signoffs_post: list[str] = field(default_factory=list)
    max_execution_depth_distance: int = 1
    status: str = "pending"
    sid: str = field(default_factory=new_sid)


@dataclass
class WorkflowInstance:
    """Compiled workflow with concrete pillar instances."""

    name: str
    role: str
    pillars: list[PillarInstance]
    status: str = "pending"
    sid: str = field(default_factory=new_sid)


@dataclass
class CompiledOrchestration:
    """Final compiler output consumed by executor."""

    goal: GoalRequest
    workflow: WorkflowInstance
    orchestrator_tascs: list[TascInstance]
    sid: str = field(default_factory=new_sid)
    audit: list[str] = field(default_factory=list)


class MetaOrchestratorCompiler:
    """Compile goals into executable workflow/pillar/action instances."""

    def __init__(self, bundle: BundleSpec) -> None:
        self.bundle = bundle

    def compile_goal(
        self,
        goal: str | GoalRequest,
        *,
        workflow_name: str | None = None,
        role: str | None = None,
        constraints_pack: dict[str, Any] | None = None,
    ) -> CompiledOrchestration:
        """Compile a goal into a workflow instance and self-hosted Tascs."""
        request = goal if isinstance(goal, GoalRequest) else GoalRequest(goal=goal)
        if role:
            request.role = role
        if constraints_pack:
            request.constraints_pack.update(constraints_pack)

        selected = self._select_workflow(workflow_name=workflow_name, role=request.role)
        pillars = [self._compile_pillar(name) for name in selected.get("pillars", [])]

        workflow = WorkflowInstance(
            name=selected["name"],
            role=selected.get("role", request.role),
            pillars=pillars,
        )

        orchestrator_tascs = self._build_orchestrator_tascs()
        audit = [
            f"compile_goal:{request.goal}",
            f"workflow:{workflow.name}",
            f"pillars:{len(workflow.pillars)}",
        ]

        return CompiledOrchestration(
            goal=request,
            workflow=workflow,
            orchestrator_tascs=orchestrator_tascs,
            audit=audit,
        )

    def _select_workflow(self, workflow_name: str | None, role: str) -> dict[str, Any]:
        workflows = self.bundle.workflows

        if workflow_name:
            for workflow in workflows:
                if workflow.get("name") == workflow_name:
                    return workflow
            raise KeyError(f"Unknown workflow: {workflow_name}")

        for workflow in workflows:
            if workflow.get("role") == role:
                return workflow

        return workflows[0]

    def _compile_pillar(self, pillar_name: str) -> PillarInstance:
        templates = self.bundle.templates
        template = templates[pillar_name]

        action_names = list(template.get("composed_of") or [])
        if not action_names:
            # Keep data-driven behavior even when no explicit actions exist.
            action_names = [pillar_name]

        tascs = [self._compile_action(action_name, parent_pillar=pillar_name) for action_name in action_names]
        gates = template.get("gates") or {}
        signoffs = template.get("signoffs") or {}

        return PillarInstance(
            name=pillar_name,
            tascs=tascs,
            ops=list(template.get("ops") or []),
            in_artifacts=list(template.get("IN") or []),
            out_artifacts=list(template.get("OUT") or []),
            gates_pre=list(gates.get("pre") or []),
            gates_post=list(gates.get("post") or []),
            signoffs_pre=list(signoffs.get("pre") or []),
            signoffs_post=list(signoffs.get("post") or []),
            max_execution_depth_distance=int(template.get("max_execution_depth_distance", 1)),
        )

    def _compile_action(self, action_name: str, parent_pillar: str) -> TascInstance:
        templates = self.bundle.templates
        template = templates.get(action_name)
        if template is None:
            # Synthetic action from pillar-level template.
            pillar = templates[parent_pillar]
            return TascInstance(
                name=action_name,
                kind="action",
                template_name=parent_pillar,
                ops=list(pillar.get("ops") or []),
                in_artifacts=list(pillar.get("IN") or []),
                out_artifacts=list(pillar.get("OUT") or []),
                max_execution_depth_distance=int(pillar.get("max_execution_depth_distance", 1)),
                metadata={"synthetic": True, "pillar": parent_pillar},
            )

        gates = template.get("gates") or {}
        signoffs = template.get("signoffs") or {}
        return TascInstance(
            name=action_name,
            kind=str(template.get("kind", "action")),
            template_name=action_name,
            ops=list(template.get("ops") or []),
            in_artifacts=list(template.get("IN") or []),
            out_artifacts=list(template.get("OUT") or []),
            gates_pre=list(gates.get("pre") or []),
            gates_post=list(gates.get("post") or []),
            signoffs_pre=list(signoffs.get("pre") or []),
            signoffs_post=list(signoffs.get("post") or []),
            max_execution_depth_distance=int(template.get("max_execution_depth_distance", 1)),
            metadata={"pillar": parent_pillar},
        )

    def _build_orchestrator_tascs(self) -> list[TascInstance]:
        pipeline = list(self.bundle.orchestrator.get("pipeline") or [])
        tascs: list[TascInstance] = []
        for step in pipeline:
            tascs.append(
                TascInstance(
                    name=str(step),
                    kind="orchestrator_step",
                    template_name="meta_orchestrator_pipeline",
                    ops=["Plan"],
                    in_artifacts=["ProblemContract"],
                    out_artifacts=["ExecutionPlan"],
                    metadata={"self_hosted": True},
                )
            )
        return tascs
