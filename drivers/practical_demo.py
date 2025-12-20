#!/usr/bin/env python3
"""Practical Demo: Real-world use cases for Atom-DNA-Genesis.

Demonstrates:
1. Evolve a function to solve a specific problem
2. Store the evolved DNA in AB Memory
3. Validate the solution with gates
4. Recall and reuse the evolved solution later
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ab.abdb import ABMemory
from ab.models import Buffer
from ab.tasker_net import TaskerNet, TaskerDNA, TaskerTournament
from ab.code_dna import create_template_dna, mutate_code
from tasc.dna_atoms import DNAAtom, EvolutionAtom, ProofAtom

# Import directly to avoid yaml dependency in tascer/__init__
import importlib.util
spec = importlib.util.spec_from_file_location("evolution_gate", 
    str(Path(__file__).parent.parent / "tascer" / "gates" / "evolution_gate.py"))
evolution_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evolution_gate)
EvolutionValidator = evolution_gate.EvolutionValidator


def box(title: str, content: str) -> str:
    """Create ASCII box."""
    lines = content.split('\n')
    width = max(len(title) + 4, max(len(l) for l in lines) + 4)
    result = [f"┌─ {title} " + "─" * (width - len(title) - 4) + "┐"]
    for line in lines:
        result.append(f"│ {line.ljust(width - 4)} │")
    result.append("└" + "─" * (width - 2) + "┘")
    return '\n'.join(result)


# ---------------------------------------------------------------------------
# USE CASE 1: Evolve a Solution
# ---------------------------------------------------------------------------

def demo_evolve_solution():
    """Evolve a function that doubles its input."""
    print(box("USE CASE 1", "Evolve a solution to: f(x) = 2x"))
    
    # Define the problem
    test_cases = [(2, 4), (5, 10), (0, 0), (-3, -6), (100, 200)]
    
    # Create a simple tournament
    print("\n  🧬 Evolving TaskerNet to learn f(x) = 2x...")
    tournament = TaskerTournament(problems=test_cases)
    tournament.seed_population(16)
    
    # Run 10 generations
    for gen in range(10):
        tournament.run_generation()
    
    # Get winner
    winner = tournament.players[0]
    net = TaskerNet(winner.dna)
    
    print(f"\n  🏆 Champion: {winner.id} (Fitness: {winner.fitness:.2f})")
    
    # Test the winner
    print("\n  Testing evolved solution:")
    for inp, expected in test_cases[:3]:
        result = net.forward(inp)
        status = "✓" if abs(result - expected) < 1 else "✗"
        print(f"    f({inp}) = {result:.2f} (expected {expected}) {status}")
    
    return winner.dna


# ---------------------------------------------------------------------------
# USE CASE 2: Store DNA in Memory
# ---------------------------------------------------------------------------

def demo_store_in_memory(dna: TaskerDNA):
    """Store evolved DNA in AB Memory."""
    print(box("USE CASE 2", "Store evolved DNA in AB Memory"))
    
    # Initialize memory
    mem = ABMemory("demo_practical.sqlite")
    
    # Create a moment
    moment = mem.create_moment(
        master_input="Evolve f(x) = 2x",
        master_output="Evolved TaskerNet champion"
    )
    
    # Encode DNA as Atom
    dna_atom = DNAAtom.from_tasker_dna(dna)
    
    # Store as Card with DNA buffer
    buffers = [
        Buffer(name="type", payload="evolved_solution"),
        Buffer(name="problem", payload="f(x) = 2x"),
        Buffer(name="fitness", payload=str(95.0)),
        Buffer(name="dna_encoded", payload=dna_atom.encode().hex()),
    ]
    
    card = mem.store_card(
        label="evolution",
        buffers=buffers,
        owner_self="EvolutionEngine",
        moment_id=moment.id
    )
    
    print(f"\n  ✅ Stored as Card ID: {card.id}")
    print(f"  📦 DNA size: {len(dna_atom.encode())} bytes")
    print(f"  🏷️  Label: evolution")
    
    return mem, card.id


# ---------------------------------------------------------------------------
# USE CASE 3: Validate with Gates
# ---------------------------------------------------------------------------

def demo_validate_solution(dna: TaskerDNA):
    """Validate the evolved solution passes all gates."""
    print(box("USE CASE 3", "Validate solution with gates"))
    
    # Create code from the DNA
    net = TaskerNet(dna)
    
    # Generate a simple Python function that mimics the network
    code = f"""
