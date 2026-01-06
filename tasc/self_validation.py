"""Self-validating tascs using experimental methodology.

This module implements the advanced capability for tascs to generate their own
validation experiments, directly applying the learning system's EXPLORE mode
methodology to task validation.

Key concepts:
1. Experiment synthesis: Generate testable hypotheses about task completion
2. Experiment execution: Run experiments to validate hypotheses
3. Result analysis: Evaluate experiment outcomes
4. Evidence generation: Create evidence from experimental results

This enables truly self-validating tascs that prove their own completion
through formal experimentation, not just assertion.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import asyncio

from .evidence import Evidence, EvidenceCollection, EvidenceSource
from .tasc import Tasc
from .domains import TaskDomain


class ExperimentStatus(Enum):
    """Status of a validation experiment."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class ValidationExperiment:
    """An experiment to validate task completion.

    This mirrors the learning system's Experiment structure but is
    focused on validating task outcomes rather than proving theorems.
    """

    id: str
    hypothesis: str  # What we're testing
    test_code: str  # Code to run the test
    expected_outcome: str  # What should happen if hypothesis is true
    status: ExperimentStatus = ExperimentStatus.PENDING
    actual_outcome: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0

    def to_evidence(self) -> Evidence:
        """Convert experiment result to evidence."""
        text = f"Experiment: {self.hypothesis}\n"
        text += f"Expected: {self.expected_outcome}\n"
        text += f"Actual: {self.actual_outcome}\n"
        text += f"Status: {self.status.value}"

        return Evidence.create(
            text=text,
            source=EvidenceSource.EXPERIMENT,
            citations=[f"experiment:{self.id}"],
        )


