"""Hypothesis generation and testing capabilities."""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass


@dataclass
class Hypothesis:
    """Represents a hypothesis to test."""
    name: str
    description: str
    test_function: Callable
    confidence: float = 0.0
    evidence_count: int = 0
    supporting_evidence: int = 0


class HypothesisTesting:
    """Generates and tests hypotheses."""

    def execute(self, problem_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hypothesis testing.

        Args:
            problem_text: The problem statement
            context: Context including hypotheses and test data

        Returns:
            Result dictionary
        """
        # Get hypotheses from context
        hypotheses = context.get("hypotheses", [])
        if not hypotheses:
            return {"success": False, "error": "No hypotheses to test"}

        # Get test data
        test_data = context.get("test_data", [])
        if not test_data:
            return {"success": False, "error": "No test data provided"}

        # Test each hypothesis
        results = []

        for hyp in hypotheses:
            if not isinstance(hyp, Hypothesis):
                # Convert dict to Hypothesis
                hyp = Hypothesis(
                    name=hyp.get("name", "unnamed"),
                    description=hyp.get("description", ""),
                    test_function=hyp.get("test_function"),
                )

            supporting = 0
            contradicting = 0
            evidence_details = []

            for data_point in test_data:
                try:
                    result = hyp.test_function(data_point)
                    if result:
                        supporting += 1
                        evidence_details.append({"data": data_point, "result": "support"})
                    else:
                        contradicting += 1
                        evidence_details.append({"data": data_point, "result": "contradict"})
                except Exception as e:
                    evidence_details.append({"data": data_point, "error": str(e)})

            total = supporting + contradicting
            confidence = supporting / total if total > 0 else 0.0

            results.append({
                "hypothesis": hyp.name,
                "description": hyp.description,
                "supporting": supporting,
                "contradicting": contradicting,
                "confidence": confidence,
                "evidence": evidence_details,
                "verdict": self._get_verdict(confidence, supporting, contradicting),
            })

        # Find best hypothesis
        best = max(results, key=lambda r: r["confidence"])

        return {
            "success": True,
            "all_results": results,
            "best_hypothesis": best,
            "recommendation": f"Use hypothesis: {best['hypothesis']} (confidence: {best['confidence']:.1%})",
        }

    def _get_verdict(self, confidence: float, supporting: int, contradicting: int) -> str:
        """Determine verdict based on evidence."""
        if contradicting == 0 and supporting > 0:
            return "CONFIRMED"
        elif confidence >= 0.9:
            return "STRONGLY_SUPPORTED"
        elif confidence >= 0.7:
            return "SUPPORTED"
        elif confidence >= 0.5:
            return "WEAKLY_SUPPORTED"
        elif supporting == 0:
            return "REFUTED"
        else:
            return "CONTRADICTED"

    def generate_hypotheses_for_pattern(
        self,
        data_points: List[Any],
        pattern_type: str = "numeric"
    ) -> List[Hypothesis]:
        """Generate common hypotheses for pattern recognition.

        Args:
            data_points: Data points to analyze
            pattern_type: Type of pattern (numeric, sequence, grid)

        Returns:
            List of generated hypotheses
        """
        hypotheses = []

        if pattern_type == "numeric" and all(isinstance(x, (int, float)) for x in data_points):
            # Arithmetic sequence
            hypotheses.append(Hypothesis(
                name="arithmetic_sequence",
                description="Values form an arithmetic sequence (constant difference)",
                test_function=lambda dp: self._test_arithmetic_sequence(dp),
            ))

            # Geometric sequence
            hypotheses.append(Hypothesis(
                name="geometric_sequence",
                description="Values form a geometric sequence (constant ratio)",
                test_function=lambda dp: self._test_geometric_sequence(dp),
            ))

            # Squares
            hypotheses.append(Hypothesis(
                name="perfect_squares",
                description="Values are perfect squares",
                test_function=lambda dp: all(int(x**0.5)**2 == x for x in dp),
            ))

        elif pattern_type == "grid":
            # Row patterns
            hypotheses.append(Hypothesis(
                name="row_sum_constant",
                description="Each row sums to the same value",
                test_function=lambda grid: self._test_row_sum_constant(grid),
            ))

            # Column patterns
            hypotheses.append(Hypothesis(
                name="column_sum_constant",
                description="Each column sums to the same value",
                test_function=lambda grid: self._test_column_sum_constant(grid),
            ))

        return hypotheses

    def _test_arithmetic_sequence(self, values: List[float]) -> bool:
        """Test if values form an arithmetic sequence."""
        if len(values) < 2:
            return True

        differences = [values[i+1] - values[i] for i in range(len(values) - 1)]
        return all(abs(d - differences[0]) < 1e-10 for d in differences)

    def _test_geometric_sequence(self, values: List[float]) -> bool:
        """Test if values form a geometric sequence."""
        if len(values) < 2 or any(v == 0 for v in values[:-1]):
            return False

        ratios = [values[i+1] / values[i] for i in range(len(values) - 1)]
        return all(abs(r - ratios[0]) < 1e-10 for r in ratios)

    def _test_row_sum_constant(self, grid: List[List[int]]) -> bool:
        """Test if all rows have same sum."""
        if not grid:
            return True

        row_sums = [sum(row) for row in grid]
        return all(s == row_sums[0] for s in row_sums)

    def _test_column_sum_constant(self, grid: List[List[int]]) -> bool:
        """Test if all columns have same sum."""
        if not grid or not grid[0]:
            return True

        n_cols = len(grid[0])
        col_sums = [sum(grid[i][j] for i in range(len(grid))) for j in range(n_cols)]
        return all(s == col_sums[0] for s in col_sums)
