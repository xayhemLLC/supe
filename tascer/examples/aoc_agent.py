#!/usr/bin/env python3
"""AoC Agent - AI Coding Agent for Advent of Code using Tascers.

This module demonstrates how to build an autonomous AI agent that can solve
Advent of Code problems using the Tasc framework for:
- Safety (checkpoints, legality checks)
- Observability (dual ledgers)
- Control (Overlord decisions)
- Reversibility (sandbox mode)

Usage:
    from tascer.examples.aoc_agent import AocAgent, solve_problem
    
    # Quick solve
    result = solve_problem(day=1, part=1, year=2024)
    
    # Or with more control
    agent = AocAgent(day=1, part=1, year=2024, workspace="./aoc_workspace")
    agent.run()
"""

import hashlib
import os
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from tasc import Tasc

from tascer.checkpoint import CheckpointManager
from tascer.ledgers import LedgerStorage
from tascer.ledgers.exe import ConfidenceScore, StopReason
from tascer.overlord.decision import (
    StopConditionState,
    StopCondition,
    OverlordDecision,
    should_stop,
    create_continue_decision,
)
from tascer.overlord.legality import check_action_legality
from tascer.primitives import run_and_observe, capture_context
from tascer.audit import export_to_markdown


@dataclass
class AocProblem:
    """Represents an Advent of Code problem."""
    
    day: int
    part: int
    year: int
    title: str = ""
    description: str = ""
    examples: List[Tuple[str, str]] = field(default_factory=list)  # (input, expected)
    puzzle_input: str = ""


@dataclass  
class AgentResult:
    """Result from running the AoC agent."""
    
    success: bool
    answer: Optional[str] = None
    iterations: int = 0
    stop_reason: Optional[StopCondition] = None
    audit_path: Optional[str] = None
    solution_code: Optional[str] = None


