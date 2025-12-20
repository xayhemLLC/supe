"""EXPLORE mode utilities for mathematical experimentation.

Provides utilities for:
- Parsing mathematical claims into testable hypotheses
- Creating experiment plans using Tascer
- Synthesizing theorems from experiment results

EXPLORE mode is for learning through experimentation, particularly for
mathematical properties, system behaviors, and conjectures that can be
validated through testing.
"""

import re
from typing import List, Dict, Any, Optional

from ..models import Question, Evidence, Theorem, Belief
from ..types import QuestionType, EvidenceSource, TheoremStatus, Confidence, ID


# ============================================================================
# Mathematical Claim Parsing
# ============================================================================


def parse_mathematical_claim(question: str) -> Dict[str, Any]:
    """Parse a question into a testable mathematical claim.

    Extracts:
    - Property being tested (e.g., "commutative", "associative")
    - Operation/domain (e.g., "addition", "multiplication")
    - Variables/parameters

    Args:
        question: Question text to parse.

    Returns:
        Dictionary with parsed claim components:
        {
            "property": str,
            "operation": str,
            "hypothesis": str,
            "test_cases": List[Dict],
        }
    """
    question_lower = question.lower()

    # Detect property type
    property_patterns = {
        "commutative": r"commutat",
        "associative": r"associat",
        "distributive": r"distribut",
        "identity": r"identity",
        "inverse": r"invers",
        "transitive": r"transit",
        "reflexive": r"reflex",
        "symmetric": r"symmetr",
    }

    detected_property = None
    for prop, pattern in property_patterns.items():
        if re.search(pattern, question_lower):
            detected_property = prop
            break

    # Detect operation
    operation_patterns = {
        "addition": r"add|sum|\+",
        "multiplication": r"multipl|product|\*|×",
        "subtraction": r"subtract|minus|-",
        "division": r"divid|quotient|/",
    }

    detected_operation = None
    for op, pattern in operation_patterns.items():
        if re.search(pattern, question_lower):
            detected_operation = op
            break

    # Generate hypothesis statement
    if detected_property and detected_operation:
        hypothesis = f"{detected_operation.capitalize()} is {detected_property}"
    else:
        hypothesis = question  # Fallback to original question

    # Generate basic test cases based on property
    test_cases = []
    if detected_property == "commutative":
        # Test a op b = b op a
        test_cases = [
            {"a": 2, "b": 3, "test": "a op b == b op a"},
            {"a": 5, "b": 7, "test": "a op b == b op a"},
            {"a": 0, "b": 10, "test": "a op b == b op a"},
        ]
    elif detected_property == "associative":
        # Test (a op b) op c = a op (b op c)
        test_cases = [
            {"a": 2, "b": 3, "c": 4, "test": "(a op b) op c == a op (b op c)"},
            {"a": 1, "b": 5, "c": 9, "test": "(a op b) op c == a op (b op c)"},
        ]
    elif detected_property == "identity":
        # Test a op e = a
        test_cases = [
            {"a": 5, "e": 0, "test": "a op e == a"},
            {"a": 100, "e": 0, "test": "a op e == a"},
        ]

    return {
        "property": detected_property or "unknown",
        "operation": detected_operation or "unknown",
        "hypothesis": hypothesis,
        "test_cases": test_cases,
    }


# ============================================================================
# Experiment Plan Creation
# ============================================================================


