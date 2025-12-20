"""Neural Cellular Automata Solver for ARC.

This module implements an Input-Aware Neural Network that learns the
transformation function `(InputGrid, x, y) -> OutputColor`.
"""

import math
import random
import json
import urllib.request
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field

from ab.atoms import DNA, Gene, Instruction
from ab.genetics import crossover, mutate
from ab.neural import NeuralLayer, NeuralNetwork, relu, softmax, mat_mul, mat_add_vec

# ---------------------------------------------------------------------------
# NCA Network: Takes neighborhood context as input
# ---------------------------------------------------------------------------

class NCANetwork:
    """Neural Cellular Automata Network.
    
    Input Features (per pixel):
    - x_norm, y_norm: Normalized coordinates
    - input_color: One-hot encoded color of this pixel in INPUT grid
    - neighbor_colors: Average colors of 8 neighbors in INPUT grid
    
    Total Input Size: 2 (coords) + 10 (color) + 10 (avg neighbors) = 22
    """
    
    INPUT_SIZE = 22
    OUTPUT_SIZE = 10  # 10 ARC colors
    
    def __init__(self, dna: DNA):
        self.layers: List[NeuralLayer] = []
        
        # Architecture: 22 -> 32 -> 32 -> 10
        hidden_size = 32
        
        g0 = dna.get_gene("0")
        g1 = dna.get_gene("1")
        g2 = dna.get_gene("2")
        
        self.layers.append(NeuralLayer(self.INPUT_SIZE, hidden_size, g0))
        self.layers.append(NeuralLayer(hidden_size, hidden_size, g1))
        self.layers.append(NeuralLayer(hidden_size, self.OUTPUT_SIZE, g2))
        
    def predict(self, features: List[float]) -> List[float]:
        """Forward pass."""
        x = [features]
        for layer in self.layers:
            x = layer.forward(x)
        return softmax(x[0])
    
    def to_dna(self) -> DNA:
        """Serialize network back to DNA."""
        genes = [
            self.layers[0].to_gene("0"),
            self.layers[1].to_gene("1"),
            self.layers[2].to_gene("2")
        ]
        return DNA(genes=genes)


def one_hot(color: int, num_classes: int = 10) -> List[float]:
    """One-hot encode a color."""
    vec = [0.0] * num_classes
    if 0 <= color < num_classes:
        vec[color] = 1.0
    return vec


def get_neighbors(grid: List[List[int]], x: int, y: int) -> List[float]:
    """Get average one-hot of 8 neighbors."""
    h = len(grid)
    w = len(grid[0]) if h > 0 else 0
    
    avg = [0.0] * 10
    count = 0
    
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                color = grid[ny][nx]
                oh = one_hot(color)
                for i in range(10):
                    avg[i] += oh[i]
                count += 1
                
    if count > 0:
        for i in range(10):
            avg[i] /= count
            
    return avg


def extract_features(input_grid: List[List[int]], x: int, y: int, width: int, height: int) -> List[float]:
    """Build feature vector for NCA."""
    # Normalized coords
    x_norm = x / max(1, width - 1)
    y_norm = y / max(1, height - 1)
    
    # Input color at this pixel
    input_color = input_grid[y][x] if y < len(input_grid) and x < len(input_grid[0]) else 0
    color_oh = one_hot(input_color)
    
    # Neighbor context
    neighbors = get_neighbors(input_grid, x, y)
    
    return [x_norm, y_norm] + color_oh + neighbors


# ---------------------------------------------------------------------------
# ARC Multi-Task Environment
# ---------------------------------------------------------------------------

