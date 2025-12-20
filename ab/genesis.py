"""Genesis: Self-Evolving AI System.

Combines three revolutionary concepts:
A) PersonalCoder - Evolves to match YOUR coding style
B) MetaEvolution - Evolves the evolution process itself
C) SelfModifyingTasc - AI writes its own upgrades

This is the most advanced module in the Tasc framework.
"""

import sys
sys.path.insert(0, ".")

import random
import copy
import time
from typing import List, Dict, Callable, Any, Tuple, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from ab.tasker_net import TaskerNet, TaskerDNA, TaskerPlayer, crossover_dna
from ab.energy import EnergyNetwork
from ab.code_dna import CodeDNA, CodeGene, CodeInstruction, OpCode, create_random_code_dna, mutate_code


# ===========================================================================
# PART A: PersonalCoder - Evolves to Code Like You
# ===========================================================================

@dataclass
class CodingPattern:
    """A pattern learned from your corrections."""
    description: str
    pattern_type: str  # "prefer", "avoid", "style"
    weight: float = 1.0
    examples: List[str] = field(default_factory=list)


class PersonalCoder:
    """An AI coder that evolves to match YOUR coding style.
    
    Records your corrections, evolves specialists, and personalizes
    its suggestions based on what you've taught it.
    """
    
    def __init__(self):
        self.brain = TaskerDNA.random(num_nodes=5)
        self.patterns: List[CodingPattern] = []
        self.correction_history: List[Dict[str, Any]] = []
        self.energy_net = EnergyNetwork()
        self.generation = 0
        
        # Initialize energy nodes for different strategies
        self.strategies = ["simple", "verbose", "functional", "oop", "defensive"]
        for s in self.strategies:
            self.energy_net.add_node(s, initial_energy=20.0)
        
        # Connect them all
        for i, s1 in enumerate(self.strategies):
            for s2 in self.strategies[i+1:]:
                self.energy_net.connect(s1, s2)
    
    def suggest_approach(self, problem_description: str) -> str:
        """Suggest a coding approach based on evolved preferences."""
        # Select strategy based on energy
        strategy = self.energy_net.select_by_energy(self.strategies)
        
        approaches = {
            "simple": "Use minimal code, avoid complexity",
            "verbose": "Use clear variable names, add comments",
            "functional": "Use map/filter/reduce, avoid state",
            "oop": "Create classes, encapsulate logic",
            "defensive": "Add error handling, validate inputs",
        }
        
        return f"[{strategy.upper()}] {approaches[strategy]}"
    
    def record_correction(self, ai_suggestion: str, your_fix: str, feedback: str = ""):
        """Learn from your correction."""
        self.correction_history.append({
            "ai": ai_suggestion,
            "human": your_fix,
            "feedback": feedback,
            "timestamp": time.time()
        })
        
        # Analyze the correction to update patterns
        if "simpl" in your_fix.lower() or len(your_fix) < len(ai_suggestion) * 0.7:
            self.energy_net.inject_energy("simple", 30.0)
            self.patterns.append(CodingPattern("Prefer simpler solutions", "prefer", 1.0))
        
        if "class " in your_fix.lower():
            self.energy_net.inject_energy("oop", 25.0)
        
        if "try:" in your_fix.lower() or "except" in your_fix.lower():
            self.energy_net.inject_energy("defensive", 20.0)
        
        if "lambda" in your_fix.lower() or "map(" in your_fix.lower():
            self.energy_net.inject_energy("functional", 25.0)
        
        # Diffuse the learning
        self.energy_net.run_diffusion(3)
        
        # Maybe evolve the brain
        if len(self.correction_history) % 5 == 0:
            self._evolve()
    
    def _evolve(self):
        """Evolve the brain based on corrections."""
        self.generation += 1
        self.brain.mutate(rate=0.2)
        print(f"🧬 PersonalCoder evolved to generation {self.generation}")
    
    def get_style_profile(self) -> Dict[str, float]:
        """Get current learned style preferences."""
        return self.energy_net.get_energy_distribution()
    
    def status(self) -> str:
        """Get status report."""
        lines = [
            f"PersonalCoder Status:",
            f"  Generation: {self.generation}",
            f"  Patterns learned: {len(self.patterns)}",
            f"  Corrections recorded: {len(self.correction_history)}",
            f"\nStyle Profile:",
        ]
        for strategy, energy in self.get_style_profile().items():
            bar = "█" * int(energy / 5)
            lines.append(f"  {strategy:12} [{energy:5.1f}] {bar}")
        return "\n".join(lines)


