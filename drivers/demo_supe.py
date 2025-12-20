"""Demo for the 'supe' version of AB with hardware and actions.

This script showcases the extended cognitive cycle that incorporates
raw sensor data, master cards, awareness cards, subself proposals,
Overlord arbitration and action execution.  It demonstrates how
sensor readings are captured on a master card, fused inputs on an
awareness card, and how chosen actions are executed via the
``ab.actions`` registry.

To run this demo from the project root:

    python3 drivers/demo_supe.py

The demo is self-contained and uses ``ab_memory_supe.sqlite`` as
its database.  Feel free to remove the file after running.
"""

from __future__ import annotations

import os
from typing import Dict, Tuple

from ab.abdb import ABMemory
from ab.mind import pulse_supe
from ab.models import Buffer


def planner_branch(memory: ABMemory, awareness_card_id: int) -> Tuple[str, float]:
    """A simple planner subself for the demo.

    Reads the ``tasks`` buffer from the awareness card (if present) and
    proposes printing a summary.  The weight is proportional to the
    number of tasks.
    """
    card = memory.get_card(awareness_card_id)
    tasks_buf = next((buf for buf in card.buffers if buf.name == "tasks"), None)
    tasks = tasks_buf.payload.decode("utf-8") if tasks_buf else ""
    task_lines = [t for t in tasks.split("\n") if t.strip()]
    count = len(task_lines) or 1
    message = f"print Planner sees {count} task(s): {', '.join(task_lines)}"
    return message, float(count)


def coder_branch(memory: ABMemory, awareness_card_id: int) -> Tuple[str, float]:
    """A coder subself that proposes writing code for tasks."""
    card = memory.get_card(awareness_card_id)
    tasks_buf = next((buf for buf in card.buffers if buf.name == "tasks"), None)
    tasks = tasks_buf.payload.decode("utf-8") if tasks_buf else ""
    first_task = tasks.split("\n")[0].strip() if tasks else "nothing"
    message = f"print Coding task: {first_task}"
    # Lower weight than planner to demonstrate Overlord arbitration
    return message, 0.5


def main() -> None:
    # Remove existing database for a clean run
    db_path = "ab_memory_supe.sqlite"
    if os.path.exists(db_path):
        os.remove(db_path)
    memory = ABMemory(db_path=db_path)
    # Define raw inputs for the awareness card
    master_prompt = "Choose next action based on tasks."
    raw_inputs: Dict[str, str] = {
        "prompt": master_prompt,
        "state": "thinking",
        "tasks": "Refactor parser\nWrite documentation",
        "emotional_tone": "focused",
        "previous_output": "",
    }
    # Define subselves
    subselves = {
        "planner": planner_branch,
        "coder": coder_branch,
    }
    # Run a supe pulse
    output_card = pulse_supe(memory, raw_inputs, subselves, owner_self="supe_demo")
    # Fetch the moment associated with the output
    moment_id = output_card.moment_id
    moment = memory.get_moment(moment_id)
    print("Moment ID:", moment.id)
    print("Master input:", moment.master_input)
    print("Master output:", moment.master_output)
    print("Master card ID:", moment.master_card_id)
    print("Awareness card ID:", moment.awareness_card_id)
    # Display master card contents
    if moment.master_card_id:
        master_card = memory.get_card(moment.master_card_id)
        print("Master card buffers:")
        for buf in master_card.buffers:
            print(f"  - {buf.name}: {buf.payload.decode('utf-8')}")
    # Display awareness card contents
    if moment.awareness_card_id:
        aware = memory.get_card(moment.awareness_card_id)
        print("Awareness card buffers:")
        for buf in aware.buffers:
            print(f"  - {buf.name}: {buf.payload.decode('utf-8')}")
    # Display output card contents
    print("Output card buffers:")
    for buf in output_card.buffers:
        print(f"  - {buf.name}: {buf.payload.decode('utf-8')}")


if __name__ == "__main__":
    main()