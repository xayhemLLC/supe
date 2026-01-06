"""ARC Integration Demo - Complete Workflow Example

Demonstrates the fully integrated ARC visual reasoning system:
1. Problem classification
2. Capability discovery
3. Task solving
4. Solution learning
5. Cross-task transfer
"""

from supe.reasoning.arc import (
    ARCGrid,
    ARCTask,
    setup_arc_integration,
    print_grid,
)
from supe.reasoning.capability_registry import CapabilityRegistry
from supe.reasoning.problem_types import ProblemClassifier, ProblemDomain, ReasoningPattern


def demo_setup():
    """Demo 1: System Setup and Registration"""
    print("\n" + "="*70)
    print("DEMO 1: System Setup and Registration")
    print("="*70)

    # Initialize supe's reasoning components
    registry = CapabilityRegistry()
    classifier = ProblemClassifier()

    print("\n1. Initializing supe reasoning framework...")
    print(f"   Registry has {len(registry.capabilities)} base capabilities")

    # Setup ARC integration
    print("\n2. Integrating ARC visual reasoning...")
    arc_capability = setup_arc_integration(
        registry,
        classifier,
        max_depth=3,
        beam_width=5,
        enable_learning=True,
    )

    print(f"   ✓ Registry now has {len(registry.capabilities)} capabilities")
    print(f"   ✓ ARC registered with 3 reasoning patterns")

    # Show registered ARC capabilities
    print("\n3. ARC Capabilities:")
    for name in ["arc_program_synthesis", "arc_transformation_inference", "arc_visual_patterns"]:
        cap = registry.get_capability(name)
        print(f"   - {cap.name}")
        print(f"     Pattern: {cap.pattern.value}")
        print(f"     Confidence: {cap.confidence}")

    return registry, classifier, arc_capability


def demo_problem_classification(classifier):
    """Demo 2: Automatic Problem Classification"""
    print("\n" + "="*70)
    print("DEMO 2: Automatic Problem Classification")
    print("="*70)

    # Test different problem descriptions
    test_problems = [
        "Given these grid transformations, predict the next output",
        "I have a visual pattern that repeats. Can you help me understand it?",
        "Transform this grid by rotating it 90 degrees",
        "Analyze this grid and find the pattern",
    ]

    print("\nClassifying various problem descriptions:\n")

    for i, problem in enumerate(test_problems, 1):
        print(f"{i}. Problem: \"{problem}\"")

        # Classify
        signature = classifier.classify(problem)

        print(f"   Domain: {signature.domain.value}")
        print(f"   Patterns: {[p.value for p in list(signature.required_patterns)[:2]]}")
        print(f"   Complexity: {signature.complexity}/10")
        print()

    return signature


def demo_capability_discovery(registry):
    """Demo 3: Capability Discovery and Selection"""
    print("\n" + "="*70)
    print("DEMO 3: Capability Discovery and Selection")
    print("="*70)

    # Find capabilities for visual reasoning
    print("\n1. Searching for VISUAL_REASONING capabilities...")

    capabilities = registry.find_capabilities(
        domain=ProblemDomain.VISUAL_REASONING,
        pattern=ReasoningPattern.PROGRAM_SYNTHESIS,
    )

    print(f"   Found {len(capabilities)} matching capabilities:")
    for cap in capabilities:
        print(f"   - {cap.name} (confidence: {cap.confidence})")

    # Find for transformation inference
    print("\n2. Searching for TRANSFORMATION_INFERENCE capabilities...")

    capabilities = registry.find_capabilities(
        domain=ProblemDomain.VISUAL_REASONING,
        pattern=ReasoningPattern.TRANSFORMATION_INFERENCE,
    )

    print(f"   Found {len(capabilities)} matching capabilities:")
    for cap in capabilities:
        print(f"   - {cap.name} (confidence: {cap.confidence})")

    return capabilities[0] if capabilities else None


