"""Unified evidence-based validation for tascs.

This module implements the core validation system that evaluates task completion
based on evidence quality, using the proven methodology from the learning system's
confidence scoring (supe/learning/states/evaluate.py).

Key principles:
1. Evidence-based: Validation is based on collected evidence, not binary pass/fail
2. Multi-factor scoring: Evidence count, source diversity, validation status, citations
3. Confidence intervals: 0.0-1.0 continuous scoring instead of binary gates
4. Human review gates: Low confidence triggers human review requirements
5. Retrospective validation: Confidence can be updated as new evidence emerges

This replaces traditional binary validators with a probabilistic, evidence-driven approach.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import subprocess

from .tasc import Tasc
from .evidence import Evidence, EvidenceCollection, EvidenceSource


@dataclass
class ValidationResult:
    """Result of evidence-based task validation.

    This structure mirrors the learning system's confidence evaluation,
    providing detailed breakdown of how validation confidence was computed.
    """

    # Overall validation confidence (0.0-1.0)
    overall_confidence: float

    # Factor breakdowns (match learning system's evaluate.py:101-226)
    evidence_factor: float  # Quality of evidence (0.8-1.2, can boost)
    process_factor: float  # Process quality (0.8-1.0)
    objective_factor: float  # Objective checks (0.0-1.0)

    # Evidence analysis
    evidence_count: int
    source_diversity: int
    validated_evidence_count: int
    cited_evidence_count: int

    # Missing requirements
    missing_evidence_types: List[str] = field(default_factory=list)
    missing_process_steps: List[str] = field(default_factory=list)

    # Objective check results
    objective_checks: Dict[str, bool] = field(default_factory=dict)

    # Review requirements
    requires_human_review: bool = False
    review_reasons: List[str] = field(default_factory=list)

    # Status
    validation_status: str = "pending"  # "pending", "partial", "complete", "failed"

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "overall_confidence": self.overall_confidence,
            "evidence_factor": self.evidence_factor,
            "process_factor": self.process_factor,
            "objective_factor": self.objective_factor,
            "evidence_count": self.evidence_count,
            "source_diversity": self.source_diversity,
            "validated_evidence_count": self.validated_evidence_count,
            "cited_evidence_count": self.cited_evidence_count,
            "missing_evidence_types": self.missing_evidence_types,
            "missing_process_steps": self.missing_process_steps,
            "objective_checks": self.objective_checks,
            "requires_human_review": self.requires_human_review,
            "review_reasons": self.review_reasons,
            "validation_status": self.validation_status,
        }


class UnifiedValidator:
    """Unified evidence-based validator for all task types.

    This validator applies the learning system's confidence scoring methodology
    to task validation. Instead of binary pass/fail gates, it evaluates:

    1. Evidence quality (count, diversity, validation, citations)
    2. Process adherence (required steps completed)
    3. Objective checks (tests, builds, linting)

    The result is a confidence score (0.0-1.0) that indicates validation quality.
    """

    def __init__(self, debug: bool = False):
        """Initialize validator.

        Args:
            debug: Enable debug logging
        """
        self.debug = debug

    async def validate(
        self,
        tasc: Tasc,
        evidence_collection: EvidenceCollection,
        run_objective_checks: bool = True,
    ) -> ValidationResult:
        """Validate a tasc based on its evidence collection.

        This implements the core validation logic, applying multi-factor
        confidence scoring to determine validation quality.

        Args:
            tasc: The tasc to validate
            evidence_collection: Collection of evidence for this tasc
            run_objective_checks: Whether to run objective tests/builds

        Returns:
            ValidationResult with detailed breakdown
        """
        if self.debug:
            print(f"\n=== Validating Tasc: {tasc.id} ===")
            print(f"Title: {tasc.title}")
            print(f"Evidence items: {len(evidence_collection.evidence_items)}")

        # 1. Evaluate evidence quality (like learning system's evaluate.py:101-151)
        evidence_factor = self._evaluate_evidence_quality(
            evidence_collection.evidence_items
        )

        # 2. Evaluate process adherence
        process_factor, missing_steps = self._evaluate_process_adherence(
            tasc, evidence_collection
        )

        # 3. Run objective checks (if enabled)
        if run_objective_checks:
            objective_factor, objective_checks = await self._run_objective_checks(tasc)
        else:
            objective_factor = 1.0
            objective_checks = {}

        # 4. Compute overall confidence (multiplicative, like evaluate.py:203-226)
        base_confidence = tasc.confidence_score if tasc.confidence_score else 0.7
        overall_confidence = min(
            1.0,
            base_confidence * evidence_factor * process_factor * objective_factor
        )

        # 5. Determine validation status
        status = self._determine_status(
            overall_confidence, missing_steps, objective_checks
        )

        # 6. Determine if human review is required
        requires_review, review_reasons = self._check_review_requirements(
            overall_confidence, evidence_factor, objective_factor, missing_steps
        )

        # 7. Analyze evidence
        evidence_items = evidence_collection.evidence_items
        evidence_count = len(evidence_items)
        source_diversity = len(set(e.source for e in evidence_items))
        validated_count = sum(1 for e in evidence_items if e.validated)
        cited_count = sum(1 for e in evidence_items if e.citations)

        # 8. Check for missing required evidence types
        missing_evidence = self._check_missing_evidence(tasc, evidence_collection)

        if self.debug:
            print(f"\nValidation Results:")
            print(f"  Overall Confidence: {overall_confidence:.2f}")
            print(f"  Evidence Factor: {evidence_factor:.2f}")
            print(f"  Process Factor: {process_factor:.2f}")
            print(f"  Objective Factor: {objective_factor:.2f}")
            print(f"  Status: {status}")
            print(f"  Requires Review: {requires_review}")

        return ValidationResult(
            overall_confidence=overall_confidence,
            evidence_factor=evidence_factor,
            process_factor=process_factor,
            objective_factor=objective_factor,
            evidence_count=evidence_count,
            source_diversity=source_diversity,
            validated_evidence_count=validated_count,
            cited_evidence_count=cited_count,
            missing_evidence_types=missing_evidence,
            missing_process_steps=missing_steps,
            objective_checks=objective_checks,
            requires_human_review=requires_review,
            review_reasons=review_reasons,
            validation_status=status,
        )

    def _evaluate_evidence_quality(self, evidence_list: List[Evidence]) -> float:
        """Evaluate quality of evidence using learning system methodology.

        This is identical to supe/learning/states/evaluate.py:101-151.

        Factors:
        - Number of evidence items (more = better, up to 5 optimal)
        - Source diversity (multiple sources = better)
        - Validation status (validated evidence = better)
        - Citation quality (specific citations = better)

        Args:
            evidence_list: List of evidence to evaluate

        Returns:
            Quality factor (0.8-1.2, can boost confidence)
        """
        if not evidence_list:
            return 0.8  # Penalty for no evidence

        # Count evidence (1-5 optimal, diminishing returns after)
        evidence_count = len(evidence_list)
        count_factor = min(1.0, evidence_count / 5.0)

        # Source diversity (different source types)
        sources = set(e.source for e in evidence_list)
        diversity_factor = min(1.0, len(sources) / 3.0)

        # Validation status
        validated_count = sum(1 for e in evidence_list if e.validated)
        validation_factor = validated_count / len(evidence_list)

        # Citation quality (evidence with citations is better)
        with_citations = sum(1 for e in evidence_list if e.citations)
        citation_factor = with_citations / len(evidence_list)

        # Prefer validated, cited evidence from experiments/tests/docs
        quality_bonus = 0.0
        for e in evidence_list:
            if e.source == EvidenceSource.EXPERIMENT and e.validated:
                quality_bonus += 0.1
            elif e.source == EvidenceSource.TEST and e.validated:
                quality_bonus += 0.1
            elif e.source == EvidenceSource.DOC and e.citations:
                quality_bonus += 0.05
            elif e.source == EvidenceSource.REGRESSION_TEST:
                quality_bonus += 0.1

        # Combine factors (weighted average + bonus)
        base_quality = (
            count_factor * 0.3 +
            diversity_factor * 0.2 +
            validation_factor * 0.3 +
            citation_factor * 0.2
        )

        if self.debug:
            print(f"\n  Evidence Quality Breakdown:")
            print(f"    Count Factor: {count_factor:.2f} ({evidence_count} items)")
            print(f"    Diversity Factor: {diversity_factor:.2f} ({len(sources)} sources)")
            print(f"    Validation Factor: {validation_factor:.2f} ({validated_count} validated)")
            print(f"    Citation Factor: {citation_factor:.2f} ({with_citations} cited)")
            print(f"    Quality Bonus: {quality_bonus:.2f}")

        return min(1.2, base_quality + quality_bonus)

    def _evaluate_process_adherence(
        self, tasc: Tasc, evidence_collection: EvidenceCollection
    ) -> Tuple[float, List[str]]:
        """Evaluate whether required process steps were followed.

        This checks if the task followed a rigorous process (e.g., hypothesis,
        root cause, fix, test for debugging tasks).

        Args:
            tasc: The tasc being validated
            evidence_collection: Evidence collection

        Returns:
            Tuple of (process_factor, missing_steps)
        """
        # Get required evidence types from tasc
        required_types = tasc.required_evidence_types
        if not required_types:
            # No specific requirements, assume process followed
            return 1.0, []

        # Check which required types are present
        present_sources = set(e.source.value for e in evidence_collection.evidence_items)
        missing = [req for req in required_types if req not in present_sources]

        # Compute process factor based on completion
        completion_rate = (len(required_types) - len(missing)) / len(required_types)
        process_factor = 0.8 + (completion_rate * 0.2)  # Range: 0.8-1.0

        if self.debug:
            print(f"\n  Process Adherence:")
            print(f"    Required: {required_types}")
            print(f"    Present: {list(present_sources)}")
            print(f"    Missing: {missing}")
            print(f"    Completion: {completion_rate:.2%}")

        return process_factor, missing

    async def _run_objective_checks(
        self, tasc: Tasc
    ) -> Tuple[float, Dict[str, bool]]:
        """Run objective validation checks (tests, builds, linting).

        Args:
            tasc: The tasc being validated

        Returns:
            Tuple of (objective_factor, check_results)
        """
        results = {}

        # Check if testing_instructions defines a validation command
        if tasc.testing_instructions:
            try:
                # Run the validation command
                result = subprocess.run(
                    tasc.testing_instructions,
                    shell=True,
                    capture_output=True,
                    timeout=300,  # 5 minute timeout
                )
                results["command_execution"] = result.returncode == 0
            except subprocess.TimeoutExpired:
                results["command_execution"] = False
            except Exception:
                results["command_execution"] = False

        # Compute objective factor (1.0 if all pass, 0.0 if any fail)
        if not results:
            objective_factor = 1.0  # No checks to run
        else:
            objective_factor = 1.0 if all(results.values()) else 0.0

        if self.debug:
            print(f"\n  Objective Checks:")
            for check, passed in results.items():
                print(f"    {check}: {'✓' if passed else '✗'}")

        return objective_factor, results

    def _determine_status(
        self,
        confidence: float,
        missing_steps: List[str],
        objective_checks: Dict[str, bool],
    ) -> str:
        """Determine validation status based on confidence and checks.

        Args:
            confidence: Overall confidence score
            missing_steps: List of missing process steps
            objective_checks: Objective check results

        Returns:
            Status string: "complete", "partial", "failed", or "pending"
        """
        # Check objective failures first
        if objective_checks and not all(objective_checks.values()):
            return "failed"

        # Check confidence thresholds
        if confidence >= 0.8 and not missing_steps:
            return "complete"
        elif confidence >= 0.6:
            return "partial"
        elif confidence < 0.5:
            return "failed"
        else:
            return "pending"

    def _check_review_requirements(
        self,
        confidence: float,
        evidence_factor: float,
        objective_factor: float,
        missing_steps: List[str],
    ) -> Tuple[bool, List[str]]:
        """Determine if human review is required.

        Args:
            confidence: Overall confidence
            evidence_factor: Evidence quality factor
            objective_factor: Objective check factor
            missing_steps: Missing process steps

        Returns:
            Tuple of (requires_review, reasons)
        """
        reasons = []

        # Low overall confidence
        if confidence < 0.7:
            reasons.append(f"Low confidence ({confidence:.2f} < 0.7)")

        # Insufficient evidence
        if evidence_factor < 0.9:
            reasons.append(f"Insufficient evidence quality ({evidence_factor:.2f})")

        # Objective check failures
        if objective_factor < 1.0:
            reasons.append("Objective checks failed")

        # Missing critical process steps
        if missing_steps:
            reasons.append(f"Missing process steps: {', '.join(missing_steps)}")

        return len(reasons) > 0, reasons

    def _check_missing_evidence(
        self, tasc: Tasc, evidence_collection: EvidenceCollection
    ) -> List[str]:
        """Check for missing required evidence types.

        Args:
            tasc: The tasc being validated
            evidence_collection: Evidence collection

        Returns:
            List of missing evidence type names
        """
        if not tasc.required_evidence_types:
            return []

        present_sources = set(e.source.value for e in evidence_collection.evidence_items)
        return [req for req in tasc.required_evidence_types if req not in present_sources]


# Convenience functions for common validation scenarios

async def validate_tasc_with_evidence(
    tasc: Tasc,
    evidence_collection: EvidenceCollection,
    debug: bool = False,
) -> ValidationResult:
    """Convenience function to validate a tasc with evidence.

    Args:
        tasc: The tasc to validate
        evidence_collection: Evidence collection
        debug: Enable debug logging

    Returns:
        ValidationResult
    """
    validator = UnifiedValidator(debug=debug)
    return await validator.validate(tasc, evidence_collection)


def create_validation_summary(result: ValidationResult) -> str:
    """Create a human-readable validation summary.

    Args:
        result: Validation result

    Returns:
        Formatted summary string
    """
    status_emoji = {
        "complete": "✅",
        "partial": "⚠️ ",
        "failed": "❌",
        "pending": "⏳",
    }

    lines = [
        f"\n{'='*60}",
        f"VALIDATION SUMMARY",
        f"{'='*60}",
        f"\n{status_emoji.get(result.validation_status, '?')} Status: {result.validation_status.upper()}",
        f"\nOverall Confidence: {result.overall_confidence:.1%}",
        f"\n{'─'*60}",
        f"\nFactor Breakdown:",
        f"  • Evidence Quality:  {result.evidence_factor:.2f} (count={result.evidence_count}, diversity={result.source_diversity})",
        f"  • Process Adherence: {result.process_factor:.2f}",
        f"  • Objective Checks:  {result.objective_factor:.2f}",
    ]

    if result.missing_evidence_types:
        lines.append(f"\nMissing Evidence:")
        for missing in result.missing_evidence_types:
            lines.append(f"  • {missing}")

    if result.missing_process_steps:
        lines.append(f"\nMissing Process Steps:")
        for missing in result.missing_process_steps:
            lines.append(f"  • {missing}")

    if result.objective_checks:
        lines.append(f"\nObjective Checks:")
        for check, passed in result.objective_checks.items():
            status = "✓" if passed else "✗"
            lines.append(f"  {status} {check}")

    if result.requires_human_review:
        lines.append(f"\n⚠️  HUMAN REVIEW REQUIRED")
        lines.append(f"\nReasons:")
        for reason in result.review_reasons:
            lines.append(f"  • {reason}")

    lines.append(f"\n{'='*60}\n")

    return "\n".join(lines)
