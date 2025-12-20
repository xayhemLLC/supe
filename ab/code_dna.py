"""Code-DNA: Genetic primitives for program evolution.

This module defines DNA structures that encode executable code.
Genes represent code blocks (functions, expressions, statements).
DNA represents a complete program.
"""

import ast
import random
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class OpCode(Enum):
    """Instruction operation codes for code generation."""
    # Variables
    VAR = "var"       # Variable reference
    CONST = "const"   # Constant value
    ASSIGN = "assign" # Assignment statement
    
    # Control Flow
    IF = "if"         # Conditional
    LOOP = "loop"     # For/while loop
    RETURN = "ret"    # Return statement
    
    # Operations
    CALL = "call"     # Function call
    BINOP = "binop"   # Binary operation (+, -, *, /, %, etc.)
    COMPARE = "cmp"   # Comparison (==, <, >, etc.)
    
    # Collections
    LIST = "list"     # List literal
    INDEX = "idx"     # Indexing operation
    SLICE = "slice"   # Slicing operation


@dataclass
class CodeInstruction:
    """Atomic code instruction."""
    op: OpCode
    args: Dict[str, Any] = field(default_factory=dict)
    
    def to_string(self) -> str:
        args_str = ",".join(f"{k}={v}" for k, v in self.args.items())
        return f"{self.op.value}({args_str})"
    
    @classmethod
    def from_string(cls, s: str) -> "CodeInstruction":
        # Parse "op(key=val,key2=val2)"
        op_end = s.index("(")
        op = OpCode(s[:op_end])
        args_str = s[op_end+1:-1]
        args = {}
        if args_str:
            for pair in args_str.split(","):
                k, v = pair.split("=", 1)
                args[k] = v
        return cls(op=op, args=args)


@dataclass
class CodeGene:
    """A gene representing a code block or expression."""
    id: str
    instructions: List[CodeInstruction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_python_ast(self) -> List[ast.stmt]:
        """Convert gene to list of Python AST statements."""
        if not self.instructions:
            return [ast.Pass()]
        
        statements = []
        for inst in self.instructions:
            stmt = self._instruction_to_stmt(inst)
            if stmt:
                statements.append(stmt)
        
        return statements if statements else [ast.Pass()]
    
    def _instruction_to_stmt(self, inst: CodeInstruction) -> Optional[ast.stmt]:
        """Convert instruction to a statement node."""
        if inst.op == OpCode.CONST:
            # Constant alone is not useful as statement, skip
            return None
        
        elif inst.op == OpCode.VAR:
            # Variable reference alone is not useful, skip
            return None
        
        elif inst.op == OpCode.ASSIGN:
            target = str(inst.args.get("t", "result"))
            value_str = str(inst.args.get("v", "0"))
            
            # Try to parse value
            try:
                value = ast.Constant(value=int(value_str))
            except ValueError:
                try:
                    value = ast.Constant(value=float(value_str))
                except ValueError:
                    if value_str.isidentifier():
                        value = ast.Name(id=value_str, ctx=ast.Load())
                    else:
                        value = ast.Constant(value=0)
            
            return ast.Assign(
                targets=[ast.Name(id=target, ctx=ast.Store())],
                value=value
            )
        
        elif inst.op == OpCode.BINOP:
            left_str = str(inst.args.get("l", "input_data"))
            right_str = str(inst.args.get("r", "1"))
            op_str = str(inst.args.get("op", "+"))
            
            op_map = {
                "+": ast.Add(), "-": ast.Sub(),
                "*": ast.Mult(), "/": ast.Div(),
                "%": ast.Mod(), "//": ast.FloorDiv(),
            }
            
            # Parse left operand
            if left_str.isidentifier():
                left = ast.Name(id=left_str, ctx=ast.Load())
            else:
                try:
                    left = ast.Constant(value=int(left_str))
                except:
                    left = ast.Constant(value=0)
            
            # Parse right operand
            if right_str.isidentifier():
                right = ast.Name(id=right_str, ctx=ast.Load())
            else:
                try:
                    right = ast.Constant(value=int(right_str))
                except:
                    right = ast.Constant(value=1)
            
            # Wrap binop as assignment to 'result'
            binop = ast.BinOp(left=left, op=op_map.get(op_str, ast.Add()), right=right)
            return ast.Assign(
                targets=[ast.Name(id="result", ctx=ast.Store())],
                value=binop
            )
        
        elif inst.op == OpCode.RETURN:
            val_str = str(inst.args.get("v", "result"))
            if val_str.isidentifier():
                return ast.Return(value=ast.Name(id=val_str, ctx=ast.Load()))
            try:
                return ast.Return(value=ast.Constant(value=int(val_str)))
            except:
                return ast.Return(value=ast.Constant(value=0))
        
        elif inst.op == OpCode.CALL:
            func = str(inst.args.get("f", "print"))
            arg_str = str(inst.args.get("a", ""))
            arg_list = arg_str.split(";") if arg_str else []
            args = []
            for a in arg_list:
                a = a.strip()
                if a.isidentifier():
                    args.append(ast.Name(id=a, ctx=ast.Load()))
                elif a:
                    try:
                        args.append(ast.Constant(value=int(a)))
                    except:
                        args.append(ast.Constant(value=a))
            
            return ast.Expr(value=ast.Call(
                func=ast.Name(id=func, ctx=ast.Load()),
                args=args,
                keywords=[]
            ))
        
        return None


@dataclass
class CodeDNA:
    """DNA representing a complete program."""
    genes: List[CodeGene] = field(default_factory=list)
    entry_gene: str = "main"  # Which gene is the entry point
    
    def to_python_code(self) -> str:
        """Generate executable Python code from DNA."""
        # Find entry gene
        entry = self.get_gene(self.entry_gene)
        if not entry:
            return "def solve(input_data):\n    return 0"
        
        # Get statements from gene
        body = entry.to_python_ast()
        
        # Ensure we have a result variable initialized
        init_result = ast.Assign(
            targets=[ast.Name(id="result", ctx=ast.Store())],
            value=ast.Constant(value=0)
        )
        body = [init_result] + body
        
        func_def = ast.FunctionDef(
            name="solve",
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg="input_data")],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]
            ),
            body=body,
            decorator_list=[],
            returns=None
        )
        
        module = ast.Module(body=[func_def], type_ignores=[])
        ast.fix_missing_locations(module)
        
        return ast.unparse(module)
    
    def get_gene(self, gene_id: str) -> Optional[CodeGene]:
        for g in self.genes:
            if g.id == gene_id:
                return g
        return None
    
    def encode(self) -> str:
        """Serialize DNA to string."""
        parts = []
        for gene in self.genes:
            inst_strs = [i.to_string() for i in gene.instructions]
            parts.append(f"G:{gene.id}|{';'.join(inst_strs)}")
        return "||".join(parts)
    
    @classmethod
    def decode(cls, s: str) -> "CodeDNA":
        """Deserialize DNA from string."""
        genes = []
        for part in s.split("||"):
            if not part.startswith("G:"):
                continue
            gene_part = part[2:]
            gene_id, inst_str = gene_part.split("|", 1)
            instructions = []
            if inst_str:
                for i_str in inst_str.split(";"):
                    if i_str:
                        instructions.append(CodeInstruction.from_string(i_str))
            genes.append(CodeGene(id=gene_id, instructions=instructions))
        return cls(genes=genes)