class AocAgent:
    """AI Agent that solves Advent of Code problems using Tascers.
    
    The agent follows a structured workflow:
    1. Initialize Tasc infrastructure (checkpoint, ledgers)
    2. Define the task as a Tasc
    3. Fetch/parse the problem
    4. Loop: generate code → test → refine (controlled by Overlord)
    5. Submit answer when tests pass
    6. Export audit trail
    
    Attributes:
        day: AoC day number (1-25)
        part: Part number (1 or 2)
        year: AoC year
        workspace: Directory for agent files
        code_generator: Optional callback to generate solution code
    """
    
    def __init__(
        self,
        day: int,
        part: int,
        year: int = 2024,
        workspace: Optional[str] = None,
        code_generator: Optional[Callable[[AocProblem, Optional[str]], str]] = None,
        max_iterations: int = 20,
    ):
        self.day = day
        self.part = part
        self.year = year
        self.workspace = workspace or tempfile.mkdtemp(prefix=f"aoc_{year}_day{day}_")
        self.code_generator = code_generator or self._default_code_generator
        self.max_iterations = max_iterations
        
        # Create workspace structure
        os.makedirs(self.workspace, exist_ok=True)
        os.makedirs(f"{self.workspace}/output", exist_ok=True)
        os.makedirs(f"{self.workspace}/evidence", exist_ok=True)
        
        # Initialize Tasc infrastructure
        self.run_id = f"aoc_{year}_day{day}_part{part}_{datetime.now().strftime('%H%M%S')}"
        
        self.checkpoint_mgr = CheckpointManager(
            run_id=self.run_id,
            root_dir=self.workspace,
            output_dir=f"{self.workspace}/output",
        )
        
        self.ledger = LedgerStorage(
            run_id=self.run_id,
            output_dir=f"{self.workspace}/output",
        )
        
        # Overlord state
        self.state = StopConditionState(
            legal_actions={"file.write", "file.read", "terminal.run"},
            max_actions=max_iterations * 3,  # ~3 actions per iteration
            hypothesis=f"Solve AoC {year} Day {day} Part {part}",
        )
        
        # Problem and solution state
        self.problem: Optional[AocProblem] = None
        self.current_solution: Optional[str] = None
        self.iteration = 0
        self.last_error: Optional[str] = None
        
    def _create_tasc(self) -> Tasc:
        """Create a Tasc representing this AoC problem."""
        return Tasc(
            id=f"aoc_{self.year}_day{self.day:02d}_part{self.part}",
            status="in_progress",
            title=f"Solve Advent of Code {self.year} Day {self.day} Part {self.part}",
            additional_notes=self.problem.description if self.problem else "",
            testing_instructions="Run solution.py with puzzle input, verify against examples first.",
            desired_outcome="Correct answer that passes all test cases",
            dependencies=[],
        )
    
    def _default_code_generator(
        self, 
        problem: AocProblem, 
        previous_error: Optional[str] = None
    ) -> str:
        """Default code generator - creates a template solution.
        
        In a real implementation, this would call an LLM to generate code.
        Here we provide a simple template for demonstration.
        """
        template = f'''#!/usr/bin/env python3
"""Advent of Code {problem.year} Day {problem.day} Part {problem.part}

{problem.title}
"""

import sys


def solve(data: str) -> str:
    """Solve the puzzle.
    
    Args:
        data: Puzzle input as a string.
    
    Returns:
        The answer as a string.
    """
    lines = data.strip().split("\\n")
    
    # TODO: Implement solution
    # Problem: {problem.description[:200]}...
    
    # Placeholder - return first line length as demo
    return str(len(lines[0]) if lines else 0)


def main():
    data = sys.stdin.read()
    answer = solve(data)
    print(answer)


if __name__ == "__main__":
    main()
'''
        return template
    
    def load_problem(self, problem: AocProblem) -> None:
        """Load an AoC problem for the agent to solve."""
        self.problem = problem
        
        # Save puzzle input to workspace
        input_path = f"{self.workspace}/puzzle_input.txt"
        with open(input_path, "w") as f:
            f.write(problem.puzzle_input)
        
        # Save examples
        for i, (example_in, example_out) in enumerate(problem.examples):
            with open(f"{self.workspace}/example_{i+1}_input.txt", "w") as f:
                f.write(example_in)
            with open(f"{self.workspace}/example_{i+1}_expected.txt", "w") as f:
                f.write(example_out)
        
        self.ledger.moments.record_context({
            "problem_year": problem.year,
            "problem_day": problem.day,
            "problem_part": problem.part,
            "examples_count": len(problem.examples),
            "input_size": len(problem.puzzle_input),
        })
    
    def run(self) -> AgentResult:
        """Run the agent to solve the AoC problem.
        
        Returns:
            AgentResult with success status, answer, and audit trail.
        """
        if not self.problem:
            return AgentResult(
                success=False,
                stop_reason=StopCondition.NO_LEGAL_ACTIONS,
            )
        
        # 1. Create safety checkpoint
        checkpoint = self.checkpoint_mgr.create(
            f"Before solving AoC {self.year} Day {self.day} Part {self.part}"
        )
        
        # 2. Record intent in Exe ledger
        self.ledger.exe.record_narrative(
            f"Starting AoC {self.year} Day {self.day} Part {self.part}. "
            f"Strategy: Generate code, test against {len(self.problem.examples)} examples, "
            f"iterate until all pass or budget exhausted."
        )
        
        # 3. Main agent loop
        answer = None
        while self.iteration < self.max_iterations:
            # Check Overlord for stop conditions
            decision = should_stop(self.state)
            if decision:
                self.ledger.exe.record_stop(
                    StopReason.GOAL_ACHIEVED if self.state.goal_achieved
                    else StopReason.BUDGET_EXHAUSTED,
                    decision.narrative,
                )
                break
            
            self.iteration += 1
            
            # Generate/refine solution
            self._generate_solution()
            
            # Test against examples
            passed, answer = self._test_solution()
            
            if passed:
                self.state.goal_achieved = True
            else:
                self.state.actions_taken += 1
        
        # 4. Export audit trail
        audit_path = self._export_audit()
        
        return AgentResult(
            success=self.state.goal_achieved,
            answer=answer if self.state.goal_achieved else None,
            iterations=self.iteration,
            stop_reason=self.state.hypothesis_status,
            audit_path=audit_path,
            solution_code=self.current_solution,
        )
    
    def _generate_solution(self) -> None:
        """Generate or refine the solution code."""
        
        # Record proposal in Exe ledger
        self.ledger.exe.record_proposal(
            action_id="file.write",
            narrative=f"Generating solution (iteration {self.iteration})"
                     + (f", fixing: {self.last_error[:100]}" if self.last_error else ""),
            confidence=ConfidenceScore(
                value=0.5 + (0.1 * min(self.iteration, 4)),  # Increases with iterations
                calibration_note="Confidence increases as we learn from errors",
            ),
        )
        
        # Check legality
        legality = check_action_legality(
            action_id="file.write",
            inputs={"path": f"{self.workspace}/solution.py"},
            permissions={"file_write"},
            has_checkpoint=True,
        )
        
        if not legality.is_legal:
            self.state.safety_violations.extend(legality.violations)
            self.ledger.moments.record_action_result("file.write", {
                "status": "blocked",
                "violations": legality.violations,
            })
            return
        
        # Generate code
        self.current_solution = self.code_generator(self.problem, self.last_error)
        
        # Write to file
        solution_path = f"{self.workspace}/solution.py"
        with open(solution_path, "w") as f:
            f.write(self.current_solution)
        
        # Record in Moments ledger
        self.ledger.moments.record_action_result("file.write", {
            "path": "solution.py",
            "bytes_written": len(self.current_solution),
            "iteration": self.iteration,
        })
    
    def _test_solution(self) -> Tuple[bool, Optional[str]]:
        """Test the solution against examples.
        
        Returns:
            (all_passed, last_answer)
        """
        if not self.problem.examples:
            # No examples, just run with puzzle input
            return self._run_with_input("puzzle_input.txt")
        
        all_passed = True
        last_answer = None
        
        for i, (example_in, expected) in enumerate(self.problem.examples):
            # Record proposal
            self.ledger.exe.record_proposal(
                action_id="terminal.run",
                narrative=f"Testing against example {i+1}/{len(self.problem.examples)}",
                confidence=ConfidenceScore(0.8, "Examples are reliable test cases"),
            )
            
            # Run solution
            input_file = f"example_{i+1}_input.txt"
            result = run_and_observe(
                f"{sys.executable} solution.py < {input_file}",
                cwd=self.workspace,
                shell=True,
                timeout_sec=30,
            )
            
            actual = result.stdout.strip()
            last_answer = actual
            
            # Record in Moments
            self.ledger.moments.record_action_result("terminal.run", {
                "example": i + 1,
                "exit_code": result.exit_code,
                "expected": expected.strip(),
                "actual": actual,
                "passed": actual == expected.strip(),
                "duration_ms": result.duration_ms,
            })
            
            # Track observation hash for convergence detection
            obs_hash = hashlib.md5(
                f"{result.exit_code}:{result.stdout}:{result.stderr}".encode()
            ).hexdigest()[:8]
            self.state.recent_observation_hashes.append(obs_hash)
            
            if result.exit_code != 0:
                all_passed = False
                self.last_error = f"Exit code {result.exit_code}: {result.stderr[:200]}"
            elif actual != expected.strip():
                all_passed = False
                self.last_error = f"Expected '{expected.strip()}', got '{actual}'"
        
        if all_passed:
            self.last_error = None
        
        return all_passed, last_answer
    
    def _run_with_input(self, input_file: str) -> Tuple[bool, Optional[str]]:
        """Run solution with a specific input file."""
        result = run_and_observe(
            f"{sys.executable} solution.py < {input_file}",
            cwd=self.workspace,
            shell=True,
            timeout_sec=60,
        )
        
        self.ledger.moments.record_action_result("terminal.run", {
            "input_file": input_file,
            "exit_code": result.exit_code,
            "stdout": result.stdout[:500],
            "duration_ms": result.duration_ms,
        })
        
        if result.exit_code == 0:
            return True, result.stdout.strip()
        else:
            self.last_error = result.stderr[:200]
            return False, None
    
    def _export_audit(self) -> str:
        """Export the audit trail to markdown."""
        return export_to_markdown(
            storage=self.ledger,
            output_dir=f"{self.workspace}/output",
            hypothesis=f"Solve AoC {self.year} Day {self.day} Part {self.part}",
        )


