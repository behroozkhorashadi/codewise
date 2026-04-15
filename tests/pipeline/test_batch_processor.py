"""
Tests for source/pipeline/batch_processor.py

Covers:
- load_samples(): metadata.csv path, fallback glob path, error cases
- _load_samples_from_metadata(): full metadata fields, missing file, empty CSV
- initialize_models(): dry_run flag, each model branch, no-models error
- run(): resume filtering, max_samples cap, metadata persistence
"""

import csv
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
import yaml

from source.pipeline.batch_processor import BatchProcessor

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

MINIMAL_CONFIG = {
    "models": {
        "claude": {"enabled": False},
        "gpt4": {"enabled": False},
        "gemma": {"enabled": False},
    },
    "logging": {"log_dir": "logs", "level": "INFO"},
    "pipeline": {"cache_path": "intermediate/cache"},
}


def write_config(tmp_path: Path, config: dict = None) -> Path:
    """Write a YAML config file and return its path."""
    cfg = config if config is not None else MINIMAL_CONFIG
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(cfg))
    return config_file


def make_processor(tmp_path: Path, config: dict = None) -> BatchProcessor:
    """Construct a BatchProcessor wired to tmp directories, no real I/O side-effects."""
    config_file = write_config(tmp_path, config)
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    output_dir = tmp_path / "outputs"

    with (
        patch("source.pipeline.batch_processor.PipelineLogger"),
        patch("source.pipeline.batch_processor.CacheManager"),
        patch("source.pipeline.batch_processor.SampleProcessor"),
        patch.object(BatchProcessor, "_load_pipeline_metadata", return_value={"samples_processed": []}),
    ):
        processor = BatchProcessor(
            config_file=str(config_file),
            dataset_dir=str(dataset_dir),
            output_dir=str(output_dir),
        )
    # Expose real paths for tests that populate them
    processor.dataset_dir = dataset_dir
    return processor


# ---------------------------------------------------------------------------
# BatchProcessor.__init__ / _load_config
# ---------------------------------------------------------------------------


class TestLoadConfig:
    def test_raises_when_config_missing(self, tmp_path):
        with (
            patch("source.pipeline.batch_processor.PipelineLogger"),
            patch("source.pipeline.batch_processor.CacheManager"),
            patch("source.pipeline.batch_processor.SampleProcessor"),
        ):
            with pytest.raises(FileNotFoundError, match="Config file not found"):
                BatchProcessor(
                    config_file=str(tmp_path / "nonexistent.yaml"),
                    dataset_dir=str(tmp_path),
                    output_dir=str(tmp_path / "out"),
                )

    def test_loads_valid_config(self, tmp_path):
        processor = make_processor(tmp_path)
        assert "models" in processor.config


# ---------------------------------------------------------------------------
# load_samples() — metadata.csv branch
# ---------------------------------------------------------------------------


