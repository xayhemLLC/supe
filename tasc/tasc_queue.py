"""Simple Tasc queue built on top of AB memory.

This module defines the ``TascQueue`` class which provides basic
operations for creating, retrieving, listing and updating Tascs.  It
relies on the ``ABMemory`` engine from ``ab`` to persist each
Tasc as a card in the underlying moment ledger.  The queue does not
expose advanced scheduling or prioritization; it simply wraps
creation and update semantics and is intended as a starting point
for higher‑level planning and orchestration logic.
"""

from __future__ import annotations

from typing import List, Optional

from ab import ABMemory

from .tasc import Tasc
from .ab_integration import store_tasc, load_tasc
from .ab_integration import attach_buffer_to_tasc  # re-export for convenience
from ab.models import Buffer  # type: ignore


class TascQueue:
    """A minimal queue manager for Tascs using AB memory storage."""

    def __init__(self, memory: ABMemory) -> None:
        self.memory = memory

    def create_tasc(self, tasc: Tasc, owner_self: Optional[str] = None) -> int:
        """Persist a Tasc and return its card ID."""
        card_id = store_tasc(self.memory, tasc, owner_self=owner_self)
        return card_id

    def get_tasc(self, card_id: int) -> Tasc:
        """Retrieve a Tasc by its card ID."""
        return load_tasc(self.memory, card_id)

    def list_tascs(self) -> List[int]:
        """Return the card IDs of all Tascs stored in memory."""
        cards = self.memory.find_cards_by_label("tasc")
        return [c.id for c in cards]

    def update_tasc_status(self, card_id: int, new_status: str) -> None:
        """Update the ``status`` field of the specified Tasc.

        This method loads the existing Tasc, modifies its status and
        stores it back into the same card.  Existing attachments and
        other metadata are preserved.
        """
        # Load current card and Tasc
        card = self.memory.get_card(card_id)
        if card.label != "tasc":
            raise ValueError(f"Card {card_id} is not a Tasc (label={card.label})")
        current_tasc = load_tasc(self.memory, card_id)
        # Create a new Tasc with updated status and same other fields
        updated_tasc = Tasc(
            id=current_tasc.id,
            status=new_status,
            title=current_tasc.title,
            additional_notes=current_tasc.additional_notes,
            testing_instructions=current_tasc.testing_instructions,
            desired_outcome=current_tasc.desired_outcome,
            dependencies=current_tasc.dependencies,
        )
        # Encode and replace the tasc payload buffer while preserving attachments
        from .atom import decode_atom, Atom
        # Build new payload
        new_atom = updated_tasc.to_atom()
        new_payload = new_atom.encode()
        # Build new buffers list: replace tasc_payload, keep others
        new_buffers = []
        replaced = False
        for buf in card.buffers:
            if buf.name == "tasc_payload":
                new_buffers.append(Buffer(name="tasc_payload", headers={"atom_type": "tasc"}, payload=new_payload, exe=None))
                replaced = True
            else:
                new_buffers.append(buf)
        if not replaced:
            # If no tasc_payload present, treat as error
            raise ValueError(f"Card {card_id} does not contain a tasc_payload buffer")
        # Update storage
        self.memory.update_card_buffers(card_id, new_buffers)

    def attach_buffer(self, card_id: int, buffer: Buffer) -> None:
        """Attach an additional buffer to the specified Tasc."""
        attach_buffer_to_tasc(self.memory, card_id, buffer)
