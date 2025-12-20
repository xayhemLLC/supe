"""Demonstration script for the Tasc queue integrated with AB memory.

This script shows how to create and manage Tascs using the
``TascQueue`` and ``ABMemory`` classes.  It performs the following
steps:

1. Initialise an in‑memory AB store.
2. Create a ``TascQueue`` instance.
3. Construct and store a couple of Tascs.
4. List all stored Tasc IDs.
5. Load and display a Tasc.
6. Update a Tasc's status.
7. Attach an extra buffer (e.g., a note) to a Tasc.
8. Reload and display the updated Tasc and attachments.

Run this script directly with ``python drivers/demo_tasc_queue.py`` to
see the output.
"""

from __future__ import annotations

import json
import os
import sys

# Adjust sys.path so that ab_core and tasc_core can be imported when
# running this script directly from the drivers directory.  This adds
# the project root (parent of this file's directory) to the module
# search path before importing project packages.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ab import ABMemory  # type: ignore
from ab.models import Buffer  # type: ignore
from tasc.tasc import Tasc  # type: ignore
from tasc.tasc_queue import TascQueue  # type: ignore


def print_tasc(card_id: int, queue: TascQueue) -> None:
    """Helper function to print a Tasc and its attachments."""
    memory = queue.memory
    card = memory.get_card(card_id)
    tasc = queue.get_tasc(card_id)
    print(f"Card ID: {card.id}")
    print(f"Moment ID: {card.moment_id}")
    print("Tasc:")
    print(json.dumps(
        {
            "id": tasc.id,
            "status": tasc.status,
            "title": tasc.title,
            "additional_notes": tasc.additional_notes,
            "testing_instructions": tasc.testing_instructions,
            "desired_outcome": tasc.desired_outcome,
            "dependencies": tasc.dependencies,
        },
        indent=2,
    ))
    print("Attachments:")
    for buf in card.buffers:
        if buf.name != "tasc_payload":
            print(f"  - {buf.name} (len={len(buf.payload)}) headers={buf.headers}")
    print()


def main() -> None:
    # Adjust sys.path so that ab_core and tasc_core can be imported when
    # running this script directly from the drivers directory.  This adds
    # the project root (parent of this file's directory) to the module
    # search path.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    # Initialise a new memory store (this uses ab_memory.sqlite in the current directory)
    memory = ABMemory(db_path=":memory:")
    # Create a queue
    queue = TascQueue(memory)
    # Create two Tascs
    t1 = Tasc(
        id="DEMO-1",
        status="draft",
        title="Implement AB-Tasc integration",
        additional_notes="Store Tascs as cards in AB.",
        testing_instructions="Run demo script.",
        desired_outcome="Tasc stored in AB and retrievable.",
        dependencies=[],
    )
    t2 = Tasc(
        id="DEMO-2",
        status="draft",
        title="Add attachments",
        additional_notes="Attach a spec document.",
        testing_instructions="Upload file and check retrieval.",
        desired_outcome="Attachment stored.",
        dependencies=["DEMO-1"],
    )
    cid1 = queue.create_tasc(t1)
    cid2 = queue.create_tasc(t2)
    print("Created Tascs with card IDs:", cid1, cid2)
    # List
    print("All Tasc card IDs:", queue.list_tascs())
    # Display first Tasc
    print("\nInitial state of first Tasc:")
    print_tasc(cid1, queue)
    # Update status
    queue.update_tasc_status(cid1, "in_progress")
    print("After updating status of first Tasc:")
    print_tasc(cid1, queue)
    # Attach a note to second Tasc
    note = Buffer(name="note", headers={"description": "Initial spec"}, payload=b"This is a sample spec.", exe=None)
    queue.attach_buffer(cid2, note)
    print("After attaching a buffer to second Tasc:")
    print_tasc(cid2, queue)


if __name__ == "__main__":
    main()