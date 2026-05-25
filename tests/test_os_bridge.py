"""Tests for AgentOS OS Bridge module."""

import pytest
import os
import tempfile
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.os_bridge import OSBridge, SecurityError, Permission


class TestOSBridge:
    """Test OS Bridge operations."""

    @pytest.fixture
    def bridge(self):
        """Create an OS Bridge instance with temp workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield OSBridge(workspace_dir=tmpdir)

    def test_workspace_dir_created(self, bridge):
        """Test workspace directory is set."""
        assert bridge.workspace_dir is not None
        assert os.path.exists(bridge.workspace_dir)

    def test_read_file_success(self, bridge):
        """Test reading a file."""
        # Create a test file
        test_file = os.path.join(bridge.workspace_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Hello, World!")

        result = bridge.read_file(test_file)
        assert result["success"] is True
        assert result["content"] == "Hello, World!"

    def test_read_file_not_found(self, bridge):
        """Test reading non-existent file."""
        result = bridge.read_file(os.path.join(bridge.workspace_dir, "nonexistent.txt"))
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_write_file_success(self, bridge):
        """Test writing a file."""
        test_file = os.path.join(bridge.workspace_dir, "output.txt")
        result = bridge.write_file(test_file, "Test content")
        assert result["success"] is True
        assert os.path.exists(test_file)

    def test_write_file_protected_path(self, bridge):
        """Test writing to protected path is blocked."""
        with pytest.raises(SecurityError):
            bridge.write_file("C:\\Windows\\System32\\test.txt", "malicious")

    def test_delete_file(self, bridge):
        """Test deleting a file."""
        test_file = os.path.join(bridge.workspace_dir, "delete_me.txt")
        with open(test_file, "w") as f:
            f.write("Delete me")

        result = bridge.delete_file(test_file)
        assert result["success"] is True
        assert not os.path.exists(test_file)

    def test_list_directory(self, bridge):
        """Test listing directory."""
        # Create test files
        with open(os.path.join(bridge.workspace_dir, "file1.txt"), "w") as f:
            f.write("content1")
        with open(os.path.join(bridge.workspace_dir, "file2.txt"), "w") as f:
            f.write("content2")

        os.makedirs(os.path.join(bridge.workspace_dir, "subdir"), exist_ok=True)

        result = bridge.list_directory(bridge.workspace_dir)
        assert result["success"] is True
        assert len(result["entries"]) >= 2

    def test_get_file_info(self, bridge):
        """Test getting file info."""
        test_file = os.path.join(bridge.workspace_dir, "info.txt")
        with open(test_file, "w") as f:
            f.write("Test")

        result = bridge.get_file_info(test_file)
        assert result["success"] is True
        assert result["type"] == "file"
        assert "size" in result

    def test_path_exists(self, bridge):
        """Test path existence check."""
        test_file = os.path.join(bridge.workspace_dir, "exists.txt")
        with open(test_file, "w") as f:
            f.write("test")

        assert bridge.path_exists(test_file) is True
        assert bridge.path_exists(os.path.join(bridge.workspace_dir, "nonexistent.txt")) is False

    def test_path_exists_protected(self, bridge):
        """Test path exists returns False for protected paths."""
        assert bridge.path_exists("C:\\Windows\\System32") is False

    def test_normalize_path(self, bridge):
        """Test path normalization."""
        normalized = bridge.normalize_path("~/test/path")
        assert "test" in normalized
        assert normalized != "~/test/path"  # Should expand ~

    def test_create_directory(self, bridge):
        """Test creating a directory."""
        new_dir = os.path.join(bridge.workspace_dir, "new_directory")
        result = bridge.create_directory(new_dir)
        assert result["success"] is True
        assert os.path.isdir(new_dir)


class TestOSBridgeSecurity:
    """Test OS Bridge security features."""

    @pytest.fixture
    def bridge(self):
        """Create an OS Bridge instance with temp workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield OSBridge(workspace_dir=tmpdir)

    def test_blocked_paths_windows(self, bridge):
        """Test dangerous paths are blocked on Windows."""
        if os.name == 'nt':
            with pytest.raises(SecurityError):
                bridge._is_path_safe("C:\\Windows\\System32\\cmd.exe")

    def test_blocked_paths_macos(self, bridge):
        """Test dangerous paths are blocked on macOS."""
        if os.name == 'posix':
            with pytest.raises(SecurityError):
                bridge._is_path_safe("/System/Library/Extensions")

    def test_command_blocked(self, bridge):
        """Test dangerous commands are blocked."""
        with pytest.raises(SecurityError):
            bridge._check_command_safety("rm -rf /")

    def test_command_blocked_windows(self, bridge):
        """Test dangerous Windows commands blocked."""
        with pytest.raises(SecurityError):
            bridge._check_command_safety("format c:")


class TestOSBridgeFileWatching:
    """Test file watching functionality."""

    @pytest.fixture
    def bridge(self):
        """Create an OS Bridge instance with temp workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield OSBridge(workspace_dir=tmpdir)

    def test_watch_directory(self, bridge):
        """Test starting a directory watch."""
        result = bridge.watch_directory(bridge.workspace_dir)
        assert result["success"] is True
        assert "watcher_id" in result
        assert result["file_count"] >= 0

    def test_watch_invalid_path(self, bridge):
        """Test watching non-existent path."""
        result = bridge.watch_directory("/nonexistent/path")
        assert result["success"] is False

    def test_check_for_changes(self, bridge):
        """Test checking for file changes."""
        # Start watching
        watch_result = bridge.watch_directory(bridge.workspace_dir)
        watcher_id = watch_result["watcher_id"]

        # Create a new file
        import time
        test_file = os.path.join(bridge.workspace_dir, "newfile.txt")
        with open(test_file, "w") as f:
            f.write("new content")
        time.sleep(0.1)

        # Check for changes
        result = bridge.check_for_changes(watcher_id)
        assert result["success"] is True
        assert len(result["changes"]["created"]) >= 1

    def test_stop_watching(self, bridge):
        """Test stopping a watch."""
        result = bridge.watch_directory(bridge.workspace_dir)
        watcher_id = result["watcher_id"]

        stop_result = bridge.stop_watching(watcher_id)
        assert stop_result["success"] is True


class TestOSBridgeBatchOperations:
    """Test batch file operations."""

    @pytest.fixture
    def bridge(self):
        """Create an OS Bridge instance with temp workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield OSBridge(workspace_dir=tmpdir)

    def test_copy_file(self, bridge):
        """Test copying a file."""
        source = os.path.join(bridge.workspace_dir, "source.txt")
        dest = os.path.join(bridge.workspace_dir, "dest.txt")

        with open(source, "w") as f:
            f.write("test content")

        result = bridge.copy_file(source, dest)
        assert result["success"] is True
        assert os.path.exists(dest)

    def test_move_file(self, bridge):
        """Test moving a file."""
        source = os.path.join(bridge.workspace_dir, "original.txt")
        dest = os.path.join(bridge.workspace_dir, "moved.txt")

        with open(source, "w") as f:
            f.write("test content")

        result = bridge.move_file(source, dest)
        assert result["success"] is True
        assert os.path.exists(dest)
        assert not os.path.exists(source)

    def test_search_files(self, bridge):
        """Test searching for files."""
        # Create test files
        for name in ["test1.txt", "test2.py", "other.log"]:
            with open(os.path.join(bridge.workspace_dir, name), "w") as f:
                f.write("content")

        result = bridge.search_files(bridge.workspace_dir, "test*.txt")
        assert result["success"] is True
        assert result["count"] >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])