class TestLoadSamplesMetadataCSV:
    def _write_sample_file(self, path: Path, content: str = "def foo(): pass\n") -> None:
        path.write_text(content)

    def test_prefers_metadata_csv_over_glob(self, tmp_path):
        processor = make_processor(tmp_path)
        sample_code = "def bar(): return 1\n"
        sample_file = tmp_path / "sample_a.py"
        self._write_sample_file(sample_file, sample_code)

        # Also place a stray .py file that should NOT be loaded (glob fallback ignored)
        stray = processor.dataset_dir / "stray.py"
        stray.write_text("x = 1\n")

        csv_path = processor.dataset_dir / "metadata.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["sample_id", "file_path", "category"])
            writer.writeheader()
            writer.writerow({"sample_id": "a001", "file_path": str(sample_file), "category": "oss"})

        samples = processor.load_samples()

        assert len(samples) == 1
        assert samples[0]["sample_id"] == "a001"
        assert samples[0]["code"] == sample_code

    def test_carries_optional_metadata_fields(self, tmp_path):
        processor = make_processor(tmp_path)
        sample_file = tmp_path / "s.py"
        sample_file.write_text("pass\n")

        csv_path = processor.dataset_dir / "metadata.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "sample_id",
                    "file_path",
                    "source",
                    "category",
                    "quality_expectation",
                    "description",
                    "complexity",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "sample_id": "s1",
                    "file_path": str(sample_file),
                    "source": "github",
                    "category": "oss",
                    "quality_expectation": "high",
                    "description": "a sample",
                    "complexity": "low",
                }
            )

        samples = processor.load_samples()
        s = samples[0]
        assert s["source"] == "github"
        assert s["category"] == "oss"
        assert s["quality_expectation"] == "high"
        assert s["description"] == "a sample"
        assert s["complexity"] == "low"

    def test_strips_whitespace_from_fields(self, tmp_path):
        processor = make_processor(tmp_path)
        sample_file = tmp_path / "s.py"
        sample_file.write_text("pass\n")

        csv_path = processor.dataset_dir / "metadata.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["sample_id", "file_path"])
            writer.writeheader()
            writer.writerow({"sample_id": "  s1  ", "file_path": f"  {sample_file}  "})

        samples = processor.load_samples()
        assert samples[0]["sample_id"] == "s1"

    def test_raises_when_sample_file_not_found(self, tmp_path):
        processor = make_processor(tmp_path)
        csv_path = processor.dataset_dir / "metadata.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["sample_id", "file_path"])
            writer.writeheader()
            writer.writerow({"sample_id": "x", "file_path": "/does/not/exist.py"})

        with pytest.raises(FileNotFoundError, match="Sample file not found"):
            processor.load_samples()

    def test_raises_when_csv_has_no_rows(self, tmp_path):
        processor = make_processor(tmp_path)
        csv_path = processor.dataset_dir / "metadata.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["sample_id", "file_path"])
            writer.writeheader()
            # No data rows

        with pytest.raises(FileNotFoundError, match="No samples found"):
            processor.load_samples()

    def test_relative_file_path_resolved_from_repo_root(self, tmp_path):
        """Relative paths in CSV should resolve relative to repo root (project directory)."""
        processor = make_processor(tmp_path)

        # Place a real file and compute its path relative to the repo root
        import source.pipeline.batch_processor as bp_module

        repo_root = Path(bp_module.__file__).parent.parent.parent
        sample_file = repo_root / "test_temp_sample.py"
        sample_file.write_text("def hello(): pass\n")

        try:
            relative_path = sample_file.relative_to(repo_root)
            csv_path = processor.dataset_dir / "metadata.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["sample_id", "file_path"])
                writer.writeheader()
                writer.writerow({"sample_id": "rel1", "file_path": str(relative_path)})

            samples = processor.load_samples()
            assert samples[0]["sample_id"] == "rel1"
            assert "hello" in samples[0]["code"]
        finally:
            sample_file.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# load_samples() — glob fallback branch
# ---------------------------------------------------------------------------


class TestLoadSamplesFallbackGlob:
    def test_loads_py_files_alphabetically(self, tmp_path):
        processor = make_processor(tmp_path)
        (processor.dataset_dir / "b.py").write_text("b = 2\n")
        (processor.dataset_dir / "a.py").write_text("a = 1\n")

        samples = processor.load_samples()
        assert [s["sample_id"] for s in samples] == ["a", "b"]
        assert samples[0]["code"] == "a = 1\n"

    def test_skips_test_files(self, tmp_path):
        processor = make_processor(tmp_path)
        (processor.dataset_dir / "sample.py").write_text("x = 1\n")
        (processor.dataset_dir / "test_sample.py").write_text("# test\n")

        samples = processor.load_samples()
        assert len(samples) == 1
        assert samples[0]["sample_id"] == "sample"

    def test_raises_when_no_py_files(self, tmp_path):
        processor = make_processor(tmp_path)
        # dataset_dir exists but has no .py files
        with pytest.raises(FileNotFoundError, match="No sample files found"):
            processor.load_samples()

    def test_raises_when_only_test_files(self, tmp_path):
        processor = make_processor(tmp_path)
        (processor.dataset_dir / "test_only.py").write_text("# test\n")

        with pytest.raises(FileNotFoundError, match="No sample files found"):
            processor.load_samples()


# ---------------------------------------------------------------------------
# initialize_models()
# ---------------------------------------------------------------------------


