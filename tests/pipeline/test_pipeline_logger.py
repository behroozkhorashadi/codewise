"""Tests for source/pipeline/pipeline_logger.py"""

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from source.pipeline.pipeline_logger import PipelineLogger, get_logger


@pytest.fixture
def logger_instance(tmp_path):
    return PipelineLogger(log_dir=str(tmp_path / "logs"), enable_file_logging=True)


@pytest.fixture
def logger_no_file(tmp_path):
    return PipelineLogger(log_dir=str(tmp_path / "logs"), enable_file_logging=False)


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestPipelineLoggerInit:
    def test_creates_log_dir(self, tmp_path):
        log_dir = tmp_path / "new_logs"
        assert not log_dir.exists()
        PipelineLogger(log_dir=str(log_dir), enable_file_logging=False)
        assert log_dir.exists()

    def test_no_file_logging_skips_file_handler(self, tmp_path):
        pl = PipelineLogger(log_dir=str(tmp_path), enable_file_logging=False)
        file_handlers = [h for h in pl.logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(file_handlers) == 0

    def test_file_logging_creates_log_file_on_use(self, logger_instance):
        logger_instance.log_sample_processing("s1", "started", "claude", "critique")
        assert logger_instance.api_call_log_file.parent.exists()

    def test_debug_level(self, tmp_path):
        pl = PipelineLogger(log_dir=str(tmp_path), log_level="DEBUG", enable_file_logging=False)
        assert pl.logger.level == logging.DEBUG


import logging.handlers

# ---------------------------------------------------------------------------
# log_api_call
# ---------------------------------------------------------------------------


class TestLogApiCall:
    def test_writes_jsonl_entry(self, logger_instance):
        logger_instance.log_api_call(
            model_name="claude",
            prompt_type="critique",
            sample_id="sample_001",
            input_tokens=100,
            output_tokens=200,
            cost_usd=0.001,
        )
        log_file = logger_instance.api_call_log_file
        assert log_file.exists()
        line = json.loads(log_file.read_text().strip())
        assert line["model"] == "claude"
        assert line["prompt_type"] == "critique"
        assert line["sample_id"] == "sample_001"
        assert line["total_tokens"] == 300
        assert line["status"] == "success"
        assert line["cached"] is False

    def test_cached_flag(self, logger_instance):
        logger_instance.log_api_call("gpt4", "improve", "s1", 50, 50, 0.0, cached=True)
        line = json.loads(logger_instance.api_call_log_file.read_text().strip())
        assert line["cached"] is True

    def test_error_status(self, logger_instance):
        logger_instance.log_api_call("claude", "critique", "s1", 0, 0, 0.0, status="error", error_message="timeout")
        line = json.loads(logger_instance.api_call_log_file.read_text().strip())
        assert line["status"] == "error"
        assert line["error_message"] == "timeout"

    def test_multiple_entries_appended(self, logger_instance):
        for i in range(3):
            logger_instance.log_api_call("m", "t", f"s{i}", 10, 10, 0.0)
        lines = logger_instance.api_call_log_file.read_text().strip().split("\n")
        assert len(lines) == 3


# ---------------------------------------------------------------------------
# log_sample_processing / log_error
# ---------------------------------------------------------------------------


class TestLogSampleProcessing:
    def test_does_not_raise(self, logger_instance):
        logger_instance.log_sample_processing("s1", "started", "claude", "critique", "msg")

    def test_no_file_logging_does_not_raise(self, logger_no_file):
        logger_no_file.log_sample_processing("s1", "completed", "gpt4", "improve")


class TestLogError:
    def test_does_not_raise(self, logger_instance):
        logger_instance.log_error("s1", ValueError("something went wrong"))


# ---------------------------------------------------------------------------
# get_api_call_summary
# ---------------------------------------------------------------------------


class TestGetApiCallSummary:
    def test_empty_when_no_log_file(self, logger_instance):
        summary = logger_instance.get_api_call_summary()
        assert summary["total_calls"] == 0
        assert summary["successful_calls"] == 0
        assert summary["total_cost_usd"] == 0.0

    def test_counts_calls_correctly(self, logger_instance):
        logger_instance.log_api_call("claude", "critique", "s1", 100, 50, 0.005)
        logger_instance.log_api_call("gpt4", "improve", "s2", 80, 60, 0.003, status="error")
        logger_instance.log_api_call("claude", "critique", "s3", 90, 40, 0.004, cached=True)

        summary = logger_instance.get_api_call_summary()
        assert summary["total_calls"] == 3
        assert summary["successful_calls"] == 2
        assert summary["failed_calls"] == 1
        assert summary["cached_calls"] == 1
        assert summary["total_cost_usd"] == pytest.approx(0.012, abs=1e-6)

    def test_groups_by_model(self, logger_instance):
        logger_instance.log_api_call("claude", "critique", "s1", 100, 50, 0.005)
        logger_instance.log_api_call("claude", "improve", "s2", 80, 60, 0.003)
        logger_instance.log_api_call("gpt4", "critique", "s3", 70, 30, 0.002)

        summary = logger_instance.get_api_call_summary()
        assert summary["by_model"]["claude"]["calls"] == 2
        assert summary["by_model"]["gpt4"]["calls"] == 1

    def test_groups_by_prompt_type(self, logger_instance):
        logger_instance.log_api_call("m", "critique", "s1", 10, 10, 0.0)
        logger_instance.log_api_call("m", "critique", "s2", 10, 10, 0.0)
        logger_instance.log_api_call("m", "improve", "s3", 10, 10, 0.0)

        summary = logger_instance.get_api_call_summary()
        assert summary["by_prompt_type"]["critique"]["calls"] == 2
        assert summary["by_prompt_type"]["improve"]["calls"] == 1

    def test_skips_malformed_jsonl_lines(self, logger_instance):
        logger_instance.api_call_log_file.write_text("not json\n")
        summary = logger_instance.get_api_call_summary()
        assert summary["total_calls"] == 0


# ---------------------------------------------------------------------------
# get_logger
# ---------------------------------------------------------------------------


class TestGetLogger:
    def test_returns_logger_instance(self):
        log = get_logger("test_name")
        assert isinstance(log, logging.Logger)

    def test_default_name(self):
        log = get_logger()
        assert log.name == "codewise_pipeline"


class TestLogApiCallIOError:
    def test_ioerror_on_write_does_not_raise(self, tmp_path):
        pl = PipelineLogger(log_dir=str(tmp_path), enable_file_logging=False)
        with patch("builtins.open", side_effect=IOError("disk full")):
            pl.log_api_call("m", "t", "s1", 10, 10, 0.0)


class TestGetApiCallSummaryIOError:
    def test_ioerror_on_read_returns_empty(self, tmp_path):
        pl = PipelineLogger(log_dir=str(tmp_path), enable_file_logging=False)
        pl.api_call_log_file = tmp_path / "api_calls.jsonl"
        pl.api_call_log_file.write_text("")  # create it
        with patch("builtins.open", side_effect=IOError("disk error")):
            summary = pl.get_api_call_summary()
        assert summary["total_calls"] == 0
