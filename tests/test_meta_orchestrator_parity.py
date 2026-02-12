"""Contract-parity tests for FoT meta-orchestrator and YAML bundle."""

from __future__ import annotations

from pathlib import Path

from teams.meta_orchestrator.gates import GateEngine
from teams.meta_orchestrator.ops_runtime import OpsRuntime
from teams.meta_orchestrator.spec_loader import load_bundle
from teams.nubflow.ledgers import GitLedgerAdapter
from teams.nubflow.types import LedgerCursor


def test_all_yaml_ops_have_runtime_outputs() -> None:
    bundle = load_bundle()
    runtime = OpsRuntime(bundle)

    for op in bundle.ops:
        name = str(op["name"])
        outputs = runtime.run_op(
            name,
            inputs={},
            goal="Parity check goal",
            tasc_id="parity_tasc",
            context={"workspace": str(Path.cwd())},
        )
        for required_field in op.get("OUT", []):
            assert required_field in outputs, f"op={name} missing OUT field={required_field}"


def test_gate_engine_policy_and_signoff_enforcement() -> None:
    bundle = load_bundle()
    gates = GateEngine(bundle)

    artifact_store = {
        "problem_contract": {"scope": "x"},
        "decision_log": ["a"],
        "system_map": {"components": ["api"]},
        "constraints_pack": ["small"],
        "query_plan": {"limit": 5},
    }

    gate_results = gates.evaluate(
        ["IntakeSufficiencyGate"],
        phase="post",
        record={"status": "success", "ops": ["ShaveContext"]},
        artifact_store=artifact_store,
        approvals={},
        goal_context={},
    )
    assert gate_results and gate_results[0].passed

    signoff_results = gates.evaluate_signoffs(
        ["PeerReviewSignoff"],
        phase="post",
        approvals={},
        goal_context={},
    )
    assert signoff_results and not signoff_results[0].passed
    assert signoff_results[0].hold


def test_git_ledger_adapter_real_repo_query() -> None:
    adapter = GitLedgerAdapter()
    cursor = LedgerCursor(ledger_sid=adapter.sid)

    result = adapter.query(
        query_plan={"repo_path": str(Path.cwd()), "limit": 3, "include_diff": False},
        cursor=cursor,
        budget=3,
    )

    assert result.items
    assert result.evidence_pack.get("ledger_kind") == "GitLedger"
    assert "branch" in result.evidence_pack
