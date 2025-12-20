"""Neural network primitives using DNA genes.

This module implements a lightweight, pure-Python neural network layer system
where weights are stored as Genes and Instructions.
"""

import math
import random
from typing import List, Tuple, Any, Optional
from dataclasses import dataclass

from .atoms import DNA, Gene, Instruction

# ---------------------------------------------------------------------------
# Math Utils (Micro Matrix Lib)
# ---------------------------------------------------------------------------

def mat_mul(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication C = A * B."""
    rows_A = len(A)
    cols_A = len(A[0])
    rows_B = len(B)
    cols_B = len(B[0])

    if cols_A != rows_B:
         raise ValueError(f"Shape mismatch: {rows_A}x{cols_A} vs {rows_B}x{cols_B}")

    C = [[0.0 for _ in range(cols_B)] for _ in range(rows_A)]

    for i in range(rows_A):
        for j in range(cols_B):
            sum_val = 0.0
            for k in range(cols_A):
                sum_val += A[i][k] * B[k][j]
            C[i][j] = sum_val
            
    return C

def mat_add_vec(A: List[List[float]], b: List[float]) -> List[List[float]]:
    """Broadcasting addition: A + b (row-wise)."""
    rows = len(A)
    cols = len(A[0])
    if len(b) != cols:
        raise ValueError("Bias vector dimension mismatch")
        
    C = []
    for i in range(rows):
        row = [A[i][j] + b[j] for j in range(cols)]
        C.append(row)
    return C

def relu(x: float) -> float:
    return max(0.0, x)

def softmax(row: List[float]) -> List[float]:
    # Shift for stability
    m = max(row)
    exps = [math.exp(x - m) for x in row]
    sum_exps = sum(exps)
    return [e / sum_exps for e in exps]

# ---------------------------------------------------------------------------
# Neural DNA Logic
# ---------------------------------------------------------------------------

class NeuralLayer:
    """A layer defined by a Gene."""
    
    def __init__(self, input_dim: int, output_dim: int, gene: Optional[Gene] = None):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.weights: List[List[float]] = []
        self.bias: List[float] = [0.0] * output_dim
        
        if gene:
            self._unpack_gene(gene)
        else:
            self._init_random()
            
    def _init_random(self):
        # Xavier-ish init
        limit = math.sqrt(6 / (self.input_dim + self.output_dim))
        self.weights = [[random.uniform(-limit, limit) for _ in range(self.output_dim)] for _ in range(self.input_dim)]
        self.bias = [0.0] * self.output_dim
        
    def _unpack_gene(self, gene: Gene):
        """Reconstruct weights from Gene Instructions."""
        # Gene atomics: "w=0.123", "b=0.01"
        # We need mapping. For simplicity, let's assume sequential mapping or index-based.
        # "w=0:1:0.55" -> weight at row 0, col 1 is 0.55
        self._init_random() # Start random, overwrite with DNA
        
        for atom in gene.atomics:
            if atom.op_code == "w":
                # Payload: "row:col:val"
                try:
                    r, c, v = str(atom.payload).split(":")
                    r, c = int(r), int(c)
                    v = float(v)
                    if 0 <= r < self.input_dim and 0 <= c < self.output_dim:
                        self.weights[r][c] = v
                except:
                    pass
            elif atom.op_code == "b":
                 # Payload: "col:val"
                 try:
                     c, v = str(atom.payload).split(":")
                     c = int(c)
                     v = float(v)
                     if 0 <= c < self.output_dim:
                         self.bias[c] = v
                 except:
                     pass

    def to_gene(self, layer_id: str) -> Gene:
         """Serialize current weights to a Gene."""
         atomics = []
         # Compression: Only store non-zero or significant weights? 
         # Or store all. Pure Python DNA might get large.
         # Let's simple-store all for now.
         for r in range(self.input_dim):
             for c in range(self.output_dim):
                 # compress precision
                 val = round(self.weights[r][c], 4)
                 if val != 0:
                    atomics.append(Instruction("w", f"{r}:{c}:{val}"))
                    
         for c in range(self.output_dim):
             val = round(self.bias[c], 4)
             if val != 0:
                 atomics.append(Instruction("b", f"{c}:{val}"))
                 
         return Gene(id=layer_id, traits={"type": "dense"}, atomics=atomics)
         
    def forward(self, inputs: List[List[float]]) -> List[List[float]]:
        # inputs: [Batch, InputDim] (We usually do Batch=1)
        z = mat_mul(inputs, self.weights)
        z = mat_add_vec(z, self.bias)
        # Apply ReLU
        return [[relu(x) for x in row] for row in z]


class NeuralNetwork:
    """A network assembled from a genome."""
    def __init__(self, dna: DNA, input_size: int, output_size: int):
        self.layers: List[NeuralLayer] = []
        
        # Decode DNA genes into layers
        # Sort genes by ID 0, 1, 2...
        sorted_genes = sorted(dna.genes, key=lambda x: int(x.id) if x.id.isdigit() else 999)
        
        current_dim = input_size
        
        # Fixed Topology for Version 1: 
        # HIDDEN -> HIDDEN -> OUTPUT
        # We map Gene 0 -> Layer 1, Gene 1 -> Layer 2...
        # If Gene doesn't exist, we init random
        
        # Architecture: 
        # Input -> 16 -> 16 -> Output
        hidden_size = 16
        
        # Layer 1
        g0 = dna.get_gene("0")
        l1 = NeuralLayer(current_dim, hidden_size, g0)
        self.layers.append(l1)
        
        # Layer 2
        g1 = dna.get_gene("1")
        l2 = NeuralLayer(hidden_size, hidden_size, g1)
        self.layers.append(l2)
        
        # Output Layer
        g2 = dna.get_gene("2")
        l3 = NeuralLayer(hidden_size, output_size, g2)
        self.layers.append(l3)
        
    def predict(self, input_vec: List[float]) -> List[float]:
        """Forward pass for single vector."""
        # Wrap as batch 1
        x = [input_vec]
        
        for layer in self.layers:
            x = layer.forward(x)
            
        return softmax(x[0]) # Output logic: Softmax or Raw? Softmax is good for ARC colors
