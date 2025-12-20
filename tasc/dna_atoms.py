"""DNA Atoms: Encode/decode DNA structures as binary Atoms.

This module bridges the evolutionary DNA system (TaskerDNA, genes)
with the Tasc binary encoding layer (Atoms). This allows:
- Storing evolved genomes in AB Memory as first-class Atoms
- Transmitting DNA over the wire
- Proof validation via Tascer gates
"""

import json
import struct
from dataclasses import asdict
from typing import Any, Dict, Tuple

from .atom import Atom
from .atomtypes import registry, AtomType


# ---------------------------------------------------------------------------
# DNA Serialization
# ---------------------------------------------------------------------------

def encode_dna(dna_dict: Dict[str, Any]) -> bytes:
    """Encode a DNA dictionary to bytes.
    
    Uses JSON for flexibility, with length prefix.
    """
    json_str = json.dumps(dna_dict, separators=(',', ':'))
    return json_str.encode('utf-8')


def decode_dna(payload: bytes) -> Dict[str, Any]:
    """Decode DNA bytes back to dictionary."""
    return json.loads(payload.decode('utf-8'))


def encode_gene(gene_dict: Dict[str, Any]) -> bytes:
    """Encode a single gene to bytes."""
    json_str = json.dumps(gene_dict, separators=(',', ':'))
    return json_str.encode('utf-8')


def decode_gene(payload: bytes) -> Dict[str, Any]:
    """Decode gene bytes back to dictionary."""
    return json.loads(payload.decode('utf-8'))


def encode_evolution_result(result: Dict[str, Any]) -> bytes:
    """Encode evolution result to bytes."""
    json_str = json.dumps(result, separators=(',', ':'))
    return json_str.encode('utf-8')


def decode_evolution_result(payload: bytes) -> Dict[str, Any]:
    """Decode evolution result from bytes."""
    return json.loads(payload.decode('utf-8'))


def encode_proof(proof: Dict[str, Any]) -> bytes:
    """Encode proof chain to bytes."""
    json_str = json.dumps(proof, separators=(',', ':'))
    return json_str.encode('utf-8')


def decode_proof(payload: bytes) -> Dict[str, Any]:
    """Decode proof chain from bytes."""
    return json.loads(payload.decode('utf-8'))


# ---------------------------------------------------------------------------
# Register DNA AtomTypes
# ---------------------------------------------------------------------------

def register_dna_atomtypes():
    """Register DNA-related atom types in the registry."""
    
    # DNA atomtype (pindex=20)
    dna_type = AtomType(
        pindex=20,
        name="dna",
        kind="composite",
        params={"description": "Serialized TaskerDNA genome"},
        encoder=encode_dna,
        decoder=decode_dna,
    )
    
    # Gene atomtype (pindex=21)
    gene_type = AtomType(
        pindex=21,
        name="gene",
        kind="composite",
        params={"description": "Single gene unit"},
        encoder=encode_gene,
        decoder=decode_gene,
    )
    
    # Evolution result atomtype (pindex=22)
    evolution_type = AtomType(
        pindex=22,
        name="evolution_result",
        kind="composite",
        params={"description": "Result of evolution cycle"},
        encoder=encode_evolution_result,
        decoder=decode_evolution_result,
    )
    
    # Proof atomtype (pindex=23)
    proof_type = AtomType(
        pindex=23,
        name="proof",
        kind="composite",
        params={"description": "Validation proof chain"},
        encoder=encode_proof,
        decoder=decode_proof,
    )
    
    # Register all
    for atom_type in [dna_type, gene_type, evolution_type, proof_type]:
        try:
            registry.register(atom_type)
        except ValueError:
            pass  # Already registered


# ---------------------------------------------------------------------------
# High-Level API
# ---------------------------------------------------------------------------

class DNAAtom:
    """High-level wrapper for DNA Atoms."""
    
    @staticmethod
    def from_tasker_dna(dna) -> Atom:
        """Create an Atom from a TaskerDNA instance.
        
        Args:
            dna: A TaskerDNA instance from ab/tasker_net.py
            
        Returns:
            An Atom of type 'dna'
        """
        # Convert to dict - use actual field names
        dna_dict = {
            "structure": {
                "num_layers": dna.structure.num_layers,
                "branching_factor": dna.structure.branching_factor,
                "connection_density": dna.structure.connection_density,
                "skip_connections": dna.structure.skip_connections,
            },
            "behaviors": {
                k: {
                    "activation": v.activation.value,  # Enum to string
                    "transform": v.transform.value,    # Enum to string
                    "recall_probability": v.recall_probability,
                    "output_scale": v.output_scale,
                }
                for k, v in dna.behaviors.items()
            },
            "weights": {
                str(k): v for k, v in dna.weights.weights.items()
            }
        }
        
        dna_type = registry.get_by_name("dna")
        return Atom.from_value(dna_type, dna_dict)
    
    @staticmethod
    def to_tasker_dna(atom: Atom):
        """Convert an Atom back to TaskerDNA.
        
        Returns:
            A TaskerDNA instance
        """
        # Import here to avoid circular
        import sys
        sys.path.insert(0, ".")
        from ab.tasker_net import TaskerDNA, StructureGene, BehaviorGene, WeightGene, ActivationType, TransformType
        
        dna_dict = atom.decode_value()
        
        structure = StructureGene(
            num_layers=dna_dict["structure"]["num_layers"],
            branching_factor=dna_dict["structure"]["branching_factor"],
            connection_density=dna_dict["structure"]["connection_density"],
            skip_connections=dna_dict["structure"]["skip_connections"],
        )
        
        behaviors = {}
        for k, v in dna_dict["behaviors"].items():
            behaviors[k] = BehaviorGene(
                activation=ActivationType(v["activation"]),
                transform=TransformType(v["transform"]),
                recall_probability=v["recall_probability"],
                output_scale=v["output_scale"],
            )
        
        weights = WeightGene()
        for k_str, v in dna_dict["weights"].items():
            # Parse tuple from string
            key = eval(k_str)
            weights.weights[key] = v
        
        return TaskerDNA(structure=structure, behaviors=behaviors, weights=weights)


class EvolutionAtom:
    """High-level wrapper for evolution result Atoms."""
    
    @staticmethod
    def create(
        generation: int,
        best_fitness: float,
        population_size: int,
        best_dna_id: str = "",
        elapsed_time: float = 0.0,
        claims: dict = None,
    ) -> Atom:
        """Create an evolution result Atom."""
        result = {
            "generation": generation,
            "best_fitness": best_fitness,
            "population_size": population_size,
            "best_dna_id": best_dna_id,
            "elapsed_time": elapsed_time,
            "claims": claims or {},
        }
        
        evo_type = registry.get_by_name("evolution_result")
        return Atom.from_value(evo_type, result)


class ProofAtom:
    """High-level wrapper for proof chain Atoms."""
    
    @staticmethod
    def create(
        claim: str,
        evidence: list,
        gates_passed: list,
        gates_failed: list,
        overall_status: str,
    ) -> Atom:
        """Create a proof chain Atom."""
        proof = {
            "claim": claim,
            "evidence": evidence,
            "gates_passed": gates_passed,
            "gates_failed": gates_failed,
            "overall_status": overall_status,
        }
        
        proof_type = registry.get_by_name("proof")
        return Atom.from_value(proof_type, proof)


# Register on import
register_dna_atomtypes()
