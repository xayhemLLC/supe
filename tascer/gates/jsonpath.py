"""TASC_GATE_JSONPATH - JSON path assertions for structured output.

Parse JSON output or file, assert:
- JSONPath comparisons
- Schema validation (basic)

Note: Uses a simple JSONPath subset without external dependencies.
Supports: $.key, $.key.nested, $[0], $.array[*].field
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


def _get_by_path(data: Any, path: str) -> List[Any]:
    """Simple JSONPath-like accessor.
    
    Supports:
    - $.key - access dict key
    - $.key.nested - nested access
    - $[0] - array index
    - $.array[*] - all array elements
    - $.key[*].field - field from all array elements
    
    Returns list of matching values (for [*] support).
    """
    if not path.startswith("$"):
        path = "$." + path
    
    # Remove leading $
    path = path[1:]
    
    # Handle empty path
    if not path or path == ".":
        return [data]
    
    # Remove leading dot
    if path.startswith("."):
        path = path[1:]
    
    results = [data]
    
    # Parse path segments
    segments = re.split(r'\.(?![^\[]*\])', path)
    
    for segment in segments:
        if not segment:
            continue
        
        new_results = []
        
        # Check for array access
        array_match = re.match(r'(\w+)?\[(\*|\d+)\]', segment)
        
        if array_match:
            key = array_match.group(1)
            index = array_match.group(2)
            
            for item in results:
                # First access the key if present
                if key and isinstance(item, dict):
                    item = item.get(key)
                
                if item is None:
                    continue
                
                # Then handle array access
                if isinstance(item, list):
                    if index == "*":
                        new_results.extend(item)
                    else:
                        idx = int(index)
                        if 0 <= idx < len(item):
                            new_results.append(item[idx])
        else:
            # Simple key access
            for item in results:
                if isinstance(item, dict) and segment in item:
                    new_results.append(item[segment])
        
        results = new_results
    
    return results


@dataclass
class JsonPathAssertion:
    """A single JSONPath assertion."""
    
    path: str
    expected: Any = None
    operator: str = "eq"  # eq, ne, contains, gt, lt, gte, lte, exists, type
    
    def check(self, data: Any) -> tuple:
        """Check this assertion against data.
        
        Returns:
            (passed: bool, actual_value: Any)
        """
        values = _get_by_path(data, self.path)
        
        if not values:
            if self.operator == "exists":
                return (self.expected is False, None)
            return (False, None)
        
        # For single value comparisons, use first match
        actual = values[0] if len(values) == 1 else values
        
        if self.operator == "exists":
            return (self.expected is True, actual)
        elif self.operator == "eq":
            return (actual == self.expected, actual)
        elif self.operator == "ne":
            return (actual != self.expected, actual)
        elif self.operator == "contains":
            if isinstance(actual, str):
                return (self.expected in actual, actual)
            elif isinstance(actual, list):
                return (self.expected in actual, actual)
            return (False, actual)
        elif self.operator == "gt":
            try:
                return (actual > self.expected, actual)
            except TypeError:
                return (False, actual)
        elif self.operator == "lt":
            try:
                return (actual < self.expected, actual)
            except TypeError:
                return (False, actual)
        elif self.operator == "gte":
            try:
                return (actual >= self.expected, actual)
            except TypeError:
                return (False, actual)
        elif self.operator == "lte":
            try:
                return (actual <= self.expected, actual)
            except TypeError:
                return (False, actual)
        elif self.operator == "type":
            type_map = {
                "string": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "null": type(None),
            }
            expected_type = type_map.get(self.expected)
            return (isinstance(actual, expected_type) if expected_type else False, actual)
        
        return (False, actual)


@dataclass
class JsonPathGate:
    """Gate that validates JSON data against JSONPath assertions."""
    
    assertions: List[JsonPathAssertion] = field(default_factory=list)
    
    def check(
        self,
        data: Optional[Union[str, Dict, List]] = None,
        json_file: Optional[str] = None,
    ):
        """Check JSON data against all assertions.
        
        Args:
            data: JSON data (string to parse or already parsed).
            json_file: Path to JSON file to load.
        
        Returns:
            GateResult with pass/fail status.
        """
        from ..contracts import GateResult
        
        # Load data
        if json_file:
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                return GateResult(
                    gate_name="JSONPATH",
                    passed=False,
                    message=f"Failed to load JSON file: {e}",
                    evidence={"file": json_file, "error": str(e)},
                )
        elif isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                return GateResult(
                    gate_name="JSONPATH",
                    passed=False,
                    message=f"Failed to parse JSON: {e}",
                    evidence={"error": str(e)},
                )
        
        if data is None:
            return GateResult(
                gate_name="JSONPATH",
                passed=False,
                message="No JSON data provided",
                evidence={},
            )
        
        # Check all assertions
        passed_assertions = []
        failed_assertions = []
        
        for assertion in self.assertions:
            passed, actual = assertion.check(data)
            result = {
                "path": assertion.path,
                "operator": assertion.operator,
                "expected": assertion.expected,
                "actual": actual,
                "passed": passed,
            }
            if passed:
                passed_assertions.append(result)
            else:
                failed_assertions.append(result)
        
        all_passed = len(failed_assertions) == 0
        
        if all_passed:
            message = f"All {len(passed_assertions)} JSONPath assertions passed"
        else:
            message = f"{len(failed_assertions)} assertion(s) failed: " + ", ".join(
                f"{a['path']} {a['operator']} {a['expected']}" for a in failed_assertions[:3]
            )
        
        return GateResult(
            gate_name="JSONPATH",
            passed=all_passed,
            message=message,
            evidence={
                "passed_count": len(passed_assertions),
                "failed_count": len(failed_assertions),
                "failed_assertions": failed_assertions[:5],  # Limit detail
            },
        )
    
    @classmethod
    def from_dict(cls, assertions_dict: Dict[str, Any]) -> "JsonPathGate":
        """Create gate from simple dict of path -> expected value.
        
        Args:
            assertions_dict: Dict mapping JSONPath to expected value.
        
        Returns:
            JsonPathGate with eq assertions for each path.
        """
        assertions = [
            JsonPathAssertion(path=path, expected=value, operator="eq")
            for path, value in assertions_dict.items()
        ]
        return cls(assertions=assertions)
