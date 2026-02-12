"""YAML bundle loading for the FoT meta-orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class BundleSpec:
    """Normalized runtime view over the orchestrator bundle."""

    raw: dict[str, Any]

    @property
    def bundle(self) -> dict[str, Any]:
        return self.raw.get("Bundle", {})

    @property
    def flow_of_time_spec(self) -> dict[str, Any]:
        return self.raw.get("FlowOfTimeSpec", {})

    @property
    def templates(self) -> dict[str, Any]:
        return self.raw.get("Templates", {})

    @property
    def workflows(self) -> list[dict[str, Any]]:
        return list(self.raw.get("Workflows", []))

    @property
    def ops(self) -> list[dict[str, Any]]:
        return list(self.raw.get("Ops", []))

    @property
    def gates(self) -> list[dict[str, Any]]:
        return list(self.raw.get("Gates", []))

    @property
    def signoffs(self) -> list[dict[str, Any]]:
        return list(self.raw.get("Signoffs", []))

    @property
    def orchestrator(self) -> dict[str, Any]:
        return self.raw.get("MetaOrchestrator", {})

    @property
    def artifact_types(self) -> list[dict[str, Any]]:
        return list(self.raw.get("ArtifactTypes", []))

    def gate_index(self) -> dict[str, dict[str, Any]]:
        return {gate["name"]: gate for gate in self.gates if "name" in gate}

    def signoff_index(self) -> dict[str, dict[str, Any]]:
        return {item["name"]: item for item in self.signoffs if "name" in item}

    def op_index(self) -> dict[str, dict[str, Any]]:
        return {op["name"]: op for op in self.ops if "name" in op}

    def artifact_type_names(self) -> set[str]:
        return {str(item.get("name")) for item in self.artifact_types if item.get("name")}


def default_bundle_path() -> Path:
    return Path(__file__).parent / "specs" / "flow_of_time_v0_0_0.yaml"


def load_bundle(path: str | Path | None = None) -> BundleSpec:
    """Load bundle YAML file from disk and return a normalized spec."""
    bundle_path = Path(path) if path else default_bundle_path()
    with bundle_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    normalized = normalize_bundle(raw)
    validate_bundle(normalized)
    return BundleSpec(raw=normalized)


def load_bundle_from_text(yaml_text: str) -> BundleSpec:
    """Load a bundle from in-memory YAML text."""
    raw = yaml.safe_load(yaml_text) or {}
    normalized = normalize_bundle(raw)
    validate_bundle(normalized)
    return BundleSpec(raw=normalized)


def normalize_bundle(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy keys and naming conventions."""
    data = dict(raw)

    # Backward compatibility with prior naming in drafts.
    if "FlowOfTimeSpec" not in data and "NubFlowSpec" in data:
        data["FlowOfTimeSpec"] = data.pop("NubFlowSpec")

    flow = data.get("FlowOfTimeSpec") or {}
    if flow.get("name", "").lower().startswith("nubflow"):
        flow["name"] = "Flow of Time (FoT)"
    if "version" not in flow:
        flow["version"] = "0.0.0"
    data["FlowOfTimeSpec"] = flow

    bundle = data.get("Bundle") or {}
    if not bundle.get("version"):
        bundle["version"] = "0.0.0"
    data["Bundle"] = bundle

    return data


def validate_bundle(raw: dict[str, Any]) -> None:
    """Validate minimal bundle shape for runtime use."""
    required_keys = {
        "Bundle",
        "FlowOfTimeSpec",
        "Ops",
        "Templates",
        "Workflows",
        "MetaOrchestrator",
    }
    missing = sorted(key for key in required_keys if key not in raw)
    if missing:
        raise ValueError(f"Bundle missing required keys: {', '.join(missing)}")

    templates = raw.get("Templates") or {}
    if not isinstance(templates, dict) or not templates:
        raise ValueError("Templates must be a non-empty mapping")

    workflows = raw.get("Workflows") or []
    if not isinstance(workflows, list) or not workflows:
        raise ValueError("Workflows must contain at least one workflow")

    for workflow in workflows:
        if "name" not in workflow or "pillars" not in workflow:
            raise ValueError("Each workflow requires 'name' and 'pillars'")

    for workflow in workflows:
        for pillar_name in workflow.get("pillars", []):
            if pillar_name not in templates:
                raise ValueError(f"Workflow references unknown pillar template: {pillar_name}")

    flow_states = set(raw.get("FlowOfTimeSpec", {}).get("states") or [])
    expected_states = {
        "nub::enter",
        "nub::absorb",
        "nub::store",
        "nub::route",
        "nub::transform",
        "nub::finalize",
        "nub::overlord_commit",
        "nub::exit",
        "nub::hold",
        "nub::error",
    }
    missing_states = sorted(expected_states - flow_states)
    if missing_states:
        raise ValueError(f"FlowOfTimeSpec missing required states: {', '.join(missing_states)}")

    op_index = {op.get("name"): op for op in raw.get("Ops", []) if op.get("name")}
    if not op_index:
        raise ValueError("Ops must contain at least one op")

    gates = {gate.get("name"): gate for gate in raw.get("Gates", []) if gate.get("name")}
    signoffs = {item.get("name"): item for item in raw.get("Signoffs", []) if item.get("name")}
    artifact_names = {str(item.get("name")) for item in raw.get("ArtifactTypes", []) if item.get("name")}

    for name, template in templates.items():
        for op_name in template.get("ops") or []:
            if op_name not in op_index:
                raise ValueError(f"Template '{name}' references unknown op '{op_name}'")

        gates_cfg = template.get("gates") or {}
        for phase in ("pre", "post"):
            for gate_name in gates_cfg.get(phase) or []:
                if gate_name not in gates:
                    raise ValueError(f"Template '{name}' references unknown gate '{gate_name}'")

        signoff_cfg = template.get("signoffs") or {}
        for phase in ("pre", "post"):
            for signoff_name in signoff_cfg.get(phase) or []:
                if signoff_name not in signoffs:
                    raise ValueError(f"Template '{name}' references unknown signoff '{signoff_name}'")

        for field_name in ("IN", "OUT"):
            for artifact in template.get(field_name) or []:
                if artifact_names and artifact not in artifact_names:
                    raise ValueError(
                        f"Template '{name}' references unknown artifact type '{artifact}' in {field_name}"
                    )
