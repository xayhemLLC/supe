"""Tournament driver for Neuro-Genetic evolution on ARC."""

import random
from typing import List, Tuple
from dataclasses import dataclass

from ab.atoms import DNA, Gene, Instruction
from ab.genetics import crossover, mutate
from ab.neural import NeuralNetwork
from tascer.drivers.tournament import Tournament, ARCEnvironment, Player

# Subclass Tournament to use Neural Logic
class NeuroTournament(Tournament):
    
    def seed_bracket(self, size: int = 64):
        """Create population of Neural Networks."""
        self.players = []
        for i in range(size):
            # We don't need to manually create genes with weights.
            # NeuralNetwork class inits random if genes missing.
            # So we create empty DNA with correct IDs.
            genes = [Gene(id="0"), Gene(id="1"), Gene(id="2")]
            dna = DNA(genes=genes)
            
            # Create a NeuralNetwork to initialize the random weights
            # and then SAVE them back to the DNA.
            # Input: x,y,color? 
            # Or Flattened Grid?
            # ARC grids vary in size.
            # New approach: NEURAL CELLULAR AUTOMATA (NCA) style?
            # Or Local Kernel?
            # For simplicity: Pixel-wise predictor.
            # Input: (x, y, normalized_x, normalized_y) + neighbors?
            # Let's try simple: (x, y) -> Color Class Probabilities (10)
            
            nn = NeuralNetwork(dna, input_size=2, output_size=10)
            
            # Serialize back to DNA
            genes_with_weights = [
                nn.layers[0].to_gene("0"),
                nn.layers[1].to_gene("1"),
                nn.layers[2].to_gene("2")
            ]
            
            full_dna = DNA(genes=genes_with_weights)
            self.players.append(Player(id=f"NeuroSeed-{i+1}", dna=full_dna))
            
        print(f"🧠 Neuro-Tournament initialized with {len(self.players)} Neural Agents.")

    def evaluate_player(self, player: Player):
        """Run Neural Net on ARC task."""
        if not self.environment.train_pairs:
            player.score = 0
            return

        target_grid = self.environment.train_pairs[0]["output"]
        height = len(target_grid)
        width = len(target_grid[0])
        
        # Instantiate NN from DNA
        nn = NeuralNetwork(player.dna, input_size=2, output_size=10)
        
        score = 0
        total = width * height
        
        # Pixel-wise prediction
        for y in range(height):
            for x in range(width):
                # Input: Normalized coordinates
                input_vec = [x / width, y / height]
                
                # Output: Logits for 10 colors
                logits = nn.predict(input_vec)
                
                # Argmax
                predicted_color = logits.index(max(logits))
                
                if predicted_color == target_grid[y][x]:
                    score += 1
                    
        player.score = (score / total) * 100.0

    # Override play rounds to use custom evaluate
    def _play_qualifying_round(self):
        for p in self.players:
            self.evaluate_player(p)
        self.players.sort(key=lambda x: x.score, reverse=True)
        print(f"Top Neural Score: {self.players[0].score:.2f}")
        self.players = self.players[:len(self.players)//2]

    def _play_knockout_round(self):
        # Neural Mutation Parameters need to be tuned.
        # mutation_power determines how much weights shift.
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
            print(f"Match: {p1.id} ({p1.score:.1f}) vs {p2.id} ({p2.score:.1f})")
            
            # Sexual Reproduction of Neural Nets!
            # Crossover swaps entire layers (Genes) or weights?
            # Our crossover() function swaps Genes.
            # Since Gene = Layer, this means Child has Layer 1 from Mom, Layer 2 from Dad.
            # This is "Layer-wise Crossover".
            
            child_dna = crossover(p1.dna, p2.dna)
            
            # Mutate weights slightly (Backprop via evolution)
            # mutation_power=0.1 means weights shift by ~10% standard deviation equivalent
            child_dna = mutate(child_dna, mutation_rate=0.05, mutation_power=0.1)
            
            child_id = f"Child({p1.id}+{p2.id})"
            child = Player(id=child_id, dna=child_dna)
            
            self.evaluate_player(child)
            print(f"  -> Offspring Score: {child.score:.1f}")
            
            best = max([p1, p2, child], key=lambda x: x.score)
            next_round.append(best)
            
        self.players = next_round


if __name__ == "__main__":
    t = NeuroTournament()
    t.seed_bracket(32)
    t.play()
