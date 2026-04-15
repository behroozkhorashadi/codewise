"""
Tests for source/pipeline/model_api.py

Covers:
- GPT4Reviewer default model_name changed to gpt-4o
- ClaudeReviewer / GPT4Reviewer / GemmaReviewer: cache hit/miss paths,
  API success/failure, JSON parsing fallback
- CodeReviewModel._parse_json_response: valid JSON, embedded JSON, unparseable
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from source.pipeline.model_api import ClaudeReviewer, GemmaReviewer, GPT4Reviewer

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_cache_manager(cached_response=None):
    """Return a mock CacheManager. If cached_response is set, .get() returns it."""
    cm = MagicMock()
    cm.get.return_value = cached_response
    return cm


def _fake_prompt_template(self, name):  # noqa: ARG001
    return "Review this code: {code_content}"


def _fake_improve_template(self, name):
    if name == "improve_template":
        return "Improve: {code_content} critique: {critique}"
    if name == "recritique_template":
        return "Recritique original: {original_code} scores: {original_scores} improved: {improved_code}"
    return "Review this code: {code_content}"


# ---------------------------------------------------------------------------
# GPT4Reviewer — default model name
# ---------------------------------------------------------------------------


class TestGPT4ReviewerDefaults:
    def test_default_model_is_gpt4o(self):
        with patch("source.pipeline.model_api.openai.OpenAI"):
            reviewer = GPT4Reviewer(api_key="test-key")
        assert reviewer.model_name == "gpt-4o"

    def test_custom_model_name_respected(self):
        with patch("source.pipeline.model_api.openai.OpenAI"):
            reviewer = GPT4Reviewer(api_key="test-key", model_name="gpt-4-turbo")
        assert reviewer.model_name == "gpt-4-turbo"


# ---------------------------------------------------------------------------
# ClaudeReviewer — default model name
# ---------------------------------------------------------------------------


class TestClaudeReviewerDefaults:
    def test_default_model_is_sonnet(self):
        with patch("source.pipeline.model_api.anthropic.Anthropic"):
            reviewer = ClaudeReviewer(api_key="test-key")
        assert reviewer.model_name == "claude-3-5-sonnet-20241022"


# ---------------------------------------------------------------------------
# CodeReviewModel._parse_json_response
# ---------------------------------------------------------------------------


class TestParseJsonResponse:
    """Tests via GPT4Reviewer (concrete subclass)."""

    def _make_reviewer(self):
        with patch("source.pipeline.model_api.openai.OpenAI"):
            return GPT4Reviewer(api_key="k")

    def test_parses_valid_json(self):
        r = self._make_reviewer()
        result = r._parse_json_response('{"score": 7}')
        assert result == {"score": 7}

    def test_extracts_embedded_json(self):
        r = self._make_reviewer()
        result = r._parse_json_response('Some preamble\n{"score": 5}\nsome suffix')
        assert result["score"] == 5

    def test_returns_error_dict_when_no_json(self):
        r = self._make_reviewer()
        result = r._parse_json_response("This is plain text with no JSON.")
        assert "error" in result
        assert "raw_response" in result

    def test_returns_error_dict_when_json_malformed(self):
        r = self._make_reviewer()
        result = r._parse_json_response("{bad json here}")
        assert "error" in result


# ---------------------------------------------------------------------------
# GPT4Reviewer.critique
# ---------------------------------------------------------------------------


class TestGPT4ReviewerCritique:
    CODE = "def foo(): pass"

    def _make_reviewer(self, cache_manager=None):
        with patch("source.pipeline.model_api.openai.OpenAI"):
            return GPT4Reviewer(api_key="k", cache_manager=cache_manager)

    def test_returns_cached_response_on_hit(self):
        cached = {"response": {"score": 9}}
        reviewer = self._make_reviewer(make_cache_manager(cached_response=cached))
        result = reviewer.critique(self.CODE)
        assert result == {"score": 9}
        reviewer.client.chat.completions.create.assert_not_called()

    def test_calls_api_on_cache_miss(self):
        reviewer = self._make_reviewer(make_cache_manager())
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"score": 7}'
        reviewer.client.chat.completions.create.return_value = mock_response

        with patch.object(reviewer, "_load_prompt_template", return_value="template {code_content}"):
            result = reviewer.critique(self.CODE)

        assert result == {"score": 7}

    def test_stores_result_in_cache(self):
        cm = make_cache_manager()
        reviewer = self._make_reviewer(cm)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"score": 6}'
        reviewer.client.chat.completions.create.return_value = mock_response

        with patch.object(reviewer, "_load_prompt_template", return_value="template {code_content}"):
            reviewer.critique(self.CODE)

        cm.set.assert_called_once()

    def test_returns_error_dict_on_api_exception(self):
        reviewer = self._make_reviewer(make_cache_manager())
        reviewer.client.chat.completions.create.side_effect = RuntimeError("API down")

        with patch.object(reviewer, "_load_prompt_template", return_value="template {code_content}"):
            result = reviewer.critique(self.CODE)

        assert "error" in result

    def test_no_cache_manager_skips_cache_lookup(self):
        reviewer = self._make_reviewer(cache_manager=None)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"score": 5}'
        reviewer.client.chat.completions.create.return_value = mock_response

        with patch.object(reviewer, "_load_prompt_template", return_value="template {code_content}"):
            result = reviewer.critique(self.CODE)

        assert result == {"score": 5}


# ---------------------------------------------------------------------------
# GPT4Reviewer.improve
# ---------------------------------------------------------------------------


class TestGPT4ReviewerImprove:
    CODE = "def foo(): pass"
    CRITIQUE = {"score": 4, "feedback": "too simple"}

    def _make_reviewer(self, cache_manager=None):
        with patch("source.pipeline.model_api.openai.OpenAI"):
            return GPT4Reviewer(api_key="k", cache_manager=cache_manager)

    def test_returns_cached_response_on_hit(self):
        cached = {"response": {"improved_code": "def foo(): return 1"}}
        reviewer = self._make_reviewer(make_cache_manager(cached))
        result = reviewer.improve(self.CODE, self.CRITIQUE)
        assert result == {"improved_code": "def foo(): return 1"}

    def test_calls_api_on_cache_miss(self):
        reviewer = self._make_reviewer(make_cache_manager())
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"improved_code": "..."}'
        reviewer.client.chat.completions.create.return_value = mock_response

        with patch.object(reviewer, "_load_prompt_template", return_value="improve {code_content} {critique}"):
            result = reviewer.improve(self.CODE, self.CRITIQUE)

        assert "improved_code" in result

    def test_returns_error_on_api_exception(self):
        reviewer = self._make_reviewer(make_cache_manager())
        reviewer.client.chat.completions.create.side_effect = Exception("timeout")

        with patch.object(reviewer, "_load_prompt_template", return_value="improve {code_content} {critique}"):
            result = reviewer.improve(self.CODE, self.CRITIQUE)

        assert "error" in result


# ---------------------------------------------------------------------------
# GPT4Reviewer.recritique
# ---------------------------------------------------------------------------


class TestGPT4ReviewerRecritique:
    ORIG = "def foo(): pass"
    IMPROVED = "def foo(): return 1"
    CRITIQUE = {"scores": {"clarity": 5}}

    def _make_reviewer(self, cache_manager=None):
        with patch("source.pipeline.model_api.openai.OpenAI"):
            return GPT4Reviewer(api_key="k", cache_manager=cache_manager)

    def test_returns_cached_response_on_hit(self):
        cached = {"response": {"new_score": 8}}
        reviewer = self._make_reviewer(make_cache_manager(cached))
        result = reviewer.recritique(self.ORIG, self.IMPROVED, self.CRITIQUE)
        assert result == {"new_score": 8}

    def test_calls_api_on_cache_miss(self):
        reviewer = self._make_reviewer(make_cache_manager())
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"new_score": 8}'
        reviewer.client.chat.completions.create.return_value = mock_response

        tmpl = "recritique {original_code} {original_scores} {improved_code}"
        with patch.object(reviewer, "_load_prompt_template", return_value=tmpl):
            result = reviewer.recritique(self.ORIG, self.IMPROVED, self.CRITIQUE)

        assert result["new_score"] == 8

    def test_returns_error_on_api_exception(self):
        reviewer = self._make_reviewer(make_cache_manager())
        reviewer.client.chat.completions.create.side_effect = Exception("network error")

        tmpl = "recritique {original_code} {original_scores} {improved_code}"
        with patch.object(reviewer, "_load_prompt_template", return_value=tmpl):
            result = reviewer.recritique(self.ORIG, self.IMPROVED, self.CRITIQUE)

        assert "error" in result

    def test_caches_result_keyed_on_improved_code(self):
        cm = make_cache_manager()
        reviewer = self._make_reviewer(cm)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"new_score": 9}'
        reviewer.client.chat.completions.create.return_value = mock_response

        tmpl = "recritique {original_code} {original_scores} {improved_code}"
        with patch.object(reviewer, "_load_prompt_template", return_value=tmpl):
            reviewer.recritique(self.ORIG, self.IMPROVED, self.CRITIQUE)

        # cache.set should be called with the improved code as the key
        call_args = cm.set.call_args
        assert call_args[0][1] == self.IMPROVED


# ---------------------------------------------------------------------------
# ClaudeReviewer.critique
# ---------------------------------------------------------------------------


class TestClaudeReviewerCritique:
    CODE = "def bar(): pass"

    def _make_reviewer(self, cache_manager=None):
        with patch("source.pipeline.model_api.anthropic.Anthropic"):
            return ClaudeReviewer(api_key="k", cache_manager=cache_manager)

    def test_returns_cached_response_on_hit(self):
        cached = {"response": {"score": 8}}
        reviewer = self._make_reviewer(make_cache_manager(cached))
        result = reviewer.critique(self.CODE)
        assert result == {"score": 8}

    def test_calls_anthropic_api_on_cache_miss(self):
        reviewer = self._make_reviewer(make_cache_manager())
        mock_message = MagicMock()
        mock_message.content[0].text = '{"score": 7}'
        reviewer.client.messages.create.return_value = mock_message

        with patch.object(reviewer, "_load_prompt_template", return_value="template {code_content}"):
            result = reviewer.critique(self.CODE)

        assert result == {"score": 7}

    def test_returns_error_on_api_exception(self):
        reviewer = self._make_reviewer(make_cache_manager())
        reviewer.client.messages.create.side_effect = Exception("auth error")

        with patch.object(reviewer, "_load_prompt_template", return_value="template {code_content}"):
            result = reviewer.critique(self.CODE)

        assert "error" in result

    def test_stores_in_cache_after_api_call(self):
        cm = make_cache_manager()
        reviewer = self._make_reviewer(cm)
        mock_message = MagicMock()
        mock_message.content[0].text = '{"score": 6}'
        reviewer.client.messages.create.return_value = mock_message

        with patch.object(reviewer, "_load_prompt_template", return_value="template {code_content}"):
            reviewer.critique(self.CODE)

        cm.set.assert_called_once()


# ---------------------------------------------------------------------------
# ClaudeReviewer.improve and .recritique
# ---------------------------------------------------------------------------


class TestClaudeReviewerImproveRecritique:
    CODE = "def bar(): pass"
    CRITIQUE = {"scores": {"clarity": 4}}
    IMPROVED = "def bar(): return 0"

    def _make_reviewer(self, cache_manager=None):
        with patch("source.pipeline.model_api.anthropic.Anthropic"):
            return ClaudeReviewer(api_key="k", cache_manager=cache_manager)

    def test_improve_returns_cached_on_hit(self):
        cached = {"response": {"improved": "code"}}
        reviewer = self._make_reviewer(make_cache_manager(cached))
        result = reviewer.improve(self.CODE, self.CRITIQUE)
        assert result == {"improved": "code"}

    def test_improve_calls_api_on_miss(self):
        reviewer = self._make_reviewer(make_cache_manager())
        mock_message = MagicMock()
        mock_message.content[0].text = '{"improved": "better code"}'
        reviewer.client.messages.create.return_value = mock_message

        with patch.object(reviewer, "_load_prompt_template", return_value="improve {code_content} {critique}"):
            result = reviewer.improve(self.CODE, self.CRITIQUE)

        assert result.get("improved") == "better code"

    def test_improve_returns_error_on_exception(self):
        reviewer = self._make_reviewer(make_cache_manager())
        reviewer.client.messages.create.side_effect = Exception("down")

        with patch.object(reviewer, "_load_prompt_template", return_value="improve {code_content} {critique}"):
            result = reviewer.improve(self.CODE, self.CRITIQUE)

        assert "error" in result

    def test_recritique_returns_cached_on_hit(self):
        cached = {"response": {"new_score": 9}}
        reviewer = self._make_reviewer(make_cache_manager(cached))
        result = reviewer.recritique(self.CODE, self.IMPROVED, self.CRITIQUE)
        assert result == {"new_score": 9}

    def test_recritique_calls_api_on_miss(self):
        reviewer = self._make_reviewer(make_cache_manager())
        mock_message = MagicMock()
        mock_message.content[0].text = '{"new_score": 8}'
        reviewer.client.messages.create.return_value = mock_message

        tmpl = "recritique {original_code} {original_scores} {improved_code}"
        with patch.object(reviewer, "_load_prompt_template", return_value=tmpl):
            result = reviewer.recritique(self.CODE, self.IMPROVED, self.CRITIQUE)

        assert result["new_score"] == 8

    def test_recritique_returns_error_on_exception(self):
        reviewer = self._make_reviewer(make_cache_manager())
        reviewer.client.messages.create.side_effect = Exception("timeout")

        tmpl = "recritique {original_code} {original_scores} {improved_code}"
        with patch.object(reviewer, "_load_prompt_template", return_value=tmpl):
            result = reviewer.recritique(self.CODE, self.IMPROVED, self.CRITIQUE)

        assert "error" in result


# ---------------------------------------------------------------------------
# GemmaReviewer — not yet implemented stubs
# ---------------------------------------------------------------------------


class TestGemmaReviewer:
    def _make_reviewer(self):
        return GemmaReviewer()

    def test_critique_returns_error(self):
        result = self._make_reviewer().critique("def foo(): pass")
        assert "error" in result

    def test_improve_returns_error(self):
        result = self._make_reviewer().improve("def foo(): pass", {})
        assert "error" in result

    def test_recritique_returns_error(self):
        result = self._make_reviewer().recritique("orig", "improved", {})
        assert "error" in result

    def test_custom_base_url_stored(self):
        reviewer = GemmaReviewer(base_url="http://myhost:11434")
        assert reviewer.base_url == "http://myhost:11434"