class ARCMultiTaskEnv:
    """Loads and evaluates on multiple ARC tasks."""
    
    BASE_URL = "https://raw.githubusercontent.com/fchollet/ARC-AGI/master/data/training/"
    
    # A subset of training task IDs for faster iteration
    TASK_IDS = [
        "007bbfb7", "00d62c1b", "017c7c7b", "025d127b", "0520fde7",
        "05f2a901", "06df4c85", "08ed6ac7", "09629e4f", "0a938d79"
    ]
    
    def __init__(self, max_tasks: int = 5):
        self.tasks: Dict[str, Any] = {}
        self._load_tasks(max_tasks)
        
    def _load_tasks(self, max_tasks: int):
        print(f"🌐 Loading {max_tasks} ARC tasks...")
        for task_id in self.TASK_IDS[:max_tasks]:
            url = f"{self.BASE_URL}{task_id}.json"
            try:
                with urllib.request.urlopen(url, timeout=5) as f:
                    data = json.loads(f.read().decode())
                    self.tasks[task_id] = data
            except Exception as e:
                print(f"  ⚠ Failed to load {task_id}: {e}")
        print(f"✅ Loaded {len(self.tasks)} tasks.")
        
    def evaluate(self, dna: DNA) -> float:
        """Evaluate DNA across all loaded tasks."""
        if not self.tasks:
            return 0.0
            
        total_score = 0.0
        total_pairs = 0
        
        nn = NCANetwork(dna)
        
        for task_id, task_data in self.tasks.items():
            for pair in task_data.get("train", []):
                input_grid = pair["input"]
                target_grid = pair["output"]
                
                h_out = len(target_grid)
                w_out = len(target_grid[0]) if h_out > 0 else 0
                
                correct = 0
                total_pixels = h_out * w_out
                
                for y in range(h_out):
                    for x in range(w_out):
                        # Handle size mismatch: use input if possible
                        h_in = len(input_grid)
                        w_in = len(input_grid[0]) if h_in > 0 else 0
                        
                        # Map output coords to input coords (simple scaling)
                        in_x = int(x * w_in / max(1, w_out))
                        in_y = int(y * h_in / max(1, h_out))
                        
                        features = extract_features(input_grid, in_x, in_y, w_out, h_out)
                        
                        logits = nn.predict(features)
                        predicted = logits.index(max(logits))
                        
                        if predicted == target_grid[y][x]:
                            correct += 1
                            
                if total_pixels > 0:
                    total_score += correct / total_pixels
                    total_pairs += 1
                    
        if total_pairs == 0:
            return 0.0
            
        return (total_score / total_pairs) * 100.0


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------

@dataclass
class Player:
    id: str
    dna: DNA
    score: float = 0.0
    history: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# NCA Tournament
# ---------------------------------------------------------------------------

class NCATournament:
    """Tournament evolving NCA networks on multi-task ARC."""
    
    def __init__(self, num_tasks: int = 5):
        self.players: List[Player] = []
        self.round_num: int = 0
        self.environment = ARCMultiTaskEnv(max_tasks=num_tasks)
        
    def seed_bracket(self, size: int = 64):
        """Create population of NCA Networks."""
        self.players = []
        for i in range(size):
            # Create empty DNA, let NCANetwork init random weights
            genes = [Gene(id="0"), Gene(id="1"), Gene(id="2")]
            dna = DNA(genes=genes)
            
            # Init and serialize back
            nn = NCANetwork(dna)
            full_dna = nn.to_dna()
            
            self.players.append(Player(id=f"NCA-{i+1}", dna=full_dna))
            
        print(f"🧬 NCA Tournament initialized with {len(self.players)} agents.")
        
    def evaluate_player(self, player: Player):
        player.score = self.environment.evaluate(player.dna)
        
    def play(self, max_rounds: int = 10):
        """Run tournament."""
        while len(self.players) > 1 and self.round_num < max_rounds:
            self.round_num += 1
            print(f"\n--- Round {self.round_num} (Players: {len(self.players)}) ---")
            
            if len(self.players) > 16:
                self._qualifying_round()
            else:
                self._knockout_round()
                
        if self.players:
            winner = self.players[0]
            print(f"\n🏆 CHAMPION: {winner.id} (Score: {winner.score:.2f}%)")
            
    def _qualifying_round(self):
        for p in self.players:
            self.evaluate_player(p)
        self.players.sort(key=lambda x: x.score, reverse=True)
        
        top = self.players[0]
        print(f"Top Score: {top.score:.2f}% ({top.id})")
        
        self.players = self.players[:len(self.players)//2]
        
    def _knockout_round(self):
        next_round = []
        
        for p in self.players:
            self.evaluate_player(p)
        self.players.sort(key=lambda x: x.score, reverse=True)
        
        matchups = []
        for i in range(0, len(self.players), 2):
            if i+1 < len(self.players):
                matchups.append((self.players[i], self.players[i+1]))
            else:
                next_round.append(self.players[i])
                
        for p1, p2 in matchups:
            print(f"Match: {p1.id} ({p1.score:.1f}%) vs {p2.id} ({p2.score:.1f}%)")
            
            child_dna = crossover(p1.dna, p2.dna)
            child_dna = mutate(child_dna, mutation_rate=0.1, mutation_power=0.2)
            
            child = Player(id=f"Child({p1.id}+{p2.id})", dna=child_dna)
            self.evaluate_player(child)
            
            print(f"  -> Offspring: {child.score:.1f}%")
            
            best = max([p1, p2, child], key=lambda x: x.score)
            next_round.append(best)
            
        self.players = next_round


if __name__ == "__main__":
    import sys
    
    num_tasks = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    pop_size = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    
    t = NCATournament(num_tasks=num_tasks)
    t.seed_bracket(size=pop_size)
    t.play(max_rounds=8)
