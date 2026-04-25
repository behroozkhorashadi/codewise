"""Tests for source/experiment/analysis.py"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from source.experiment.analysis import (
    CRITERIA,
    MODELS,
    _get_scores,
    inter_model_agreement,
    load_results,
    print_report,
    score_delta,
    score_variance,
    summary,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_result(gpt_overall=8, claude_overall=7, gpt_criteria=None, claude_criteria=None):
    """Build a minimal experiment result dict."""
    base_criteria = {c: 7 for c in CRITERIA}
    gpt_c = {**base_criteria, **(gpt_criteria or {})}
    claude_c = {**base_criteria, **(claude_criteria or {})}
    return {
        "condition_a": {
            "gpt-4o": {"overall_score": gpt_overall, "criteria_scores": gpt_c},
            "claude": {"overall_score": claude_overall, "criteria_scores": claude_c},
        },
        "condition_b": {
            "gpt-4o": {"overall_score": gpt_overall + 1, "criteria_scores": {k: v + 1 for k, v in gpt_c.items()}},
            "claude": {"overall_score": claude_overall - 1, "criteria_scores": {k: v - 1 for k, v in claude_c.items()}},
        },
    }


SAMPLE_RESULTS = [make_result(8, 7), make_result(6, 5)]


# ---------------------------------------------------------------------------
# _get_scores
# ---------------------------------------------------------------------------


class TestGetScores:
    def test_returns_criteria_and_overall(self):
        condition = {"gpt-4o": {"overall_score": 8, "criteria_scores": {"documentation": 7}}}
        scores = _get_scores(condition, "gpt-4o")
        assert scores["documentation"] == 7
        assert scores["overall"] == 8

    def test_returns_empty_on_error_key(self):
        condition = {"gpt-4o": {"error": "timeout"}}
        assert _get_scores(condition, "gpt-4o") == {}

    def test_returns_empty_on_missing_model(self):
        assert _get_scores({}, "gpt-4o") == {}

    def test_no_overall_score(self):
        condition = {"claude": {"criteria_scores": {"documentation": 5}}}
        scores = _get_scores(condition, "claude")
        assert scores == {"documentation": 5}
        assert "overall" not in scores


# ---------------------------------------------------------------------------
# score_delta
# ---------------------------------------------------------------------------


class TestScoreDelta:
    def test_positive_delta_for_gpt(self):
        results = [make_result(gpt_overall=7, claude_overall=8)]
        deltas = score_delta(results)
        # condition_b gpt overall = 8, condition_a = 7 → delta = +1
        assert deltas["gpt-4o"]["overall"] == 1.0

    def test_negative_delta_for_claude(self):
        results = [make_result(gpt_overall=7, claude_overall=8)]
        deltas = score_delta(results)
        # condition_b claude overall = 7, condition_a = 8 → delta = -1
        assert deltas["claude"]["overall"] == -1.0

    def test_mean_over_multiple_results(self):
        results = [make_result(gpt_overall=6), make_result(gpt_overall=8)]
        deltas = score_delta(results)
        assert deltas["gpt-4o"]["overall"] == 1.0

    def test_skips_result_with_error(self):
        r = make_result()
        r["condition_a"]["gpt-4o"] = {"error": "failed"}
        deltas = score_delta([r])
        assert deltas["gpt-4o"]["overall"] is None

    def test_empty_results(self):
        deltas = score_delta([])
        for model in MODELS:
            assert deltas[model]["overall"] is None


# ---------------------------------------------------------------------------
# inter_model_agreement
# ---------------------------------------------------------------------------


class TestInterModelAgreement:
    def test_perfect_agreement_returns_one(self):
        # Both models give identical scores → r = 1
        results = []
        for v in range(1, 6):
            r = make_result(gpt_overall=v, claude_overall=v)
            results.append(r)
        agreement = inter_model_agreement(results)
        assert agreement["condition_a"]["overall"] == pytest.approx(1.0, abs=0.01)

    def test_returns_none_for_insufficient_data(self):
        agreement = inter_model_agreement([make_result()])
        assert agreement["condition_a"]["overall"] is None

    def test_both_conditions_present(self):
        agreement = inter_model_agreement(SAMPLE_RESULTS)
        assert "condition_a" in agreement
        assert "condition_b" in agreement

    def test_all_criteria_present(self):
        results = [make_result() for _ in range(5)]
        agreement = inter_model_agreement(results)
        for c in CRITERIA + ["overall"]:
            assert c in agreement["condition_a"]

    def test_zero_denominator_returns_none(self):
        # All scores identical → std dev = 0 → pearson denominator = 0
        results = [make_result(gpt_overall=5, claude_overall=5) for _ in range(3)]
        agreement = inter_model_agreement(results)
        # den = 0 → returns None
        assert agreement["condition_a"]["overall"] is None


# ---------------------------------------------------------------------------
# score_variance
# ---------------------------------------------------------------------------


class TestScoreVariance:
    def test_keys_present(self):
        var = score_variance(SAMPLE_RESULTS)
        assert "gpt-4o_a" in var
        assert "gpt-4o_b" in var
        assert "claude_a" in var
        assert "claude_b" in var

    def test_non_negative_variance(self):
        var = score_variance(SAMPLE_RESULTS)
        for val in var.values():
            if val is not None:
                assert val >= 0

    def test_returns_none_when_no_data(self):
        var = score_variance([])
        for val in var.values():
            assert val is None

    def test_uniform_scores_have_zero_variance(self):
        # All criteria scores equal → variance = 0
        r = make_result()
        for cond_key in ["condition_a", "condition_b"]:
            for model in MODELS:
                r[cond_key][model]["criteria_scores"] = {c: 5 for c in CRITERIA}
        var = score_variance([r])
        assert var["gpt-4o_a"] == 0.0


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------


class TestSummary:
    def test_summary_structure(self):
        s = summary(SAMPLE_RESULTS)
        assert s["total_methods"] == 2
        assert "score_delta" in s
        assert "inter_model_agreement" in s
        assert "score_variance" in s

    def test_empty_results(self):
        s = summary([])
        assert s["total_methods"] == 0


# ---------------------------------------------------------------------------
# load_results
# ---------------------------------------------------------------------------


class TestLoadResults:
    def test_loads_valid_json_list(self, tmp_path):
        data = [make_result(), make_result()]
        (tmp_path / "results.json").write_text(json.dumps(data))
        results = load_results(str(tmp_path))
        assert len(results) == 2

    def test_skips_progress_files(self, tmp_path):
        data = [make_result()]
        (tmp_path / "repo_progress.json").write_text(json.dumps(data))
        results = load_results(str(tmp_path))
        assert results == []

    def test_skips_non_condition_dicts(self, tmp_path):
        data = [{"no_condition_a": True}, make_result()]
        (tmp_path / "results.json").write_text(json.dumps(data))
        results = load_results(str(tmp_path))
        assert len(results) == 1

    def test_handles_non_list_json(self, tmp_path):
        (tmp_path / "results.json").write_text(json.dumps({"key": "value"}))
        results = load_results(str(tmp_path))
        assert results == []

    def test_empty_directory(self, tmp_path):
        assert load_results(str(tmp_path)) == []


# ---------------------------------------------------------------------------
# print_report
# ---------------------------------------------------------------------------


class TestPrintReport:
    def test_prints_no_results_for_empty_dir(self, tmp_path, capsys):
        print_report(str(tmp_path))
        assert "No results found" in capsys.readouterr().out

    def test_prints_report_for_valid_results(self, tmp_path, capsys):
        data = [make_result() for _ in range(3)]
        (tmp_path / "results.json").write_text(json.dumps(data))
        print_report(str(tmp_path))
        out = capsys.readouterr().out
        assert "EXPERIMENT ANALYSIS" in out
        assert "Score Delta" in out
        assert "Inter-Model Agreement" in out
        assert "Score Variance" in out
