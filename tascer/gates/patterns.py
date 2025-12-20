"""TASC_GATE_STDOUT_STDERR_PATTERNS - Pattern matching for output validation.

Features:
- Denylist patterns (ERROR, Unhandled, stack traces)
- Allowlist exceptions
- Severity thresholds (warnings allowed <= N)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from ..contracts import GateResult


@dataclass
class PatternMatch:
    """A matched pattern in output."""
    
    pattern: str
    line_number: int
    line: str
    source: str  # stdout | stderr


@dataclass
class PatternGate:
    """Gate that validates stdout/stderr against pattern rules.
    
    Denylist patterns must NOT appear (unless in allowlist exceptions).
    Allowlist patterns override denylist matches.
    """
    
    # Patterns that must NOT appear in output
    denylist: List[str] = field(default_factory=lambda: [
        r"(?i)error[:\s]",
        r"(?i)exception[:\s]",
        r"(?i)traceback",
        r"(?i)unhandled",
        r"(?i)fatal[:\s]",
        r"(?i)panic[:\s]",
    ])
    
    # Patterns that override denylist (allowed even if in denylist)
    allowlist_exceptions: List[str] = field(default_factory=list)
    
    # Maximum number of warnings allowed
    severity_threshold: int = 0
    
    # Warning patterns (counted but don't fail if under threshold)
    warning_patterns: List[str] = field(default_factory=lambda: [
        r"(?i)warning[:\s]",
        r"(?i)warn[:\s]",
        r"(?i)deprecated",
    ])
    
    # Whether to check stdout
    check_stdout: bool = True
    
    # Whether to check stderr
    check_stderr: bool = True
    
    def _find_matches(
        self,
        text: str,
        patterns: List[str],
        source: str,
    ) -> List[PatternMatch]:
        """Find all pattern matches in text."""
        matches = []
        lines = text.split("\n")
        
        for pattern in patterns:
            try:
                regex = re.compile(pattern)
                for i, line in enumerate(lines, 1):
                    if regex.search(line):
                        matches.append(PatternMatch(
                            pattern=pattern,
                            line_number=i,
                            line=line[:200],  # Truncate long lines
                            source=source,
                        ))
            except re.error:
                continue
        
        return matches
    
    def _is_allowed(self, match: PatternMatch) -> bool:
        """Check if a match is in the allowlist exceptions."""
        for pattern in self.allowlist_exceptions:
            try:
                if re.search(pattern, match.line):
                    return True
            except re.error:
                continue
        return False
    
    def check(
        self,
        stdout: str = "",
        stderr: str = "",
    ) -> GateResult:
        """Check stdout/stderr for forbidden patterns.
        
        Args:
            stdout: Command stdout.
            stderr: Command stderr.
        
        Returns:
            GateResult with pass/fail status and matched patterns.
        """
        denied_matches: List[PatternMatch] = []
        warning_matches: List[PatternMatch] = []
        
        # Check stdout
        if self.check_stdout and stdout:
            matches = self._find_matches(stdout, self.denylist, "stdout")
            for match in matches:
                if not self._is_allowed(match):
                    denied_matches.append(match)
            warning_matches.extend(
                self._find_matches(stdout, self.warning_patterns, "stdout")
            )
        
        # Check stderr
        if self.check_stderr and stderr:
            matches = self._find_matches(stderr, self.denylist, "stderr")
            for match in matches:
                if not self._is_allowed(match):
                    denied_matches.append(match)
            warning_matches.extend(
                self._find_matches(stderr, self.warning_patterns, "stderr")
            )
        
        # Determine pass/fail
        warnings_over_threshold = len(warning_matches) > self.severity_threshold
        passed = len(denied_matches) == 0 and not warnings_over_threshold
        
        # Build message
        if passed:
            message = "No forbidden patterns found"
            if warning_matches:
                message += f" ({len(warning_matches)} warnings within threshold)"
        else:
            parts = []
            if denied_matches:
                parts.append(f"{len(denied_matches)} forbidden pattern(s) found")
            if warnings_over_threshold:
                parts.append(
                    f"{len(warning_matches)} warnings exceed threshold of {self.severity_threshold}"
                )
            message = "; ".join(parts)
        
        return GateResult(
            gate_name="STDOUT_STDERR_PATTERNS",
            passed=passed,
            message=message,
            evidence={
                "denied_matches": [
                    {"pattern": m.pattern, "line": m.line_number, "source": m.source}
                    for m in denied_matches[:10]  # Limit to first 10
                ],
                "warning_count": len(warning_matches),
                "severity_threshold": self.severity_threshold,
            },
        )
    
    def check_terminal_result(self, result) -> GateResult:
        """Check a TerminalResult object.
        
        Args:
            result: A TerminalResult from run_and_observe.
        
        Returns:
            GateResult with pass/fail status.
        """
        return self.check(result.stdout, result.stderr)
