"""TaskerNet: Unified Neuroevolution System.

Encodes Tasc structures (Cards, Buffers, Selves) as evolvable DNA.
Decodes DNA into executable neural tree networks.
Evolves via tournaments to discover optimal architectures.
"""

import math
import random
import copy
from typing import List, Dict, Any, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

try:
    from .energy import EnergyNetwork, EnergyNode
except ImportError:
    from energy import EnergyNetwork, EnergyNode


# ---------------------------------------------------------------------------
# Genes: The Configurable DNA Components
# ---------------------------------------------------------------------------

class ActivationType(Enum):
    RELU = "relu"
    TANH = "tanh"
    SIGMOID = "sigmoid"
    LINEAR = "linear"


class TransformType(Enum):
    """Buffer transform types (like Self behaviors)."""
    IDENTITY = "identity"
    DOUBLE = "double"
    SQUARE = "square"
    NEGATE = "negate"
    ABS = "abs"
    CLAMP = "clamp"


@dataclass
class StructureGene:
    """Encodes network topology."""
    num_layers: int = 3            # Depth of tree
    branching_factor: int = 2      # Children per node (avg)
    connection_density: float = 0.5  # 0=tree, 1=full graph
    skip_connections: bool = False   # Allow skip connections
    
    def mutate(self, rate: float = 0.1):
        if random.random() < rate:
            self.num_layers = max(1, self.num_layers + random.randint(-1, 1))
        if random.random() < rate:
            self.branching_factor = max(1, self.branching_factor + random.randint(-1, 1))
        if random.random() < rate:
            self.connection_density = max(0, min(1, self.connection_density + random.uniform(-0.2, 0.2)))
        if random.random() < rate:
            self.skip_connections = not self.skip_connections


@dataclass
class BehaviorGene:
    """Encodes node behaviors (like Selves)."""
    activation: ActivationType = ActivationType.RELU
    transform: TransformType = TransformType.IDENTITY
    recall_probability: float = 0.0  # Chance to query memory
    output_scale: float = 1.0        # Output multiplier
    
    def mutate(self, rate: float = 0.1):
        if random.random() < rate:
            self.activation = random.choice(list(ActivationType))
        if random.random() < rate:
            self.transform = random.choice(list(TransformType))
        if random.random() < rate:
            self.recall_probability = max(0, min(1, self.recall_probability + random.uniform(-0.2, 0.2)))
        if random.random() < rate:
            self.output_scale = max(0.1, self.output_scale + random.uniform(-0.3, 0.3))


@dataclass
class WeightGene:
    """Encodes connection weights."""
    weights: Dict[Tuple[str, str], float] = field(default_factory=dict)
    
    def get_weight(self, src: str, dst: str, default: float = 1.0) -> float:
        return self.weights.get((src, dst), default)
    
    def set_weight(self, src: str, dst: str, value: float):
        self.weights[(src, dst)] = value
    
    def mutate(self, rate: float = 0.1, power: float = 0.3):
        for key in self.weights:
            if random.random() < rate:
                self.weights[key] += random.gauss(0, power)


@dataclass
class TaskerDNA:
    """Complete genome for a TaskerNet."""
    structure: StructureGene = field(default_factory=StructureGene)
    behaviors: Dict[str, BehaviorGene] = field(default_factory=dict)
    weights: WeightGene = field(default_factory=WeightGene)
    
    def mutate(self, rate: float = 0.1):
        self.structure.mutate(rate)
        for b in self.behaviors.values():
            b.mutate(rate)
        self.weights.mutate(rate)
    
    @classmethod
    def random(cls, num_nodes: int = 5) -> "TaskerDNA":
        """Create random DNA."""
        dna = cls()
        dna.structure = StructureGene(
            num_layers=random.randint(2, 5),
            branching_factor=random.randint(1, 4),
            connection_density=random.random(),
            skip_connections=random.random() > 0.5
        )
        for i in range(num_nodes):
            dna.behaviors[f"node_{i}"] = BehaviorGene(
                activation=random.choice(list(ActivationType)),
                transform=random.choice(list(TransformType)),
                recall_probability=random.random() * 0.3,
                output_scale=random.uniform(0.5, 2.0)
            )
        return dna


