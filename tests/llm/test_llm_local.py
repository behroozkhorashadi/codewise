"""Tests for source/llm/llm_local.py"""

import json
from unittest.mock import MagicMock, patch

import pytest

from source.llm.llm_local import local_model_request


class TestLocalModelRequest:
    def _make_response(self, content="hello"):
        resp = MagicMock()
        resp.json.return_value = {"choices": [{"message": {"content": content}}]}
        resp.raise_for_status.return_value = None
        return resp

    @patch("source.llm.llm_local.requests.post")
    def test_returns_content_on_success(self, mock_post):
        mock_post.return_value = self._make_response("LLM response")
        result = local_model_request("evaluate this code")
        assert result == "LLM response"

    @patch("source.llm.llm_local.requests.post")
    def test_handles_missing_choices(self, mock_post):
        resp = MagicMock()
        resp.json.return_value = {}
        resp.raise_for_status.return_value = None
        mock_post.return_value = resp
        result = local_model_request("test")
        assert "Error" in result

    @patch("source.llm.llm_local.requests.post")
    def test_handles_empty_choices_list(self, mock_post):
        resp = MagicMock()
        resp.json.return_value = {"choices": []}
        resp.raise_for_status.return_value = None
        mock_post.return_value = resp
        result = local_model_request("test")
        assert "Error" in result

    @patch("source.llm.llm_local.requests.post")
    def test_handles_missing_message_content(self, mock_post):
        resp = MagicMock()
        resp.json.return_value = {"choices": [{"no_message": True}]}
        resp.raise_for_status.return_value = None
        mock_post.return_value = resp
        result = local_model_request("test")
        assert "Error" in result

    @patch("source.llm.llm_local.requests.post")
    def test_handles_request_exception(self, mock_post):
        import requests as req

        mock_post.side_effect = req.exceptions.RequestException("connection refused")
        result = local_model_request("test")
        assert "Request failed" in result

    @patch("source.llm.llm_local.requests.post")
    def test_handles_json_decode_error(self, mock_post):
        resp = MagicMock()
        resp.json.side_effect = json.JSONDecodeError("bad json", "", 0)
        resp.raise_for_status.return_value = None
        mock_post.return_value = resp
        result = local_model_request("test")
        assert "Failed to decode JSON" in result

    @patch("source.llm.llm_local.requests.post")
    def test_handles_key_error(self, mock_post):
        # Trigger KeyError: choices is a dict with string key "0", not integer 0
        resp = MagicMock()
        resp.json.return_value = {"choices": {"0": "value"}}
        resp.raise_for_status.return_value = None
        mock_post.return_value = resp
        result = local_model_request("test")
        assert "Failed to extract" in result or "Error" in result

    @patch("source.llm.llm_local.requests.post")
    def test_handles_unexpected_exception(self, mock_post):
        mock_post.side_effect = Exception("unexpected")
        result = local_model_request("test")
        assert "Unexpected error" in result or "error" in result.lower()
