"""Utility functions to create structured AB cards for common phases.

This module defines helper functions for constructing and storing
specialised cards in the AB memory. Each card type corresponds to a
distinct phase of the work cycle (specification, planning, execution
decision, evidence collection, bug reporting or conversation summary).

Cards are stored using the generic ``store_card`` API provided by
``ABMemory``. These helpers handle buffer construction, sensible
header assignment and connection creation between the new card and
its originating Tasc card. Connections encode relations such as
``spec_for``, ``plan_for`` or ``evidence_of``. When additional
metadata is provided (e.g. known pitfalls or definitions of done),
these are serialised as JSON strings and stored in their own
buffers.

These functions all accept an optional ``moment_id`` argument. If
provided, the new card will be associated with that moment; if
``None`` the card is stored without a moment and may be linked
later.
"""

from __future__ import annotations

import json
from typing import List, Optional, Dict

from .models import Buffer
from .abdb import ABMemory


def _serialise_list(lst: List[str]) -> str:
    """Serialise a list of strings as a JSON array.

    Args:
        lst: The list of strings to serialise.

    Returns:
        A JSON string representing the list. An empty list becomes
        ``"[]"``. The function ensures stable ordering for
        reproducibility.
    """
    return json.dumps(lst, ensure_ascii=False)


def create_spec_card(
    memory: ABMemory,
    tasc_card_id: int,
    spec: str,
    known_pitfalls: Optional[List[str]] = None,
    definition_of_done: Optional[List[str]] = None,
    owner_self: Optional[str] = None,
    moment_id: Optional[int] = None,
) -> int:
    """Create a specification card for a Tasc.

    The specification card captures the formal problem definition and
    requirements. It may also include a list of known pitfalls and a
    definition of what constitutes a complete solution.

    Args:
        memory: The AB storage manager.
        tasc_card_id: The ID of the Tasc card this spec belongs to.
        spec: The textual specification.
        known_pitfalls: Optional list of pitfalls or potential
            challenges.
        definition_of_done: Optional list defining completion
            criteria.
        owner_self: Optional identity of the author.
        moment_id: Optional moment association.

    Returns:
        The ID of the newly created spec card.
    """
    buffers: List[Buffer] = []
    # Primary spec text
    buffers.append(
        Buffer(
            name="spec_text",
            headers={"content_type": "text/plain"},
            payload=spec.encode("utf-8"),
        )
    )
    # Known pitfalls as JSON array if provided
    if known_pitfalls:
        buffers.append(
            Buffer(
                name="known_pitfalls",
                headers={"content_type": "application/json"},
                payload=_serialise_list(known_pitfalls).encode("utf-8"),
            )
        )
    # Definition of done as JSON array
    if definition_of_done:
        buffers.append(
            Buffer(
                name="definition_of_done",
                headers={"content_type": "application/json"},
                payload=_serialise_list(definition_of_done).encode("utf-8"),
            )
        )
    # Store the spec card
    card = memory.store_card(
        label="spec", buffers=buffers, owner_self=owner_self, moment_id=moment_id
    )
    # Link spec card to tasc card
    memory.create_connection(card.id, tasc_card_id, "spec_for")
    return card.id  # type: ignore


def create_plan_card(
    memory: ABMemory,
    tasc_card_id: int,
    plan: str,
    plan_items: Optional[List[str]] = None,
    owner_self: Optional[str] = None,
    moment_id: Optional[int] = None,
) -> int:
    """Create a plan card describing the intended approach.

    Args:
        memory: The AB storage manager.
        tasc_card_id: The ID of the Tasc card this plan belongs to.
        plan: The overall plan description.
        plan_items: Optional breakdown of plan steps.
        owner_self: Optional identity of the author.
        moment_id: Optional moment association.

    Returns:
        The ID of the newly created plan card.
    """
    buffers: List[Buffer] = []
    buffers.append(
        Buffer(
            name="plan_text",
            headers={"content_type": "text/plain"},
            payload=plan.encode("utf-8"),
        )
    )
    if plan_items:
        buffers.append(
            Buffer(
                name="plan_items",
                headers={"content_type": "application/json"},
                payload=_serialise_list(plan_items).encode("utf-8"),
            )
        )
    card = memory.store_card(
        label="plan", buffers=buffers, owner_self=owner_self, moment_id=moment_id
    )
    memory.create_connection(card.id, tasc_card_id, "plan_for")
    return card.id  # type: ignore


