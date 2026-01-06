"""Pattern matching and recognition capabilities."""

from typing import Dict, Any, List, Optional, Tuple
import re


class PatternMatcher:
    """Identifies and matches patterns in data."""

    def execute(self, problem_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pattern matching.

        Args:
            problem_text: The problem statement
            context: Context including data to analyze

        Returns:
            Result dictionary
        """
        # Get data from context
        data = context.get("data")
        if data is None:
            return {"success": False, "error": "No data to analyze"}

        # Determine data type and apply appropriate pattern matching
        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            return self._match_numeric_sequence(data, context)
        elif isinstance(data, list) and all(isinstance(row, list) for row in data):
            return self._match_grid_pattern(data, context)
        elif isinstance(data, str):
            return self._match_string_pattern(data, context)
        else:
            return {"success": False, "error": f"Unsupported data type: {type(data)}"}

    def _match_numeric_sequence(self, sequence: List[float], context: Dict[str, Any]) -> Dict[str, Any]:
        """Match patterns in numeric sequences.

        Args:
            sequence: List of numbers
            context: Additional context

        Returns:
            Result with detected patterns
        """
        patterns = []

        # Arithmetic sequence
        if len(sequence) >= 2:
            diffs = [sequence[i+1] - sequence[i] for i in range(len(sequence) - 1)]
            if all(abs(d - diffs[0]) < 1e-10 for d in diffs):
                patterns.append({
                    "type": "arithmetic",
                    "difference": diffs[0],
                    "next_value": sequence[-1] + diffs[0],
                    "formula": f"a_n = {sequence[0]} + {diffs[0]}*(n-1)",
                })

        # Geometric sequence
        if len(sequence) >= 2 and all(v != 0 for v in sequence[:-1]):
            ratios = [sequence[i+1] / sequence[i] for i in range(len(sequence) - 1)]
            if all(abs(r - ratios[0]) < 1e-10 for r in ratios):
                patterns.append({
                    "type": "geometric",
                    "ratio": ratios[0],
                    "next_value": sequence[-1] * ratios[0],
                    "formula": f"a_n = {sequence[0]} * {ratios[0]}^(n-1)",
                })

        # Polynomial (quadratic differences)
        if len(sequence) >= 3:
            second_diffs = [diffs[i+1] - diffs[i] for i in range(len(diffs) - 1)]
            if all(abs(d - second_diffs[0]) < 1e-10 for d in second_diffs):
                patterns.append({
                    "type": "polynomial_degree_2",
                    "second_difference": second_diffs[0],
                    "note": "Quadratic sequence detected",
                })

        # Fibonacci-like
        if len(sequence) >= 3:
            is_fibonacci = all(
                abs(sequence[i] - (sequence[i-1] + sequence[i-2])) < 1e-10
                for i in range(2, len(sequence))
            )
            if is_fibonacci:
                patterns.append({
                    "type": "fibonacci",
                    "next_value": sequence[-1] + sequence[-2],
                    "formula": "a_n = a_(n-1) + a_(n-2)",
                })

        return {
            "success": len(patterns) > 0,
            "patterns": patterns,
            "best_pattern": patterns[0] if patterns else None,
        }

    def _match_grid_pattern(self, grid: List[List[Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Match patterns in 2D grids.

        Args:
            grid: 2D grid of values
            context: Additional context

        Returns:
            Result with detected patterns
        """
        patterns = []

        if not grid or not grid[0]:
            return {"success": False, "error": "Empty grid"}

        rows = len(grid)
        cols = len(grid[0])

        # Row sum pattern
        row_sums = [sum(row) for row in grid]
        if all(s == row_sums[0] for s in row_sums):
            patterns.append({
                "type": "constant_row_sum",
                "value": row_sums[0],
            })

        # Column sum pattern
        col_sums = [sum(grid[i][j] for i in range(rows)) for j in range(cols)]
        if all(s == col_sums[0] for s in col_sums):
            patterns.append({
                "type": "constant_column_sum",
                "value": col_sums[0],
            })

        # Product pattern
        row_products = []
        for row in grid:
            prod = 1
            for val in row:
                prod *= val
            row_products.append(prod)

        if all(p == row_products[0] for p in row_products):
            patterns.append({
                "type": "constant_row_product",
                "value": row_products[0],
            })

        # Diagonal pattern
        if rows == cols:
            main_diag = [grid[i][i] for i in range(rows)]
            anti_diag = [grid[i][rows-1-i] for i in range(rows)]

            main_sum = sum(main_diag)
            anti_sum = sum(anti_diag)

            if main_sum == anti_sum == row_sums[0]:
                patterns.append({
                    "type": "magic_square_candidate",
                    "note": "Diagonals sum to same value as rows/columns",
                })

        # Row relationship pattern
        # Check if each row follows same formula
        for i in range(rows - 1):
            if len(grid[i]) >= 4:
                # Test: a + b + c = d
                if grid[i][0] + grid[i][1] + grid[i][2] == grid[i][3]:
                    # Check if same pattern in all rows
                    if all(
                        len(row) >= 4 and row[0] + row[1] + row[2] == row[3]
                        for row in grid
                    ):
                        patterns.append({
                            "type": "row_sum_pattern",
                            "formula": "row[0] + row[1] + row[2] = row[3]",
                        })
                        break

                # Test: a * b * c = d
                if grid[i][0] * grid[i][1] * grid[i][2] == grid[i][3]:
                    if all(
                        len(row) >= 4 and row[0] * row[1] * row[2] == row[3]
                        for row in grid
                    ):
                        patterns.append({
                            "type": "row_product_pattern",
                            "formula": "row[0] * row[1] * row[2] = row[3]",
                        })
                        break

                # Test: a * b = c, then predict d
                # Look at product mod 10
                prod_mod = (grid[i][0] * grid[i][1]) % 10
                if prod_mod == grid[i][2]:
                    if all(
                        len(row) >= 3 and (row[0] * row[1]) % 10 == row[2]
                        for row in grid
                    ):
                        patterns.append({
                            "type": "product_mod_10_pattern",
                            "formula": "(row[0] * row[1]) % 10 = row[2]",
                        })

        return {
            "success": len(patterns) > 0,
            "patterns": patterns,
            "grid_info": {
                "rows": rows,
                "cols": cols,
                "row_sums": row_sums,
                "column_sums": col_sums,
            },
        }

    def _match_string_pattern(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Match patterns in strings.

        Args:
            text: Text to analyze
            context: Additional context

        Returns:
            Result with detected patterns
        """
        patterns = []

        # Email pattern
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', text):
            patterns.append({"type": "email"})

        # Phone number
        if re.match(r'^[\d\s\(\)\-\+]+$', text) and len(text.replace(' ', '')) >= 10:
            patterns.append({"type": "phone_number"})

        # URL
        if re.match(r'^https?://', text):
            patterns.append({"type": "url"})

        # Repeating pattern
        for length in range(1, len(text) // 2 + 1):
            pattern = text[:length]
            if text == pattern * (len(text) // length) + text[:len(text) % length]:
                patterns.append({
                    "type": "repeating",
                    "pattern": pattern,
                    "repetitions": len(text) // length,
                })
                break

        return {
            "success": len(patterns) > 0,
            "patterns": patterns,
        }

    def predict_next_value(self, sequence: List[float]) -> Optional[float]:
        """Predict next value in sequence.

        Args:
            sequence: Numeric sequence

        Returns:
            Predicted next value or None
        """
        result = self._match_numeric_sequence(sequence, {})

        if result.get("best_pattern"):
            return result["best_pattern"].get("next_value")

        return None
