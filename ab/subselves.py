"""Subself management and lane operations for AB.

This module defines utilities for creating and managing subselves
(autonomous cognitive agents) within the AB memory space. Each
subself is recorded in the ``selves`` table of the database and has
its own lane card where it can store buffers or references to
cards it creates.  Subselves can also subscribe to buffers on
other cards to receive updates automatically when the source
buffers change.

The functions here build on the underlying ``ABMemory`` methods
for creating selves and managing subscriptions.  They provide a
higher-level API for lane operations and subscription propagation.
"""

from __future__ import annotations

from typing import List, Optional

from .abdb import ABMemory
from .models import Buffer, Card
from tasc.atom import Atom  # type: ignore
from tasc.atomtypes import registry  # type: ignore
from tasc.ulist import UList  # type: ignore


class LaneManager:
    """Manage a subself's lane as a ulist of card references.

    Each subself has a lane card (label ``"lane"``). The lane card
    contains a buffer named ``"lane_list"`` whose payload is a
    ``UList`` of ``ref`` atoms.  Each element of the list is a string
    containing the ID of a card created or owned by the subself.

    The methods here allow callers to fetch the lane, add a card to
    it, remove a card, and reorder it.  The implementation mirrors
    ``tasc.q_manager.QManager`` for consistency.
    """

    def __init__(self, memory: ABMemory) -> None:
        self.memory = memory

    def _get_lane_card(self, lane_card_id: int) -> Card:
        card = self.memory.get_card(lane_card_id)
        if card.label != "lane":
            raise ValueError(f"Card {lane_card_id} is not a lane card (label={card.label})")
        return card

    def load_lane(self, lane_card_id: int) -> List[int]:
        """Return a list of card IDs stored in the lane."""
        card = self._get_lane_card(lane_card_id)
        # Find buffer
        buf = None
        for b in card.buffers:
            if b.name == "lane_list":
                buf = b
                break
        if buf is None:
            return []
        ulist, _ = UList.decode(buf.payload, 0)
        ids: List[int] = []
        for atom in ulist.elements:
            val = atom.decode_value()
            ids.append(int(val))
        return ids

    def _store_lane(self, lane_card_id: int, ids: List[int]) -> None:
        ref_type = registry.get_by_name("ref")
        atoms = [Atom.from_value(ref_type, str(i)) for i in ids]
        ulist = UList(elements=atoms)
        payload = ulist.encode()
        new_buf = Buffer(name="lane_list", headers={"atom_type": "ulist"}, payload=payload, exe=None)
        card = self._get_lane_card(lane_card_id)
        # Replace existing buffer or append
        new_buffers: List[Buffer] = []
        replaced = False
        for b in card.buffers:
            if b.name == "lane_list":
                new_buffers.append(new_buf)
                replaced = True
            else:
                new_buffers.append(b)
        if not replaced:
            new_buffers.append(new_buf)
        self.memory.update_card_buffers(lane_card_id, new_buffers)

    def add_to_lane(self, lane_card_id: int, card_id: int) -> None:
        ids = self.load_lane(lane_card_id)
        ids.append(card_id)
        self._store_lane(lane_card_id, ids)

    def remove_from_lane(self, lane_card_id: int, card_id: int) -> None:
        ids = self.load_lane(lane_card_id)
        if card_id in ids:
            ids.remove(card_id)
            self._store_lane(lane_card_id, ids)

    def reorder_lane(self, lane_card_id: int, new_order: List[int]) -> None:
        current = self.load_lane(lane_card_id)
        if sorted(current) != sorted(new_order):
            raise ValueError("new_order must contain the same card IDs as the current lane")
        self._store_lane(lane_card_id, new_order)


def propagate_subscriptions(memory: ABMemory, source_card_id: int, buffer_name: str) -> None:
    """Propagate a buffer update to all subscribed cards.

    When a buffer on ``source_card_id`` with the name ``buffer_name`` is
    updated, this function should be called to copy the buffer
    contents to all subscriber cards that have a subscription to
    that source buffer.  The copy is stored as a buffer with the same
    name on the subscriber card (headers and exe are copied as well).

    Note: if the subscriber already has a buffer with that name, it
    will be replaced.  Propagation does not cascade; that is, updates
    triggered by propagation do not in turn trigger further
    propagation.
    """
    # Get the source card and find the buffer to propagate
    source = memory.get_card(source_card_id)
    src_buf = None
    for b in source.buffers:
        if b.name == buffer_name:
            src_buf = b
            break
    if src_buf is None:
        raise ValueError(f"Buffer '{buffer_name}' not found on card {source_card_id}")
    # Find subscriptions
    subs = memory.list_subscriptions(source_card_id=source_card_id)
    for sub in subs:
        if sub["buffer_name"] != buffer_name:
            continue
        subscriber_id = sub["subscriber_card_id"]
        # Copy buffer
        new_buf = Buffer(
            name=buffer_name,
            headers=dict(src_buf.headers),
            payload=bytes(src_buf.payload),
            exe=src_buf.exe,
        )
        # Replace or append buffer on subscriber card
        card = memory.get_card(subscriber_id)
        new_buffers: List[Buffer] = []
        replaced = False
        for b in card.buffers:
            if b.name == buffer_name:
                new_buffers.append(new_buf)
                replaced = True
            else:
                new_buffers.append(b)
        if not replaced:
            new_buffers.append(new_buf)
        memory.update_card_buffers(subscriber_id, new_buffers)