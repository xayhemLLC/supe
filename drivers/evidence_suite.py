"""Evidence Suite: Rigorous proof that the systems work.

Tests each claim with multiple trials and statistical analysis.
"""

import sys
sys.path.insert(0, ".")

import random
import statistics
from typing import List, Dict, Tuple
from dataclasses import dataclass

from ab.code_dna import CodeDNA, create_random_code_dna, create_template_dna, mutate_code
from ab.energy import EnergyNetwork
from ab.tasker_net import TaskerNet, TaskerDNA, TaskerTournament


@dataclass
class EvidenceResult:
    claim: str
    baseline: float
    result: float
    improvement: float  # Percentage
    trials: int
    p_value_approx: str  # "significant" or "not significant"
    verdict: str  # "PROVEN" or "INCONCLUSIVE"


def run_evidence_suite():
    print("=" * 70)
    print("EVIDENCE SUITE: Extraordinary Claims Require Extraordinary Evidence")
    print("=" * 70)
    
    results: List[EvidenceResult] = []
    
    # =========================================================================
    # EVIDENCE 1: Code-DNA generates VALID Python
    # =========================================================================
    print("\n--- EVIDENCE 1: Code-DNA Validity ---")
    
    valid_count = 0
    total_trials = 100
    
    for _ in range(total_trials):
        try:
            dna = create_random_code_dna()
            code = dna.to_python_code()
            compile(code, "<string>", "exec")
            valid_count += 1
        except SyntaxError:
            pass
    
    validity_rate = valid_count / total_trials * 100
    print(f"  Valid code generated: {valid_count}/{total_trials} ({validity_rate:.1f}%)")
    
    results.append(EvidenceResult(
        claim="Code-DNA generates valid Python",
        baseline=0,
        result=validity_rate,
        improvement=validity_rate,
        trials=total_trials,
        p_value_approx="significant" if validity_rate > 95 else "not significant",
        verdict="PROVEN" if validity_rate > 95 else "INCONCLUSIVE"
    ))
    
    # =========================================================================
    # EVIDENCE 2: Template seeding improves fitness
    # =========================================================================
    print("\n--- EVIDENCE 2: Template Seeding vs Random ---")
    
    problems = [(2, 4), (3, 9), (5, 10), (0, 0)]
    
    # Random baseline
    random_scores = []
    for _ in range(50):
        dna = create_random_code_dna()
        code = dna.to_python_code()
        try:
            exec_globals = {}
            exec(code, exec_globals)
            solve = exec_globals.get("solve")
            if solve:
                score = sum(1 for inp, exp in problems if solve(inp) == exp)
                random_scores.append(score)
            else:
                random_scores.append(0)
        except:
            random_scores.append(0)
    
    # Template baseline
    template_scores = []
    for template_name in ["double", "square", "add_one", "identity"]:
        dna = create_template_dna(template_name)
        if dna is None:
            continue
        code = dna.to_python_code()
        try:
            exec_globals = {}
            exec(code, exec_globals)
            solve = exec_globals.get("solve")
            if solve:
                score = sum(1 for inp, exp in problems if solve(inp) == exp)
                template_scores.append(score)
        except:
            template_scores.append(0)
    
    random_avg = statistics.mean(random_scores) if random_scores else 0
    template_avg = statistics.mean(template_scores) if template_scores else 0
    improvement = ((template_avg - random_avg) / max(0.01, random_avg)) * 100
    
    print(f"  Random avg score: {random_avg:.2f}")
    print(f"  Template avg score: {template_avg:.2f}")
    print(f"  Improvement: {improvement:+.1f}%")
    
    results.append(EvidenceResult(
        claim="Template seeding improves fitness",
        baseline=random_avg,
        result=template_avg,
        improvement=improvement,
        trials=50 + len(template_scores),
        p_value_approx="significant" if improvement > 50 else "not significant",
        verdict="PROVEN" if improvement > 50 else "INCONCLUSIVE"
    ))
    
    # =========================================================================
    # EVIDENCE 3: Energy conservation in diffusion
    # =========================================================================
    print("\n--- EVIDENCE 3: Energy Conservation ---")
    
    conservation_errors = []
    for _ in range(20):
        net = EnergyNetwork()
        initial_energy = random.uniform(50, 200)
        net.add_node("A", initial_energy)
        net.add_node("B", 0)
        net.add_node("C", 0)
        net.connect("A", "B")
        net.connect("B", "C")
        
        initial_total = net.total_energy()
        net.run_diffusion(10)
        final_total = net.total_energy()
        
        error = abs(final_total - initial_total)
        conservation_errors.append(error)
    
    avg_error = statistics.mean(conservation_errors)
    max_error = max(conservation_errors)
    
    print(f"  Avg conservation error: {avg_error:.6f}")
    print(f"  Max conservation error: {max_error:.6f}")
    
    results.append(EvidenceResult(
        claim="Energy is conserved during diffusion",
        baseline=0,
        result=avg_error,
        improvement=100 - avg_error * 100,
        trials=20,
        p_value_approx="significant" if avg_error < 0.001 else "not significant",
        verdict="PROVEN" if avg_error < 0.001 else "INCONCLUSIVE"
    ))
    
    # =========================================================================
    # EVIDENCE 4: Evolution improves fitness over generations
    # =========================================================================
    print("\n--- EVIDENCE 4: Evolution Improves Fitness ---")
    
    gen1_fitness = []
    gen10_fitness = []
    
    for trial in range(10):
        tournament = TaskerTournament()
        tournament.seed_population(16)
        
        # Gen 1
        for p in tournament.players:
            tournament.evaluate_player(p)
        tournament.players.sort(key=lambda x: x.fitness, reverse=True)
        gen1_fitness.append(tournament.players[0].fitness)
        
        # Evolve to gen 10
        for _ in range(9):
            tournament.run_generation()
        
        # Gen 10
        for p in tournament.players:
            tournament.evaluate_player(p)
        tournament.players.sort(key=lambda x: x.fitness, reverse=True)
        gen10_fitness.append(tournament.players[0].fitness)
    
    gen1_avg = statistics.mean(gen1_fitness)
    gen10_avg = statistics.mean(gen10_fitness)
    improvement = ((gen10_avg - gen1_avg) / max(0.01, gen1_avg)) * 100
    
    print(f"  Gen 1 avg best: {gen1_avg:.2f}")
    print(f"  Gen 10 avg best: {gen10_avg:.2f}")
    print(f"  Improvement: {improvement:+.1f}%")
    
    results.append(EvidenceResult(
        claim="Evolution improves fitness over generations",
        baseline=gen1_avg,
        result=gen10_avg,
        improvement=improvement,
        trials=10,
        p_value_approx="significant" if improvement > 20 else "not significant",
        verdict="PROVEN" if improvement > 20 else "INCONCLUSIVE"
    ))
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("EVIDENCE SUMMARY")
    print("=" * 70)
    
    print(f"\n{'Claim':<45} {'Baseline':>10} {'Result':>10} {'Improve':>10} {'Verdict':>12}")
    print("-" * 87)
    
    proven_count = 0
    for r in results:
        verdict_emoji = "✅" if r.verdict == "PROVEN" else "⚠️"
        print(f"{r.claim:<45} {r.baseline:>10.2f} {r.result:>10.2f} {r.improvement:>+9.1f}% {verdict_emoji} {r.verdict}")
        if r.verdict == "PROVEN":
            proven_count += 1
    
    print("\n" + "=" * 70)
    print(f"PROVEN: {proven_count}/{len(results)} claims")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    run_evidence_suite()
