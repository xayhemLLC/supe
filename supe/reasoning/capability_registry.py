"""Registry of reasoning capabilities the system currently possesses.

Tracks what reasoning methods are implemented and can be invoked.
"""

from dataclasses import dataclass, field
from typing import Dict, Set, Callable, List, Optional, Any
from enum import Enum
import inspect

from supe.reasoning.problem_types import ReasoningPattern, ProblemDomain
from supe.reasoning.capabilities import (
    AlgebraicManipulation,
    ExhaustiveSearch,
    HypothesisTesting,
    PatternMatcher,
    DeductiveReasoner,
    Optimizer,
)


@dataclass
class ReasoningCapability:
    """A specific reasoning capability the system can use."""
    name: str
    pattern: ReasoningPattern
    domains: Set[ProblemDomain]
    description: str
    implementation: Optional[Callable] = None
    prerequisites: Set[str] = field(default_factory=set)
    confidence: float = 1.0  # How well this capability works
    usage_count: int = 0
    success_rate: float = 0.0

    def can_handle(self, domain: ProblemDomain, pattern: ReasoningPattern) -> bool:
        """Check if this capability can handle the given domain/pattern."""
        return (domain in self.domains or ProblemDomain.UNKNOWN in self.domains) and \
               self.pattern == pattern

    def invoke(self, *args, **kwargs) -> Any:
        """Invoke this capability."""
        if self.implementation is None:
            raise NotImplementedError(f"Capability {self.name} has no implementation")

        self.usage_count += 1
        return self.implementation(*args, **kwargs)


