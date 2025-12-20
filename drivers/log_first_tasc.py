"""Log the Energy Diffusion Network as the first Tasc.

This script demonstrates using the Tasc framework to record
the development of the Energy Diffusion system.
"""

import sys
sys.path.insert(0, ".")

from ab.abdb import ABMemory
from ab.models import Buffer

def log_first_tasc():
    """Create the first Tasc entry in AB Memory."""
    
    # Initialize memory
    mem = ABMemory("ab_memory.sqlite")
    
    # Create a Moment for this development session
    moment = mem.create_moment(
        master_input="Implement Energy Diffusion Network",
        master_output="Created ab/energy.py with biological energy flow"
    )
    
    # Create the Tasc card
    tasc_card = mem.store_card(
        label="tasc",
        buffers=[
            Buffer(name="title", payload="Energy Diffusion Network"),
            Buffer(name="description", payload="""
A network where energy diffuses between connected nodes.
Each node divides its energy equally among itself and neighbors.
This creates natural clustering and credit assignment for RL.
            """.strip()),
            Buffer(name="status", payload="complete"),
            Buffer(name="type", payload="feature"),
            Buffer(
                name="code_location", 
                payload="ab/energy.py"
            ),
            Buffer(
                name="key_classes",
                payload="EnergyNode, EnergyNetwork, EnergyOverlord"
            ),
            Buffer(
                name="integration",
                payload="Replaces sharp Overlord selection with energy-based routing"
            ),
        ],
        owner_self="Antigravity",
        moment_id=moment.id,
        dna=None  # No genetic component for this tasc
    )
    
    print(f"✅ First Tasc logged!")
    print(f"   Card ID: {tasc_card.id}")
    print(f"   Moment ID: {moment.id}")
    print(f"   Label: {tasc_card.label}")
    print(f"   Title: {tasc_card.buffers[0].payload}")
    
    # Recall it to verify
    recalled = mem.get_card(tasc_card.id)
    print(f"\n📋 Verified recall:")
    for buf in recalled.buffers:
        print(f"   {buf.name}: {str(buf.payload)[:50]}...")
    
    return tasc_card


if __name__ == "__main__":
    log_first_tasc()
