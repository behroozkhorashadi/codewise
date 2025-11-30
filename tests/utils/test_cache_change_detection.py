"""Integration tests for cache change detection."""

import json
import os
import tempfile

import pytest

from source.utils.output_storage import AnalysisOutputStorage


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_repo_dir():
    """Create a temporary repository directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample Python files
        with open(os.path.join(tmpdir, "module1.py"), "w") as f:
            f.write("def func1():\n    pass\n")
        with open(os.path.join(tmpdir, "module2.py"), "w") as f:
            f.write("def func2():\n    pass\n")
        yield tmpdir


@pytest.fixture
def storage(temp_cache_dir):
    """Create AnalysisOutputStorage instance with temp cache directory."""
    return AnalysisOutputStorage(output_dir=temp_cache_dir)


@pytest.fixture
def sample_results():
    """Create sample analysis results."""
    return [
        {
            "method_name": "test_method",
            "file_path": "/test/file.py",
            "raw_response": json.dumps({"score": 8}),
            "structured_response": {"overall_score": 8},
        }
    ]


class TestCacheChangeDetection:
    """Tests for cache change detection in AnalysisOutputStorage."""

    def test_detect_no_changes_after_analysis(self, storage, temp_repo_dir, sample_results):
        """Test that no changes are detected immediately after analysis."""
        # Save analysis
        storage.save_analysis_output(
            root_directory=temp_repo_dir,
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        # Detect changes (without modifying anything)
        change_info = storage.detect_repo_changes(temp_repo_dir, None, "entire_project")

        assert change_info is None

    def test_detect_changes_after_file_modification(self, storage, temp_repo_dir, sample_results):
        """Test that changes are detected after modifying a file."""
        # Save analysis
        storage.save_analysis_output(
            root_directory=temp_repo_dir,
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        # Modify a file
        module_path = os.path.join(temp_repo_dir, "module1.py")
        with open(module_path, "w") as f:
            f.write("def func1():\n    return 42\n")

        # Detect changes
        change_info = storage.detect_repo_changes(temp_repo_dir, None, "entire_project")

        assert change_info is not None
        assert change_info['has_changes'] is True
        assert len(change_info['changes']['modified']) == 1

    def test_detect_changes_after_file_addition(self, storage, temp_repo_dir, sample_results):
        """Test that changes are detected after adding a file."""
        # Save analysis
        storage.save_analysis_output(
            root_directory=temp_repo_dir,
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        # Add a new file
        new_file_path = os.path.join(temp_repo_dir, "module3.py")
        with open(new_file_path, "w") as f:
            f.write("def func3():\n    pass\n")

        # Detect changes
        change_info = storage.detect_repo_changes(temp_repo_dir, None, "entire_project")

        assert change_info is not None
        assert change_info['has_changes'] is True
        assert len(change_info['changes']['added']) == 1

    def test_detect_changes_after_file_deletion(self, storage, temp_repo_dir, sample_results):
        """Test that changes are detected after deleting a file."""
        # Save analysis
        storage.save_analysis_output(
            root_directory=temp_repo_dir,
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        # Delete a file
        module_path = os.path.join(temp_repo_dir, "module2.py")
        os.remove(module_path)

        # Detect changes
        change_info = storage.detect_repo_changes(temp_repo_dir, None, "entire_project")

        assert change_info is not None
        assert change_info['has_changes'] is True
        assert len(change_info['changes']['removed']) == 1

    def test_detect_multiple_changes(self, storage, temp_repo_dir, sample_results):
        """Test detection of multiple simultaneous changes."""
        # Save analysis
        storage.save_analysis_output(
            root_directory=temp_repo_dir,
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        # Make multiple changes
        # 1. Modify a file
        module_path = os.path.join(temp_repo_dir, "module1.py")
        with open(module_path, "w") as f:
            f.write("def func1():\n    return 99\n")

        # 2. Delete a file
        os.remove(os.path.join(temp_repo_dir, "module2.py"))

        # 3. Add a file
        new_file_path = os.path.join(temp_repo_dir, "module3.py")
        with open(new_file_path, "w") as f:
            f.write("def func3():\n    pass\n")

        # Detect changes
        change_info = storage.detect_repo_changes(temp_repo_dir, None, "entire_project")

        assert change_info is not None
        assert change_info['has_changes'] is True
        changes = change_info['changes']
        assert len(changes['modified']) == 1
        assert len(changes['removed']) == 1
        assert len(changes['added']) == 1

    def test_detect_changes_returns_none_for_nonexistent_cache(self, storage, temp_repo_dir):
        """Test that detect_changes returns None when no cache exists."""
        change_info = storage.detect_repo_changes(temp_repo_dir, None, "entire_project")

        assert change_info is None

    def test_detect_changes_includes_timestamp(self, storage, temp_repo_dir, sample_results):
        """Test that change_info includes cached timestamp."""
        # Save analysis
        storage.save_analysis_output(
            root_directory=temp_repo_dir,
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        # Modify file
        module_path = os.path.join(temp_repo_dir, "module1.py")
        with open(module_path, "w") as f:
            f.write("def func1():\n    return 42\n")

        # Detect changes
        change_info = storage.detect_repo_changes(temp_repo_dir, None, "entire_project")

        assert 'cached_timestamp' in change_info
        assert change_info['cached_timestamp'] is not None

    def test_repo_state_stored_in_cache(self, storage, temp_repo_dir, sample_results):
        """Test that repository state is stored in cache file."""
        # Save analysis
        storage.save_analysis_output(
            root_directory=temp_repo_dir,
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        # Load cache file directly
        output_path = storage.get_analysis_output_path(temp_repo_dir, None, "entire_project")
        with open(output_path, "r") as f:
            cached_data = json.load(f)

        assert 'repo_hash' in cached_data
        assert 'repo_state' in cached_data
        assert isinstance(cached_data['repo_state'], dict)
        assert len(cached_data['repo_state']) > 0

    def test_single_file_analysis_detects_changes(self, storage, temp_repo_dir, sample_results):
        """Test change detection works for single file analysis mode."""
        file_path = os.path.join(temp_repo_dir, "module1.py")

        # Save analysis for single file
        storage.save_analysis_output(
            root_directory=temp_repo_dir,
            file_path=file_path,
            analysis_mode="single_file",
            analysis_results=sample_results,
        )

        # Modify a file in the repo
        with open(file_path, "w") as f:
            f.write("def func1():\n    return 42\n")

        # Detect changes
        change_info = storage.detect_repo_changes(temp_repo_dir, file_path, "single_file")

        assert change_info is not None
        assert change_info['has_changes'] is True

    def test_backward_compatibility_old_cache_no_repo_state(self, storage, temp_repo_dir):
        """Test backward compatibility with old cache format (no repo_state)."""
        # Create old-format cache file manually
        output_path = storage.get_analysis_output_path(temp_repo_dir, None, "entire_project")

        old_format_data = {
            "timestamp": "2025-11-29T00:00:00",
            "analysis_mode": "entire_project",
            "root_directory": temp_repo_dir,
            "file_path": None,
            "metadata": {},
            "results": [{"method_name": "old_method"}],
            # Note: No repo_hash or repo_state fields
        }

        with open(output_path, "w") as f:
            json.dump(old_format_data, f)

        # Try to detect changes
        change_info = storage.detect_repo_changes(temp_repo_dir, None, "entire_project")

        # Should return None because old format doesn't have repo_state
        assert change_info is None

    def test_cache_file_contains_detailed_file_hashes(self, storage, temp_repo_dir, sample_results):
        """Test that cache file contains detailed file hashes for each file."""
        # Save analysis
        storage.save_analysis_output(
            root_directory=temp_repo_dir,
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        # Load cache
        output_path = storage.get_analysis_output_path(temp_repo_dir, None, "entire_project")
        with open(output_path, "r") as f:
            cached_data = json.load(f)

        repo_state = cached_data['repo_state']

        # Should have entries for module1.py and module2.py
        assert any("module1.py" in path for path in repo_state.keys())
        assert any("module2.py" in path for path in repo_state.keys())

        # Each entry should be a hash string (64 chars for SHA256)
        for file_path, file_hash in repo_state.items():
            assert isinstance(file_hash, str)
            assert len(file_hash) == 64
