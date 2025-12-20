"""Project Euler problem source.

Provides classic algorithmic problems with integer answers
that are easy to verify.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class EulerProblem:
    """A Project Euler problem."""
    
    number: int
    title: str
    description: str
    expected_answer: str  # Integer as string
    difficulty: int  # 1-100 (Euler's own rating)
    examples: List[Tuple[str, str]] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    @property
    def id(self) -> str:
        return f"euler_{self.number:04d}"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "number": self.number,
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty,
            "tags": self.tags,
        }


class EulerProblemSource:
    """Source of Project Euler problems.
    
    Contains classic algorithmic problems with verified integer answers.
    Great for RL training because answers are always verifiable.
    """
    
    def __init__(self):
        self._problems: Dict[str, EulerProblem] = {}
        self._load_builtin_problems()
    
    def _load_builtin_problems(self) -> None:
        """Load curated Project Euler problems."""
        self._problems = {
            "euler_0001": EulerProblem(
                number=1,
                title="Multiples of 3 or 5",
                description="Find the sum of all multiples of 3 or 5 below 1000.",
                expected_answer="233168",
                difficulty=5,
                examples=[
                    ("10", "23"),  # 3+5+6+9 = 23
                ],
                hints=["Use arithmetic progression formula for O(1) solution"],
                tags=["math", "divisibility"],
            ),
            
            "euler_0002": EulerProblem(
                number=2,
                title="Even Fibonacci Numbers",
                description="Find sum of even Fibonacci numbers not exceeding 4000000.",
                expected_answer="4613732",
                difficulty=5,
                examples=[
                    ("100", "44"),  # 2+8+34 = 44
                ],
                hints=["Every 3rd Fibonacci is even"],
                tags=["fibonacci", "math"],
            ),
            
            "euler_0003": EulerProblem(
                number=3,
                title="Largest Prime Factor",
                description="Find the largest prime factor of 600851475143.",
                expected_answer="6857",
                difficulty=5,
                examples=[
                    ("13195", "29"),  # 5*7*13*29
                ],
                hints=["Divide out small factors first"],
                tags=["primes", "factorization"],
            ),
            
            "euler_0004": EulerProblem(
                number=4,
                title="Largest Palindrome Product",
                description="Find largest palindrome from product of two 3-digit numbers.",
                expected_answer="906609",
                difficulty=5,
                examples=[
                    ("2", "9009"),  # 91*99 = 9009
                ],
                tags=["palindrome", "brute-force"],
            ),
            
            "euler_0005": EulerProblem(
                number=5,
                title="Smallest Multiple",
                description="Find smallest positive number evenly divisible by 1-20.",
                expected_answer="232792560",
                difficulty=5,
                examples=[
                    ("10", "2520"),
                ],
                hints=["LCM of 1..n"],
                tags=["lcm", "math"],
            ),
            
            "euler_0006": EulerProblem(
                number=6,
                title="Sum Square Difference",
                description="Find difference between sum of squares and square of sum for 1..100.",
                expected_answer="25164150",
                difficulty=5,
                examples=[
                    ("10", "2640"),  # 55^2 - 385 = 3025 - 385 = 2640
                ],
                hints=["Use closed-form formulas"],
                tags=["math", "formula"],
            ),
            
            "euler_0007": EulerProblem(
                number=7,
                title="10001st Prime",
                description="Find the 10001st prime number.",
                expected_answer="104743",
                difficulty=5,
                examples=[
                    ("6", "13"),  # 2,3,5,7,11,13
                ],
                tags=["primes", "sieve"],
            ),
            
            "euler_0009": EulerProblem(
                number=9,
                title="Special Pythagorean Triplet",
                description="Find abc where a+b+c=1000 and a²+b²=c².",
                expected_answer="31875000",
                difficulty=5,
                examples=[
                    ("12", "60"),  # 3+4+5=12, 3*4*5=60
                ],
                tags=["pythagorean", "math"],
            ),
            
            "euler_0010": EulerProblem(
                number=10,
                title="Summation of Primes",
                description="Find sum of all primes below 2000000.",
                expected_answer="142913828922",
                difficulty=5,
                examples=[
                    ("10", "17"),  # 2+3+5+7 = 17
                ],
                tags=["primes", "sieve", "sum"],
            ),
            
            "euler_0014": EulerProblem(
                number=14,
                title="Longest Collatz Sequence",
                description="Find starting number under 1000000 with longest Collatz chain.",
                expected_answer="837799",
                difficulty=5,
                examples=[
                    ("10", "9"),  # 9 has longest chain under 10
                ],
                hints=["Use memoization"],
                tags=["collatz", "dynamic-programming"],
            ),
            
            "euler_0020": EulerProblem(
                number=20,
                title="Factorial Digit Sum",
                description="Find sum of digits in 100!.",
                expected_answer="648",
                difficulty=5,
                examples=[
                    ("10", "27"),  # 10! = 3628800, sum = 27
                ],
                tags=["factorial", "big-integer"],
            ),
            
            "euler_0025": EulerProblem(
                number=25,
                title="1000-digit Fibonacci Number",
                description="Find index of first Fibonacci number with 1000 digits.",
                expected_answer="4782",
                difficulty=5,
                examples=[
                    ("3", "12"),  # F_12 = 144 (first 3-digit)
                ],
                tags=["fibonacci", "big-integer"],
            ),
        }
    
    def list_problems(
        self,
        max_difficulty: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> List[EulerProblem]:
        """List available problems with optional filters."""
        problems = list(self._problems.values())
        
        if max_difficulty:
            problems = [p for p in problems if p.difficulty <= max_difficulty]
        
        if tags:
            problems = [p for p in problems if any(t in p.tags for t in tags)]
        
        return sorted(problems, key=lambda p: p.number)
    
    def get_problem(self, problem_id: str) -> Optional[EulerProblem]:
        """Get a specific problem by ID."""
        return self._problems.get(problem_id)
    
    def get_by_number(self, number: int) -> Optional[EulerProblem]:
        """Get a problem by its Euler number."""
        return self._problems.get(f"euler_{number:04d}")
    
    def sample(
        self,
        max_difficulty: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> EulerProblem:
        """Sample a random problem."""
        import random
        problems = self.list_problems(max_difficulty=max_difficulty, tags=tags)
        if not problems:
            raise ValueError("No problems match the criteria")
        return random.choice(problems)
    
    def verify_answer(self, problem_id: str, answer: str) -> bool:
        """Verify if an answer is correct."""
        problem = self.get_problem(problem_id)
        if not problem:
            return False
        return answer.strip() == problem.expected_answer
    
    def __len__(self) -> int:
        return len(self._problems)
    
    def __iter__(self):
        return iter(self._problems.values())
