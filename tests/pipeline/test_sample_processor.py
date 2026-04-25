"""Tests for source/pipeline/sample_processor.py"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from source.pipeline.sample_processor import SampleProcessor

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def processor(tmp_path, mock_logger):
    return SampleProcessor(output_dir=str(tmp_path / "outputs"), logger_instance=mock_logger)


def _make_model(critique=None, improve=None, recritique=None):
    model = MagicMock()
    model.critique.return_value = critique or {"feedback": "looks good"}
    model.improve.return_value = improve or {"refactored_code": "def foo(): return 2"}
    model.recritique.return_value = recritique or {"feedback": "improved"}
    return model


SAMPLE_CODE = "def foo(): return 1"


# ---------------------------------------------------------------------------
# process_sample – happy path
# ---------------------------------------------------------------------------


class TestProcessSampleSuccess:
    def test_returns_completed_status(self, processor):
        result = processor.process_sample("s1", SAMPLE_CODE, _make_model(), "claude")
        assert result["status"] == "completed"

    def test_result_has_all_phases(self, processor):
        result = processor.process_sample("s1", SAMPLE_CODE, _make_model(), "claude")
        assert "critique" in result["phases"]
        assert "improve" in result["phases"]
        assert "recritique" in result["phases"]

    def test_output_files_are_created(self, processor, tmp_path):
        processor.process_sample("s1", SAMPLE_CODE, _make_model(), "claude")
        outputs = list((tmp_path / "outputs" / "claude").glob("*.json"))
        assert len(outputs) >= 4  # critique, improved, recritique, summary

    def test_sample_id_in_result(self, processor):
        result = processor.process_sample("my_sample", SAMPLE_CODE, _make_model(), "gpt4")
        assert result["sample_id"] == "my_sample"

    def test_model_name_in_result(self, processor):
        result = processor.process_sample("s1", SAMPLE_CODE, _make_model(), "gpt4")
        assert result["model_name"] == "gpt4"

    def test_uses_refactored_code_in_recritique(self, processor):
        model = _make_model(improve={"refactored_code": "def foo(): return 99"})
        processor.process_sample("s1", SAMPLE_CODE, model, "claude")
        call_args = model.recritique.call_args
        assert "def foo(): return 99" in call_args.args or "def foo(): return 99" in str(call_args)

    def test_fallback_to_original_code_when_no_refactored_code(self, processor):
        model = _make_model(improve={"no_refactored_code": True})
        result = processor.process_sample("s1", SAMPLE_CODE, model, "claude")
        assert result["status"] == "completed"


# ---------------------------------------------------------------------------
# process_sample – dry_run
# ---------------------------------------------------------------------------


class TestProcessSampleDryRun:
    def test_dry_run_skips_api_calls(self, processor):
        model = _make_model()
        result = processor.process_sample("s1", SAMPLE_CODE, model, "claude", dry_run=True)
        model.critique.assert_not_called()
        model.improve.assert_not_called()
        model.recritique.assert_not_called()

    def test_dry_run_returns_completed(self, processor):
        result = processor.process_sample("s1", SAMPLE_CODE, _make_model(), "claude", dry_run=True)
        assert result["status"] == "completed"

    def test_dry_run_phases_marked_skipped(self, processor):
        result = processor.process_sample("s1", SAMPLE_CODE, _make_model(), "claude", dry_run=True)
        for phase in ["critique", "improve", "recritique"]:
            assert result["phases"][phase]["result"]["status"] == "skipped"


# ---------------------------------------------------------------------------
# process_sample – error handling
# ---------------------------------------------------------------------------


class TestProcessSampleErrors:
    def test_critique_error_returns_failed(self, processor):
        model = _make_model()
        model.critique.side_effect = RuntimeError("API down")
        result = processor.process_sample("s1", SAMPLE_CODE, model, "claude")
        assert result["status"] == "failed"
        assert result["errors"][0]["phase"] == "critique"

    def test_improve_error_returns_failed(self, processor):
        model = _make_model()
        model.improve.side_effect = RuntimeError("improve failed")
        result = processor.process_sample("s1", SAMPLE_CODE, model, "claude")
        assert result["status"] == "failed"
        assert result["errors"][0]["phase"] == "improve"

    def test_recritique_error_returns_failed(self, processor):
        model = _make_model()
        model.recritique.side_effect = RuntimeError("recritique failed")
        result = processor.process_sample("s1", SAMPLE_CODE, model, "claude")
        assert result["status"] == "failed"
        assert result["errors"][0]["phase"] == "recritique"

    def test_error_message_captured(self, processor):
        model = _make_model()
        model.critique.side_effect = ValueError("bad input")
        result = processor.process_sample("s1", SAMPLE_CODE, model, "claude")
        assert "bad input" in result["errors"][0]["error"]


# ---------------------------------------------------------------------------
# process_multiple_samples
# ---------------------------------------------------------------------------


class TestProcessMultipleSamples:
    def _make_samples(self, n):
        return [{"sample_id": f"s{i}", "code": f"def f{i}(): pass"} for i in range(n)]

    def test_processes_all_samples_all_models(self, processor):
        samples = self._make_samples(3)
        models = [(_make_model(), "claude"), (_make_model(), "gpt4")]
        results = processor.process_multiple_samples(samples, models, dry_run=True)
        assert len(results) == 6  # 3 samples × 2 models

    def test_max_samples_cap(self, processor):
        samples = self._make_samples(5)
        results = processor.process_multiple_samples(samples, [(_make_model(), "claude")], max_samples=2, dry_run=True)
        assert len(results) == 2

    def test_continues_on_model_exception(self, processor):
        samples = self._make_samples(2)
        bad_model = MagicMock()
        bad_model.critique.side_effect = Exception("crash")
        results = processor.process_multiple_samples(samples, [(bad_model, "broken")], dry_run=False)
        # Should record failed results rather than crashing
        assert len(results) == 2
        for r in results:
            assert r["status"] == "failed"

    def test_empty_samples_returns_empty(self, processor):
        results = processor.process_multiple_samples([], [(_make_model(), "claude")])
        assert results == []

    def test_result_contains_sample_ids(self, processor):
        samples = [{"sample_id": "abc", "code": "x = 1"}]
        results = processor.process_multiple_samples(samples, [(_make_model(), "claude")], dry_run=True)
        assert results[0]["sample_id"] == "abc"
