"""Planner Agent - Software architect agent for CUF DESIGN phase.

The planner agent:
- Analyzes codebases to understand architecture
- Designs implementation plans
- Identifies critical files and dependencies
- Considers trade-offs and alternatives
- Outputs structured plans for BUILD phase

This agent operates in the EXPLORE → DEFINE → DESIGN phases of CUF.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from tasc import Tasc, TascPhase


class PlanStatus(Enum):
    """Status of a plan."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class FileChange:
    """A planned change to a file."""

    path: str
    change_type: str  # "create", "modify", "delete", "rename"
    description: str
    estimated_lines: int | None = None
    dependencies: list[str] = field(default_factory=list)
    risk_level: str = "low"  # "low", "medium", "high"

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "change_type": self.change_type,
            "description": self.description,
            "estimated_lines": self.estimated_lines,
            "dependencies": self.dependencies,
            "risk_level": self.risk_level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FileChange:
        return cls(
            path=data["path"],
            change_type=data["change_type"],
            description=data["description"],
            estimated_lines=data.get("estimated_lines"),
            dependencies=data.get("dependencies", []),
            risk_level=data.get("risk_level", "low"),
        )


@dataclass
class PlanStep:
    """A step in the implementation plan."""

    step_number: int
    title: str
    description: str
    file_changes: list[FileChange] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    validation: str | None = None  # How to verify this step
    rollback: str | None = None  # How to undo this step
    depends_on: list[int] = field(default_factory=list)  # Step numbers

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_number": self.step_number,
            "title": self.title,
            "description": self.description,
            "file_changes": [fc.to_dict() for fc in self.file_changes],
            "commands": self.commands,
            "validation": self.validation,
            "rollback": self.rollback,
            "depends_on": self.depends_on,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanStep:
        return cls(
            step_number=data["step_number"],
            title=data["title"],
            description=data["description"],
            file_changes=[FileChange.from_dict(fc) for fc in data.get("file_changes", [])],
            commands=data.get("commands", []),
            validation=data.get("validation"),
            rollback=data.get("rollback"),
            depends_on=data.get("depends_on", []),
        )


@dataclass
class ArchitecturalDecision:
    """A decision made during planning."""

    title: str
    context: str
    decision: str
    alternatives: list[str] = field(default_factory=list)
    consequences: list[str] = field(default_factory=list)
    rationale: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "context": self.context,
            "decision": self.decision,
            "alternatives": self.alternatives,
            "consequences": self.consequences,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArchitecturalDecision:
        return cls(
            title=data["title"],
            context=data["context"],
            decision=data["decision"],
            alternatives=data.get("alternatives", []),
            consequences=data.get("consequences", []),
            rationale=data.get("rationale"),
        )


@dataclass
class ImplementationPlan:
    """A complete implementation plan."""

    id: str
    title: str
    goal: str
    status: PlanStatus = PlanStatus.DRAFT

    # Context
    codebase_analysis: str | None = None
    existing_patterns: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    # Plan content
    summary: str | None = None
    steps: list[PlanStep] = field(default_factory=list)
    decisions: list[ArchitecturalDecision] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None).isoformat())
    updated_at: str | None = None
    approved_at: str | None = None
    approved_by: str | None = None

    # Linked tasc
    tasc_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "goal": self.goal,
            "status": self.status.value,
            "codebase_analysis": self.codebase_analysis,
            "existing_patterns": self.existing_patterns,
            "constraints": self.constraints,
            "summary": self.summary,
            "steps": [s.to_dict() for s in self.steps],
            "decisions": [d.to_dict() for d in self.decisions],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
            "tasc_id": self.tasc_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ImplementationPlan:
        return cls(
            id=data["id"],
            title=data["title"],
            goal=data["goal"],
            status=PlanStatus(data.get("status", "draft")),
            codebase_analysis=data.get("codebase_analysis"),
            existing_patterns=data.get("existing_patterns", []),
            constraints=data.get("constraints", []),
            summary=data.get("summary"),
            steps=[PlanStep.from_dict(s) for s in data.get("steps", [])],
            decisions=[ArchitecturalDecision.from_dict(d) for d in data.get("decisions", [])],
            created_at=data.get("created_at", datetime.now(timezone.utc).replace(tzinfo=None).isoformat()),
            updated_at=data.get("updated_at"),
            approved_at=data.get("approved_at"),
            approved_by=data.get("approved_by"),
            tasc_id=data.get("tasc_id"),
        )

    def to_markdown(self) -> str:
        """Export plan as readable markdown."""
        lines = [
            f"# {self.title}",
            "",
            f"**Status:** {self.status.value}",
            f"**Created:** {self.created_at}",
            "",
            "## Goal",
            "",
            self.goal,
            "",
        ]

        if self.summary:
            lines.extend(["## Summary", "", self.summary, ""])

        if self.codebase_analysis:
            lines.extend(["## Codebase Analysis", "", self.codebase_analysis, ""])

        if self.existing_patterns:
            lines.extend(["## Existing Patterns", ""])
            for pattern in self.existing_patterns:
                lines.append(f"- {pattern}")
            lines.append("")

        if self.constraints:
            lines.extend(["## Constraints", ""])
            for constraint in self.constraints:
                lines.append(f"- {constraint}")
            lines.append("")

        if self.decisions:
            lines.extend(["## Architectural Decisions", ""])
            for i, decision in enumerate(self.decisions, 1):
                lines.extend([
                    f"### ADR-{i}: {decision.title}",
                    "",
                    f"**Context:** {decision.context}",
                    "",
                    f"**Decision:** {decision.decision}",
                    "",
                ])
                if decision.alternatives:
                    lines.append("**Alternatives Considered:**")
                    for alt in decision.alternatives:
                        lines.append(f"- {alt}")
                    lines.append("")
                if decision.rationale:
                    lines.extend([f"**Rationale:** {decision.rationale}", ""])

        if self.steps:
            lines.extend(["## Implementation Steps", ""])
            for step in self.steps:
                lines.extend([
                    f"### Step {step.step_number}: {step.title}",
                    "",
                    step.description,
                    "",
                ])
                if step.file_changes:
                    lines.append("**File Changes:**")
                    for fc in step.file_changes:
                        risk = f" ⚠️ {fc.risk_level}" if fc.risk_level != "low" else ""
                        lines.append(f"- `{fc.path}` ({fc.change_type}){risk}: {fc.description}")
                    lines.append("")
                if step.commands:
                    lines.append("**Commands:**")
                    lines.append("```bash")
                    for cmd in step.commands:
                        lines.append(cmd)
                    lines.append("```")
                    lines.append("")
                if step.validation:
                    lines.extend([f"**Validation:** {step.validation}", ""])

        return "\n".join(lines)


