"""Python language runner."""

import os
import subprocess
import sys
import tempfile
import time
from typing import Optional

from .base import LanguageRunner, Language, CompileResult, RunResult


class PythonRunner(LanguageRunner):
    """Runner for Python code.
    
    Python is interpreted, so 'compile' just does syntax checking.
    """
    
    def __init__(self, python_path: Optional[str] = None):
        self.python_path = python_path or sys.executable
    
    @property
    def language(self) -> Language:
        return Language.PYTHON
    
    @property
    def file_extension(self) -> str:
        return ".py"
    
    def is_available(self) -> bool:
        """Python is always available since we're running in Python."""
        return True
    
    def compile(self, code: str, work_dir: str) -> CompileResult:
        """Check Python syntax without executing.
        
        Uses py_compile for syntax validation.
        """
        start = time.time()
        
        # Write to temp file
        code_path = os.path.join(work_dir, "solution.py")
        with open(code_path, "w") as f:
            f.write(code)
        
        try:
            # Syntax check using -m py_compile
            result = subprocess.run(
                [self.python_path, "-m", "py_compile", code_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            duration = (time.time() - start) * 1000
            
            if result.returncode == 0:
                return CompileResult(
                    success=True,
                    output_path=code_path,
                    duration_ms=duration,
                )
            else:
                return CompileResult(
                    success=False,
                    errors=result.stderr or result.stdout,
                    duration_ms=duration,
                )
        except subprocess.TimeoutExpired:
            return CompileResult(
                success=False,
                errors="Syntax check timed out",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return CompileResult(
                success=False,
                errors=str(e),
                duration_ms=(time.time() - start) * 1000,
            )
    
    def run(
        self,
        code: str,
        input_data: str,
        work_dir: str,
        timeout_sec: float = 30.0,
    ) -> RunResult:
        """Execute Python code with given input."""
        start = time.time()
        
        # Write code to file
        code_path = os.path.join(work_dir, "solution.py")
        with open(code_path, "w") as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                [self.python_path, code_path],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                cwd=work_dir,
            )
            
            duration = (time.time() - start) * 1000
            
            return RunResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration_ms=duration,
                output_value=result.stdout.strip().split('\n')[-1] if result.stdout else None,
            )
        except subprocess.TimeoutExpired:
            return RunResult(
                success=False,
                stderr=f"Execution timed out after {timeout_sec}s",
                exit_code=-1,
                duration_ms=timeout_sec * 1000,
                timed_out=True,
            )
        except Exception as e:
            return RunResult(
                success=False,
                stderr=str(e),
                exit_code=-1,
                duration_ms=(time.time() - start) * 1000,
            )
    
    def get_solution_template(self) -> str:
        return '''#!/usr/bin/env python3
"""Solution for the problem."""
import sys

def solve(data: str) -> str:
    """Solve the problem.
    
    Args:
        data: Input data as a string.
    
    Returns:
        The answer as a string.
    """
    lines = data.strip().split("\\n")
    # TODO: Implement solution
    return ""

if __name__ == "__main__":
    print(solve(sys.stdin.read()))
'''
