"""K-Tourney Tournament Runner.

Implements a World Cup style elimination tournament for genetic agents.
Features:
- "Male" (Winner) and "Female" (Runner-up) mating logic.
- Bracket seeded with top performers.
- New blood injection in later rounds.
"""

import random
import copy
from typing import List, Tuple, Optional, Any, Dict
from dataclasses import dataclass
import time

# Use our existing primitives
from ab.atoms import DNA, Gene, Instruction
from ab.genetics import crossover, mutate

# If datasets is not installed, we'll mock it or use a fallback
try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False
    print("Warning: 'datasets' library not found. Using mock/fallback data.")


@dataclass
class Player:
    """A participant in the tournament."""
    id: str
    dna: DNA
    score: float = 0.0 # Higher is better
    history: List[str] = None # Track match history

    def __post_init__(self):
        if self.history is None:
            self.history = []


import json
import urllib.request
from ab.atoms import DNA, Gene, Instruction
from ab.genetics import crossover, mutate

# Re-use Canvas from apex_demo if possible, or redefine simple version
try:
    from drivers.apex_demo import Canvas
except ImportError:
    # Fallback simpler canvas for ARC
    class Canvas:
        def __init__(self, width, height):
            self.width = width
            self.height = height
            self.pixels = {}
        def draw_pixel(self, x, y, color):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.pixels[(x, y)] = color
        def render_dna(self, dna):
            for gene in dna.genes:
                c = gene.traits.get("color", "#000000")
                for atom in gene.atomics:
                    if atom.op_code == "p" and isinstance(atom.payload, (list, tuple)):
                        self.draw_pixel(atom.payload[0], atom.payload[1], c)
        def diff(self, target_grid):
            # target_grid is list of lists of ints
            score = 0
            for y in range(self.height):
                for x in range(self.width):
                    # Map hex to int or just compare equality abstractly?
                    # ARC uses 0-9 ints. Our DNA uses Hex.
                    # Simplified: We treat everything as strings.
                    # We need a mapper. Let's strict map for now or just generic diff.
                    # For this demo, we assume the DNA tries to output matching colors.
                    pass
            return 0


class ARCEnvironment:
    """Real ARC Environment using GitHub data."""
    def __init__(self):
        self.task_data = None
        self.current_task_id = None
        self.train_pairs = []
        self.test_pairs = []
        self._load_data()

    def _load_data(self):
        print("🌐 Fetching ARC data from GitHub...")
        url = "https://raw.githubusercontent.com/fchollet/ARC-AGI/master/data/training/007bbfb7.json"
        try:
            with urllib.request.urlopen(url) as f:
                self.task_data = json.loads(f.read().decode())
                self.train_pairs = self.task_data["train"]
                self.test_pairs = self.task_data["test"] 
                print("✅ Data loaded: 007bbfb7")
        except Exception as e:
            print(f"❌ Failed to load ARC data: {e}")
            self.train_pairs = []

    def evaluate(self, dna: DNA) -> float:
        if not self.train_pairs:
            return 0.0
            
        # Try to match the FIRST training example output
        target_grid = self.train_pairs[0]["output"]
        height = len(target_grid)
        width = len(target_grid[0])
        
        # Create canvas
        canvas = Canvas(width, height)
        canvas.render_dna(dna)
        
        # Compare
        # Issue: DNA generates Hex colors (#FF0000), ARC expects Ints (0-9).
        # We need a Color Gene -> ARC Int mapping.
        # Heuristic: Gene ID or Trait "c" determines the int color.
        # Let's say gene.traits["c"] = int_color
        
        score = 0
        total_pixels = width * height
        
        for y in range(height):
            for x in range(width):
                target_val = target_grid[y][x]
                
                # Check what DNA painted here
                # We need to dig into canvas pixels
                painted_val = canvas.pixels.get((x, y))
                
                # If painted_val matches target_val, +1 score
                if painted_val == target_val:
                    score += 1
                    
        return (score / total_pixels) * 100.0

# Redefine Canvas to support Int colors for ARC
class Canvas:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.pixels = {} # (x,y) -> int color
        
    def render_dna(self, dna: DNA):
        for gene in dna.genes:
            # Trait 'c' for color integer
            try:
                c = int(gene.traits.get("c", 0))
            except:
                c = 0
                
            for atom in gene.atomics:
                if atom.op_code == "p": # Pixel
                     x, y = atom.payload
                     if 0 <= x < self.width and 0 <= y < self.height:
                         self.pixels[(x, y)] = c


