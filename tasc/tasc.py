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

The minimal schema defined here should be sufficient for ticket-style
use cases. Additional metadata can be added later by extending
``Tasc`` or by adding auxiliary fields into the underlying ``UObject``.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .uobj import UObject
from .atom import Atom
from .atomtypes import registry


@dataclass
class Tasc:
    """High-level representation of a Tasc ticket.

    Attributes correspond to the fields defined in the minimal ticket
    schema. All fields are stored as strings in the underlying
    universal object; dependencies are stored as a comma-separated list
    of IDs for simplicity.
    
    The optional proof-related fields (proof_hash, validated_at) enable
    integration with the proof-of-work validation system.
    """

    id: str
    status: str
    title: str
    additional_notes: str
    testing_instructions: str
    desired_outcome: str
    dependencies: List[str] = field(default_factory=list)
    
    # Optional proof-of-work fields
    proof_hash: Optional[str] = None
    validated_at: Optional[str] = None

    # Learning-specific fields (for learning tascs)
    learning_mode: Optional[str] = None  # "INGEST" or "EXPLORE"
    confidence_score: Optional[float] = None  # 0.0-1.0
    gaps: List[str] = field(default_factory=list)
    unresolved_questions: List[str] = field(default_factory=list)
    review_schedule: Optional[Dict[str, str]] = None  # Spaced repetition schedule
    related_session_id: Optional[str] = None  # Link to LearningSession card

    # Evidence-based validation fields
    evidence_collection_id: Optional[str] = None  # Reference to EvidenceCollection atom
    validation_confidence: Optional[float] = None  # Overall validation confidence (0.0-1.0)
    required_evidence_types: List[str] = field(default_factory=list)  # Required evidence sources
    validation_status: Optional[str] = None  # "pending", "partial", "complete", "failed"

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
        # Include proof fields if set
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "status": self.status,
            "title": self.title,
            "additional_notes": self.additional_notes,
            "testing_instructions": self.testing_instructions,
            "desired_outcome": self.desired_outcome,
            "dependencies": self.dependencies,
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
    def from_dict(cls, data: Dict[str, Any]) -> "Tasc":
        """Create a Tasc from a dictionary."""
        deps = data.get("dependencies", [])
        if isinstance(deps, str):
            deps = [d for d in deps.split(",") if d]
        gaps = data.get("gaps", [])
        if isinstance(gaps, list):
            gaps = gaps
        else:
            gaps = []
        unresolved = data.get("unresolved_questions", [])
        if isinstance(unresolved, list):
            unresolved = unresolved
        else:
            unresolved = []
        return cls(
            id=data.get("id", ""),
            status=data.get("status", "pending"),
            title=data.get("title", ""),
            additional_notes=data.get("additional_notes", ""),
            testing_instructions=data.get("testing_instructions", ""),
            desired_outcome=data.get("desired_outcome", ""),
            dependencies=deps,
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

        # Parse learning fields (stored as JSON strings in UObject)
        gaps = []
        if data.get("gaps"):
            try:
                gaps = json.loads(data["gaps"])
            except:
                gaps = []

        unresolved = []
        if data.get("unresolved_questions"):
            try:
                unresolved = json.loads(data["unresolved_questions"])
            except:
                unresolved = []

        review_schedule = None
        if data.get("review_schedule"):
            try:
                review_schedule = json.loads(data["review_schedule"])
            except:
                review_schedule = None

        confidence_score = None
        if data.get("confidence_score"):
            try:
                confidence_score = float(data["confidence_score"])
            except:
                confidence_score = None

        # Parse evidence validation fields
        required_evidence_types = []
        if data.get("required_evidence_types"):
            try:
                required_evidence_types = json.loads(data["required_evidence_types"])
            except:
                required_evidence_types = []

        validation_confidence = None
        if data.get("validation_confidence"):
            try:
                validation_confidence = float(data["validation_confidence"])
            except:
                validation_confidence = None

        return cls(
            id=data.get("id", ""),
            status=data.get("status", ""),
            title=data.get("title", ""),
            additional_notes=data.get("additional_notes", ""),
            testing_instructions=data.get("testing_instructions", ""),
            desired_outcome=data.get("desired_outcome", ""),
            dependencies=deps,
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