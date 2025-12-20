"""Advent of Code problem source.

Provides problems from Advent of Code (2015-2024) with:
- Problem descriptions
- Example inputs/outputs
- Known correct answers
"""

import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path


@dataclass
class AocProblem:
    """An Advent of Code problem."""
    
    year: int
    day: int
    part: int
    title: str = ""
    description: str = ""
    examples: List[Tuple[str, str]] = field(default_factory=list)
    puzzle_input: str = ""
    expected_answer: Optional[str] = None
    difficulty: str = "unknown"  # easy, medium, hard
    tags: List[str] = field(default_factory=list)
    
    @property
    def id(self) -> str:
        return f"aoc_{self.year}_day{self.day:02d}_part{self.part}"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "year": self.year,
            "day": self.day,
            "part": self.part,
            "title": self.title,
            "description": self.description,
            "examples": self.examples,
            "difficulty": self.difficulty,
            "tags": self.tags,
        }


class AocProblemSource:
    """Source of Advent of Code problems.
    
    Contains a curated set of AoC problems with known solutions.
    Problems are categorized by difficulty and algorithmic tags.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.path.expanduser("~/.cache/tascer/aoc")
        os.makedirs(self.cache_dir, exist_ok=True)
        self._problems: Dict[str, AocProblem] = {}
        self._load_builtin_problems()
    
    def _load_builtin_problems(self) -> None:
        """Load built-in curated problems."""
        # A curated set of easy-to-verify AoC problems
        self._problems = {
            # 2023 Day 1 - Sum of calibration values
            "aoc_2023_day01_part1": AocProblem(
                year=2023, day=1, part=1,
                title="Trebuchet?!",
                description="Find the first and last digit in each line, form a two-digit number, sum all.",
                examples=[
                    ("1abc2\npqr3stu8vwx\na1b2c3d4e5f\ntreb7uchet", "142"),
                ],
                difficulty="easy",
                tags=["string", "parsing"],
            ),
            
            # 2022 Day 1 - Calorie Counting
            "aoc_2022_day01_part1": AocProblem(
                year=2022, day=1, part=1,
                title="Calorie Counting",
                description="Find the Elf carrying the most Calories. Sum each group, find max.",
                examples=[
                    ("1000\n2000\n3000\n\n4000\n\n5000\n6000\n\n7000\n8000\n9000\n\n10000", "24000"),
                ],
                difficulty="easy",
                tags=["sum", "grouping"],
            ),
            
            "aoc_2022_day01_part2": AocProblem(
                year=2022, day=1, part=2,
                title="Calorie Counting - Top Three",
                description="Find the top three Elves carrying the most Calories. Sum their totals.",
                examples=[
                    ("1000\n2000\n3000\n\n4000\n\n5000\n6000\n\n7000\n8000\n9000\n\n10000", "45000"),
                ],
                difficulty="easy",
                tags=["sum", "sorting"],
            ),
            
            # 2021 Day 1 - Sonar Sweep
            "aoc_2021_day01_part1": AocProblem(
                year=2021, day=1, part=1,
                title="Sonar Sweep",
                description="Count measurements larger than the previous one.",
                examples=[
                    ("199\n200\n208\n210\n200\n207\n240\n269\n260\n263", "7"),
                ],
                difficulty="easy",
                tags=["array", "comparison"],
            ),
            
            # 2020 Day 1 - Report Repair  
            "aoc_2020_day01_part1": AocProblem(
                year=2020, day=1, part=1,
                title="Report Repair",
                description="Find two numbers that sum to 2020, return their product.",
                examples=[
                    ("1721\n979\n366\n299\n675\n1456", "514579"),
                ],
                difficulty="easy",
                tags=["two-sum", "hash"],
            ),
            
            "aoc_2020_day01_part2": AocProblem(
                year=2020, day=1, part=2,
                title="Report Repair - Three Sum",
                description="Find three numbers that sum to 2020, return their product.",
                examples=[
                    ("1721\n979\n366\n299\n675\n1456", "241861950"),
                ],
                difficulty="medium",
                tags=["three-sum", "hash"],
            ),
            
            # 2015 Day 1 - Not Quite Lisp
            "aoc_2015_day01_part1": AocProblem(
                year=2015, day=1, part=1,
                title="Not Quite Lisp",
                description="( goes up, ) goes down. Find final floor.",
                examples=[
                    ("(())", "0"),
                    ("()()", "0"),
                    ("(((", "3"),
                    ("))(((((", "3"),
                    ("())", "-1"),
                    ("))(", "-1"),
                    (")))", "-3"),
                    (")())())", "-3"),
                ],
                difficulty="easy",
                tags=["string", "counter"],
            ),
            
            "aoc_2015_day01_part2": AocProblem(
                year=2015, day=1, part=2,
                title="Not Quite Lisp - Basement",
                description="Find position of character that first enters basement (floor -1).",
                examples=[
                    (")", "1"),
                    ("()())", "5"),
                ],
                difficulty="easy",
                tags=["string", "search"],
            ),
            
            # 2019 Day 1 - The Tyranny of the Rocket Equation
            "aoc_2019_day01_part1": AocProblem(
                year=2019, day=1, part=1,
                title="The Tyranny of the Rocket Equation",
                description="Calculate fuel: mass // 3 - 2. Sum for all modules.",
                examples=[
                    ("12", "2"),
                    ("14", "2"),
                    ("1969", "654"),
                    ("100756", "33583"),
                ],
                difficulty="easy",
                tags=["math", "sum"],
            ),
        }
    
    def list_problems(
        self,
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None,
        year: Optional[int] = None,
    ) -> List[AocProblem]:
        """List available problems with optional filters."""
        problems = list(self._problems.values())
        
        if difficulty:
            problems = [p for p in problems if p.difficulty == difficulty]
        
        if tags:
            problems = [p for p in problems if any(t in p.tags for t in tags)]
        
        if year:
            problems = [p for p in problems if p.year == year]
        
        return problems
    
    def get_problem(self, problem_id: str) -> Optional[AocProblem]:
        """Get a specific problem by ID."""
        return self._problems.get(problem_id)
    
    def sample(
        self,
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> AocProblem:
        """Sample a random problem."""
        import random
        problems = self.list_problems(difficulty=difficulty, tags=tags)
        if not problems:
            raise ValueError("No problems match the criteria")
        return random.choice(problems)
    
    def add_problem(self, problem: AocProblem) -> None:
        """Add a custom problem."""
        self._problems[problem.id] = problem
    
    def __len__(self) -> int:
        return len(self._problems)
    
    def __iter__(self):
        return iter(self._problems.values())
