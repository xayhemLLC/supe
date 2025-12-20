"""TypeScript language runner."""

import os
import shutil
import subprocess
import time
from typing import Optional

from .base import LanguageRunner, Language, CompileResult, RunResult


class TypeScriptRunner(LanguageRunner):
    """Runner for TypeScript code.
    
    Supports multiple runtimes:
    - Deno (preferred - built-in TS support)
    - ts-node (fallback)
    - npx tsx (another fallback)
    """
    
    def __init__(
        self,
        deno_path: Optional[str] = None,
        ts_node_path: Optional[str] = None,
    ):
        self.deno_path = deno_path or "deno"
        self.ts_node_path = ts_node_path or "npx"
        self._runtime: Optional[str] = None
    
    @property
    def language(self) -> Language:
        return Language.TYPESCRIPT
    
    @property
    def file_extension(self) -> str:
        return ".ts"
    
    def is_available(self) -> bool:
        """Check if any TypeScript runtime is available."""
        return self._detect_runtime() is not None
    
    def _detect_runtime(self) -> Optional[str]:
        """Detect which TS runtime is available."""
        if self._runtime:
            return self._runtime
        
        # Try Deno first (best TS support)
        if shutil.which(self.deno_path):
            self._runtime = "deno"
            return "deno"
        
        # Try npx tsx
        try:
            result = subprocess.run(
                ["npx", "--version"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                self._runtime = "tsx"
                return "tsx"
        except Exception:
            pass
        
        return None
    
    def compile(self, code: str, work_dir: str) -> CompileResult:
        """Type-check TypeScript code without running."""
        start = time.time()
        runtime = self._detect_runtime()
        
        if not runtime:
            return CompileResult(
                success=False,
                errors="No TypeScript runtime found (install Deno or Node.js)",
                duration_ms=0,
            )
        
        # Write source file
        source_path = os.path.join(work_dir, "solution.ts")
        with open(source_path, "w") as f:
            f.write(code)
        
        try:
            if runtime == "deno":
                # Deno has built-in type checking
                result = subprocess.run(
                    [self.deno_path, "check", source_path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=work_dir,
                )
            else:
                # Use tsc for type checking
                result = subprocess.run(
                    ["npx", "tsc", "--noEmit", source_path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=work_dir,
                )
            
            duration = (time.time() - start) * 1000
            
            if result.returncode == 0:
                return CompileResult(
                    success=True,
                    output_path=source_path,
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
                errors="Type checking timed out",
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
        """Run TypeScript code."""
        start = time.time()
        runtime = self._detect_runtime()
        
        if not runtime:
            return RunResult(
                success=False,
                stderr="No TypeScript runtime found (install Deno or Node.js)",
                exit_code=-1,
                duration_ms=0,
            )
        
        # Write source file
        source_path = os.path.join(work_dir, "solution.ts")
        with open(source_path, "w") as f:
            f.write(code)
        
        try:
            if runtime == "deno":
                cmd = [
                    self.deno_path, "run",
                    "--allow-read",  # Allow reading stdin
                    source_path,
                ]
            else:
                cmd = ["npx", "tsx", source_path]
            
            result = subprocess.run(
                cmd,
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
        return '''// Solution for the problem

function solve(input: string): string {
    const lines = input.trim().split("\\n");
    // TODO: Implement solution
    return "";
}

// Read from stdin
const decoder = new TextDecoder();
const chunks: Uint8Array[] = [];

// Deno-compatible stdin reading
declare const Deno: any;
if (typeof Deno !== "undefined") {
    const buf = new Uint8Array(1024);
    let n: number | null;
    while ((n = Deno.stdin.readSync(buf)) !== null) {
        chunks.push(buf.slice(0, n));
    }
    const input = decoder.decode(new Uint8Array(chunks.flatMap(c => [...c])));
    console.log(solve(input));
} else {
    // Node.js fallback
    process.stdin.on("data", (chunk: Buffer) => chunks.push(chunk));
    process.stdin.on("end", () => {
        const input = Buffer.concat(chunks).toString();
        console.log(solve(input));
    });
}
'''
