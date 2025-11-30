"""Integration tests for output_storage with structured responses."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from source.utils.output_storage import AnalysisOutputStorage


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def storage(temp_cache_dir):
    """Create AnalysisOutputStorage instance with temp directory."""
    return AnalysisOutputStorage(output_dir=temp_cache_dir)


@pytest.fixture
def sample_structured_response():
    """Create a sample structured response."""
    return {
        "overall_score": 8,
        "overall_feedback": "Well-implemented method",
        "criteria_scores": {
            "separation_of_concerns": 9,
            "documentation": 9,
            "logic_clarity": 8,
            "understandability": 8,
            "efficiency": 6,
            "error_handling": 7,
            "testability": 8,
            "reusability": 8,
            "code_consistency": 9,
            "dependency_management": 8,
            "security_awareness": 7,
            "side_effects": 8,
            "scalability": 5,
            "resource_management": 7,
            "encapsulation": 8,
            "readability": 9,
        },
        "criteria_feedback": {
            "separation_of_concerns": "Clear single responsibility",
            "documentation": "Excellent docstring",
            "logic_clarity": None,
            "understandability": None,
            "efficiency": "Consider optimization",
            "error_handling": None,
            "testability": None,
            "reusability": None,
            "code_consistency": None,
            "dependency_management": None,
            "security_awareness": None,
            "side_effects": None,
            "scalability": "May have issues with large data",
            "resource_management": None,
            "encapsulation": None,
            "readability": None,
        },
        "suggestions": ["Optimize loops", "Add type hints"],
        "strengths": ["Well-structured", "Clear intent"],
    }


@pytest.fixture
def sample_results(sample_structured_response):
    """Create sample analysis results with structured responses."""
    return [
        {
            "method_name": "method_1",
            "file_path": "/path/to/file1.py",
            "raw_response": json.dumps(sample_structured_response),
            "structured_response": sample_structured_response,
        },
        {
            "method_name": "method_2",
            "file_path": "/path/to/file2.py",
            "raw_response": json.dumps(sample_structured_response),
            "structured_response": sample_structured_response,
        },
    ]


class TestSaveStructuredResults:
    """Tests for saving structured results."""

    def test_save_single_file_analysis(self, storage, sample_results):
        """Test saving single file analysis results."""
        output_path = storage.save_analysis_output(
            root_directory="/test/path",
            file_path="/test/path/file.py",
            analysis_mode="single_file",
            analysis_results=sample_results,
            metadata={"method_count": 2},
        )

        assert os.path.exists(output_path)
        assert "single_file.json" in output_path

    def test_save_entire_project_analysis(self, storage, sample_results):
        """Test saving entire project analysis results."""
        output_path = storage.save_analysis_output(
            root_directory="/test/memori",
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
            metadata={"method_count": 2, "file_count": 1},
        )

        assert os.path.exists(output_path)
        assert "entire_project.json" in output_path

    def test_saved_file_contains_both_responses(self, storage, sample_results):
        """Test that saved file contains both raw and structured responses."""
        output_path = storage.save_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        with open(output_path, 'r') as f:
            data = json.load(f)

        # Check structure
        assert "results" in data
        assert len(data["results"]) == 2

        # Check each result
        for result in data["results"]:
            assert "method_name" in result
            assert "raw_response" in result
            assert "structured_response" in result

    def test_saved_file_has_timestamp(self, storage, sample_results):
        """Test that saved file has timestamp."""
        output_path = storage.save_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert "timestamp" in data
        assert data["timestamp"] is not None

    def test_saved_file_has_metadata(self, storage, sample_results):
        """Test that saved file includes metadata."""
        output_path = storage.save_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
            metadata={"method_count": 2, "file_count": 1},
        )

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert "metadata" in data
        assert data["metadata"]["method_count"] == 2
        assert data["metadata"]["file_count"] == 1


class TestLoadStructuredResults:
    """Tests for loading structured results."""

    def test_load_existing_results(self, storage, sample_results):
        """Test loading existing results."""
        # Save first
        storage.save_analysis_output(
            root_directory="/test/path",
            file_path="/test/path/file.py",
            analysis_mode="single_file",
            analysis_results=sample_results,
        )

        # Load
        loaded = storage.load_analysis_output(
            root_directory="/test/path",
            file_path="/test/path/file.py",
            analysis_mode="single_file",
        )

        assert loaded is not None
        assert "results" in loaded
        assert len(loaded["results"]) == 2

    def test_load_nonexistent_results(self, storage):
        """Test loading non-existent results returns None."""
        loaded = storage.load_analysis_output(
            root_directory="/nonexistent/path",
            file_path=None,
            analysis_mode="entire_project",
        )

        assert loaded is None

    def test_loaded_results_have_structured_response(self, storage, sample_results):
        """Test that loaded results have structured_response field."""
        # Save first
        storage.save_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        # Load
        loaded = storage.load_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
        )

        for result in loaded["results"]:
            assert "structured_response" in result
            structured = result["structured_response"]
            assert "overall_score" in structured
            assert "criteria_scores" in structured
            assert "criteria_feedback" in structured
            assert "suggestions" in structured
            assert "strengths" in structured

    def test_loaded_structured_response_has_all_criteria(self, storage, sample_results):
        """Test that loaded structured response has all 16 criteria."""
        # Save first
        storage.save_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        # Load
        loaded = storage.load_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
        )

        criteria = [
            "separation_of_concerns",
            "documentation",
            "logic_clarity",
            "understandability",
            "efficiency",
            "error_handling",
            "testability",
            "reusability",
            "code_consistency",
            "dependency_management",
            "security_awareness",
            "side_effects",
            "scalability",
            "resource_management",
            "encapsulation",
            "readability",
        ]

        for result in loaded["results"]:
            structured = result["structured_response"]
            for criterion in criteria:
                assert criterion in structured["criteria_scores"]
                assert criterion in structured["criteria_feedback"]


class TestOutputExistence:
    """Tests for checking output existence."""

    def test_output_exists_returns_true(self, storage, sample_results):
        """Test that output_exists returns True for existing output."""
        # Save
        storage.save_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        # Check
        exists = storage.output_exists(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
        )

        assert exists is True

    def test_output_exists_returns_false(self, storage):
        """Test that output_exists returns False for non-existing output."""
        exists = storage.output_exists(
            root_directory="/nonexistent/path",
            file_path=None,
            analysis_mode="entire_project",
        )

        assert exists is False


class TestDeleteAnalysis:
    """Tests for deleting analysis output."""

    def test_delete_existing_output(self, storage, sample_results):
        """Test deleting existing output."""
        # Save
        storage.save_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        # Delete
        deleted = storage.delete_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
        )

        assert deleted is True

    def test_delete_nonexistent_output(self, storage):
        """Test deleting non-existent output returns False."""
        deleted = storage.delete_analysis_output(
            root_directory="/nonexistent/path",
            file_path=None,
            analysis_mode="entire_project",
        )

        assert deleted is False

    def test_deleted_output_cannot_be_loaded(self, storage, sample_results):
        """Test that deleted output cannot be loaded."""
        # Save
        storage.save_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        # Delete
        storage.delete_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
        )

        # Try to load
        loaded = storage.load_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
        )

        assert loaded is None


class TestGetAllCachedAnalyses:
    """Tests for getting all cached analyses."""

    def test_get_all_cached_analyses(self, storage, sample_results):
        """Test getting all cached analyses."""
        # Save multiple analyses
        storage.save_analysis_output(
            root_directory="/test/path1",
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        storage.save_analysis_output(
            root_directory="/test/path2",
            file_path="/test/path2/file.py",
            analysis_mode="single_file",
            analysis_results=sample_results,
        )

        # Get all
        all_cached = storage.get_all_cached_analyses()

        assert len(all_cached) == 2

    def test_cached_analysis_info(self, storage, sample_results):
        """Test that cached analysis info includes key fields."""
        # Save
        storage.save_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=sample_results,
        )

        # Get all
        all_cached = storage.get_all_cached_analyses()

        for filename, info in all_cached.items():
            assert "timestamp" in info
            assert "analysis_mode" in info
            assert "root_directory" in info
            assert "result_count" in info

    def test_empty_cache_returns_empty_dict(self, storage):
        """Test that empty cache returns empty dictionary."""
        all_cached = storage.get_all_cached_analyses()

        assert all_cached == {}


class TestFileNaming:
    """Tests for cache file naming."""

    def test_single_file_naming(self, storage):
        """Test naming for single file analysis."""
        filename = storage.get_analysis_filename(
            root_directory="/test/path",
            file_path="/test/path/subdir/myfile.py",
            analysis_mode="single_file",
        )

        assert "single_file" in filename
        assert "myfile" in filename
        assert filename.endswith(".json")

    def test_entire_project_naming(self, storage):
        """Test naming for entire project analysis."""
        filename = storage.get_analysis_filename(
            root_directory="/test/memori",
            file_path=None,
            analysis_mode="entire_project",
        )

        assert "entire_project" in filename
        assert "memori" in filename
        assert filename.endswith(".json")

    def test_get_analysis_output_path(self, storage):
        """Test getting full output path."""
        path = storage.get_analysis_output_path(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
        )

        assert storage.output_dir in path
        assert ".json" in path


class TestBackwardCompatibility:
    """Tests for backward compatibility with old format."""

    def test_load_old_format_results(self, storage):
        """Test loading results in old format (without structured_response)."""
        # Create old format result
        old_format_results = [
            {
                "method_name": "old_method",
                "api_response": "This is free-form text response",
            }
        ]

        output_path = storage.save_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
            analysis_results=old_format_results,
        )

        # Load
        loaded = storage.load_analysis_output(
            root_directory="/test/path",
            file_path=None,
            analysis_mode="entire_project",
        )

        # Should still load without errors
        assert loaded is not None
        assert len(loaded["results"]) == 1
        assert loaded["results"][0]["method_name"] == "old_method"


class TestConcurrentAccess:
    """Tests for concurrent access scenarios."""

    def test_multiple_saves_to_different_paths(self, storage, sample_results):
        """Test saving to different cache paths."""
        paths = []

        for i in range(3):
            path = storage.save_analysis_output(
                root_directory=f"/test/path{i}",
                file_path=None,
                analysis_mode="entire_project",
                analysis_results=sample_results,
            )
            paths.append(path)

        # All should exist
        for path in paths:
            assert os.path.exists(path)

        # All should be different
        assert len(set(paths)) == 3
