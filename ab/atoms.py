"""Core genetic primitives for AB.

This module defines the fundamental units of the genetic system:
- Instruction (Atomic): The smallest executable unit.
- Gene: A cluster of instructions and traits.
- DNA: A collection of Genes representing an organism's blueprint.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import json


@dataclass
class Instruction:
    """Atomic instruction unit.
    
    Represents a single executable operation, e.g., drawing a pixel.
    """
    op_code: str
    payload: Any
    
    def to_string(self) -> str:
        """Serialize to string format (e.g. p=10:20)."""
        if self.op_code == "p": # Pixel
            # Payload is assumed to be (x, y) tuple or list
            if isinstance(self.payload, (list, tuple)) and len(self.payload) == 2:
                return f"p={self.payload[0]}:{self.payload[1]}"
        # Fallback for generic payload
        return f"{self.op_code}={str(self.payload)}"

    @staticmethod
    def from_string(s: str) -> "Instruction":
        """Parse from string format."""
        if "=" not in s:
            raise ValueError(f"Invalid instruction format: {s}")
        
        op, val = s.split("=", 1)
        
        if op == "p":
            try:
                x, y = val.split(":")
                return Instruction(op_code="p", payload=(int(x), int(y)))
            except ValueError:
                pass
                
        return Instruction(op_code=op, payload=val)


@dataclass
class Gene:
    """A functional cluster of instructions (Atomics).
    
    A Gene groups related instructions (e.g., all pixels of a certain color)
    and high-level traits.
    """
    id: str  # e.g., "0"
    traits: Dict[str, Any] = field(default_factory=dict)
    atomics: List[Instruction] = field(default_factory=list)

    def to_dna_string(self) -> str:
        """Serialize to DNA segment string.
        
        Format: g=ID,trait1=val1,trait2=val2,op=val,op=val;
        """
        parts = [f"g={self.id}"]
        
        # Serialize traits (hex color is a special case often used)
        for k, v in self.traits.items():
            if k == "color" and str(v).startswith("#"):
                parts.append(f"h={str(v)[1:]}") # Strip # for h=
            else:
                parts.append(f"{k}={v}")
                
        # Serialize atomics
        for atomic in self.atomics:
            parts.append(atomic.to_string())
            
        return ",".join(parts) + ";"

    @staticmethod
    def from_dna_string(segment: str) -> "Gene":
        """Parse from DNA segment string."""
        segment = segment.strip(";")
        parts = segment.split(",")
        
        gene_id = "0"
        traits = {}
        atomics = []
        
        for part in parts:
            if not part:
                continue
            
            if "=" not in part:
                continue
                
            key, val = part.split("=", 1)
            
            if key == "g":
                gene_id = val
            elif key == "h":
                traits["color"] = f"#{val}"
            elif key == "p":
                # Special handling for pixel atomic
                try:
                    x, y = val.split(":")
                    atomics.append(Instruction(op_code="p", payload=(int(x), int(y))))
                except ValueError:
                    pass
            else:
                # Generic trait or other atomic
                # Heuristic: if it looks like a coordinate, it's an atomic, otherwise trait
                if ":" in val and val.replace(":", "").isdigit():
                     atomics.append(Instruction(op_code=key, payload=val))
                else:
                    traits[key] = val
                    
        return Gene(id=gene_id, traits=traits, atomics=atomics)


@dataclass
class DNA:
    """The complete genetic blueprint.
    
    A collection of Genes that defines an entity.
    """
    genes: List[Gene] = field(default_factory=list)
    
    def encode(self) -> str:
        """Serialize full DNA to string."""
        return "".join(g.to_dna_string() for g in self.genes)
    
    @staticmethod
    def decode(dna_string: str) -> "DNA":
        """Parse full DNA string into object structure."""
        if not dna_string:
            return DNA()
            
        segments = dna_string.split(";")
        genes = []
        for seg in segments:
            if not seg.strip():
                continue
            # restore the semicolon for parsing logic if needed or just parse segment
            # Gene.from_dna_string expects "key=val,key=val;" or "key=val,key=val"
            genes.append(Gene.from_dna_string(seg))
            
        return DNA(genes=genes)

    def add_gene(self, gene: Gene) -> None:
        """Add a gene to the DNA."""
        self.genes.append(gene)
        
    def get_gene(self, gene_id: str) -> Optional[Gene]:
        """Retrieve a gene by ID."""
        for g in self.genes:
            if g.id == gene_id:
                return g
        return None