# ---------------------------------------------------------------------------
# TaskerNode: A node in the neural tree (like a Card with Buffers + Self)
# ---------------------------------------------------------------------------

@dataclass
class TaskerNode:
    """A node in the TaskerNet (Card + Buffer + Self combined)."""
    id: str
    behavior: BehaviorGene = field(default_factory=BehaviorGene)
    energy: float = 0.0
    activation: float = 0.0
    children: List[str] = field(default_factory=list)
    parents: List[str] = field(default_factory=list)
    
    def activate(self, input_value: float) -> float:
        """Apply activation function to input."""
        x = input_value * self.behavior.output_scale
        
        # Apply transform (like Self behavior)
        if self.behavior.transform == TransformType.DOUBLE:
            x = x * 2
        elif self.behavior.transform == TransformType.SQUARE:
            x = x * x
        elif self.behavior.transform == TransformType.NEGATE:
            x = -x
        elif self.behavior.transform == TransformType.ABS:
            x = abs(x)
        elif self.behavior.transform == TransformType.CLAMP:
            x = max(-1, min(1, x))
        
        # Apply activation function
        if self.behavior.activation == ActivationType.RELU:
            return max(0, x)
        elif self.behavior.activation == ActivationType.TANH:
            return math.tanh(x)
        elif self.behavior.activation == ActivationType.SIGMOID:
            return 1 / (1 + math.exp(-max(-500, min(500, x))))
        else:
            return x


# ---------------------------------------------------------------------------
# TaskerNet: The main neural tree network
# ---------------------------------------------------------------------------

