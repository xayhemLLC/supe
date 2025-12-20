"""Manager for the global task queue (Q) stored as a card in AB memory.

This module introduces the concept of a Q card: a card labelled
``"q"`` whose primary buffer is a ulist of references to Tasc cards.
Each element in the ulist is a ``ref`` atom containing the string
identifier of a Tasc card.  The Q card acts as a central queue of
action items.  Functions are provided to create a queue card,
inspect its contents, and modify the order of tasks.
"""

from __future__ import annotations

from typing import List, Optional

from ab import ABMemory
from ab.models import Buffer  # type: ignore

from .atom import Atom, decode_atom
from .atomtypes import registry
from .uobj import UObject
from .ulist import UList


class QManager:
    """Manage the Q card (ulist of Tasc references) in AB memory."""

    def __init__(self, memory: ABMemory) -> None:
        self.memory = memory

    def create_queue(self, owner_self: Optional[str] = None) -> int:
        """Create a new empty Q card and return its card ID."""
        # Empty ulist
        empty_ulist = UList(elements=[])
        payload = empty_ulist.encode()
        buf = Buffer(name="q_list", headers={"atom_type": "ulist"}, payload=payload, exe=None)
        card = self.memory.store_card(label="q", buffers=[buf], owner_self=owner_self)
        return card.id  # type: ignore

    def load_queue(self, q_card_id: int) -> List[int]:
        """Return a list of Tasc card IDs stored in the Q.

        Args:
            q_card_id: The card ID of the queue card.

        Returns:
            A list of integers representing card IDs of Tascs in the queue.
        """
        card = self.memory.get_card(q_card_id)
        if card.label != "q":
            raise ValueError(f"Card {q_card_id} is not a Q card (label={card.label})")
        # Find q_list buffer
        q_buf = None
        for buf in card.buffers:
            if buf.name == "q_list":
                q_buf = buf
                break
        if q_buf is None:
            raise ValueError(f"Q card {q_card_id} does not contain a q_list buffer")
        # Decode ulist of ref atoms
        ulist, offset = UList.decode(q_buf.payload, 0)
        # Convert refs to ints
        ref_type = registry.get_by_name("ref")
        card_ids: List[int] = []
        for atom in ulist.elements:
            # Each element is an Atom representing a ref; decode string and cast to int
            # However, the Atom stored in UList is the Atom directly, not encoded further.
            # The Atom payload is stored as [pindex][len][payload]. decode_value() gives the string
            val = atom.decode_value()
            card_ids.append(int(val))
        return card_ids

    def _store_ulist(self, q_card_id: int, ulist: UList) -> None:
        """Helper to store a new ulist payload into the Q card."""
        payload = ulist.encode()
        new_buf = Buffer(name="q_list", headers={"atom_type": "ulist"}, payload=payload, exe=None)
        card = self.memory.get_card(q_card_id)
        # Replace q_list buffer, keep others (unlikely any others)
        new_buffers = []
        replaced = False
        for buf in card.buffers:
            if buf.name == "q_list":
                new_buffers.append(new_buf)
                replaced = True
            else:
                new_buffers.append(buf)
        if not replaced:
            new_buffers.append(new_buf)
        self.memory.update_card_buffers(q_card_id, new_buffers)

    def add_to_queue(self, q_card_id: int, tasc_card_id: int) -> None:
        """Append a Tasc card ID to the Q."""
        ids = self.load_queue(q_card_id)
        ids.append(tasc_card_id)
        # Convert to UList of ref atoms
        ref_type = registry.get_by_name("ref")
        atoms = [Atom.from_value(ref_type, str(i)) for i in ids]
        ulist = UList(elements=atoms)
        self._store_ulist(q_card_id, ulist)

    def remove_from_queue(self, q_card_id: int, tasc_card_id: int) -> None:
        """Remove a Tasc card ID from the Q."""
        ids = self.load_queue(q_card_id)
        if tasc_card_id in ids:
            ids.remove(tasc_card_id)
            ref_type = registry.get_by_name("ref")
            atoms = [Atom.from_value(ref_type, str(i)) for i in ids]
            ulist = UList(elements=atoms)
            self._store_ulist(q_card_id, ulist)

    def reorder_queue(self, q_card_id: int, new_order: List[int]) -> None:
        """Reorder the Q according to the provided list of card IDs."""
        # Verify that new_order contains same elements as current
        current = self.load_queue(q_card_id)
        if sorted(current) != sorted(new_order):
            raise ValueError("new_order must contain the same task IDs as the current queue")
        ref_type = registry.get_by_name("ref")
        atoms = [Atom.from_value(ref_type, str(i)) for i in new_order]
        ulist = UList(elements=atoms)
        self._store_ulist(q_card_id, ulist)