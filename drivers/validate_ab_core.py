"""Standalone validation script for the AB memory engine and Tasc integration.

This script exercises the ``ab`` and ``tasc.ab_integration``
modules by storing and retrieving a Tasc object within the AB memory
system. It runs independently of any external test framework and
prints out results or raises assertions on failure.
"""

import os
import sys

# Ensure the parent directory is on the module search path so that
# ab_core and tasc_core can be imported when running this script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ab import ABMemory
from tasc.tasc import Tasc
from tasc.ab_integration import store_tasc, load_tasc


def main() -> None:
    # Use a temporary database file for tests
    db_path = "ab_test.sqlite"
    if os.path.exists(db_path):
        os.remove(db_path)
    # Create memory and a sample tasc
    memory = ABMemory(db_path=db_path)
    original = Tasc(
        id="DEMO-AB-001",
        status="queued",
        title="Store and retrieve via AB",
        additional_notes="Testing AB storage of a Tasc.",
        testing_instructions="Run this script to verify.",
        desired_outcome="Tasc round-trips through AB memory without loss.",
        dependencies=[],
    )
    card_id = store_tasc(memory, original, owner_self="tester")
    memory.close()
    # Reopen and load
    memory2 = ABMemory(db_path=db_path)
    recovered = load_tasc(memory2, card_id)
    memory2.close()
    assert recovered == original, f"Recovered Tasc differs from original: {recovered} vs {original}"
    print("Tasc storage and retrieval via AB memory passed.")
    # Clean up test file
    if os.path.exists(db_path):
        os.remove(db_path)


if __name__ == "__main__":
    main()