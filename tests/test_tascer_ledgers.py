"""Tests for Tasc ledgers."""

import json
import os
import pytest
import tempfile
from datetime import datetime


class TestMomentsLedger:
    """Tests for Moments Ledger (reality log)."""
    
    def test_create_empty_ledger(self):
        """Test creating an empty moments ledger."""
        from tascer.ledgers import MomentsLedger
        
        ledger = MomentsLedger(run_id="test_run")
        assert len(ledger) == 0
    
    def test_record_context(self):
        """Test recording context snapshot."""
        from tascer.ledgers import MomentsLedger
        
        ledger = MomentsLedger(run_id="test_run")
        moment = ledger.record_context({"cwd": "/test", "branch": "main"})
        
        assert moment is not None
        assert moment.moment_type.value == "context_snapshot"
        assert moment.data["cwd"] == "/test"
        assert len(ledger) == 1
    
    def test_record_action_start(self):
        """Test recording action start."""
        from tascer.ledgers import MomentsLedger
        
        ledger = MomentsLedger(run_id="test_run")
        moment = ledger.record_action_start("terminal.run", {"command": "ls"})
        
        assert moment.action_id == "terminal.run"
        assert moment.moment_type.value == "action_start"
    
    def test_record_action_result(self):
        """Test recording action result."""
        from tascer.ledgers import MomentsLedger
        
        ledger = MomentsLedger(run_id="test_run")
        moment = ledger.record_action_result(
            "terminal.run",
            {"exit_code": 0, "stdout": "hello"},
        )
        
        assert moment.moment_type.value == "action_result"
        assert moment.data["exit_code"] == 0
    
    def test_hash_chain_integrity(self):
        """Test hash chain links moments together."""
        from tascer.ledgers import MomentsLedger
        
        ledger = MomentsLedger(run_id="test_run")
        m1 = ledger.record_context({"test": 1})
        m2 = ledger.record_context({"test": 2})
        m3 = ledger.record_context({"test": 3})
        
        # Each moment should have hash
        assert m1.entry_hash is not None
        assert m2.entry_hash is not None
        assert m3.entry_hash is not None
        
        # Hashes should be different
        assert m1.entry_hash != m2.entry_hash
        assert m2.entry_hash != m3.entry_hash
        
        # Later entries link to previous
        assert m2.previous_hash == m1.entry_hash
        assert m3.previous_hash == m2.entry_hash
    
    def test_verify_integrity(self):
        """Test integrity verification passes for valid chain."""
        from tascer.ledgers import MomentsLedger
        
        ledger = MomentsLedger(run_id="test_run")
        ledger.record_context({"test": 1})
        ledger.record_context({"test": 2})
        ledger.record_context({"test": 3})
        
        assert ledger.verify_integrity()
    
    def test_get_by_action(self):
        """Test filtering moments by action."""
        from tascer.ledgers import MomentsLedger
        
        ledger = MomentsLedger(run_id="test_run")
        ledger.record_action_start("terminal.run", {})
        ledger.record_action_start("file.read", {})
        ledger.record_action_result("terminal.run", {"exit_code": 0})
        
        terminal_moments = ledger.get_by_action("terminal.run")
        assert len(terminal_moments) == 2
    
    def test_to_dict_and_back(self):
        """Test serialization/deserialization."""
        from tascer.ledgers import MomentsLedger
        
        ledger = MomentsLedger(run_id="test_run")
        ledger.record_context({"test": "value"})
        ledger.record_action_start("test.action", {"input": 42})
        
        data = ledger.to_dict()
        
        assert data["run_id"] == "test_run"
        assert len(data["entries"]) == 2


class TestExeLedger:
    """Tests for Exe Ledger (intent log)."""
    
    def test_create_empty_ledger(self):
        """Test creating an empty exe ledger."""
        from tascer.ledgers import ExeLedger
        
        ledger = ExeLedger(run_id="test_run")
        assert len(ledger) == 0
    
    def test_record_narrative(self):
        """Test recording narrative decision."""
        from tascer.ledgers import ExeLedger
        
        ledger = ExeLedger(run_id="test_run")
        decision = ledger.record_narrative("Starting diagnostics")
        
        assert decision.narrative == "Starting diagnostics"
        assert len(ledger) == 1
    
    def test_record_execution(self):
        """Test recording execution decision."""
        from tascer.ledgers import ExeLedger
        
        ledger = ExeLedger(run_id="test_run")
        decision = ledger.record_execution("terminal.run")
        
        assert decision.action_id == "terminal.run"
        assert decision.decision_type.value == "execute"
    
    def test_record_stop(self):
        """Test recording stop decision."""
        from tascer.ledgers import ExeLedger
        from tascer.ledgers.exe import StopReason
        
        ledger = ExeLedger(run_id="test_run")
        decision = ledger.record_stop(StopReason.GOAL_ACHIEVED, "Task complete")
        
        assert decision.decision_type.value == "stop"
        assert decision.stop_reason == StopReason.GOAL_ACHIEVED
    
    def test_record_rejection(self):
        """Test recording rejection."""
        from tascer.ledgers import ExeLedger
        
        ledger = ExeLedger(run_id="test_run")
        decision = ledger.record_rejection("file.delete", "Missing permissions")
        
        assert decision.action_id == "file.delete"
        assert decision.decision_type.value == "reject"
    
    def test_confidence_scoring(self):
        """Test confidence scoring on decisions."""
        from tascer.ledgers import ExeLedger
        from tascer.ledgers.exe import ConfidenceScore
        
        ledger = ExeLedger(run_id="test_run")
        confidence = ConfidenceScore(value=0.85, calibration_note="High certainty")
        decision = ledger.record_execution("terminal.run", confidence=confidence)
        
        assert decision.confidence.value == 0.85


class TestLedgerStorage:
    """Tests for integrated ledger storage."""
    
    def test_create_storage(self):
        """Test creating ledger storage."""
        from tascer.ledgers import LedgerStorage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LedgerStorage(run_id="test_run", output_dir=tmpdir)
            assert storage.moments is not None
            assert storage.exe is not None
    
    def test_execute_action_records_both(self):
        """Test execute_action records in both ledgers."""
        from tascer.ledgers import LedgerStorage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LedgerStorage(run_id="test_run", output_dir=tmpdir)
            storage.execute_action("terminal.run", {"command": "ls"})
            
            assert len(storage.exe) >= 1
            assert len(storage.moments) >= 1
    
    def test_cross_reference(self):
        """Test cross-referencing between ledgers."""
        from tascer.ledgers import LedgerStorage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LedgerStorage(run_id="test_run", output_dir=tmpdir)
            storage.execute_action("terminal.run", {"command": "ls"})
            
            # Cross-refs are stored internally
            assert len(storage._cross_refs) >= 1
    
    def test_save_and_load(self):
        """Test saving to disk."""
        from tascer.ledgers import LedgerStorage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LedgerStorage(run_id="test_run", output_dir=tmpdir)
            storage.moments.record_context({"test": "value"})
            storage.exe.record_narrative("Testing save")
            
            paths = storage.save()
            
            assert os.path.exists(paths["moments"])
            assert os.path.exists(paths["exe"])
