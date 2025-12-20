"""Unified problem generator for RL training.

Combines all problem sources into a single interface.
"""

import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .problems.aoc import AocProblem, AocProblemSource
from .problems.euler import EulerProblem, EulerProblemSource
from .problems.logic import LogicProblem, LogicProblemSource


class ProblemType(Enum):
    """Types of problems."""
    AOC = "aoc"
    EULER = "euler"
    LOGIC = "logic"


@dataclass
class UnifiedProblem:
    """A problem in unified format for the RL environment."""
    
    id: str
    problem_type: ProblemType
    title: str
    description: str
    input_data: str
    expected_answer: Optional[str]
    examples: List[tuple]  # List of (input, expected_output)
    difficulty: str
    tags: List[str]
    original: Any  # Original problem object
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.problem_type.value,
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty,
            "tags": self.tags,
            "has_examples": len(self.examples) > 0,
            "has_answer": self.expected_answer is not None,
        }


class ProblemGenerator:
    """Unified problem generator for RL training.
    
    Combines problems from:
    - Advent of Code (algorithmic, string parsing)
    - Project Euler (mathematical, number theory)
    - Logic Puzzles (SAT, Sudoku, type inference)
    
    Example:
        >>> gen = ProblemGenerator()
        >>> problem = gen.sample()
        >>> print(problem.title)
        >>> 
        >>> # Sample specific type
        >>> euler = gen.sample(problem_type=ProblemType.EULER)
        >>> 
        >>> # Sample by difficulty
        >>> easy = gen.sample(difficulty="easy")
    """
    
    def __init__(self):
        self.aoc = AocProblemSource()
        self.euler = EulerProblemSource()
        self.logic = LogicProblemSource()
    
    def _convert_aoc(self, problem: AocProblem) -> UnifiedProblem:
        """Convert AoC problem to unified format."""
        return UnifiedProblem(
            id=problem.id,
            problem_type=ProblemType.AOC,
            title=problem.title,
            description=problem.description,
            input_data=problem.puzzle_input,
            expected_answer=problem.expected_answer,
            examples=problem.examples,
            difficulty=problem.difficulty,
            tags=problem.tags,
            original=problem,
        )
    
    def _convert_euler(self, problem: EulerProblem) -> UnifiedProblem:
        """Convert Euler problem to unified format."""
        return UnifiedProblem(
            id=problem.id,
            problem_type=ProblemType.EULER,
            title=problem.title,
            description=problem.description,
            input_data="",  # Euler problems have hardcoded inputs
            expected_answer=problem.expected_answer,
            examples=problem.examples,
            difficulty="easy" if problem.difficulty <= 10 else "medium",
            tags=problem.tags,
            original=problem,
        )
    
    def _convert_logic(self, problem: LogicProblem) -> UnifiedProblem:
        """Convert Logic problem to unified format."""
        return UnifiedProblem(
            id=problem.id,
            problem_type=ProblemType.LOGIC,
            title=problem.title,
            description=problem.description,
            input_data=problem.input_data,
            expected_answer=problem.expected_answer,
            examples=[(problem.input_data, problem.expected_answer)],
            difficulty=problem.difficulty,
            tags=[problem.category],
            original=problem,
        )
    
    def list_all(
        self,
        problem_type: Optional[ProblemType] = None,
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[UnifiedProblem]:
        """List all available problems."""
        problems = []
        
        if problem_type is None or problem_type == ProblemType.AOC:
            for p in self.aoc.list_problems(difficulty=difficulty, tags=tags):
                problems.append(self._convert_aoc(p))
        
        if problem_type is None or problem_type == ProblemType.EULER:
            for p in self.euler.list_problems(tags=tags):
                problems.append(self._convert_euler(p))
        
        if problem_type is None or problem_type == ProblemType.LOGIC:
            for p in self.logic.list_problems(difficulty=difficulty):
                problems.append(self._convert_logic(p))
        
        # Filter by difficulty if specified
        if difficulty:
            problems = [p for p in problems if p.difficulty == difficulty]
        
        return problems
    
    def sample(
        self,
        problem_type: Optional[ProblemType] = None,
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> UnifiedProblem:
        """Sample a random problem.
        
        Args:
            problem_type: Optional type filter (AOC, EULER, LOGIC)
            difficulty: Optional difficulty filter (easy, medium, hard)
            tags: Optional tag filter
        
        Returns:
            A randomly selected problem.
        """
        problems = self.list_all(
            problem_type=problem_type,
            difficulty=difficulty,
            tags=tags,
        )
        
        if not problems:
            raise ValueError("No problems match the criteria")
        
        return random.choice(problems)
    
    def get_problem(self, problem_id: str) -> Optional[UnifiedProblem]:
        """Get a specific problem by ID."""
        if problem_id.startswith("aoc_"):
            p = self.aoc.get_problem(problem_id)
            return self._convert_aoc(p) if p else None
        elif problem_id.startswith("euler_"):
            p = self.euler.get_problem(problem_id)
            return self._convert_euler(p) if p else None
        elif problem_id.startswith("logic_"):
            p = self.logic.get_problem(problem_id)
            return self._convert_logic(p) if p else None
        return None
    
    def verify_answer(self, problem_id: str, answer: str) -> bool:
        """Verify if an answer is correct."""
        problem = self.get_problem(problem_id)
        if not problem or not problem.expected_answer:
            return False
        
        # Normalize comparison
        expected = problem.expected_answer.strip()
        actual = answer.strip()
        
        return actual == expected
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about available problems."""
        all_problems = self.list_all()
        
        by_type = {}
        by_difficulty = {}
        
        for p in all_problems:
            # Count by type
            t = p.problem_type.value
            by_type[t] = by_type.get(t, 0) + 1
            
            # Count by difficulty
            d = p.difficulty
            by_difficulty[d] = by_difficulty.get(d, 0) + 1
        
        return {
            "total": len(all_problems),
            "by_type": by_type,
            "by_difficulty": by_difficulty,
        }
    
    def __len__(self) -> int:
        return len(self.aoc) + len(self.euler) + len(self.logic)