# ---------------------------------------------------------------------------
# Code-DNA Genetic Operations
# ---------------------------------------------------------------------------

def crossover_code(dna_a: CodeDNA, dna_b: CodeDNA) -> CodeDNA:
    """Crossover two Code-DNAs by mixing genes."""
    new_genes = []
    
    all_ids = set(g.id for g in dna_a.genes) | set(g.id for g in dna_b.genes)
    
    for gid in all_ids:
        gene_a = dna_a.get_gene(gid)
        gene_b = dna_b.get_gene(gid)
        
        if gene_a and gene_b:
            # Mix instructions
            mixed_insts = []
            max_len = max(len(gene_a.instructions), len(gene_b.instructions))
            for i in range(max_len):
                if random.random() < 0.5:
                    if i < len(gene_a.instructions):
                        mixed_insts.append(gene_a.instructions[i])
                else:
                    if i < len(gene_b.instructions):
                        mixed_insts.append(gene_b.instructions[i])
            new_genes.append(CodeGene(id=gid, instructions=mixed_insts))
        elif gene_a:
            new_genes.append(CodeGene(id=gid, instructions=list(gene_a.instructions)))
        else:
            new_genes.append(CodeGene(id=gid, instructions=list(gene_b.instructions)))
    
    return CodeDNA(genes=new_genes)


def mutate_code(dna: CodeDNA, rate: float = 0.1) -> CodeDNA:
    """Mutate Code-DNA by adding/removing/modifying instructions."""
    import copy
    new_dna = copy.deepcopy(dna)
    
    for gene in new_dna.genes:
        if random.random() < rate:
            mutation_type = random.choice(["add", "remove", "modify"])
            
            if mutation_type == "add" and len(gene.instructions) < 10:
                # Add random instruction
                new_inst = _random_instruction()
                pos = random.randint(0, len(gene.instructions))
                gene.instructions.insert(pos, new_inst)
            
            elif mutation_type == "remove" and len(gene.instructions) > 1:
                # Remove random instruction
                pos = random.randint(0, len(gene.instructions) - 1)
                gene.instructions.pop(pos)
            
            elif mutation_type == "modify" and gene.instructions:
                # Modify random instruction
                pos = random.randint(0, len(gene.instructions) - 1)
                _mutate_instruction(gene.instructions[pos])
    
    return new_dna


