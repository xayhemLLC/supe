"""Overlord Prompt Injection Block.

Builds context for LLM prompts with action metadata,
constraints, and current state.
"""

from typing import Any, Dict, List, Optional

import yaml

from ..action_registry import get_registry, ActionMetadata, ActionCategory


def build_action_context(
    available_actions: Optional[List[str]] = None,
    permissions: Optional[List[str]] = None,
    has_checkpoint: bool = False,
    in_sandbox: bool = False,
) -> str:
    """Build action context block for LLM prompt.
    
    This context helps the LLM understand:
    - What actions are available
    - Which are mutations vs observations
    - What permissions/constraints exist
    - What evidence each action produces
    
    Args:
        available_actions: Filter to these actions only.
        permissions: Current permission set.
        has_checkpoint: Whether checkpoint is active.
        in_sandbox: Whether in sandbox mode.
    
    Returns:
        Formatted context string for prompt injection.
    """
    registry = get_registry()
    
    lines = [
        "# Available Actions",
        "",
        "## Current State",
        f"- Checkpoint Active: {has_checkpoint}",
        f"- Sandbox Mode: {in_sandbox}",
        f"- Permissions: {', '.join(permissions or ['none'])}",
        "",
    ]
    
    # Get actions by category
    try:
        all_actions = registry.list_all()
    except Exception:
        # Registry not loaded
        lines.append("*(Action registry not available)*")
        return "\n".join(lines)
    
    # Filter if specified
    if available_actions:
        all_actions = [a for a in all_actions if a.id in available_actions]
    
    # Group by category
    observations = [a for a in all_actions if a.category == ActionCategory.OBSERVATION]
    mutations = [a for a in all_actions if a.category == ActionCategory.MUTATION]
    controls = [a for a in all_actions if a.category == ActionCategory.CONTROL]
    
    # Observations
    lines.append("## Observation Actions (read-only)")
    lines.append("")
    for action in observations:
        lines.append(f"### `{action.id}`")
        lines.append(f"{action.description}")
        lines.append(f"- Produces: {', '.join(action.evidence_produced)}")
        lines.append("")
    
    # Mutations
    lines.append("## Mutation Actions (state-changing)")
    lines.append("")
    lines.append("> ⚠️ Mutations require active checkpoint unless otherwise noted.")
    lines.append("")
    for action in mutations:
        requires = []
        if action.requires_checkpoint:
            requires.append("checkpoint")
        if action.sandbox_only:
            requires.append("sandbox")
        if action.gated:
            requires.append("approval")
        
        req_str = f" [requires: {', '.join(requires)}]" if requires else ""
        risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(
            action.risk_level.value, "⚪"
        )
        
        lines.append(f"### `{action.id}` {risk_icon}{req_str}")
        lines.append(f"{action.description}")
        lines.append(f"- Risk: {action.risk_level.value}")
        lines.append(f"- Rollback: {'yes' if action.rollback_supported else 'no'}")
        lines.append("")
    
    # Controls
    lines.append("## Control Actions")
    lines.append("")
    for action in controls:
        lines.append(f"### `{action.id}`")
        lines.append(f"{action.description}")
        lines.append("")
    
    return "\n".join(lines)


def inject_action_metadata(
    action_id: str,
) -> str:
    """Get formatted metadata for a specific action.
    
    Args:
        action_id: Action to get metadata for.
    
    Returns:
        Formatted metadata string.
    """
    registry = get_registry()
    
    try:
        action = registry.get(action_id)
    except Exception:
        return f"*Unknown action: {action_id}*"
    
    if not action:
        return f"*Unknown action: {action_id}*"
    
    return f"""## Action: `{action.id}`

**{action.name}**

{action.description}

| Property | Value |
|----------|-------|
| Category | {action.category.value} |
| Mutates State | {action.mutates_state} |
| Risk Level | {action.risk_level.value} |
| Requires Checkpoint | {action.requires_checkpoint} |
| Rollback Supported | {action.rollback_supported} |
| Sandbox Only | {action.sandbox_only} |
| Gated | {action.gated} |

**Permissions Required:** {', '.join(action.permissions_required) or 'none'}

**Evidence Produced:** {', '.join(action.evidence_produced)}
"""


def build_stop_conditions_context() -> str:
    """Build context explaining stop conditions."""
    return """# Stop Conditions

The agent should STOP when any of these conditions are met:

1. **No Legal Actions** - No remaining action can be legally executed
2. **Low Information Gain** - Recent actions aren't producing new insights
3. **Repeated Observations** - Same observation seen multiple times
4. **Budget Exhausted** - Action limit reached
5. **Hypothesis Proven/Disproven** - Goal determined
6. **Safety Guard** - Security violation detected
7. **Goal Achieved** - Task completed successfully

Stopping is a **decision**, not a failure. Emit:
```json
{
  "decision": "STOP",
  "reason": "Explanation of why stopping is correct"
}
```
"""


def build_full_overlord_context(
    permissions: Optional[List[str]] = None,
    has_checkpoint: bool = False,
    in_sandbox: bool = False,
    current_hypothesis: Optional[str] = None,
    actions_taken: int = 0,
    max_actions: int = 100,
) -> str:
    """Build complete Overlord context for LLM prompt.
    
    Args:
        permissions: Current permission set.
        has_checkpoint: Whether checkpoint is active.
        in_sandbox: Whether in sandbox mode.
        current_hypothesis: Current working hypothesis.
        actions_taken: Number of actions taken.
        max_actions: Maximum actions allowed.
    
    Returns:
        Complete formatted context for Overlord prompt.
    """
    lines = [
        "# Overlord Context",
        "",
        "You are the Overlord - the narrator and chooser, not the executor.",
        "",
        "## Current State",
        f"- Actions Taken: {actions_taken}/{max_actions}",
        f"- Checkpoint Active: {has_checkpoint}",
        f"- Sandbox Mode: {in_sandbox}",
    ]
    
    if current_hypothesis:
        lines.append(f"- Hypothesis: {current_hypothesis}")
    
    lines.append("")
    lines.append(build_action_context(
        permissions=permissions,
        has_checkpoint=has_checkpoint,
        in_sandbox=in_sandbox,
    ))
    lines.append("")
    lines.append(build_stop_conditions_context())
    
    return "\n".join(lines)