# ===========================================================================
# PART B: MetaEvolution - Evolves the Evolution Process
# ===========================================================================

@dataclass
class MutationOperator:
    """A mutation operator that can itself be evolved."""
    name: str
    rate: float = 0.1  # Probability of application
    power: float = 0.3  # Strength of mutation
    target: str = "all"  # What to mutate: "weights", "structure", "behavior"
    
    def apply(self, dna: TaskerDNA) -> TaskerDNA:
        """Apply this mutation operator to DNA."""
        new_dna = copy.deepcopy(dna)
        
        if self.target in ["weights", "all"]:
            new_dna.weights.mutate(self.rate, self.power)
        
        if self.target in ["structure", "all"]:
            new_dna.structure.mutate(self.rate)
        
        if self.target in ["behavior", "all"]:
            for b in new_dna.behaviors.values():
                b.mutate(self.rate)
        
        return new_dna
    
    def mutate_self(self):
        """Mutate THIS operator (meta-mutation)."""
        self.rate = max(0.01, min(0.5, self.rate + random.gauss(0, 0.05)))
        self.power = max(0.05, min(1.0, self.power + random.gauss(0, 0.1)))
        self.target = random.choice(["weights", "structure", "behavior", "all"])


class MetaEvolution:
    """Evolves the evolution process itself.
    
    Level 0: Evolve solutions
    Level 1: Evolve network architectures  
    Level 2: Evolve the mutation operators
    Level 3: Evolve the fitness function
    """
    
    def __init__(self):
        # Population of mutation operators
        self.operators: List[MutationOperator] = [
            MutationOperator("gentle", rate=0.05, power=0.1, target="weights"),
            MutationOperator("aggressive", rate=0.3, power=0.5, target="all"),
            MutationOperator("structural", rate=0.2, power=0.3, target="structure"),
            MutationOperator("behavioral", rate=0.15, power=0.2, target="behavior"),
        ]
        
        # Track operator performance
        self.operator_scores: Dict[str, List[float]] = {op.name: [] for op in self.operators}
        self.generation = 0
        
        # Fitness function weights (can also evolve!)
        self.fitness_weights = {
            "accuracy": 1.0,
            "simplicity": 0.1,
            "novelty": 0.05,
        }
    
    def select_operator(self) -> MutationOperator:
        """Select mutation operator based on past performance."""
        # Thompson sampling: sample from beta distribution based on successes
        scores = []
        for op in self.operators:
            history = self.operator_scores[op.name]
            if len(history) < 3:
                score = random.random()
            else:
                avg = sum(history[-10:]) / len(history[-10:])
                score = avg + random.gauss(0, 0.1)
            scores.append(score)
        
        best_idx = scores.index(max(scores))
        return self.operators[best_idx]
    
    def report_result(self, operator_name: str, fitness_improvement: float):
        """Report how well an operator did."""
        if operator_name in self.operator_scores:
            self.operator_scores[operator_name].append(fitness_improvement)
    
    def evolve_operators(self):
        """Meta-evolve: mutate the mutation operators themselves."""
        self.generation += 1
        
        # Find best and worst performers
        avg_scores = {}
        for name, scores in self.operator_scores.items():
            if scores:
                avg_scores[name] = sum(scores[-10:]) / len(scores[-10:])
            else:
                avg_scores[name] = 0.0
        
        if not avg_scores:
            return
        
        best_name = max(avg_scores, key=avg_scores.get)
        worst_name = min(avg_scores, key=avg_scores.get)
        
        # Clone best, replace worst
        best_op = next(op for op in self.operators if op.name == best_name)
        for i, op in enumerate(self.operators):
            if op.name == worst_name:
                # Create mutated clone of best
                new_op = copy.deepcopy(best_op)
                new_op.name = f"evolved_{self.generation}"
                new_op.mutate_self()
                self.operators[i] = new_op
                self.operator_scores[new_op.name] = []
                print(f"🔄 Meta-evolved: {worst_name} → {new_op.name}")
                break
    
    def evolve_fitness_weights(self, improvement_rate: float):
        """Evolve the fitness function weights."""
        if improvement_rate > 0.1:  # Things are improving
            # Slightly increase what we're emphasizing
            pass
        else:  # Stagnating
            # Try more novelty
            self.fitness_weights["novelty"] = min(0.5, self.fitness_weights["novelty"] * 1.2)
    
    def status(self) -> str:
        lines = [f"MetaEvolution (Gen {self.generation}):"]
        for op in self.operators:
            scores = self.operator_scores.get(op.name, [])
            avg = sum(scores[-5:]) / len(scores[-5:]) if scores else 0
            lines.append(f"  {op.name}: rate={op.rate:.2f} power={op.power:.2f} → avg={avg:.2f}")
        return "\n".join(lines)


