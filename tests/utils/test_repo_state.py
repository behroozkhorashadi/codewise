"""Tests for repository state tracking and change detection."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from source.utils.repo_state import RepositoryState


@pytest.fixture
def temp_repo_dir():
    """Create a temporary repository directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_repo(temp_repo_dir):
    """Create a sample repository with Python files."""
    # Create some Python files
    file1_path = os.path.join(temp_repo_dir, "module1.py")
    file2_path = os.path.join(temp_repo_dir, "module2.py")
    subdir_path = os.path.join(temp_repo_dir, "subdir")
    file3_path = os.path.join(subdir_path, "module3.py")

    os.makedirs(subdir_path, exist_ok=True)

    # Write some content to files
    with open(file1_path, "w") as f:
        f.write("def function1():\n    pass\n")

    with open(file2_path, "w") as f:
        f.write("def function2():\n    return True\n")

    with open(file3_path, "w") as f:
        f.write("class MyClass:\n    pass\n")

    return temp_repo_dir


class TestComputeFileHash:
    """Tests for file hash computation."""

    def test_compute_file_hash_consistent(self, sample_repo):
        """Test that hash of same file is consistent."""
        file_path = os.path.join(sample_repo, "module1.py")

        hash1 = RepositoryState._compute_file_hash(file_path)
        hash2 = RepositoryState._compute_file_hash(file_path)

        assert hash1 == hash2

    def test_compute_file_hash_changes_with_content(self, sample_repo):
        """Test that hash changes when file content changes."""
        file_path = os.path.join(sample_repo, "module1.py")

        hash1 = RepositoryState._compute_file_hash(file_path)

        # Modify file
        with open(file_path, "w") as f:
            f.write("def function1():\n    return 42\n")

        hash2 = RepositoryState._compute_file_hash(file_path)

        assert hash1 != hash2

    def test_compute_file_hash_different_files(self, sample_repo):
        """Test that different files have different hashes."""
        file1_path = os.path.join(sample_repo, "module1.py")
        file2_path = os.path.join(sample_repo, "module2.py")

        hash1 = RepositoryState._compute_file_hash(file1_path)
        hash2 = RepositoryState._compute_file_hash(file2_path)

        assert hash1 != hash2

    def test_compute_file_hash_nonexistent_file(self):
        """Test that nonexistent file returns empty hash."""
        hash_val = RepositoryState._compute_file_hash("/nonexistent/file.py")
        assert hash_val == ""


class TestComputeRepoState:
    """Tests for repository state computation."""

    def test_compute_repo_state_includes_all_files(self, sample_repo):
        """Test that repo state includes all Python files."""
        repo_state = RepositoryState.compute_repo_state(sample_repo)

        # Should have 3 Python files
        assert len(repo_state) == 3

    def test_compute_repo_state_excludes_test_files(self, sample_repo):
        """Test that test files are excluded from state."""
        # Create a test file
        test_file_path = os.path.join(sample_repo, "test_module.py")
        with open(test_file_path, "w") as f:
            f.write("def test_something():\n    pass\n")

        repo_state = RepositoryState.compute_repo_state(sample_repo)

        # Should still be 3 (test files excluded)
        assert len(repo_state) == 3

    def test_compute_repo_state_excludes_cache_dir(self, sample_repo):
        """Test that .codewise_cache directory is excluded."""
        cache_dir = os.path.join(sample_repo, ".codewise_cache")
        os.makedirs(cache_dir, exist_ok=True)

        cache_file = os.path.join(cache_dir, "cached.py")
        with open(cache_file, "w") as f:
            f.write("# cached\n")

        repo_state = RepositoryState.compute_repo_state(sample_repo)

        # Should still be 3 (cache dir excluded)
        assert len(repo_state) == 3

    def test_compute_repo_state_excludes_venv(self, sample_repo):
        """Test that venv directory is excluded."""
        venv_dir = os.path.join(sample_repo, "venv")
        os.makedirs(venv_dir, exist_ok=True)

        venv_file = os.path.join(venv_dir, "module.py")
        with open(venv_file, "w") as f:
            f.write("# venv\n")

        repo_state = RepositoryState.compute_repo_state(sample_repo)

        # Should still be 3 (venv excluded)
        assert len(repo_state) == 3

    def test_compute_repo_state_consistent(self, sample_repo):
        """Test that repo state is consistent for unchanged repo."""
        state1 = RepositoryState.compute_repo_state(sample_repo)
        state2 = RepositoryState.compute_repo_state(sample_repo)

        assert state1 == state2


class TestComputeRepoHash:
    """Tests for repository-level hash computation."""

    def test_compute_repo_hash_consistent(self, sample_repo):
        """Test that repo hash is consistent for same state."""
        repo_state = RepositoryState.compute_repo_state(sample_repo)

        hash1 = RepositoryState.compute_repo_hash(repo_state)
        hash2 = RepositoryState.compute_repo_hash(repo_state)

        assert hash1 == hash2

    def test_compute_repo_hash_changes_with_file_modification(self, sample_repo):
        """Test that repo hash changes when file is modified."""
        state1 = RepositoryState.compute_repo_state(sample_repo)
        hash1 = RepositoryState.compute_repo_hash(state1)

        # Modify a file
        file_path = os.path.join(sample_repo, "module1.py")
        with open(file_path, "w") as f:
            f.write("def function1():\n    return 99\n")

        state2 = RepositoryState.compute_repo_state(sample_repo)
        hash2 = RepositoryState.compute_repo_hash(state2)

        assert hash1 != hash2

    def test_compute_repo_hash_empty_state(self):
        """Test repo hash for empty repository."""
        hash_val = RepositoryState.compute_repo_hash({})
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64  # SHA256 hex digest length


