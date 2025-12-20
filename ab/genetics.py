"""Genetic operations for DNA manipulation."""

import random
import copy
from typing import List, Optional, Tuple, Any

from .atoms import DNA, Gene, Instruction


def crossover(dna_a: DNA, dna_b: DNA, rate: float = 0.5) -> DNA:
    """Perform uniform crossover between two DNA strands.
    
    Combines genes from both parents. For each unique gene ID found in
    the parents, we select the gene from parent A or parent B with
    probability `rate`.
    """
    # Collect all unique gene IDs
    ids_a = {g.id for g in dna_a.genes}
    ids_b = {g.id for g in dna_b.genes}
    all_ids = sorted(list(ids_a | ids_b))
    
    new_genes = []
    
    for gid in all_ids:
        gene_a = dna_a.get_gene(gid)
        gene_b = dna_b.get_gene(gid)
        
        selected_gene = None
        
        if gene_a and gene_b:
            # Both parents have it, pick one
            if random.random() < rate:
                selected_gene = gene_b
            else:
                selected_gene = gene_a
        elif gene_a:
            # Only A has it
            selected_gene = gene_a
        else:
            # Only B has it
            selected_gene = gene_b
            
        # Append a deep copy to ensure independence
        new_genes.append(copy.deepcopy(selected_gene))
        
    return DNA(genes=new_genes)


def mutate(dna: DNA, mutation_rate: float = 0.01, mutation_power: float = 0.1) -> DNA:
    """Apply random mutations to a DNA strand.
    
    Args:
        dna: The source DNA.
        mutation_rate: Probability that any given gene will be mutated.
        mutation_power: Magnitude of mutation (e.g. how much to shift a color).
        
    Returns:
        A new mutated DNA object.
    """
    new_dna = copy.deepcopy(dna)
    
    for gene in new_dna.genes:
        if random.random() < mutation_rate:
            _mutate_gene(gene, mutation_power)
            
    return new_dna


def _mutate_gene(gene: Gene, power: float) -> None:
    """Mutate a single gene in place."""
    # 1. Mutate Traits (e.g. Color)
    if "color" in gene.traits:
        if random.random() < 0.5:
            gene.traits["color"] = _mutate_hex_color(gene.traits["color"], power)
            
    # 2. Mutate Atomics (e.g. Pixel coordinates)
    # Chance to mutate an existing atomic
    for atomic in gene.atomics:
        if random.random() < 0.1: # 10% chance per atomic if gene is selected
            _mutate_atomic(atomic, power)
            
    # Chance to add or remove atomics could go here


def _mutate_hex_color(hex_color: str, power: float) -> str:
    """Shift a hex color slightly."""
    if not hex_color.startswith("#") or len(hex_color) != 7:
        return hex_color
        
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # Random shift -25 to +25 scaled by power? 
        # Actually power usually means probability or stdev. 
        # Let's just do random noise.
        delta = int(255 * power)
        
        r = max(0, min(255, r + random.randint(-delta, delta)))
        g = max(0, min(255, g + random.randint(-delta, delta)))
        b = max(0, min(255, b + random.randint(-delta, delta)))
        
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


def _mutate_atomic(atomic: Instruction, power: float) -> None:
    """Mutate an instruction payload."""
    if atomic.op_code == "p":
        # Payload is (x, y)
        if isinstance(atomic.payload, (list, tuple)):
            x, y = atomic.payload
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
            atomic.payload = (x + dx, y + dy)


def compute_similarity(dna_a: DNA, dna_b: DNA) -> float:
    """Compute genetic similarity coefficient (0.0 to 1.0).
    
    Based on shared gene IDs and trait similarity.
    """
    ids_a = {g.id for g in dna_a.genes}
    ids_b = {g.id for g in dna_b.genes}
    
    intersection = ids_a & ids_b
    union = ids_a | ids_b
    
    if not union:
        return 1.0
        
    jaccard_index = len(intersection) / len(union)
    
    # Can refine this by comparing content of shared genes,
    # but strictly structural similarity is a good start.
    return jaccard_index
