"""Moments Ledger - Immutable record of reality.

The Moments Ledger captures what actually happened:
- Context snapshots
- Action results
- Evidence artifacts
- Timestamps

This is TRUTH - the authoritative record of observations and outcomes.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MomentType(Enum):
    """Types of moments that can be recorded."""
    CONTEXT_SNAPSHOT = "context_snapshot"
    ACTION_START = "action_start"
    ACTION_RESULT = "action_result"
    EVIDENCE = "evidence"
    GATE_RESULT = "gate_result"
    CHECKPOINT = "checkpoint"
    ERROR = "error"


@dataclass
class EvidenceRef:
    """Reference to an evidence artifact."""
    
    artifact_type: str  # file, screenshot, log, hash, etc.
    path: Optional[str] = None
    content_hash: Optional[str] = None
    inline_content: Optional[str] = None  # For small artifacts
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_type": self.artifact_type,
            "path": self.path,
            "content_hash": self.content_hash,
            "inline_content": self.inline_content,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceRef":
        return cls(
            artifact_type=data["artifact_type"],
            path=data.get("path"),
            content_hash=data.get("content_hash"),
            inline_content=data.get("inline_content"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MomentEntry:
    """A single entry in the Moments Ledger.
    
    Each entry is immutable and captures a specific observation
    or result at a point in time.
    """
    
    # Identity
    moment_id: str
    run_id: str
    sequence_num: int
    
    # Timing
    timestamp: datetime
    
    # Type and content
    moment_type: MomentType
    action_id: Optional[str] = None  # For action-related moments
    
    # Payload
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Evidence references
    evidence: List[EvidenceRef] = field(default_factory=list)
    
    # Hash chain for integrity
    previous_hash: Optional[str] = None
    entry_hash: Optional[str] = None
    
    def compute_hash(self) -> str:
        """Compute hash of this entry for chain integrity."""
        content = {
            "moment_id": self.moment_id,
            "run_id": self.run_id,
            "sequence_num": self.sequence_num,
            "timestamp": self.timestamp.isoformat(),
            "moment_type": self.moment_type.value,
            "action_id": self.action_id,
            "data": self.data,
            "previous_hash": self.previous_hash,
        }
        serialized = json.dumps(content, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "moment_id": self.moment_id,
            "run_id": self.run_id,
            "sequence_num": self.sequence_num,
            "timestamp": self.timestamp.isoformat(),
            "moment_type": self.moment_type.value,
            "action_id": self.action_id,
            "data": self.data,
            "evidence": [e.to_dict() for e in self.evidence],
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MomentEntry":
        return cls(
            moment_id=data["moment_id"],
            run_id=data["run_id"],
            sequence_num=data["sequence_num"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            moment_type=MomentType(data["moment_type"]),
            action_id=data.get("action_id"),
            data=data.get("data", {}),
            evidence=[EvidenceRef.from_dict(e) for e in data.get("evidence", [])],
            previous_hash=data.get("previous_hash"),
            entry_hash=data.get("entry_hash"),
        )


class MomentsLedger:
    """Immutable append-only log of reality.
    
    The Moments Ledger is the authoritative record of what happened.
    Entries cannot be modified or deleted after being appended.
    A hash chain ensures integrity.
    """
    
    def __init__(self, run_id: str):
        """Initialize ledger for a run.
        
        Args:
            run_id: Unique identifier for this run.
        """
        self.run_id = run_id
        self._entries: List[MomentEntry] = []
        self._sequence = 0
    
    def append(
        self,
        moment_type: MomentType,
        data: Dict[str, Any],
        action_id: Optional[str] = None,
        evidence: Optional[List[EvidenceRef]] = None,
    ) -> MomentEntry:
        """Append a new moment to the ledger.
        
        Args:
            moment_type: Type of moment.
            data: Moment data/payload.
            action_id: Associated action ID if applicable.
            evidence: Evidence references.
        
        Returns:
            The created MomentEntry.
        """
        self._sequence += 1
        
        previous_hash = None
        if self._entries:
            previous_hash = self._entries[-1].entry_hash
        
        entry = MomentEntry(
            moment_id=f"{self.run_id}_m{self._sequence}",
            run_id=self.run_id,
            sequence_num=self._sequence,
            timestamp=datetime.now(),
            moment_type=moment_type,
            action_id=action_id,
            data=data,
            evidence=evidence or [],
            previous_hash=previous_hash,
        )
        
        # Compute and set hash
        entry.entry_hash = entry.compute_hash()
        
        self._entries.append(entry)
        return entry
    
    def record_context(self, context_data: Dict[str, Any]) -> MomentEntry:
        """Record a context snapshot."""
        return self.append(MomentType.CONTEXT_SNAPSHOT, context_data)
    
    def record_action_start(
        self,
        action_id: str,
        inputs: Dict[str, Any]
    ) -> MomentEntry:
        """Record action start."""
        return self.append(
            MomentType.ACTION_START,
            {"inputs": inputs},
            action_id=action_id,
        )
    
    def record_action_result(
        self,
        action_id: str,
        result: Dict[str, Any],
        evidence: Optional[List[EvidenceRef]] = None,
    ) -> MomentEntry:
        """Record action result with evidence."""
        return self.append(
            MomentType.ACTION_RESULT,
            result,
            action_id=action_id,
            evidence=evidence,
        )
    
    def record_error(
        self,
        error_type: str,
        message: str,
        action_id: Optional[str] = None,
    ) -> MomentEntry:
        """Record an error."""
        return self.append(
            MomentType.ERROR,
            {"error_type": error_type, "message": message},
            action_id=action_id,
        )
    
    def get_all(self) -> List[MomentEntry]:
        """Get all entries (read-only copy)."""
        return list(self._entries)
    
    def get_by_action(self, action_id: str) -> List[MomentEntry]:
        """Get all entries for a specific action."""
        return [e for e in self._entries if e.action_id == action_id]
    
    def get_by_type(self, moment_type: MomentType) -> List[MomentEntry]:
        """Get all entries of a specific type."""
        return [e for e in self._entries if e.moment_type == moment_type]
    
    def get_latest(self, n: int = 1) -> List[MomentEntry]:
        """Get the latest N entries."""
        return self._entries[-n:] if self._entries else []
    
    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        """Verify hash chain integrity.
        
        Returns:
            Tuple of (is_valid, error_message).
        """
        for i, entry in enumerate(self._entries):
            # Verify entry hash
            computed_hash = entry.compute_hash()
            if entry.entry_hash != computed_hash:
                return False, f"Hash mismatch at entry {i}: {entry.moment_id}"
            
            # Verify chain
            if i > 0:
                expected_prev = self._entries[i - 1].entry_hash
                if entry.previous_hash != expected_prev:
                    return False, f"Chain broken at entry {i}: {entry.moment_id}"
        
        return True, None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize ledger to dictionary."""
        return {
            "run_id": self.run_id,
            "entries": [e.to_dict() for e in self._entries],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MomentsLedger":
        """Deserialize ledger from dictionary."""
        ledger = cls(run_id=data["run_id"])
        ledger._entries = [MomentEntry.from_dict(e) for e in data["entries"]]
        ledger._sequence = len(ledger._entries)
        return ledger
    
    def __len__(self) -> int:
        return len(self._entries)
