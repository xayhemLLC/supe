#!/usr/bin/env python3
"""Test Claude plan generation."""

import os
import sys

# Add to path
sys.path.insert(0, os.path.dirname(__file__))

# Check if API key is set
if not os.getenv("ANTHROPIC_API_KEY"):
    print("⚠️  ANTHROPIC_API_KEY not set")
    print("   Set it with: export ANTHROPIC_API_KEY=your-key")
    print("\nRunning dry-run test without API...")

    # Test imports
    print("\n1. Testing imports...")
    try:
        from tascer import generate_plan
        from tascer.claude_planner import ClaudePlanner
        from tascer.llm_planner import PlanGenerationRequest, generate_plan_prompt
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)

    # Test prompt generation
    print("\n2. Testing prompt generation...")
    request = PlanGenerationRequest(
        goal="Fix the 500 error on login endpoint",
        context="FastAPI app with JWT auth",
        constraints=["Must maintain backwards compatibility"],
    )
    prompt = generate_plan_prompt(request)
    print(f"✅ Generated prompt ({len(prompt)} chars)")
    print(f"   First 200 chars: {prompt[:200]}...")

    print("\n✅ Dry-run test passed!")
    print("\n💡 To test with Claude API:")
    print("   1. Set ANTHROPIC_API_KEY")
    print("   2. Run: python test_claude_plan.py")
    print("   Or use CLI: tascer plan 'your goal here'")
    sys.exit(0)

# Test with actual API
print("🤖 Testing Claude plan generation...\n")

from tascer import generate_plan

try:
    result = generate_plan(
        goal="Add a dark mode toggle to the settings page",
        context="React app with TailwindCSS",
        constraints=["Must work in all browsers", "Should respect user preference"],
        max_tascs=5,
    )

    print(f"✅ Plan generated successfully!")
    print(f"\n📋 Title: {result.plan.title}")
    print(f"📊 Confidence: {result.confidence:.0%}")
    print(f"💭 Reasoning: {result.reasoning}\n")

    print(f"Tascs ({len(result.plan.tascs)}):")
    for i, tasc in enumerate(result.plan.tascs, 1):
        deps = f" (after {', '.join(tasc.dependencies)})" if tasc.dependencies else ""
        print(f"  {i}. {tasc.title}{deps}")
        if tasc.testing_instructions:
            print(f"     Test: {tasc.testing_instructions}")

    print(f"\n💾 Plan ID: {result.plan.id}")
    print("\n✅ All tests passed!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
