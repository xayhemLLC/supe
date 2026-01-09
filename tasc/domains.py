"""Domain-specific validation requirements for different task types.

This module defines what evidence is required for various problem-solving domains:
- Debugging: hypothesis, reproduction, root cause, fix, regression test
- Design: requirements, alternatives, trade-offs, prototype, validation
- Research: questions, sources, notes, examples, experiments
- Refactoring: motivation, tests before, changes, tests after, metrics
- Feature: requirements, design, implementation, tests, documentation
- Security: threat model, vulnerability analysis, mitigation, validation

Each domain specifies:
1. Required evidence types (what artifacts must be present)
2. Optional evidence types (nice-to-have artifacts)
3. Validation weight adjustments (how to score domain-specific evidence)
4. Process templates (recommended workflows for the domain)

This allows tasks to self-declare their domain and get automatic validation
requirements based on best practices.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from .evidence import EvidenceSource


class TaskDomain(Enum):
    """Enumeration of task domains with different validation requirements."""

    DEBUGGING = "debugging"
    DESIGN = "design"
    RESEARCH = "research"
    REFACTORING = "refactoring"
    FEATURE = "feature"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    GENERAL = "general"  # Default/catch-all


@dataclass
class DomainRequirements:
    """Validation requirements for a specific task domain.

    Defines what evidence is required, optional, and how to weight it
    for validation purposes.
    """

    domain: TaskDomain

    # Required evidence sources (must be present for high confidence)
    required_sources: List[EvidenceSource]

    # Optional evidence sources (boost confidence if present)
    optional_sources: List[EvidenceSource] = field(default_factory=list)

    # Source weights (multipliers for evidence quality scoring)
    source_weights: Dict[EvidenceSource, float] = field(default_factory=dict)

    # Minimum confidence threshold for this domain
    min_confidence: float = 0.7

    # Description of what this domain entails
    description: str = ""

    # Process template (recommended steps)
    process_template: List[str] = field(default_factory=list)


# ============================================================================
# Domain Definitions
# ============================================================================

DEBUGGING_REQUIREMENTS = DomainRequirements(
    domain=TaskDomain.DEBUGGING,
    required_sources=[
        EvidenceSource.REASONING,       # Hypothesis about the bug
        EvidenceSource.EXPERIMENT,      # Reproduction steps
        EvidenceSource.CODE_ANALYSIS,   # Root cause analysis
        EvidenceSource.CODE,            # The fix
        EvidenceSource.REGRESSION_TEST, # Test to prevent recurrence
    ],
    optional_sources=[
        EvidenceSource.DOC,            # Documentation updates
        EvidenceSource.PROFILING,      # Performance analysis
        EvidenceSource.PEER_REVIEW,    # Code review
    ],
    source_weights={
        EvidenceSource.REGRESSION_TEST: 1.2,  # Extra weight for regression tests
        EvidenceSource.EXPERIMENT: 1.1,       # Extra weight for reproduction
    },
    min_confidence=0.8,  # Higher bar for bug fixes
    description="Bug fix with hypothesis, reproduction, root cause, fix, and regression test",
    process_template=[
        "1. Form hypothesis about the bug cause",
        "2. Document reproduction steps",
        "3. Analyze root cause (code analysis, debugging)",
        "4. Implement fix",
        "5. Add regression test to prevent recurrence",
        "6. Verify fix doesn't break existing functionality",
        "7. Update documentation if needed",
    ],
)

DESIGN_REQUIREMENTS = DomainRequirements(
    domain=TaskDomain.DESIGN,
    required_sources=[
        EvidenceSource.DOC,          # Requirements document
        EvidenceSource.REASONING,    # Design alternatives considered
        EvidenceSource.CODE,         # Prototype or proof of concept
    ],
    optional_sources=[
        EvidenceSource.PEER_REVIEW,   # Design review feedback
        EvidenceSource.USER_FEEDBACK, # User acceptance testing
        EvidenceSource.BENCHMARK,     # Performance validation
    ],
    source_weights={
        EvidenceSource.REASONING: 1.2,     # Extra weight for trade-off analysis
        EvidenceSource.USER_FEEDBACK: 1.1, # Extra weight for user validation
    },
    min_confidence=0.7,
    description="Design work with requirements, alternatives, trade-offs, and prototype",
    process_template=[
        "1. Document requirements and constraints",
        "2. Generate multiple design alternatives",
        "3. Analyze trade-offs (performance, complexity, maintainability)",
        "4. Select approach and document rationale",
        "5. Create prototype or proof of concept",
        "6. Get design review feedback",
        "7. Validate with users/stakeholders if applicable",
    ],
)

RESEARCH_REQUIREMENTS = DomainRequirements(
    domain=TaskDomain.RESEARCH,
    required_sources=[
        EvidenceSource.DOC,          # Research questions
        EvidenceSource.DOC,          # Sources consulted
        EvidenceSource.DOC,          # Notes/findings
        EvidenceSource.CODE,         # Working examples
    ],
    optional_sources=[
        EvidenceSource.EXPERIMENT,   # Experimental validation
        EvidenceSource.TEST,         # Tests demonstrating understanding
    ],
    source_weights={
        EvidenceSource.EXPERIMENT: 1.2,  # Extra weight for experimental validation
        EvidenceSource.DOC: 1.0,         # Standard weight for documentation
    },
    min_confidence=0.6,  # Lower bar for research (exploratory)
    description="Research with questions, sources, notes, and working examples",
    process_template=[
        "1. Define research questions",
        "2. Identify and document sources",
        "3. Take Cornell-style notes",
        "4. Create working code examples",
        "5. Validate understanding through experiments/tests",
        "6. Document gaps and follow-up questions",
    ],
)

REFACTORING_REQUIREMENTS = DomainRequirements(
    domain=TaskDomain.REFACTORING,
    required_sources=[
        EvidenceSource.REASONING,     # Motivation for refactoring
        EvidenceSource.TEST,          # Tests before refactoring
        EvidenceSource.CODE,          # Refactored code
        EvidenceSource.TEST,          # Tests after refactoring
    ],
    optional_sources=[
        EvidenceSource.METRIC,        # Code quality metrics
        EvidenceSource.BENCHMARK,     # Performance comparison
        EvidenceSource.PEER_REVIEW,   # Code review
    ],
    source_weights={
        EvidenceSource.TEST: 1.2,    # Extra weight for test preservation
        EvidenceSource.METRIC: 1.1,  # Extra weight for measurable improvement
    },
    min_confidence=0.8,  # High bar to ensure safety
    description="Refactoring with motivation, tests, changes, and validation",
    process_template=[
        "1. Document motivation for refactoring",
        "2. Ensure comprehensive test coverage exists",
        "3. Measure baseline metrics (complexity, performance)",
        "4. Perform refactoring incrementally",
        "5. Verify all tests still pass",
        "6. Measure improved metrics",
        "7. Get code review",
    ],
)

FEATURE_REQUIREMENTS = DomainRequirements(
    domain=TaskDomain.FEATURE,
    required_sources=[
        EvidenceSource.DOC,          # Feature requirements
        EvidenceSource.CODE,         # Implementation
        EvidenceSource.TEST,         # Test coverage
    ],
    optional_sources=[
        EvidenceSource.REASONING,     # Design decisions
        EvidenceSource.DOC,           # User documentation
        EvidenceSource.USER_FEEDBACK, # User acceptance testing
        EvidenceSource.PEER_REVIEW,   # Code review
    ],
    source_weights={
        EvidenceSource.TEST: 1.2,         # Extra weight for test coverage
        EvidenceSource.USER_FEEDBACK: 1.1,# Extra weight for user validation
    },
    min_confidence=0.75,
    description="Feature development with requirements, implementation, and tests",
    process_template=[
        "1. Document feature requirements",
        "2. Design approach and get review",
        "3. Implement feature incrementally",
        "4. Write comprehensive tests",
        "5. Update user documentation",
        "6. Get code review",
        "7. User acceptance testing if applicable",
    ],
)

SECURITY_REQUIREMENTS = DomainRequirements(
    domain=TaskDomain.SECURITY,
    required_sources=[
        EvidenceSource.DOC,            # Threat model
        EvidenceSource.SECURITY_SCAN,  # Vulnerability analysis
        EvidenceSource.CODE,           # Mitigation implementation
        EvidenceSource.TEST,           # Security tests
    ],
    optional_sources=[
        EvidenceSource.PEER_REVIEW,    # Security review
        EvidenceSource.DOC,            # Security documentation
    ],
    source_weights={
        EvidenceSource.SECURITY_SCAN: 1.3,  # Extra weight for scans
        EvidenceSource.PEER_REVIEW: 1.2,    # Extra weight for security review
    },
    min_confidence=0.9,  # Very high bar for security
    description="Security work with threat model, analysis, mitigation, and validation",
    process_template=[
        "1. Create threat model",
        "2. Run security scans and vulnerability analysis",
        "3. Implement mitigations",
        "4. Write security tests",
        "5. Get security-focused code review",
        "6. Document security considerations",
    ],
)

PERFORMANCE_REQUIREMENTS = DomainRequirements(
    domain=TaskDomain.PERFORMANCE,
    required_sources=[
        EvidenceSource.PROFILING,    # Baseline measurements
        EvidenceSource.CODE,         # Optimization implementation
        EvidenceSource.BENCHMARK,    # Performance validation
    ],
    optional_sources=[
        EvidenceSource.REASONING,    # Optimization rationale
        EvidenceSource.TEST,         # Performance regression tests
        EvidenceSource.PEER_REVIEW,  # Code review
    ],
    source_weights={
        EvidenceSource.BENCHMARK: 1.3,  # Extra weight for benchmarks
        EvidenceSource.PROFILING: 1.2,  # Extra weight for profiling data
    },
    min_confidence=0.75,
    description="Performance optimization with profiling, changes, and benchmarks",
    process_template=[
        "1. Profile to identify bottlenecks",
        "2. Document optimization approach",
        "3. Implement optimizations",
        "4. Run benchmarks to measure improvement",
        "5. Add performance regression tests",
        "6. Verify correctness not compromised",
    ],
)

# Registry of all domain requirements
DOMAIN_REGISTRY: Dict[TaskDomain, DomainRequirements] = {
    TaskDomain.DEBUGGING: DEBUGGING_REQUIREMENTS,
    TaskDomain.DESIGN: DESIGN_REQUIREMENTS,
    TaskDomain.RESEARCH: RESEARCH_REQUIREMENTS,
    TaskDomain.REFACTORING: REFACTORING_REQUIREMENTS,
    TaskDomain.FEATURE: FEATURE_REQUIREMENTS,
    TaskDomain.SECURITY: SECURITY_REQUIREMENTS,
    TaskDomain.PERFORMANCE: PERFORMANCE_REQUIREMENTS,
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_requirements_for_domain(domain: TaskDomain) -> DomainRequirements:
    """Get validation requirements for a task domain.

    Args:
        domain: The task domain

    Returns:
        DomainRequirements for that domain
    """
    return DOMAIN_REGISTRY.get(
        domain,
        DomainRequirements(
            domain=TaskDomain.GENERAL,
            required_sources=[],
            min_confidence=0.6,
            description="General task with no specific requirements",
        ),
    )


def infer_domain_from_title(title: str) -> TaskDomain:
    """Infer task domain from title keywords.

    Args:
        title: Task title

    Returns:
        Inferred TaskDomain
    """
    title_lower = title.lower()

    # Refactoring keywords (check early - "auth" in refactoring isn't security)
    if any(kw in title_lower for kw in ["refactor", "clean up", "reorganize", "simplify"]):
        return TaskDomain.REFACTORING

    # Security keywords (high priority but after refactoring)
    if any(kw in title_lower for kw in ["security", "vulnerability", "encrypt"]):
        return TaskDomain.SECURITY

    # Debugging keywords
    if any(kw in title_lower for kw in ["fix", "bug", "crash", "error", "debug"]):
        return TaskDomain.DEBUGGING

    # Design keywords
    if any(kw in title_lower for kw in ["design", "architecture", "plan"]):
        return TaskDomain.DESIGN

    # Research keywords
    if any(kw in title_lower for kw in ["research", "investigate", "explore", "learn"]):
        return TaskDomain.RESEARCH

    # Feature keywords
    if any(kw in title_lower for kw in ["add", "implement", "feature", "new", "create"]):
        return TaskDomain.FEATURE

    # Performance keywords
    if any(kw in title_lower for kw in ["performance", "optimize", "speed", "slow"]):
        return TaskDomain.PERFORMANCE

    # Default
    return TaskDomain.GENERAL


def get_required_evidence_types(domain: TaskDomain) -> List[str]:
    """Get list of required evidence source names for a domain.

    Args:
        domain: The task domain

    Returns:
        List of evidence source value strings
    """
    requirements = get_requirements_for_domain(domain)
    return [source.value for source in requirements.required_sources]


def apply_domain_to_tasc(tasc, domain: Optional[TaskDomain] = None):
    """Apply domain-specific requirements to a tasc.

    This sets the required_evidence_types field based on the domain.
    If no domain is provided, attempts to infer from title.

    Args:
        tasc: The Tasc object to modify
        domain: Optional domain (inferred from title if not provided)
    """
    if domain is None:
        domain = infer_domain_from_title(tasc.title)

    tasc.required_evidence_types = get_required_evidence_types(domain)

    # Store domain in additional_notes metadata (could add dedicated field)
    if tasc.additional_notes:
        tasc.additional_notes += f"\n\n[Domain: {domain.value}]"
    else:
        tasc.additional_notes = f"[Domain: {domain.value}]"
