"""Example: Debugging tasc with evidence-based validation (standalone).

This demonstrates how debugging tasks can be validated using the same
methodology as the learning system, without requiring full supe imports.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class EvidenceSource(Enum):
    """Evidence sources (simplified from learning system)"""
    REASONING = "reasoning"
    EXPERIMENT = "experiment"
    CODE_ANALYSIS = "code_analysis"
    CODE = "code"
    TEST = "test"
    DOC = "doc"


@dataclass
class Evidence:
    """Evidence artifact"""
    text: str
    source: EvidenceSource
    citations: List[str]


@dataclass
class DebugTaskc:
    """A debugging task with evidence tracking"""

    bug_description: str
    hypothesis: str = ""
    reproduction_steps: List[str] = field(default_factory=list)
    root_cause: str = ""
    fix_applied: str = ""
    test_added: bool = False

    # Evidence artifacts (collected during debugging)
    evidence: List[Evidence] = field(default_factory=list)

    def add_hypothesis_evidence(self, hypothesis: str):
        """Document hypothesis as evidence"""
        self.hypothesis = hypothesis
        self.evidence.append(Evidence(
            text=f"Hypothesis: {hypothesis}",
            source=EvidenceSource.REASONING,
            citations=["debugger_analysis"]
        ))

    def add_reproduction_evidence(self, steps: List[str]):
        """Document reproduction steps as evidence"""
        self.reproduction_steps = steps
        self.evidence.append(Evidence(
            text=f"Reproduced bug with {len(steps)} steps",
            source=EvidenceSource.EXPERIMENT,
            citations=["manual_reproduction"]
        ))

    def add_root_cause_evidence(self, root_cause: str, file_path: str, line: int):
        """Document root cause as evidence"""
        self.root_cause = root_cause
        self.evidence.append(Evidence(
            text=f"Root cause: {root_cause}",
            source=EvidenceSource.CODE_ANALYSIS,
            citations=[f"{file_path}:{line}"]
        ))

    def add_fix_evidence(self, fix_description: str, diff_hash: str):
        """Document fix as evidence"""
        self.fix_applied = fix_description
        self.evidence.append(Evidence(
            text=f"Fix applied: {fix_description}",
            source=EvidenceSource.CODE,
            citations=[f"commit:{diff_hash}"]
        ))

    def add_regression_test_evidence(self, test_path: str):
        """Document regression test as evidence"""
        self.test_added = True
        self.evidence.append(Evidence(
            text="Regression test added to prevent recurrence",
            source=EvidenceSource.TEST,
            citations=[test_path]
        ))


async def debug_with_evidence_validation():
    """Example debugging workflow with evidence collection"""

    # 1. Create debugging tasc
    tasc = DebugTaskc(
        bug_description="Application crashes when user clicks logout button"
    )

    print("=== DEBUGGING WITH EVIDENCE COLLECTION ===\n")

    # 2. Form hypothesis (evidence #1)
    tasc.add_hypothesis_evidence(
        "Null pointer dereference in session cleanup handler"
    )
    print(f"✓ Hypothesis documented: {tasc.hypothesis}")

    # 3. Reproduce bug (evidence #2)
    tasc.add_reproduction_evidence([
        "Login as test user",
        "Navigate to profile page",
        "Click logout button",
        "Observe crash with SIGSEGV"
    ])
    print(f"✓ Reproduction steps documented: {len(tasc.reproduction_steps)} steps")

    # 4. Find root cause (evidence #3)
    tasc.add_root_cause_evidence(
        "SessionManager.cleanup() accesses user.session without null check",
        "src/auth/session_manager.py",
        142
    )
    print(f"✓ Root cause identified: {tasc.root_cause}")

    # 5. Apply fix (evidence #4)
    tasc.add_fix_evidence(
        "Added null check before accessing user.session in cleanup()",
        "abc123def456"
    )
    print(f"✓ Fix applied: {tasc.fix_applied}")

    # 6. Add regression test (evidence #5)
    tasc.add_regression_test_evidence(
        "tests/auth/test_session_manager.py::test_logout_with_expired_session"
    )
    print(f"✓ Regression test added")

    # 7. Validate with evidence-based scoring
    print("\n=== EVIDENCE-BASED VALIDATION ===\n")

    confidence = validate_debug_tasc(tasc)

    print(f"\nOverall Confidence: {confidence:.2%}")
    print(f"Evidence Count: {len(tasc.evidence)}")
    print(f"Evidence Sources: {set(e.source.value for e in tasc.evidence)}")

    if confidence >= 0.8:
        print("\n✅ VALIDATION PASSED - High confidence in fix")
    elif confidence >= 0.6:
        print("\n⚠️  VALIDATION UNCERTAIN - Consider additional testing")
    else:
        print("\n❌ VALIDATION FAILED - Insufficient evidence")

    # 8. Show evidence artifacts
    print("\n=== EVIDENCE ARTIFACTS ===\n")
    for i, evidence in enumerate(tasc.evidence, 1):
        print(f"{i}. [{evidence.source.value}] {evidence.text}")
        print(f"   Citations: {', '.join(evidence.citations)}")

    # 9. Compare with incomplete debugging (no evidence)
    print("\n\n=== COMPARISON: DEBUGGING WITHOUT EVIDENCE ===\n")

    incomplete_tasc = DebugTaskc(
        bug_description="Application crashes when user clicks logout button",
        fix_applied="Changed something in session_manager.py"
    )
    # Only one piece of evidence (the fix itself, no reasoning)
    incomplete_tasc.evidence.append(Evidence(
        text="Applied a fix",
        source=EvidenceSource.CODE,
        citations=[]
    ))

    incomplete_confidence = validate_debug_tasc(incomplete_tasc)
    print(f"\nOverall Confidence: {incomplete_confidence:.2%}")
    print(f"Evidence Count: {len(incomplete_tasc.evidence)}")

    if incomplete_confidence < 0.6:
        print("\n❌ VALIDATION FAILED - Missing critical evidence:")
        print("   - No hypothesis documented")
        print("   - No reproduction steps")
        print("   - No root cause analysis")
        print("   - No regression test")


def validate_debug_tasc(tasc: DebugTaskc) -> float:
    """Validate debugging tasc using learning system methodology

    This mirrors the confidence scoring in:
    supe/learning/states/evaluate.py:101-151
    """

    # Count evidence
    count = len(tasc.evidence)
    count_factor = min(1.0, count / 5.0)
    print(f"Count Factor: {count_factor:.2f} ({count} evidence items, optimal: 5)")

    # Source diversity
    sources = set(e.source for e in tasc.evidence)
    diversity_factor = min(1.0, len(sources) / 3.0)
    print(f"Diversity Factor: {diversity_factor:.2f} ({len(sources)} source types, optimal: 3)")

    # Required evidence checklist (domain-specific for debugging)
    has_hypothesis = any("Hypothesis" in e.text for e in tasc.evidence)
    has_reproduction = any("Reproduced" in e.text for e in tasc.evidence)
    has_root_cause = any("Root cause" in e.text for e in tasc.evidence)
    has_fix = any("Fix applied" in e.text for e in tasc.evidence)
    has_test = any("Regression test" in e.text for e in tasc.evidence)

    required_count = sum([has_hypothesis, has_reproduction, has_root_cause, has_fix, has_test])
    required_factor = required_count / 5.0
    print(f"Required Factor: {required_factor:.2f} ({required_count}/5 required artifacts)")

    # Quality bonuses (like learning system's evidence evaluation)
    quality_bonus = 0.0
    if has_test:
        quality_bonus += 0.1
        print("  + Test bonus: 0.1")
    if has_root_cause and has_fix:
        quality_bonus += 0.1
        print("  + Root cause + fix bonus: 0.1")
    if has_reproduction and has_test:
        quality_bonus += 0.05
        print("  + Reproduction + test bonus: 0.05")

    # Compute overall confidence (weighted average + bonus)
    # This matches the pattern in evaluate.py:144-151
    base = (
        count_factor * 0.2 +
        diversity_factor * 0.2 +
        required_factor * 0.6
    )

    return min(1.0, base + quality_bonus)


if __name__ == "__main__":
    asyncio.run(debug_with_evidence_validation())
