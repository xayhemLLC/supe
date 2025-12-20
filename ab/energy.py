"""Energy Diffusion Network: Biological energy flow for Overlord routing.

Energy distributes by dividing equally among neighbors + self.
This creates a softer, more organic routing system than sharp selection.
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import random


@dataclass
class EnergyNode:
    """A node in the energy network."""
    id: str
    energy: float = 0.0
    neighbors: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def degree(self) -> int:
        """Number of neighbors (not including self)."""
        return len(self.neighbors)
    
    def share_count(self) -> int:
        """Number of shares for diffusion (neighbors + self)."""
        return self.degree + 1


class EnergyNetwork:
    """A network where energy diffuses between connected nodes.
    
    Each step, every node divides its energy equally among:
    - Itself (1 share)
    - Each neighbor (1 share each)
    
    This creates natural clustering and credit assignment.
    """
    
    def __init__(self):
        self.nodes: Dict[str, EnergyNode] = {}
        self.step_count: int = 0
        self.history: List[Dict[str, float]] = []
        
    def add_node(self, node_id: str, initial_energy: float = 0.0) -> EnergyNode:
        """Add a node to the network."""
        if node_id not in self.nodes:
            self.nodes[node_id] = EnergyNode(id=node_id, energy=initial_energy)
        return self.nodes[node_id]
    
    def connect(self, node_a: str, node_b: str):
        """Create bidirectional connection between nodes."""
        if node_a not in self.nodes:
            self.add_node(node_a)
        if node_b not in self.nodes:
            self.add_node(node_b)
        
        self.nodes[node_a].neighbors.add(node_b)
        self.nodes[node_b].neighbors.add(node_a)
        
    def inject_energy(self, node_id: str, amount: float):
        """Inject energy into a node (e.g., from reward)."""
        if node_id in self.nodes:
            self.nodes[node_id].energy += amount
            
    def total_energy(self) -> float:
        """Total energy in the system (should be conserved)."""
        return sum(n.energy for n in self.nodes.values())
    
    def diffusion_step(self):
        """Perform one diffusion step: energy spreads to neighbors equally."""
        # Calculate incoming energy for each node
        incoming: Dict[str, float] = defaultdict(float)
        
        for node_id, node in self.nodes.items():
            share_count = node.share_count()
            if share_count == 0:
                continue
                
            share = node.energy / share_count
            
            # Send to self
            incoming[node_id] += share
            
            # Send to neighbors
            for neighbor_id in node.neighbors:
                incoming[neighbor_id] += share
        
        # Update all nodes
        for node_id, node in self.nodes.items():
            node.energy = incoming[node_id]
        
        self.step_count += 1
        
        # Record history
        snapshot = {nid: n.energy for nid, n in self.nodes.items()}
        self.history.append(snapshot)
        
    def run_diffusion(self, steps: int = 10):
        """Run multiple diffusion steps."""
        for _ in range(steps):
            self.diffusion_step()
            
    def get_energy_distribution(self) -> Dict[str, float]:
        """Get current energy distribution as dict."""
        return {nid: n.energy for nid, n in self.nodes.items()}
    
    def select_by_energy(self, candidates: Optional[List[str]] = None) -> str:
        """Select a node probabilistically based on energy."""
        if candidates is None:
            candidates = list(self.nodes.keys())
        
        if not candidates:
            return ""
        
        energies = [max(0, self.nodes[c].energy) for c in candidates]
        total = sum(energies)
        
        if total == 0:
            return random.choice(candidates)
        
        # Weighted random selection
        r = random.random() * total
        cumulative = 0
        for i, c in enumerate(candidates):
            cumulative += energies[i]
            if r <= cumulative:
                return c
        
        return candidates[-1]
    
    def visualize_ascii(self, width: int = 50) -> str:
        """ASCII visualization of energy distribution."""
        if not self.nodes:
            return "Empty network"
        
        max_energy = max(n.energy for n in self.nodes.values())
        if max_energy == 0:
            max_energy = 1
        
        lines = ["Energy Distribution:"]
        for node_id, node in sorted(self.nodes.items()):
            bar_len = int((node.energy / max_energy) * width)
            bar = "█" * bar_len
            lines.append(f"{node_id:12} [{node.energy:6.2f}] {bar}")
        
        lines.append(f"\nTotal Energy: {self.total_energy():.2f}")
        lines.append(f"Steps: {self.step_count}")
        
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Overlord Integration: Energy-Based Self Selection
# ---------------------------------------------------------------------------

class EnergyOverlord:
    """Overlord that routes based on energy diffusion."""
    
    def __init__(self):
        self.network = EnergyNetwork()
        self.selves: List[str] = []
        
        # Add the Overlord node as hub
        self.network.add_node("overlord", initial_energy=100.0)
        
    def register_self(self, name: str):
        """Register a Self and connect it to the Overlord."""
        self.selves.append(name)
        self.network.add_node(name, initial_energy=0.0)
        self.network.connect("overlord", name)
        
    def select_self(self) -> str:
        """Select a Self based on energy distribution."""
        if not self.selves:
            return ""
        return self.network.select_by_energy(self.selves)
    
    def reward_self(self, name: str, reward: float):
        """Inject reward energy into a Self node."""
        self.network.inject_energy(name, reward)
        
    def step(self):
        """Run one diffusion step."""
        self.network.diffusion_step()
        
    def status(self) -> str:
        """Get status visualization."""
        return self.network.visualize_ascii()


# ---------------------------------------------------------------------------
# Demo / First Tasc
# ---------------------------------------------------------------------------

def demo_energy_network():
    """Demonstrate the energy diffusion network."""
    print("=" * 60)
    print("ENERGY DIFFUSION NETWORK - First Tasc!")
    print("=" * 60)
    
    # Create network
    net = EnergyNetwork()
    
    # Add nodes: Overlord + 3 Selves
    net.add_node("overlord", initial_energy=100.0)
    net.add_node("MathSelf", initial_energy=0.0)
    net.add_node("StringSelf", initial_energy=0.0)
    net.add_node("ListSelf", initial_energy=0.0)
    
    # Connect: Star topology with Overlord at center
    net.connect("overlord", "MathSelf")
    net.connect("overlord", "StringSelf")
    net.connect("overlord", "ListSelf")
    
    # Also connect Selves to each other (full mesh)
    net.connect("MathSelf", "StringSelf")
    net.connect("StringSelf", "ListSelf")
    net.connect("ListSelf", "MathSelf")
    
    print("\nInitial State:")
    print(net.visualize_ascii())
    
    # Run diffusion
    print("\n--- After 5 Diffusion Steps ---")
    net.run_diffusion(5)
    print(net.visualize_ascii())
    
    # Inject reward into MathSelf (simulating it solved a problem)
    print("\n--- Injecting +50 reward into MathSelf ---")
    net.inject_energy("MathSelf", 50.0)
    print(net.visualize_ascii())
    
    # Run more diffusion
    print("\n--- After 5 More Steps ---")
    net.run_diffusion(5)
    print(net.visualize_ascii())
    
    # Selection demo
    print("\n--- Selection by Energy (10 trials) ---")
    selections = [net.select_by_energy(["MathSelf", "StringSelf", "ListSelf"]) for _ in range(10)]
    for name in ["MathSelf", "StringSelf", "ListSelf"]:
        count = selections.count(name)
        print(f"  {name}: selected {count}/10 times")
    
    print("\n" + "=" * 60)
    print("Energy diffusion complete!")
    print("=" * 60)
    
    return net


if __name__ == "__main__":
    demo_energy_network()
