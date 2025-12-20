"""Tests for Tasc checkpoint system."""

import os
import pytest
import tempfile


class TestCheckpoint:
    """Tests for Checkpoint dataclass."""
    
    def test_checkpoint_creation(self):
        """Test creating a checkpoint."""
        from tascer.checkpoint import Checkpoint
        from datetime import datetime
        
        cp = Checkpoint(
            checkpoint_id="test_cp1",
            run_id="test_run",
            created_at=datetime.now(),
            git_branch="main",
            git_commit="abc123",
            git_dirty=False,
        )
        
        assert cp.checkpoint_id == "test_cp1"
        assert cp.git_branch == "main"
    
    def test_checkpoint_to_dict(self):
        """Test checkpoint serialization."""
        from tascer.checkpoint import Checkpoint
        from datetime import datetime
        
        cp = Checkpoint(
            checkpoint_id="test_cp1",
            run_id="test_run",
            created_at=datetime.now(),
            git_branch="main",
            git_commit="abc123",
            git_dirty=False,
            file_snapshot={"test.txt": "hash123"},
        )
        
        data = cp.to_dict()
        
        assert data["checkpoint_id"] == "test_cp1"
        assert data["git_branch"] == "main"
        assert data["file_snapshot"]["test.txt"] == "hash123"
    
    def test_checkpoint_from_dict(self):
        """Test checkpoint deserialization."""
        from tascer.checkpoint import Checkpoint
        from datetime import datetime
        
        data = {
            "checkpoint_id": "test_cp1",
            "run_id": "test_run",
            "created_at": datetime.now().isoformat(),
            "git_branch": "main",
            "git_commit": "abc123",
            "git_dirty": False,
        }
        
        cp = Checkpoint.from_dict(data)
        
        assert cp.checkpoint_id == "test_cp1"
        assert cp.git_branch == "main"


class TestCheckpointManager:
    """Tests for CheckpointManager."""
    
    def test_create_manager(self):
        """Test creating checkpoint manager."""
        from tascer.checkpoint import CheckpointManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(
                run_id="test_run",
                root_dir=tmpdir,
                output_dir=tmpdir,
            )
            
            assert not manager.has_active_checkpoint()
    
    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        from tascer.checkpoint import CheckpointManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, "w") as f:
                f.write("original content")
            
            manager = CheckpointManager(
                run_id="test_run",
                root_dir=tmpdir,
                output_dir=tmpdir,
            )
            
            checkpoint = manager.create("Test checkpoint")
            
            assert manager.has_active_checkpoint()
            assert checkpoint.checkpoint_id is not None
            assert "test.txt" in checkpoint.file_snapshot
    
    def test_require_checkpoint_raises(self):
        """Test require_checkpoint raises without checkpoint."""
        from tascer.checkpoint import CheckpointManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(
                run_id="test_run",
                root_dir=tmpdir,
                output_dir=tmpdir,
            )
            
            with pytest.raises(RuntimeError) as exc_info:
                manager.require_checkpoint("file.write")
            
            assert "checkpoint" in str(exc_info.value).lower()
    
    def test_require_checkpoint_passes(self):
        """Test require_checkpoint passes with checkpoint."""
        from tascer.checkpoint import CheckpointManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(
                run_id="test_run",
                root_dir=tmpdir,
                output_dir=tmpdir,
            )
            
            manager.create("Before test")
            manager.require_checkpoint("file.write")  # Should not raise
    
    def test_rollback_restores_file(self):
        """Test rollback restores file content."""
        from tascer.checkpoint import CheckpointManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file with original content
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, "w") as f:
                f.write("original")
            
            manager = CheckpointManager(
                run_id="test_run",
                root_dir=tmpdir,
                output_dir=tmpdir,
            )
            
            # Create checkpoint
            manager.create("Before modification")
            
            # Modify file
            with open(test_file, "w") as f:
                f.write("modified")
            
            # Verify modified
            with open(test_file, "r") as f:
                assert f.read() == "modified"
            
            # Rollback
            result = manager.rollback()
            
            # Verify restored
            with open(test_file, "r") as f:
                assert f.read() == "original"
            
            assert len(result["files_restored"]) > 0
    
    def test_rollback_deletes_new_file(self):
        """Test rollback deletes files created after checkpoint."""
        from tascer.checkpoint import CheckpointManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(
                run_id="test_run",
                root_dir=tmpdir,
                output_dir=tmpdir,
            )
            
            # Create checkpoint with empty dir
            manager.create("Before file creation")
            
            # Create new file
            new_file = os.path.join(tmpdir, "new.txt")
            with open(new_file, "w") as f:
                f.write("new content")
            
            assert os.path.exists(new_file)
            
            # Rollback
            result = manager.rollback()
            
            # File should be deleted
            assert not os.path.exists(new_file)
            assert "new.txt" in result["files_deleted"]
    
    def test_list_checkpoints(self):
        """Test listing checkpoints."""
        from tascer.checkpoint import CheckpointManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(
                run_id="test_run",
                root_dir=tmpdir,
                output_dir=tmpdir,
            )
            
            manager.create("First")
            manager.create("Second")
            manager.create("Third")
            
            checkpoints = manager.list_checkpoints()
            assert len(checkpoints) == 3
    
    def test_process_tracking(self):
        """Test process tracking."""
        from tascer.checkpoint import CheckpointManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(
                run_id="test_run",
                root_dir=tmpdir,
                output_dir=tmpdir,
            )
            
            manager.track_process(12345)
            manager.track_process(67890)
            
            checkpoint = manager.create("With processes")
            
            assert 12345 in checkpoint.tracked_pids
            assert 67890 in checkpoint.tracked_pids


class TestRequiresCheckpointDecorator:
    """Tests for @requires_checkpoint decorator."""
    
    def test_decorator_raises_without_checkpoint(self):
        """Test decorator raises when no checkpoint."""
        from tascer.checkpoint import requires_checkpoint, CheckpointManager
        
        @requires_checkpoint
        def dangerous_mutation(checkpoint_manager=None):
            return "mutated"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(
                run_id="test_run",
                root_dir=tmpdir,
                output_dir=tmpdir,
            )
            
            with pytest.raises(RuntimeError):
                dangerous_mutation(checkpoint_manager=manager)
    
    def test_decorator_passes_with_checkpoint(self):
        """Test decorator passes when checkpoint exists."""
        from tascer.checkpoint import requires_checkpoint, CheckpointManager
        
        @requires_checkpoint
        def dangerous_mutation(checkpoint_manager=None):
            return "mutated"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(
                run_id="test_run",
                root_dir=tmpdir,
                output_dir=tmpdir,
            )
            manager.create("Before mutation")
            
            result = dangerous_mutation(checkpoint_manager=manager)
            assert result == "mutated"
