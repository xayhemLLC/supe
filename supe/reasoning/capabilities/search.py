"""Search and enumeration capabilities."""

from typing import Dict, Any, List, Callable, Optional, Tuple
from itertools import product, permutations, combinations


class ExhaustiveSearch:
    """Performs exhaustive search over solution spaces."""

    def execute(self, problem_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute exhaustive search.

        Args:
            problem_text: The problem statement
            context: Context including search space and test function

        Returns:
            Result dictionary
        """
        # Get search space from context
        search_space = context.get("search_space")
        if not search_space:
            return {"success": False, "error": "No search space defined"}

        # Get test function from context
        test_fn = context.get("test_function")
        if not test_fn:
            return {"success": False, "error": "No test function defined"}

        # Perform exhaustive search
        results = []
        for candidate in search_space:
            result = test_fn(candidate)
            if result:
                results.append({
                    "candidate": candidate,
                    "result": result,
                })

        return {
            "success": len(results) > 0,
            "results": results,
            "total_tested": len(list(search_space)),
            "solutions_found": len(results),
        }

    def enumerate_factor_pairs(self, n: int) -> List[Tuple[int, int]]:
        """Enumerate all factor pairs of n.

        Args:
            n: Number to factor

        Returns:
            List of (a, b) pairs where a * b = n
        """
        if n == 0:
            return [(0, 0)]

        pairs = []
        abs_n = abs(n)

        for i in range(1, abs_n + 1):
            if abs_n % i == 0:
                j = abs_n // i
                # Consider sign combinations
                if n > 0:
                    pairs.append((i, j))
                    if i != j:
                        pairs.append((-i, -j))
                else:
                    pairs.append((i, -j))
                    pairs.append((-i, j))

        return pairs

    def enumerate_partitions(self, n: int, k: int) -> List[List[int]]:
        """Enumerate all ways to partition n into k positive integers.

        Args:
            n: Number to partition
            k: Number of parts

        Returns:
            List of partitions
        """
        if k == 1:
            return [[n]]
        if k > n:
            return []

        partitions = []

        for i in range(1, n - k + 2):
            for sub_partition in self.enumerate_partitions(n - i, k - 1):
                partitions.append([i] + sub_partition)

        return partitions

    def enumerate_combinations(self, items: List[Any], r: int) -> List[List[Any]]:
        """Enumerate all r-combinations of items.

        Args:
            items: List of items
            r: Number to choose

        Returns:
            List of combinations
        """
        return [list(c) for c in combinations(items, r)]

    def enumerate_permutations(self, items: List[Any], r: Optional[int] = None) -> List[List[Any]]:
        """Enumerate all r-permutations of items.

        Args:
            items: List of items
            r: Number to arrange (None = all)

        Returns:
            List of permutations
        """
        if r is None:
            r = len(items)
        return [list(p) for p in permutations(items, r)]

    def grid_search(
        self,
        dimensions: List[List[Any]],
        objective: Callable,
        maximize: bool = True
    ) -> Dict[str, Any]:
        """Perform grid search over multi-dimensional space.

        Args:
            dimensions: List of possible values for each dimension
            objective: Function to evaluate candidates
            maximize: Whether to maximize (True) or minimize (False)

        Returns:
            Best candidate and value
        """
        best_value = float('-inf') if maximize else float('inf')
        best_candidate = None

        for candidate in product(*dimensions):
            value = objective(candidate)

            if maximize and value > best_value:
                best_value = value
                best_candidate = candidate
            elif not maximize and value < best_value:
                best_value = value
                best_candidate = candidate

        return {
            "success": best_candidate is not None,
            "best_candidate": best_candidate,
            "best_value": best_value,
        }