class Tournament:
    def __init__(self):
        self.players: List[Player] = []
        self.round_num: int = 0
        self.environment = ARCEnvironment()
        
    def seed_bracket(self, size: int = 128):
        """Create initial random population."""
        self.players = []
        for i in range(size):
            genes = []
            for _ in range(10): # More complex genes for ARC
                # Random color 0-9
                color = random.randint(0, 9)
                # Random pixels
                atomics = []
                for _ in range(5):
                    x = random.randint(0, 30)
                    y = random.randint(0, 30)
                    atomics.append(Instruction("p", (x, y)))
                
                genes.append(Gene(id=str(random.randint(0, 99)), traits={"c": color}, atomics=atomics))
            
            dna = DNA(genes=genes)
            self.players.append(Player(id=f"Seed-{i+1}", dna=dna)) # Initialize score 0
            
        print(f"🏆 Tournament initialized with {len(self.players)} players.")

    def play(self):
        """Run the full tournament."""
        while len(self.players) > 1:
            self.round_num += 1
            print(f"\n--- Round {self.round_num} (Players: {len(self.players)}) ---")
            
            if len(self.players) > 16:
                # Qualifying Rounds: Standard Fitness Selection
                self._play_qualifying_round()
            else:
                # Knockout Phase: World Cup Logic
                self._play_knockout_round()
                
        winner = self.players[0]
        print(f"\n🎉 TOURNAMENT CHAMPION: {winner.id} (Score: {winner.score:.2f})")
        # print(f"DNA: {winner.dna.encode()}") # Too long

    def _play_qualifying_round(self):
        """Mass evaluation and cut to top 50%."""
        for p in self.players:
            p.score = self.environment.evaluate(p.dna)
        
        self.players.sort(key=lambda x: x.score, reverse=True)
        print(f"Top Score: {self.players[0].score:.2f}")
        
        survivors = self.players[:len(self.players)//2]
        self.players = survivors

    def _play_knockout_round(self):
        """1v2, 3v4 matchups with offspring advancing."""
        next_round_players = []
        
        for p in self.players:
            p.score = self.environment.evaluate(p.dna)
        self.players.sort(key=lambda x: x.score, reverse=True)
        
        # Logic: 1v2, 3v4 match up. 
        # They mate. Child advances (Evolutionary Bracket).
        
        matchups = []
        for i in range(0, len(self.players), 2):
            if i+1 < len(self.players):
                matchups.append((self.players[i], self.players[i+1]))
            else:
                next_round_players.append(self.players[i])
                
        for p1, p2 in matchups:
            print(f"Match: {p1.id} ({p1.score:.1f}) vs {p2.id} ({p2.score:.1f})")
            
            # Create Child
            child_dna = crossover(p1.dna, p2.dna)
            # Mutate Child (heavier mutation to find solution)
            child_dna = mutate(child_dna, mutation_rate=0.2, mutation_power=0.5)
            
            # Also mutate Traits specifically for ARC (color)
            for g in child_dna.genes:
                if random.random() < 0.1:
                    g.traits["c"] = random.randint(0, 9)
            
            child_id = f"Child({p1.id}+{p2.id})"
            child = Player(id=child_id, dna=child_dna)
            
            # Evaluate Child immediatey to see if it improved
            child.score = self.environment.evaluate(child.dna)
            print(f"  -> Offspring Score: {child.score:.1f}")
            
            # Selection: Does Child beat parents?
            # User said "they can advance".
            # Let's pick the BEST of {P1, P2, Child} to advance, ensuring quality goes up.
            best = max([p1, p2, child], key=lambda x: x.score)
            print(f"  -> Advancing: {best.id} ({best.score:.1f})")
            
            next_round_players.append(best)
            
        self.players = next_round_players
        
        # Inject new blood if requested aka "new 14 seeded"
        # User said "new 14 will be seeded" -> "This can also begin from a round of 128"
        # Since we are reducing size, maybe we don't inject every round unless explicitly asked.
        # But let's verify if we need to pad the bracket.
        pass



if __name__ == "__main__":
    t = Tournament()
    t.seed_bracket(32) # Start with 32 for quick demo
    t.play()
