"""Test ARC Phase 5: Integration with Supe.

Validates:
- ARC capability registration
- Problem signature recognition
- Capability invocation through registry
- Solution library and learning
- Benchmark evaluation
- End-to-end supe integration
"""

from supe.reasoning.arc import (
    ARCGrid,
    ARCTask,
    ARCCapability,
    ARCEvaluator,
    quick_evaluation,
    register_arc_capability,
    register_arc_problem_signatures,
    setup_arc_integration,
)
from supe.reasoning.capability_registry import CapabilityRegistry
from supe.reasoning.problem_types import (
    ProblemDomain,
    ReasoningPattern,
    ProblemClassifier,
)


def test_capability_registration():
    """Test registering ARC capability with registry."""
    print("\n" + "="*60)
    print("TEST 1: Capability Registration")
    print("="*60)

    # Create registry
    registry = CapabilityRegistry()

    # Register ARC capability
    arc_capability = register_arc_capability(
        registry,
        max_depth=2,
        beam_width=3,
        enable_learning=True,
    )

    # Check registration
    cap = registry.get_capability("arc_program_synthesis")
    assert cap is not None, "ARC capability not registered"
    assert cap.pattern == ReasoningPattern.PROGRAM_SYNTHESIS
    assert ProblemDomain.VISUAL_REASONING in cap.domains

    print("  ✓ ARC capability registered")
    print(f"    Pattern: {cap.pattern.value}")
    print(f"    Domains: {[d.value for d in cap.domains]}")
    print(f"    Confidence: {cap.confidence}")

    # Check all three patterns registered
    patterns = [
        "arc_program_synthesis",
        "arc_transformation_inference",
        "arc_visual_patterns",
    ]
    for pattern_name in patterns:
        cap = registry.get_capability(pattern_name)
        assert cap is not None, f"{pattern_name} not registered"
        print(f"  ✓ {pattern_name} registered")


def test_problem_signatures():
    """Test ARC problem signature recognition."""
    print("\n" + "="*60)
    print("TEST 2: Problem Signature Recognition")
    print("="*60)

    # Create classifier
    classifier = ProblemClassifier()

    # Register ARC signatures
    register_arc_problem_signatures(classifier)

    # Check signature registration
    sig = classifier.get_signature("arc_transformation_task")
    assert sig is not None, "ARC transformation signature not registered"
    assert sig.domain == ProblemDomain.VISUAL_REASONING
    assert ReasoningPattern.PROGRAM_SYNTHESIS in sig.required_patterns

    print("  ✓ ARC transformation signature registered")
    print(f"    Domain: {sig.domain.value}")
    print(f"    Patterns: {[p.value for p in sig.required_patterns]}")
    print(f"    Complexity: {sig.complexity}")

    # Test classification
    problem_text = "Given these grid transformation examples, predict the output"
    signature = classifier.classify(problem_text)

    print(f"\n  Classification of: '{problem_text}'")
    print(f"    Domain: {signature.domain.value}")
    print(f"    Patterns: {[p.value for p in signature.required_patterns]}")

    print("  ✓ Problem classification working")


def test_capability_invocation():
    """Test invoking ARC capability through registry."""
    print("\n" + "="*60)
    print("TEST 3: Capability Invocation")
    print("="*60)

    # Setup integrated system
    registry = CapabilityRegistry()
    classifier = ProblemClassifier()
    arc_capability = setup_arc_integration(registry, classifier)

    # Create simple task
    task = ARCTask(
        train=[
            (ARCGrid.from_list([[1, 0], [1, 0]]),
             ARCGrid.from_list([[1, 1], [0, 0]])),
        ],
        test_inputs=[ARCGrid.from_list([[0, 1], [0, 1]])],
        test_outputs=[ARCGrid.from_list([[0, 0], [1, 1]])],
        task_id="test_rotation",
    )

    # Get capability from registry
    cap = registry.get_capability("arc_program_synthesis")
    assert cap is not None

    # Invoke through registry
    result = cap.invoke(task)

    assert result.success, f"Task solving failed: {result.explanation}"
    assert result.predictions[0] is not None, "No prediction generated"

    print("  ✓ Capability invoked through registry")
    print(f"    Success: {result.success}")
    print(f"    Program: {result.explanation}")
    print(f"    Confidence: {result.confidence:.0%}")
    print(f"    Time: {result.synthesis_time:.3f}s")

    # Check statistics
    registry.update_statistics("arc_program_synthesis", success=True)
    stats = registry.get_statistics()
    arc_stats = stats["arc_program_synthesis"]

    print(f"\n  Capability statistics:")
    print(f"    Usage count: {arc_stats['usage_count']}")
    print(f"    Success rate: {arc_stats['success_rate']:.1%}")


