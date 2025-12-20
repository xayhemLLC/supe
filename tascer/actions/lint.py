"""ACTION_LINT_FIX_LOOP - Iterative lint fixing.

Hypothesis: "We can converge to lint-pass within bounded iterations."

Features:
- Iteration budget
- Detect "stuck" (same errors repeating)
- Each iteration emits diff + lint output
- Produces "root-cause summary" if cannot converge
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..primitives.terminal import run_and_observe, TerminalResult


@dataclass
class LintIteration:
    """Record of a single lint iteration."""
    
    iteration: int
    exit_code: int
    error_count: int
    errors: List[str]
    fixed_in_iteration: int = 0


@dataclass
class LintFixResult:
    """Result of lint fix loop."""
    
    success: bool
    converged: bool
    iterations_used: int
    max_iterations: int
    initial_error_count: int
    final_error_count: int
    iterations: List[LintIteration] = field(default_factory=list)
    stuck_reason: Optional[str] = None
    root_cause_summary: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "converged": self.converged,
            "iterations_used": self.iterations_used,
            "max_iterations": self.max_iterations,
            "initial_error_count": self.initial_error_count,
            "final_error_count": self.final_error_count,
            "stuck_reason": self.stuck_reason,
            "root_cause_summary": self.root_cause_summary,
        }


def lint_fix_loop(
    lint_cmd: str = "ruff check .",
    fix_cmd: Optional[str] = "ruff check . --fix",
    cwd: Optional[str] = None,
    max_iterations: int = 5,
    timeout_per_iteration: float = 60,
) -> LintFixResult:
    """Run lint-fix loop until passing or iteration budget exhausted.
    
    ACTION_LINT_FIX_LOOP implementation.
    
    Args:
        lint_cmd: Command to check lint status.
        fix_cmd: Command to auto-fix issues. If None, only checks.
        cwd: Working directory.
        max_iterations: Maximum fix iterations before giving up.
        timeout_per_iteration: Timeout for each command.
    
    Returns:
        LintFixResult with convergence status and iteration history.
    """
    if cwd is None:
        cwd = os.getcwd()
    
    iterations: List[LintIteration] = []
    previous_errors: set = set()
    
    # Initial lint check
    initial_result = run_and_observe(
        lint_cmd,
        cwd=cwd,
        timeout_sec=timeout_per_iteration,
        shell=True,
    )
    
    initial_errors = _parse_lint_errors(initial_result.stdout + initial_result.stderr)
    initial_error_count = len(initial_errors)
    
    if initial_result.exit_code == 0:
        # Already passing
        return LintFixResult(
            success=True,
            converged=True,
            iterations_used=0,
            max_iterations=max_iterations,
            initial_error_count=0,
            final_error_count=0,
        )
    
    iterations.append(LintIteration(
        iteration=0,
        exit_code=initial_result.exit_code,
        error_count=initial_error_count,
        errors=initial_errors[:20],  # Limit stored errors
    ))
    previous_errors = set(initial_errors)
    
    # Fix loop
    for i in range(1, max_iterations + 1):
        if fix_cmd is None:
            # No fix command, can't iterate
            break
        
        # Run fix command
        fix_result = run_and_observe(
            fix_cmd,
            cwd=cwd,
            timeout_sec=timeout_per_iteration,
            shell=True,
        )
        
        # Check lint status after fix
        check_result = run_and_observe(
            lint_cmd,
            cwd=cwd,
            timeout_sec=timeout_per_iteration,
            shell=True,
        )
        
        current_errors = _parse_lint_errors(check_result.stdout + check_result.stderr)
        current_error_count = len(current_errors)
        
        # Calculate fixed count
        fixed_count = len(previous_errors) - len(set(current_errors) & previous_errors)
        
        iterations.append(LintIteration(
            iteration=i,
            exit_code=check_result.exit_code,
            error_count=current_error_count,
            errors=current_errors[:20],
            fixed_in_iteration=max(0, iterations[-1].error_count - current_error_count),
        ))
        
        if check_result.exit_code == 0:
            # Converged!
            return LintFixResult(
                success=True,
                converged=True,
                iterations_used=i,
                max_iterations=max_iterations,
                initial_error_count=initial_error_count,
                final_error_count=0,
                iterations=iterations,
            )
        
        # Check if stuck (same errors repeating)
        current_error_set = set(current_errors)
        if current_error_set == previous_errors:
            root_cause = _analyze_root_cause(current_errors)
            return LintFixResult(
                success=False,
                converged=False,
                iterations_used=i,
                max_iterations=max_iterations,
                initial_error_count=initial_error_count,
                final_error_count=current_error_count,
                iterations=iterations,
                stuck_reason="Same errors repeating - auto-fix cannot resolve",
                root_cause_summary=root_cause,
            )
        
        previous_errors = current_error_set
    
    # Exhausted iterations
    final_errors = iterations[-1].errors if iterations else []
    root_cause = _analyze_root_cause(final_errors)
    
    return LintFixResult(
        success=False,
        converged=False,
        iterations_used=max_iterations,
        max_iterations=max_iterations,
        initial_error_count=initial_error_count,
        final_error_count=iterations[-1].error_count if iterations else initial_error_count,
        iterations=iterations,
        stuck_reason="Max iterations exhausted",
        root_cause_summary=root_cause,
    )


def _parse_lint_errors(output: str) -> List[str]:
    """Parse lint output to extract error messages."""
    errors = []
    for line in output.split("\n"):
        line = line.strip()
        # Common lint error patterns
        if any(indicator in line for indicator in [
            ": error:",
            ": E",
            ": F",
            ": W",
            "error[",
        ]):
            errors.append(line[:200])  # Truncate long lines
        elif line and ":" in line and not line.startswith(" "):
            # Generic file:line:col pattern
            parts = line.split(":")
            if len(parts) >= 3 and parts[1].isdigit():
                errors.append(line[:200])
    return errors


def _analyze_root_cause(errors: List[str]) -> str:
    """Analyze errors to produce a root cause summary."""
    if not errors:
        return "No errors to analyze"
    
    # Group by error type/code
    error_types: Dict[str, int] = {}
    files_affected: set = set()
    
    for error in errors:
        # Try to extract error code
        parts = error.split()
        for part in parts:
            if part.startswith("E") and len(part) <= 5:
                error_types[part] = error_types.get(part, 0) + 1
            elif part.startswith("F") and len(part) <= 5:
                error_types[part] = error_types.get(part, 0) + 1
        
        # Extract file
        if ":" in error:
            file_part = error.split(":")[0]
            if "/" in file_part or file_part.endswith(".py"):
                files_affected.add(file_part)
    
    lines = [f"Affecting {len(files_affected)} file(s)"]
    
    if error_types:
        top_types = sorted(error_types.items(), key=lambda x: -x[1])[:5]
        lines.append("Top error types: " + ", ".join(f"{t}({n})" for t, n in top_types))
    
    return "; ".join(lines)