class PlannerAgent:
    """Agent for creating implementation plans.

    The planner agent operates in the EXPLORE → DEFINE → DESIGN phases,
    analyzing codebases and creating structured implementation plans.
    """

    def __init__(
        self,
        working_dir: str | None = None,
        plans_dir: str | None = None,
    ):
        self.working_dir = working_dir or os.getcwd()
        self.plans_dir = plans_dir or os.path.join(self.working_dir, ".supe", "plans")
        os.makedirs(self.plans_dir, exist_ok=True)

    def analyze_codebase(
        self,
        focus_paths: list[str] | None = None,
        patterns_to_find: list[str] | None = None,
    ) -> dict[str, Any]:
        """Analyze codebase structure and patterns."""
        analysis: dict[str, Any] = {
            "root": self.working_dir,
            "structure": {},
            "patterns": [],
            "technologies": [],
            "entry_points": [],
        }

        # Find key files
        key_files = [
            "package.json",
            "pyproject.toml",
            "setup.py",
            "Cargo.toml",
            "go.mod",
            "Makefile",
            "docker-compose.yml",
            "Dockerfile",
        ]

        for kf in key_files:
            path = os.path.join(self.working_dir, kf)
            if os.path.exists(path):
                analysis["technologies"].append(kf)

        # Analyze directory structure
        focus = focus_paths or [self.working_dir]
        for base in focus:
            if not os.path.exists(base):
                continue
            for root, dirs, files in os.walk(base):
                # Skip hidden and common ignore dirs
                dirs[:] = [
                    d for d in dirs
                    if not d.startswith(".")
                    and d not in ("node_modules", "__pycache__", "venv", ".venv", "dist", "build")
                ]
                rel_root = os.path.relpath(root, self.working_dir)
                if rel_root == ".":
                    rel_root = ""

                # Count files by extension
                ext_counts: dict[str, int] = {}
                for f in files:
                    if f.startswith("."):
                        continue
                    ext = os.path.splitext(f)[1] or "no_ext"
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1

                if ext_counts:
                    analysis["structure"][rel_root or "(root)"] = ext_counts

                # Stop after reasonable depth
                if rel_root.count(os.sep) > 3:
                    dirs.clear()

        # Find patterns in code (simple heuristics)
        if patterns_to_find:
            import re
            for pattern in patterns_to_find:
                try:
                    regex = re.compile(pattern)
                    for root, dirs, files in os.walk(self.working_dir):
                        dirs[:] = [d for d in dirs if not d.startswith(".")]
                        for f in files:
                            if f.endswith((".py", ".ts", ".js", ".go", ".rs")):
                                try:
                                    fpath = os.path.join(root, f)
                                    with open(fpath, encoding="utf-8", errors="ignore") as file:
                                        content = file.read()
                                    if regex.search(content):
                                        analysis["patterns"].append({
                                            "pattern": pattern,
                                            "file": os.path.relpath(fpath, self.working_dir),
                                        })
                                except Exception:
                                    continue
                except re.error:
                    continue

        return analysis

    def create_plan(
        self,
        goal: str,
        title: str | None = None,
        constraints: list[str] | None = None,
        tasc: Tasc | None = None,
    ) -> ImplementationPlan:
        """Create a new implementation plan."""
        import uuid

        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        plan = ImplementationPlan(
            id=plan_id,
            title=title or f"Plan: {goal[:50]}",
            goal=goal,
            constraints=constraints or [],
            tasc_id=tasc.id if tasc else None,
        )

        # Analyze codebase
        analysis = self.analyze_codebase()
        plan.codebase_analysis = json.dumps(analysis["structure"], indent=2)
        plan.existing_patterns = [
            f"Uses {tech}" for tech in analysis["technologies"]
        ]

        return plan

    def add_step(
        self,
        plan: ImplementationPlan,
        title: str,
        description: str,
        file_changes: list[dict[str, Any]] | None = None,
        commands: list[str] | None = None,
        validation: str | None = None,
        depends_on: list[int] | None = None,
    ) -> PlanStep:
        """Add a step to a plan."""
        step_number = len(plan.steps) + 1

        step = PlanStep(
            step_number=step_number,
            title=title,
            description=description,
            file_changes=[FileChange.from_dict(fc) for fc in (file_changes or [])],
            commands=commands or [],
            validation=validation,
            depends_on=depends_on or [],
        )

        plan.steps.append(step)
        plan.updated_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

        return step

    def add_decision(
        self,
        plan: ImplementationPlan,
        title: str,
        context: str,
        decision: str,
        alternatives: list[str] | None = None,
        rationale: str | None = None,
    ) -> ArchitecturalDecision:
        """Add an architectural decision to a plan."""
        adr = ArchitecturalDecision(
            title=title,
            context=context,
            decision=decision,
            alternatives=alternatives or [],
            rationale=rationale,
        )

        plan.decisions.append(adr)
        plan.updated_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

        return adr

    def save_plan(self, plan: ImplementationPlan) -> str:
        """Save plan to disk."""
        plan_path = os.path.join(self.plans_dir, f"{plan.id}.json")
        with open(plan_path, "w") as f:
            json.dump(plan.to_dict(), f, indent=2)

        # Also save markdown version
        md_path = os.path.join(self.plans_dir, f"{plan.id}.md")
        with open(md_path, "w") as f:
            f.write(plan.to_markdown())

        return plan_path

    def load_plan(self, plan_id: str) -> ImplementationPlan | None:
        """Load a plan from disk."""
        plan_path = os.path.join(self.plans_dir, f"{plan_id}.json")
        if not os.path.exists(plan_path):
            return None

        with open(plan_path) as f:
            data = json.load(f)

        return ImplementationPlan.from_dict(data)

    def list_plans(self) -> list[dict[str, Any]]:
        """List all saved plans."""
        plans = []
        for f in os.listdir(self.plans_dir):
            if f.endswith(".json"):
                plan_path = os.path.join(self.plans_dir, f)
                try:
                    with open(plan_path) as file:
                        data = json.load(file)
                    plans.append({
                        "id": data["id"],
                        "title": data["title"],
                        "status": data["status"],
                        "created_at": data["created_at"],
                    })
                except Exception:
                    continue
        return sorted(plans, key=lambda p: p["created_at"], reverse=True)

    def approve_plan(self, plan: ImplementationPlan, approved_by: str = "user") -> None:
        """Mark a plan as approved."""
        plan.status = PlanStatus.APPROVED
        plan.approved_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        plan.approved_by = approved_by
        plan.updated_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        self.save_plan(plan)

    def reject_plan(self, plan: ImplementationPlan, reason: str | None = None) -> None:
        """Mark a plan as rejected."""
        plan.status = PlanStatus.REJECTED
        plan.updated_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        if reason:
            plan.constraints.append(f"REJECTION REASON: {reason}")
        self.save_plan(plan)

    def create_tasc_from_plan(self, plan: ImplementationPlan) -> Tasc:
        """Create a Tasc from an approved plan."""
        if plan.status != PlanStatus.APPROVED:
            raise ValueError("Can only create tasc from approved plans")

        # Build testing instructions from plan steps
        testing_instructions = []
        for step in plan.steps:
            if step.validation:
                testing_instructions.append(f"Step {step.step_number}: {step.validation}")
            for cmd in step.commands:
                testing_instructions.append(f"  $ {cmd}")

        tasc = Tasc(
            id=f"tasc_from_{plan.id}",
            status="active",
            title=plan.title,
            additional_notes=plan.summary or "",
            testing_instructions="\n".join(testing_instructions),
            desired_outcome=plan.goal,
            # Set CUF fields
            phase=TascPhase.BUILD,  # Ready to build
            chosen_approach=plan.summary,
            alternatives_considered=[
                d.decision for d in plan.decisions if d.alternatives
            ],
            constraints=plan.constraints,
        )

        # Record the transition from DESIGN to BUILD
        tasc.transition_to(
            TascPhase.BUILD,
            reason=f"Plan {plan.id} approved, starting build",
        )

        return tasc


# Convenience functions
def create_plan(goal: str, **kwargs: Any) -> ImplementationPlan:
    """Create a new implementation plan."""
    agent = PlannerAgent()
    return agent.create_plan(goal, **kwargs)


def load_plan(plan_id: str) -> ImplementationPlan | None:
    """Load a plan by ID."""
    agent = PlannerAgent()
    return agent.load_plan(plan_id)


def list_plans() -> list[dict[str, Any]]:
    """List all plans."""
    agent = PlannerAgent()
    return agent.list_plans()