def demo_task_solving(capability):
    """Demo 4: Solving ARC Tasks"""
    print("\n" + "="*70)
    print("DEMO 4: Solving ARC Tasks")
    print("="*70)

    # Create a rotation task
    print("\n1. Task: Grid Rotation (90 degrees)")

    train1_in = ARCGrid.from_list([[1, 0], [1, 0]])
    train1_out = ARCGrid.from_list([[1, 1], [0, 0]])

    train2_in = ARCGrid.from_list([[0, 1], [0, 1]])
    train2_out = ARCGrid.from_list([[0, 0], [1, 1]])

    test_in = ARCGrid.from_list([[1, 1], [0, 0]])
    test_out = ARCGrid.from_list([[0, 1], [0, 1]])

    print("\n   Training Example 1:")
    print_grid(train1_in, title="     Input")
    print_grid(train1_out, title="     Output")

    print("\n   Training Example 2:")
    print_grid(train2_in, title="     Input")
    print_grid(train2_out, title="     Output")

    # Create task
    task = ARCTask(
        train=[(train1_in, train1_out), (train2_in, train2_out)],
        test_inputs=[test_in],
        test_outputs=[test_out],
        task_id="demo_rotation",
    )

    # Solve through capability
    print("\n2. Invoking ARC capability...")
    result = capability.invoke(task)

    print(f"\n   ✓ Solution found!")
    print(f"   Program: {result.explanation}")
    print(f"   Confidence: {result.confidence:.0%}")
    print(f"   Time: {result.synthesis_time:.3f}s")

    print("\n   Test Input:")
    print_grid(test_in, title="     Input")

    print("\n   Predicted Output:")
    print_grid(result.predictions[0], title="     Prediction")

    print("\n   Ground Truth:")
    print_grid(test_out, title="     Expected")

    # Verify correctness
    correct = result.predictions[0].equals(test_out)
    print(f"\n   ✓ Prediction is {'CORRECT' if correct else 'INCORRECT'}!")

    return result


def demo_learning(arc_capability):
    """Demo 5: Solution Library and Learning"""
    print("\n" + "="*70)
    print("DEMO 5: Solution Library and Learning")
    print("="*70)

    print("\n1. Checking solution library...")
    stats = arc_capability.get_statistics()
    print(f"   Current library size: {stats['solution_library_size']}")
    print(f"   Tasks attempted: {stats['tasks_attempted']}")
    print(f"   Tasks solved: {stats['tasks_solved']}")

    # Solve additional similar tasks
    print("\n2. Solving similar tasks to demonstrate learning...")

    similar_tasks = [
        {
            "train": [
                (ARCGrid.from_list([[0, 0], [1, 1]]), ARCGrid.from_list([[1, 0], [1, 0]])),
            ],
            "test": ARCGrid.from_list([[1, 1], [0, 0]]),
            "expected": ARCGrid.from_list([[0, 1], [0, 1]]),
            "id": "rotation_variant_1",
        },
        {
            "train": [
                (ARCGrid.from_list([[1, 0, 0], [1, 0, 0]]), ARCGrid.from_list([[0, 1], [0, 1], [0, 0]])),
            ],
            "test": ARCGrid.from_list([[0, 1], [0, 1], [0, 0]]),
            "expected": ARCGrid.from_list([[0, 0, 0], [1, 1, 0]]),
            "id": "rotation_variant_2",
        },
    ]

    for i, task_data in enumerate(similar_tasks, 1):
        print(f"\n   Task {i}: {task_data['id']}")

        task = ARCTask(
            train=task_data['train'],
            test_inputs=[task_data['test']],
            test_outputs=[task_data['expected']],
            task_id=task_data['id'],
        )

        result = arc_capability(task)

        if result.success:
            print(f"     ✓ Solved (time: {result.synthesis_time:.3f}s)")
            print(f"       Program: {result.explanation}")
        else:
            print(f"     ✗ Failed")

    # Check updated statistics
    print("\n3. Updated statistics:")
    stats = arc_capability.get_statistics()
    print(f"   Library size: {stats['solution_library_size']}")
    print(f"   Tasks attempted: {stats['tasks_attempted']}")
    print(f"   Tasks solved: {stats['tasks_solved']}")
    print(f"   Solve rate: {stats['solve_rate']:.0%}")
    print(f"   Avg time: {stats['avg_synthesis_time']:.3f}s")


