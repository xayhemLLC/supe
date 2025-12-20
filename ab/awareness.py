"""Awareness cards and subscription utilities.

Awareness cards are special cards that aggregate context and share
information with subscribers. They allow multiple subselves or tasks
to operate with a common context without duplicating data. Each
awareness card has one or more buffers (e.g., ``prompt``, ``context``),
and other cards can subscribe to updates on these buffers. When a
buffer on an awareness card is modified, the system propagates a
copy or reference of the updated buffer to all subscriber cards
registered for that buffer.

This module provides helpers to create awareness cards, manage
subscriptions to awareness buffers, and update awareness buffers with
automatic propagation.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from .abdb import ABMemory
from .models import Buffer
from .subselves import propagate_subscriptions


def create_awareness_card(
    memory: ABMemory,
    name: str,
    buffers: Iterable[Buffer],
    owner_self: Optional[str] = None,
) -> int:
    """Create a new awareness card.

    Args:
        memory: The ``ABMemory`` instance.
        name: A logical name for the awareness card; stored in a
            ``awareness_name`` header on all buffers.
        buffers: An iterable of ``Buffer`` objects to attach to the card.
        owner_self: Optional owner identifier.

    Returns:
        The ID of the new awareness card.
    """
    # Ensure the name is included in headers for each buffer
    bufs: List[Buffer] = []
    for buf in buffers:
        headers = dict(buf.headers)
        headers["awareness_name"] = name
        bufs.append(Buffer(name=buf.name, headers=headers, payload=buf.payload, exe=buf.exe))
    card = memory.store_card(label="awareness", buffers=bufs, owner_self=owner_self)
    return card.id  # type: ignore


def subscribe_to_awareness(
    memory: ABMemory,
    awareness_card_id: int,
    subscriber_card_id: int,
    buffer_names: Iterable[str],
    config: Optional[dict] = None,
) -> List[int]:
    """Subscribe a card to one or more buffers on an awareness card.

    A subscription is created for each buffer name provided.  Returns
    the IDs of the new subscription records.
    """
    sub_ids: List[int] = []
    for bname in buffer_names:
        sub_id = memory.create_subscription(
            subscriber_card_id=subscriber_card_id,
            source_card_id=awareness_card_id,
            buffer_name=bname,
            config=config,
        )
        sub_ids.append(sub_id)
    return sub_ids


def update_awareness_buffer(
    memory: ABMemory,
    awareness_card_id: int,
    buffer_name: str,
    new_buffer: Buffer,
) -> None:
    """Update a buffer on an awareness card and propagate to subscribers.

    The buffer is replaced on the awareness card and then
    ``propagate_subscriptions`` is called to copy the update to
    subscribers.
    """
    card = memory.get_card(awareness_card_id)
    if card.label != "awareness":
        raise ValueError(f"Card {awareness_card_id} is not an awareness card (label={card.label})")
    # Replace or append buffer
    new_buffers: List[Buffer] = []
    replaced = False
    for buf in card.buffers:
        if buf.name == buffer_name:
            # Copy headers but update payload and exe
            headers = dict(new_buffer.headers)
            headers.setdefault("awareness_name", buf.headers.get("awareness_name"))
            new_buf = Buffer(name=buffer_name, headers=headers, payload=new_buffer.payload, exe=new_buffer.exe)
            new_buffers.append(new_buf)
            replaced = True
        else:
            new_buffers.append(buf)
    if not replaced:
        # Append if missing, copy headers from new_buffer but ensure awareness_name if possible
        headers = dict(new_buffer.headers)
        headers.setdefault("awareness_name", "")
        new_buffers.append(Buffer(name=buffer_name, headers=headers, payload=new_buffer.payload, exe=new_buffer.exe))
    memory.update_card_buffers(awareness_card_id, new_buffers)
    # Propagate to subscribers
    propagate_subscriptions(memory, awareness_card_id, buffer_name)