class TaskerNet:
    """Neural tree network decoded from TaskerDNA.
    
    This is a dynamic graph where:
    - Nodes = Tascs (Cards with Buffers)
    - Edges = weighted connections
    - Behaviors = Self activation functions
    - Energy = flows from root through network
    """
    
    def __init__(self, dna: TaskerDNA):
        self.dna = dna
        self.nodes: Dict[str, TaskerNode] = {}
        self.root_id: str = "root"
        self.output_ids: List[str] = []
        self.energy_net = EnergyNetwork()
        
        self._build_from_dna()
    
    def _build_from_dna(self):
        """Decode DNA into network structure."""
        structure = self.dna.structure
        behaviors = self.dna.behaviors
        
        # Create root node
        root_behavior = behaviors.get("node_0", BehaviorGene())
        self.nodes["root"] = TaskerNode(id="root", behavior=root_behavior, energy=100.0)
        self.energy_net.add_node("root", 100.0)
        
        # Build tree structure
        current_layer = ["root"]
        node_counter = 1
        
        for layer_idx in range(structure.num_layers - 1):
            next_layer = []
            
            for parent_id in current_layer:
                # Determine number of children (with some randomness)
                base_children = structure.branching_factor
                num_children = max(1, base_children + random.randint(-1, 1))
                
                for c in range(num_children):
                    child_id = f"node_{node_counter}"
                    node_counter += 1
                    
                    # Get or create behavior
                    child_behavior = behaviors.get(child_id, BehaviorGene())
                    
                    # Create node
                    self.nodes[child_id] = TaskerNode(id=child_id, behavior=child_behavior)
                    self.energy_net.add_node(child_id, 0.0)
                    
                    # Connect to parent
                    self.nodes[parent_id].children.append(child_id)
                    self.nodes[child_id].parents.append(parent_id)
                    self.energy_net.connect(parent_id, child_id)
                    
                    # Set initial weight
                    weight = self.dna.weights.get_weight(parent_id, child_id, 1.0)
                    self.dna.weights.set_weight(parent_id, child_id, weight)
                    
                    next_layer.append(child_id)
            
            current_layer = next_layer
            
            # Add skip connections based on density
            if structure.skip_connections and structure.connection_density > 0:
                for node_id in current_layer:
                    for other_id in list(self.nodes.keys()):
                        if other_id != node_id and other_id not in self.nodes[node_id].parents:
                            if random.random() < structure.connection_density * 0.2:
                                self.nodes[other_id].children.append(node_id)
                                self.nodes[node_id].parents.append(other_id)
                                self.energy_net.connect(other_id, node_id)
        
        # Last layer nodes are outputs
        self.output_ids = current_layer if current_layer else ["root"]
    
    def forward(self, input_value: float) -> float:
        """Forward pass: propagate input through network."""
        # Reset activations
        for node in self.nodes.values():
            node.activation = 0.0
        
        # Set root activation
        self.nodes["root"].activation = input_value
        
        # BFS propagation
        queue = ["root"]
        visited = set()
        
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            
            node = self.nodes[node_id]
            
            # Propagate to children
            for child_id in node.children:
                weight = self.dna.weights.get_weight(node_id, child_id, 1.0)
                child = self.nodes[child_id]
                
                # Accumulate weighted input
                child.activation += node.activation * weight
                
                if child_id not in visited:
                    queue.append(child_id)
        
        # Compute output: average of output node activations
        output_sum = 0.0
        for out_id in self.output_ids:
            output_sum += self.nodes[out_id].activate(self.nodes[out_id].activation)
        
        return output_sum / max(1, len(self.output_ids))
    
    def diffuse_energy(self, steps: int = 1):
        """Run energy diffusion through the network."""
        self.energy_net.run_diffusion(steps)
        
        # Sync energy back to nodes
        for node_id, node in self.nodes.items():
            if node_id in self.energy_net.nodes:
                node.energy = self.energy_net.nodes[node_id].energy
    
    def inject_reward(self, node_id: str, reward: float):
        """Inject reward energy into a node."""
        if node_id in self.energy_net.nodes:
            self.energy_net.inject_energy(node_id, reward)
    
    def node_count(self) -> int:
        return len(self.nodes)
    
    def visualize(self) -> str:
        """ASCII visualization of the network."""
        lines = [f"TaskerNet ({self.node_count()} nodes):"]
        
        def print_node(node_id: str, depth: int):
            node = self.nodes[node_id]
            indent = "  " * depth
            act = node.behavior.activation.value[:3]
            trans = node.behavior.transform.value[:3]
            lines.append(f"{indent}└─ {node_id} [E={node.energy:.1f}, {act}/{trans}]")
            for child_id in node.children:
                if child_id in self.nodes:
                    print_node(child_id, depth + 1)
        
        print_node("root", 0)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Crossover and Evolution
# ---------------------------------------------------------------------------

def crossover_dna(dna_a: TaskerDNA, dna_b: TaskerDNA) -> TaskerDNA:
    """Crossover two TaskerDNA genomes."""
    child = TaskerDNA()
    
    # Structure: randomly pick from parents
    if random.random() < 0.5:
        child.structure = copy.deepcopy(dna_a.structure)
    else:
        child.structure = copy.deepcopy(dna_b.structure)
    
    # Behaviors: merge from both parents
    all_keys = set(dna_a.behaviors.keys()) | set(dna_b.behaviors.keys())
    for key in all_keys:
        if key in dna_a.behaviors and key in dna_b.behaviors:
            if random.random() < 0.5:
                child.behaviors[key] = copy.deepcopy(dna_a.behaviors[key])
            else:
                child.behaviors[key] = copy.deepcopy(dna_b.behaviors[key])
        elif key in dna_a.behaviors:
            child.behaviors[key] = copy.deepcopy(dna_a.behaviors[key])
        else:
            child.behaviors[key] = copy.deepcopy(dna_b.behaviors[key])
    
    # Weights: average where both exist
    all_weight_keys = set(dna_a.weights.weights.keys()) | set(dna_b.weights.weights.keys())
    for key in all_weight_keys:
        w_a = dna_a.weights.weights.get(key, 1.0)
        w_b = dna_b.weights.weights.get(key, 1.0)
        child.weights.weights[key] = (w_a + w_b) / 2
    
    return child


