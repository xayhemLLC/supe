"""Demo for full AB kernel functionality with Tasc integration.

This script exercises the extended AB system by creating a moment
with an awareness card, running a pulse through multiple subselves,
recording the master output, and performing a recall operation.  It
shows how master inputs and outputs are stored on moments and cards,
how awareness cards fuse raw inputs, how proposals from subselves are
integrated by the Overlord, and how recall traverses the memory web.

To run this demo from the project root:

    python3 drivers/demo_ab_kernel.py

This demo is self-contained and uses the in-memory SQLite database
``ab_memory.sqlite`` in the current working directory.  Feel free to
remove the file after running.
"""

from __future__ import annotations

import os
from typing import Dict, Tuple

from ab.abdb import ABMemory
from ab.mind import pulse, create_moment_with_inputs
from ab.recall import recall_cards
from ab.search import search_cards
from ab.models import Buffer


def planner_branch(memory: ABMemory, awareness_card_id: int) -> Tuple[str, float]:
    """Example planner subself: summarises tasks from the awareness card.

    It reads the ``tasks`` buffer (if present) and proposes a plan with a
    weight proportional to the number of tasks.
    """
    card = memory.get_card(awareness_card_id)
    tasks = ""
    for buf in card.buffers:
        if buf.name == "tasks":
            tasks = buf.payload.decode("utf-8")
            break
    # Count tasks by line
    count = len([t for t in tasks.split("\n") if t.strip()]) or 1
    plan = f"Plan generated for {count} tasks"
    weight = float(count)
    return plan, weight


def coder_branch(memory: ABMemory, awareness_card_id: int) -> Tuple[str, float]:
    """Example coder subself: returns a code stub and a fixed weight."""
    return "def example_function():\n    pass", 0.5


def main() -> None:
    # Remove existing database for a clean run
    if os.path.exists("ab_memory.sqlite"):
        os.remove("ab_memory.sqlite")
    memory = ABMemory()
    # Define master input and raw inputs
    master_input = "What should I work on?"
    raw_inputs: Dict[str, str] = {
        "prompt": master_input,
        "state": "idle",
        "files": "",
        "errors": "",
        "tasks": "Write report\nRefactor code",
        "emotional_tone": "curious",
        "previous_output": "None",
    }
    # Define subselves
    subselves = {
        "planner": planner_branch,
        "coder": coder_branch,
    }
    # Run a pulse
    output_card = pulse(memory, master_input, raw_inputs, subselves, owner_self="demo_user")
    # Fetch the moment
    moment_id = output_card.moment_id
    moment = memory.get_moment(moment_id)
    print("Moment ID:", moment.id)
    print("Master input:", moment.master_input)
    print("Master output:", moment.master_output)
    print("Awareness card ID:", moment.awareness_card_id)
    # Show awareness card contents
    if moment.awareness_card_id:
        aware = memory.get_card(moment.awareness_card_id)
        print("Awareness card buffers:")
        for buf in aware.buffers:
            print(f"  - {buf.name}: {buf.payload.decode('utf-8')}")
    # Show output card contents
    print("Output card buffers:")
    for buf in output_card.buffers:
        print(f"  - {buf.name}: {buf.payload.decode('utf-8')}")
    # Perform recall using keyword 'Plan'
    results = recall_cards(memory, query="plan", start_card_id=output_card.id, top_k=3)
    print("Recall results for 'plan':")
    for card, score in results:
        print(f"  Card {card.id} (label={card.label}) score={score}")
    # Search cards for keyword 'report'
    search_results = search_cards(memory, keyword="report")
    print("Search results for 'report':")
    for c in search_results:
        print(f"  Card {c.id} label={c.label}")


if __name__ == "__main__":
    main()