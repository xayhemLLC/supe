"""Evidence atoms for task validation.

This module defines Evidence as an atomic structure that can be encoded/decoded
using the Atom system. Evidence is the fundamental unit of validation - all
task validation is based on collecting, evaluating, and storing evidence artifacts.

Evidence follows the learning system's proven methodology while respecting the
Atom-based architecture of the Tasc system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .atom import Atom
from .atomtypes import registry
from .uobj import UObject


class EvidenceSource(Enum):
    """Sources of evidence for task validation.

    These match the learning system's evidence sources but are extended
    for task-specific validation scenarios.
    """
    # Learning system sources
    DOC = "doc"                    # Documentation, comments, design docs
    CODE = "code"                  # Source code, implementation
    TEST = "test"                  # Test results, test cases
    EXPERIMENT = "experiment"      # Experimental validation, reproduction steps
    REASONING = "reasoning"        # Logical analysis, hypotheses
    PEER_REVIEW = "peer_review"    # Code reviews, human feedback

    # Task-specific sources
    CODE_ANALYSIS = "code_analysis"      # Static analysis, linting
    PROFILING = "profiling"              # Performance measurements
    SECURITY_SCAN = "security_scan"      # Security analysis results
    USER_FEEDBACK = "user_feedback"      # User acceptance testing
    METRIC = "metric"                    # Quantitative measurements
    ARTIFACT = "artifact"                # Build artifacts, screenshots, logs
    BENCHMARK = "benchmark"              # Performance benchmarks
    REGRESSION_TEST = "regression_test"  # Tests added to prevent recurrence


@dataclass
class Evidence:
    """Evidence supporting task completion or validation.

    Evidence is the atomic unit of validation. Each piece of evidence:
    - Has a unique ID
    - Comes from a specific source
    - Contains traceable citations
    - Can be validated
    - Has a confidence score

    Evidence can be encoded as Atoms for storage in the Tasc system.
    """

    id: str
    text: str
    source: EvidenceSource
    citations: List[str] = field(default_factory=list)
    validated: bool = False
    validation_method: str = ""
    confidence: float = 1.0
    created_at: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, text: str, source: EvidenceSource, citations: List[str]) -> "Evidence":
        """Factory method to create new evidence."""
        return cls(
            id=str(uuid4()),
            text=text,
            source=source,
            citations=citations,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "source": self.source.value,
            "citations": self.citations,
            "validated": self.validated,
            "validation_method": self.validation_method,
            "confidence": float(self.confidence),
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Evidence":
        """Create Evidence from dictionary."""
        return cls(
            id=data["id"],
            text=data["text"],
            source=EvidenceSource(data["source"]),
            citations=data.get("citations", []),
            validated=data.get("validated", False),
            validation_method=data.get("validation_method", ""),
            confidence=float(data.get("confidence", 1.0)),
            created_at=int(data.get("created_at", int(datetime.now().timestamp() * 1000))),
            metadata=data.get("metadata", {}),
        )

    def to_uobject(self) -> UObject:
        """Convert to UObject for Atom encoding."""
        import json

        data = {
            "kind": "evidence",
            "id": self.id,
            "text": self.text,
            "source": self.source.value,
            "citations": json.dumps(self.citations),
            "validated": "1" if self.validated else "0",
            "validation_method": self.validation_method,
            "confidence": str(self.confidence),
            "created_at": str(self.created_at),
            "metadata": json.dumps(self.metadata),
        }

        return UObject.from_dict_of_strings(data)

    @classmethod
    def from_uobject(cls, uobj: UObject) -> "Evidence":
        """Create Evidence from UObject."""
        import json

        data = uobj.to_dict_of_strings()

        if data.get("kind") != "evidence":
            raise ValueError("UObject kind is not 'evidence'")

        citations = []
        if data.get("citations"):
            try:
                citations = json.loads(data["citations"])
            except:
                citations = []

        metadata = {}
        if data.get("metadata"):
            try:
                metadata = json.loads(data["metadata"])
            except:
                metadata = {}

        return cls(
            id=data["id"],
            text=data["text"],
            source=EvidenceSource(data["source"]),
            citations=citations,
            validated=data.get("validated") == "1",
            validation_method=data.get("validation_method", ""),
            confidence=float(data.get("confidence", "1.0")),
            created_at=int(data.get("created_at", str(int(datetime.now().timestamp() * 1000)))),
            metadata=metadata,
        )

    def to_atom(self) -> Atom:
        """Encode as an Atom of type 'evidence'."""
        uobj = self.to_uobject()
        ulist = uobj.to_ulist()
        payload = ulist.encode()
        evidence_type = registry.get_by_name("evidence")
        return Atom.from_value(evidence_type, payload)

    @classmethod
    def from_atom(cls, atom: Atom) -> "Evidence":
        """Decode Evidence from an 'evidence' Atom."""
        evidence_type = registry.get_by_name("evidence")
        if atom.pindex != evidence_type.pindex:
            raise ValueError("Atom is not of atomtype 'evidence'")

        from .ulist import UList
        ulist, _ = UList.decode(atom.payload, 0)
        uobj = UObject.from_ulist(ulist)
        return cls.from_uobject(uobj)


@dataclass
class EvidenceCollection:
    """A collection of evidence artifacts for task validation.

    This groups related evidence together and can be encoded as a single Atom.
    """

    id: str
    tasc_id: str  # The tasc this evidence collection validates
    evidence_items: List[Evidence] = field(default_factory=list)
    created_at: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))

    @classmethod
    def create(cls, tasc_id: str) -> "EvidenceCollection":
        """Create a new evidence collection for a tasc."""
        return cls(
            id=str(uuid4()),
            tasc_id=tasc_id,
        )

    def add_evidence(self, evidence: Evidence) -> None:
        """Add an evidence item to the collection."""
        self.evidence_items.append(evidence)

    def get_evidence_by_source(self, source: EvidenceSource) -> List[Evidence]:
        """Get all evidence from a specific source."""
        return [e for e in self.evidence_items if e.source == source]

    def get_validated_evidence(self) -> List[Evidence]:
        """Get all validated evidence."""
        return [e for e in self.evidence_items if e.validated]

    def get_source_diversity(self) -> int:
        """Get the number of unique evidence sources."""
        return len(set(e.source for e in self.evidence_items))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "tasc_id": self.tasc_id,
            "evidence_items": [e.to_dict() for e in self.evidence_items],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceCollection":
        """Create EvidenceCollection from dictionary."""
        return cls(
            id=data["id"],
            tasc_id=data["tasc_id"],
            evidence_items=[Evidence.from_dict(e) for e in data.get("evidence_items", [])],
            created_at=int(data.get("created_at", int(datetime.now().timestamp() * 1000))),
        )

    def to_uobject(self) -> UObject:
        """Convert to UObject for Atom encoding."""
        import json

        data = {
            "kind": "evidence_collection",
            "id": self.id,
            "tasc_id": self.tasc_id,
            "evidence_ids": json.dumps([e.id for e in self.evidence_items]),
            "evidence_count": str(len(self.evidence_items)),
            "created_at": str(self.created_at),
        }

        return UObject.from_dict_of_strings(data)

    def to_atom(self) -> Atom:
        """Encode as an Atom of type 'evidence_collection'."""
        uobj = self.to_uobject()
        ulist = uobj.to_ulist()
        payload = ulist.encode()
        collection_type = registry.get_by_name("evidence_collection")
        return Atom.from_value(collection_type, payload)


# Helper functions for evidence collection

def collect_test_evidence(
    test_results: Dict[str, Any],
    test_command: str = ""
) -> Evidence:
    """Create evidence from test results.

    Args:
        test_results: Dictionary with test results (passed, failed, total, etc.)
        test_command: Command used to run tests

    Returns:
        Evidence object
    """
    passed = test_results.get("passed", 0)
    total = test_results.get("total", 0)

    text = f"Test suite: {passed}/{total} tests passed"
    if test_results.get("coverage"):
        text += f" (coverage: {test_results['coverage']}%)"

    citations = []
    if test_command:
        citations.append(f"command:{test_command}")
    if test_results.get("report_path"):
        citations.append(test_results["report_path"])

    return Evidence.create(
        text=text,
        source=EvidenceSource.TEST,
        citations=citations,
    )


def collect_code_evidence(
    file_path: str,
    line_start: int,
    line_end: int,
    description: str,
    commit_hash: Optional[str] = None
) -> Evidence:
    """Create evidence from code changes.

    Args:
        file_path: Path to the modified file
        line_start: Starting line number
        line_end: Ending line number
        description: Description of the change
        commit_hash: Optional git commit hash

    Returns:
        Evidence object
    """
    citations = [f"{file_path}:{line_start}-{line_end}"]
    if commit_hash:
        citations.append(f"commit:{commit_hash}")

    return Evidence.create(
        text=description,
        source=EvidenceSource.CODE,
        citations=citations,
    )


def collect_documentation_evidence(
    doc_path: str,
    section: str,
    content: str
) -> Evidence:
    """Create evidence from documentation.

    Args:
        doc_path: Path to documentation file
        section: Section heading or identifier
        content: Documentation content

    Returns:
        Evidence object
    """
    return Evidence.create(
        text=content,
        source=EvidenceSource.DOC,
        citations=[f"{doc_path}#{section}"],
    )


def collect_analysis_evidence(
    analysis_type: str,
    findings: str,
    tool: str = ""
) -> Evidence:
    """Create evidence from code analysis.

    Args:
        analysis_type: Type of analysis (linting, security, etc.)
        findings: Analysis findings
        tool: Tool used for analysis

    Returns:
        Evidence object
    """
    citations = []
    if tool:
        citations.append(f"tool:{tool}")

    return Evidence.create(
        text=f"{analysis_type}: {findings}",
        source=EvidenceSource.CODE_ANALYSIS,
        citations=citations,
    )
