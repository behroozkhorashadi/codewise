"""Tests for source/llm/llm_integration.py"""

from unittest.mock import MagicMock, patch

import pytest

from source.llm.llm_integration import get_method_ratings


class TestGetMethodRatings:
    def test_returns_instructions_when_no_api_key(self):
        with patch("source.llm.llm_integration.openai.api_key", None):
            result = get_method_ratings("some prompt")
        assert "OpenAI API key" in result

    @patch("source.llm.llm_integration.openai.chat.completions.create")
    def test_returns_response_content_on_success(self, mock_create):
        mock_choice = MagicMock()
        mock_choice.message.content = "Score: 8/10"
        mock_create.return_value = MagicMock(choices=[mock_choice])

        with patch("source.llm.llm_integration.openai.api_key", "fake-key"):
            result = get_method_ratings("evaluate this")

        assert result == "Score: 8/10"

    @patch("source.llm.llm_integration.openai.chat.completions.create")
    def test_uses_specified_model(self, mock_create):
        mock_choice = MagicMock()
        mock_choice.message.content = "ok"
        mock_create.return_value = MagicMock(choices=[mock_choice])

        with patch("source.llm.llm_integration.openai.api_key", "fake-key"):
            get_method_ratings("prompt", model="gpt-4-turbo")

        call_kwargs = mock_create.call_args
        assert call_kwargs.kwargs["model"] == "gpt-4-turbo"

    @patch("source.llm.llm_integration.openai.chat.completions.create")
    def test_returns_empty_message_string_when_content_none(self, mock_create):
        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_create.return_value = MagicMock(choices=[mock_choice])

        with patch("source.llm.llm_integration.openai.api_key", "fake-key"):
            result = get_method_ratings("prompt")

        assert "empty" in result.lower() or "invalid" in result.lower()

    @patch("source.llm.llm_integration.openai.chat.completions.create")
    def test_handles_openai_error(self, mock_create):
        import openai as openai_mod

        mock_create.side_effect = openai_mod.OpenAIError("rate limit")

        with patch("source.llm.llm_integration.openai.api_key", "fake-key"):
            result = get_method_ratings("prompt")

        assert "OpenAI API error" in result