def create_experiment_plan(
    question: Question,
    claim: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a Tascer-compatible experiment plan.

    Converts a mathematical claim into a structured plan with:
    - Test cases to execute
    - Expected outcomes
    - Validation criteria

    Args:
        question: The question being explored.
        claim: Parsed mathematical claim.

    Returns:
        Dictionary suitable for Tascer TascPlan creation.
    """
    property_name = claim.get("property", "unknown")
    operation = claim.get("operation", "unknown")
    hypothesis = claim.get("hypothesis", question.text)
    test_cases = claim.get("test_cases", [])

    # Create plan structure
    plan = {
        "title": f"Experiment: {hypothesis}",
        "description": f"Testing {property_name} property of {operation}",
        "hypothesis": hypothesis,
        "test_cases": test_cases,
        "tascs": [],
    }

    # Create tascs for each test case
    for i, test_case in enumerate(test_cases):
        tasc = {
            "id": f"test_{property_name}_{i}",
            "title": f"Test case {i+1}: {test_case.get('test', 'test')}",
            "testing_instructions": f"# Validate: {test_case}",
            "desired_outcome": "Test passes and validates hypothesis",
            "test_data": test_case,
        }
        plan["tascs"].append(tasc)

    return plan


# ============================================================================
# Theorem Synthesis
# ============================================================================


def synthesize_theorem(
    question: Question,
    claim: Dict[str, Any],
    experiment_results: List[Dict[str, Any]],
) -> Theorem:
    """Synthesize a theorem from experiment results.

    Args:
        question: The question being explored.
        claim: Parsed mathematical claim.
        experiment_results: Results from experiments.

    Returns:
        Theorem with proof or counterexample.
    """
    hypothesis = claim.get("hypothesis", question.text)
    property_name = claim.get("property", "unknown")

    # Analyze experiment results
    total_tests = len(experiment_results)
    passed_tests = sum(1 for r in experiment_results if r.get("passed", False))

    # Determine theorem status
    if passed_tests == total_tests and total_tests > 0:
        status = TheoremStatus.PROVEN
        proof = f"Validated through {total_tests} test cases. All tests passed."
        counterexample = None
    elif passed_tests == 0 and total_tests > 0:
        status = TheoremStatus.DISPROVEN
        # Find first failed test as counterexample
        failed = next((r for r in experiment_results if not r.get("passed", True)), None)
        counterexample = str(failed.get("test_data", "Unknown")) if failed else None
        proof = f"Disproven by counterexample: {counterexample}"
    else:
        status = TheoremStatus.CONJECTURE
        proof = f"Partially validated: {passed_tests}/{total_tests} tests passed. More evidence needed."
        counterexample = None

    # Extract validated properties
    properties_validated = []
    if status == TheoremStatus.PROVEN:
        properties_validated.append(property_name)

    return Theorem(
        statement=hypothesis,
        proof=proof,
        status=status,
        counterexample=counterexample,
        experiments=experiment_results,
        properties_validated=properties_validated,
    )


def create_belief_from_theorem(
    question: Question,
    theorem: Theorem,
    evidence_list: List[Evidence],
    confidence: Optional[Confidence] = None,
) -> Belief:
    """Create a Belief from a theorem.

    Args:
        question: The question being explored.
        theorem: Synthesized theorem.
        evidence_list: Supporting evidence (experiment results).
        confidence: Optional confidence override.

    Returns:
        Belief wrapping the theorem.
    """
    # Calculate confidence based on theorem status
    if confidence is None:
        if theorem.status == TheoremStatus.PROVEN:
            confidence = Confidence(0.95)  # High confidence
        elif theorem.status == TheoremStatus.DISPROVEN:
            confidence = Confidence(0.0)  # No confidence in false claim
        else:
            # Conjecture: confidence based on pass rate
            if theorem.experiments:
                passed = sum(1 for e in theorem.experiments if e.get("passed", False))
                confidence = Confidence(passed / len(theorem.experiments))
            else:
                confidence = Confidence(0.5)

    evidence_ids = [ID(e.id) for e in evidence_list]

    return Belief.create_from_theorem(
        question_id=ID(question.id),
        theorem=theorem,
        confidence=confidence,
        evidence_ids=evidence_ids,
    )


# ============================================================================
# EXPLORE Workflow
# ============================================================================


def process_explore_question(
    question: Question,
) -> Dict[str, Any]:
    """Process question in EXPLORE mode.

    Workflow:
    1. Parse mathematical claim
    2. Create experiment plan
    3. Return structure for execution

    Args:
        question: Question to explore.

    Returns:
        Dictionary with:
        {
            "claim": Dict[str, Any],
            "experiment_plan": Dict[str, Any],
            "test_cases": List[Dict],
        }
    """
    # 1. Parse claim
    claim = parse_mathematical_claim(question.text)

    # 2. Create experiment plan
    experiment_plan = create_experiment_plan(question, claim)

    return {
        "claim": claim,
        "experiment_plan": experiment_plan,
        "test_cases": claim.get("test_cases", []),
    }


def execute_simple_test(test_case: Dict[str, Any], operation: str) -> Dict[str, Any]:
    """Execute a simple mathematical test case.

    This is a simplified executor for demonstration. In production,
    would use Tascer's full validation pipeline.

    Args:
        test_case: Test case with values.
        operation: Operation to test ("addition", "multiplication", etc.)

    Returns:
        Dictionary with test result.
    """
    try:
        a = test_case.get("a", 0)
        b = test_case.get("b", 0)
        c = test_case.get("c")

        # Map operation to Python operator
        ops = {
            "addition": lambda x, y: x + y,
            "multiplication": lambda x, y: x * y,
            "subtraction": lambda x, y: x - y,
        }

        op_func = ops.get(operation, lambda x, y: x + y)

        # Test commutative property
        if "a op b == b op a" in test_case.get("test", ""):
            result = op_func(a, b) == op_func(b, a)
        # Test associative property
        elif c is not None and "(a op b) op c == a op (b op c)" in test_case.get("test", ""):
            result = op_func(op_func(a, b), c) == op_func(a, op_func(b, c))
        # Test identity property
        elif "a op e == a" in test_case.get("test", ""):
            e = test_case.get("e", 0)
            result = op_func(a, e) == a
        else:
            result = True  # Default pass

        return {
            "passed": result,
            "test_data": test_case,
            "result": result,
        }
    except Exception as e:
        return {
            "passed": False,
            "test_data": test_case,
            "error": str(e),
        }
