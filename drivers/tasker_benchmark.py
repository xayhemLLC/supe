"""TaskerNet Benchmark Suite: Test evolved networks across problem domains.

Tests mathematical, classification, sequence, memory, and Codewars-style problems.
Tracks which architectures excel at which domains.
"""

import sys
sys.path.insert(0, ".")

from typing import List, Dict, Tuple, Any
from dataclasses import dataclass, field
import time

from ab.tasker_net import TaskerNet, TaskerDNA, TaskerTournament, TaskerPlayer, crossover_dna


# ---------------------------------------------------------------------------
# Problem Definitions
# ---------------------------------------------------------------------------

@dataclass
class Problem:
    """A test problem with input/output pairs."""
    name: str
    category: str
    test_cases: List[Tuple[float, float]]
    description: str = ""


# Math Problems
MATH_PROBLEMS = [
    Problem(
        name="double",
        category="math",
        description="Return 2x",
        test_cases=[(1, 2), (2, 4), (3, 6), (5, 10), (-2, -4), (0, 0)]
    ),
    Problem(
        name="square",
        category="math",
        description="Return x²",
        test_cases=[(2, 4), (3, 9), (4, 16), (-2, 4), (0, 0), (5, 25)]
    ),
    Problem(
        name="cube",
        category="math",
        description="Return x³",
        test_cases=[(2, 8), (3, 27), (-2, -8), (1, 1), (0, 0)]
    ),
    Problem(
        name="add_ten",
        category="math",
        description="Return x + 10",
        test_cases=[(0, 10), (5, 15), (-10, 0), (100, 110)]
    ),
]

# Classification Problems
CLASSIFICATION_PROBLEMS = [
    Problem(
        name="is_positive",
        category="classification",
        description="Return 1 if x > 0, else 0",
        test_cases=[(5, 1), (-3, 0), (0, 0), (100, 1), (-0.5, 0)]
    ),
    Problem(
        name="is_even",
        category="classification",
        description="Return 1 if x is even (mod 2 = 0)",
        test_cases=[(2, 1), (3, 0), (4, 1), (7, 0), (0, 1), (-2, 1)]
    ),
    Problem(
        name="sign",
        category="classification",
        description="Return -1, 0, or 1 based on sign",
        test_cases=[(5, 1), (-3, -1), (0, 0), (100, 1), (-0.5, -1)]
    ),
]

# Sequence/Aggregate Problems (simplified to single number for now)
SEQUENCE_PROBLEMS = [
    Problem(
        name="clamp_to_10",
        category="sequence",
        description="Clamp x to max 10",
        test_cases=[(5, 5), (15, 10), (0, 0), (10, 10), (100, 10)]
    ),
    Problem(
        name="abs_value",
        category="sequence",
        description="Return absolute value",
        test_cases=[(5, 5), (-5, 5), (0, 0), (-100, 100), (3.5, 3.5)]
    ),
    Problem(
        name="floor_div_2",
        category="sequence",
        description="Return x // 2 (integer division)",
        test_cases=[(10, 5), (7, 3), (0, 0), (1, 0), (100, 50)]
    ),
]

# Codewars-Style Problems (simplified numeric versions)
CODEWARS_PROBLEMS = [
    Problem(
        name="fizzbuzz_mod",
        category="codewars",
        description="Return x%15 (FizzBuzz-like modulo)",
        test_cases=[(15, 0), (30, 0), (7, 7), (10, 10), (3, 3)]
    ),
    Problem(
        name="digit_sum_approx",
        category="codewars",
        description="Return x % 9 (digit sum approximation)",
        test_cases=[(18, 0), (19, 1), (27, 0), (5, 5), (123, 6)]
    ),
]

ALL_PROBLEMS = MATH_PROBLEMS + CLASSIFICATION_PROBLEMS + SEQUENCE_PROBLEMS + CODEWARS_PROBLEMS


# ---------------------------------------------------------------------------
# Benchmark Runner
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkResult:
    """Result of benchmarking on a problem category."""
    category: str
    best_fitness: float
    best_architecture: str
    avg_fitness: float
    problems_solved: int
    total_problems: int
    evolution_time_s: float