# ===========================================================================
# PART C: SelfModifyingTasc - AI Writes Its Own Upgrades
# ===========================================================================

@dataclass
class UpgradeProposal:
    """A proposed upgrade to the system."""
    title: str
    code: str
    target_file: str
    rationale: str
    confidence: float  # 0-1
    tested: bool = False
    approved: bool = False


class SelfModifyingTasc:
    """An AI that proposes and writes its own upgrades.
    
    When it detects a limitation or pattern, it generates code
    to upgrade itself and proposes it for review.
    """
    
    def __init__(self):
        self.upgrade_proposals: List[UpgradeProposal] = []
        self.applied_upgrades: List[str] = []
        self.known_limitations: List[str] = []
        self.meta_dna = TaskerDNA.random(num_nodes=3)
    
    def detect_limitation(self, performance_data: Dict[str, float]):
        """Detect limitations from performance metrics."""
        limitations = []
        
        if performance_data.get("accuracy", 1.0) < 0.5:
            limitations.append("Low accuracy - need better representation")
        
        if performance_data.get("speed", 1.0) < 0.3:
            limitations.append("Too slow - need optimization")
        
        if performance_data.get("diversity", 1.0) < 0.2:
            limitations.append("Low diversity - need more exploration")
        
        self.known_limitations.extend(limitations)
        return limitations
    
    def propose_upgrade(self, limitation: str) -> Optional[UpgradeProposal]:
        """Generate a code upgrade proposal to address a limitation."""
        
        # Template-based upgrade generation
        upgrades = {
            "Low accuracy": UpgradeProposal(
                title="Add Layer Depth",
                code="""
# Upgrade: Increase network depth for better accuracy
def enhanced_forward(self, x):
    for _ in range(2):  # Double the depth
        x = self.layer(x)
    return x
""",
                target_file="ab/tasker_net.py",
                rationale="Deeper networks can capture more complex patterns",
                confidence=0.7
            ),
            "Too slow": UpgradeProposal(
                title="Add Caching",
                code="""
# Upgrade: Cache repeated computations
_cache = {}
def cached_forward(self, x, cache_key=None):
    if cache_key and cache_key in _cache:
        return _cache[cache_key]
    result = self.forward(x)
    if cache_key:
        _cache[cache_key] = result
    return result
""",
                target_file="ab/tasker_net.py",
                rationale="Caching avoids redundant computation",
                confidence=0.8
            ),
            "Low diversity": UpgradeProposal(
                title="Add Novelty Search",
                code="""
# Upgrade: Reward novel solutions
def novelty_bonus(self, new_solution, archive):
    distances = [distance(new_solution, s) for s in archive]
    return sum(sorted(distances)[:5]) / 5  # Avg distance to 5 nearest
""",
                target_file="ab/genesis.py",
                rationale="Novelty search encourages exploration",
                confidence=0.6
            ),
        }
        
        for key, upgrade in upgrades.items():
            if key in limitation:
                self.upgrade_proposals.append(upgrade)
                return upgrade
        
        return None
    
    def approve_upgrade(self, proposal: UpgradeProposal):
        """Mark an upgrade as approved (would apply in production)."""
        proposal.approved = True
        self.applied_upgrades.append(proposal.title)
        print(f"✅ Upgrade approved: {proposal.title}")
    
    def status(self) -> str:
        lines = [
            "SelfModifyingTasc Status:",
            f"  Known limitations: {len(self.known_limitations)}",
            f"  Proposed upgrades: {len(self.upgrade_proposals)}",
            f"  Applied upgrades: {len(self.applied_upgrades)}",
        ]
        
        if self.upgrade_proposals:
            lines.append("\nPending Proposals:")
            for p in self.upgrade_proposals[-3:]:
                status = "✅" if p.approved else "⏳"
                lines.append(f"  {status} {p.title} (conf: {p.confidence:.0%})")
        
        return "\n".join(lines)


