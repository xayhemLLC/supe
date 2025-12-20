"""High-level cognitive operations for AB.

This module encapsulates the core loop of the AB kernel.  It
provides helper functions to create moments with associated
awareness cards, process subselves to generate outputs, integrate
those outputs via the Overlord, and record the results as new
cards.  It also exposes the ``pulse`` function which performs a
complete cognitive cycle: load inputs, transform them via
subselves, integrate, and record.

These helpers make use of lower-level modules like ``abdb``,
``awareness``, ``overlord`` and ``subselves`` but shield callers from
their details.
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional

from .abdb import ABMemory
from .awareness import create_awareness_card
from .hardware import get_raw_input_data
from .actions import registry as action_registry
from .models import Buffer, Moment, Card
from .overlord import Overlord
from .subselves import LaneManager
from tasc.atom import Atom  # type: ignore
from tasc.atomtypes import registry  # type: ignore
from tasc.ulist import UList  # type: ignore


def create_moment_with_inputs(
    memory: ABMemory,
    master_input: str,
    raw_inputs: Dict[str, str],
    owner_self: Optional[str] = None,
) -> Moment:
    """Create a new moment with an awareness card capturing raw inputs.

    Args:
        memory: The AB memory instance.
        master_input: The high-level prompt or context initiating this moment.
        raw_inputs: A dictionary of input fields to fuse into the
            awareness card.  Typical keys include ``prompt``, ``state``,
            ``files``, ``errors``, ``tasks``, ``emotional_tone`` and
            ``previous_output``.  The values should be strings.
        owner_self: Optional identity of the agent initiating the moment.

    Returns:
        The created ``Moment`` instance.  The moment's
        ``master_input`` and ``awareness_card_id`` fields are populated.
    """
    # Build buffers for the awareness card from raw inputs
    buffers: List[Buffer] = []
    for key, val in raw_inputs.items():
        buf = Buffer(
            name=key,
            headers={"content_type": "text/plain"},
            payload=val.encode("utf-8"),
            exe=None,
        )
        buffers.append(buf)
    # Create awareness card
    awareness_id = create_awareness_card(memory, name="moment_awareness", buffers=buffers, owner_self=owner_self)
    # Create moment with master_input and awareness_card_id
    moment = memory.create_moment(master_input=master_input, awareness_card_id=awareness_id)
    return moment


def record_master_output(
    memory: ABMemory,
    moment_id: int,
    output: str,
    buffers: Optional[List[Buffer]] = None,
    owner_self: Optional[str] = None,
) -> int:
    """Record the master output of a moment and persist as a card.

    This helper updates the moment's ``master_output`` field and
    creates a new card labelled ``"output"`` that stores the master
    output and any additional buffers produced by the cognitive
    cycle.

    Args:
        memory: The AB memory instance.
        moment_id: The ID of the moment whose output is being
            recorded.
        output: The text of the master output.
        buffers: Optional extra buffers to include on the output card.
        owner_self: Optional owner identity for the output card.

    Returns:
        The ID of the new output card.
    """
    # Update the moment's master output
    memory.update_moment_fields(moment_id, master_output=output)
    # Prepare buffers: the master output itself becomes a buffer
    out_buffers = []
    out_buffers.append(Buffer(name="master_output", headers={"content_type": "text/plain"}, payload=output.encode("utf-8"), exe=None))
    if buffers:
        out_buffers.extend(buffers)
    card = memory.store_card(label="output", buffers=out_buffers, owner_self=owner_self, moment_id=moment_id)
    return card.id  # type: ignore


def pulse(
    memory: ABMemory,
    master_input: str,
    raw_inputs: Dict[str, str],
    subselves: Dict[str, callable],
    owner_self: Optional[str] = None,
) -> Card:
    """Execute a full cognitive pulse: input, transform, emit, integrate, record.

    This function embodies the ``LOAD → TRANSFORM → EMIT → INTEGRATE → RECORD``
    protocol described in the AB kernel.  It performs the following steps:

    1. ``LOAD``: Create a moment with awareness card capturing ``raw_inputs``
       and register the ``master_input``.
    2. ``TRANSFORM``: For each subself, call its branch function with
       the awareness card ID to produce an output and a weight.  The
       branch function should return a tuple ``(text_output, weight)``.
    3. ``EMIT``: Collect the weighted outputs from all subselves.
    4. ``INTEGRATE``: Use the Overlord to select a single output based
       on the weights (higher weight wins).  Persist a decision card
       recording the choice.
    5. ``RECORD``: Update the moment's ``master_output`` and store an
       output card with the final output.

    Args:
        memory: The AB memory instance.
        master_input: The high-level prompt or question driving this
            cognitive cycle.
        raw_inputs: A dictionary of raw inputs for the awareness card.
        subselves: A mapping from subself name to a callable.  Each
            callable takes ``(memory, awareness_card_id)`` and returns
            ``(output_str, weight)``.
        owner_self: Optional owner identity for created cards.

    Returns:
        The ``Card`` object representing the stored master output.
    """
    # 1. Load: create moment with awareness card
    moment = create_moment_with_inputs(memory, master_input, raw_inputs, owner_self=owner_self)
    awareness_card_id = moment.awareness_card_id
    assert awareness_card_id is not None
    # 2. Transform: call each subself's branch on the awareness card
    proposals: List[dict] = []
    for name, branch in subselves.items():
        # Each branch returns (text, weight)
        out, weight = branch(memory, awareness_card_id)
        proposals.append({"subself_id": name, "action": out, "priority": weight})
    # 3. Emit: proposals list is ready
    # 4. Integrate: run overlord arbitration
    overlord = Overlord(memory)
    for p in proposals:
        overlord.add_proposal(p)
    winner = overlord.decide()
    if winner is None:
        # No proposals; set empty output
        chosen = ""
    else:
        chosen = winner["action"]
    # 5. Record: update moment and store output card
    out_card_id = record_master_output(memory, moment.id, chosen, buffers=None, owner_self=owner_self)
    # Return the card object for convenience
    return memory.get_card(out_card_id)


# ---------------------------------------------------------------------------
# Extended pulse for the "supe" version
# ---------------------------------------------------------------------------

def create_master_card(
    memory: ABMemory,
    sensor_data: Dict[str, str],
    owner_self: Optional[str] = None,
    moment_id: Optional[int] = None,
) -> int:
    """Create a master card containing raw sensor and state data.

    This helper constructs a card labeled ``"master"`` with a buffer
    for each entry in ``sensor_data``.  The payloads are encoded
    as UTF-8 bytes.  The card is associated with the provided
    ``moment_id`` if given; otherwise a new moment will be created.

    Args:
        memory: The AB memory instance.
        sensor_data: A mapping of sensor names to their string
            values.
        owner_self: Optional owner identity for the card.
        moment_id: Optionally associate the master card with an
            existing moment.

    Returns:
        The ID of the stored master card.
    """
    buffers: List[Buffer] = []
    for key, val in sensor_data.items():
        buf = Buffer(
            name=key,
            headers={"content_type": "text/plain"},
            payload=val.encode("utf-8"),
            exe=None,
        )
        buffers.append(buf)
    card = memory.store_card(label="master", buffers=buffers, owner_self=owner_self, moment_id=moment_id)
    return card.id  # type: ignore


def pulse_supe(
    memory: ABMemory,
    raw_inputs: Dict[str, str],
    subselves: Dict[str, callable],
    owner_self: Optional[str] = None,
) -> Card:
    """Execute an extended cognitive pulse with hardware and action execution.

    This variant of ``pulse`` adds the following steps:

    1. Read raw sensor and state data via ``get_raw_input_data``.
    2. Create a master card from the sensor data and associate it with the new moment.
    3. Create a moment with awareness card capturing ``raw_inputs`` and store the master card ID.
    4. Run subselves to produce proposals (action strings with weights).
    5. Use the Overlord to choose one proposal.
    6. Record the master output and persist it.
    7. Parse and execute the selected action via the global action registry.

    Args:
        memory: The AB memory instance.
        raw_inputs: A mapping of input fields for the awareness card.
        subselves: A mapping from subself name to a callable.  Each
            callable takes ``(memory, awareness_card_id)`` and returns
            ``(output_str, weight)``.
        owner_self: Optional owner identity for created cards.

    Returns:
        The ``Card`` object representing the stored master output.
    """
    # 1. Gather raw sensor data
    sensor_data = get_raw_input_data(memory)
    # 2. Create a master card and a moment; store master_card_id on moment
    # First create a moment without awareness to get an ID for the master card
    tmp_moment = memory.create_moment(master_input=None, master_output=None)
    # Create master card associated with this moment
    master_card_id = create_master_card(memory, sensor_data, owner_self=owner_self, moment_id=tmp_moment.id)
    # Update the moment with master_card_id and register the master input (we
    # synthesize a master input by concatenating some sensor values and raw_inputs)
    # Synthesise master_input as prompt plus top-level sensor summary
    master_input_parts: List[str] = []
    if "prompt" in raw_inputs:
        master_input_parts.append(raw_inputs["prompt"])
    # Include previous_output and threads_of_thought to provide context
    if sensor_data.get("previous_output"):
        master_input_parts.append(sensor_data["previous_output"])
    if sensor_data.get("threads_of_thought"):
        master_input_parts.append(sensor_data["threads_of_thought"])
    master_input = " | ".join(master_input_parts) if master_input_parts else ""
    memory.update_moment_fields(tmp_moment.id, master_input=master_input, master_card_id=master_card_id)
    # 3. Create awareness card and attach it to the existing moment
    # Build buffers for awareness from raw_inputs
    awareness_buffers: List[Buffer] = []
    for key, val in raw_inputs.items():
        buf = Buffer(
            name=key,
            headers={"content_type": "text/plain"},
            payload=val.encode("utf-8"),
            exe=None,
        )
        awareness_buffers.append(buf)
    awareness_card_id = create_awareness_card(memory, name="moment_awareness", buffers=awareness_buffers, owner_self=owner_self)
    # Update the moment with the awareness card ID
    memory.update_moment_fields(tmp_moment.id, awareness_card_id=awareness_card_id)
    # 4. Run subselves to produce proposals
    proposals: List[dict] = []
    for name, branch in subselves.items():
        out, weight = branch(memory, awareness_card_id)
        proposals.append({"subself_id": name, "action": out, "priority": weight})
    # 5. Integrate via the Overlord
    overlord = Overlord(memory)
    for p in proposals:
        overlord.add_proposal(p)
    winner = overlord.decide()
    chosen = winner["action"] if winner else ""
    # 6. Record master output on tmp_moment and store output card
    output_card_id = record_master_output(memory, tmp_moment.id, chosen, buffers=None, owner_self=owner_self)
    output_card = memory.get_card(output_card_id)
    # 7. Execute selected action
    action_registry.execute(memory, chosen, owner_self)
    return output_card