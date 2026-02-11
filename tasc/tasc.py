"""Wrapper for Tasc objects built on top of universal objects.

The ``Tasc`` class encapsulates the data fields necessary to describe
implementation tasks or tickets in the Tasc OS. A Tasc is defined by
several human-readable fields (ID, status, title, notes, test
instructions, desired outcomes) and a list of dependencies (IDs of
other Tascs).

This module provides methods to serialise a Tasc into a universal
object (``UObject``) and then into an ATOM of type ``"tasc"``. It
also provides a classmethod to reverse the process: given an ATOM of
type ``tasc``, decode it back into a Tasc instance.

The Tasc lifecycle follows the Canonical Unified Flow (CUF):
    Explore → Define → Design → Build → Validate → Ship → Observe → Improve → Institutionalize → Retire

Each phase represents a governed transition with proofs, enabling full
lifecycle auditability.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .atom import Atom
from .atomtypes import registry
from .uobj import UObject


class PhaseTransitionError(Exception):
    """Raised when a phase transition fails gate validation."""

    def __init__(
        self,
        message: str,
        from_phase: "TascPhase",
        to_phase: "TascPhase",
        gate_failures: list[Any] | None = None,
    ):
        super().__init__(message)
        self.from_phase = from_phase
        self.to_phase = to_phase
        self.gate_failures = gate_failures or []


class TascPhase(Enum):
    """Canonical Unified Flow phases for Tasc lifecycle.

    This is a state machine, not a checklist. Most tascs loop in the middle
    (Build → Validate → Ship → Observe → Improve), some skip phases, and
    some live forever in Observe/Improve.
    """

    # Discovery and direction
    EXPLORE = "explore"
    """Reduce unknowns. Find opportunity or risk.
    Research, discovery, spikes, literature review, user interviews.
    Output: Insights, questions, candidate directions.
    Failure mode: Premature commitment."""

    DEFINE = "define"
    """Choose a direction and make it explicit.
    Problem statement, hypothesis, brief, spec, success criteria.
    Output: Intent + constraints + success definition.
    Failure mode: Vague goals, moving targets."""

    DESIGN = "design"
    """Shape the solution before paying full price.
    Ideation, sketches, PoC, architecture, approach selection.
    Output: Chosen approach + decomposition.
    Failure mode: Over-design or under-thinking."""

    # Execution
    BUILD = "build"
    """Make it real.
    Coding, training models, producing assets, tooling, construction.
    Output: Working thing (or candidate reality).
    Failure mode: Building the wrong thing very well."""

    VALIDATE = "validate"
    """Does it actually work?
    Tests, experiments, QA, benchmarks, analysis, user tests.
    Output: Evidence, pass/fail signals.
    Failure mode: Vibes-based acceptance."""

    SHIP = "ship"
    """Make it real for others.
    Deploy, release, publish, distribute, launch.
    Output: Real-world exposure.
    Failure mode: Perma-staging, fear of release."""

    # Feedback loop
    OBSERVE = "observe"
    """What is actually happening?
    Metrics, logs, monitoring, user behavior, error rates.
    Output: Ground truth.
    Failure mode: Flying blind."""

    IMPROVE = "improve"
    """Make it better, faster, cheaper, safer.
    Iteration, optimization, refactors, scaling, UX improvements.
    Output: Better version.
    Failure mode: Random tweaks, local optimization."""

    # Maturity
    INSTITUTIONALIZE = "institutionalize"
    """Make it part of the default world.
    Docs, standards, ownership, training, automation, governance.
    Output: Durable, repeatable capability.
    Failure mode: Tribal knowledge, hero systems."""

    RETIRE = "retire"
    """End it cleanly.
    Deprecation, migration, shutdowns, archiving.
    Output: Clean exit, no zombies.
    Failure mode: Undead systems draining resources."""


@dataclass
class PhaseTransition:
    """Record of a phase transition with proof."""

    from_phase: str | None  # None for initial phase
    to_phase: str
    timestamp: str
    proof_hash: str | None = None
    gate_results: list[dict[str, Any]] = field(default_factory=list)
    reason: str | None = None  # Why this transition happened

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_phase": self.from_phase,
            "to_phase": self.to_phase,
            "timestamp": self.timestamp,
            "proof_hash": self.proof_hash,
            "gate_results": self.gate_results,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PhaseTransition":
        return cls(
            from_phase=data.get("from_phase"),
            to_phase=data["to_phase"],
            timestamp=data["timestamp"],
            proof_hash=data.get("proof_hash"),
            gate_results=data.get("gate_results", []),
            reason=data.get("reason"),
        )


@dataclass
class TascCycle:
    """Tracks iteration cycles through the Build→Validate→Ship→Observe→Improve loop."""

    cycle_number: int
    started_at: str
    completed_at: str | None = None
    phases_visited: list[str] = field(default_factory=list)
    outcome: str | None = None  # "success", "partial", "failed", "abandoned"
    learnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_number": self.cycle_number,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "phases_visited": self.phases_visited,
            "outcome": self.outcome,
            "learnings": self.learnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TascCycle":
        return cls(
            cycle_number=data["cycle_number"],
            started_at=data["started_at"],
            completed_at=data.get("completed_at"),
            phases_visited=data.get("phases_visited", []),
            outcome=data.get("outcome"),
            learnings=data.get("learnings", []),
        )


@dataclass
class ObservationConfig:
    """Configuration for the Observe phase - connects to real metrics."""

    metrics_endpoint: str | None = None
    error_threshold: float = 0.01  # 1% error rate triggers alert
    success_criteria: dict[str, Any] = field(default_factory=dict)
    monitoring_duration: str | None = None  # e.g., "7d", "24h"
    rollback_trigger: str | None = None  # Condition that triggers auto-rollback

    def to_dict(self) -> dict[str, Any]:
        return {
            "metrics_endpoint": self.metrics_endpoint,
            "error_threshold": self.error_threshold,
            "success_criteria": self.success_criteria,
            "monitoring_duration": self.monitoring_duration,
            "rollback_trigger": self.rollback_trigger,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ObservationConfig":
        return cls(
            metrics_endpoint=data.get("metrics_endpoint"),
            error_threshold=data.get("error_threshold", 0.01),
            success_criteria=data.get("success_criteria", {}),
            monitoring_duration=data.get("monitoring_duration"),
            rollback_trigger=data.get("rollback_trigger"),
        )


@dataclass
class DeprecationPlan:
    """Plan for clean retirement of a Tasc."""

    replacement_tasc_id: str | None = None
    migration_steps: list[str] = field(default_factory=list)
    sunset_date: str | None = None
    dependents_notified: bool = False
    archived_artifacts: list[str] = field(default_factory=list)
    final_state_snapshot: str | None = None  # Hash of final state

    def to_dict(self) -> dict[str, Any]:
        return {
            "replacement_tasc_id": self.replacement_tasc_id,
            "migration_steps": self.migration_steps,
            "sunset_date": self.sunset_date,
            "dependents_notified": self.dependents_notified,
            "archived_artifacts": self.archived_artifacts,
            "final_state_snapshot": self.final_state_snapshot,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeprecationPlan":
        return cls(
            replacement_tasc_id=data.get("replacement_tasc_id"),
            migration_steps=data.get("migration_steps", []),
            sunset_date=data.get("sunset_date"),
            dependents_notified=data.get("dependents_notified", False),
            archived_artifacts=data.get("archived_artifacts", []),
            final_state_snapshot=data.get("final_state_snapshot"),
        )


@dataclass
class InstitutionalArtifact:
    """Knowledge captured during Institutionalize phase."""

    artifact_type: str  # "doc", "pattern", "automation", "training", "standard"
    title: str
    content_hash: str | None = None
    location: str | None = None  # File path, URL, etc.
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": self.artifact_type,
            "title": self.title,
            "content_hash": self.content_hash,
            "location": self.location,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstitutionalArtifact":
        return cls(
            artifact_type=data["artifact_type"],
            title=data["title"],
            content_hash=data.get("content_hash"),
            location=data.get("location"),
            created_at=data.get("created_at"),
        )


@dataclass
class Tasc:
    """High-level representation of a Tasc ticket with Canonical Unified Flow support.

    Attributes correspond to the fields defined in the minimal ticket
    schema. All fields are stored as strings in the underlying
    universal object; dependencies are stored as a comma-separated list
    of IDs for simplicity.

    The Tasc lifecycle follows the CUF state machine:
        Explore → Define → Design → Build → Validate → Ship → Observe → Improve → Institutionalize → Retire

    Most tascs loop in Build→Validate→Ship→Observe→Improve, with Explore/Define/Design
    happening when direction changes, Institutionalize when proving valuable, and
    Retire when no longer worth maintaining.
    """

    id: str
    status: str
    title: str
    additional_notes: str
    testing_instructions: str
    desired_outcome: str
    dependencies: list[str] = field(default_factory=list)

    # ─────────────────────────────────────────────────────────────────────────
    # Canonical Unified Flow (CUF) Fields
    # ─────────────────────────────────────────────────────────────────────────

    # Current phase in the CUF state machine
    phase: TascPhase = TascPhase.EXPLORE

    # Phase transition history (audit trail)
    phase_transitions: list[PhaseTransition] = field(default_factory=list)

    # Iteration cycle tracking (Build→Validate→Ship→Observe→Improve loops)
    cycles: list[TascCycle] = field(default_factory=list)
    current_cycle: int | None = None  # Index into cycles list

    # Phase-specific configurations
    observation_config: ObservationConfig | None = None  # For Observe phase
    deprecation_plan: DeprecationPlan | None = None  # For Retire phase
    institutional_artifacts: list[InstitutionalArtifact] = field(default_factory=list)

    # Define phase: success criteria and constraints
    success_criteria: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    hypothesis: str | None = None  # What we're testing/proving

    # Design phase: approach documentation
    chosen_approach: str | None = None
    alternatives_considered: list[str] = field(default_factory=list)
    decomposition: list[str] = field(default_factory=list)  # Sub-tasc IDs

    # Ship phase: deployment tracking
    shipped_at: str | None = None
    ship_target: str | None = None  # "production", "staging", "beta", etc.
    rollback_available: bool = False

    # ─────────────────────────────────────────────────────────────────────────
    # Original proof-of-work fields
    # ─────────────────────────────────────────────────────────────────────────

    proof_hash: str | None = None
    validated_at: str | None = None

    # Learning-specific fields (for learning tascs)
    learning_mode: str | None = None  # "INGEST" or "EXPLORE"
    confidence_score: float | None = None  # 0.0-1.0
    gaps: list[str] = field(default_factory=list)
    unresolved_questions: list[str] = field(default_factory=list)
    review_schedule: dict[str, str] | None = None  # Spaced repetition schedule
    related_session_id: str | None = None  # Link to LearningSession card

    # Evidence-based validation fields
    evidence_collection_id: str | None = None  # Reference to EvidenceCollection atom
    validation_confidence: float | None = None  # Overall validation confidence (0.0-1.0)
    required_evidence_types: list[str] = field(default_factory=list)  # Required evidence sources
    validation_status: str | None = None  # "pending", "partial", "complete", "failed"

    # ─────────────────────────────────────────────────────────────────────────
    # CUF Phase Transition Methods
    # ─────────────────────────────────────────────────────────────────────────

    def transition_to(
        self,
        new_phase: TascPhase,
        reason: str | None = None,
        proof_hash: str | None = None,
        gate_results: list[dict[str, Any]] | None = None,
        *,
        validate_gates: bool = False,
        gate_registry: Any = None,
    ) -> PhaseTransition:
        """Transition to a new phase in the CUF state machine.

        Args:
            new_phase: The target phase to transition to.
            reason: Human-readable reason for the transition.
            proof_hash: Optional proof hash for this transition.
            gate_results: Pre-computed gate results (if already validated).
            validate_gates: If True, run phase gates before transitioning.
            gate_registry: Custom gate registry (uses default if None).

        Returns:
            PhaseTransition record.

        Raises:
            PhaseTransitionError: If validate_gates=True and blocking gates fail.

        Records the transition in the audit trail and returns the transition record.
        """
        computed_gate_results = gate_results or []

        # Optionally validate gates before transitioning
        if validate_gates:
            from .phase_gates import get_default_registry

            registry = gate_registry or get_default_registry()
            validation = registry.validate_transition(self, self.phase, new_phase)
            computed_gate_results = [r.to_dict() for r in validation.gate_results]

            if not validation.all_passed:
                failures = validation.blocking_failures
                failure_msgs = [f"- {f.gate_name}: {f.message}" for f in failures]
                raise PhaseTransitionError(
                    f"Cannot transition from {self.phase.value} to {new_phase.value}. "
                    f"Blocking gates failed:\n" + "\n".join(failure_msgs),
                    from_phase=self.phase,
                    to_phase=new_phase,
                    gate_failures=failures,
                )

        transition = PhaseTransition(
            from_phase=self.phase.value,
            to_phase=new_phase.value,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            proof_hash=proof_hash,
            gate_results=computed_gate_results,
            reason=reason,
        )
        self.phase_transitions.append(transition)

        old_phase = self.phase
        self.phase = new_phase

        # Track cycles when entering Build phase
        if new_phase == TascPhase.BUILD:
            self._start_new_cycle()

        # Complete cycle when leaving Improve phase (back to Build or forward)
        if old_phase == TascPhase.IMPROVE and new_phase in (
            TascPhase.BUILD,
            TascPhase.INSTITUTIONALIZE,
            TascPhase.RETIRE,
        ):
            self._complete_current_cycle()

        return transition

    def can_transition_to(
        self,
        new_phase: TascPhase,
        gate_registry: Any = None,
    ) -> tuple[bool, list[Any]]:
        """Check if a transition to the given phase would pass all gates.

        Args:
            new_phase: The target phase to check.
            gate_registry: Custom gate registry (uses default if None).

        Returns:
            Tuple of (can_transition, list of gate results).
        """
        from .phase_gates import get_default_registry

        registry = gate_registry or get_default_registry()
        validation = registry.validate_transition(self, self.phase, new_phase)
        return validation.all_passed, validation.gate_results

    def _start_new_cycle(self) -> None:
        """Start a new iteration cycle."""
        cycle = TascCycle(
            cycle_number=len(self.cycles) + 1,
            started_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            phases_visited=[TascPhase.BUILD.value],
        )
        self.cycles.append(cycle)
        self.current_cycle = len(self.cycles) - 1

    def _complete_current_cycle(self) -> None:
        """Mark the current cycle as complete."""
        if self.current_cycle is not None and self.current_cycle < len(self.cycles):
            cycle = self.cycles[self.current_cycle]
            cycle.completed_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

    def record_phase_visit(self) -> None:
        """Record that the current phase was visited in the current cycle."""
        if self.current_cycle is not None and self.current_cycle < len(self.cycles):
            cycle = self.cycles[self.current_cycle]
            if self.phase.value not in cycle.phases_visited:
                cycle.phases_visited.append(self.phase.value)

    def add_learning(self, learning: str) -> None:
        """Add a learning to the current cycle."""
        if self.current_cycle is not None and self.current_cycle < len(self.cycles):
            self.cycles[self.current_cycle].learnings.append(learning)

    @property
    def cycle_count(self) -> int:
        """Number of iteration cycles this tasc has gone through."""
        return len(self.cycles)

    @property
    def is_in_feedback_loop(self) -> bool:
        """Check if tasc is in the Build→Validate→Ship→Observe→Improve loop."""
        return self.phase in (
            TascPhase.BUILD,
            TascPhase.VALIDATE,
            TascPhase.SHIP,
            TascPhase.OBSERVE,
            TascPhase.IMPROVE,
        )

    @property
    def is_mature(self) -> bool:
        """Check if tasc has reached maturity phases."""
        return self.phase in (TascPhase.INSTITUTIONALIZE, TascPhase.RETIRE)

    @property
    def is_retired(self) -> bool:
        """Check if tasc has been retired."""
        return self.phase == TascPhase.RETIRE

    def to_uobject(self) -> UObject:
        """Represent this Tasc as a ``UObject`` with string fields."""
        import json

        dep_str = ",".join(self.dependencies)
        data = {
            "kind": "tasc",
            "id": self.id,
            "status": self.status,
            "title": self.title,
            "additional_notes": self.additional_notes,
            "testing_instructions": self.testing_instructions,
            "desired_outcome": self.desired_outcome,
            "dependencies": dep_str,
        }

        # ─────────────────────────────────────────────────────────────────────
        # CUF fields
        # ─────────────────────────────────────────────────────────────────────
        data["phase"] = self.phase.value
        if self.phase_transitions:
            data["phase_transitions"] = json.dumps(
                [t.to_dict() for t in self.phase_transitions]
            )
        if self.cycles:
            data["cycles"] = json.dumps([c.to_dict() for c in self.cycles])
        if self.current_cycle is not None:
            data["current_cycle"] = str(self.current_cycle)
        if self.observation_config:
            data["observation_config"] = json.dumps(self.observation_config.to_dict())
        if self.deprecation_plan:
            data["deprecation_plan"] = json.dumps(self.deprecation_plan.to_dict())
        if self.institutional_artifacts:
            data["institutional_artifacts"] = json.dumps(
                [a.to_dict() for a in self.institutional_artifacts]
            )
        if self.success_criteria:
            data["success_criteria"] = json.dumps(self.success_criteria)
        if self.constraints:
            data["constraints"] = json.dumps(self.constraints)
        if self.hypothesis:
            data["hypothesis"] = self.hypothesis
        if self.chosen_approach:
            data["chosen_approach"] = self.chosen_approach
        if self.alternatives_considered:
            data["alternatives_considered"] = json.dumps(self.alternatives_considered)
        if self.decomposition:
            data["decomposition"] = json.dumps(self.decomposition)
        if self.shipped_at:
            data["shipped_at"] = self.shipped_at
        if self.ship_target:
            data["ship_target"] = self.ship_target
        if self.rollback_available:
            data["rollback_available"] = "true"

        # ─────────────────────────────────────────────────────────────────────
        # Original proof fields
        # ─────────────────────────────────────────────────────────────────────
        if self.proof_hash:
            data["proof_hash"] = self.proof_hash
        if self.validated_at:
            data["validated_at"] = self.validated_at

        # Include learning fields if set
        if self.learning_mode:
            data["learning_mode"] = self.learning_mode
        if self.confidence_score is not None:
            data["confidence_score"] = str(self.confidence_score)
        if self.gaps:
            data["gaps"] = json.dumps(self.gaps)
        if self.unresolved_questions:
            data["unresolved_questions"] = json.dumps(self.unresolved_questions)
        if self.review_schedule:
            data["review_schedule"] = json.dumps(self.review_schedule)
        if self.related_session_id:
            data["related_session_id"] = self.related_session_id

        # Include evidence validation fields if set
        if self.evidence_collection_id:
            data["evidence_collection_id"] = self.evidence_collection_id
        if self.validation_confidence is not None:
            data["validation_confidence"] = str(self.validation_confidence)
        if self.required_evidence_types:
            data["required_evidence_types"] = json.dumps(self.required_evidence_types)
        if self.validation_status:
            data["validation_status"] = self.validation_status

        return UObject.from_dict_of_strings(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            # Core fields
            "id": self.id,
            "status": self.status,
            "title": self.title,
            "additional_notes": self.additional_notes,
            "testing_instructions": self.testing_instructions,
            "desired_outcome": self.desired_outcome,
            "dependencies": self.dependencies,
            # CUF fields
            "phase": self.phase.value,
            "phase_transitions": [t.to_dict() for t in self.phase_transitions],
            "cycles": [c.to_dict() for c in self.cycles],
            "current_cycle": self.current_cycle,
            "observation_config": (
                self.observation_config.to_dict() if self.observation_config else None
            ),
            "deprecation_plan": (
                self.deprecation_plan.to_dict() if self.deprecation_plan else None
            ),
            "institutional_artifacts": [
                a.to_dict() for a in self.institutional_artifacts
            ],
            "success_criteria": self.success_criteria,
            "constraints": self.constraints,
            "hypothesis": self.hypothesis,
            "chosen_approach": self.chosen_approach,
            "alternatives_considered": self.alternatives_considered,
            "decomposition": self.decomposition,
            "shipped_at": self.shipped_at,
            "ship_target": self.ship_target,
            "rollback_available": self.rollback_available,
            # Proof fields
            "proof_hash": self.proof_hash,
            "validated_at": self.validated_at,
            # Learning fields
            "learning_mode": self.learning_mode,
            "confidence_score": self.confidence_score,
            "gaps": self.gaps,
            "unresolved_questions": self.unresolved_questions,
            "review_schedule": self.review_schedule,
            "related_session_id": self.related_session_id,
            # Evidence validation fields
            "evidence_collection_id": self.evidence_collection_id,
            "validation_confidence": self.validation_confidence,
            "required_evidence_types": self.required_evidence_types,
            "validation_status": self.validation_status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Tasc":
        """Create a Tasc from a dictionary."""
        # Parse list fields
        deps = data.get("dependencies", [])
        if isinstance(deps, str):
            deps = [d for d in deps.split(",") if d]

        gaps = data.get("gaps", [])
        if not isinstance(gaps, list):
            gaps = []

        unresolved = data.get("unresolved_questions", [])
        if not isinstance(unresolved, list):
            unresolved = []

        # Parse CUF phase
        phase_str = data.get("phase", "explore")
        try:
            phase = TascPhase(phase_str)
        except ValueError:
            phase = TascPhase.EXPLORE

        # Parse phase transitions
        transitions_data = data.get("phase_transitions", [])
        phase_transitions = [
            PhaseTransition.from_dict(t) if isinstance(t, dict) else t
            for t in transitions_data
        ]

        # Parse cycles
        cycles_data = data.get("cycles", [])
        cycles = [
            TascCycle.from_dict(c) if isinstance(c, dict) else c for c in cycles_data
        ]

        # Parse observation config
        obs_data = data.get("observation_config")
        observation_config = (
            ObservationConfig.from_dict(obs_data)
            if isinstance(obs_data, dict)
            else None
        )

        # Parse deprecation plan
        dep_plan_data = data.get("deprecation_plan")
        deprecation_plan = (
            DeprecationPlan.from_dict(dep_plan_data)
            if isinstance(dep_plan_data, dict)
            else None
        )

        # Parse institutional artifacts
        artifacts_data = data.get("institutional_artifacts", [])
        institutional_artifacts = [
            InstitutionalArtifact.from_dict(a) if isinstance(a, dict) else a
            for a in artifacts_data
        ]

        return cls(
            # Core fields
            id=data.get("id", ""),
            status=data.get("status", "pending"),
            title=data.get("title", ""),
            additional_notes=data.get("additional_notes", ""),
            testing_instructions=data.get("testing_instructions", ""),
            desired_outcome=data.get("desired_outcome", ""),
            dependencies=deps,
            # CUF fields
            phase=phase,
            phase_transitions=phase_transitions,
            cycles=cycles,
            current_cycle=data.get("current_cycle"),
            observation_config=observation_config,
            deprecation_plan=deprecation_plan,
            institutional_artifacts=institutional_artifacts,
            success_criteria=data.get("success_criteria", []),
            constraints=data.get("constraints", []),
            hypothesis=data.get("hypothesis"),
            chosen_approach=data.get("chosen_approach"),
            alternatives_considered=data.get("alternatives_considered", []),
            decomposition=data.get("decomposition", []),
            shipped_at=data.get("shipped_at"),
            ship_target=data.get("ship_target"),
            rollback_available=data.get("rollback_available", False),
            # Proof fields
            proof_hash=data.get("proof_hash"),
            validated_at=data.get("validated_at"),
            # Learning fields
            learning_mode=data.get("learning_mode"),
            confidence_score=data.get("confidence_score"),
            gaps=gaps,
            unresolved_questions=unresolved,
            review_schedule=data.get("review_schedule"),
            related_session_id=data.get("related_session_id"),
            # Evidence validation fields
            evidence_collection_id=data.get("evidence_collection_id"),
            validation_confidence=data.get("validation_confidence"),
            required_evidence_types=data.get("required_evidence_types", []),
            validation_status=data.get("validation_status"),
        )

    def to_atom(self) -> Atom:
        """Encode this Tasc as an ATOM of type ``"tasc"``."""
        uobj = self.to_uobject()
        ulist = uobj.to_ulist()
        payload = ulist.encode()
        tasc_type = registry.get_by_name("tasc")
        return Atom.from_value(tasc_type, payload)

    @classmethod
    def from_atom(cls, atom: Atom) -> "Tasc":
        """Decode a Tasc from a ``tasc`` Atom."""
        import json

        tasc_type = registry.get_by_name("tasc")
        if atom.pindex != tasc_type.pindex:
            raise ValueError("Atom is not of atomtype 'tasc'")
        # Payload is encoded UList
        from .ulist import UList  # local import to avoid circular

        ulist, _ = UList.decode(atom.payload, 0)
        uobj = UObject.from_ulist(ulist)
        data = uobj.to_dict_of_strings()
        if data.get("kind") != "tasc":
            raise ValueError("Decoded object kind is not 'tasc'")
        deps_str = data.get("dependencies", "")
        deps = [d for d in deps_str.split(",") if d]

        # ─────────────────────────────────────────────────────────────────────
        # Parse CUF fields (stored as JSON strings in UObject)
        # ─────────────────────────────────────────────────────────────────────

        # Phase
        phase_str = data.get("phase", "explore")
        try:
            phase = TascPhase(phase_str)
        except ValueError:
            phase = TascPhase.EXPLORE

        # Phase transitions
        phase_transitions = []
        if data.get("phase_transitions"):
            try:
                transitions_data = json.loads(data["phase_transitions"])
                phase_transitions = [
                    PhaseTransition.from_dict(t) for t in transitions_data
                ]
            except Exception:
                phase_transitions = []

        # Cycles
        cycles = []
        if data.get("cycles"):
            try:
                cycles_data = json.loads(data["cycles"])
                cycles = [TascCycle.from_dict(c) for c in cycles_data]
            except Exception:
                cycles = []

        # Current cycle
        current_cycle = None
        if data.get("current_cycle"):
            try:
                current_cycle = int(data["current_cycle"])
            except Exception:
                current_cycle = None

        # Observation config
        observation_config = None
        if data.get("observation_config"):
            try:
                obs_data = json.loads(data["observation_config"])
                observation_config = ObservationConfig.from_dict(obs_data)
            except Exception:
                observation_config = None

        # Deprecation plan
        deprecation_plan = None
        if data.get("deprecation_plan"):
            try:
                dep_data = json.loads(data["deprecation_plan"])
                deprecation_plan = DeprecationPlan.from_dict(dep_data)
            except Exception:
                deprecation_plan = None

        # Institutional artifacts
        institutional_artifacts = []
        if data.get("institutional_artifacts"):
            try:
                artifacts_data = json.loads(data["institutional_artifacts"])
                institutional_artifacts = [
                    InstitutionalArtifact.from_dict(a) for a in artifacts_data
                ]
            except Exception:
                institutional_artifacts = []

        # Define phase fields
        success_criteria = []
        if data.get("success_criteria"):
            try:
                success_criteria = json.loads(data["success_criteria"])
            except Exception:
                success_criteria = []

        constraints = []
        if data.get("constraints"):
            try:
                constraints = json.loads(data["constraints"])
            except Exception:
                constraints = []

        # Design phase fields
        alternatives_considered = []
        if data.get("alternatives_considered"):
            try:
                alternatives_considered = json.loads(data["alternatives_considered"])
            except Exception:
                alternatives_considered = []

        decomposition = []
        if data.get("decomposition"):
            try:
                decomposition = json.loads(data["decomposition"])
            except Exception:
                decomposition = []

        # ─────────────────────────────────────────────────────────────────────
        # Parse learning fields (stored as JSON strings in UObject)
        # ─────────────────────────────────────────────────────────────────────

        gaps = []
        if data.get("gaps"):
            try:
                gaps = json.loads(data["gaps"])
            except Exception:
                gaps = []

        unresolved = []
        if data.get("unresolved_questions"):
            try:
                unresolved = json.loads(data["unresolved_questions"])
            except Exception:
                unresolved = []

        review_schedule = None
        if data.get("review_schedule"):
            try:
                review_schedule = json.loads(data["review_schedule"])
            except Exception:
                review_schedule = None

        confidence_score = None
        if data.get("confidence_score"):
            try:
                confidence_score = float(data["confidence_score"])
            except Exception:
                confidence_score = None

        # Parse evidence validation fields
        required_evidence_types = []
        if data.get("required_evidence_types"):
            try:
                required_evidence_types = json.loads(data["required_evidence_types"])
            except Exception:
                required_evidence_types = []

        validation_confidence = None
        if data.get("validation_confidence"):
            try:
                validation_confidence = float(data["validation_confidence"])
            except Exception:
                validation_confidence = None

        return cls(
            # Core fields
            id=data.get("id", ""),
            status=data.get("status", ""),
            title=data.get("title", ""),
            additional_notes=data.get("additional_notes", ""),
            testing_instructions=data.get("testing_instructions", ""),
            desired_outcome=data.get("desired_outcome", ""),
            dependencies=deps,
            # CUF fields
            phase=phase,
            phase_transitions=phase_transitions,
            cycles=cycles,
            current_cycle=current_cycle,
            observation_config=observation_config,
            deprecation_plan=deprecation_plan,
            institutional_artifacts=institutional_artifacts,
            success_criteria=success_criteria,
            constraints=constraints,
            hypothesis=data.get("hypothesis"),
            chosen_approach=data.get("chosen_approach"),
            alternatives_considered=alternatives_considered,
            decomposition=decomposition,
            shipped_at=data.get("shipped_at"),
            ship_target=data.get("ship_target"),
            rollback_available=data.get("rollback_available") == "true",
            # Proof fields
            proof_hash=data.get("proof_hash"),
            validated_at=data.get("validated_at"),
            # Learning fields
            learning_mode=data.get("learning_mode"),
            confidence_score=confidence_score,
            gaps=gaps,
            unresolved_questions=unresolved,
            review_schedule=review_schedule,
            related_session_id=data.get("related_session_id"),
            # Evidence validation fields
            evidence_collection_id=data.get("evidence_collection_id"),
            validation_confidence=validation_confidence,
            required_evidence_types=required_evidence_types,
            validation_status=data.get("validation_status"),
        )

    @property
    def is_validated(self) -> bool:
        """Check if this Tasc has been validated."""
        return self.proof_hash is not None and self.validated_at is not None

    @property
    def command(self) -> str:
        """Return the testing_instructions as the command to execute.

        This is an alias for proof-of-work integration where
        testing_instructions contains the command to validate.
        """
        return self.testing_instructions