class TaskerBenchmark:
    """Run TaskerNet evolution across multiple problem domains."""
    
    def __init__(self, population_size: int = 32, generations: int = 10):
        self.pop_size = population_size
        self.generations = generations
        self.results: Dict[str, BenchmarkResult] = {}
        self.specialists: Dict[str, TaskerPlayer] = {}  # Best player per category
        
    def run_category(self, problems: List[Problem]) -> BenchmarkResult:
        """Run evolution on a category of problems."""
        if not problems:
            return BenchmarkResult("empty", 0, "", 0, 0, 0, 0)
        
        category = problems[0].category
        
        # Combine all test cases from problems in this category
        all_test_cases = []
        for p in problems:
            all_test_cases.extend(p.test_cases)
        
        # Create tournament
        tournament = TaskerTournament(problems=all_test_cases)
        tournament.seed_population(self.pop_size)
        
        start_time = time.time()
        
        # Evolve
        for _ in range(self.generations):
            tournament.run_generation()
        
        elapsed = time.time() - start_time
        
        # Final evaluation
        for p in tournament.players:
            tournament.evaluate_player(p)
        tournament.players.sort(key=lambda x: x.fitness, reverse=True)
        
        best = tournament.players[0]
        avg_fitness = sum(p.fitness for p in tournament.players) / len(tournament.players)
        
        # Count "solved" problems (fitness > threshold)
        solved = sum(1 for p in tournament.players if p.fitness > 50)
        
        # Store specialist
        self.specialists[category] = best
        
        # Describe architecture
        net = TaskerNet(best.dna)
        arch_desc = f"{net.node_count()} nodes, {best.dna.structure.branching_factor} branching"
        
        return BenchmarkResult(
            category=category,
            best_fitness=best.fitness,
            best_architecture=arch_desc,
            avg_fitness=avg_fitness,
            problems_solved=solved,
            total_problems=len(problems),
            evolution_time_s=elapsed
        )
    
    def run_all(self):
        """Run benchmark on all problem categories."""
        categories = {
            "math": MATH_PROBLEMS,
            "classification": CLASSIFICATION_PROBLEMS,
            "sequence": SEQUENCE_PROBLEMS,
            "codewars": CODEWARS_PROBLEMS,
        }
        
        print("=" * 70)
        print("TASKERNET BENCHMARK SUITE")
        print("=" * 70)
        print(f"Population: {self.pop_size} | Generations: {self.generations}")
        print("=" * 70)
        
        for cat_name, problems in categories.items():
            print(f"\n--- Running {cat_name.upper()} ---")
            result = self.run_category(problems)
            self.results[cat_name] = result
            
            print(f"  Best Fitness: {result.best_fitness:.2f}")
            print(f"  Architecture: {result.best_architecture}")
            print(f"  Avg Fitness: {result.avg_fitness:.2f}")
            print(f"  Time: {result.evolution_time_s:.2f}s")
        
        self.print_summary()
    
    def print_summary(self):
        """Print benchmark summary."""
        print("\n" + "=" * 70)
        print("BENCHMARK SUMMARY")
        print("=" * 70)
        
        print(f"\n{'Category':<15} {'Best Fit':>10} {'Avg Fit':>10} {'Architecture':<25} {'Time':>8}")
        print("-" * 70)
        
        for cat, result in self.results.items():
            print(f"{cat:<15} {result.best_fitness:>10.2f} {result.avg_fitness:>10.2f} {result.best_architecture:<25} {result.evolution_time_s:>7.2f}s")
        
        # Find best overall category
        if self.results:
            best_cat = max(self.results.items(), key=lambda x: x[1].best_fitness)
            print(f"\n🏆 Best Category: {best_cat[0]} (Fitness: {best_cat[1].best_fitness:.2f})")
    
    def test_specialist(self, category: str, test_input: float) -> float:
        """Test a specialist network on an input."""
        if category not in self.specialists:
            return 0.0
        
        net = TaskerNet(self.specialists[category].dna)
        return net.forward(test_input)


# ---------------------------------------------------------------------------
# Cross-Domain Analysis
# ---------------------------------------------------------------------------

def cross_domain_test(benchmark: TaskerBenchmark):
    """Test each specialist on other domains."""
    print("\n" + "=" * 70)
    print("CROSS-DOMAIN ANALYSIS")
    print("=" * 70)
    print("(Testing each specialist on problems from other domains)")
    
    all_cats = list(benchmark.specialists.keys())
    
    for specialist_cat in all_cats:
        if specialist_cat not in benchmark.specialists:
            continue
        
        specialist = benchmark.specialists[specialist_cat]
        net = TaskerNet(specialist.dna)
        
        print(f"\n{specialist_cat.upper()} Specialist:")
        
        for test_cat, problems in [("math", MATH_PROBLEMS), ("classification", CLASSIFICATION_PROBLEMS)]:
            if test_cat == specialist_cat:
                continue
            
            total_error = 0
            for p in problems[:2]:  # Test on first 2 problems
                for inp, exp in p.test_cases[:2]:
                    out = net.forward(inp)
                    total_error += abs(out - exp)
            
            print(f"  → on {test_cat}: avg error = {total_error/4:.2f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    bench = TaskerBenchmark(population_size=24, generations=12)
    bench.run_all()
    cross_domain_test(bench)
    
    print("\n" + "=" * 70)
    print("Done! Use bench.test_specialist('math', 5) to query specialists.")
    print("=" * 70)