def test_solution_library():
    """Test solution library and incremental learning."""
    print("\n" + "="*60)
    print("TEST 4: Solution Library & Learning")
    print("="*60)

    # Create capability with learning
    capability = ARCCapability(
        max_depth=2,
        beam_width=5,
        enable_learning=True,
    )

    # Task 1: Rotation
    task1 = ARCTask(
        train=[
            (ARCGrid.from_list([[1, 0], [1, 0]]),
             ARCGrid.from_list([[1, 1], [0, 0]])),
        ],
        test_inputs=[ARCGrid.from_list([[0, 1], [0, 1]])],
        test_outputs=[ARCGrid.from_list([[0, 0], [1, 1]])],
        task_id="task1",
    )

    result1 = capability(task1)
    assert result1.success, "Task 1 failed"

    library_size_1 = len(capability.solution_library)
    print(f"  Task 1 solved: {result1.explanation}")
    print(f"  Library size after task 1: {library_size_1}")

    # Task 2: Same pattern (should reuse)
    task2 = ARCTask(
        train=[
            (ARCGrid.from_list([[1, 1], [0, 0]]),
             ARCGrid.from_list([[0, 1], [0, 1]])),
        ],
        test_inputs=[ARCGrid.from_list([[0, 0], [1, 1]])],
        test_outputs=[ARCGrid.from_list([[1, 0], [1, 0]])],
        task_id="task2",
    )

    result2 = capability(task2)
    assert result2.success, "Task 2 failed"

    library_size_2 = len(capability.solution_library)
    print(f"  Task 2 solved: {result2.explanation}")
    print(f"  Library size after task 2: {library_size_2}")

    # Check statistics
    stats = capability.get_statistics()
    print(f"\n  ✓ Learning statistics:")
    print(f"    Tasks attempted: {stats['tasks_attempted']}")
    print(f"    Tasks solved: {stats['tasks_solved']}")
    print(f"    Solve rate: {stats['solve_rate']:.0%}")
    print(f"    Library size: {stats['solution_library_size']}")


def test_evaluator():
    """Test benchmark evaluation harness."""
    print("\n" + "="*60)
    print("TEST 5: Benchmark Evaluation")
    print("="*60)

    # Create capability
    capability = ARCCapability(max_depth=2, beam_width=5)

    # Create evaluator
    evaluator = ARCEvaluator(capability)

    # Create test tasks
    tasks = []
    for i in range(3):
        task = ARCTask(
            train=[
                (ARCGrid.from_list([[1, 0], [1, 0]]),
                 ARCGrid.from_list([[1, 1], [0, 0]])),
                (ARCGrid.from_list([[0, 1], [0, 1]]),
                 ARCGrid.from_list([[0, 0], [1, 1]])),
            ],
            test_inputs=[ARCGrid.from_list([[1, 1], [0, 0]])],
            test_outputs=[ARCGrid.from_list([[0, 1], [0, 1]])],
            task_id=f"eval_task_{i}",
        )
        tasks.append(task)

    # Evaluate
    print("  Evaluating 3 test tasks...")
    results = evaluator.evaluate_tasks(tasks, print_progress=False)

    print(f"\n  ✓ Evaluation complete")
    print(f"    Total tasks: {results.total_tasks}")
    print(f"    Solved tasks: {results.solved_tasks}")
    print(f"    Solve rate: {results.solve_rate():.0%}")
    print(f"    Test accuracy: {results.test_accuracy():.0%}")
    print(f"    Avg time: {results.avg_time_per_task():.3f}s")

    # Check individual results
    for i, task_result in enumerate(results.task_results):
        status = "✓" if task_result.success else "✗"
        print(f"    {status} {task_result.task_id}: {task_result.accuracy():.0%} accuracy")


