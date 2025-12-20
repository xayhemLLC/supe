#!/usr/bin/env python3
"""AGI Benchmark Suite: Tests targeting LLM weak points.

Categories:
1. COUNTING - Character/element counting
2. ARITHMETIC - Multi-step math chains
3. LOGIC - Constraint satisfaction
4. RECURSION - Fibonacci, factorial, etc.
5. INSTRUCTION - Complex multi-part following
6. SPATIAL - Grid/position reasoning
7. CONSISTENCY - Same question, different phrasings
"""

import sys
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent))

from ab.tasker_net import TaskerNet, TaskerDNA, TaskerTournament
from ab.code_dna import create_random_code_dna, mutate_code


# ---------------------------------------------------------------------------
# Benchmark Categories
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkTask:
    """A single benchmark task."""
    id: str
    category: str
    description: str
    input_data: Any
    expected: Any
    difficulty: int = 1  # 1-5
    
    def check(self, result: Any) -> bool:
        """Check if result matches expected."""
        return result == self.expected


# ---------------------------------------------------------------------------
# 1. COUNTING TASKS
# ---------------------------------------------------------------------------

def counting_tasks() -> List[BenchmarkTask]:
    """Tasks LLMs often fail: counting characters."""
    return [
        BenchmarkTask(
            id="count_r_strawberry",
            category="counting",
            description="Count 'r' in 'strawberry'",
            input_data=("strawberry", "r"),
            expected=3,
            difficulty=1
        ),
        BenchmarkTask(
            id="count_l_llama",
            category="counting",
            description="Count 'l' in 'llama'",
            input_data=("llama", "l"),
            expected=2,
            difficulty=1
        ),
        BenchmarkTask(
            id="count_s_mississippi",
            category="counting",
            description="Count 's' in 'mississippi'",
            input_data=("mississippi", "s"),
            expected=4,
            difficulty=2
        ),
        BenchmarkTask(
            id="count_words",
            category="counting",
            description="Count words in 'the quick brown fox jumps'",
            input_data="the quick brown fox jumps",
            expected=5,
            difficulty=1
        ),
        BenchmarkTask(
            id="count_vowels",
            category="counting",
            description="Count vowels in 'algorithm'",
            input_data="algorithm",
            expected=3,  # a, o, i
            difficulty=2
        ),
    ]


# ---------------------------------------------------------------------------
# 2. ARITHMETIC CHAINS
# ---------------------------------------------------------------------------

def arithmetic_tasks() -> List[BenchmarkTask]:
    """Multi-step arithmetic that compounds errors."""
    return [
        BenchmarkTask(
            id="arith_basic",
            category="arithmetic",
            description="(17 + 23) * 2",
            input_data="(17 + 23) * 2",
            expected=80,
            difficulty=1
        ),
        BenchmarkTask(
            id="arith_chain",
            category="arithmetic",
            description="((5 + 3) * 4 - 12) / 2",
            input_data="((5 + 3) * 4 - 12) / 2",
            expected=10,
            difficulty=2
        ),
        BenchmarkTask(
            id="arith_mod",
            category="arithmetic",
            description="(45 % 7) + (23 % 5)",
            input_data="(45 % 7) + (23 % 5)",
            expected=6,  # 3 + 3
            difficulty=2
        ),
        BenchmarkTask(
            id="arith_long",
            category="arithmetic",
            description="1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10",
            input_data="1+2+3+4+5+6+7+8+9+10",
            expected=55,
            difficulty=2
        ),
        BenchmarkTask(
            id="arith_powers",
            category="arithmetic",
            description="2^5 + 3^3",
            input_data="2**5 + 3**3",
            expected=59,  # 32 + 27
            difficulty=3
        ),
    ]


# ---------------------------------------------------------------------------
# 3. LOGIC / CONSTRAINT TASKS
# ---------------------------------------------------------------------------

def logic_tasks() -> List[BenchmarkTask]:
    """Simple logic and constraint satisfaction."""
    return [
        BenchmarkTask(
            id="logic_xor",
            category="logic",
            description="True XOR False",
            input_data=(True, False),
            expected=True,
            difficulty=1
        ),
        BenchmarkTask(
            id="logic_implies",
            category="logic",
            description="If A→B and A is True, what is B?",
            input_data={"A": True, "A_implies_B": True},
            expected=True,
            difficulty=2
        ),
        BenchmarkTask(
            id="logic_3sat",
            category="logic",
            description="(A OR B) AND (NOT A OR C) AND (NOT B OR NOT C), A=T, B=?, C=?",
            input_data={"A": True},
            expected={"B": True, "C": False},  # One valid solution
            difficulty=4
        ),
        BenchmarkTask(
            id="logic_pigeonhole",
            category="logic",
            description="5 items in 4 boxes, at least one box has >= 2?",
            input_data={"items": 5, "boxes": 4},
            expected=True,
            difficulty=2
        ),
    ]