class CapabilityRegistry:
    """Registry of all reasoning capabilities available to the system."""

    def __init__(self):
        """Initialize the registry with base capabilities."""
        self.capabilities: Dict[str, ReasoningCapability] = {}
        self._initialize_base_capabilities()

    def _initialize_base_capabilities(self):
        """Register the base reasoning capabilities."""

        # Instantiate implementations
        algebraic = AlgebraicManipulation()
        search = ExhaustiveSearch()
        hypothesis = HypothesisTesting()
        pattern = PatternMatcher()
        deductive = DeductiveReasoner()
        optimizer = Optimizer()

        # Algebraic reasoning
        self.register(ReasoningCapability(
            name="algebraic_manipulation",
            pattern=ReasoningPattern.ALGEBRAIC,
            domains={ProblemDomain.ALGEBRA, ProblemDomain.UNKNOWN},
            description="Solve equations through algebraic manipulation",
            implementation=algebraic,
            prerequisites=set(),
            confidence=0.9,
        ))

        # Systematic search
        self.register(ReasoningCapability(
            name="exhaustive_search",
            pattern=ReasoningPattern.SYSTEMATIC_SEARCH,
            domains={ProblemDomain.ALGEBRA, ProblemDomain.COMBINATORICS, ProblemDomain.UNKNOWN},
            description="Try all possible combinations systematically",
            implementation=search,
            prerequisites=set(),
            confidence=1.0,  # Always works, just may be slow
        ))

        # Hypothesis testing
        self.register(ReasoningCapability(
            name="hypothesis_testing",
            pattern=ReasoningPattern.HYPOTHESIS_TESTING,
            domains={
                ProblemDomain.PATTERN_RECOGNITION,
                ProblemDomain.ALGEBRA,
                ProblemDomain.UNKNOWN,
            },
            description="Generate and test candidate hypotheses",
            implementation=hypothesis,
            prerequisites={"hypothesis_generation"},
            confidence=0.85,
        ))

        # Constraint satisfaction
        self.register(ReasoningCapability(
            name="constraint_solver",
            pattern=ReasoningPattern.CONSTRAINT_SATISFACTION,
            domains={
                ProblemDomain.ALGEBRA,
                ProblemDomain.LOGIC,
                ProblemDomain.UNKNOWN,
            },
            description="Find values satisfying all constraints",
            implementation=search,  # Uses search for now
            prerequisites=set(),
            confidence=0.9,
        ))

        # Pattern matching
        self.register(ReasoningCapability(
            name="pattern_matcher",
            pattern=ReasoningPattern.PATTERN_MATCHING,
            domains={
                ProblemDomain.PATTERN_RECOGNITION,
                ProblemDomain.NUMBER_THEORY,
                ProblemDomain.UNKNOWN,
            },
            description="Identify patterns in sequences or structures",
            implementation=pattern,
            prerequisites=set(),
            confidence=0.75,
        ))

        # Deductive reasoning
        self.register(ReasoningCapability(
            name="deductive_reasoner",
            pattern=ReasoningPattern.DEDUCTIVE,
            domains={
                ProblemDomain.LOGIC,
                ProblemDomain.GEOMETRY,
                ProblemDomain.PROOF,
                ProblemDomain.UNKNOWN,
            },
            description="Apply logical inference rules",
            implementation=deductive,
            prerequisites=set(),
            confidence=0.95,
        ))

        # Optimization
        self.register(ReasoningCapability(
            name="optimizer",
            pattern=ReasoningPattern.OPTIMIZATION,
            domains={
                ProblemDomain.OPTIMIZATION,
                ProblemDomain.ALGEBRA,
                ProblemDomain.UNKNOWN,
            },
            description="Find minimum or maximum values",
            implementation=optimizer,
            prerequisites={"exhaustive_search"},  # Often needs search
            confidence=0.8,
        ))

        # Geometric reasoning
        self.register(ReasoningCapability(
            name="geometric_reasoner",
            pattern=ReasoningPattern.GEOMETRIC,
            domains={ProblemDomain.GEOMETRY},
            description="Apply geometric theorems and spatial reasoning",
            prerequisites=set(),
            confidence=0.85,
        ))

    def register(self, capability: ReasoningCapability):
        """Register a new capability."""
        self.capabilities[capability.name] = capability

    def get_capability(self, name: str) -> Optional[ReasoningCapability]:
        """Get a capability by name."""
        return self.capabilities.get(name)

    def find_capabilities(
        self,
        domain: ProblemDomain,
        pattern: ReasoningPattern,
    ) -> List[ReasoningCapability]:
        """Find capabilities that can handle the given domain/pattern."""
        matches = []
        for cap in self.capabilities.values():
            if cap.can_handle(domain, pattern):
                matches.append(cap)

        # Sort by confidence (best first)
        return sorted(matches, key=lambda c: c.confidence, reverse=True)

    def has_capability(self, pattern: ReasoningPattern, domain: ProblemDomain) -> bool:
        """Check if any capability exists for the pattern/domain."""
        return len(self.find_capabilities(domain, pattern)) > 0

    def get_missing_patterns(
        self,
        required_patterns: Set[ReasoningPattern],
        domain: ProblemDomain,
    ) -> Set[ReasoningPattern]:
        """Find patterns that are required but not implemented."""
        missing = set()
        for pattern in required_patterns:
            if not self.has_capability(pattern, domain):
                missing.add(pattern)
        return missing

    def update_statistics(
        self,
        capability_name: str,
        success: bool,
    ):
        """Update success statistics for a capability."""
        cap = self.get_capability(capability_name)
        if cap:
            # Exponential moving average
            alpha = 0.1
            new_rate = 1.0 if success else 0.0
            cap.success_rate = alpha * new_rate + (1 - alpha) * cap.success_rate

    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get usage statistics for all capabilities."""
        stats = {}
        for name, cap in self.capabilities.items():
            stats[name] = {
                "pattern": cap.pattern.value,
                "domains": [d.value for d in cap.domains],
                "usage_count": cap.usage_count,
                "success_rate": cap.success_rate,
                "confidence": cap.confidence,
            }
        return stats

    def list_capabilities(self) -> List[str]:
        """List all registered capability names."""
        return list(self.capabilities.keys())
