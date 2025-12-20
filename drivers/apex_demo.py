"""ApexVeil: Genetic Image Reproduction Demo using Tasc Atoms.

This driver demonstrates simulating genetic evolution to reproduce a target image.
It treats the image as a set of genes (color clusters) and evolves a population
to match the target.
"""

import sys
import random
import time
from typing import List, Tuple, Dict
from dataclasses import dataclass

# Mock image library usage to avoid dependencies for this core demo
# In a real app we might use PIL. Here we simulate infinite canvas.

from ab.atoms import DNA, Gene, Instruction
from ab.genetics import crossover, mutate, compute_similarity

# ---------------------------------------------------------------------------
# Image / Simulation Primitives
# ---------------------------------------------------------------------------

@dataclass
class Pixel:
    x: int
    y: int
    color: str  # Hex

class Canvas:
    """A virtual canvas for rendering DNA."""
    def __init__(self, width: int = 20, height: int = 20):
        self.width = width
        self.height = height
        self.pixels: Dict[Tuple[int, int], str] = {}
        
    def clear(self):
        self.pixels = {}
        
    def draw_pixel(self, x: int, y: int, color: str):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[(x, y)] = color
            
    def render_dna(self, dna: DNA):
        """Execute DNA instructions to paint the canvas."""
        for gene in dna.genes:
            # Gene-level trait: Color
            color = gene.traits.get("color", "#FFFFFF")
            
            for atom in gene.atomics:
                if atom.op_code == "p":
                    # Payload is (x, y)
                    x, y = atom.payload
                    self.draw_pixel(x, y, color)
                    
    def to_string(self) -> str:
        """ASCII art rendering of canvas."""
        lines = []
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                color = self.pixels.get((x, y), None)
                if color:
                    # Simple mapping for demo: assume predefined colors or just hash char
                    line += "#" 
                else:
                    line += "."
            lines.append(line)
        return "\n".join(lines)

    def diff(self, target: "Canvas") -> int:
        """Compute pixel difference score (lower is better)."""
        score = 0
        # Check every coordinate
        for y in range(self.height):
            for x in range(self.width):
                color_self = self.pixels.get((x, y))
                color_target = target.pixels.get((x, y))
                
                if color_self != color_target:
                    score += 1
        return score


# ---------------------------------------------------------------------------
# Demo Logic
# ---------------------------------------------------------------------------

class ApexVeilDemo:
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        self.target_canvas = Canvas(width, height)
        self.population: List[DNA] = []
        
        # Create a simple target pattern (a cross)
        self._create_target_pattern()
        
    def _create_target_pattern(self):
        # Draw a cross
        c = "#FF0000"
        mid_x = self.width // 2
        mid_y = self.height // 2
        
        # Horizontal line
        for x in range(self.width):
            self.target_canvas.draw_pixel(x, mid_y, c)
            
        # Vertical line
        for y in range(self.height):
            self.target_canvas.draw_pixel(mid_x, y, c)
            
    def init_population(self, size: int = 10):
        """Create random initial population."""
        self.population = []
        for _ in range(size):
            # Create a random DNA with 1 gene and random pixels
            gene = Gene(id="0", traits={"color": "#FF0000"})
            for _ in range(5):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                gene.atomics.append(Instruction("p", (x, y)))
                
            self.population.append(DNA(genes=[gene]))
            
    def evolve(self, generations: int = 20):
        """Run evolutionary loop."""
        print(f"Target:\n{self.target_canvas.to_string()}\n")
        
        for gen in range(1, generations + 1):
            # 1. Evaluate Fitness
            scored_pop = []
            for dna in self.population:
                canvas = Canvas(self.width, self.height)
                canvas.render_dna(dna)
                score = canvas.diff(self.target_canvas)
                scored_pop.append((dna, score))
                
            # Sort by score (ascending, lower diff is better)
            scored_pop.sort(key=lambda x: x[1])
            
            best_dna, best_score = scored_pop[0]
            
            # Print progress
            if gen % 5 == 0 or gen == 1:
                print(f"Gen {gen}: Best Score = {best_score} / {self.width * self.height}")
                
            if best_score == 0:
                print(f"🎉 Perfect match found at Gen {gen}!")
                break
                
            # 2. Select (Elitism + Parents)
            survivors = scored_pop[:len(scored_pop)//2] # Top 50%
            
            # 3. Reproduce & Mutate
            new_pop = [x[0] for x in survivors] # Keep survivors
            
            while len(new_pop) < len(self.population):
                # Pick two parents randomly from survivors
                parent_a = random.choice(survivors)[0]
                parent_b = random.choice(survivors)[0]
                
                # Crossover
                child = crossover(parent_a, parent_b)
                
                # Mutate
                child = mutate(child, mutation_rate=0.2, mutation_power=0.5)
                
                new_pop.append(child)
                
            self.population = new_pop
            
        print("\nFinal Result (Best):")
        final_canvas = Canvas(self.width, self.height)
        final_canvas.render_dna(self.population[0])
        print(final_canvas.to_string())
        
        print("\nFinal DNA String:")
        print(self.population[0].encode())


if __name__ == "__main__":
    demo = ApexVeilDemo(width=10, height=10)
    demo.init_population(size=20)
    demo.evolve(generations=50)
