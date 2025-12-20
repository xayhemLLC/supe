"""Ledger Storage - Persistence and cross-referencing.

Provides a unified storage layer for both ledgers with:
- JSON file persistence
- Cross-reference lookup between Exe and Moments
- Forensic analysis helpers
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .moments import MomentsLedger, MomentEntry, MomentType
from .exe import ExeLedger, Decision, DecisionType


@dataclass
class CrossReference:
    """Cross-reference between Exe and Moments entries."""
    
    decision_id: str
    moment_id: str
    action_id: Optional[str]
    relationship: str  # "executed", "result_of", "triggered_by"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "moment_id": self.moment_id,
            "action_id": self.action_id,
            "relationship": self.relationship,
        }


class LedgerStorage:
    """Unified storage for Moments and Exe ledgers.
    
    Manages persistence and provides cross-reference
    capabilities for forensic analysis.
    """
    
    def __init__(
        self,
        run_id: str,
        output_dir: str = "./tascer_output",
    ):
        """Initialize storage.
        
        Args:
            run_id: Unique run identifier.
            output_dir: Directory for ledger files.
        """
        self.run_id = run_id
        self.output_dir = output_dir
        
        # Initialize both ledgers
        self.moments = MomentsLedger(run_id)
        self.exe = ExeLedger(run_id)
        
        # Cross-references
        self._cross_refs: List[CrossReference] = []
    
    def add_cross_reference(
        self,
        decision_id: str,
        moment_id: str,
        relationship: str = "executed",
        action_id: Optional[str] = None,
    ) -> CrossReference:
        """Add a cross-reference between ledgers."""
        ref = CrossReference(
            decision_id=decision_id,
            moment_id=moment_id,
            action_id=action_id,
            relationship=relationship,
        )
        self._cross_refs.append(ref)
        return ref
    
    def execute_action(
        self,
        action_id: str,
        inputs: Dict[str, Any],
        narrative: str = "",
    ) -> Tuple[Decision, MomentEntry]:
        """Record action execution in both ledgers.
        
        Creates linked entries in Exe (decision) and Moments (action start).
        
        Args:
            action_id: Action being executed.
            inputs: Action inputs.
            narrative: Reasoning for this action.
        
        Returns:
            Tuple of (Decision, MomentEntry).
        """
        # Record in Exe (intent)
        decision = self.exe.record_execution(action_id=action_id)
        
        # Record in Moments (reality)
        moment = self.moments.record_action_start(action_id=action_id, inputs=inputs)
        
        # Link them
        decision.moment_ref = moment.moment_id
        self.add_cross_reference(
            decision_id=decision.decision_id,
            moment_id=moment.moment_id,
            action_id=action_id,
            relationship="executed",
        )
        
        return decision, moment
    
    def record_result(
        self,
        action_id: str,
        result: Dict[str, Any],
        success: bool,
    ) -> MomentEntry:
        """Record action result in Moments ledger."""
        return self.moments.record_action_result(
            action_id=action_id,
            result={**result, "success": success},
        )
    
    def get_moments_for_decision(self, decision_id: str) -> List[MomentEntry]:
        """Get all Moments entries linked to a decision."""
        moment_ids = [
            ref.moment_id
            for ref in self._cross_refs
            if ref.decision_id == decision_id
        ]
        return [
            entry for entry in self.moments.get_all()
            if entry.moment_id in moment_ids
        ]
    
    def get_decisions_for_moment(self, moment_id: str) -> List[Decision]:
        """Get all decisions linked to a Moment entry."""
        decision_ids = [
            ref.decision_id
            for ref in self._cross_refs
            if ref.moment_id == moment_id
        ]
        return [
            d for d in self.exe.get_all()
            if d.decision_id in decision_ids
        ]
    
    def analyze_divergence(self) -> List[Dict[str, Any]]:
        """Analyze divergence between intent (Exe) and reality (Moments).
        
        Returns cases where:
        - Proposed actions weren't executed
        - Executed actions had unexpected results
        - Confidence was miscalibrated
        """
        divergences = []
        
        # Find proposals without executions
        proposals = self.exe.get_proposals()
        for proposal in proposals:
            executions = [
                d for d in self.exe.get_by_action(proposal.action_id or "")
                if d.decision_type == DecisionType.EXECUTE
            ]
            if not executions:
                divergences.append({
                    "type": "unexecuted_proposal",
                    "decision": proposal.to_dict(),
                })
        
        # Find action results that differ from expectations
        for ref in self._cross_refs:
            if ref.relationship == "executed":
                moments = self.get_moments_for_decision(ref.decision_id)
                results = [
                    m for m in moments
                    if m.moment_type == MomentType.ACTION_RESULT
                ]
                for result in results:
                    if not result.data.get("success", True):
                        divergences.append({
                            "type": "unexpected_failure",
                            "decision_id": ref.decision_id,
                            "moment": result.to_dict(),
                        })
        
        return divergences
    
    def save(self) -> Dict[str, str]:
        """Save both ledgers to disk.
        
        Returns:
            Dict mapping ledger names to file paths.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        
        paths = {}
        
        # Save Moments
        moments_path = os.path.join(
            self.output_dir,
            f"{self.run_id}_moments.json"
        )
        with open(moments_path, "w") as f:
            json.dump(self.moments.to_dict(), f, indent=2)
        paths["moments"] = moments_path
        
        # Save Exe
        exe_path = os.path.join(
            self.output_dir,
            f"{self.run_id}_exe.json"
        )
        with open(exe_path, "w") as f:
            json.dump(self.exe.to_dict(), f, indent=2)
        paths["exe"] = exe_path
        
        # Save cross-references
        refs_path = os.path.join(
            self.output_dir,
            f"{self.run_id}_refs.json"
        )
        with open(refs_path, "w") as f:
            json.dump(
                {
                    "run_id": self.run_id,
                    "cross_references": [r.to_dict() for r in self._cross_refs],
                },
                f,
                indent=2,
            )
        paths["refs"] = refs_path
        
        return paths
    
    @classmethod
    def load(cls, run_id: str, output_dir: str = "./tascer_output") -> "LedgerStorage":
        """Load ledgers from disk.
        
        Args:
            run_id: Run identifier to load.
            output_dir: Directory containing ledger files.
        
        Returns:
            LedgerStorage with loaded data.
        """
        storage = cls(run_id=run_id, output_dir=output_dir)
        
        # Load Moments
        moments_path = os.path.join(output_dir, f"{run_id}_moments.json")
        if os.path.exists(moments_path):
            with open(moments_path, "r") as f:
                storage.moments = MomentsLedger.from_dict(json.load(f))
        
        # Load Exe
        exe_path = os.path.join(output_dir, f"{run_id}_exe.json")
        if os.path.exists(exe_path):
            with open(exe_path, "r") as f:
                storage.exe = ExeLedger.from_dict(json.load(f))
        
        # Load cross-references
        refs_path = os.path.join(output_dir, f"{run_id}_refs.json")
        if os.path.exists(refs_path):
            with open(refs_path, "r") as f:
                data = json.load(f)
                storage._cross_refs = [
                    CrossReference(**ref)
                    for ref in data.get("cross_references", [])
                ]
        
        return storage
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize entire storage to dictionary."""
        return {
            "run_id": self.run_id,
            "moments": self.moments.to_dict(),
            "exe": self.exe.to_dict(),
            "cross_references": [r.to_dict() for r in self._cross_refs],
        }