def create_decision_card(
    memory: ABMemory,
    tasc_card_id: int,
    decision: str,
    reasoning: Optional[str] = None,
    owner_self: Optional[str] = None,
    moment_id: Optional[int] = None,
) -> int:
    """Create a decision card documenting the chosen course of action.

    Args:
        memory: The AB storage manager.
        tasc_card_id: The ID of the Tasc card this decision relates to.
        decision: A textual description of the selected action or
            strategy.
        reasoning: Optional rationale for the decision.
        owner_self: Optional author identity.
        moment_id: Optional moment association.

    Returns:
        The ID of the newly created decision card.
    """
    buffers: List[Buffer] = []
    buffers.append(
        Buffer(
            name="decision_text",
            headers={"content_type": "text/plain"},
            payload=decision.encode("utf-8"),
        )
    )
    if reasoning:
        buffers.append(
            Buffer(
                name="reasoning",
                headers={"content_type": "text/plain"},
                payload=reasoning.encode("utf-8"),
            )
        )
    card = memory.store_card(
        label="decision", buffers=buffers, owner_self=owner_self, moment_id=moment_id
    )
    memory.create_connection(card.id, tasc_card_id, "decision_of")
    return card.id  # type: ignore


def create_evidence_card(
    memory: ABMemory,
    tasc_card_id: int,
    evidence: bytes,
    content_type: str,
    description: Optional[str] = None,
    owner_self: Optional[str] = None,
    moment_id: Optional[int] = None,
) -> int:
    """Create an evidence card storing binary artefacts or data.

    Args:
        memory: The AB storage manager.
        tasc_card_id: The ID of the Tasc this evidence supports.
        evidence: Binary payload (e.g. file contents, screenshot).
        content_type: MIME type of the evidence (e.g.
            ``"application/octet-stream"`` or ``"image/png"``).
        description: Optional textual description of the evidence.
        owner_self: Optional author identity.
        moment_id: Optional moment association.

    Returns:
        The ID of the newly created evidence card.
    """
    buffers: List[Buffer] = []
    buffers.append(
        Buffer(
            name="evidence",
            headers={"content_type": content_type},
            payload=evidence,
        )
    )
    if description:
        buffers.append(
            Buffer(
                name="description",
                headers={"content_type": "text/plain"},
                payload=description.encode("utf-8"),
            )
        )
    card = memory.store_card(
        label="evidence", buffers=buffers, owner_self=owner_self, moment_id=moment_id
    )
    memory.create_connection(card.id, tasc_card_id, "evidence_of")
    return card.id  # type: ignore


def create_bug_card(
    memory: ABMemory,
    tasc_card_id: int,
    description: str,
    reproduction_steps: Optional[str] = None,
    fix: Optional[str] = None,
    owner_self: Optional[str] = None,
    moment_id: Optional[int] = None,
) -> int:
    """Create a bug card capturing an issue encountered.

    Args:
        memory: The AB storage manager.
        tasc_card_id: The ID of the Tasc that encountered the bug.
        description: Description of the bug.
        reproduction_steps: Optional steps to reproduce.
        fix: Optional fix or workaround description.
        owner_self: Optional author identity.
        moment_id: Optional moment association.

    Returns:
        The ID of the newly created bug card.
    """
    buffers: List[Buffer] = []
    buffers.append(
        Buffer(
            name="bug_description",
            headers={"content_type": "text/plain"},
            payload=description.encode("utf-8"),
        )
    )
    if reproduction_steps:
        buffers.append(
            Buffer(
                name="reproduction_steps",
                headers={"content_type": "text/plain"},
                payload=reproduction_steps.encode("utf-8"),
            )
        )
    if fix:
        buffers.append(
            Buffer(
                name="fix", headers={"content_type": "text/plain"}, payload=fix.encode("utf-8")
            )
        )
    card = memory.store_card(
        label="bug", buffers=buffers, owner_self=owner_self, moment_id=moment_id
    )
    memory.create_connection(card.id, tasc_card_id, "bug_of")
    return card.id  # type: ignore


def create_convo_card(
    memory: ABMemory,
    tasc_card_id: int,
    conversation: str,
    owner_self: Optional[str] = None,
    moment_id: Optional[int] = None,
) -> int:
    """Create a conversation card storing compressed dialogue.

    Args:
        memory: The AB storage manager.
        tasc_card_id: The ID of the Tasc this conversation relates to.
        conversation: Text of the conversation (should be
            pre-compressed or summarised before being stored).
        owner_self: Optional author identity.
        moment_id: Optional moment association.

    Returns:
        The ID of the newly created conversation card.
    """
    buffers: List[Buffer] = []
    buffers.append(
        Buffer(
            name="conversation",
            headers={"content_type": "text/plain"},
            payload=conversation.encode("utf-8"),
        )
    )
    card = memory.store_card(
        label="conversation", buffers=buffers, owner_self=owner_self, moment_id=moment_id
    )
    memory.create_connection(card.id, tasc_card_id, "conversation_of")
    return card.id  # type: ignore