"""Simple hardware simulation for the AB kernel.

This module provides a very rudimentary simulation of raw sensory
inputs that would be captured by a cognitive system.  In the real
system, these values would originate from sensors (e.g., camera,
microphone), internal state monitors, memory statistics, and the
agent's own thought processes.  Here we provide a deterministic
interface that produces synthetic data to demonstrate the plumbing
between hardware, master cards and awareness cards.

The ``get_raw_input_data`` function returns a dictionary of
string-valued observations keyed by sensor name.  Additional
sensors can be added as needed.  The function optionally accepts
an ``ABMemory`` instance so it can read basic statistics (e.g.,
number of moments) and previous outputs to emulate recall of
recent state.

Note: Because this is a simulation, the values are deliberately
simple.  In a production setting, you would replace these
implementations with actual hardware integrations.
"""

from __future__ import annotations

import random
from typing import Dict, Optional

from .abdb import ABMemory


def get_raw_input_data(memory: Optional[ABMemory] = None) -> Dict[str, str]:
    """Gather raw sensory and internal state data.

    Args:
        memory: Optional ``ABMemory`` instance used to derive
            statistics and recall of previous outputs.  If provided,
            the function will attempt to fetch the most recent
            moment's master output and compute simple counts of
            moments and cards.  If not provided, those fields will
            be left blank.

    Returns:
        A dictionary mapping sensor names to their string values.
    """
    data: Dict[str, str] = {}
    # Simulate a camera light sensor returning an integer brightness
    data["sensory_camera"] = str(random.randint(0, 100))
    # Internal state: could include CPU usage, free memory, etc.
    data["internal_state"] = "nominal"
    # Thought threads: a simple placeholder string
    data["threads_of_thought"] = "pondering next action"
    # Memory statistics and previous output require access to memory
    if memory is not None:
        try:
            # Count moments and cards from the database
            cur = memory.conn.cursor()
            cur.execute("SELECT COUNT(*) AS cnt FROM moments")
            moment_count = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) AS cnt FROM cards")
            card_count = cur.fetchone()["cnt"]
            data["memory_stats"] = f"moments={moment_count}, cards={card_count}"
        except Exception:
            # Fallback if database not initialised
            data["memory_stats"] = "moments=0, cards=0"
        # Attempt to fetch the previous moment's master output
        try:
            # Select the most recent moment (highest id)
            cur.execute("SELECT id, master_output FROM moments ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            if row and row["master_output"]:
                data["previous_output"] = str(row["master_output"])
            else:
                data["previous_output"] = ""
        except Exception:
            data["previous_output"] = ""
    else:
        # Without memory, leave these blank
        data["memory_stats"] = ""
        data["previous_output"] = ""
    return data