"""Optimization capabilities."""

from typing import Dict, Any, List, Callable, Optional, Tuple
from dataclasses import dataclass


@dataclass
class OptimizationResult:
    """Result of an optimization."""
    optimal_value: Any
    optimal_score: float
    candidates_evaluated: int
    method: str


class Optimizer:
    """Performs optimization and finds optimal solutions."""

    def execute(self, problem_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimization.

        Args:
            problem_text: The problem statement
            context: Context including candidates and objective function

        Returns:
            Result dictionary
        """
        # Get candidates and objective function
        candidates = context.get("candidates")
        if not candidates:
            return {"success": False, "error": "No candidates provided"}

        objective = context.get("objective_function")
        if not objective:
            return {"success": False, "error": "No objective function provided"}

        # Determine if maximizing or minimizing
        maximize = context.get("maximize", True)

        # Perform optimization
        result = self.find_optimal(candidates, objective, maximize)

        return {
            "success": True,
            "optimal_value": result.optimal_value,
            "optimal_score": result.optimal_score,
            "candidates_evaluated": result.candidates_evaluated,
            "method": result.method,
        }

    def find_optimal(
        self,
        candidates: List[Any],
        objective: Callable[[Any], float],
        maximize: bool = True
    ) -> OptimizationResult:
        """Find optimal candidate.

        Args:
            candidates: List of candidates
            objective: Objective function to optimize
            maximize: Whether to maximize (True) or minimize (False)

        Returns:
            OptimizationResult
        """
        if not candidates:
            raise ValueError("No candidates to optimize over")

        best_value = None
        best_score = float('-inf') if maximize else float('inf')
        evaluated = 0

        for candidate in candidates:
            try:
                score = objective(candidate)
                evaluated += 1

                if maximize and score > best_score:
                    best_score = score
                    best_value = candidate
                elif not maximize and score < best_score:
                    best_score = score
                    best_value = candidate

            except Exception as e:
                # Skip candidates that fail evaluation
                continue

        return OptimizationResult(
            optimal_value=best_value,
            optimal_score=best_score,
            candidates_evaluated=evaluated,
            method="exhaustive_search",
        )

    def find_minimum(
        self,
        candidates: List[Any],
        objective: Callable[[Any], float]
    ) -> OptimizationResult:
        """Find candidate with minimum objective value.

        Args:
            candidates: List of candidates
            objective: Objective function

        Returns:
            OptimizationResult
        """
        return self.find_optimal(candidates, objective, maximize=False)

    def find_maximum(
        self,
        candidates: List[Any],
        objective: Callable[[Any], float]
    ) -> OptimizationResult:
        """Find candidate with maximum objective value.

        Args:
            candidates: List of candidates
            objective: Objective function

        Returns:
            OptimizationResult
        """
        return self.find_optimal(candidates, objective, maximize=True)

    def pareto_optimal(
        self,
        candidates: List[Any],
        objectives: List[Callable[[Any], float]],
        maximize: List[bool]
    ) -> List[Any]:
        """Find Pareto-optimal candidates (multi-objective).

        Args:
            candidates: List of candidates
            objectives: List of objective functions
            maximize: Whether to maximize each objective

        Returns:
            List of Pareto-optimal candidates
        """
        if len(objectives) != len(maximize):
            raise ValueError("Length of objectives and maximize must match")

        # Evaluate all candidates on all objectives
        evaluations = []
        for candidate in candidates:
            scores = []
            for obj in objectives:
                try:
                    scores.append(obj(candidate))
                except:
                    scores.append(None)
            evaluations.append((candidate, scores))

        # Find Pareto frontier
        pareto_optimal = []

        for i, (cand_i, scores_i) in enumerate(evaluations):
            if None in scores_i:
                continue

            is_dominated = False

            for j, (cand_j, scores_j) in enumerate(evaluations):
                if i == j or None in scores_j:
                    continue

                # Check if j dominates i
                dominates = True
                for k in range(len(objectives)):
                    if maximize[k]:
                        if scores_j[k] <= scores_i[k]:
                            dominates = False
                            break
                    else:
                        if scores_j[k] >= scores_i[k]:
                            dominates = False
                            break

                if dominates:
                    is_dominated = True
                    break

            if not is_dominated:
                pareto_optimal.append(cand_i)

        return pareto_optimal

    def constrained_optimization(
        self,
        candidates: List[Any],
        objective: Callable[[Any], float],
        constraints: List[Callable[[Any], bool]],
        maximize: bool = True
    ) -> OptimizationResult:
        """Optimize with constraints.

        Args:
            candidates: List of candidates
            objective: Objective function
            constraints: List of constraint functions (return True if satisfied)
            maximize: Whether to maximize

        Returns:
            OptimizationResult
        """
        # Filter to feasible candidates
        feasible = []
        for candidate in candidates:
            if all(constraint(candidate) for constraint in constraints):
                feasible.append(candidate)

        if not feasible:
            return OptimizationResult(
                optimal_value=None,
                optimal_score=float('nan'),
                candidates_evaluated=len(candidates),
                method="constrained_exhaustive_search_no_feasible",
            )

        result = self.find_optimal(feasible, objective, maximize)
        result.method = "constrained_exhaustive_search"
        result.candidates_evaluated = len(candidates)

        return result

    def greedy_selection(
        self,
        items: List[Any],
        value_fn: Callable[[Any], float],
        capacity: float,
        size_fn: Callable[[Any], float]
    ) -> Tuple[List[Any], float]:
        """Greedy selection (e.g., fractional knapsack).

        Args:
            items: List of items
            value_fn: Function to get item value
            capacity: Total capacity
            size_fn: Function to get item size

        Returns:
            Tuple of (selected_items, total_value)
        """
        # Sort by value/size ratio (greedy criterion)
        items_with_ratio = [
            (item, value_fn(item) / size_fn(item) if size_fn(item) > 0 else float('inf'))
            for item in items
        ]
        items_with_ratio.sort(key=lambda x: x[1], reverse=True)

        selected = []
        total_value = 0.0
        remaining_capacity = capacity

        for item, ratio in items_with_ratio:
            size = size_fn(item)
            if size <= remaining_capacity:
                selected.append(item)
                total_value += value_fn(item)
                remaining_capacity -= size

        return selected, total_value
