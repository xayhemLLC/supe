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

    def to_uobject(self) -> UObject:
        """Represent this Tasc as a ``UObject`` with string fields."""
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
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tasc":
        """Create a Tasc from a dictionary."""
        deps = data.get("dependencies", [])
        if isinstance(deps, str):
            deps = [d for d in deps.split(",") if d]
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