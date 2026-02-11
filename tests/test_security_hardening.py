"""Security hardening regression tests."""

from tascer.gates.evolution_gate import TestGate as EvolutionTestGate


def test_evolution_test_gate_runs_in_subprocess_and_passes() -> None:
    gate = EvolutionTestGate(timeout_sec=2.0)
    result = gate.check(
        {
            "code": "def solve(x):\n    return x * 2\n",
            "test_cases": [(2, 4), (3, 6)],
        }
    )
    assert result.passed is True
    assert result.evidence.get("sandboxed") is True


def test_evolution_test_gate_blocks_import_builtins() -> None:
    gate = EvolutionTestGate(timeout_sec=2.0)
    result = gate.check(
        {
            "code": "import os\n\ndef solve(x):\n    return os.getenv('HOME', '')\n",
            "test_cases": [(1, "")],
        }
    )
    assert result.passed is False
    assert "error" in result.evidence
