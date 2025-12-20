"""EXPLORE_ENV state - Learn through mathematical experimentation.

This state implements EXPLORE mode learning:
1. Parse question into mathematical claim
2. Create experiment test cases
3. Execute experiments
4. Create Evidence from experiment results
5. Store evidence with validation metadata

The evidence will be synthesized into theorems in the INTEGRATE_KNOWLEDGE state.
"""

from ..models import LearningContext, Evidence
from ..types import LearningState, EvidenceSource
from ..modes.explore import (
    process_explore_question,
    execute_simple_test,
)
from ..storage import store_evidence
from .base import BaseState


class ExploreEnvState(BaseState):
    """EXPLORE mode: Learn through experimentation."""

    async def execute(self, context: LearningContext) -> LearningState:
        """Gather evidence through experiments.

        Args:
            context: Learning context.

        Returns:
            Next state (INTEGRATE_KNOWLEDGE).
        """
        self._log("Starting EXPLORE mode experimentation")

        if context.focus_question is None:
            self._log("ERROR: No focus question")
            return LearningState.IDLE_OR_TERMINATE

        question = context.focus_question
        self._log(f"Exploring: {question.text}")

        # Step 1: Parse question into mathematical claim
        self._log("Parsing mathematical claim...")
        explore_data = process_explore_question(question)

        claim = explore_data["claim"]
        test_cases = explore_data["test_cases"]

        self._log(f"Property: {claim['property']}")
        self._log(f"Operation: {claim['operation']}")
        self._log(f"Hypothesis: {claim['hypothesis']}")
        self._log(f"Test cases: {len(test_cases)}")

        # Store claim in context metadata
        context.metadata["explore_claim"] = claim
        context.metadata["explore_hypothesis"] = claim["hypothesis"]

        # Step 2: Execute experiments
        experiment_results = []
        for i, test_case in enumerate(test_cases):
            self._log(f"Executing test case {i+1}/{len(test_cases)}...")

            # Execute the test
            result = execute_simple_test(test_case, claim["operation"])
            experiment_results.append(result)

            passed = result.get("passed", False)
            self._log(f"  Result: {'PASS' if passed else 'FAIL'}")

            # Create evidence for each experiment
            evidence_text = f"Test case {i+1}: {test_case.get('test', 'test')}\n"
            evidence_text += f"Data: {test_case}\n"
            evidence_text += f"Result: {'PASSED' if passed else 'FAILED'}"

            if not passed and result.get("error"):
                evidence_text += f"\nError: {result['error']}"

            evidence = Evidence.create(
                text=evidence_text,
                source=EvidenceSource.EXPERIMENT,
                citations=[f"experiment_{i+1}"],
            )
            evidence.validated = True
            evidence.validation_method = "experiment_execution"
            evidence.confidence = 1.0 if passed else 0.0
            evidence.metadata = {
                "test_case": test_case,
                "result": result,
                "experiment_index": i,
            }

            context.add_evidence(evidence)
            store_evidence(self.machine.memory, evidence)

        # Store experiment results in context
        context.metadata["experiment_results"] = experiment_results

        # Calculate overall pass rate
        total = len(experiment_results)
        passed = sum(1 for r in experiment_results if r.get("passed", False))
        pass_rate = passed / total if total > 0 else 0.0

        self._log(f"Experiments complete: {passed}/{total} passed ({pass_rate:.1%})")

        # Identify gaps if experiments failed
        if pass_rate < 1.0:
            failed_tests = [r for r in experiment_results if not r.get("passed", True)]
            for r in failed_tests:
                gap = f"Test case failed: {r.get('test_data', 'unknown')}"
                context.add_gap(gap)
                self._log(f"Gap identified: {gap}")

        # Transition to knowledge integration
        self._log_transition(LearningState.EXPLORE_ENV, LearningState.INTEGRATE_KNOWLEDGE)
        return LearningState.INTEGRATE_KNOWLEDGE
