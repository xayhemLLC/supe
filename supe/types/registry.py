"""Registry for "supe types" (role-style entrypoints)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SupeTypeSpec:
    """User-facing description for a runnable supe type."""

    key: str
    title: str
    description: str


_TYPE_SPECS: tuple[SupeTypeSpec, ...] = (
    SupeTypeSpec(
        key="backend-engineer",
        title="Backend Engineer",
        description="Daily backend ticket loop (intake -> plan -> review -> execute -> validate -> ship).",
    ),
    SupeTypeSpec(
        key="qa-engineer",
        title="QA Engineer",
        description="Validation-first daily loop (focus on test plans, checks, and release readiness).",
    ),
    SupeTypeSpec(
        key="pm",
        title="Product Manager",
        description="Roadmap/policy/objective synthesis loop using the company guidance team.",
    ),
    SupeTypeSpec(
        key="staff-engineer",
        title="Staff Engineer",
        description="Architecture and technical direction loop using the company guidance team.",
    ),
    SupeTypeSpec(
        key="sre",
        title="SRE",
        description="Reliability and delivery health loop (observability + risk + rollout focus).",
    ),
    SupeTypeSpec(
        key="security-reviewer",
        title="Security Reviewer",
        description="Security review and risk triage loop (safe-by-default, evidence-driven).",
    ),
    SupeTypeSpec(
        key="release-manager",
        title="Release Manager",
        description="Release readiness and signoff loop (staging/prod gating, audit outputs).",
    ),
    SupeTypeSpec(
        key="gfx-designer",
        title="GFX Designer",
        description="Design loop for a graphics subagent and its contracts/guardrails.",
    ),
    SupeTypeSpec(
        key="founder",
        title="Founder",
        description="Company-direction loop (priorities, constraints, decisions, and next actions).",
    ),
)


def list_supe_types() -> list[SupeTypeSpec]:
    return list(_TYPE_SPECS)


def get_supe_type(key: str) -> SupeTypeSpec | None:
    normalized = key.strip().lower()
    for spec in _TYPE_SPECS:
        if spec.key == normalized:
            return spec
    return None
