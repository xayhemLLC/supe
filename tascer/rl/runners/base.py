"""Base interface for language runners.

Language runners compile and execute code in different programming languages.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any


class Language(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    RUST = "rust"
    TYPESCRIPT = "typescript"


@dataclass
class CompileResult:
    """Result of code compilation."""
    
    success: bool
    errors: str = ""
    warnings: str = ""
    output_path: Optional[str] = None
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "errors": self.errors,
            "warnings": self.warnings,
            "output_path": self.output_path,
            "duration_ms": self.duration_ms,
        }


@dataclass
class RunResult:
    """Result of code execution."""
    
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: float = 0.0
    timed_out: bool = False
    memory_mb: float = 0.0
    
    # Parsed output (for verification)
    output_value: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "timed_out": self.timed_out,
            "memory_mb": self.memory_mb,
            "output_value": self.output_value,
        }


class LanguageRunner(ABC):
    """Abstract base class for language-specific code runners.
    
    Each language runner handles:
    - Compilation (if needed)
    - Execution
    - Output parsing
    - Timeout handling
    """
    
    @property
    @abstractmethod
    def language(self) -> Language:
        """Return the language this runner handles."""
        pass
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this language."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this language runtime is available."""
        pass
    
    @abstractmethod
    def compile(self, code: str, work_dir: str) -> CompileResult:
        """Compile the code (or validate for interpreted languages).
        
        Args:
            code: Source code to compile.
            work_dir: Working directory for compilation.
        
        Returns:
            CompileResult with success status and any errors.
        """
        pass
    
    @abstractmethod
    def run(
        self,
        code: str,
        input_data: str,
        work_dir: str,
        timeout_sec: float = 30.0,
    ) -> RunResult:
        """Execute the code with given input.
        
        Args:
            code: Source code to run.
            input_data: Input to pass to the program via stdin.
            work_dir: Working directory for execution.
            timeout_sec: Maximum execution time.
        
        Returns:
            RunResult with stdout, stderr, exit code, etc.
        """
        pass
    
    def get_solution_template(self) -> str:
        """Return a template for solutions in this language."""
        return ""
    
    def wrap_for_stdin(self, code: str) -> str:
        """Wrap code to read from stdin if needed."""
        return code


def get_runner(language: Language) -> LanguageRunner:
    """Get the appropriate runner for a language."""
    from .python_runner import PythonRunner
    from .rust_runner import RustRunner
    from .typescript_runner import TypeScriptRunner
    
    runners = {
        Language.PYTHON: PythonRunner,
        Language.RUST: RustRunner,
        Language.TYPESCRIPT: TypeScriptRunner,
    }
    
    runner_class = runners.get(language)
    if runner_class is None:
        raise ValueError(f"No runner for language: {language}")
    
    return runner_class()