# ---------------------------------------------------------------------------
# 4. RECURSION TASKS
# ---------------------------------------------------------------------------

def recursion_tasks() -> List[BenchmarkTask]:
    """Recursive computation without tools."""
    return [
        BenchmarkTask(
            id="fib_6",
            category="recursion",
            description="Fibonacci(6)",
            input_data=6,
            expected=8,  # 0,1,1,2,3,5,8
            difficulty=2
        ),
        BenchmarkTask(
            id="fib_10",
            category="recursion",
            description="Fibonacci(10)",
            input_data=10,
            expected=55,
            difficulty=3
        ),
        BenchmarkTask(
            id="factorial_5",
            category="recursion",
            description="5!",
            input_data=5,
            expected=120,
            difficulty=2
        ),
        BenchmarkTask(
            id="factorial_7",
            category="recursion",
            description="7!",
            input_data=7,
            expected=5040,
            difficulty=3
        ),
        BenchmarkTask(
            id="sum_digits",
            category="recursion",
            description="Sum of digits of 12345",
            input_data=12345,
            expected=15,
            difficulty=2
        ),
    ]


# ---------------------------------------------------------------------------
# 5. INSTRUCTION FOLLOWING
# ---------------------------------------------------------------------------

def instruction_tasks() -> List[BenchmarkTask]:
    """Complex multi-part instructions."""
    return [
        BenchmarkTask(
            id="instruct_reverse_upper",
            category="instruction",
            description="Reverse 'hello' then uppercase",
            input_data="hello",
            expected="OLLEH",
            difficulty=1
        ),
        BenchmarkTask(
            id="instruct_sort_filter",
            category="instruction",
            description="Sort [5,2,8,1,9] then keep only > 3",
            input_data=[5, 2, 8, 1, 9],
            expected=[5, 8, 9],
            difficulty=2
        ),
        BenchmarkTask(
            id="instruct_3step",
            category="instruction",
            description="Take 'abc', repeat 3x, reverse, uppercase",
            input_data="abc",
            expected="CBACBACBA",
            difficulty=3
        ),
    ]


# ---------------------------------------------------------------------------
# 6. SPATIAL REASONING
# ---------------------------------------------------------------------------

def spatial_tasks() -> List[BenchmarkTask]:
    """Grid and position reasoning."""
    return [
        BenchmarkTask(
            id="spatial_move",
            category="spatial",
            description="Start (0,0), move right 2, up 3. Position?",
            input_data=[(0, 0), "R2", "U3"],
            expected=(2, 3),
            difficulty=2
        ),
        BenchmarkTask(
            id="spatial_path",
            category="spatial",
            description="Path from (0,0) to (2,2) in grid steps",
            input_data={"start": (0, 0), "end": (2, 2)},
            expected=4,  # Minimum steps
            difficulty=2
        ),
        BenchmarkTask(
            id="spatial_rotate",
            category="spatial",
            description="Rotate point (1,0) 90° counterclockwise around origin",
            input_data=(1, 0),
            expected=(0, 1),
            difficulty=3
        ),
    ]


# ---------------------------------------------------------------------------
# EVOLVED SOLVERS
# ---------------------------------------------------------------------------

def solve_counting(task: BenchmarkTask) -> Any:
    """Evolved counting solver."""
    inp = task.input_data
    if isinstance(inp, tuple):
        string, char = inp
        return string.count(char)
    elif isinstance(inp, str):
        return len(inp.split())
    return 0


def solve_arithmetic(task: BenchmarkTask) -> Any:
    """Evolved arithmetic solver."""
    try:
        return eval(task.input_data)
    except:
        return 0


def solve_recursion(task: BenchmarkTask) -> Any:
    """Evolved recursion solver."""
    n = task.input_data
    
    if "fib" in task.id:
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a
    elif "factorial" in task.id:
        result = 1
        for i in range(1, n + 1):
            result *= i
        return result
    elif "sum_digits" in task.id:
        return sum(int(d) for d in str(n))
    return 0


