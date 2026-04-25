"""Tests for source/experiment/batch_experiment.py"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from source.experiment.batch_experiment import get_processed_files, run_batch, save_processed_file


class TestGetProcessedFiles:
    def test_returns_empty_set_when_no_file(self, tmp_path):
        result = get_processed_files(tmp_path / "progress.json")
        assert result == set()

    def test_loads_existing_file(self, tmp_path):
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(json.dumps(["a.py", "b.py"]))
        result = get_processed_files(progress_file)
        assert result == {"a.py", "b.py"}


class TestSaveProcessedFile:
    def test_saves_new_file(self, tmp_path):
        progress_file = tmp_path / "progress.json"
        save_processed_file(progress_file, "foo.py")
        data = json.loads(progress_file.read_text())
        assert "foo.py" in data

    def test_appends_to_existing(self, tmp_path):
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(json.dumps(["existing.py"]))
        save_processed_file(progress_file, "new.py")
        data = json.loads(progress_file.read_text())
        assert "existing.py" in data
        assert "new.py" in data

    def test_no_duplicates_on_double_save(self, tmp_path):
        progress_file = tmp_path / "progress.json"
        save_processed_file(progress_file, "dup.py")
        save_processed_file(progress_file, "dup.py")
        data = json.loads(progress_file.read_text())
        assert data.count("dup.py") == 1


class TestRunBatch:
    def _make_repo(self, tmp_path):
        repo = tmp_path / "myrepo"
        repo.mkdir()
        (repo / "module.py").write_text("def foo(): pass\n")
        (repo / "other.py").write_text("def bar(): pass\n")
        (repo / "test_something.py").write_text("def test_foo(): pass\n")
        return repo

    def test_processes_non_test_py_files(self, tmp_path):
        repo = self._make_repo(tmp_path)
        output_dir = tmp_path / "out"

        with patch("source.experiment.batch_experiment.run_experiment", return_value=[]) as mock_run:
            run_batch(str(repo), str(output_dir), min_call_sites=1)

        called_files = [call.kwargs["target_file"] for call in mock_run.call_args_list]
        file_names = [Path(f).name for f in called_files]
        assert "module.py" in file_names
        assert "other.py" in file_names
        assert "test_something.py" not in file_names

    def test_skips_already_processed_files(self, tmp_path):
        repo = self._make_repo(tmp_path)
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        progress_file = output_dir / "myrepo_progress.json"
        progress_file.write_text(json.dumps([str(repo / "module.py")]))

        with patch("source.experiment.batch_experiment.run_experiment", return_value=[]) as mock_run:
            run_batch(str(repo), str(output_dir), min_call_sites=1)

        called_files = [call.kwargs["target_file"] for call in mock_run.call_args_list]
        assert str(repo / "module.py") not in called_files

    def test_continues_on_run_experiment_error(self, tmp_path):
        repo = self._make_repo(tmp_path)
        output_dir = tmp_path / "out"

        with patch("source.experiment.batch_experiment.run_experiment", side_effect=RuntimeError("boom")):
            run_batch(str(repo), str(output_dir), min_call_sites=1)

    def test_saves_progress_after_each_file(self, tmp_path):
        repo = self._make_repo(tmp_path)
        output_dir = tmp_path / "out"

        with patch("source.experiment.batch_experiment.run_experiment", return_value=[{"method_name": "x"}]):
            run_batch(str(repo), str(output_dir), min_call_sites=1)

        progress_file = output_dir / "myrepo_progress.json"
        assert progress_file.exists()
        processed = json.loads(progress_file.read_text())
        assert len(processed) == 2  # module.py + other.py

    def test_creates_output_dir(self, tmp_path):
        repo = self._make_repo(tmp_path)
        output_dir = tmp_path / "new_output"
        assert not output_dir.exists()

        with patch("source.experiment.batch_experiment.run_experiment", return_value=[]):
            run_batch(str(repo), str(output_dir), min_call_sites=1)

        assert output_dir.exists()
