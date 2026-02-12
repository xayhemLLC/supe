"""Artifact naming and resolution helpers for the meta-orchestrator."""

from __future__ import annotations

import re
from typing import Any

_ARTIFACT_ALIASES: dict[str, list[str]] = {
    "Ticket": ["ticket"],
    "ProblemContract": ["problem_contract"],
    "DecisionLog": ["decision_log", "decisions"],
    "SystemMap": ["system_map"],
    "ConstraintsPack": ["constraints_pack", "constraints"],
    "QueryPlan": ["query_plan"],
    "EvidencePack": ["evidence_pack"],
    "ExecutionPlan": ["execution_plan"],
    "ValidationPlan": ["validation_plan"],
    "RolloutPlan": ["rollout_plan"],
    "ApprovedPlan": ["approved_plan", "execution_plan"],
    "ChangeSet": ["change_set", "changeset"],
    "ValidationReport": ["validation_report"],
    "Deployment": ["deployment"],
    "ReleaseNotes": ["release_notes"],
    "LearningNote": ["learning_note"],
    "ToolForgeRequest": ["tool_forge_request", "tool_forge_requests"],
}


def artifact_key(name: str) -> str:
    """Convert artifact names (e.g., ``ProblemContract``) to snake_case keys."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()


def artifact_aliases(name: str) -> list[str]:
    """Return normalized key candidates for a given artifact type name."""
    aliases = list(_ARTIFACT_ALIASES.get(name, []))
    key = artifact_key(name)
    if key not in aliases:
        aliases.insert(0, key)
    return aliases


def extract_required_inputs(artifact_store: dict[str, Any], artifact_names: list[str]) -> dict[str, Any]:
    """Collect required artifact values from a mixed-key artifact store."""
    inputs: dict[str, Any] = {}
    for artifact in artifact_names:
        for alias in artifact_aliases(artifact):
            if alias in artifact_store:
                inputs[alias] = artifact_store[alias]
                break
    return inputs


def merge_artifact_outputs(
    artifact_store: dict[str, Any],
    declared_out_artifacts: list[str],
    op_output: dict[str, Any],
) -> dict[str, Any]:
    """Merge operation output data into the shared artifact store."""
    merged = dict(artifact_store)

    # Store all op outputs verbatim first for downstream debugging and flexibility.
    for key, value in op_output.items():
        merged[key] = value

    # Ensure declared artifact outputs are surfaced under canonical names.
    for artifact in declared_out_artifacts:
        aliases = artifact_aliases(artifact)
        value = None
        for alias in aliases:
            if alias in op_output:
                value = op_output[alias]
                break

        # Last-resort fallback: exact case-insensitive key match.
        if value is None:
            for key, candidate in op_output.items():
                if key.lower() == artifact.lower() or key.lower() == artifact_key(artifact):
                    value = candidate
                    break

        if value is not None:
            for alias in aliases:
                merged[alias] = value

    return merged


def artifacts_present(artifact_store: dict[str, Any], artifact_names: list[str]) -> tuple[bool, list[str]]:
    """Return whether all artifacts are present and list missing artifacts."""
    missing: list[str] = []
    for artifact in artifact_names:
        if not any(alias in artifact_store for alias in artifact_aliases(artifact)):
            missing.append(artifact)
    return not missing, missing
