"""Tests for source/experiment/experiment_runner.py"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from source.experiment.experiment_runner import _evaluate, run_experiment

# ---------------------------------------------------------------------------
# _evaluate
# ---------------------------------------------------------------------------


class TestEvaluate:
    @patch("source.experiment.experiment_runner._call_openai")
    @patch("source.experiment.experiment_runner._call_claude")
    def test_returns_both_model_results(self, mock_claude, mock_gpt):
        mock_gpt.return_value = '{"overall_score": 8}'
        mock_claude.return_value = '{"overall_score": 7}'
        with patch("source.experiment.experiment_runner.parse_json_response", side_effect=lambda r: json.loads(r)):
            result = _evaluate("prompt")
        assert "gpt-4o" in result
        assert "claude" in result

    @patch("source.experiment.experiment_runner._call_openai", side_effect=Exception("API error"))
    @patch("source.experiment.experiment_runner._call_claude")
    def test_records_error_on_api_failure(self, mock_claude, mock_gpt):
        mock_claude.return_value = '{"overall_score": 7}'
        with patch("source.experiment.experiment_runner.parse_json_response", return_value={"overall_score": 7}):
            result = _evaluate("prompt")
        assert "error" in result["gpt-4o"]

    @patch("source.experiment.experiment_runner._call_openai", side_effect=Exception("both fail"))
    @patch("source.experiment.experiment_runner._call_claude", side_effect=Exception("both fail"))
    def test_both_models_fail(self, mock_claude, mock_gpt):
        result = _evaluate("prompt")
        assert "error" in result["gpt-4o"]
        assert "error" in result["claude"]


# ---------------------------------------------------------------------------
# run_experiment
# ---------------------------------------------------------------------------


def _make_mock_method_pointer(name="my_func", file_path="/tmp/fake.py"):
    method_id = MagicMock()
    method_id.method_name = name
    mp = MagicMock()
    mp.method_id = method_id
    mp.function_node = MagicMock()
    mp.file_path = file_path
    return mp


def _make_call_site(file_path="/tmp/other.py"):
    cs = MagicMock()
    cs.function_node = MagicMock()
    cs.file_path = file_path
    return cs


class TestRunExperiment:
    def _default_patches(self):
        method_ptr = _make_mock_method_pointer()
        call_site = _make_call_site()
        usages = {method_ptr: [call_site, call_site]}
        return {
            "usages": usages,
            "method_body": "def my_func(): pass",
            "call_site_body": "def caller(): my_func()",
        }

    @patch("source.experiment.experiment_runner._evaluate")
    @patch("source.experiment.experiment_runner.get_method_body")
    @patch("source.experiment.experiment_runner.collect_method_usages")
    def test_returns_results_list(self, mock_collect, mock_body, mock_eval, tmp_path):
        d = self._default_patches()
        mock_collect.return_value = d["usages"]
        mock_body.return_value = d["method_body"]
        mock_eval.return_value = {"gpt-4o": {"overall_score": 8}, "claude": {"overall_score": 7}}

        results = run_experiment(str(tmp_path), "/fake/file.py", output_dir=str(tmp_path), min_call_sites=1)

        assert len(results) == 1
        assert results[0]["method_name"] == "my_func"
        assert "condition_a" in results[0]
        assert "condition_b" in results[0]

    @patch("source.experiment.experiment_runner._evaluate")
    @patch("source.experiment.experiment_runner.get_method_body")
    @patch("source.experiment.experiment_runner.collect_method_usages")
    def test_skips_methods_below_min_call_sites(self, mock_collect, mock_body, mock_eval, tmp_path):
        method_ptr = _make_mock_method_pointer()
        mock_collect.return_value = {method_ptr: [_make_call_site()]}  # only 1 call site
        mock_body.return_value = "def x(): pass"

        results = run_experiment(str(tmp_path), "/fake/file.py", output_dir=str(tmp_path), min_call_sites=2)

        assert results == []
        mock_eval.assert_not_called()

    @patch("source.experiment.experiment_runner._evaluate")
    @patch("source.experiment.experiment_runner.get_method_body")
    @patch("source.experiment.experiment_runner.collect_method_usages")
    def test_saves_output_file(self, mock_collect, mock_body, mock_eval, tmp_path):
        d = self._default_patches()
        mock_collect.return_value = d["usages"]
        mock_body.return_value = d["method_body"]
        mock_eval.return_value = {}

        run_experiment(str(tmp_path), "/fake/file.py", output_dir=str(tmp_path), min_call_sites=1)

        json_files = list(tmp_path.glob("*.json"))
        assert len(json_files) == 1

    @patch("source.experiment.experiment_runner._evaluate")
    @patch("source.experiment.experiment_runner.get_method_body")
    @patch("source.experiment.experiment_runner.collect_method_usages")
    def test_creates_output_dir_if_missing(self, mock_collect, mock_body, mock_eval, tmp_path):
        output_dir = tmp_path / "new_output"
        assert not output_dir.exists()
        mock_collect.return_value = {}
        mock_body.return_value = ""

        run_experiment(str(tmp_path), "/fake/file.py", output_dir=str(output_dir), min_call_sites=1)

        assert output_dir.exists()

    @patch("source.experiment.experiment_runner._evaluate")
    @patch("source.experiment.experiment_runner.get_method_body")
    @patch("source.experiment.experiment_runner.collect_method_usages")
    def test_result_has_required_fields(self, mock_collect, mock_body, mock_eval, tmp_path):
        d = self._default_patches()
        mock_collect.return_value = d["usages"]
        mock_body.return_value = d["method_body"]
        mock_eval.return_value = {}

        results = run_experiment(str(tmp_path), "/fake/file.py", output_dir=str(tmp_path), min_call_sites=1)

        r = results[0]
        for field in [
            "method_name",
            "file_path",
            "repo_dir",
            "num_call_sites",
            "timestamp",
            "condition_a",
            "condition_b",
        ]:
            assert field in r


class TestCallOpenai:
    @patch("source.experiment.experiment_runner.openai.OpenAI")
    def test_call_openai_returns_content(self, mock_openai_class):
        from source.experiment.experiment_runner import _call_openai

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="response text"))]
        )
        with patch.dict("os.environ", {"OPENAI_API_KEY": "fake"}):
            result = _call_openai("test prompt")
        assert result == "response text"


class TestCallClaude:
    @patch("source.experiment.experiment_runner.anthropic.Anthropic")
    def test_call_claude_returns_content(self, mock_anthropic_class):
        from source.experiment.experiment_runner import _call_claude

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text="claude response")])
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "fake"}):
            result = _call_claude("test prompt")
        assert result == "claude response"
