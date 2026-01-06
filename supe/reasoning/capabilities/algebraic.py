"""Algebraic manipulation capabilities."""

import re
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class AlgebraicExpression:
    """Represents an algebraic expression."""
    terms: List[Tuple[int, int]]  # (coefficient, power)
    constant: int = 0

    def __str__(self) -> str:
        """String representation."""
        parts = []
        for coef, power in sorted(self.terms, key=lambda x: -x[1]):
            if power == 0:
                parts.append(str(coef))
            elif power == 1:
                if coef == 1:
                    parts.append("x")
                elif coef == -1:
                    parts.append("-x")
                else:
                    parts.append(f"{coef}x")
            else:
                if coef == 1:
                    parts.append(f"x^{power}")
                elif coef == -1:
                    parts.append(f"-x^{power}")
                else:
                    parts.append(f"{coef}x^{power}")

        if self.constant != 0:
            parts.append(str(self.constant))

        return " + ".join(parts).replace("+ -", "- ")


class AlgebraicManipulation:
    """Performs algebraic manipulation and equation solving."""

    def execute(self, problem_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute algebraic manipulation.

        Args:
            problem_text: The problem statement
            context: Context including parsed expressions

        Returns:
            Result dictionary
        """
        # Determine what type of algebraic operation
        if "factor" in problem_text.lower():
            return self._factor_polynomial(problem_text, context)
        elif "solve" in problem_text.lower():
            return self._solve_equation(problem_text, context)
        elif "simplify" in problem_text.lower():
            return self._simplify_expression(problem_text, context)
        else:
            return {"success": False, "error": "Unknown algebraic operation"}

    def _factor_polynomial(self, problem_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Factor a polynomial expression.

        Handles quadratic factorization: x² + bx + c = (x + m)(x + n)
        where m + n = b and m * n = c
        """
        # Extract polynomial from text
        poly = self._parse_quadratic(problem_text)
        if not poly:
            return {"success": False, "error": "Could not parse quadratic"}

        a, b, c = poly

        # For now, handle only monic quadratics (a=1)
        if a != 1:
            return {
                "success": False,
                "error": f"Non-monic quadratic (a={a}), not yet implemented",
                "partial": True
            }

        # Find two numbers that sum to b and multiply to c
        factors = self._find_factor_pair(c, b)
        if not factors:
            return {
                "success": False,
                "error": "Not factorable over integers",
                "tried": f"Need m*n={c} and m+n={b}"
            }

        m, n = factors
        factored = f"(x {'+' if m >= 0 else ''}{m})(x {'+' if n >= 0 else ''}{n})"

        return {
            "success": True,
            "factorization": factored,
            "factors": [m, n],
            "verification": f"({m}) + ({n}) = {m+n} = {b}, ({m}) * ({n}) = {m*n} = {c}",
        }

    def _parse_quadratic(self, text: str) -> Optional[Tuple[int, int, int]]:
        """Parse quadratic expression ax² + bx + c.

        Returns:
            Tuple (a, b, c) or None if not parsable
        """
        # Normalize text
        text = text.lower().replace("²", "^2").replace(" ", "")

        # Pattern for x^2 + bx + c or x² + bx + c
        # Handle: x^2+5x+6, x²+5x+6, x^2 + 5x + 6

        # Extract coefficient of x^2
        a_match = re.search(r'([+-]?\d*)x\^2', text)
        if not a_match:
            return None

        a_str = a_match.group(1)
        if a_str in ['', '+']:
            a = 1
        elif a_str == '-':
            a = -1
        else:
            a = int(a_str)

        # Extract coefficient of x
        b_match = re.search(r'([+-]?\d+)x(?!\^)', text)
        if not b_match:
            b = 0
        else:
            b = int(b_match.group(1))

        # Extract constant term
        # Look for number not followed by x
        c_match = re.search(r'([+-]?\d+)(?!x)', text)
        if not c_match or 'x^2' in c_match.group(0) or 'x' in c_match.group(0):
            c = 0
        else:
            # Find all numbers, take the last one (constant term)
            numbers = re.findall(r'[+-]?\d+', text)
            if numbers:
                # Get last number that isn't part of x^2 or x term
                for num in reversed(numbers):
                    if text.index(num) > max(text.rfind('x^2'), text.rfind('x')):
                        c = int(num)
                        break
                else:
                    c = 0
            else:
                c = 0

        return (a, b, c)

    def _find_factor_pair(self, product: int, sum_value: int) -> Optional[Tuple[int, int]]:
        """Find two integers that multiply to product and add to sum_value.

        Args:
            product: Target product
            sum_value: Target sum

        Returns:
            Tuple (m, n) or None if not found
        """
        # Try all divisors of product
        if product == 0:
            return (0, sum_value)

        abs_product = abs(product)

        for m in range(-abs_product, abs_product + 1):
            if m == 0:
                continue
            if abs_product % abs(m) == 0:
                n = product // m
                if m + n == sum_value:
                    return (m, n)

        return None

    def _solve_equation(self, problem_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Solve an algebraic equation."""
        # Simple linear equation solver: ax + b = c
        # Extract equation
        if '=' in problem_text:
            left, right = problem_text.split('=')

            # For now, simple cases
            return {
                "success": False,
                "error": "General equation solving not yet implemented",
                "partial": True
            }

        return {"success": False, "error": "No equation found"}

    def _simplify_expression(self, problem_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify an algebraic expression."""
        return {
            "success": False,
            "error": "Expression simplification not yet implemented",
            "partial": True
        }
