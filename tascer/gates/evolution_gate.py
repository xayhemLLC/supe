"""Evolution Gate: Validates evolved solutions meet claims.

Gates check that:
1. Generated code compiles
2. Tests pass
3. Fitness meets claimed threshold
4. No regressions from previous best
"""

import json
import os
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from typing import Any


# Local GateResult to avoid tascer yaml dependency
@dataclass
class GateResult:
    """Result of a validation gate check."""
    gate_name: str
    passed: bool
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "passed": self.passed,
            "message": self.message,
            "evidence": self.evidence,
        }


# ---------------------------------------------------------------------------
# Base Gate
# ---------------------------------------------------------------------------

class Gate:
    """Base class for validation gates."""

    name: str = "base"

    def check(self, context: dict[str, Any]) -> GateResult:
        """Run the gate check.

        Args:
            context: Dictionary with relevant data

        Returns:
            GateResult with pass/fail and evidence
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Compilation Gate
# ---------------------------------------------------------------------------

class CompilationGate(Gate):
    """Validates that generated code compiles."""

    name = "compilation"

    def check(self, context: dict[str, Any]) -> GateResult:
        code = context.get("code", "")

        try:
            compile(code, "<evolved>", "exec")
            return GateResult(
                gate_name=self.name,
                passed=True,
                message="Code compiles successfully",
                evidence={"code_length": len(code)}
            )
        except SyntaxError as e:
            return GateResult(
                gate_name=self.name,
                passed=False,
                message=f"Syntax error: {e}",
                evidence={"error": str(e)}
            )


# ---------------------------------------------------------------------------
# Test Gate
# ---------------------------------------------------------------------------

class TestGate(Gate):
    """Validates that tests pass."""

    name = "test"

    _RUNNER = textwrap.dedent(
        """
        import json
        import sys

        SAFE_BUILTINS = {
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "int": int,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "pow": pow,
            "range": range,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "zip": zip,
        }

        def emit(obj):
            sys.stdout.write(json.dumps(obj))

        def main():
            try:
                payload = json.loads(sys.stdin.read() or "{}")
            except json.JSONDecodeError as exc:
                emit({"ok": False, "error": f"Invalid payload: {exc}"})
                return 0

            code = payload.get("code", "")
            test_cases = payload.get("test_cases", [])

            try:
                exec_globals = {"__builtins__": SAFE_BUILTINS}
                exec(code, exec_globals)
            except Exception as exc:
                emit({"ok": False, "error": f"Execution error: {exc}"})
                return 0

            solve = exec_globals.get("solve")
            if not callable(solve):
                emit({"ok": False, "error": "No 'solve' function found"})
                return 0

            passed = 0
            failed = 0
            failures = []

            for case in test_cases:
                if not isinstance(case, (list, tuple)) or len(case) != 2:
                    failed += 1
                    failures.append({"input": case, "error": "Invalid test case format"})
                    continue

                inp, expected = case
                try:
                    result = solve(inp)
                    if result == expected:
                        passed += 1
                    else:
                        failed += 1
                        failures.append({"input": inp, "expected": expected, "got": result})
                except Exception as exc:
                    failed += 1
                    failures.append({"input": inp, "error": str(exc)})

            emit(
                {
                    "ok": True,
                    "passed": passed,
                    "failed": failed,
                    "failures": failures[:3],
                }
            )
            return 0

        raise SystemExit(main())
        """
    ).strip()

    def __init__(self, timeout_sec: float = 5.0):
        self.timeout_sec = timeout_sec

    def _run_tests(self, code: str, test_cases: list[Any]) -> dict[str, Any]:
        payload = json.dumps({"code": code, "test_cases": test_cases})
        runner_path = None

        try:
            with tempfile.NamedTemporaryFile("w", suffix="_evolution_gate.py", delete=False) as f:
                f.write(self._RUNNER)
                runner_path = f.name

            proc = subprocess.run(
                [sys.executable, "-I", runner_path],
                input=payload,
                text=True,
                capture_output=True,
                timeout=self.timeout_sec,
                env={"PYTHONIOENCODING": "utf-8"},
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"Execution timed out after {self.timeout_sec}s"}
        except OSError as exc:
            return {"ok": False, "error": f"Failed to execute test subprocess: {exc}"}
        finally:
            if runner_path and os.path.exists(runner_path):
                os.unlink(runner_path)

        if proc.returncode != 0:
            stderr = proc.stderr.strip() or "unknown error"
            return {"ok": False, "error": f"Subprocess failed: {stderr}"}

        try:
            return json.loads(proc.stdout or "{}")
        except json.JSONDecodeError as exc:
            return {"ok": False, "error": f"Invalid subprocess output: {exc}"}

    def check(self, context: dict[str, Any]) -> GateResult:
        code = context.get("code", "")
        test_cases = context.get("test_cases", [])

        if not test_cases:
            return GateResult(
                gate_name=self.name,
                passed=True,
                message="No test cases provided",
                evidence={}
            )

        result = self._run_tests(code, test_cases)
        if not result.get("ok"):
            return GateResult(
                gate_name=self.name,
                passed=False,
                message=result.get("error", "Execution error"),
                evidence={"error": result.get("error", "Execution error")},
            )

        passed = int(result.get("passed", 0))
        failed = int(result.get("failed", 0))
        all_passed = failed == 0
        return GateResult(
            gate_name=self.name,
            passed=all_passed,
            message=f"{passed}/{passed+failed} tests passed",
            evidence={
                "passed": passed,
                "failed": failed,
                "failures": result.get("failures", []),
                "sandboxed": True,
            },
        )


# ---------------------------------------------------------------------------
# Fitness Gate
# ---------------------------------------------------------------------------

class FitnessGate(Gate):
    """Validates that fitness meets claimed threshold."""

    name = "fitness"

    def __init__(self, threshold: float = 0.0):
        self.threshold = threshold

    def check(self, context: dict[str, Any]) -> GateResult:
        claimed = context.get("claimed_fitness", 0)
        actual = context.get("actual_fitness", 0)

        passed = actual >= self.threshold and actual >= claimed * 0.9  # 10% tolerance

        return GateResult(
            gate_name=self.name,
            passed=passed,
            message=f"Fitness {actual:.2f} vs claimed {claimed:.2f} (threshold {self.threshold})",
            evidence={
                "claimed": claimed,
                "actual": actual,
                "threshold": self.threshold,
            }
        )


# ---------------------------------------------------------------------------
# Regression Gate
# ---------------------------------------------------------------------------

class RegressionGate(Gate):
    """Validates no regression from previous best."""

    name = "regression"

    def check(self, context: dict[str, Any]) -> GateResult:
        previous_best = context.get("previous_best_fitness", 0)
        current = context.get("actual_fitness", 0)

        # Allow 5% regression tolerance
        passed = current >= previous_best * 0.95

        if passed:
            improvement = ((current - previous_best) / max(0.01, previous_best)) * 100
            message = f"No regression: {current:.2f} vs previous {previous_best:.2f} ({improvement:+.1f}%)"
        else:
            regression = ((previous_best - current) / max(0.01, previous_best)) * 100
            message = f"REGRESSION: {current:.2f} vs previous {previous_best:.2f} (-{regression:.1f}%)"

        return GateResult(
            gate_name=self.name,
            passed=passed,
            message=message,
            evidence={
                "previous_best": previous_best,
                "current": current,
            }
        )


# ---------------------------------------------------------------------------
# Evolution Validator
# ---------------------------------------------------------------------------

class EvolutionValidator:
    """Runs all evolution gates and produces validation report."""

    def __init__(self, fitness_threshold: float = 0.0):
        self.gates: list[Gate] = [
            CompilationGate(),
            TestGate(),
            FitnessGate(threshold=fitness_threshold),
            RegressionGate(),
        ]

    def validate(self, context: dict[str, Any]) -> dict[str, Any]:
        """Run all gates and return validation results.

        Args:
            context: Dict with code, test_cases, fitness, etc.

        Returns:
            Dict with overall_status, gate_results, summary
        """
        results = []
        passed_gates = []
        failed_gates = []

        for gate in self.gates:
            result = gate.check(context)
            results.append(result)

            if result.passed:
                passed_gates.append(gate.name)
            else:
                failed_gates.append(gate.name)

        overall = "PASS" if not failed_gates else "FAIL"

        return {
            "overall_status": overall,
            "gates_passed": passed_gates,
            "gates_failed": failed_gates,
            "gate_results": [r.to_dict() for r in results],
            "summary": f"{len(passed_gates)}/{len(self.gates)} gates passed",
        }


# ---------------------------------------------------------------------------
# Quick Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    validator = EvolutionValidator(fitness_threshold=50.0)

    # Test context
    context = {
        "code": "def solve(x): return x * 2",
        "test_cases": [(2, 4), (3, 6), (5, 10)],
        "claimed_fitness": 80.0,
        "actual_fitness": 85.0,
        "previous_best_fitness": 75.0,
    }

    result = validator.validate(context)

    print("=" * 50)
    print("EVOLUTION VALIDATION RESULT")
    print("=" * 50)
    print(f"Overall: {result['overall_status']}")
    print(f"Summary: {result['summary']}")
    print(f"Passed: {result['gates_passed']}")
    print(f"Failed: {result['gates_failed']}")
