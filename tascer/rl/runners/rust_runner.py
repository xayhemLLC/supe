"""Rust language runner."""

import os
import shutil
import subprocess
import time
from typing import Optional

from .base import LanguageRunner, Language, CompileResult, RunResult


class RustRunner(LanguageRunner):
    """Runner for Rust code.
    
    Rust requires compilation before execution. Uses rustc directly
    for simple single-file programs.
    """
    
    def __init__(self, rustc_path: Optional[str] = None):
        self.rustc_path = rustc_path or "rustc"
    
    @property
    def language(self) -> Language:
        return Language.RUST
    
    @property
    def file_extension(self) -> str:
        return ".rs"
    
    def is_available(self) -> bool:
        """Check if rustc is available."""
        return shutil.which(self.rustc_path) is not None
    
    def compile(self, code: str, work_dir: str) -> CompileResult:
        """Compile Rust code with rustc."""
        start = time.time()
        
        # Write source file
        source_path = os.path.join(work_dir, "solution.rs")
        output_path = os.path.join(work_dir, "solution")
        
        with open(source_path, "w") as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                [
                    self.rustc_path,
                    source_path,
                    "-o", output_path,
                    "-O",  # Optimize
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=work_dir,
            )
            
            duration = (time.time() - start) * 1000
            
            if result.returncode == 0:
                return CompileResult(
                    success=True,
                    output_path=output_path,
                    warnings=result.stderr if "warning" in result.stderr.lower() else "",
                    duration_ms=duration,
                )
            else:
                return CompileResult(
                    success=False,
                    errors=result.stderr,
                    duration_ms=duration,
                )
        except subprocess.TimeoutExpired:
            return CompileResult(
                success=False,
                errors="Compilation timed out after 60s",
                duration_ms=(time.time() - start) * 1000,
            )
        except FileNotFoundError:
            return CompileResult(
                success=False,
                errors=f"rustc not found at: {self.rustc_path}",
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
        """Compile and run Rust code."""
        # First compile
        compile_result = self.compile(code, work_dir)
        
        if not compile_result.success:
            return RunResult(
                success=False,
                stderr=f"Compilation failed:\n{compile_result.errors}",
                exit_code=-1,
                duration_ms=compile_result.duration_ms,
            )
        
        # Then run
        start = time.time()
        
        try:
            result = subprocess.run(
                [compile_result.output_path],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                cwd=work_dir,
            )
            
            duration = compile_result.duration_ms + (time.time() - start) * 1000
            
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
                duration_ms=compile_result.duration_ms + timeout_sec * 1000,
                timed_out=True,
            )
        except Exception as e:
            return RunResult(
                success=False,
                stderr=str(e),
                exit_code=-1,
                duration_ms=compile_result.duration_ms + (time.time() - start) * 1000,
            )
    
    def get_solution_template(self) -> str:
        return '''use std::io::{self, Read};

fn solve(input: &str) -> String {
    let lines: Vec<&str> = input.trim().lines().collect();
    // TODO: Implement solution
    String::new()
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    println!("{}", solve(&input));
}
'''
