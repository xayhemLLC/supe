"""Gym-style RL Environment for Code Agents.

Provides a standardized training environment for reinforcement learning.
"""

import os
import sys
import hashlib
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .problem_generator import ProblemGenerator, UnifiedProblem, ProblemType
from .reward import RewardComputer, RewardComponents
from .memory_store import MemoryStore, Experience, Solution
from .runners.base import Language, get_runner, RunResult


class ActionType(Enum):
    """Available actions in the environment."""
    SUBMIT_CODE = "submit_code"
    REFINE_CODE = "refine_code"
    CHANGE_APPROACH = "change_approach"


@dataclass
class State:
    """Current environment state."""
    
    problem: UnifiedProblem
    current_code: str
    language: Language
    iteration: int
    tests_passed: int
    tests_failed: int
    last_error: Optional[str]
    last_output: Optional[str]
    is_correct: bool
    done: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem.id,
            "iteration": self.iteration,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "has_error": self.last_error is not None,
            "is_correct": self.is_correct,
            "done": self.done,
            "code_length": len(self.current_code),
        }
    
    def get_hash(self) -> str:
        """Get a hash of the state for experience replay."""
        content = f"{self.problem.id}:{self.current_code}:{self.tests_passed}"
        return hashlib.md5(content.encode()).hexdigest()[:8]


@dataclass
class StepResult:
    """Result of taking a step in the environment."""
    
    state: State
    reward: RewardComponents
    done: bool
    info: Dict[str, Any] = field(default_factory=dict)