def solve_problem(
    day: int,
    part: int = 1,
    year: int = 2024,
    problem_description: str = "",
    examples: Optional[List[Tuple[str, str]]] = None,
    puzzle_input: str = "",
    code_generator: Optional[Callable] = None,
) -> AgentResult:
    """Convenience function to solve an AoC problem.
    
    Args:
        day: Day number (1-25)
        part: Part number (1 or 2)
        year: Year
        problem_description: Problem text
        examples: List of (input, expected_output) tuples
        puzzle_input: The actual puzzle input
        code_generator: Optional custom code generator
    
    Returns:
        AgentResult with the solution
    
    Example:
        >>> result = solve_problem(
        ...     day=1, part=1, year=2024,
        ...     examples=[("1\\n2\\n3", "6")],
        ...     puzzle_input="10\\n20\\n30",
        ... )
        >>> print(result.answer)
    """
    problem = AocProblem(
        day=day,
        part=part,
        year=year,
        title=f"Day {day} Part {part}",
        description=problem_description,
        examples=examples or [],
        puzzle_input=puzzle_input,
    )
    
    agent = AocAgent(
        day=day,
        part=part,
        year=year,
        code_generator=code_generator,
    )
    agent.load_problem(problem)
    
    return agent.run()


# =============================================================================
# Demo: Solve a simple problem
# =============================================================================

