"""Tasc CLI Package.

Provides the Tasc task management system with Canonical Unified Flow (CUF) support.

CUF Phases:
    Explore → Define → Design → Build → Validate → Ship → Observe → Improve → Institutionalize → Retire

Validation Methods (7 types):
    AUTOMATED_TEST, MANUAL_REVIEW, STATIC_ANALYSIS, BENCHMARK,
    INTEGRATION_TEST, SECURITY_SCAN, USER_ACCEPTANCE
"""
from .cli import main
from .evidence import ValidationMethod
from .phase_gates import (
    GateSeverity,
    PhaseGateRegistry,
    PhaseGateResult,
    TransitionValidationResult,
    get_default_registry,
)
from .tasc import (
    DeprecationPlan,
    InstitutionalArtifact,
    ObservationConfig,
    PhaseTransition,
    PhaseTransitionError,
    Tasc,
    TascCycle,
    TascPhase,
)

__all__ = [
    "main",
    # Core Tasc
    "Tasc",
    # CUF Types
    "TascPhase",
    "PhaseTransition",
    "PhaseTransitionError",
    "TascCycle",
    "ObservationConfig",
    "DeprecationPlan",
    "InstitutionalArtifact",
    # Phase Gates
    "PhaseGateRegistry",
    "PhaseGateResult",
    "GateSeverity",
    "TransitionValidationResult",
    "get_default_registry",
    # Validation
    "ValidationMethod",
]

