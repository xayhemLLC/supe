"""Critiquer subagent - Reviews reasoning for errors before committing.

This subagent acts as a double-checker that:
1. Reviews each reasoning step for common errors
2. Checks for logical consistency
3. Identifies rushed or unsupported conclusions
4. Flags potential mistakes before they're committed

Inspired by the NTT complexity error where we rushed and got O(log N)
instead of O(N log N). The Critiquer would catch:
- Missing validation checkpoints
- Conclusions without evidence
- Common mistake patterns
- Logical inconsistencies

Example output:
    ┌─────────────────────────────────────────────────┐
    │  CRITIQUE REPORT                                │
    ├─────────────────────────────────────────────────┤
    │  ⚠️  Step 3: Missing validation checkpoint      │
    │  ⚠️  Step 4: Conclusion lacks evidence          │
    │  ❌  Step 5: Logical inconsistency detected     │
    ├─────────────────────────────────────────────────┤
    │  Verdict: NEEDS_REVISION (2 warnings, 1 error)  │
    └─────────────────────────────────────────────────┘
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import re

from ab.abdb import ABMemory

from .problem_solver import TASC, ReasoningStep, StepStatus, ValidationCheckpoint


class ErrorType(Enum):
    """Types of errors the critic can detect."""

    # Validation errors
    MISSING_CHECKPOINT = "missing_checkpoint"
    FAILED_CHECKPOINT = "failed_checkpoint"
    SKIPPED_VALIDATION = "skipped_validation"

    # Logic errors
    LOGICAL_INCONSISTENCY = "logical_inconsistency"
    CIRCULAR_REASONING = "circular_reasoning"
    NON_SEQUITUR = "non_sequitur"

    # Evidence errors
    UNSUPPORTED_CONCLUSION = "unsupported_conclusion"
    MISSING_EVIDENCE = "missing_evidence"
    WEAK_EVIDENCE = "weak_evidence"

    # Common mistakes
    ARITHMETIC_ERROR = "arithmetic_error"
    ORDER_CONFUSION = "order_confusion"
    SIGN_ERROR = "sign_error"
    OFF_BY_ONE = "off_by_one"

    # Process errors
    RUSHED_REASONING = "rushed_reasoning"
    INCOMPLETE_ANALYSIS = "incomplete_analysis"
    ASSUMPTION_NOT_STATED = "assumption_not_stated"


class Severity(Enum):
    """Severity levels for detected issues."""
    INFO = "info"         # Minor suggestion
    WARNING = "warning"   # Should review
    ERROR = "error"       # Must fix
    CRITICAL = "critical" # Cannot proceed


@dataclass
class CritiqueItem:
    """A single issue found during critique."""

    error_type: ErrorType
    severity: Severity
    location: str  # e.g., "Step 3", "Evidence 2"
    description: str
    suggestion: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.error_type.value,
            "severity": self.severity.value,
            "location": self.location,
            "description": self.description,
            "suggestion": self.suggestion,
            "context": self.context,
        }


class CritiqueVerdict(Enum):
    """Overall verdict from critique."""
    APPROVED = "approved"           # No issues found
    APPROVED_WITH_NOTES = "approved_with_notes"  # Minor issues only
    NEEDS_REVISION = "needs_revision"  # Has warnings
    REJECTED = "rejected"           # Has errors
    BLOCKED = "blocked"             # Has critical issues


@dataclass
class CritiqueResult:
    """Result of a full critique review."""

    tasc_id: str
    verdict: Optional[CritiqueVerdict] = None
    items: List[CritiqueItem] = field(default_factory=list)
    summary: str = ""
    confidence_adjustment: float = 0.0  # Adjustment to confidence
    reviewed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.items if i.severity == Severity.INFO)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.items if i.severity == Severity.WARNING)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.items if i.severity == Severity.ERROR)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.items if i.severity == Severity.CRITICAL)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tasc_id": self.tasc_id,
            "verdict": self.verdict.value if self.verdict else None,
            "items": [i.to_dict() for i in self.items],
            "summary": self.summary,
            "confidence_adjustment": self.confidence_adjustment,
            "counts": {
                "info": self.info_count,
                "warning": self.warning_count,
                "error": self.error_count,
                "critical": self.critical_count,
            },
            "reviewed_at": self.reviewed_at,
        }

    def to_ascii(self) -> str:
        """Render as ASCII box format."""
        width = 60
        lines = []

        # Header
        lines.append("┌" + "─" * (width - 2) + "┐")
        lines.append(f"│  CRITIQUE REPORT: {self.tasc_id:<{width-23}}│")
        lines.append("├" + "─" * (width - 2) + "┤")

        # Items
        for item in self.items:
            icon = {
                Severity.INFO: "ℹ️ ",
                Severity.WARNING: "⚠️ ",
                Severity.ERROR: "❌",
                Severity.CRITICAL: "🚫",
            }.get(item.severity, "  ")

            text = f"{item.location}: {item.description}"
            if len(text) > width - 10:
                text = text[:width - 13] + "..."
            lines.append(f"│  {icon} {text:<{width-9}}│")

        if not self.items:
            lines.append(f"│  ✅ No issues found{' ' * (width - 23)}│")

        lines.append("├" + "─" * (width - 2) + "┤")

        # Verdict
        verdict_value = self.verdict.value.upper() if self.verdict else "PENDING"
        verdict_text = f"Verdict: {verdict_value}"
        if self.warning_count or self.error_count:
            verdict_text += f" ({self.warning_count} warnings, {self.error_count} errors)"
        lines.append(f"│  {verdict_text:<{width-5}}│")

        lines.append("└" + "─" * (width - 2) + "┘")

        return "\n".join(lines)


class Critiquer:
    """Subagent that reviews reasoning for errors.

    The Critiquer examines TASC outputs and checks for:
    - Missing or failed validation checkpoints
    - Logical inconsistencies
    - Unsupported conclusions
    - Common mistake patterns
    - Rushed reasoning

    Example:
        critiquer = Critiquer(memory)
        critique = await critiquer.review(tasc)
        if critique.verdict != CritiqueVerdict.APPROVED:
            print(critique.to_ascii())
    """

    name = "critiquer"

    # Common mistake patterns to check
    COMMON_MISTAKES = {
        "complexity": [
            (r"O\(log\s*N\)", r"O\(N\s*log\s*N\)", "Complexity might be O(N log N), not O(log N)"),
            (r"O\(1\)", r"O\(N\)", "Constant time claim - verify it's not O(N)"),
        ],
        "arithmetic": [
            (r"= 0", r"", "Zero result - double-check arithmetic"),
            (r"-\s*-", r"+", "Double negative - verify sign"),
        ],
        "logic": [
            (r"therefore.*because", r"", "Circular reasoning pattern detected"),
            (r"obviously|clearly|trivially", r"", "Unsupported 'obvious' claim"),
        ],
    }

    # Minimum checkpoints per step type
    MIN_CHECKPOINTS = {
        "calculation": 1,
        "logic": 1,
        "verification": 2,
    }

    def __init__(self, memory: ABMemory):
        self.memory = memory

    async def review(self, tasc: TASC) -> CritiqueResult:
        """Perform full critique of a TASC.

        Args:
            tasc: The TASC to review

        Returns:
            CritiqueResult with all findings
        """
        result = CritiqueResult(tasc_id=tasc.id)
        items = []

        # Check 1: Validation coverage
        items.extend(self._check_validation_coverage(tasc))

        # Check 2: Step completeness
        items.extend(self._check_step_completeness(tasc))

        # Check 3: Evidence support
        items.extend(self._check_evidence_support(tasc))

        # Check 4: Logical consistency
        items.extend(self._check_logical_consistency(tasc))

        # Check 5: Common mistakes
        items.extend(self._check_common_mistakes(tasc))

        # Check 6: Rushed reasoning
        items.extend(self._check_rushed_reasoning(tasc))

        result.items = items

        # Determine verdict
        result.verdict = self._determine_verdict(items)

        # Calculate confidence adjustment
        result.confidence_adjustment = self._calculate_confidence_adjustment(items)

        # Generate summary
        result.summary = self._generate_summary(result)

        return result

    def _check_validation_coverage(self, tasc: TASC) -> List[CritiqueItem]:
        """Check that all steps have appropriate validation."""
        items = []

        for step in tasc.reasoning_steps:
            # Check for missing checkpoints
            if not step.checkpoints:
                items.append(CritiqueItem(
                    error_type=ErrorType.MISSING_CHECKPOINT,
                    severity=Severity.WARNING,
                    location=f"Step {step.step_number}",
                    description="No validation checkpoints defined",
                    suggestion="Add at least one checkpoint to validate this step",
                ))

            # Check for failed checkpoints
            failed = [cp for cp in step.checkpoints if not cp.passed]
            for cp in failed:
                items.append(CritiqueItem(
                    error_type=ErrorType.FAILED_CHECKPOINT,
                    severity=Severity.ERROR,
                    location=f"Step {step.step_number}",
                    description=f"Checkpoint failed: {cp.description}",
                    suggestion=f"Expected: {cp.expected}, Got: {cp.actual}",
                    context={"checkpoint": cp.to_dict()},
                ))

            # Check step status
            if step.status == StepStatus.SKIPPED:
                items.append(CritiqueItem(
                    error_type=ErrorType.SKIPPED_VALIDATION,
                    severity=Severity.WARNING,
                    location=f"Step {step.step_number}",
                    description="Step was skipped without validation",
                    suggestion="Either validate this step or mark it as N/A with justification",
                ))

        return items

    def _check_step_completeness(self, tasc: TASC) -> List[CritiqueItem]:
        """Check that steps are complete with required fields."""
        items = []

        for step in tasc.reasoning_steps:
            # Check for empty results
            if step.result is None and step.status == StepStatus.VALIDATED:
                items.append(CritiqueItem(
                    error_type=ErrorType.INCOMPLETE_ANALYSIS,
                    severity=Severity.WARNING,
                    location=f"Step {step.step_number}",
                    description="Step marked validated but has no result",
                    suggestion="Record the result of this step",
                ))

            # Check for computation without observation
            if step.computation and not step.observation:
                items.append(CritiqueItem(
                    error_type=ErrorType.INCOMPLETE_ANALYSIS,
                    severity=Severity.INFO,
                    location=f"Step {step.step_number}",
                    description="Computation provided without observation context",
                    suggestion="Add an observation explaining why this computation is done",
                ))

        return items

    def _check_evidence_support(self, tasc: TASC) -> List[CritiqueItem]:
        """Check that conclusions are supported by evidence."""
        items = []

        # Check for unsupported conclusions
        if tasc.proposed_answer and not tasc.evidence:
            items.append(CritiqueItem(
                error_type=ErrorType.MISSING_EVIDENCE,
                severity=Severity.WARNING,
                location="Answer",
                description="Proposed answer has no supporting evidence",
                suggestion="Add evidence to support the conclusion",
            ))

        # Check for unvalidated evidence
        unvalidated = [e for e in tasc.evidence if not e.get("validated")]
        if unvalidated and tasc.confidence > 0.8:
            items.append(CritiqueItem(
                error_type=ErrorType.WEAK_EVIDENCE,
                severity=Severity.WARNING,
                location="Evidence",
                description=f"{len(unvalidated)} evidence items are not validated",
                suggestion="Validate evidence before claiming high confidence",
            ))

        # Check for single verification method
        methods = set(e["source"] for e in tasc.evidence if e.get("validated"))
        if tasc.confidence > 0.9 and len(methods) < 2:
            items.append(CritiqueItem(
                error_type=ErrorType.WEAK_EVIDENCE,
                severity=Severity.INFO,
                location="Evidence",
                description="High confidence with only one verification method",
                suggestion="Consider adding independent verification",
            ))

        return items

    def _check_logical_consistency(self, tasc: TASC) -> List[CritiqueItem]:
        """Check for logical inconsistencies in reasoning."""
        items = []

        # Check step results for consistency
        results = []
        for step in tasc.reasoning_steps:
            if step.result is not None:
                results.append((step.step_number, step.result))

        # Look for contradictions
        seen_values: Dict[str, List[int]] = {}
        for step_num, result in results:
            result_str = str(result)
            if result_str not in seen_values:
                seen_values[result_str] = []
            seen_values[result_str].append(step_num)

        # Check final answer consistency
        if tasc.proposed_value is not None:
            final_result = None
            for step in reversed(tasc.reasoning_steps):
                if step.result is not None:
                    final_result = step.result
                    break

            if final_result is not None and final_result != tasc.proposed_value:
                items.append(CritiqueItem(
                    error_type=ErrorType.LOGICAL_INCONSISTENCY,
                    severity=Severity.ERROR,
                    location="Answer",
                    description=f"Final step result ({final_result}) differs from proposed value ({tasc.proposed_value})",
                    suggestion="Reconcile the discrepancy between step result and final answer",
                ))

        return items

    def _check_common_mistakes(self, tasc: TASC) -> List[CritiqueItem]:
        """Check for common mistake patterns."""
        items = []

        # Collect all text to check
        all_text = []
        for step in tasc.reasoning_steps:
            if step.observation:
                all_text.append(step.observation)
            if step.computation:
                all_text.append(step.computation)

        full_text = " ".join(all_text)

        # Check each pattern category
        for category, patterns in self.COMMON_MISTAKES.items():
            for pattern, _, warning in patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    items.append(CritiqueItem(
                        error_type=ErrorType.ARITHMETIC_ERROR if category == "arithmetic"
                                  else ErrorType.LOGICAL_INCONSISTENCY,
                        severity=Severity.INFO,
                        location="Reasoning",
                        description=warning,
                        suggestion="Double-check this pattern for accuracy",
                        context={"category": category, "pattern": pattern},
                    ))

        return items

    def _check_rushed_reasoning(self, tasc: TASC) -> List[CritiqueItem]:
        """Check for signs of rushed reasoning."""
        items = []

        # Check for very few steps on complex problems
        if len(tasc.reasoning_steps) < 2 and tasc.confidence > 0.8:
            items.append(CritiqueItem(
                error_type=ErrorType.RUSHED_REASONING,
                severity=Severity.WARNING,
                location="Overall",
                description="High confidence with minimal reasoning steps",
                suggestion="Consider breaking down the reasoning into more steps",
            ))

        # Check for steps without checkpoints
        steps_without_checkpoints = sum(
            1 for s in tasc.reasoning_steps if not s.checkpoints
        )
        if steps_without_checkpoints > len(tasc.reasoning_steps) / 2:
            items.append(CritiqueItem(
                error_type=ErrorType.RUSHED_REASONING,
                severity=Severity.WARNING,
                location="Validation",
                description=f"{steps_without_checkpoints}/{len(tasc.reasoning_steps)} steps lack validation",
                suggestion="Add validation checkpoints to ensure accuracy",
            ))

        # Check for unstated assumptions
        assumption_keywords = ["assume", "given that", "if we", "suppose"]
        for step in tasc.reasoning_steps:
            text = (step.observation or "") + " " + (step.computation or "")
            if any(kw in text.lower() for kw in assumption_keywords):
                if not any(g.lower().startswith("assum") for g in tasc.given):
                    items.append(CritiqueItem(
                        error_type=ErrorType.ASSUMPTION_NOT_STATED,
                        severity=Severity.INFO,
                        location=f"Step {step.step_number}",
                        description="Step contains assumptions not listed in 'given'",
                        suggestion="Explicitly state assumptions in the 'given' section",
                    ))

        return items

    def _determine_verdict(self, items: List[CritiqueItem]) -> CritiqueVerdict:
        """Determine overall verdict from critique items."""
        critical = any(i.severity == Severity.CRITICAL for i in items)
        errors = any(i.severity == Severity.ERROR for i in items)
        warnings = any(i.severity == Severity.WARNING for i in items)
        infos = any(i.severity == Severity.INFO for i in items)

        if critical:
            return CritiqueVerdict.BLOCKED
        elif errors:
            return CritiqueVerdict.REJECTED
        elif warnings:
            return CritiqueVerdict.NEEDS_REVISION
        elif infos:
            return CritiqueVerdict.APPROVED_WITH_NOTES
        else:
            return CritiqueVerdict.APPROVED

    def _calculate_confidence_adjustment(self, items: List[CritiqueItem]) -> float:
        """Calculate confidence adjustment based on issues found."""
        adjustment = 0.0

        for item in items:
            if item.severity == Severity.CRITICAL:
                adjustment -= 0.3
            elif item.severity == Severity.ERROR:
                adjustment -= 0.15
            elif item.severity == Severity.WARNING:
                adjustment -= 0.05
            # INFO doesn't affect confidence

        return max(-0.5, adjustment)  # Cap at -50%

    def _generate_summary(self, result: CritiqueResult) -> str:
        """Generate a summary of the critique."""
        parts = []

        if result.verdict == CritiqueVerdict.APPROVED:
            parts.append("All checks passed.")
        elif result.verdict == CritiqueVerdict.APPROVED_WITH_NOTES:
            parts.append(f"Approved with {result.info_count} minor note(s).")
        elif result.verdict == CritiqueVerdict.NEEDS_REVISION:
            parts.append(f"Needs revision: {result.warning_count} warning(s) found.")
        elif result.verdict == CritiqueVerdict.REJECTED:
            parts.append(f"Rejected: {result.error_count} error(s) must be fixed.")
        else:
            parts.append(f"Blocked: {result.critical_count} critical issue(s).")

        if result.confidence_adjustment != 0:
            parts.append(f"Confidence adjustment: {result.confidence_adjustment:+.0%}")

        return " ".join(parts)