def demo():
    """Demonstrate the AoC agent with a simple sum problem."""
    print("=" * 60)
    print("🎄 AoC Agent Demo - Sum of Numbers")
    print("=" * 60)
    print()
    
    # Define a simple problem: sum all numbers
    problem = AocProblem(
        day=1,
        part=1,
        year=2024,
        title="Sum of Numbers",
        description="Given a list of numbers (one per line), find their sum.",
        examples=[
            ("1\n2\n3", "6"),
            ("10\n20\n30", "60"),
        ],
        puzzle_input="100\n200\n300\n400",
    )
    
    # Custom code generator that actually solves sum problems
    def sum_generator(prob: AocProblem, error: Optional[str] = None) -> str:
        return '''#!/usr/bin/env python3
import sys

def solve(data: str) -> str:
    numbers = [int(x) for x in data.strip().split("\\n") if x]
    return str(sum(numbers))

if __name__ == "__main__":
    print(solve(sys.stdin.read()))
'''
    
    # Run the agent
    agent = AocAgent(day=1, part=1, year=2024, code_generator=sum_generator)
    agent.load_problem(problem)
    result = agent.run()
    
    print(f"✅ Success: {result.success}")
    print(f"📊 Answer: {result.answer}")
    print(f"🔄 Iterations: {result.iterations}")
    print(f"📝 Audit trail: {result.audit_path}")
    print()
    
    # Show audit trail preview
    if result.audit_path and os.path.exists(result.audit_path):
        print("Audit Trail Preview:")
        print("-" * 40)
        with open(result.audit_path) as f:
            lines = f.readlines()[:20]
            for line in lines:
                print(f"  {line.rstrip()}")
        if len(lines) >= 20:
            print("  ...")
    
    return result


if __name__ == "__main__":
    demo()
