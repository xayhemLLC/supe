"""Claude-based TascPlan generation.

Uses Claude (Anthropic API) to generate executable, validatable plans from natural language goals.
"""

import json
import os
from typing import Optional

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .llm_planner import (
    PlanGenerationRequest,
    GeneratedPlan,
    generate_plan_prompt,
    parse_generated_plan,
)


class ClaudePlanner:
    """Generate TascPlans using Claude."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
    ):
        """Initialize Claude planner.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No API key provided. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter"
            )

        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate_plan(
        self,
        request: PlanGenerationRequest,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> GeneratedPlan:
        """Generate a TascPlan using Claude.

        Args:
            request: Plan generation request
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            GeneratedPlan with parsed plan and metadata

        Example:
            >>> planner = ClaudePlanner()
            >>> request = PlanGenerationRequest(
            ...     goal="Fix the 500 error on login endpoint",
            ...     context="FastAPI app with JWT auth",
            ...     constraints=["Must maintain backwards compatibility"],
            ... )
            >>> result = planner.generate_plan(request)
            >>> print(result.plan.title)
            >>> print(f"Confidence: {result.confidence}")
        """
        # Generate prompt
        prompt = generate_plan_prompt(request)

        # Call Claude API
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract response text
        response_text = message.content[0].text

        # Parse into GeneratedPlan
        try:
            plan = parse_generated_plan(response_text, request)
            return plan
        except Exception as e:
            raise ValueError(f"Failed to parse Claude response: {e}\n\nResponse:\n{response_text}")

    def generate_plan_streaming(
        self,
        request: PlanGenerationRequest,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """Generate a plan with streaming output.

        Yields text chunks as they arrive from Claude.
        Returns the final GeneratedPlan at the end.

        Args:
            request: Plan generation request
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Text chunks from Claude

        Returns:
            Final GeneratedPlan (yielded as last item)

        Example:
            >>> planner = ClaudePlanner()
            >>> for chunk in planner.generate_plan_streaming(request):
            ...     if isinstance(chunk, str):
            ...         print(chunk, end="", flush=True)
            ...     else:
            ...         plan = chunk  # Final result
        """
        prompt = generate_plan_prompt(request)

        response_text = ""

        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                response_text += text
                yield text

        # Parse final response
        plan = parse_generated_plan(response_text, request)
        yield plan


def generate_plan_with_claude(
    goal: str,
    context: str = "",
    constraints: list = None,
    max_tascs: int = 10,
    require_approval: bool = True,
    prior_tasc_ids: list = None,
    api_key: Optional[str] = None,
    model: str = "claude-sonnet-4-5-20250929",
    temperature: float = 0.7,
) -> GeneratedPlan:
    """Convenience function to generate a plan with Claude.

    Args:
        goal: Natural language goal
        context: Additional context
        constraints: List of constraints
        max_tascs: Maximum number of tascs
        require_approval: Add approval gate at end
        prior_tasc_ids: Previous tascs to cite
        api_key: Anthropic API key
        model: Claude model to use
        temperature: Sampling temperature

    Returns:
        GeneratedPlan

    Example:
        >>> plan = generate_plan_with_claude(
        ...     goal="Add dark mode to settings page",
        ...     context="React app with TailwindCSS",
        ...     constraints=["Must work in all browsers"],
        ... )
        >>> print(plan.plan.title)
        >>> for tasc in plan.plan.tascs:
        ...     print(f"- {tasc.title}")
    """
    planner = ClaudePlanner(api_key=api_key, model=model)

    request = PlanGenerationRequest(
        goal=goal,
        context=context,
        constraints=constraints or [],
        max_tascs=max_tascs,
        require_approval=require_approval,
        prior_tasc_ids=prior_tasc_ids or [],
    )

    return planner.generate_plan(request, temperature=temperature)


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m tascer.claude_planner 'your goal here'")
        sys.exit(1)

    goal = " ".join(sys.argv[1:])

    print(f"Generating plan for: {goal}\n")

    try:
        result = generate_plan_with_claude(
            goal=goal,
            context="Python project with pytest",
        )

        print(f"✅ Plan: {result.plan.title}")
        print(f"📊 Confidence: {result.confidence:.0%}")
        print(f"💭 Reasoning: {result.reasoning}\n")
        print(f"📋 Tascs ({len(result.plan.tascs)}):")
        for i, tasc in enumerate(result.plan.tascs, 1):
            deps = f" (after {', '.join(tasc.dependencies)})" if tasc.dependencies else ""
            print(f"  {i}. {tasc.title}{deps}")
            if tasc.testing_instructions:
                print(f"     Test: {tasc.testing_instructions}")

        print(f"\n💾 Plan ID: {result.plan.id}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
