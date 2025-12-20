"""Helper functions to bridge Tasc objects with the AB memory engine.

These functions encapsulate the logic for storing and retrieving Tasc
objects in the AB memory system implemented by ``ab``. A Tasc
is represented as an ATOM; we store the encoded bytes in a buffer
attached to a card with label ``"tasc"``. When retrieving, we decode
the payload back into a ``Tasc`` instance.
"""

from __future__ import annotations

from typing import Optional

from ab import ABMemory

from .atom import Atom
from .atomtypes import registry
from .tasc import Tasc
from ab.models import Buffer  # type: ignore  # Buffer is defined in ab_core


def store_tasc(
    memory: ABMemory,
    tasc: Tasc,
    owner_self: Optional[str] = None,
    moment_id: Optional[int] = None,
) -> int:
    """Store a Tasc in AB memory and return the card ID.

    Args:
        memory: The ``ABMemory`` instance to use for storage.
        tasc: The Tasc object to store.
        owner_self: Optional self identifier.
        moment_id: Optional moment id to associate the card with.

    Returns:
        The ID of the stored card.
    """
    # Encode the Tasc into an Atom and then into bytes
    atom = tasc.to_atom()
    payload_bytes = atom.encode()
    buf = Buffer(
        name="tasc_payload",
        headers={"atom_type": "tasc"},
        payload=payload_bytes,
        exe=None,
    )
    card = memory.store_card(label="tasc", buffers=[buf], owner_self=owner_self, moment_id=moment_id)
    return card.id  # type: ignore[return-value]


def load_tasc(memory: ABMemory, card_id: int) -> Tasc:
    """Load a Tasc from the given card ID.

    Args:
        memory: The ``ABMemory`` instance to load from.
        card_id: The ID of the card to load.

    Returns:
        The decoded ``Tasc`` object.

    Raises:
        ValueError: If the card does not contain a valid Tasc payload.
    """
    card = memory.get_card(card_id)
    if card.label != "tasc":
        raise ValueError(f"Card {card_id} is not a Tasc (label={card.label})")
    # Find the buffer containing the tasc payload
    tasc_buf = None
    for buf in card.buffers:
        if buf.name == "tasc_payload":
            tasc_buf = buf
            break
    if tasc_buf is None:
        raise ValueError(f"Card {card_id} does not contain a tasc_payload buffer")
    # Decode the atom
    payload = tasc_buf.payload
    # decode an Atom from the beginning of payload
    from .atom import decode_atom
    atom, offset = decode_atom(payload, 0)
    if offset != len(payload):
        # There should only be one atom in the payload
        raise ValueError(
            f"Expected single atom payload, but extra bytes found (offset {offset}, len {len(payload)})"
        )
    # Ensure it's a tasc atom
    tasc_type = registry.get_by_name("tasc")
    if atom.pindex != tasc_type.pindex:
        raise ValueError(f"Payload atom type {atom.pindex} is not 'tasc'")
    return Tasc.from_atom(atom)


def attach_buffer_to_tasc(
    memory: ABMemory,
    card_id: int,
    buffer: Buffer,
) -> None:
    """Attach an additional buffer to an existing Tasc card.

    The card must have the label "tasc".  This function retrieves
    the current buffers, appends the new buffer and updates the card
    storage.  It does not modify the Tasc payload itself.  Use this
    to store supplementary artefacts (e.g., files, logs, transcripts)
    alongside the core Tasc definition.

    Args:
        memory: The ``ABMemory`` instance used for storage.
        card_id: The ID of the card to which the buffer should be attached.
        buffer: The ``Buffer`` instance to attach.
    """
    card = memory.get_card(card_id)
    if card.label != "tasc":
        raise ValueError(f"Card {card_id} is not a Tasc (label={card.label})")
    # Append the new buffer
    new_buffers = card.buffers + [buffer]
    # Update storage
    memory.update_card_buffers(card_id, new_buffers)