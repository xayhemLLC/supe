"""Demonstration of extended AB and Tasc functionality.

This script creates a small AB memory universe with subselves,
awareness cards, tasks and demonstrates the Overlord, subscriptions
and search.  It can be run standalone and prints its operations to
stdout.  The goal is to exercise the new features implemented in
``ab`` such as subselves, lanes, awareness cards, and the
Overlord decision engine.

Usage:
    python3 drivers/demo_ab_extended.py
"""


from __future__ import annotations

import os
import sys

# Ensure the project root (parent directory) is on sys.path so that
# ``ab`` and ``tasc`` packages can be imported when this
# script is executed directly.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pprint import pprint

from ab import ABMemory
from ab.moment_ledger import group_moments_by_day
from ab.awareness import create_awareness_card, subscribe_to_awareness, update_awareness_buffer
from ab.overlord import Overlord
from ab.search import search_cards
from ab.models import Buffer
from ab.subselves import LaneManager
from tasc.tasc import Tasc
from tasc.ab_integration import store_tasc
from tasc.q_manager import QManager


def main() -> None:
    # Use an in-memory database for demonstration
    mem = ABMemory(db_path=":memory:")

    # Create planner and coder subselves
    planner_id = mem.create_self("planner", role="planner")
    coder_id = mem.create_self("coder", role="coder")
    selves = mem.list_selves()
    print("Subselves created:")
    pprint(selves)

    # Create Q card for tasks and QManager
    qman = QManager(mem)
    q_card_id = qman.create_queue(owner_self="system")
    print(f"Created Q card with ID {q_card_id}")

    # Create and store two simple Tascs
    t1 = Tasc(
        id="TASK-1",
        status="draft",
        title="First extended task",
        additional_notes="Demo task 1",
        testing_instructions="",
        desired_outcome="",
        dependencies=[],
    )
    c1 = store_tasc(mem, t1, owner_self="planner")
    print(f"Stored Tasc 1 as card {c1}")
    qman.add_to_queue(q_card_id, c1)

    t2 = Tasc(
        id="TASK-2",
        status="draft",
        title="Second extended task",
        additional_notes="Demo task 2",
        testing_instructions="",
        desired_outcome="",
        dependencies=["TASK-1"],
    )
    c2 = store_tasc(mem, t2, owner_self="coder")
    print(f"Stored Tasc 2 as card {c2}")
    qman.add_to_queue(q_card_id, c2)

    # Show Q contents
    print("Q card contents:", qman.load_queue(q_card_id))

    # Create an awareness card with a prompt buffer
    prompt_buf = Buffer(name="prompt", headers={"content_type": "text/plain"}, payload=b"Initial prompt.")
    awareness_id = create_awareness_card(mem, name="global_context", buffers=[prompt_buf], owner_self="planner")
    print(f"Created awareness card {awareness_id}")

    # Subscribe coder task card to the prompt buffer of awareness card
    sub_ids = subscribe_to_awareness(mem, awareness_id, c2, buffer_names=["prompt"])
    print(f"Subscribed Tasc 2 to awareness prompt buffer (sub IDs: {sub_ids})")

    # Update the prompt buffer; this should propagate to Tasc 2
    new_prompt = Buffer(name="prompt", headers={"content_type": "text/plain"}, payload=b"Updated global prompt.")
    update_awareness_buffer(mem, awareness_id, "prompt", new_prompt)
    # Check Tasc 2 card buffers
    tasc2_card = mem.get_card(c2)
    print("Buffers on Tasc 2 after prompt update:")
    for b in tasc2_card.buffers:
        print(f"  - {b.name}: {b.payload}")

    # Demonstrate Overlord: planner and coder propose actions
    overlord = Overlord(mem)
    overlord.add_proposal({"subself_id": planner_id, "action": "plan next steps", "priority": 3})
    overlord.add_proposal({"subself_id": coder_id, "action": "implement feature", "priority": 5})
    winner = overlord.decide()
    print("Overlord chose:", winner)

    # Use search to find cards containing the word "prompt"
    print("Searching for keyword 'prompt'")
    results = search_cards(mem, keyword="prompt")
    for card in results:
        print(f"Found card {card.id} label={card.label}")

    # Show grouping of moments by day
    groups = group_moments_by_day(mem)
    print("Moments grouped by day:")
    for day, moments in groups.items():
        print(f"  {day}: {len(moments)} moment(s)")


if __name__ == "__main__":
    main()