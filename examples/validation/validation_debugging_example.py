"""Example: Evidence-based validation for debugging tasks.

This demonstrates how debugging tasks are validated using the evidence-based
validation system with domain-specific requirements.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tasc.tasc import Tasc
from tasc.evidence import Evidence, EvidenceCollection, EvidenceSource
from tasc.domains import TaskDomain, apply_domain_to_tasc
from tasc.validation import validate_tasc_with_evidence, create_validation_summary


async def main():
    """Example debugging task validation workflow."""

    print("=" * 70)
    print("DEBUGGING TASK VALIDATION EXAMPLE")
    print("=" * 70)

    # 1. Create a debugging tasc
    tasc = Tasc(
        id="debug-001",
        status="completed",
        title="Fix crash when user clicks logout button",
        additional_notes="App crashes with SIGSEGV on logout",
        testing_instructions="pytest tests/auth/test_logout.py",
        desired_outcome="User can logout without crash",
    )

    # Apply debugging domain requirements
    apply_domain_to_tasc(tasc, TaskDomain.DEBUGGING)

    print(f"\n📋 Task: {tasc.title}")
    print(f"   Domain: Debugging")
    print(f"   Required Evidence: {', '.join(tasc.required_evidence_types)}")

    # 2. Collect evidence during debugging process
    print("\n" + "=" * 70)
    print("EVIDENCE COLLECTION")
    print("=" * 70)

    collection = EvidenceCollection.create(tasc.id)

    # Evidence 1: Hypothesis
    hypothesis_evidence = Evidence.create(
        text="Hypothesis: Null pointer dereference in SessionManager.cleanup() when accessing user.session",
        source=EvidenceSource.REASONING,
        citations=["debugger_analysis", "stack_trace.txt"],
    )
    collection.add_evidence(hypothesis_evidence)
    print("\n✓ Evidence #1: Hypothesis documented")
    print(f"  {hypothesis_evidence.text}")

    # Evidence 2: Reproduction steps
    reproduction_evidence = Evidence.create(
        text="Reproduced bug in 4 steps:\n"
             "1. Login as test user\n"
             "2. Navigate to profile page\n"
             "3. Click logout button\n"
             "4. Observe SIGSEGV crash",
        source=EvidenceSource.EXPERIMENT,
        citations=["reproduction_script.sh"],
    )
    reproduction_evidence.validated = True
    reproduction_evidence.validation_method = "manual_reproduction"
    collection.add_evidence(reproduction_evidence)
    print("\n✓ Evidence #2: Reproduction steps validated")
    print(f"  {reproduction_evidence.text.split(chr(10))[0]}...")

    # Evidence 3: Root cause analysis
    root_cause_evidence = Evidence.create(
        text="Root cause: SessionManager.cleanup() accesses user.session without null check. "
             "When session has expired, user.session is None, causing null pointer dereference.",
        source=EvidenceSource.CODE_ANALYSIS,
        citations=["src/auth/session_manager.py:142"],
    )
    collection.add_evidence(root_cause_evidence)
    print("\n✓ Evidence #3: Root cause identified")
    print(f"  {root_cause_evidence.text}")

    # Evidence 4: The fix
    fix_evidence = Evidence.create(
        text="Added null check before accessing user.session in cleanup():\n"
             "if user.session is not None:\n"
             "    user.session.invalidate()",
        source=EvidenceSource.CODE,
        citations=["src/auth/session_manager.py:142-144", "commit:abc123def456"],
    )
    collection.add_evidence(fix_evidence)
    print("\n✓ Evidence #4: Fix implemented")
    print(f"  {fix_evidence.text.split(chr(10))[0]}...")

    # Evidence 5: Regression test
    regression_test_evidence = Evidence.create(
        text="Added regression test: test_logout_with_expired_session()\n"
             "Verifies logout works correctly when session is None or expired.",
        source=EvidenceSource.REGRESSION_TEST,
        citations=["tests/auth/test_logout.py::test_logout_with_expired_session"],
    )
    regression_test_evidence.validated = True
    regression_test_evidence.validation_method = "test_execution"
    collection.add_evidence(regression_test_evidence)
    print("\n✓ Evidence #5: Regression test added and passing")
    print(f"  {regression_test_evidence.text.split(chr(10))[0]}")

    # Evidence 6: Code review
    review_evidence = Evidence.create(
        text="Code review approved by @senior-dev. No issues found.",
        source=EvidenceSource.PEER_REVIEW,
        citations=["github.com/org/repo/pull/123#review"],
    )
    collection.add_evidence(review_evidence)
    print("\n✓ Evidence #6: Code review completed")

    # 3. Run validation
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    result = await validate_tasc_with_evidence(
        tasc,
        collection,
        debug=True,
    )

    # 4. Display results
    print(create_validation_summary(result))

    # 5. Show what happens with incomplete evidence
    print("\n" + "=" * 70)
    print("COMPARISON: DEBUGGING WITHOUT EVIDENCE")
    print("=" * 70)

    incomplete_tasc = Tasc(
        id="debug-002",
        status="completed",
        title="Fixed the logout crash",
        additional_notes="Applied a fix to session_manager.py",
        testing_instructions="",
        desired_outcome="Logout works",
    )
    apply_domain_to_tasc(incomplete_tasc, TaskDomain.DEBUGGING)

    incomplete_collection = EvidenceCollection.create(incomplete_tasc.id)
    # Only add the fix, no other evidence
    incomplete_collection.add_evidence(
        Evidence.create(
            text="Fixed something in session_manager.py",
            source=EvidenceSource.CODE,
            citations=[],
        )
    )

    incomplete_result = await validate_tasc_with_evidence(
        incomplete_tasc,
        incomplete_collection,
        debug=False,
    )

    print(f"\n⚠️  Incomplete Evidence:")
    print(f"   Overall Confidence: {incomplete_result.overall_confidence:.1%}")
    print(f"   Evidence Count: {incomplete_result.evidence_count}")
    print(f"   Missing: {', '.join(incomplete_result.missing_evidence_types)}")
    print(f"   Status: {incomplete_result.validation_status}")
    print(f"   Requires Review: {incomplete_result.requires_human_review}")

    # 6. Key takeaways
    print("\n" + "=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)
    print("\n1. Complete Evidence → High Confidence")
    print(f"   With all required evidence: {result.overall_confidence:.1%} confidence")
    print(f"   Without required evidence: {incomplete_result.overall_confidence:.1%} confidence")

    print("\n2. Domain-Specific Requirements")
    print("   Debugging requires: hypothesis, reproduction, root cause, fix, regression test")
    print("   Missing evidence automatically triggers human review")

    print("\n3. Multi-Factor Scoring")
    print(f"   Evidence quality: {result.evidence_factor:.2f}")
    print(f"   Process adherence: {result.process_factor:.2f}")
    print(f"   Objective checks: {result.objective_factor:.2f}")

    print("\n4. Evidence Types Matter")
    print("   Validated evidence (tests, reproductions) boost confidence")
    print("   Cited evidence (file paths, commits) boost confidence")
    print("   Source diversity (multiple evidence types) boosts confidence")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