class TestInitializeModels:
    def _config_with_models(self, claude=False, gpt4=False, gemma=False) -> dict:
        return {
            "models": {
                "claude": {"enabled": claude, "model_name": "claude-3-5-sonnet-20241022"},
                "gpt4": {"enabled": gpt4, "model_name": "gpt-4o"},
                "gemma": {"enabled": gemma, "model_name": "gemma:latest", "base_url": "http://localhost:11434"},
            },
            "logging": {"log_dir": "logs", "level": "INFO"},
            "pipeline": {"cache_path": "intermediate/cache"},
        }

    def test_dry_run_skips_api_key_lookup_for_claude(self, tmp_path):
        processor = make_processor(tmp_path, self._config_with_models(claude=True))
        with patch("source.pipeline.batch_processor.ClaudeReviewer") as mock_claude:
            mock_claude.return_value = MagicMock()
            models = processor.initialize_models(dry_run=True)

        _, kwargs = mock_claude.call_args
        assert kwargs["api_key"] == "dry-run"
        assert any(name == "claude" for _, name in models)

    def test_dry_run_skips_api_key_lookup_for_gpt4(self, tmp_path):
        processor = make_processor(tmp_path, self._config_with_models(gpt4=True))
        with patch("source.pipeline.batch_processor.GPT4Reviewer") as mock_gpt4:
            mock_gpt4.return_value = MagicMock()
            models = processor.initialize_models(dry_run=True)

        _, kwargs = mock_gpt4.call_args
        assert kwargs["api_key"] == "dry-run"
        assert any(name == "gpt4" for _, name in models)

    def test_non_dry_run_calls_get_api_key_for_claude(self, tmp_path):
        processor = make_processor(tmp_path, self._config_with_models(claude=True))
        with (
            patch.object(processor, "_get_api_key", return_value="real-key") as mock_get,
            patch("source.pipeline.batch_processor.ClaudeReviewer") as mock_claude,
        ):
            mock_claude.return_value = MagicMock()
            processor.initialize_models(dry_run=False)

        mock_get.assert_called_once_with("ANTHROPIC_API_KEY")

    def test_non_dry_run_calls_get_api_key_for_gpt4(self, tmp_path):
        processor = make_processor(tmp_path, self._config_with_models(gpt4=True))
        with (
            patch.object(processor, "_get_api_key", return_value="real-key") as mock_get,
            patch("source.pipeline.batch_processor.GPT4Reviewer") as mock_gpt4,
        ):
            mock_gpt4.return_value = MagicMock()
            processor.initialize_models(dry_run=False)

        mock_get.assert_called_once_with("OPENAI_API_KEY")

    def test_gemma_does_not_require_api_key(self, tmp_path):
        processor = make_processor(tmp_path, self._config_with_models(gemma=True))
        with patch("source.pipeline.batch_processor.GemmaReviewer") as mock_gemma:
            mock_gemma.return_value = MagicMock()
            models = processor.initialize_models(dry_run=False)

        assert any(name == "gemma" for _, name in models)

    def test_raises_when_no_models_enabled(self, tmp_path):
        processor = make_processor(tmp_path, self._config_with_models())
        with pytest.raises(ValueError, match="No models enabled"):
            processor.initialize_models()

    def test_all_three_models_enabled(self, tmp_path):
        processor = make_processor(tmp_path, self._config_with_models(claude=True, gpt4=True, gemma=True))
        with (
            patch("source.pipeline.batch_processor.ClaudeReviewer", return_value=MagicMock()),
            patch("source.pipeline.batch_processor.GPT4Reviewer", return_value=MagicMock()),
            patch("source.pipeline.batch_processor.GemmaReviewer", return_value=MagicMock()),
        ):
            models = processor.initialize_models(dry_run=True)

        names = [name for _, name in models]
        assert "claude" in names
        assert "gpt4" in names
        assert "gemma" in names

    def test_model_name_passed_to_gpt4_reviewer(self, tmp_path):
        processor = make_processor(tmp_path, self._config_with_models(gpt4=True))
        with patch("source.pipeline.batch_processor.GPT4Reviewer") as mock_gpt4:
            mock_gpt4.return_value = MagicMock()
            processor.initialize_models(dry_run=True)

        _, kwargs = mock_gpt4.call_args
        assert kwargs["model_name"] == "gpt-4o"

    def test_model_name_passed_to_claude_reviewer(self, tmp_path):
        processor = make_processor(tmp_path, self._config_with_models(claude=True))
        with patch("source.pipeline.batch_processor.ClaudeReviewer") as mock_claude:
            mock_claude.return_value = MagicMock()
            processor.initialize_models(dry_run=True)

        _, kwargs = mock_claude.call_args
        assert kwargs["model_name"] == "claude-3-5-sonnet-20241022"