class TestDetectChanges:
    """Tests for change detection between states."""

    def test_detect_no_changes(self, sample_repo):
        """Test that no changes are detected for identical states."""
        state1 = RepositoryState.compute_repo_state(sample_repo)
        state2 = RepositoryState.compute_repo_state(sample_repo)

        changes = RepositoryState.detect_changes(state1, state2)

        assert changes['added'] == []
        assert changes['removed'] == []
        assert changes['modified'] == []

    def test_detect_added_files(self, sample_repo):
        """Test detection of added files."""
        state1 = RepositoryState.compute_repo_state(sample_repo)

        # Add a new file
        new_file_path = os.path.join(sample_repo, "new_module.py")
        with open(new_file_path, "w") as f:
            f.write("def new_function():\n    pass\n")

        state2 = RepositoryState.compute_repo_state(sample_repo)

        changes = RepositoryState.detect_changes(state1, state2)

        assert len(changes['added']) == 1
        assert changes['removed'] == []
        assert changes['modified'] == []

    def test_detect_removed_files(self, sample_repo):
        """Test detection of removed files."""
        state1 = RepositoryState.compute_repo_state(sample_repo)

        # Remove a file
        file_path = os.path.join(sample_repo, "module1.py")
        os.remove(file_path)

        state2 = RepositoryState.compute_repo_state(sample_repo)

        changes = RepositoryState.detect_changes(state1, state2)

        assert changes['added'] == []
        assert len(changes['removed']) == 1
        assert changes['modified'] == []

    def test_detect_modified_files(self, sample_repo):
        """Test detection of modified files."""
        state1 = RepositoryState.compute_repo_state(sample_repo)

        # Modify a file
        file_path = os.path.join(sample_repo, "module1.py")
        with open(file_path, "w") as f:
            f.write("def function1():\n    return 42\n")

        state2 = RepositoryState.compute_repo_state(sample_repo)

        changes = RepositoryState.detect_changes(state1, state2)

        assert changes['added'] == []
        assert changes['removed'] == []
        assert len(changes['modified']) == 1

    def test_detect_multiple_changes(self, sample_repo):
        """Test detection of multiple changes simultaneously."""
        state1 = RepositoryState.compute_repo_state(sample_repo)

        # Modify one file
        file_path = os.path.join(sample_repo, "module1.py")
        with open(file_path, "w") as f:
            f.write("def function1():\n    return 42\n")

        # Remove one file
        os.remove(os.path.join(sample_repo, "module2.py"))

        # Add one file
        new_file_path = os.path.join(sample_repo, "new_module.py")
        with open(new_file_path, "w") as f:
            f.write("def new_function():\n    pass\n")

        state2 = RepositoryState.compute_repo_state(sample_repo)

        changes = RepositoryState.detect_changes(state1, state2)

        assert len(changes['added']) == 1
        assert len(changes['removed']) == 1
        assert len(changes['modified']) == 1


class TestHasChanges:
    """Tests for the has_changes convenience method."""

    def test_has_changes_returns_false_for_identical_states(self, sample_repo):
        """Test that has_changes returns False for identical states."""
        state1 = RepositoryState.compute_repo_state(sample_repo)
        state2 = RepositoryState.compute_repo_state(sample_repo)

        has_changes = RepositoryState.has_changes(state1, state2)

        assert has_changes is False

    def test_has_changes_returns_true_for_added_file(self, sample_repo):
        """Test that has_changes returns True when file is added."""
        state1 = RepositoryState.compute_repo_state(sample_repo)

        new_file_path = os.path.join(sample_repo, "new_module.py")
        with open(new_file_path, "w") as f:
            f.write("def new_function():\n    pass\n")

        state2 = RepositoryState.compute_repo_state(sample_repo)

        has_changes = RepositoryState.has_changes(state1, state2)

        assert has_changes is True

    def test_has_changes_returns_true_for_removed_file(self, sample_repo):
        """Test that has_changes returns True when file is removed."""
        state1 = RepositoryState.compute_repo_state(sample_repo)

        os.remove(os.path.join(sample_repo, "module1.py"))

        state2 = RepositoryState.compute_repo_state(sample_repo)

        has_changes = RepositoryState.has_changes(state1, state2)

        assert has_changes is True

    def test_has_changes_returns_true_for_modified_file(self, sample_repo):
        """Test that has_changes returns True when file is modified."""
        state1 = RepositoryState.compute_repo_state(sample_repo)

        file_path = os.path.join(sample_repo, "module1.py")
        with open(file_path, "w") as f:
            f.write("def function1():\n    return 42\n")

        state2 = RepositoryState.compute_repo_state(sample_repo)

        has_changes = RepositoryState.has_changes(state1, state2)

        assert has_changes is True
