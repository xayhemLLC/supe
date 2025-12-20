"""Code Tournament: Evolves Code-DNA to solve programming problems.

This tournament driver uses genetic programming to evolve solutions.
"""

import random
import time
import traceback
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field

from ab.code_dna import CodeDNA, CodeGene, CodeInstruction, OpCode, create_random_code_dna, crossover_code, mutate_code
from ab.overlord import Overlord, SelfProfile, create_random_overlord
from ab.narrator import Narrator, create_narrator


@dataclass
class Problem:
    """A coding problem to solve."""
    id: str
    description: str
    test_cases: List[Dict[str, Any]]  # {"input": ..., "expected": ...}
    time_limit_ms: float = 1000.0


@dataclass 
class Player:
    """A player in the Code Tournament."""
    id: str
    dna: CodeDNA
    score: float = 0.0
    solved_count: int = 0
    total_time_ms: float = 0.0


# Simple coding problems for testing
SAMPLE_PROBLEMS = [
    Problem(
        id="double",
        description="Return double the input number",
        test_cases=[
            {"input": 2, "expected": 4},
            {"input": 5, "expected": 10},
            {"input": 0, "expected": 0},
            {"input": -3, "expected": -6},
        ]
    ),
    Problem(
        id="square",
        description="Return the square of the input number",
        test_cases=[
            {"input": 2, "expected": 4},
            {"input": 3, "expected": 9},
            {"input": 0, "expected": 0},
            {"input": -2, "expected": 4},
        ]
    ),
    Problem(
        id="add_one",
        description="Return input plus one",
        test_cases=[
            {"input": 0, "expected": 1},
            {"input": 10, "expected": 11},
            {"input": -1, "expected": 0},
        ]
    ),
    Problem(
        id="abs_value",
        description="Return absolute value of input",
        test_cases=[
            {"input": 5, "expected": 5},
            {"input": -5, "expected": 5},
            {"input": 0, "expected": 0},
        ]
    ),
    Problem(
        id="is_even",
        description="Return 1 if input is even, 0 otherwise",
        test_cases=[
            {"input": 2, "expected": 1},
            {"input": 3, "expected": 0},
            {"input": 0, "expected": 1},
            {"input": -4, "expected": 1},
        ]
    ),
]


class CodeTournament:
    """Tournament for evolving code solutions."""
    
    def __init__(self, problems: Optional[List[Problem]] = None, use_narrator: bool = False):
        self.problems = problems or SAMPLE_PROBLEMS
        self.players: List[Player] = []
        self.round_num = 0
        self.overlord = create_random_overlord()
        self.narrator = create_narrator("mock") if use_narrator else None
        
    def seed_bracket(self, size: int = 32):
        """Create initial population."""
        self.players = []
        for i in range(size):
            dna = create_random_code_dna(4)
            self.players.append(Player(id=f"Code-{i+1}", dna=dna))
        print(f"💻 Code Tournament initialized with {len(self.players)} agents.")
        
    def evaluate_player(self, player: Player):
        """Evaluate player's code on all problems."""
        total_score = 0.0
        solved = 0
        total_time = 0.0
        
        for problem in self.problems:
            code = player.dna.to_python_code()
            result = self._run_tests(code, problem)
            
            if result["passed"]:
                solved += 1
                total_score += 100.0
                
            total_score += result["partial_score"]
            total_time += result["time_ms"]
            
            # Apply narrator reward shaping if available
            if self.narrator:
                shaped_reward = self.narrator.shape_reward(
                    total_score, 
                    code, 
                    {"passed": result["passed"], "time_ms": result["time_ms"]}
                )
                total_score = shaped_reward
        
        player.score = total_score
        player.solved_count = solved
        player.total_time_ms = total_time
        
    def _run_tests(self, code: str, problem: Problem) -> Dict[str, Any]:
        """Run code against test cases."""
        try:
            # Compile code
            exec_globals = {}
            exec(code, exec_globals)
            solve_func = exec_globals.get("solve")
            
            if not solve_func:
                return {"passed": False, "partial_score": 0, "time_ms": 0}
            
            passed_count = 0
            total_time = 0.0
            
            for tc in problem.test_cases:
                try:
                    start = time.time()
                    result = solve_func(tc["input"])
                    elapsed = (time.time() - start) * 1000
                    total_time += elapsed
                    
                    if result == tc["expected"]:
                        passed_count += 1
                except:
                    pass
                    
            all_passed = passed_count == len(problem.test_cases)
            partial = (passed_count / len(problem.test_cases)) * 50  # Up to 50 for partial
            
            return {
                "passed": all_passed,
                "partial_score": partial,
                "time_ms": total_time
            }
            
        except Exception as e:
            return {"passed": False, "partial_score": 0, "time_ms": 0}
    
    def play(self, max_rounds: int = 10):
        """Run the tournament."""
        while len(self.players) > 1 and self.round_num < max_rounds:
            self.round_num += 1
            print(f"\n--- Round {self.round_num} (Players: {len(self.players)}) ---")
            
            if len(self.players) > 16:
                self._qualifying_round()
            else:
                self._knockout_round()
                
        if self.players:
            winner = self.players[0]
            print(f"\n🏆 CHAMPION: {winner.id}")
            print(f"Score: {winner.score:.2f}, Solved: {winner.solved_count}/{len(self.problems)}")
            print(f"\nWinning Code:\n{winner.dna.to_python_code()}")
            
            if self.narrator:
                print(f"\n{self.narrator.get_session_narrative()}")
    
    def _qualifying_round(self):
        for p in self.players:
            self.evaluate_player(p)
        self.players.sort(key=lambda x: x.score, reverse=True)
        
        top = self.players[0]
        print(f"Top Score: {top.score:.2f} ({top.id}, Solved: {top.solved_count})")
        
        self.players = self.players[:len(self.players)//2]
        
    def _knockout_round(self):
        next_round = []
        
        for p in self.players:
            self.evaluate_player(p)
        self.players.sort(key=lambda x: x.score, reverse=True)
        
        matchups = []
        for i in range(0, len(self.players), 2):
            if i+1 < len(self.players):
                matchups.append((self.players[i], self.players[i+1]))
            else:
                next_round.append(self.players[i])
                
        for p1, p2 in matchups:
            print(f"Match: {p1.id} ({p1.score:.1f}) vs {p2.id} ({p2.score:.1f})")
            
            child_dna = crossover_code(p1.dna, p2.dna)
            child_dna = mutate_code(child_dna, rate=0.15)
            
            child = Player(id=f"Child({p1.id}+{p2.id})", dna=child_dna)
            self.evaluate_player(child)
            
            print(f"  -> Offspring: {child.score:.1f} (Solved: {child.solved_count})")
            
            best = max([p1, p2, child], key=lambda x: x.score)
            next_round.append(best)
            
        self.players = next_round


if __name__ == "__main__":
    t = CodeTournament(use_narrator=True)
    t.seed_bracket(32)
    t.play(max_rounds=8)