# ===========================================================================
# UNIFIED SYSTEM: Genesis
# ===========================================================================

class Genesis:
    """The unified self-evolving AI system.
    
    Combines:
    - PersonalCoder (A): Learns YOUR style
    - MetaEvolution (B): Evolves the evolution
    - SelfModifyingTasc (C): Writes its own upgrades
    """
    
    def __init__(self):
        self.personal = PersonalCoder()
        self.meta = MetaEvolution()
        self.self_mod = SelfModifyingTasc()
        self.cycle_count = 0
    
    def run_evolution_cycle(self, problem: Tuple[float, float]) -> Dict[str, Any]:
        """Run one complete evolution cycle combining all three systems."""
        self.cycle_count += 1
        
        # A: Get personalized approach
        approach = self.personal.suggest_approach(f"Solve: {problem}")
        
        # B: Select mutation operator via meta-evolution
        operator = self.meta.select_operator()
        
        # Create and evolve a solution
        dna = TaskerDNA.random(num_nodes=3)
        mutated_dna = operator.apply(dna)
        
        # Evaluate
        net = TaskerNet(mutated_dna)
        result = net.forward(problem[0])
        error = abs(result - problem[1])
        fitness = 100.0 / (1.0 + error)
        
        # Report back to meta-evolution
        improvement = fitness - 50  # Baseline improvement
        self.meta.report_result(operator.name, improvement)
        
        # C: Check for limitations and propose upgrades
        perf = {"accuracy": 1.0 / (1.0 + error), "speed": 1.0, "diversity": 0.5}
        limitations = self.self_mod.detect_limitation(perf)
        
        for lim in limitations[:1]:  # Process first limitation
            self.self_mod.propose_upgrade(lim)
        
        # Periodically meta-evolve
        if self.cycle_count % 10 == 0:
            self.meta.evolve_operators()
        
        return {
            "cycle": self.cycle_count,
            "approach": approach,
            "operator": operator.name,
            "fitness": fitness,
            "result": result,
            "expected": problem[1],
            "error": error
        }
    
    def full_status(self) -> str:
        """Get status of all three systems."""
        return "\n\n".join([
            "=" * 60,
            "GENESIS: SELF-EVOLVING AI SYSTEM",
            "=" * 60,
            self.personal.status(),
            "-" * 40,
            self.meta.status(),
            "-" * 40,
            self.self_mod.status(),
            "=" * 60
        ])


# ===========================================================================
# DEMO
# ===========================================================================

def demo():
    print("=" * 60)
    print("🧬 GENESIS: The Self-Evolving AI System")
    print("=" * 60)
    
    genesis = Genesis()
    
    # Demo problems
    problems = [
        (2, 4),   # Double
        (3, 9),   # Square
        (5, 10),  # Double
        (-2, 4),  # Square
        (0, 0),   # Zero
    ]
    
    print("\n--- Running 20 Evolution Cycles ---\n")
    
    for i in range(20):
        problem = random.choice(problems)
        result = genesis.run_evolution_cycle(problem)
        
        if i % 5 == 0:
            print(f"Cycle {result['cycle']:2d}: [{result['operator']:12}] "
                  f"f({problem[0]})={result['result']:6.2f} "
                  f"(expected {problem[1]}, err={result['error']:.2f})")
    
    # Simulate user corrections
    print("\n--- Simulating User Corrections ---\n")
    corrections = [
        ("def solve(x): return x*x+x*x", "def solve(x): return 2*x*x"),  # Simpler
        ("class Solution:\n  def run(self):", "def run():"),  # No OOP
    ]
    
    for ai, human in corrections:
        genesis.personal.record_correction(ai, human)
    
    print(genesis.full_status())
    
    # Show pending upgrade proposal
    if genesis.self_mod.upgrade_proposals:
        print("\n--- Sample Upgrade Proposal ---")
        proposal = genesis.self_mod.upgrade_proposals[0]
        print(f"Title: {proposal.title}")
        print(f"Rationale: {proposal.rationale}")
        print(f"Confidence: {proposal.confidence:.0%}")
        print(f"Code:\n{proposal.code[:200]}...")


if __name__ == "__main__":
    demo()