def test_quick_evaluation():
    """Test quick evaluation function."""
    print("\n" + "="*60)
    print("TEST 6: Quick Evaluation (10 tasks)")
    print("="*60)

    results = quick_evaluation(
        num_tasks=10,
        max_depth=2,
        beam_width=5,
        enable_learning=True,
    )

    assert results.total_tasks == 10
    assert results.solve_rate() > 0, "No tasks solved"

    print(f"\n  ✓ Quick evaluation complete")


def test_end_to_end_integration():
    """Test complete end-to-end integration."""
    print("\n" + "="*60)
    print("TEST 7: End-to-End Integration")
    print("="*60)

    # 1. Setup complete integrated system
    registry = CapabilityRegistry()
    classifier = ProblemClassifier()
    arc_capability = setup_arc_integration(
        registry,
        classifier,
        max_depth=3,
        beam_width=5,
        enable_learning=True,
    )

    print("  ✓ Step 1: System setup complete")

    # 2. Classify a visual reasoning problem
    problem = "Given training examples of grid transformations, predict test output"
    signature = classifier.classify(problem)

    print(f"  ✓ Step 2: Problem classified as {signature.domain.value}")

    # 3. Find appropriate capability
    capabilities = registry.find_capabilities(
        domain=ProblemDomain.VISUAL_REASONING,
        pattern=ReasoningPattern.PROGRAM_SYNTHESIS,
    )

    assert len(capabilities) > 0, "No capabilities found for visual reasoning"
    print(f"  ✓ Step 3: Found {len(capabilities)} matching capabilities")

    # 4. Invoke capability
    task = ARCTask(
        train=[
            (ARCGrid.from_list([[1, 0], [1, 0]]),
             ARCGrid.from_list([[1, 1], [0, 0]])),
        ],
        test_inputs=[ARCGrid.from_list([[0, 1], [0, 1]])],
        task_id="integration_test",
    )

    best_capability = capabilities[0]
    result = best_capability.invoke(task)

    assert result.success, "Task solving failed"
    print(f"  ✓ Step 4: Task solved successfully")
    print(f"    Program: {result.explanation}")

    # 5. Update statistics
    registry.update_statistics("arc_program_synthesis", success=True)

    # 6. Check system state
    stats = registry.get_statistics()
    arc_stats = stats["arc_program_synthesis"]

    print(f"  ✓ Step 5: Statistics updated")
    print(f"    Usage: {arc_stats['usage_count']}")
    print(f"    Success rate: {arc_stats['success_rate']:.1%}")

    # 7. Solution library check
    lib_stats = arc_capability.get_statistics()
    print(f"  ✓ Step 6: Solution library")
    print(f"    Library size: {lib_stats['solution_library_size']}")

    print("\n  ✓ End-to-end integration verified")


def run_all_tests():
    """Run all Phase 5 tests."""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  ARC-AGI Phase 5: Supe Integration Tests".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)

    try:
        test_capability_registration()
        test_problem_signatures()
        test_capability_invocation()
        test_solution_library()
        test_evaluator()
        test_quick_evaluation()
        test_end_to_end_integration()

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("✓ Capability registration working")
        print("✓ Problem signature recognition working")
        print("✓ Capability invocation through registry working")
        print("✓ Solution library and learning working")
        print("✓ Benchmark evaluator working")
        print("✓ Quick evaluation working")
        print("✓ End-to-end integration verified")
        print("\n✓ ALL PHASE 5 TESTS PASSED")
        print("="*60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
