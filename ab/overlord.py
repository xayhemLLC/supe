"""Overlord Neural Network: RL-trained selector for Selves.

The Overlord learns which Self to invoke for a given task.
Its DNA encodes the neural network weights.
"""

import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .atoms import DNA, Gene, Instruction
from .neural import NeuralLayer, softmax


@dataclass
class SelfProfile:
    """Profile of an available Self."""
    name: str
    specialty: str  # e.g., "math", "string", "list"
    past_accuracy: float = 0.5
    past_speed: float = 0.5


class OverlordNetwork:
    """Neural network that selects which Self to invoke.
    
    Input Features:
    - Task embedding (simplified: problem type one-hot)
    - Available Selves profiles
    
    Output:
    - Probability distribution over Selves
    - Recall action probability
    """
    
    def __init__(self, dna: DNA, num_selves: int = 4, num_problem_types: int = 5):
        self.num_selves = num_selves
        self.num_problem_types = num_problem_types
        
        # Input: problem_type (one-hot) + self_profiles (features per self)
        # Simplified: 5 problem types + 4 selves * 2 features = 13 input
        input_size = num_problem_types + num_selves * 2
        hidden_size = 16
        output_size = num_selves + 1  # +1 for "recall" action
        
        g0 = dna.get_gene("0")
        g1 = dna.get_gene("1")
        
        self.layer1 = NeuralLayer(input_size, hidden_size, g0)
        self.layer2 = NeuralLayer(hidden_size, output_size, g1)
        
    def select(self, problem_type: int, selves: List[SelfProfile]) -> Dict[str, float]:
        """Select which Self to invoke.
        
        Returns dict with probabilities for each self and "recall" action.
        """
        # Build input vector
        features = [0.0] * self.num_problem_types
        if 0 <= problem_type < self.num_problem_types:
            features[problem_type] = 1.0
        
        for i, s in enumerate(selves[:self.num_selves]):
            features.extend([s.past_accuracy, s.past_speed])
        
        # Pad if fewer selves
        while len(features) < self.num_problem_types + self.num_selves * 2:
            features.extend([0.0, 0.0])
        
        # Forward pass
        x = [features]
        x = self.layer1.forward(x)
        x = self.layer2.forward(x)
        
        probs = softmax(x[0])
        
        # Build result
        result = {}
        for i, s in enumerate(selves[:self.num_selves]):
            result[s.name] = probs[i] if i < len(probs) else 0.0
        result["recall"] = probs[-1] if probs else 0.0
        
        return result
    
    def to_dna(self) -> DNA:
        """Serialize network to DNA."""
        genes = [
            self.layer1.to_gene("0"),
            self.layer2.to_gene("1")
        ]
        return DNA(genes=genes)


class Overlord:
    """The Overlord manages Self selection and learning."""
    
    def __init__(self, dna: Optional[DNA] = None):
        if dna is None:
            # Create random DNA
            dna = DNA(genes=[Gene(id="0"), Gene(id="1")])
        
        self.dna = dna
        self.network = OverlordNetwork(dna)
        self.selves: List[SelfProfile] = []
        self.history: List[Dict[str, Any]] = []
        
    def register_self(self, name: str, specialty: str):
        """Register a Self with the Overlord."""
        self.selves.append(SelfProfile(name=name, specialty=specialty))
        
    def select_self(self, problem_type: int) -> str:
        """Select which Self to use for a problem."""
        if not self.selves:
            return "default"
        
        probs = self.network.select(problem_type, self.selves)
        
        # Sample from distribution
        names = list(probs.keys())
        weights = [probs[n] for n in names]
        
        selected = random.choices(names, weights=weights, k=1)[0]
        
        self.history.append({
            "problem_type": problem_type,
            "selected": selected,
            "probs": probs
        })
        
        return selected
    
    def update_performance(self, self_name: str, accuracy: float, speed: float):
        """Update a Self's performance metrics."""
        for s in self.selves:
            if s.name == self_name:
                # Exponential moving average
                s.past_accuracy = 0.9 * s.past_accuracy + 0.1 * accuracy
                s.past_speed = 0.9 * s.past_speed + 0.1 * speed
                break
    
    def get_reward(self, accuracy: float, speed: float) -> float:
        """Compute reward for RL training."""
        return accuracy * 100 + speed * 10


def create_random_overlord() -> Overlord:
    """Factory for random Overlord."""
    return Overlord()


if __name__ == "__main__":
    # Demo
    overlord = create_random_overlord()
    overlord.register_self("MathSelf", "math")
    overlord.register_self("StringSelf", "string")
    overlord.register_self("ListSelf", "list")
    
    for problem_type in range(3):
        selected = overlord.select_self(problem_type)
        print(f"Problem Type {problem_type}: Selected {selected}")
        overlord.update_performance(selected, random.random(), random.random())