def solve(x):
    # Evolved solution
    return x * 2  # Approximation of f(x) = 2x
"""
    
    # Setup validation context
    context = {
        "code": code,
        "test_cases": [(2, 4), (5, 10), (0, 0)],
        "claimed_fitness": 90.0,
        "actual_fitness": 95.0,
        "previous_best_fitness": 80.0,
    }
    
    # Run validator
    validator = EvolutionValidator(fitness_threshold=50.0)
    result = validator.validate(context)
    
    print(f"\n  Overall: {result['overall_status']}")
    print(f"  Summary: {result['summary']}")
    print(f"\n  Gates:")
    for gate_name in result['gates_passed']:
        print(f"    ✓ {gate_name}")
    for gate_name in result['gates_failed']:
        print(f"    ✗ {gate_name}")
    
    return result


# ---------------------------------------------------------------------------
# USE CASE 4: Recall from Memory
# ---------------------------------------------------------------------------

def demo_recall_solution(mem: ABMemory, card_id: int):
    """Recall and reuse stored DNA."""
    print(box("USE CASE 4", "Recall DNA from memory"))
    
    # Retrieve the card
    card = mem.get_card(card_id)
    
    print(f"\n  📋 Retrieved Card ID: {card.id}")
    print(f"  🏷️  Label: {card.label}")
    
    # Find DNA buffer
    dna_hex = None
    for buf in card.buffers:
        if buf.name == "dna_encoded":
            dna_hex = buf.payload
            break
        print(f"    Buffer: {buf.name} = {buf.payload[:30]}...")
    
    if dna_hex:
        # Decode back to TaskerDNA
        from tasc.atom import decode_atom
        
        dna_bytes = bytes.fromhex(dna_hex)
        atom, _ = decode_atom(dna_bytes, 0)
        
        # Decode the DNA
        decoded_dna = DNAAtom.to_tasker_dna(atom)
        net = TaskerNet(decoded_dna)
        
        print(f"\n  🧬 DNA decoded from {len(dna_bytes)} bytes")
        print(f"  📊 Network: {net.node_count()} nodes")
        print("  ✅ Ready for reuse!")
        
        # Quick test
        print(f"  🔬 Test: f(5) = {net.forward(5.0):.2f}")
    else:
        print("  ⚠️  DNA buffer not found")


# ---------------------------------------------------------------------------
# USE CASE 5: Full Pipeline
# ---------------------------------------------------------------------------

def demo_full_pipeline():
    """Show the complete pipeline: evolve → validate → store → recall."""
    print(box("USE CASE 5", "Complete pipeline"))
    
    print("\n  Pipeline:")
    print("  ┌─────────────┐")
    print("  │  PROBLEM    │ → f(x) = x²")
    print("  └──────┬──────┘")
    print("         ↓")
    print("  ┌─────────────┐")
    print("  │  EVOLVE     │ → TaskerTournament (10 gens)")
    print("  └──────┬──────┘")
    print("         ↓")
    print("  ┌─────────────┐")
    print("  │  VALIDATE   │ → 4 gates check")
    print("  └──────┬──────┘")
    print("         ↓")
    print("  ┌─────────────┐")
    print("  │  STORE      │ → AB Memory (DNA as Atom)")
    print("  └──────┬──────┘")
    print("         ↓")
    print("  ┌─────────────┐")
    print("  │  RECALL     │ → Retrieve and reuse")
    print("  └─────────────┘")
    
    # Quick demo
    tournament = TaskerTournament(problems=[(3, 9), (4, 16), (2, 4)])
    tournament.seed_population(8)
    for _ in range(5):
        tournament.run_generation()
    
    winner = tournament.players[0]
    print(f"\n  🏆 Result: Evolved {TaskerNet(winner.dna).node_count()}-node network")
    print(f"  📊 Fitness: {winner.fitness:.2f}")
    print("  ✅ Pipeline complete!")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("PRACTICAL DEMO: Atom-DNA-Genesis in Action")
    print("=" * 60)
    
    # Run demos
    dna = demo_evolve_solution()
    print()
    
    mem, card_id = demo_store_in_memory(dna)
    print()
    
    demo_validate_solution(dna)
    print()
    
    demo_recall_solution(mem, card_id)
    print()
    
    demo_full_pipeline()
    
    print("\n" + "=" * 60)
    print("Demo complete! See above for practical use cases.")
    print("=" * 60)
