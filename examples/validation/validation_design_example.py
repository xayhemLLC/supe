"""Example: Evidence-based validation for design tasks.

This demonstrates how design tasks are validated using the evidence-based
validation system with requirements, alternatives, trade-offs, and prototypes.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tasc.tasc import Tasc
from tasc.evidence import Evidence, EvidenceCollection, EvidenceSource
from tasc.domains import TaskDomain, apply_domain_to_tasc
from tasc.validation import validate_tasc_with_evidence, create_validation_summary


async def main():
    """Example design task validation workflow."""

    print("=" * 70)
    print("DESIGN TASK VALIDATION EXAMPLE")
    print("=" * 70)

    # 1. Create a design tasc
    tasc = Tasc(
        id="design-001",
        status="completed",
        title="Design caching layer for API responses",
        additional_notes="Need to reduce API latency and database load",
        testing_instructions="python examples/cache_prototype.py",
        desired_outcome="Caching design that reduces latency by 50%",
    )

    apply_domain_to_tasc(tasc, TaskDomain.DESIGN)

    print(f"\n📋 Task: {tasc.title}")
    print(f"   Domain: Design")
    print(f"   Required Evidence: {', '.join(tasc.required_evidence_types)}")

    # 2. Collect design evidence
    print("\n" + "=" * 70)
    print("EVIDENCE COLLECTION")
    print("=" * 70)

    collection = EvidenceCollection.create(tasc.id)

    # Evidence 1: Requirements document
    requirements_evidence = Evidence.create(
        text="Requirements:\n"
             "- Reduce API latency by 50% (target: 200ms → 100ms)\n"
             "- Support 10,000 req/sec\n"
             "- Cache invalidation within 5 minutes\n"
             "- Memory budget: 4GB\n"
             "- No data consistency issues",
        source=EvidenceSource.DOC,
        citations=["docs/design/cache_requirements.md"],
    )
    collection.add_evidence(requirements_evidence)
    print("\n✓ Evidence #1: Requirements documented")
    print(f"  {requirements_evidence.text.split(chr(10))[1]}")

    # Evidence 2: Design alternatives considered
    alternatives_evidence = Evidence.create(
        text="Design Alternatives Analysis:\n\n"
             "Option 1: Redis (in-memory cache)\n"
             "  Pros: Fast, proven, supports TTL\n"
             "  Cons: Additional infrastructure, network overhead\n\n"
             "Option 2: In-process LRU cache\n"
             "  Pros: No network, simple\n"
             "  Cons: No sharing across instances, limited memory\n\n"
             "Option 3: CDN caching (CloudFlare)\n"
             "  Pros: Global distribution, DDoS protection\n"
             "  Cons: Less control, harder to invalidate\n\n"
             "Selected: Redis + in-process L1 cache (hybrid)",
        source=EvidenceSource.REASONING,
        citations=["docs/design/cache_alternatives.md"],
    )
    collection.add_evidence(alternatives_evidence)
    print("\n✓ Evidence #2: Design alternatives analyzed")
    print(f"  Evaluated 3 options, selected hybrid approach")

    # Evidence 3: Trade-offs documented
    tradeoffs_evidence = Evidence.create(
        text="Trade-off Analysis:\n"
             "- Consistency vs Performance: Chose eventual consistency (5min TTL)\n"
             "- Complexity vs Speed: Added L1 cache for hot keys (80/20 rule)\n"
             "- Cost vs Reliability: Redis cluster for HA (worth the cost)",
        source=EvidenceSource.REASONING,
        citations=["docs/design/cache_tradeoffs.md"],
    )
    collection.add_evidence(tradeoffs_evidence)
    print("\n✓ Evidence #3: Trade-offs documented")
    print(f"  {tradeoffs_evidence.text.split(chr(10))[0]}")

    # Evidence 4: Prototype implementation
    prototype_evidence = Evidence.create(
        text="Prototype: Working proof-of-concept with Redis + LRU L1 cache\n"
             "- Implements TTL-based invalidation\n"
             "- Benchmarks show 60% latency reduction (better than target)\n"
             "- Memory usage: 2.3GB (within budget)",
        source=EvidenceSource.CODE,
        citations=["examples/cache_prototype.py", "benchmarks/cache_results.json"],
    )
    prototype_evidence.validated = True
    prototype_evidence.validation_method = "benchmark"
    collection.add_evidence(prototype_evidence)
    print("\n✓ Evidence #4: Prototype validated with benchmarks")
    print(f"  60% latency reduction (exceeds 50% target)")

    # Evidence 5: Design review feedback
    review_evidence = Evidence.create(
        text="Design Review Feedback:\n"
             "- Approved by @tech-lead and @architect\n"
             "- Concern: Cache invalidation complexity → mitigated with cache keys design\n"
             "- Suggestion: Add metrics for cache hit rate → added to implementation plan",
        source=EvidenceSource.PEER_REVIEW,
        citations=["docs/design/cache_review_2024-01-15.md"],
    )
    collection.add_evidence(review_evidence)
    print("\n✓ Evidence #5: Design review completed")

    # Evidence 6: User validation
    user_evidence = Evidence.create(
        text="User Acceptance: Prototype tested with 5 API consumers\n"
             "- All reported noticeable speed improvement\n"
             "- No concerns about eventual consistency\n"
             "- Requested: cache warming for cold starts (added to backlog)",
        source=EvidenceSource.USER_FEEDBACK,
        citations=["user_feedback_summary.md"],
    )
    collection.add_evidence(user_evidence)
    print("\n✓ Evidence #6: User feedback collected")

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

    # 5. Demonstrate impact of missing trade-off analysis
    print("\n" + "=" * 70)
    print("COMPARISON: DESIGN WITHOUT TRADE-OFF ANALYSIS")
    print("=" * 70)

    incomplete_tasc = Tasc(
        id="design-002",
        status="completed",
        title="Design caching layer",
        additional_notes="Using Redis",
        testing_instructions="",
        desired_outcome="Faster API",
    )
    apply_domain_to_tasc(incomplete_tasc, TaskDomain.DESIGN)

    incomplete_collection = EvidenceCollection.create(incomplete_tasc.id)

    # Has requirements and code, but no alternatives or trade-offs
    incomplete_collection.add_evidence(
        Evidence.create(
            text="Requirements: Make API faster",
            source=EvidenceSource.DOC,
            citations=[],
        )
    )
    incomplete_collection.add_evidence(
        Evidence.create(
            text="Prototype using Redis",
            source=EvidenceSource.CODE,
            citations=[],
        )
    )

    incomplete_result = await validate_tasc_with_evidence(
        incomplete_tasc,
        incomplete_collection,
        debug=False,
    )

    print(f"\n⚠️  Without Trade-off Analysis:")
    print(f"   Overall Confidence: {incomplete_result.overall_confidence:.1%}")
    print(f"   Missing: Alternatives analysis, trade-off documentation")
    print(f"   Risk: Design may not have considered important trade-offs")
    print(f"   Requires Review: {incomplete_result.requires_human_review}")

    # 6. Key takeaways
    print("\n" + "=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)

    print("\n1. Design Validation Requires Multiple Evidence Types")
    print("   ✓ Requirements (what)")
    print("   ✓ Alternatives (options considered)")
    print("   ✓ Trade-offs (why this option)")
    print("   ✓ Prototype (proof it works)")

    print("\n2. Reasoning Evidence is Critical for Design")
    print(f"   Alternatives + Trade-offs boost confidence significantly")
    print(f"   Shows thoughtful decision-making process")

    print("\n3. Validation from Multiple Sources")
    print(f"   • Benchmarks validate performance claims")
    print(f"   • Peer review validates architectural soundness")
    print(f"   • User feedback validates real-world fit")

    print("\n4. Design Confidence Factors")
    print(f"   Complete design: {result.overall_confidence:.1%} confidence")
    print(f"   Missing trade-offs: {incomplete_result.overall_confidence:.1%} confidence")
    print(f"   Difference: {(result.overall_confidence - incomplete_result.overall_confidence):.1%}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
