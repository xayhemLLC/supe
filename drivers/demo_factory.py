"""Demonstration of the Factory v0 pipeline.

This script exercises the memory checkpoint protocol and card
schemas defined in ``ab.card_utils`` and ``ab.checkpoint``.
It shows how a Tasc can be created, planned, executed and validated
while persisting all key artefacts in AB memory. It also
demonstrates building an agent input envelope and inspecting
connections between cards.

To run this demo, execute:

    python3 drivers/demo_factory.py

The script will print out the contents of the created cards and the
agent envelope.
"""

from __future__ import annotations

import os
import tempfile
from pprint import pprint

import os
import sys

# Ensure the project root is on the Python path so ``ab`` can be imported
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ab.abdb import ABMemory
from ab.checkpoint import (
    checkpoint_after_planning,
    checkpoint_after_decision,
    checkpoint_after_evidence,
    checkpoint_after_bug,
    checkpoint_after_conversation,
)
from ab.agent_io import build_agent_input
from tasc.tasc import Tasc
from tasc.ab_integration import store_tasc


def main() -> None:
    # Create a temporary database so the demo does not persist state across runs
    tmpdb = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite")
    tmpdb.close()
    memory = ABMemory(tmpdb.name)
    try:
        # 1. Create a sample Tasc and store it
        tasc = Tasc(
            id="DEMO-TASC-001",
            status="draft",
            title="Implement dwell time tracking",
            additional_notes="{}",
            testing_instructions="Open the feed and scroll for 5 seconds; verify dwell events are emitted.",
            desired_outcome="Dwell time is tracked per feed item and stored.",
            dependencies=[],
        )
        tasc_card_id = store_tasc(memory, tasc, owner_self="planner")
        print(f"Created Tasc card ID: {tasc_card_id}\n")
        # 2. Planner checkpoint: spec + plan
        spec_text = "Measure how long each feed item is visible on screen."
        plan_text = "Instrument visibility events and heartbeat every 250ms."
        known_pitfalls = [
            "Scroll jitter causes false positives",
            "Backgrounding pauses timers",
        ]
        definition_of_done = [
            "Unit tests pass",
            "Playwright test records dwell",
            "Evidence attached",
        ]
        plan_items = [
            "Add onVisibility handler to feed items",
            "Start timer on visible",
            "Pause timer on hidden",
            "Record dwell events",
        ]
        cp = checkpoint_after_planning(
            memory,
            tasc_card_id,
            spec=spec_text,
            plan=plan_text,
            known_pitfalls=known_pitfalls,
            definition_of_done=definition_of_done,
            plan_items=plan_items,
            owner_self="planner",
        )
        print("After planning checkpoint:\nSpec card ID:", cp["spec_id"], "Plan card ID:", cp["plan_id"], "\n")
        # 3. Build agent input envelope
        envelope = build_agent_input(memory, tasc_card_id)
        print("Agent input envelope:\n")
        pprint(envelope)
        print()
        # 4. Decision checkpoint (execution)
        decision_text = "print Dwell tracking instrumentation complete"
        decision_id = checkpoint_after_decision(
            memory, tasc_card_id, decision=decision_text, reasoning="Completed implementation", owner_self="coder"
        )
        print(f"Recorded decision card ID: {decision_id}\n")
        # 5. Evidence checkpoint
        evidence_data = b"test report contents"
        evidence_id = checkpoint_after_evidence(
            memory,
            tasc_card_id,
            evidence_data=evidence_data,
            content_type="text/plain",
            description="Unit test report",
            owner_self="coder",
        )
        print(f"Recorded evidence card ID: {evidence_id}\n")
        # 6. Bug checkpoint (optional)
        bug_id = checkpoint_after_bug(
            memory,
            tasc_card_id,
            description="Timer continued in background",
            reproduction_steps="Put app in background and observe timer",
            fix="Pause timer on app background",
            owner_self="validator",
        )
        print(f"Recorded bug card ID: {bug_id}\n")
        # 7. Conversation checkpoint
        convo_id = checkpoint_after_conversation(
            memory,
            tasc_card_id,
            conversation="Planner: please implement dwell. Coder: done. Validator: bug found.",
            owner_self="coordinator",
        )
        print(f"Recorded conversation card ID: {convo_id}\n")
        # 8. Inspect connections
        conns = memory.list_connections(tasc_card_id)
        print("\nConnections for Tasc card:")
        for c in conns:
            print(c)
        # 9. Cleanup temp file path at the end
    finally:
        os.unlink(tmpdb.name)


if __name__ == "__main__":
    main()