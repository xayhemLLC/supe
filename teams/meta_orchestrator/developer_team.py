"""Developer team blueprints on top of FoT meta-orchestrator."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path

from ..nubflow.types import new_sid
from .compiler import GoalRequest, MetaOrchestratorCompiler
from .executor import MetaOrchestratorExecutor, WorkflowExecutionResult
from .spec_loader import BundleSpec, load_bundle


@dataclass
class TeamMember:
    """One human or agent role in a developer team."""

    role: str
    focus: str
    tools: list[str] = field(default_factory=list)
    sid: str = field(default_factory=new_sid)


@dataclass
class DeveloperTeamBlueprint:
    """Configuration for a reusable real-world developer team."""

    name: str
    mission: str
    use_case: str
    workflow_name: str
    role: str
    members: list[TeamMember]
    default_constraints: dict[str, object] = field(default_factory=dict)
    default_context: dict[str, object] = field(default_factory=dict)
    default_approvals: dict[str, bool] = field(default_factory=dict)
    starter_objectives: list[str] = field(default_factory=list)
    sid: str = field(default_factory=new_sid)


@dataclass
class CompanyTeamSet:
    """A profile-specific set of developer teams for a company."""

    profile: str
    description: str
    teams: dict[str, DeveloperTeamBlueprint]
    sid: str = field(default_factory=new_sid)


class DeveloperTeam:
    """Team facade that compiles and executes goals through FoT."""

    def __init__(
        self,
        blueprint: DeveloperTeamBlueprint,
        *,
        bundle: BundleSpec | None = None,
        executor: MetaOrchestratorExecutor | None = None,
    ) -> None:
        self.blueprint = blueprint
        self.bundle = bundle or load_bundle()
        self.compiler = MetaOrchestratorCompiler(self.bundle)
        self.executor = executor or MetaOrchestratorExecutor(self.bundle)

    def run_objective(
        self,
        objective: str,
        *,
        sys_inputs: list[dict[str, object]] | None = None,
        approvals: dict[str, bool] | None = None,
        extra_constraints: dict[str, object] | None = None,
        extra_context: dict[str, object] | None = None,
    ) -> WorkflowExecutionResult:
        """Compile and execute one objective through the configured workflow."""
        constraints = dict(self.blueprint.default_constraints)
        constraints.update(extra_constraints or {})
        constraints.setdefault("objective", objective)

        context = dict(self.blueprint.default_context)
        context.update(extra_context or {})
        context.setdefault("team_scope", self.blueprint.use_case)
        context.setdefault("workflow", self.blueprint.workflow_name)

        goal = GoalRequest(
            goal=objective,
            role=self.blueprint.role,
            constraints_pack=constraints,
            context=context,
        )
        compiled = self.compiler.compile_goal(
            goal,
            workflow_name=self.blueprint.workflow_name,
            role=self.blueprint.role,
        )

        merged_approvals = dict(self.blueprint.default_approvals)
        merged_approvals.update(approvals or {})

        return self.executor.execute(compiled, sys_inputs=sys_inputs, approvals=merged_approvals)


class DeveloperTeamFactory:
    """Factory for practical starter teams requested by the user."""

    @staticmethod
    def company_guidance_team(*, company_name: str, workspace: str) -> DeveloperTeamBlueprint:
        return DeveloperTeamBlueprint(
            name=f"{company_name}-product-council",
            mission="Guide company-wide engineering direction and release rhythm.",
            use_case="company_guidance",
            workflow_name="Workflow_BE_Primary",
            role="BackendEngineer",
            members=[
                TeamMember(role="EngineeringLead", focus="Roadmap and architecture tradeoffs", tools=["Search", "Plan"]),
                TeamMember(role="ReleaseManager", focus="Release quality and operational readiness", tools=["Validate", "Ship"]),
                TeamMember(role="QualityReviewer", focus="Risk and quality gates", tools=["Ask", "Validate"]),
            ],
            default_constraints={
                "stop_when": "release_notes_generated",
                "allow_mutations": False,
            },
            default_context={
                "workspace": workspace,
                "deploy_target": "staging",
                "dashboard_url": "local://company-observability",
            },
            default_approvals={
                "PeerReviewSignoff": True,
                "HumanApprovalGate": True,
            },
            starter_objectives=[
                "Prioritize and stage the next backend release",
                "Audit delivery risks for the current sprint",
            ],
        )

    @staticmethod
    def startup_backend_dev_team(*, company_name: str, developer_name: str, workspace: str) -> DeveloperTeamBlueprint:
        return DeveloperTeamBlueprint(
            name=f"{company_name}-{developer_name}-backend-loop",
            mission="Guide day-to-day backend development in a startup context.",
            use_case="startup_backend_dev",
            workflow_name="Workflow_BE_Primary",
            role="BackendEngineer",
            members=[
                TeamMember(role="BackendDev", focus="Implement API and data changes", tools=["Execute", "Validate"]),
                TeamMember(role="ProductProxy", focus="Clarify scope and constraints", tools=["Ask", "ShaveContext"]),
                TeamMember(role="AIAuditor", focus="Proofs, gates, and rollout checks", tools=["Validate", "Ship"]),
            ],
            default_constraints={
                "stop_when": "validation_report_pass",
                "allow_mutations": False,
            },
            default_context={
                "workspace": workspace,
                "deploy_target": "staging",
                "execute_command": "git status --short",
                "validate_command": "uv run pytest -q tests/test_meta_orchestrator.py",
            },
            default_approvals={
                "PeerReviewSignoff": True,
                "HumanApprovalGate": True,
            },
            starter_objectives=[
                "Break a feature request into safe backend implementation steps",
                "Validate readiness for shipping an API change",
            ],
        )

    @staticmethod
    def gfx_subagent_design_team(*, company_name: str, workspace: str) -> DeveloperTeamBlueprint:
        return DeveloperTeamBlueprint(
            name=f"{company_name}-gfx-agent-lab",
            mission="Design a graphics-focused subagent with clear contracts and guardrails.",
            use_case="gfx_subagent_design",
            workflow_name="Workflow_BE_Primary",
            role="BackendEngineer",
            members=[
                TeamMember(role="AgentArchitect", focus="Design subagent contracts and integration points", tools=["Plan", "Simplify"]),
                TeamMember(role="GFXSpecialist", focus="Rendering pipeline and asset workflow requirements", tools=["Search", "Ask"]),
                TeamMember(role="SafetyReviewer", focus="Policy, scope, and deployment safety", tools=["Validate", "Ship"]),
            ],
            default_constraints={
                "stop_when": "subagent_spec_ready",
                "allow_mutations": False,
            },
            default_context={
                "workspace": workspace,
                "deploy_target": "staging",
                "dashboard_url": "local://gfx-agent-observability",
            },
            default_approvals={
                "PeerReviewSignoff": True,
                "HumanApprovalGate": True,
            },
            starter_objectives=[
                "Design a gfx subagent that generates validated rendering tasks",
                "Define interfaces between gfx subagent and backend execution agents",
            ],
        )

    @classmethod
    def starter_pack(
        cls,
        *,
        company_name: str,
        developer_name: str,
        workspace: str | None = None,
    ) -> dict[str, DeveloperTeamBlueprint]:
        base_workspace = workspace or str(Path.cwd())
        return {
            "company_guidance": cls.company_guidance_team(company_name=company_name, workspace=base_workspace),
            "startup_backend_dev": cls.startup_backend_dev_team(
                company_name=company_name,
                developer_name=developer_name,
                workspace=base_workspace,
            ),
            "gfx_subagent_design": cls.gfx_subagent_design_team(company_name=company_name, workspace=base_workspace),
        }

    @classmethod
    def build_company_team_set(
        cls,
        *,
        profile: str,
        company_name: str,
        developer_name: str,
        workspace: str | None = None,
    ) -> CompanyTeamSet:
        """Build a company-tailored team set for a profile archetype."""
        base_workspace = workspace or str(Path.cwd())
        base_pack = cls.starter_pack(
            company_name=company_name,
            developer_name=developer_name,
            workspace=base_workspace,
        )

        normalized = profile.strip().lower().replace("-", "_")
        if normalized not in {"startup", "growth", "enterprise", "agency", "open_source"}:
            raise ValueError(
                "Unsupported profile. Use one of: startup, growth, enterprise, agency, open_source"
            )

        description = cls._profile_description(normalized)
        overrides = cls._profile_overrides(normalized)
        teams = {
            key: cls._apply_blueprint_overrides(blueprint, overrides, profile=normalized, company_name=company_name)
            for key, blueprint in base_pack.items()
        }
        return CompanyTeamSet(profile=normalized, description=description, teams=teams)

    @classmethod
    def company_sets(
        cls,
        *,
        company_name: str,
        developer_name: str,
        workspace: str | None = None,
    ) -> dict[str, CompanyTeamSet]:
        """Return all supported company profile team sets."""
        return {
            profile: cls.build_company_team_set(
                profile=profile,
                company_name=company_name,
                developer_name=developer_name,
                workspace=workspace,
            )
            for profile in ("startup", "growth", "enterprise", "agency", "open_source")
        }

    @staticmethod
    def _profile_description(profile: str) -> str:
        descriptions = {
            "startup": "Fast iteration with tight feedback loops and minimal process overhead.",
            "growth": "Balanced speed and governance while scaling engineering throughput.",
            "enterprise": "Compliance-heavy delivery with strong approval and release controls.",
            "agency": "Client-delivery focused execution with predictable reporting outputs.",
            "open_source": "Community-first collaboration with maintainability and contributor hygiene.",
        }
        return descriptions[profile]

    @classmethod
    def _profile_overrides(cls, profile: str) -> dict[str, object]:
        if profile == "startup":
            return {
                "constraints": {"allow_mutations": False, "stop_when": "validation_report_pass"},
                "context": {"deploy_target": "staging"},
                "approvals": {"PeerReviewSignoff": True, "HumanApprovalGate": True},
                "objective_prefix": "Startup",
            }
        if profile == "growth":
            return {
                "constraints": {"allow_mutations": False, "stop_when": "release_notes_generated"},
                "context": {"deploy_target": "staging"},
                "approvals": {"PeerReviewSignoff": True, "HumanApprovalGate": True, "role:PM": True},
                "objective_prefix": "Growth",
            }
        if profile == "enterprise":
            return {
                "constraints": {"allow_mutations": False, "stop_when": "prod_release_ready"},
                "context": {"deploy_target": "prod"},
                "approvals": {
                    "PeerReviewSignoff": True,
                    "HumanApprovalGate": True,
                    "ReleaseManagerSignoffIfProd": True,
                    "role:CTO": True,
                },
                "objective_prefix": "Enterprise",
            }
        if profile == "agency":
            return {
                "constraints": {"allow_mutations": False, "stop_when": "client_handoff_packet_ready"},
                "context": {"deploy_target": "staging"},
                "approvals": {"PeerReviewSignoff": True, "HumanApprovalGate": True, "role:PM": True},
                "objective_prefix": "Agency",
            }
        return {
            "constraints": {"allow_mutations": False, "stop_when": "community_release_prepared"},
            "context": {"deploy_target": "staging"},
            "approvals": {"PeerReviewSignoff": True, "HumanApprovalGate": True},
            "objective_prefix": "Open Source",
        }

    @classmethod
    def _apply_blueprint_overrides(
        cls,
        blueprint: DeveloperTeamBlueprint,
        overrides: dict[str, object],
        *,
        profile: str,
        company_name: str,
    ) -> DeveloperTeamBlueprint:
        updated = deepcopy(blueprint)
        updated.use_case = f"{profile}_{updated.use_case}"
        updated.name = f"{company_name}-{profile}-{updated.name}"
        updated.mission = f"[{profile}] {updated.mission}"

        updated.default_constraints.update(dict(overrides.get("constraints", {})))
        updated.default_context.update(dict(overrides.get("context", {})))
        updated.default_approvals.update(dict(overrides.get("approvals", {})))

        prefix = str(overrides.get("objective_prefix", profile.title()))
        updated.starter_objectives = [f"{prefix}: {objective}" for objective in updated.starter_objectives]
        return updated
