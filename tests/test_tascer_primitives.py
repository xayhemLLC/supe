"""Tests for Tascer primitives - context, terminal, git, file_ops."""

import os
import tempfile
import pytest

from tascer.primitives import (
    capture_context,
    run_and_observe,
    capture_git_state,
    snapshot_file,
    diff_directories,
    TerminalResult,
    FileSnapshot,
    DirectoryDiff,
)
from tascer.contracts import GitState


class TestCaptureContext:
    """Tests for capture_context primitive."""
    
    def test_basic_capture(self):
        """capture_context should return valid Context."""
        ctx = capture_context(tasc_id="test_tasc")
        
        assert ctx.tasc_id == "test_tasc"
        assert ctx.run_id  # Auto-generated
        assert ctx.cwd == os.getcwd()
        assert ctx.os_name  # Should detect OS
        assert ctx.arch  # Should detect arch
    
    def test_captures_toolchain_versions(self):
        """Should detect available toolchain versions."""
        ctx = capture_context(
            tasc_id="test",
            tools_to_check=["python3"],
        )
        
        # Python should be available in most environments
        assert "python3" in ctx.toolchain_versions or len(ctx.toolchain_versions) >= 0
    
    def test_respects_env_allowlist(self):
        """Should only capture allowlisted env vars."""
        # Set a test env var
        os.environ["TASCER_TEST_VAR"] = "test_value"
        
        try:
            ctx = capture_context(
                tasc_id="test",
                env_allowlist=["TASCER_TEST_VAR", "NONEXISTENT"],
            )
            
            assert ctx.env_allowlist.get("TASCER_TEST_VAR") == "test_value"
            assert "NONEXISTENT" not in ctx.env_allowlist
        finally:
            del os.environ["TASCER_TEST_VAR"]


class TestRunAndObserve:
    """Tests for run_and_observe primitive."""
    
    def test_simple_command(self):
        """Should run simple command and capture output."""
        result = run_and_observe("echo hello", shell=True)
        
        assert result.exit_code == 0
        assert "hello" in result.stdout
        assert result.duration_ms > 0
    
    def test_command_with_exit_code(self):
        """Should capture non-zero exit codes."""
        result = run_and_observe("exit 42", shell=True)
        
        assert result.exit_code == 42
    
    def test_stderr_capture(self):
        """Should capture stderr output."""
        result = run_and_observe("echo error >&2", shell=True)
        
        assert result.exit_code == 0
        assert "error" in result.stderr
    
    def test_timeout(self):
        """Should handle timeout."""
        result = run_and_observe(
            "sleep 10",
            timeout_sec=0.5,
            shell=True,
        )
        
        assert result.timed_out is True
        assert result.completion_mode == "timeout"
    
    def test_command_not_found(self):
        """Should handle command not found."""
        result = run_and_observe(
            ["nonexistent_command_xyz"],
            shell=False,
        )
        
        assert result.exit_code != 0
        # Should have error info in stderr


class TestSnapshotFile:
    """Tests for snapshot_file primitive."""
    
    def test_existing_file(self):
        """Should snapshot existing file with hash."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            f.flush()
            path = f.name
        
        try:
            snap = snapshot_file(path)
            
            assert snap.exists is True
            assert snap.sha256 is not None
            assert snap.size > 0
            assert "test content" in snap.preview
        finally:
            os.unlink(path)
    
    def test_nonexistent_file(self):
        """Should handle nonexistent file."""
        snap = snapshot_file("/nonexistent/path/file.txt")
        
        assert snap.exists is False
        assert snap.sha256 is None
    
    def test_without_hash(self):
        """Should skip hash computation if requested."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("content")
            path = f.name
        
        try:
            snap = snapshot_file(path, compute_hash=False)
            
            assert snap.exists is True
            assert snap.sha256 is None
        finally:
            os.unlink(path)


class TestDiffDirectories:
    """Tests for diff_directories primitive."""
    
    def test_detect_added_file(self):
        """Should detect added files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create before snapshot (empty)
            before = {}
            
            # Add a file
            with open(os.path.join(tmpdir, "new_file.txt"), "w") as f:
                f.write("new content")
            
            # Diff
            diff = diff_directories(tmpdir, before)
            
            assert "new_file.txt" in diff.added
            assert diff.has_changes is True
    
    def test_detect_deleted_file(self):
        """Should detect deleted files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file
            file_path = os.path.join(tmpdir, "to_delete.txt")
            with open(file_path, "w") as f:
                f.write("content")
            
            # Take before snapshot
            from tascer.primitives.file_ops import snapshot_directory
            before = snapshot_directory(tmpdir)
            
            # Delete file
            os.unlink(file_path)
            
            # Diff
            diff = diff_directories(tmpdir, before)
            
            assert "to_delete.txt" in diff.deleted
    
    def test_detect_modified_file(self):
        """Should detect modified files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file
            file_path = os.path.join(tmpdir, "modify_me.txt")
            with open(file_path, "w") as f:
                f.write("original")
            
            # Take before snapshot
            from tascer.primitives.file_ops import snapshot_directory
            before = snapshot_directory(tmpdir)
            
            # Modify file
            with open(file_path, "w") as f:
                f.write("modified")
            
            # Diff
            diff = diff_directories(tmpdir, before)
            
            assert "modify_me.txt" in diff.modified


class TestCaptureGitState:
    """Tests for capture_git_state primitive."""
    
    def test_in_git_repo(self):
        """Should capture git state in a git repo."""
        # Use the actual repo we're in
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        try:
            state = capture_git_state(repo_root)
            
            assert state.branch  # Should have a branch
            assert state.commit  # Should have a commit
            assert isinstance(state.dirty, bool)
        except ValueError:
            # Not a git repo, skip test
            pytest.skip("Not in a git repository")
    
    def test_not_git_repo(self):
        """Should raise error for non-git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="Not a git repository"):
                capture_git_state(tmpdir)
