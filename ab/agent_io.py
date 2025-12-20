"""Agent input/output envelope construction for AB/Tasc agents.

This module provides helper functions to assemble a minimal but
sufficient context packet for a stateless agent to execute a Tasc.
The envelope gathers information from the AB memory and
encapsulates it in a dictionary that can be serialised and sent
to an agent runtime. By limiting the input to only what matters
for the task, we avoid leaking unnecessary memory and maintain
discipline around the memory boundary.

An agent envelope typically contains:

* ``tasc_id``: The identifier of the Tasc card to work on.
* ``spec``: The specification text from the associated spec card.
* ``plan``: The plan text from the associated plan card, if any.
* ``known_pitfalls``: A list of pitfalls if provided in the spec.
* ``definition_of_done``: A list of done criteria, if provided.
* ``definition_of_success``: The desired outcome text from the
  original Tasc (if encoded as a buffer on the Tasc card).
* Additional context from evidence, decision or conversation
  cards may be added in future versions.

The ``build_agent_input`` function looks up the Tasc card by ID,
follows its connections to find associated spec and plan cards, and
extracts the relevant buffers. If no spec or plan card exists,
the corresponding fields are omitted. All payloads are decoded
from bytes to strings.

This module may be extended to support rich context assembly,
including merging multiple specifications or plans, or including
summaries from recall.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .abdb import ABMemory


def _decode_buffer_payload(buf_row: Any) -> str:
    """Decode a buffer's payload into a string.

    If the payload is binary but cannot be decoded as UTF-8, this
    function will return a placeholder string indicating binary
    content. Otherwise, it decodes as UTF-8.
    """
    try:
        return buf_row["payload"].decode("utf-8")  # type: ignore
    except Exception:
        return "<binary>"


def build_agent_input(memory: ABMemory, tasc_card_id: int) -> Dict[str, Any]:
    """Assemble a context packet for an agent to execute a Tasc.

    Args:
        memory: The AB storage manager.
        tasc_card_id: ID of the Tasc card for which to build an
            envelope.

    Returns:
        A dictionary containing the agent input fields. Missing
        optional fields will be omitted to keep the packet concise.
    """
    env: Dict[str, Any] = {"tasc_id": tasc_card_id}
    # Fetch tasc card buffers to extract desired outcome or other
    # metadata (e.g. from additional_notes or desired_outcome)
    tasc_card = memory.get_card(tasc_card_id)
    # Attempt to parse tasc buffers for specification fields
    for buf in tasc_card.buffers:
        if buf.name == "desired_outcome":
            env["definition_of_success"] = buf.payload.decode("utf-8")
        # Additional notes could store pitfalls or criteria
        if buf.name == "additional_notes":
            try:
                notes = json.loads(buf.payload.decode("utf-8"))
                if isinstance(notes, dict):
                    env.update(notes)
            except Exception:
                env["additional_notes"] = buf.payload.decode("utf-8")
    # Identify spec and plan cards via connections
    # spec_for relation: spec card → tasc card
    spec_id: Optional[int] = None
    plan_id: Optional[int] = None
    conns = memory.list_connections(tasc_card_id)
    for conn in conns:
        # connection relation names: 'spec_for' means source->tasc, but list_connections returns both directions
        # We need to find connections where target_id == tasc_card_id and relation ends with '_for'
        if conn["relation"] == "spec_for" and conn["target_card_id"] == tasc_card_id:
            spec_id = conn["source_card_id"]
        if conn["relation"] == "plan_for" and conn["target_card_id"] == tasc_card_id:
            plan_id = conn["source_card_id"]
    # Extract spec and pitfalls/DoD
    if spec_id is not None:
        spec_card = memory.get_card(spec_id)
        for buf in spec_card.buffers:
            if buf.name == "spec_text":
                env["spec"] = buf.payload.decode("utf-8")
            elif buf.name == "known_pitfalls":
                try:
                    env["known_pitfalls"] = json.loads(buf.payload.decode("utf-8"))
                except Exception:
                    env["known_pitfalls"] = []
            elif buf.name == "definition_of_done":
                try:
                    env["definition_of_done"] = json.loads(buf.payload.decode("utf-8"))
                except Exception:
                    env["definition_of_done"] = []
    if plan_id is not None:
        plan_card = memory.get_card(plan_id)
        for buf in plan_card.buffers:
            if buf.name == "plan_text":
                env["plan"] = buf.payload.decode("utf-8")
            elif buf.name == "plan_items":
                try:
                    env["plan_items"] = json.loads(buf.payload.decode("utf-8"))
                except Exception:
                    env["plan_items"] = []
    return env