# ---------------------------------------------------------------------------
# Tournament for TaskerNets
# ---------------------------------------------------------------------------

@dataclass
class TaskerPlayer:
    id: str
    dna: TaskerDNA
    fitness: float = 0.0


class TaskerTournament:
    """Evolve TaskerNets via competition."""
    
    def __init__(self, problems: List[Tuple[float, float]] = None):
        """
        problems: List of (input, expected_output) pairs
        """
        self.problems = problems or [
            (2.0, 4.0),   # Double
            (3.0, 9.0),   # Square  
            (5.0, 10.0),  # Double
            (-2.0, 4.0),  # Square (abs then square works)
            (0.0, 0.0),   # Zero
            (1.0, 2.0),   # Double
        ]
        self.players: List[TaskerPlayer] = []
        self.generation = 0
        self.best_fitness_history: List[float] = []
        
    def seed_population(self, size: int = 32):
        """Create initial population."""
        self.players = []
        for i in range(size):
            dna = TaskerDNA.random(num_nodes=random.randint(3, 8))
            self.players.append(TaskerPlayer(id=f"Tasker-{i+1}", dna=dna))
        print(f"🧬 TaskerTournament initialized with {len(self.players)} agents.")
    
    def evaluate_player(self, player: TaskerPlayer):
        """Evaluate fitness on problems."""
        net = TaskerNet(player.dna)
        
        total_error = 0.0
        for inp, expected in self.problems:
            try:
                output = net.forward(inp)
                error = abs(output - expected)
                total_error += error
            except:
                total_error += 1000  # Penalty for broken networks
        
        # Fitness = inverse of error (higher is better)
        player.fitness = 100.0 / (1.0 + total_error)
        
        # Bonus for smaller networks (Occam's razor)
        player.fitness += 5.0 / net.node_count()
    
    def run_generation(self):
        """Run one generation of evolution."""
        self.generation += 1
        
        # Evaluate all
        for p in self.players:
            self.evaluate_player(p)
        
        # Sort by fitness
        self.players.sort(key=lambda x: x.fitness, reverse=True)
        
        best = self.players[0]
        self.best_fitness_history.append(best.fitness)
        
        print(f"Gen {self.generation}: Best={best.id} Fitness={best.fitness:.2f} Nodes={TaskerNet(best.dna).node_count()}")
        
        # Selection: keep top 50%
        survivors = self.players[:len(self.players)//2]
        
        # Reproduction
        offspring = []
        while len(offspring) < len(survivors):
            parent_a = random.choice(survivors)
            parent_b = random.choice(survivors)
            
            child_dna = crossover_dna(parent_a.dna, parent_b.dna)
            child_dna.mutate(rate=0.15)
            
            child = TaskerPlayer(
                id=f"Child-G{self.generation}-{len(offspring)+1}",
                dna=child_dna
            )
            offspring.append(child)
        
        self.players = survivors + offspring
    
    def evolve(self, generations: int = 20):
        """Run evolution for N generations."""
        for _ in range(generations):
            self.run_generation()
        
        # Final evaluation
        for p in self.players:
            self.evaluate_player(p)
        self.players.sort(key=lambda x: x.fitness, reverse=True)
        
        winner = self.players[0]
        print(f"\n🏆 CHAMPION: {winner.id} (Fitness: {winner.fitness:.3f})")
        
        # Show champion's network
        net = TaskerNet(winner.dna)
        print(net.visualize())
        
        return winner


if __name__ == "__main__":
    print("=" * 60)
    print("TASKERNET: Unified Neuroevolution System")
    print("=" * 60)
    
    t = TaskerTournament()
    t.seed_population(32)
    winner = t.evolve(generations=15)
    
    print("\n--- Testing Champion ---")
    net = TaskerNet(winner.dna)
    for inp, exp in t.problems[:3]:
        out = net.forward(inp)
        print(f"  Input: {inp} -> Output: {out:.2f} (Expected: {exp})")