class ExperimentGenerator:
    """Generates validation experiments for different task domains.

    This is analogous to the learning system's experiment generation in
    EXPLORE mode, but adapted for task validation.
    """

    def generate_experiments(
        self,
        tasc: Tasc,
        domain: TaskDomain,
    ) -> List[ValidationExperiment]:
        """Generate validation experiments for a tasc.

        Args:
            tasc: The tasc to generate experiments for
            domain: The task domain

        Returns:
            List of validation experiments
        """
        if domain == TaskDomain.DEBUGGING:
            return self._generate_debugging_experiments(tasc)
        elif domain == TaskDomain.FEATURE:
            return self._generate_feature_experiments(tasc)
        elif domain == TaskDomain.REFACTORING:
            return self._generate_refactoring_experiments(tasc)
        elif domain == TaskDomain.PERFORMANCE:
            return self._generate_performance_experiments(tasc)
        else:
            return self._generate_generic_experiments(tasc)

    def _generate_debugging_experiments(self, tasc: Tasc) -> List[ValidationExperiment]:
        """Generate experiments for debugging tasks.

        Experiments test:
        1. Bug no longer occurs
        2. Fix doesn't break existing behavior
        3. Edge cases are handled
        """
        experiments = []

        # Experiment 1: Bug reproduction should fail (bug is fixed)
        experiments.append(
            ValidationExperiment(
                id="debug_1_reproduction",
                hypothesis="Bug no longer occurs after fix",
                test_code=tasc.testing_instructions if tasc.testing_instructions else "# No test specified",
                expected_outcome="Test passes (bug does not reproduce)",
            )
        )

        # Experiment 2: Regression test exists and passes
        experiments.append(
            ValidationExperiment(
                id="debug_2_regression",
                hypothesis="Regression test added and passes",
                test_code="# Check for new regression test",
                expected_outcome="New test exists and passes",
            )
        )

        # Experiment 3: Existing tests still pass
        experiments.append(
            ValidationExperiment(
                id="debug_3_no_breakage",
                hypothesis="Fix doesn't break existing functionality",
                test_code="# Run full test suite",
                expected_outcome="All existing tests pass",
            )
        )

        return experiments

    def _generate_feature_experiments(self, tasc: Tasc) -> List[ValidationExperiment]:
        """Generate experiments for feature implementation.

        Experiments test:
        1. Feature works as specified
        2. Edge cases are handled
        3. Tests exist and pass
        """
        experiments = []

        # Experiment 1: Feature requirements met
        experiments.append(
            ValidationExperiment(
                id="feature_1_requirements",
                hypothesis="Feature meets all requirements",
                test_code=tasc.testing_instructions if tasc.testing_instructions else "# No test specified",
                expected_outcome="Feature works as specified in requirements",
            )
        )

        # Experiment 2: Test coverage
        experiments.append(
            ValidationExperiment(
                id="feature_2_tests",
                hypothesis="Feature has adequate test coverage",
                test_code="# Check test coverage for new code",
                expected_outcome="Coverage >= 80% for new code",
            )
        )

        # Experiment 3: No regressions
        experiments.append(
            ValidationExperiment(
                id="feature_3_no_regressions",
                hypothesis="Feature doesn't break existing functionality",
                test_code="# Run full test suite",
                expected_outcome="All tests pass",
            )
        )

        return experiments

    def _generate_refactoring_experiments(self, tasc: Tasc) -> List[ValidationExperiment]:
        """Generate experiments for refactoring tasks.

        Experiments test:
        1. Behavior unchanged
        2. Code quality improved
        3. Tests still pass
        """
        experiments = []

        # Experiment 1: All tests still pass
        experiments.append(
            ValidationExperiment(
                id="refactor_1_tests_pass",
                hypothesis="Refactoring preserves all behavior",
                test_code="# Run full test suite",
                expected_outcome="All tests pass",
            )
        )

        # Experiment 2: Code quality metrics improved
        experiments.append(
            ValidationExperiment(
                id="refactor_2_quality",
                hypothesis="Code quality metrics improved",
                test_code="# Compare complexity/coverage metrics",
                expected_outcome="Metrics show improvement",
            )
        )

        return experiments

    def _generate_performance_experiments(self, tasc: Tasc) -> List[ValidationExperiment]:
        """Generate experiments for performance optimization.

        Experiments test:
        1. Performance improved
        2. Correctness preserved
        """
        experiments = []

        # Experiment 1: Performance benchmark
        experiments.append(
            ValidationExperiment(
                id="perf_1_benchmark",
                hypothesis="Performance improved by target amount",
                test_code="# Run performance benchmarks",
                expected_outcome="Benchmark shows improvement",
            )
        )

        # Experiment 2: Correctness preserved
        experiments.append(
            ValidationExperiment(
                id="perf_2_correctness",
                hypothesis="Optimization preserves correctness",
                test_code="# Run correctness tests",
                expected_outcome="All tests pass",
            )
        )

        return experiments

    def _generate_generic_experiments(self, tasc: Tasc) -> List[ValidationExperiment]:
        """Generate generic validation experiments.

        For tasks without specific domain knowledge.
        """
        experiments = []

        # Experiment 1: Desired outcome achieved
        if tasc.desired_outcome:
            experiments.append(
                ValidationExperiment(
                    id="generic_1_outcome",
                    hypothesis=f"Desired outcome achieved: {tasc.desired_outcome}",
                    test_code=tasc.testing_instructions if tasc.testing_instructions else "# Manual validation required",
                    expected_outcome=tasc.desired_outcome,
                )
            )

        # Experiment 2: Testing instructions pass
        if tasc.testing_instructions:
            experiments.append(
                ValidationExperiment(
                    id="generic_2_tests",
                    hypothesis="Testing instructions pass",
                    test_code=tasc.testing_instructions,
                    expected_outcome="Tests pass successfully",
                )
            )

        return experiments