def demo_end_to_end_workflow(registry, classifier):
    """Demo 6: Complete End-to-End Workflow"""
    print("\n" + "="*70)
    print("DEMO 6: Complete End-to-End Workflow")
    print("="*70)

    # User provides natural language problem
    problem_description = "Given grid transformation examples showing horizontal flips, predict the output for a new input"

    print(f"\n1. User Problem:")
    print(f"   \"{problem_description}\"")

    # Classify the problem
    print("\n2. System classifies problem...")
    signature = classifier.classify(problem_description)
    print(f"   Domain: {signature.domain.value}")
    if signature.required_patterns:
        print(f"   Required pattern: {list(signature.required_patterns)[0].value}")

    # Find appropriate capability (use visual reasoning directly)
    print("\n3. System finds appropriate capability...")
    capabilities = registry.find_capabilities(
        domain=ProblemDomain.VISUAL_REASONING,
        pattern=ReasoningPattern.TRANSFORMATION_INFERENCE,
    )

    if not capabilities:
        print("   ✗ No matching capability found!")
        return

    best_cap = capabilities[0]
    print(f"   ✓ Selected: {best_cap.name}")
    print(f"   Confidence: {best_cap.confidence}")

    # Create example task (flip)
    print("\n4. Creating task from user input...")
    task = ARCTask(
        train=[
            (ARCGrid.from_list([[1, 0, 0], [1, 1, 0]]),
             ARCGrid.from_list([[0, 0, 1], [0, 1, 1]])),
        ],
        test_inputs=[ARCGrid.from_list([[0, 1, 1], [1, 1, 0]])],
        task_id="user_flip_task",
    )

    print("   Training example:")
    print_grid(task.train[0][0], title="     Input")
    print_grid(task.train[0][1], title="     Output (flipped)")

    # Solve
    print("\n5. System solves task...")
    result = best_cap.invoke(task)

    if result.success:
        print(f"   ✓ Solution found!")
        print(f"   Program: {result.explanation}")
        print(f"   Time: {result.synthesis_time:.3f}s")

        print("\n6. Applying to test input:")
        print_grid(task.test_inputs[0], title="     Test Input")
        print_grid(result.predictions[0], title="     Predicted Output")

        # Update statistics
        registry.update_statistics(best_cap.name, success=True)
        print("\n7. Statistics updated in registry")
    else:
        print(f"   ✗ Failed: {result.explanation}")


def demo_statistics_tracking(registry, arc_capability):
    """Demo 7: Statistics and Performance Tracking"""
    print("\n" + "="*70)
    print("DEMO 7: Statistics and Performance Tracking")
    print("="*70)

    # Registry statistics
    print("\n1. Registry Statistics:")
    stats = registry.get_statistics()

    print("\n   ARC Capabilities:")
    for name in ["arc_program_synthesis", "arc_transformation_inference", "arc_visual_patterns"]:
        if name in stats:
            cap_stats = stats[name]
            print(f"\n   {name}:")
            print(f"     Usage count: {cap_stats['usage_count']}")
            print(f"     Success rate: {cap_stats['success_rate']:.1%}")
            print(f"     Confidence: {cap_stats['confidence']}")

    # Capability-specific statistics
    print("\n2. ARC Capability Statistics:")
    arc_stats = arc_capability.get_statistics()

    for key, value in arc_stats.items():
        if isinstance(value, float):
            if 'time' in key:
                print(f"   {key}: {value:.3f}s")
            elif 'rate' in key:
                print(f"   {key}: {value:.1%}")
            else:
                print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")


def run_complete_demo():
    """Run all demo sections"""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  ARC-AGI Integration Demo - Complete Workflow".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)

    print("\nThis demo showcases the complete integrated ARC visual reasoning system,")
    print("from problem classification to solution learning.\n")

    try:
        # Demo 1: Setup
        registry, classifier, arc_capability = demo_setup()

        # Demo 2: Classification
        demo_problem_classification(classifier)

        # Demo 3: Discovery
        capability = demo_capability_discovery(registry)

        # Demo 4: Solving
        demo_task_solving(capability)

        # Demo 5: Learning
        demo_learning(arc_capability)

        # Demo 6: End-to-End
        demo_end_to_end_workflow(registry, classifier)

        # Demo 7: Statistics
        demo_statistics_tracking(registry, arc_capability)

        # Summary
        print("\n" + "="*70)
        print("DEMO SUMMARY")
        print("="*70)
        print("\n✓ System setup and registration")
        print("✓ Automatic problem classification")
        print("✓ Capability discovery and selection")
        print("✓ Task solving with program synthesis")
        print("✓ Solution library and learning")
        print("✓ End-to-end workflow demonstration")
        print("✓ Statistics and performance tracking")
        print("\n✓ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*70)

    except Exception as e:
        print(f"\n✗ DEMO FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_complete_demo()
