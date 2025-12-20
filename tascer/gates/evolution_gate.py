"""Evolution Gate: Validates evolved solutions meet claims.

Gates check that:
1. Generated code compiles
2. Tests pass
3. Fitness meets claimed threshold
4. No regressions from previous best
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


# Local GateResult to avoid tascer yaml dependency
@dataclass
class GateResult:
    """Result of a validation gate check."""
    gate_name: str
    passed: bool
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
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
    
    def check(self, context: Dict[str, Any]) -> GateResult:
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
    
    def check(self, context: Dict[str, Any]) -> GateResult:
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
    
    def check(self, context: Dict[str, Any]) -> GateResult:
        code = context.get("code", "")
        test_cases = context.get("test_cases", [])
        
        if not test_cases:
            return GateResult(
                gate_name=self.name,
                passed=True,
                message="No test cases provided",
                evidence={}
            )
        
        try:
            exec_globals = {}
            exec(code, exec_globals)
            
            solve = exec_globals.get("solve")
            if not solve:
                return GateResult(
                    gate_name=self.name,
                    passed=False,
                    message="No 'solve' function found",
                    evidence={}
                )
            
            passed = 0
            failed = 0
            failures = []
            
            for inp, expected in test_cases:
                try:
                    result = solve(inp)
                    if result == expected:
                        passed += 1
                    else:
                        failed += 1
                        failures.append({"input": inp, "expected": expected, "got": result})
                except Exception as e:
                    failed += 1
                    failures.append({"input": inp, "error": str(e)})
            
            all_passed = failed == 0
            return GateResult(
                gate_name=self.name,
                passed=all_passed,
                message=f"{passed}/{passed+failed} tests passed",
                evidence={"passed": passed, "failed": failed, "failures": failures[:3]}
            )
            
        except Exception as e:
            return GateResult(
                gate_name=self.name,
                passed=False,
                message=f"Execution error: {e}",
                evidence={"error": str(e)}
            )


# ---------------------------------------------------------------------------
# Fitness Gate
# ---------------------------------------------------------------------------

class FitnessGate(Gate):
    """Validates that fitness meets claimed threshold."""
    
    name = "fitness"
    
    def __init__(self, threshold: float = 0.0):
        self.threshold = threshold
    
    def check(self, context: Dict[str, Any]) -> GateResult:
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
    
    def check(self, context: Dict[str, Any]) -> GateResult:
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
        self.gates: List[Gate] = [
            CompilationGate(),
            TestGate(),
            FitnessGate(threshold=fitness_threshold),
            RegressionGate(),
        ]
    
    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
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