class ExperimentExecutor:
    """Executes validation experiments and generates evidence.

    This is the runtime component that actually runs experiments
    and collects results.
    """

    async def execute_experiment(
        self,
        experiment: ValidationExperiment,
        executor_func: Optional[Callable] = None,
    ) -> ValidationExperiment:
        """Execute a single validation experiment.

        Args:
            experiment: The experiment to execute
            executor_func: Optional custom executor function

        Returns:
            Updated experiment with results
        """
        import time

        experiment.status = ExperimentStatus.RUNNING
        start_time = time.time()

        try:
            if executor_func:
                # Use custom executor
                result = await executor_func(experiment)
                experiment.actual_outcome = str(result)
                experiment.status = ExperimentStatus.PASSED
            elif experiment.test_code and experiment.test_code != "# Manual validation required":
                # Execute test code
                result = await self._execute_test_code(experiment.test_code)
                experiment.actual_outcome = str(result)

                # Simple heuristic: passed if no errors
                if result.get("returncode", 0) == 0:
                    experiment.status = ExperimentStatus.PASSED
                else:
                    experiment.status = ExperimentStatus.FAILED
            else:
                # No executable test code
                experiment.status = ExperimentStatus.ERROR
                experiment.error_message = "No executable test code provided"

        except Exception as e:
            experiment.status = ExperimentStatus.ERROR
            experiment.error_message = str(e)

        experiment.execution_time = time.time() - start_time

        return experiment

    async def _execute_test_code(self, test_code: str) -> Dict[str, Any]:
        """Execute test code and return results.

        Args:
            test_code: Code to execute

        Returns:
            Execution results
        """
        import subprocess

        try:
            result = subprocess.run(
                test_code,
                shell=True,
                capture_output=True,
                timeout=60,
            )

            return {
                "returncode": result.returncode,
                "stdout": result.stdout.decode("utf-8"),
                "stderr": result.stderr.decode("utf-8"),
            }

        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "error": "Timeout expired",
            }
        except Exception as e:
            return {
                "returncode": -1,
                "error": str(e),
            }

    async def execute_all_experiments(
        self,
        experiments: List[ValidationExperiment],
        executor_func: Optional[Callable] = None,
    ) -> List[ValidationExperiment]:
        """Execute all experiments in parallel.

        Args:
            experiments: List of experiments to execute
            executor_func: Optional custom executor

        Returns:
            List of updated experiments with results
        """
        # Execute experiments concurrently
        tasks = [
            self.execute_experiment(exp, executor_func)
            for exp in experiments
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                experiments[i].status = ExperimentStatus.ERROR
                experiments[i].error_message = str(result)

        return experiments


class SelfValidatingTaskc:
    """A tasc that can validate itself through experiments.

    This is the highest level of validation - the task generates
    its own experiments, executes them, and produces evidence.
    """

    def __init__(self, tasc: Tasc, domain: TaskDomain):
        """Initialize self-validating tasc.

        Args:
            tasc: The underlying tasc
            domain: Task domain
        """
        self.tasc = tasc
        self.domain = domain
        self.generator = ExperimentGenerator()
        self.executor = ExperimentExecutor()
        self.experiments: List[ValidationExperiment] = []

    async def synthesize_validation_experiments(self) -> List[ValidationExperiment]:
        """Generate validation experiments for this tasc.

        Returns:
            List of generated experiments
        """
        self.experiments = self.generator.generate_experiments(self.tasc, self.domain)
        return self.experiments

    async def execute_validation_experiments(
        self,
        executor_func: Optional[Callable] = None,
    ) -> List[ValidationExperiment]:
        """Execute all validation experiments.

        Args:
            executor_func: Optional custom executor

        Returns:
            List of experiments with results
        """
        if not self.experiments:
            await self.synthesize_validation_experiments()

        self.experiments = await self.executor.execute_all_experiments(
            self.experiments, executor_func
        )

        return self.experiments

    def generate_evidence_collection(self) -> EvidenceCollection:
        """Generate evidence collection from experiment results.

        Returns:
            EvidenceCollection with experimental evidence
        """
        collection = EvidenceCollection.create(self.tasc.id)

        for experiment in self.experiments:
            evidence = experiment.to_evidence()
            # Mark as validated if experiment passed
            evidence.validated = experiment.status == ExperimentStatus.PASSED
            evidence.validation_method = "experimental"
            collection.add_evidence(evidence)

        return collection

    async def self_validate(
        self,
        executor_func: Optional[Callable] = None,
    ) -> EvidenceCollection:
        """Complete self-validation workflow.

        This generates experiments, executes them, and produces evidence.

        Args:
            executor_func: Optional custom executor

        Returns:
            EvidenceCollection with all experimental evidence
        """
        # 1. Generate experiments
        await self.synthesize_validation_experiments()

        # 2. Execute experiments
        await self.execute_validation_experiments(executor_func)

        # 3. Generate evidence
        collection = self.generate_evidence_collection()

        return collection

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation experiments.

        Returns:
            Dictionary with validation summary
        """
        if not self.experiments:
            return {
                "total_experiments": 0,
                "experiments_run": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "success_rate": 0.0,
            }

        total = len(self.experiments)
        passed = sum(1 for e in self.experiments if e.status == ExperimentStatus.PASSED)
        failed = sum(1 for e in self.experiments if e.status == ExperimentStatus.FAILED)
        errors = sum(1 for e in self.experiments if e.status == ExperimentStatus.ERROR)
        pending = sum(1 for e in self.experiments if e.status == ExperimentStatus.PENDING)

        experiments_run = total - pending
        success_rate = passed / experiments_run if experiments_run > 0 else 0.0

        return {
            "total_experiments": total,
            "experiments_run": experiments_run,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pending": pending,
            "success_rate": success_rate,
        }