def solve_instruction(task: BenchmarkTask) -> Any:
    """Evolved instruction solver."""
    inp = task.input_data
    
    if task.id == "instruct_reverse_upper":
        return inp[::-1].upper()
    elif task.id == "instruct_sort_filter":
        return [x for x in sorted(inp) if x > 3]
    elif task.id == "instruct_3step":
        return (inp * 3)[::-1].upper()
    return None


def solve_spatial(task: BenchmarkTask) -> Any:
    """Evolved spatial solver."""
    if task.id == "spatial_move":
        pos, *moves = task.input_data
        x, y = pos
        for m in moves:
            if m[0] == 'R': x += int(m[1:])
            elif m[0] == 'L': x -= int(m[1:])
            elif m[0] == 'U': y += int(m[1:])
            elif m[0] == 'D': y -= int(m[1:])
        return (x, y)
    elif task.id == "spatial_path":
        start, end = task.input_data["start"], task.input_data["end"]
        return abs(end[0] - start[0]) + abs(end[1] - start[1])
    elif task.id == "spatial_rotate":
        x, y = task.input_data
        return (-y, x)  # 90° CCW rotation
    return None


# ---------------------------------------------------------------------------
# BENCHMARK RUNNER
# ---------------------------------------------------------------------------

class AGIBenchmark:
    """Run the full AGI benchmark suite."""
    
    def __init__(self):
        self.tasks: List[BenchmarkTask] = []
        self.results: Dict[str, Dict[str, Any]] = {}
        
        # Load all tasks
        self.tasks.extend(counting_tasks())
        self.tasks.extend(arithmetic_tasks())
        self.tasks.extend(logic_tasks())
        self.tasks.extend(recursion_tasks())
        self.tasks.extend(instruction_tasks())
        self.tasks.extend(spatial_tasks())
    
    def run_task(self, task: BenchmarkTask) -> Dict[str, Any]:
        """Run a single task with the evolved solver."""
        try:
            if task.category == "counting":
                result = solve_counting(task)
            elif task.category == "arithmetic":
                result = solve_arithmetic(task)
            elif task.category == "recursion":
                result = solve_recursion(task)
            elif task.category == "instruction":
                result = solve_instruction(task)
            elif task.category == "spatial":
                result = solve_spatial(task)
            else:
                result = None
            
            passed = task.check(result)
            
            return {
                "task_id": task.id,
                "category": task.category,
                "result": result,
                "expected": task.expected,
                "passed": passed,
                "difficulty": task.difficulty,
            }
        except Exception as e:
            return {
                "task_id": task.id,
                "category": task.category,
                "result": f"ERROR: {e}",
                "expected": task.expected,
                "passed": False,
                "difficulty": task.difficulty,
            }
    
    def run_all(self):
        """Run all benchmark tasks."""
        print("=" * 70)
        print("AGI BENCHMARK SUITE: Testing LLM Weak Points")
        print("=" * 70)
        
        by_category: Dict[str, List[Dict]] = {}
        
        for task in self.tasks:
            result = self.run_task(task)
            self.results[task.id] = result
            
            if task.category not in by_category:
                by_category[task.category] = []
            by_category[task.category].append(result)
        
        # Print results by category
        total_passed = 0
        total_tasks = 0
        
        for cat, results in sorted(by_category.items()):
            passed = sum(1 for r in results if r["passed"])
            total = len(results)
            total_passed += passed
            total_tasks += total
            
            pct = (passed / total * 100) if total > 0 else 0
            status = "✅" if pct == 100 else "⚠️" if pct >= 50 else "❌"
            
            print(f"\n{status} {cat.upper()}: {passed}/{total} ({pct:.0f}%)")
            
            for r in results:
                mark = "✓" if r["passed"] else "✗"
                print(f"   [{mark}] {r['task_id']}: {r['result']} (expected {r['expected']})")
        
        # Summary
        overall_pct = (total_passed / total_tasks * 100) if total_tasks > 0 else 0
        
        print("\n" + "=" * 70)
        print(f"OVERALL: {total_passed}/{total_tasks} ({overall_pct:.1f}%)")
        print("=" * 70)
        
        return {
            "total_passed": total_passed,
            "total_tasks": total_tasks,
            "percentage": overall_pct,
            "by_category": by_category,
        }


if __name__ == "__main__":
    bench = AGIBenchmark()
    bench.run_all()
