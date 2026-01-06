"""Example: Self-testing tascs with automatic experiment generation.

This demonstrates Phase 5: Self-validating tascs that generate their own
experiments, execute them, and produce evidence automatically.

This is the most advanced validation capability, directly applying the
learning system's EXPLORE mode experimental methodology to task validation.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tasc.tasc import Tasc
from tasc.domains import TaskDomain
from tasc.self_validation import SelfValidatingTaskc, ValidationExperiment, ExperimentStatus
from tasc.validation import validate_tasc_with_evidence


# Custom executor for demonstration (simulates test execution)
async def mock_executor(experiment: ValidationExperiment) -> dict:
    """Mock experiment executor for demonstration."""
    import random

    await asyncio.sleep(0.1)  # Simulate execution time

    # Simulate different outcomes based on experiment ID
    if "reproduction" in experiment.id:
        # Bug reproduction should fail (bug is fixed)
        return {"success": True, "message": "Bug does not reproduce"}
    elif "regression" in experiment.id:
        # Regression test should pass
        return {"success": True, "message": "New test passes"}
    elif "no_breakage" in experiment.id:
        # Existing tests should pass
        return {"success": True, "message": "All 47 tests passed"}
    else:
        # Generic success
        return {"success": True, "message": "Test passed"}


async def main():
    """Example self-validating tasc workflow."""

    print("=" * 70)
    print("SELF-TESTING TASC EXAMPLE")
    print("=" * 70)
    print("\nThis demonstrates Phase 5: Tascs that validate themselves through")
    print("automatically generated experiments, similar to EXPLORE mode's")
    print("theorem proving methodology.\n")

    # 1. Create a debugging tasc
    tasc = Tasc(
        id="self-test-001",
        status="completed",
        title="Fix memory leak in WebSocket connection handler",
        additional_notes="Connections not properly closed, causing memory leak",
        testing_instructions="pytest tests/websocket/test_connection_lifecycle.py",
        desired_outcome="No memory leaks in connection lifecycle",
    )

    print(f"📋 Task: {tasc.title}")
    print(f"   Status: {tasc.status}")

    # 2. Create self-validating tasc
    self_validating = SelfValidatingTaskc(tasc, TaskDomain.DEBUGGING)

    # 3. Generate validation experiments
    print("\n" + "=" * 70)
    print("EXPERIMENT SYNTHESIS (Automated)")
    print("=" * 70)
    print("\nGenerating validation experiments based on debugging domain...")

    experiments = await self_validating.synthesize_validation_experiments()

    print(f"\n✓ Generated {len(experiments)} validation experiments:")
    for i, exp in enumerate(experiments, 1):
        print(f"\n{i}. {exp.hypothesis}")
        print(f"   ID: {exp.id}")
        print(f"   Expected: {exp.expected_outcome}")

    # 4. Execute experiments
    print("\n" + "=" * 70)
    print("EXPERIMENT EXECUTION (Automated)")
    print("=" * 70)
    print("\nExecuting experiments in parallel...\n")

    results = await self_validating.execute_validation_experiments(
        executor_func=mock_executor
    )

    for i, exp in enumerate(results, 1):
        status_symbol = "✓" if exp.status == ExperimentStatus.PASSED else "✗"
        print(f"{status_symbol} Experiment {i}: {exp.status.value}")
        print(f"  Hypothesis: {exp.hypothesis}")
        print(f"  Actual: {exp.actual_outcome}")
        print(f"  Time: {exp.execution_time:.3f}s\n")

    # 5. Generate evidence from experiments
    print("=" * 70)
    print("EVIDENCE GENERATION (Automated)")
    print("=" * 70)

    evidence_collection = self_validating.generate_evidence_collection()

    print(f"\n✓ Generated {len(evidence_collection.evidence_items)} evidence items")
    print(f"   Validated: {len(evidence_collection.get_validated_evidence())}")
    print(f"   Source diversity: {evidence_collection.get_source_diversity()}")

    print("\nEvidence Items:")
    for i, evidence in enumerate(evidence_collection.evidence_items, 1):
        validated_mark = "✓" if evidence.validated else "○"
        print(f"\n{i}. [{validated_mark}] {evidence.source.value}")
        print(f"   {evidence.text.split(chr(10))[0][:70]}...")

    # 6. Run unified validation with generated evidence
    print("\n" + "=" * 70)
    print("UNIFIED VALIDATION")
    print("=" * 70)

    # Need to add required evidence types for validation
    from tasc.domains import apply_domain_to_tasc
    apply_domain_to_tasc(tasc, TaskDomain.DEBUGGING)

    # Run validation
    result = await validate_tasc_with_evidence(
        tasc,
        evidence_collection,
        debug=False,
    )

    print(f"\n✓ Validation Complete")
    print(f"   Overall Confidence: {result.overall_confidence:.1%}")
    print(f"   Evidence Factor: {result.evidence_factor:.2f}")
    print(f"   Status: {result.validation_status}")

    # 7. Get validation summary
    print("\n" + "=" * 70)
    print("EXPERIMENT SUMMARY")
    print("=" * 70)

    summary = self_validating.get_validation_summary()

    print(f"\n📊 Validation Metrics:")
    print(f"   Total Experiments: {summary['total_experiments']}")
    print(f"   Experiments Run: {summary['experiments_run']}")
    print(f"   Passed: {summary['passed']}")
    print(f"   Failed: {summary['failed']}")
    print(f"   Errors: {summary['errors']}")
    print(f"   Success Rate: {summary['success_rate']:.1%}")

    # 8. Compare with manually collected evidence
    print("\n" + "=" * 70)
    print("COMPARISON: MANUAL VS SELF-TESTING")
    print("=" * 70)

    print("\n┌─ Manual Evidence Collection ─────────────────────────────────┐")
    print("│ • Developer manually documents hypothesis                     │")
    print("│ • Developer manually writes reproduction steps                │")
    print("│ • Developer manually analyzes root cause                      │")
    print("│ • Developer manually implements fix                           │")
    print("│ • Developer manually adds regression test                     │")
    print("│ • Time: ~30-60 minutes of manual work                         │")
    print("│ • Risk: Missing evidence, incomplete documentation            │")
    print("└───────────────────────────────────────────────────────────────┘")

    print("\n┌─ Self-Testing Validation ────────────────────────────────────┐")
    print("│ • Experiments automatically generated from domain knowledge   │")
    print("│ • Experiments executed in parallel                            │")
    print("│ • Evidence automatically created from experiment results      │")
    print("│ • Validation confidence automatically computed                │")
    print(f"│ • Time: ~{sum(e.execution_time for e in results):.2f} seconds (automated)                              │")
    print("│ • Benefit: Systematic, reproducible, no missing steps         │")
    print("└───────────────────────────────────────────────────────────────┘")

    # 9. Key takeaways
    print("\n" + "=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)

    print("\n1. Automated Experiment Generation")
    print("   Self-validating tascs generate experiments based on domain")
    print("   No manual evidence collection required")

    print("\n2. Domain-Specific Validation")
    print("   Debugging: Tests bug reproduction, regression tests, no breakage")
    print("   Feature: Tests requirements, coverage, no regressions")
    print("   Refactoring: Tests behavior preservation, quality improvement")

    print("\n3. Evidence from Experiments")
    print("   Experiment results automatically become evidence")
    print("   Validated experiments boost confidence significantly")
    print("   Failed experiments provide feedback for fixing")

    print("\n4. Parallel Execution")
    print("   All experiments run concurrently for speed")
    print("   Results aggregated into unified validation")

    print("\n5. Direct Application of EXPLORE Mode")
    print("   This uses the same experimental methodology as learning")
    print("   Tascs \"prove\" their completion through experiments")
    print("   Just like theorems are proven through experiments")

    print("\n" + "=" * 70)
    print("\n✨ This is the highest level of validation sophistication:")
    print("   Tasks that validate themselves through formal experimentation!")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
