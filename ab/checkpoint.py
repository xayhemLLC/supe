"""Memory checkpoint protocol for AB and Tasc integration.

This module defines helper functions for persisting key state at
critical phases of a Tasc lifecycle. A checkpoint ensures that
subsequent cognitive cycles have access to all necessary context
without relying on transient agent or Cursor memory. By writing
structured cards into AB at defined moments—after planning,
execution, validation or failure—we guarantee continuity of
knowledge between stateless workers.

The functions defined here build upon the card utilities in
``ab.card_utils``. They create the appropriate card (spec,
plan, decision, evidence or bug) and record connections back to
the originating Tasc. This module can be extended to support
additional checkpoint types as needed.
"""

from __future__ import annotations

from typing import List, Optional, Dict

from .abdb import ABMemory
from .card_utils import (
    create_spec_card,
    create_plan_card,
    create_decision_card,
    create_bug_card,
    create_evidence_card,
    create_convo_card,
)


def checkpoint_after_planning(
    memory: ABMemory,
    tasc_card_id: int,
    spec: str,
    plan: str,
    known_pitfalls: Optional[List[str]] = None,
    definition_of_done: Optional[List[str]] = None,
    plan_items: Optional[List[str]] = None,
    owner_self: Optional[str] = None,
    moment_id: Optional[int] = None,
) -> Dict[str, int]:
    """Persist the specification and plan for a Tasc.

    This checkpoint captures both the problem definition (spec) and
    the intended solution approach (plan). It creates a spec card
    and a plan card, linking both back to the Tasc. Optionally,
    lists of pitfalls and definition-of-done criteria are stored
    alongside the spec; the plan can be further broken into
    discrete items.

    Args:
        memory: The AB storage manager.
        tasc_card_id: The ID of the Tasc card being planned.
        spec: The specification text.
        plan: The overall plan text.
        known_pitfalls: Optional list of known challenges.
        definition_of_done: Optional list of completion criteria.
        plan_items: Optional list of plan steps.
        owner_self: Optional author identity.
        moment_id: Optional moment association for these cards.

    Returns:
        A dictionary containing the new card IDs: ``{"spec_id": id1,
        "plan_id": id2}``.
    """
    spec_id = create_spec_card(
        memory=memory,
        tasc_card_id=tasc_card_id,
        spec=spec,
        known_pitfalls=known_pitfalls,
        definition_of_done=definition_of_done,
        owner_self=owner_self,
        moment_id=moment_id,
    )
    plan_id = create_plan_card(
        memory=memory,
        tasc_card_id=tasc_card_id,
        plan=plan,
        plan_items=plan_items,
        owner_self=owner_self,
        moment_id=moment_id,
    )
    return {"spec_id": spec_id, "plan_id": plan_id}


def checkpoint_after_decision(
    memory: ABMemory,
    tasc_card_id: int,
    decision: str,
    reasoning: Optional[str] = None,
    owner_self: Optional[str] = None,
    moment_id: Optional[int] = None,
) -> int:
    """Persist the chosen decision and rationale for a Tasc.

    A decision card records the course of action selected during
    execution. Optionally, it includes a textual rationale. The
    card is connected back to the Tasc via a ``decision_of``
    relation.

    Args:
        memory: The AB storage manager.
        tasc_card_id: The ID of the Tasc card receiving the decision.
        decision: The action chosen or decision text.
        reasoning: Optional rationale or explanation.
        owner_self: Optional author identity.
        moment_id: Optional moment association.

    Returns:
        The ID of the newly created decision card.
    """
    decision_id = create_decision_card(
        memory=memory,
        tasc_card_id=tasc_card_id,
        decision=decision,
        reasoning=reasoning,
        owner_self=owner_self,
        moment_id=moment_id,
    )
    return decision_id


def checkpoint_after_evidence(
    memory: ABMemory,
    tasc_card_id: int,
    evidence_data: bytes,
    content_type: str,
    description: Optional[str] = None,
    owner_self: Optional[str] = None,
    moment_id: Optional[int] = None,
) -> int:
    """Persist evidence produced during execution or validation.

    Evidence could be a generated file, a screenshot, a test report,
    or any artefact produced by the agent or human executing the
    Tasc. Storing evidence as a card allows later review and
    auditing.

    Args:
        memory: The AB storage manager.
        tasc_card_id: The ID of the Tasc card to which the
            evidence applies.
        evidence_data: Raw bytes of the evidence.
        content_type: MIME type of the evidence.
        description: Optional textual description of the evidence.
        owner_self: Optional author identity.
        moment_id: Optional moment association.

    Returns:
        The ID of the new evidence card.
    """
    evidence_id = create_evidence_card(
        memory=memory,
        tasc_card_id=tasc_card_id,
        evidence=evidence_data,
        content_type=content_type,
        description=description,
        owner_self=owner_self,
        moment_id=moment_id,
    )
    return evidence_id


def checkpoint_after_bug(
    memory: ABMemory,
    tasc_card_id: int,
    description: str,
    reproduction_steps: Optional[str] = None,
    fix: Optional[str] = None,
    owner_self: Optional[str] = None,
    moment_id: Optional[int] = None,
) -> int:
    """Persist a bug encountered during execution or validation.

    Args:
        memory: The AB storage manager.
        tasc_card_id: The ID of the Tasc card encountering the bug.
        description: Description of the bug.
        reproduction_steps: Optional steps to reproduce the bug.
        fix: Optional description of any workaround or fix.
        owner_self: Optional author identity.
        moment_id: Optional moment association.

    Returns:
        The ID of the new bug card.
    """
    bug_id = create_bug_card(
        memory=memory,
        tasc_card_id=tasc_card_id,
        description=description,
        reproduction_steps=reproduction_steps,
        fix=fix,
        owner_self=owner_self,
        moment_id=moment_id,
    )
    return bug_id


def checkpoint_after_conversation(
    memory: ABMemory,
    tasc_card_id: int,
    conversation: str,
    owner_self: Optional[str] = None,
    moment_id: Optional[int] = None,
) -> int:
    """Persist a conversation transcript related to a Tasc.

    This checkpoint stores a textual transcript of a conversation
    (e.g. chat history, meeting notes). It is assumed that the
    conversation has been summarised or compressed prior to
    storage.

    Args:
        memory: The AB storage manager.
        tasc_card_id: The ID of the Tasc card the conversation
            concerns.
        conversation: The conversation text.
        owner_self: Optional author identity.
        moment_id: Optional moment association.

    Returns:
        The ID of the new conversation card.
    """
    convo_id = create_convo_card(
        memory=memory,
        tasc_card_id=tasc_card_id,
        conversation=conversation,
        owner_self=owner_self,
        moment_id=moment_id,
    )
    return convo_id