class CodeAgentEnv:
    """Gym-style environment for training code agents.
    
    The environment provides:
    - Problem sampling from multiple sources
    - Multi-language code execution (Python, Rust, TypeScript)
    - Configurable reward shaping
    - Experience storage for replay
    
    Example:
        >>> env = CodeAgentEnv()
        >>> state = env.reset()
        >>> while not state.done:
        ...     code = agent.generate(state)
        ...     result = env.step(code)
        ...     state = result.state
        >>> print(f"Solved: {state.is_correct}")
    """
    
    def __init__(
        self,
        problem_type: Optional[ProblemType] = None,
        difficulty: Optional[str] = None,
        language: Language = Language.PYTHON,
        max_iterations: int = 20,
        memory_store: Optional[MemoryStore] = None,
        reward_computer: Optional[RewardComputer] = None,
    ):
        self.problem_type = problem_type
        self.difficulty = difficulty
        self.language = language
        self.max_iterations = max_iterations
        
        # Components
        self.problem_generator = ProblemGenerator()
        self.memory = memory_store or MemoryStore()
        self.reward_computer = reward_computer or RewardComputer()
        self.runner = get_runner(language)
        
        # Current episode state
        self._state: Optional[State] = None
        self._work_dir: Optional[str] = None
    
    @property
    def state(self) -> Optional[State]:
        return self._state
    
    def reset(
        self,
        problem_id: Optional[str] = None,
    ) -> State:
        """Reset environment with a new problem.
        
        Args:
            problem_id: Optional specific problem to use.
        
        Returns:
            Initial state.
        """
        # Clean up previous work directory
        if self._work_dir:
            import shutil
            shutil.rmtree(self._work_dir, ignore_errors=True)
        
        # Create new work directory
        self._work_dir = tempfile.mkdtemp(prefix="rl_env_")
        
        # Get problem
        if problem_id:
            problem = self.problem_generator.get_problem(problem_id)
            if not problem:
                raise ValueError(f"Problem not found: {problem_id}")
        else:
            problem = self.problem_generator.sample(
                problem_type=self.problem_type,
                difficulty=self.difficulty,
            )
        
        # Initialize state
        self._state = State(
            problem=problem,
            current_code="",
            language=self.language,
            iteration=0,
            tests_passed=0,
            tests_failed=0,
            last_error=None,
            last_output=None,
            is_correct=False,
            done=False,
        )
        
        return self._state
    
    def step(self, code: str) -> StepResult:
        """Take a step by submitting code.
        
        Args:
            code: Code to execute.
        
        Returns:
            StepResult with new state, reward, done flag, and info.
        """
        if self._state is None:
            raise RuntimeError("Must call reset() before step()")
        
        if self._state.done:
            raise RuntimeError("Episode is done. Call reset().")
        
        prev_state_hash = self._state.get_hash()
        
        # Update iteration
        self._state.iteration += 1
        self._state.current_code = code
        
        # Execute code
        run_result = self._execute(code)
        
        # Update state based on results
        self._update_state(run_result)
        
        # Compute reward
        reward = self.reward_computer.compute(
            compile_result=None,  # Runner handles this internally
            run_result=run_result,
            tests_passed=self._state.tests_passed,
            tests_failed=self._state.tests_failed,
            is_correct=self._state.is_correct,
            step_number=self._state.iteration,
        )
        
        # Check if done
        if self._state.is_correct:
            self._state.done = True
        elif self._state.iteration >= self.max_iterations:
            self._state.done = True
        
        # Store experience
        experience = Experience(
            problem_id=self._state.problem.id,
            state_hash=prev_state_hash,
            action=f"submit_code:{len(code)}",
            reward=reward.total,
            next_state_hash=self._state.get_hash(),
            done=self._state.done,
            metadata={
                "tests_passed": self._state.tests_passed,
                "is_correct": self._state.is_correct,
            },
        )
        self.memory.store_experience(experience)
        
        # Store solution if correct
        if self._state.is_correct:
            solution = Solution(
                problem_id=self._state.problem.id,
                code=code,
                language=self.language.value,
                answer=self._state.last_output or "",
                duration_ms=run_result.duration_ms if run_result else 0,
                iterations=self._state.iteration,
            )
            self.memory.store_solution(solution)
        
        return StepResult(
            state=self._state,
            reward=reward,
            done=self._state.done,
            info={
                "run_result": run_result.to_dict() if run_result else None,
                "problem_id": self._state.problem.id,
            },
        )
    
    def _execute(self, code: str) -> Optional[RunResult]:
        """Execute code and return result."""
        if not self.runner.is_available():
            return RunResult(
                success=False,
                stderr=f"{self.language.value} runtime not available",
                exit_code=-1,
            )
        
        # Use the first example as test input
        if self._state.problem.examples:
            test_input, expected = self._state.problem.examples[0]
        else:
            test_input = self._state.problem.input_data
            expected = self._state.problem.expected_answer
        
        return self.runner.run(
            code=code,
            input_data=test_input,
            work_dir=self._work_dir,
            timeout_sec=30.0,
        )
    
    def _update_state(self, run_result: Optional[RunResult]) -> None:
        """Update state based on run result."""
        if run_result is None:
            self._state.tests_failed += 1
            self._state.last_error = "Failed to execute"
            return
        
        self._state.last_output = run_result.output_value
        
        if run_result.timed_out:
            self._state.tests_failed += 1
            self._state.last_error = "Timeout"
            return
        
        if not run_result.success:
            self._state.tests_failed += 1
            self._state.last_error = run_result.stderr[:200]
            return
        
        # Check against examples
        passed = 0
        failed = 0
        
        for test_input, expected in self._state.problem.examples:
            result = self.runner.run(
                code=self._state.current_code,
                input_data=test_input,
                work_dir=self._work_dir,
                timeout_sec=10.0,
            )
            
            if result.success and result.output_value == expected.strip():
                passed += 1
            else:
                failed += 1
        
        self._state.tests_passed = passed
        self._state.tests_failed = failed
        self._state.last_error = None if failed == 0 else f"Failed {failed} tests"
        
        # Check if all tests pass
        if failed == 0 and passed > 0:
            # Verify against expected answer
            if self._state.problem.expected_answer:
                self._state.is_correct = (
                    run_result.output_value == self._state.problem.expected_answer.strip()
                )
            else:
                self._state.is_correct = True
    
    def get_problem_prompt(self) -> str:
        """Get a prompt describing the current problem."""
        if self._state is None:
            return ""
        
        p = self._state.problem
        prompt = f"""# {p.title}

{p.description}

## Examples
"""
        for i, (inp, out) in enumerate(p.examples, 1):
            prompt += f"\n### Example {i}\nInput:\n```\n{inp}\n```\nOutput:\n```\n{out}\n```\n"
        
        return prompt
    
    def close(self) -> None:
        """Clean up resources."""
        if self._work_dir:
            import shutil
            shutil.rmtree(self._work_dir, ignore_errors=True)
            self._work_dir = None


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demonstrate the RL environment."""
    print("=" * 60)
    print("🧠 RL Environment Demo")
    print("=" * 60)
    print()
    
    # Create environment
    env = CodeAgentEnv(
        problem_type=ProblemType.AOC,
        difficulty="easy",
        language=Language.PYTHON,
        max_iterations=5,
    )
    
    # Show available problems
    print(f"📊 Problem Generator Stats: {env.problem_generator.get_statistics()}")
    print()
    
    # Reset with a specific problem
    state = env.reset(problem_id="aoc_2015_day01_part1")
    
    print(f"🎯 Problem: {state.problem.title}")
    print(f"   ID: {state.problem.id}")
    print(f"   Type: {state.problem.problem_type.value}")
    print(f"   Difficulty: {state.problem.difficulty}")
    print()
    
    print("📝 Problem Prompt:")
    print("-" * 40)
    prompt = env.get_problem_prompt()
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print()
    
    # Solve with a correct solution
    solution = '''import sys

def solve(data):
    floor = 0
    for c in data:
        if c == '(':
            floor += 1
        elif c == ')':
            floor -= 1
    return str(floor)

if __name__ == "__main__":
    print(solve(sys.stdin.read().strip()))
'''
    
    print("🚀 Submitting solution...")
    result = env.step(solution)
    
    print(f"   Tests Passed: {result.state.tests_passed}")
    print(f"   Tests Failed: {result.state.tests_failed}")
    print(f"   Correct: {result.state.is_correct}")
    print(f"   Reward: {result.reward.total:.1f}")
    print(f"   Done: {result.done}")
    print()
    
    print("💰 Reward Breakdown:")
    for k, v in result.reward.to_dict().items():
        if v != 0:
            print(f"   {k}: {v:.1f}")
    print()
    
    print(f"📊 Memory Stats: {env.memory.get_statistics()}")
    
    env.close()
    print()
    print("✅ Demo complete!")


if __name__ == "__main__":
    demo()