# ---------------------------------------------------------------------------
# run() — resume, max_samples, metadata persistence
# ---------------------------------------------------------------------------


class TestRun:
    def _setup_run(self, tmp_path, samples, results, already_processed=None):
        """Return a processor ready for run() with mocked internals."""
        processor = make_processor(tmp_path)
        processor.pipeline_metadata = {"samples_processed": already_processed or []}

        processor.load_samples = MagicMock(return_value=samples)
        processor.initialize_models = MagicMock(return_value=[(MagicMock(), "gpt4")])
        processor.sample_processor = MagicMock()
        processor.sample_processor.process_multiple_samples.return_value = results
        processor.cache_manager = MagicMock()
        processor.cache_manager.get_cache_stats.return_value = {"total_files": 0, "total_size_mb": 0.0}
        processor.logger = MagicMock()
        processor.logger.get_api_call_summary.return_value = {
            "total_calls": 0,
            "successful_calls": 0,
            "cached_calls": 0,
            "total_cost_usd": 0.0,
        }
        processor._save_pipeline_metadata = MagicMock()
        return processor

    def test_resume_filters_already_processed_samples(self, tmp_path):
        samples = [{"sample_id": "a", "code": "x"}, {"sample_id": "b", "code": "y"}]
        results = [{"status": "completed", "sample_id": "b"}]
        processor = self._setup_run(tmp_path, samples, results, already_processed=["a"])

        processor.run(resume=True, dry_run=True)

        passed_samples = processor.sample_processor.process_multiple_samples.call_args[1]["samples"]
        assert len(passed_samples) == 1
        assert passed_samples[0]["sample_id"] == "b"

    def test_no_resume_passes_all_samples(self, tmp_path):
        samples = [{"sample_id": "a", "code": "x"}, {"sample_id": "b", "code": "y"}]
        results = [
            {"status": "completed", "sample_id": "a"},
            {"status": "completed", "sample_id": "b"},
        ]
        processor = self._setup_run(tmp_path, samples, results, already_processed=["a"])

        processor.run(resume=False, dry_run=True)

        passed_samples = processor.sample_processor.process_multiple_samples.call_args[1]["samples"]
        assert len(passed_samples) == 2

    def test_max_samples_cap(self, tmp_path):
        samples = [{"sample_id": str(i), "code": "x"} for i in range(5)]
        results = [{"status": "completed", "sample_id": "0"}]
        processor = self._setup_run(tmp_path, samples, results)

        processor.run(max_samples=1, dry_run=True)

        passed_samples = processor.sample_processor.process_multiple_samples.call_args[1]["samples"]
        assert len(passed_samples) == 1

    def test_completed_samples_added_to_metadata(self, tmp_path):
        samples = [{"sample_id": "new1", "code": "x"}]
        results = [{"status": "completed", "sample_id": "new1"}]
        processor = self._setup_run(tmp_path, samples, results)

        processor.run(dry_run=True)

        assert "new1" in processor.pipeline_metadata["samples_processed"]
        processor._save_pipeline_metadata.assert_called_once()

    def test_failed_samples_not_added_to_metadata(self, tmp_path):
        samples = [{"sample_id": "bad1", "code": "x"}]
        results = [{"status": "failed", "sample_id": "bad1", "model_name": "gpt4"}]
        processor = self._setup_run(tmp_path, samples, results)

        processor.run(dry_run=True)

        assert "bad1" not in processor.pipeline_metadata["samples_processed"]

    def test_duplicate_completed_sample_not_added_twice(self, tmp_path):
        samples = [{"sample_id": "dup", "code": "x"}]
        results = [{"status": "completed", "sample_id": "dup"}]
        processor = self._setup_run(tmp_path, samples, results, already_processed=["dup"])

        processor.run(resume=False, dry_run=True)

        assert processor.pipeline_metadata["samples_processed"].count("dup") == 1

    def test_initialize_models_called_with_dry_run_flag(self, tmp_path):
        samples = [{"sample_id": "x", "code": "y"}]
        results = [{"status": "completed", "sample_id": "x"}]
        processor = self._setup_run(tmp_path, samples, results)

        processor.run(dry_run=True)
        processor.initialize_models.assert_called_once_with(dry_run=True)

        processor.initialize_models.reset_mock()
        processor.run(dry_run=False)
        processor.initialize_models.assert_called_once_with(dry_run=False)
