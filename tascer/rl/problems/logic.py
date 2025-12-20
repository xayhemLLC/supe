"""Logic puzzle problem source.

Provides logic puzzles with definitive answers:
- SAT/Boolean satisfiability
- Sudoku
- Type inference
- Propositional logic
- Pattern matching
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set


@dataclass
class LogicProblem:
    """A logic puzzle with a definitive answer."""
    
    category: str  # sat, sudoku, propositional, type_inference, pattern
    title: str
    description: str
    input_data: str
    expected_answer: str
    difficulty: str = "easy"  # easy, medium, hard
    hints: List[str] = field(default_factory=list)
    
    @property
    def id(self) -> str:
        return f"logic_{self.category}_{hash(self.title) % 10000:04d}"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty,
        }


class LogicProblemSource:
    """Source of logic puzzles with definitive answers.
    
    All puzzles have verifiable correct answers, making them
    ideal for RL training.
    """
    
    def __init__(self):
        self._problems: Dict[str, LogicProblem] = {}
        self._load_builtin_problems()
    
    def _load_builtin_problems(self) -> None:
        """Load built-in logic problems."""
        # SAT Problems (Boolean satisfiability)
        self._add_sat_problems()
        
        # Sudoku Puzzles
        self._add_sudoku_problems()
        
        # Propositional Logic
        self._add_propositional_problems()
        
        # Type Inference
        self._add_type_inference_problems()
        
        # Pattern/Sequence Problems
        self._add_pattern_problems()
    
    def _add_sat_problems(self) -> None:
        """Add SAT (Boolean satisfiability) problems."""
        problems = [
            LogicProblem(
                category="sat",
                title="Simple AND",
                description="Find values for A and B such that A AND B is true. Output: A,B (each 0 or 1)",
                input_data="A AND B = true",
                expected_answer="1,1",
                difficulty="easy",
            ),
            LogicProblem(
                category="sat",
                title="OR with negation",
                description="Find A,B such that (A OR NOT B) is true. Output: A,B",
                input_data="(A OR NOT B) = true",
                expected_answer="1,0",  # One valid solution
                difficulty="easy",
            ),
            LogicProblem(
                category="sat",
                title="Two Clause",
                description="Find A,B such that (A OR B) AND (NOT A OR B) is true.",
                input_data="(A OR B) AND (NOT A OR B)",
                expected_answer="0,1",  # B must be true
                difficulty="easy",
            ),
            LogicProblem(
                category="sat",
                title="Three Variable",
                description="Find A,B,C such that (A OR B) AND (NOT B OR C) AND (NOT A OR NOT C) is true.",
                input_data="(A OR B) AND (NOT B OR C) AND (NOT A OR NOT C)",
                expected_answer="0,1,1",  # One valid
                difficulty="medium",
            ),
            LogicProblem(
                category="sat",
                title="XOR Equivalent",
                description="Find A,B such that (A OR B) AND (NOT A OR NOT B) is true.",
                input_data="(A OR B) AND (NOT A OR NOT B)",
                expected_answer="1,0",  # or 0,1
                difficulty="easy",
            ),
        ]
        for p in problems:
            self._problems[p.id] = p
    
    def _add_sudoku_problems(self) -> None:
        """Add Sudoku puzzles (4x4 for simplicity)."""
        problems = [
            LogicProblem(
                category="sudoku",
                title="4x4 Easy",
                description="Solve this 4x4 Sudoku. 0 = empty. Output: 16 digits row by row.",
                input_data="1234\n3000\n0003\n0021",
                expected_answer="1234341242134321",
                difficulty="easy",
                hints=["4x4 Sudoku uses digits 1-4, each row/col/2x2 box has 1-4 once"],
            ),
            LogicProblem(
                category="sudoku",
                title="4x4 One Missing",
                description="Complete this 4x4 Sudoku with one empty cell.",
                input_data="1234\n3412\n2143\n4320",
                expected_answer="1234341221434321",
                difficulty="easy",
            ),
            LogicProblem(
                category="sudoku",
                title="4x4 Row Complete",
                description="Sudoku where you need to fill one row.",
                input_data="0000\n3412\n2143\n4321",
                expected_answer="1234341221434321",
                difficulty="easy",
            ),
        ]
        for p in problems:
            self._problems[p.id] = p
    
    def _add_propositional_problems(self) -> None:
        """Add propositional logic problems."""
        problems = [
            LogicProblem(
                category="propositional",
                title="Modus Ponens",
                description="Given: P→Q and P. What is Q? (true/false)",
                input_data="P->Q: true\nP: true",
                expected_answer="true",
                difficulty="easy",
            ),
            LogicProblem(
                category="propositional",
                title="Modus Tollens",
                description="Given: P→Q and NOT Q. What is P? (true/false)",
                input_data="P->Q: true\nQ: false",
                expected_answer="false",
                difficulty="easy",
            ),
            LogicProblem(
                category="propositional",
                title="Chain Rule",
                description="Given: A→B, B→C, A is true. What is C?",
                input_data="A->B: true\nB->C: true\nA: true",
                expected_answer="true",
                difficulty="easy",
            ),
            LogicProblem(
                category="propositional",
                title="Contrapositive",
                description="If P→Q, what is the truth value of (NOT Q)→(NOT P)?",
                input_data="P->Q is given as true",
                expected_answer="true",
                difficulty="medium",
            ),
            LogicProblem(
                category="propositional",
                title="De Morgan",
                description="NOT(A AND B) is equivalent to what? Output: NOT_A_OR_NOT_B or NOT_A_AND_NOT_B",
                input_data="Simplify: NOT(A AND B)",
                expected_answer="NOT_A_OR_NOT_B",
                difficulty="medium",
            ),
        ]
        for p in problems:
            self._problems[p.id] = p
    
    def _add_type_inference_problems(self) -> None:
        """Add type inference problems."""
        problems = [
            LogicProblem(
                category="type_inference",
                title="Identity Function",
                description="What is the type of: f x = x? Output in format: a -> a",
                input_data="f x = x",
                expected_answer="a -> a",
                difficulty="easy",
            ),
            LogicProblem(
                category="type_inference",
                title="Constant Function",
                description="What is the type of: f x y = x?",
                input_data="f x y = x",
                expected_answer="a -> b -> a",
                difficulty="easy",
            ),
            LogicProblem(
                category="type_inference",
                title="Flip Function",
                description="What is the type of: f x y = y?",
                input_data="f x y = y",
                expected_answer="a -> b -> b",
                difficulty="easy",
            ),
            LogicProblem(
                category="type_inference",
                title="Compose",
                description="What is the type of: compose f g x = f (g x)?",
                input_data="compose f g x = f (g x)",
                expected_answer="(b -> c) -> (a -> b) -> a -> c",
                difficulty="medium",
            ),
            LogicProblem(
                category="type_inference",
                title="Apply",
                description="What is the type of: apply f x = f x?",
                input_data="apply f x = f x",
                expected_answer="(a -> b) -> a -> b",
                difficulty="easy",
            ),
        ]
        for p in problems:
            self._problems[p.id] = p
    
    def _add_pattern_problems(self) -> None:
        """Add pattern/sequence problems."""
        problems = [
            LogicProblem(
                category="pattern",
                title="Arithmetic Sequence",
                description="What comes next? 2, 4, 6, 8, ?",
                input_data="2,4,6,8",
                expected_answer="10",
                difficulty="easy",
            ),
            LogicProblem(
                category="pattern",
                title="Geometric Sequence",
                description="What comes next? 2, 6, 18, 54, ?",
                input_data="2,6,18,54",
                expected_answer="162",
                difficulty="easy",
            ),
            LogicProblem(
                category="pattern",
                title="Fibonacci-like",
                description="Each number is sum of previous two. What comes next? 1, 1, 2, 3, 5, 8, ?",
                input_data="1,1,2,3,5,8",
                expected_answer="13",
                difficulty="easy",
            ),
            LogicProblem(
                category="pattern",
                title="Square Numbers",
                description="What comes next? 1, 4, 9, 16, 25, ?",
                input_data="1,4,9,16,25",
                expected_answer="36",
                difficulty="easy",
            ),
            LogicProblem(
                category="pattern",
                title="Triangular Numbers",
                description="What comes next? 1, 3, 6, 10, 15, ?",
                input_data="1,3,6,10,15",
                expected_answer="21",
                difficulty="medium",
            ),
            LogicProblem(
                category="pattern",
                title="Prime Numbers",
                description="What comes next? 2, 3, 5, 7, 11, ?",
                input_data="2,3,5,7,11",
                expected_answer="13",
                difficulty="easy",
            ),
        ]
        for p in problems:
            self._problems[p.id] = p
    
    def list_problems(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> List[LogicProblem]:
        """List available problems with optional filters."""
        problems = list(self._problems.values())
        
        if category:
            problems = [p for p in problems if p.category == category]
        
        if difficulty:
            problems = [p for p in problems if p.difficulty == difficulty]
        
        return problems
    
    def get_problem(self, problem_id: str) -> Optional[LogicProblem]:
        """Get a specific problem by ID."""
        return self._problems.get(problem_id)
    
    def sample(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> LogicProblem:
        """Sample a random problem."""
        problems = self.list_problems(category=category, difficulty=difficulty)
        if not problems:
            raise ValueError("No problems match the criteria")
        return random.choice(problems)
    
    def verify_answer(self, problem_id: str, answer: str) -> bool:
        """Verify if an answer is correct.
        
        Note: Some problems may have multiple valid answers (e.g., SAT).
        This basic verification only checks against the stored expected answer.
        """
        problem = self.get_problem(problem_id)
        if not problem:
            return False
        
        # Normalize answers
        expected = problem.expected_answer.strip().lower().replace(" ", "")
        actual = answer.strip().lower().replace(" ", "")
        
        return actual == expected
    
    def get_categories(self) -> List[str]:
        """Get list of available categories."""
        return list(set(p.category for p in self._problems.values()))
    
    def __len__(self) -> int:
        return len(self._problems)
    
    def __iter__(self):
        return iter(self._problems.values())
