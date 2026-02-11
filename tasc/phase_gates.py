"""Phase transition gates for Canonical Unified Flow (CUF).

Gates are validation rules that must pass before a Tasc can transition
from one phase to another. This enforces CUF discipline and ensures
tascs don't skip critical steps.

Example usage:
    from tasc.phase_gates import PhaseGateRegistry, PhaseGateResult

    registry = PhaseGateRegistry()

    @registry.register_gate("explore_to_define")
    def require_insights(tasc, from_phase, to_phase) -> PhaseGateResult:
        if not tasc.additional_notes:
            return PhaseGateResult.fail("No insights documented from exploration")
        return PhaseGateResult.ok("Insights documented")

    # Later, when transitioning:
    results = registry.validate_transition(tasc, TascPhase.EXPLORE, TascPhase.DEFINE)
    if results.all_passed:
        tasc.transition_to(TascPhase.DEFINE)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .tasc import Tasc, TascPhase


class GateSeverity(Enum):
    """How strictly to enforce a gate."""

    BLOCKING = "blocking"  # Must pass to transition
    WARNING = "warning"  # Logged but doesn't block
    INFO = "info"  # Informational only


@dataclass
class PhaseGateResult:
    """Result of evaluating a phase transition gate."""

    gate_name: str
    passed: bool
    message: str
    severity: GateSeverity = GateSeverity.BLOCKING
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, message: str, gate_name: str = "", **details: Any) -> PhaseGateResult:
        """Create a passing gate result."""
        return cls(
            gate_name=gate_name,
            passed=True,
            message=message,
            details=details,
        )

    @classmethod
    def fail(
        cls,
        message: str,
        gate_name: str = "",
        severity: GateSeverity = GateSeverity.BLOCKING,
        **details: Any,
    ) -> PhaseGateResult:
        """Create a failing gate result."""
        return cls(
            gate_name=gate_name,
            passed=False,
            message=message,
            severity=severity,
            details=details,
        )

    @classmethod
    def warn(cls, message: str, gate_name: str = "", **details: Any) -> PhaseGateResult:
        """Create a warning (non-blocking) gate result."""
        return cls(
            gate_name=gate_name,
            passed=False,
            message=message,
            severity=GateSeverity.WARNING,
            details=details,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "passed": self.passed,
            "message": self.message,
            "severity": self.severity.value,
            "details": self.details,
        }


@dataclass
class TransitionValidationResult:
    """Aggregated result of all gates for a phase transition."""

    from_phase: str
    to_phase: str
    gate_results: list[PhaseGateResult]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None).isoformat())

    @property
    def all_passed(self) -> bool:
        """True if all blocking gates passed."""
        return all(
            r.passed or r.severity != GateSeverity.BLOCKING for r in self.gate_results
        )

    @property
    def blocking_failures(self) -> list[PhaseGateResult]:
        """Gates that failed and are blocking."""
        return [
            r
            for r in self.gate_results
            if not r.passed and r.severity == GateSeverity.BLOCKING
        ]

    @property
    def warnings(self) -> list[PhaseGateResult]:
        """Gates that failed but are only warnings."""
        return [
            r
            for r in self.gate_results
            if not r.passed and r.severity == GateSeverity.WARNING
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_phase": self.from_phase,
            "to_phase": self.to_phase,
            "all_passed": self.all_passed,
            "gate_results": [r.to_dict() for r in self.gate_results],
            "timestamp": self.timestamp,
        }


# Type alias for gate functions
PhaseGateFunc = Callable[["Tasc", "TascPhase", "TascPhase"], PhaseGateResult]


class PhaseGateRegistry:
    """Registry for phase transition gates.

    Gates can be registered for specific transitions (e.g., "explore_to_define")
    or for all transitions involving a phase (e.g., "entering_build", "leaving_validate").
    """

    def __init__(self) -> None:
        # Gates for specific transitions: "from_to" -> [gates]
        self._transition_gates: dict[str, list[tuple[str, PhaseGateFunc]]] = {}
        # Gates for entering any phase: "entering_phase" -> [gates]
        self._entering_gates: dict[str, list[tuple[str, PhaseGateFunc]]] = {}
        # Gates for leaving any phase: "leaving_phase" -> [gates]
        self._leaving_gates: dict[str, list[tuple[str, PhaseGateFunc]]] = {}
        # Universal gates that run on every transition
        self._universal_gates: list[tuple[str, PhaseGateFunc]] = []

    def register_gate(
        self,
        name: str,
        *,
        from_phase: TascPhase | None = None,
        to_phase: TascPhase | None = None,
    ) -> Callable[[PhaseGateFunc], PhaseGateFunc]:
        """Decorator to register a phase transition gate.

        Args:
            name: Unique name for this gate
            from_phase: Source phase (None = any phase)
            to_phase: Target phase (None = any phase)

        Examples:
            # Gate for specific transition
            @registry.register_gate("require_hypothesis", from_phase=TascPhase.EXPLORE, to_phase=TascPhase.DEFINE)
            def check_hypothesis(tasc, from_p, to_p):
                ...

            # Gate for entering BUILD from any phase
            @registry.register_gate("require_design", to_phase=TascPhase.BUILD)
            def check_design(tasc, from_p, to_p):
                ...

            # Gate for leaving VALIDATE to any phase
            @registry.register_gate("require_evidence", from_phase=TascPhase.VALIDATE)
            def check_evidence(tasc, from_p, to_p):
                ...

            # Universal gate (all transitions)
            @registry.register_gate("audit_log")
            def log_transition(tasc, from_p, to_p):
                ...
        """

        def decorator(func: PhaseGateFunc) -> PhaseGateFunc:
            if from_phase is not None and to_phase is not None:
                # Specific transition
                key = f"{from_phase.value}_to_{to_phase.value}"
                if key not in self._transition_gates:
                    self._transition_gates[key] = []
                self._transition_gates[key].append((name, func))
            elif to_phase is not None:
                # Entering a phase
                key = to_phase.value
                if key not in self._entering_gates:
                    self._entering_gates[key] = []
                self._entering_gates[key].append((name, func))
            elif from_phase is not None:
                # Leaving a phase
                key = from_phase.value
                if key not in self._leaving_gates:
                    self._leaving_gates[key] = []
                self._leaving_gates[key].append((name, func))
            else:
                # Universal gate
                self._universal_gates.append((name, func))
            return func

        return decorator

    def validate_transition(
        self,
        tasc: Tasc,
        from_phase: TascPhase,
        to_phase: TascPhase,
    ) -> TransitionValidationResult:
        """Run all applicable gates for a phase transition.

        Returns a TransitionValidationResult with all gate outcomes.
        """
        results: list[PhaseGateResult] = []

        # Collect all applicable gates
        gates_to_run: list[tuple[str, PhaseGateFunc]] = []

        # Universal gates
        gates_to_run.extend(self._universal_gates)

        # Leaving gates
        if from_phase.value in self._leaving_gates:
            gates_to_run.extend(self._leaving_gates[from_phase.value])

        # Entering gates
        if to_phase.value in self._entering_gates:
            gates_to_run.extend(self._entering_gates[to_phase.value])

        # Specific transition gates
        transition_key = f"{from_phase.value}_to_{to_phase.value}"
        if transition_key in self._transition_gates:
            gates_to_run.extend(self._transition_gates[transition_key])

        # Run all gates
        for gate_name, gate_func in gates_to_run:
            try:
                result = gate_func(tasc, from_phase, to_phase)
                # Ensure gate_name is set
                if not result.gate_name:
                    result.gate_name = gate_name
                results.append(result)
            except Exception as e:
                # Gate threw an exception - treat as blocking failure
                results.append(
                    PhaseGateResult.fail(
                        f"Gate raised exception: {e}",
                        gate_name=gate_name,
                        exception=str(e),
                    )
                )

        return TransitionValidationResult(
            from_phase=from_phase.value,
            to_phase=to_phase.value,
            gate_results=results,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Default CUF Gates
# ─────────────────────────────────────────────────────────────────────────────

default_registry = PhaseGateRegistry()


def get_default_registry() -> PhaseGateRegistry:
    """Get the default phase gate registry with standard CUF gates."""
    return default_registry


# Import TascPhase here to avoid circular imports at module level
def _register_default_gates() -> None:
    """Register the default CUF gates."""
    from .tasc import TascPhase

    # ─────────────────────────────────────────────────────────────────────────
    # EXPLORE → DEFINE: Must have gathered insights
    # ─────────────────────────────────────────────────────────────────────────
    @default_registry.register_gate(
        "require_exploration_insights",
        from_phase=TascPhase.EXPLORE,
        to_phase=TascPhase.DEFINE,
    )
    def require_exploration_insights(
        tasc: Tasc, from_phase: TascPhase, to_phase: TascPhase
    ) -> PhaseGateResult:
        """Ensure exploration produced some insights before defining."""
        if not tasc.additional_notes and not tasc.unresolved_questions:
            return PhaseGateResult.warn(
                "No insights or questions documented from exploration. "
                "Consider documenting what was learned.",
                gate_name="require_exploration_insights",
            )
        return PhaseGateResult.ok(
            "Exploration insights documented", gate_name="require_exploration_insights"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # DEFINE → DESIGN: Must have success criteria
    # ─────────────────────────────────────────────────────────────────────────
    @default_registry.register_gate(
        "require_success_criteria",
        from_phase=TascPhase.DEFINE,
        to_phase=TascPhase.DESIGN,
    )
    def require_success_criteria(
        tasc: Tasc, from_phase: TascPhase, to_phase: TascPhase
    ) -> PhaseGateResult:
        """Ensure success criteria are defined before designing."""
        if not tasc.success_criteria and not tasc.desired_outcome:
            return PhaseGateResult.fail(
                "No success criteria or desired outcome defined. "
                "How will you know when this is done?",
                gate_name="require_success_criteria",
            )
        return PhaseGateResult.ok(
            "Success criteria defined", gate_name="require_success_criteria"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # DESIGN → BUILD: Must have chosen approach
    # ─────────────────────────────────────────────────────────────────────────
    @default_registry.register_gate(
        "require_chosen_approach",
        from_phase=TascPhase.DESIGN,
        to_phase=TascPhase.BUILD,
    )
    def require_chosen_approach(
        tasc: Tasc, from_phase: TascPhase, to_phase: TascPhase
    ) -> PhaseGateResult:
        """Ensure an approach was chosen before building."""
        if not tasc.chosen_approach and not tasc.testing_instructions:
            return PhaseGateResult.warn(
                "No approach documented. Consider documenting the chosen solution.",
                gate_name="require_chosen_approach",
            )
        return PhaseGateResult.ok(
            "Approach documented", gate_name="require_chosen_approach"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # BUILD → VALIDATE: Must have something to validate
    # ─────────────────────────────────────────────────────────────────────────
    @default_registry.register_gate(
        "require_testable_artifact",
        from_phase=TascPhase.BUILD,
        to_phase=TascPhase.VALIDATE,
    )
    def require_testable_artifact(
        tasc: Tasc, from_phase: TascPhase, to_phase: TascPhase
    ) -> PhaseGateResult:
        """Ensure there's something to validate."""
        if not tasc.testing_instructions:
            return PhaseGateResult.fail(
                "No testing instructions defined. What should be validated?",
                gate_name="require_testable_artifact",
            )
        return PhaseGateResult.ok(
            "Testing instructions defined", gate_name="require_testable_artifact"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # VALIDATE → SHIP: Must have validation evidence
    # ─────────────────────────────────────────────────────────────────────────
    @default_registry.register_gate(
        "require_validation_evidence",
        from_phase=TascPhase.VALIDATE,
        to_phase=TascPhase.SHIP,
    )
    def require_validation_evidence(
        tasc: Tasc, from_phase: TascPhase, to_phase: TascPhase
    ) -> PhaseGateResult:
        """Ensure validation produced evidence before shipping."""
        if not tasc.proof_hash and tasc.validation_status != "complete":
            return PhaseGateResult.fail(
                "No validation proof or complete validation status. "
                "Shipping without validation is risky.",
                gate_name="require_validation_evidence",
            )
        return PhaseGateResult.ok(
            "Validation evidence exists", gate_name="require_validation_evidence"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # SHIP → OBSERVE: Must have observation config (warning only)
    # ─────────────────────────────────────────────────────────────────────────
    @default_registry.register_gate(
        "recommend_observation_config",
        from_phase=TascPhase.SHIP,
        to_phase=TascPhase.OBSERVE,
    )
    def recommend_observation_config(
        tasc: Tasc, from_phase: TascPhase, to_phase: TascPhase
    ) -> PhaseGateResult:
        """Recommend setting up observation config."""
        if not tasc.observation_config:
            return PhaseGateResult.warn(
                "No observation config set. Consider defining metrics and thresholds.",
                gate_name="recommend_observation_config",
            )
        return PhaseGateResult.ok(
            "Observation config defined", gate_name="recommend_observation_config"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Any → INSTITUTIONALIZE: Must have proven value
    # ─────────────────────────────────────────────────────────────────────────
    @default_registry.register_gate(
        "require_proven_value",
        to_phase=TascPhase.INSTITUTIONALIZE,
    )
    def require_proven_value(
        tasc: Tasc, from_phase: TascPhase, to_phase: TascPhase
    ) -> PhaseGateResult:
        """Ensure tasc has proven its value before institutionalizing."""
        if tasc.cycle_count < 1:
            return PhaseGateResult.warn(
                "No iteration cycles completed. Institutionalizing untested work "
                "may embed bad patterns.",
                gate_name="require_proven_value",
            )
        return PhaseGateResult.ok(
            f"Completed {tasc.cycle_count} iteration cycle(s)",
            gate_name="require_proven_value",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Any → RETIRE: Must have deprecation plan
    # ─────────────────────────────────────────────────────────────────────────
    @default_registry.register_gate(
        "require_deprecation_plan",
        to_phase=TascPhase.RETIRE,
    )
    def require_deprecation_plan(
        tasc: Tasc, from_phase: TascPhase, to_phase: TascPhase
    ) -> PhaseGateResult:
        """Ensure a deprecation plan exists before retiring."""
        if not tasc.deprecation_plan:
            return PhaseGateResult.warn(
                "No deprecation plan. Consider documenting migration steps "
                "and notifying dependents.",
                gate_name="require_deprecation_plan",
            )
        return PhaseGateResult.ok(
            "Deprecation plan exists", gate_name="require_deprecation_plan"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Prevent skipping critical phases (universal gate)
    # ─────────────────────────────────────────────────────────────────────────
    @default_registry.register_gate("prevent_phase_skipping")
    def prevent_phase_skipping(
        tasc: Tasc, from_phase: TascPhase, to_phase: TascPhase
    ) -> PhaseGateResult:
        """Warn when skipping multiple phases forward."""
        phase_order = [
            TascPhase.EXPLORE,
            TascPhase.DEFINE,
            TascPhase.DESIGN,
            TascPhase.BUILD,
            TascPhase.VALIDATE,
            TascPhase.SHIP,
            TascPhase.OBSERVE,
            TascPhase.IMPROVE,
            TascPhase.INSTITUTIONALIZE,
            TascPhase.RETIRE,
        ]

        try:
            from_idx = phase_order.index(from_phase)
            to_idx = phase_order.index(to_phase)
        except ValueError:
            return PhaseGateResult.ok("Phase order check skipped")

        # Allow backward transitions (iteration loops)
        if to_idx <= from_idx:
            return PhaseGateResult.ok(
                "Backward/same transition allowed", gate_name="prevent_phase_skipping"
            )

        # Warn if skipping more than one phase forward
        if to_idx - from_idx > 2:
            skipped = [p.value for p in phase_order[from_idx + 1 : to_idx]]
            return PhaseGateResult.warn(
                f"Skipping phases: {', '.join(skipped)}. "
                "Consider whether these steps are truly unnecessary.",
                gate_name="prevent_phase_skipping",
                skipped_phases=skipped,
            )

        return PhaseGateResult.ok(
            "Normal phase progression", gate_name="prevent_phase_skipping"
        )


# Register default gates on module load
_register_default_gates()