def _random_instruction() -> CodeInstruction:
    """Generate a random but useful code instruction."""
    # Bias towards useful operations with input_data
    op = random.choices(
        [OpCode.BINOP, OpCode.ASSIGN, OpCode.RETURN],
        weights=[0.6, 0.3, 0.1],
        k=1
    )[0]
    
    if op == OpCode.BINOP:
        return CodeInstruction(op, {
            "l": random.choice(["input_data", "input_data", "result"]),  # Bias towards input_data
            "r": str(random.randint(1, 10)),
            "op": random.choice(["+", "-", "*", "%", "+", "*"])  # Bias towards + and *
        })
    elif op == OpCode.ASSIGN:
        return CodeInstruction(op, {
            "t": "result",
            "v": random.choice(["input_data", str(random.randint(0, 10))])
        })
    elif op == OpCode.RETURN:
        return CodeInstruction(op, {"v": "result"})
    
    return CodeInstruction(OpCode.RETURN, {"v": "result"})


def _mutate_instruction(inst: CodeInstruction) -> None:
    """Mutate an instruction in place."""
    if inst.op == OpCode.BINOP:
        # Mutate operation or operands
        choice = random.choice(["op", "r", "l"])
        if choice == "op":
            inst.args["op"] = random.choice(["+", "-", "*", "%"])
        elif choice == "r":
            try:
                val = int(inst.args.get("r", 1))
                inst.args["r"] = str(max(1, val + random.randint(-2, 2)))
            except:
                inst.args["r"] = "2"
        elif choice == "l":
            inst.args["l"] = random.choice(["input_data", "result"])
    elif inst.op == OpCode.ASSIGN:
        try:
            val = int(inst.args.get("v", 0))
            inst.args["v"] = str(val + random.randint(-5, 5))
        except:
            inst.args["v"] = "input_data"


# ---------------------------------------------------------------------------
# Template-Based Seeding
# ---------------------------------------------------------------------------

# Templates are known-correct DNA patterns for common problems
TEMPLATES = {
    "double": [
        CodeInstruction(OpCode.BINOP, {"l": "input_data", "r": "2", "op": "*"}),
        CodeInstruction(OpCode.RETURN, {"v": "result"})
    ],
    "square": [
        CodeInstruction(OpCode.BINOP, {"l": "input_data", "r": "input_data", "op": "*"}),
        CodeInstruction(OpCode.RETURN, {"v": "result"})
    ],
    "add_one": [
        CodeInstruction(OpCode.BINOP, {"l": "input_data", "r": "1", "op": "+"}),
        CodeInstruction(OpCode.RETURN, {"v": "result"})
    ],
    "identity": [
        CodeInstruction(OpCode.ASSIGN, {"t": "result", "v": "input_data"}),
        CodeInstruction(OpCode.RETURN, {"v": "result"})
    ],
    "abs_approx": [
        # Approximation: if input * input, then sqrt... but we can't sqrt easily
        # Instead: input_data * input_data (squares it, always positive-ish logic)
        CodeInstruction(OpCode.BINOP, {"l": "input_data", "r": "input_data", "op": "*"}),
        CodeInstruction(OpCode.RETURN, {"v": "result"})
    ],
    "modulo": [
        CodeInstruction(OpCode.BINOP, {"l": "input_data", "r": "2", "op": "%"}),
        CodeInstruction(OpCode.RETURN, {"v": "result"})
    ],
}


def create_random_code_dna(num_instructions: int = 3) -> CodeDNA:
    """Create a random Code-DNA, possibly seeded from templates."""
    
    # 30% chance to start from a template
    if random.random() < 0.3:
        template_name = random.choice(list(TEMPLATES.keys()))
        import copy
        instructions = copy.deepcopy(TEMPLATES[template_name])
    else:
        # Generate random but useful instructions
        instructions = []
        # Always start with an operation on input_data
        instructions.append(CodeInstruction(OpCode.BINOP, {
            "l": "input_data",
            "r": str(random.randint(1, 5)),
            "op": random.choice(["+", "-", "*"])
        }))
        
        # Maybe add more operations
        for _ in range(random.randint(0, num_instructions - 2)):
            instructions.append(_random_instruction())
        
        # Always end with return
        instructions.append(CodeInstruction(OpCode.RETURN, {"v": "result"}))
    
    main_gene = CodeGene(id="main", instructions=instructions)
    return CodeDNA(genes=[main_gene])


def create_template_dna(template_name: str) -> Optional[CodeDNA]:
    """Create DNA from a specific template."""
    if template_name not in TEMPLATES:
        return None
    
    import copy
    instructions = copy.deepcopy(TEMPLATES[template_name])
    main_gene = CodeGene(id="main", instructions=instructions)
    return CodeDNA(genes=[main_gene])


if __name__ == "__main__":
    # Demo: Show templates
    print("=== Template-Based Code DNA ===\n")
    
    for name in TEMPLATES:
        dna = create_template_dna(name)
        print(f"Template: {name}")
        print(dna.to_python_code())
        print()
    
    print("=== Random DNA (Seeded) ===\n")
    for i in range(3):
        dna = create_random_code_dna()
        print(f"Random {i+1}:")
        print(dna.to_python_code())
        print()
