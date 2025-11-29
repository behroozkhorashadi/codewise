"""
LLM API Integration Layer

This module provides abstract and concrete implementations for integrating multiple LLMs
(Claude, GPT-4, Gemma) with the code review pipeline.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import anthropic
import openai

from source.pipeline.cache_manager import CacheManager
from source.pipeline.pipeline_logger import get_logger

logger = get_logger(__name__)


class CodeReviewModel(ABC):
    """Abstract base class for code review models."""

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize the model.

        Args:
            cache_manager: Cache manager instance for caching responses.
        """
        self.cache_manager = cache_manager
        self.model_name = None

    @abstractmethod
    def critique(self, code: str) -> Dict[str, Any]:
        """
        Critique the code.

        Args:
            code: The Python code to critique.

        Returns:
            Dictionary with scores and feedback.
        """
        pass

    @abstractmethod
    def improve(self, code: str, critique: Dict[str, Any]) -> Dict[str, Any]:
        """
        Improve the code based on critique.

        Args:
            code: The original Python code.
            critique: The critique from the model.

        Returns:
            Dictionary with refactored code and explanations.
        """
        pass

    @abstractmethod
    def recritique(self, original_code: str, improved_code: str, original_critique: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-evaluate the improved code.

        Args:
            original_code: The original code.
            improved_code: The refactored code.
            original_critique: The original critique scores.

        Returns:
            Dictionary with new scores and comparative analysis.
        """
        pass

    def _load_prompt_template(self, template_name: str) -> str:
        """
        Load a prompt template from file.

        Args:
            template_name: Name of the template (e.g., 'critique_template')

        Returns:
            The prompt template string.
        """
        from pathlib import Path

        template_path = Path(__file__).parent.parent.parent / "prompts" / f"{template_name}.txt"
        with open(template_path, "r") as f:
            return f.read()

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from the model.

        Args:
            response_text: The model's response text.

        Returns:
            Parsed JSON dictionary.
        """
        # Try to find JSON in the response
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON from response")
                    return {"error": "Failed to parse response", "raw_response": response_text}
            else:
                logger.error("No JSON found in response")
                return {"error": "No JSON in response", "raw_response": response_text}


class ClaudeReviewer(CodeReviewModel):
    """Code review model using Claude (via Anthropic API)."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "claude-3-5-sonnet-20241022",
        cache_manager: Optional[CacheManager] = None,
    ):
        """
        Initialize Claude reviewer.

        Args:
            api_key: Anthropic API key.
            model_name: Claude model to use.
            cache_manager: Cache manager instance.
        """
        super().__init__(cache_manager)
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_name = model_name

    def critique(self, code: str) -> Dict[str, Any]:
        """Critique code using Claude."""
        if self.cache_manager:
            cached = self.cache_manager.get("claude", code, "critique")
            if cached:
                return cached["response"]

        template = self._load_prompt_template("critique_template")
        prompt = template.format(code_content=code)

        try:
            message = self.client.messages.create(
                model=self.model_name, max_tokens=2048, messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            response = self._parse_json_response(response_text)

            # Cache the response
            if self.cache_manager:
                self.cache_manager.set("claude", code, "critique", response)

            return response
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return {"error": str(e)}

    def improve(self, code: str, critique: Dict[str, Any]) -> Dict[str, Any]:
        """Improve code based on critique."""
        if self.cache_manager:
            cached = self.cache_manager.get("claude", code, "improve")
            if cached:
                return cached["response"]

        template = self._load_prompt_template("improve_template")
        prompt = template.format(code_content=code, critique=json.dumps(critique, indent=2))

        try:
            message = self.client.messages.create(
                model=self.model_name, max_tokens=2048, messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            response = self._parse_json_response(response_text)

            if self.cache_manager:
                self.cache_manager.set("claude", code, "improve", response)

            return response
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return {"error": str(e)}

    def recritique(self, original_code: str, improved_code: str, original_critique: Dict[str, Any]) -> Dict[str, Any]:
        """Re-critique the improved code."""
        if self.cache_manager:
            cached = self.cache_manager.get("claude", improved_code, "recritique")
            if cached:
                return cached["response"]

        template = self._load_prompt_template("recritique_template")
        prompt = template.format(
            original_code=original_code,
            original_scores=json.dumps(original_critique.get("scores", {}), indent=2),
            improved_code=improved_code,
        )

        try:
            message = self.client.messages.create(
                model=self.model_name, max_tokens=2048, messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            response = self._parse_json_response(response_text)

            if self.cache_manager:
                self.cache_manager.set("claude", improved_code, "recritique", response)

            return response
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return {"error": str(e)}


class GPT4Reviewer(CodeReviewModel):
    """Code review model using GPT-4 (via OpenAI API)."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4-turbo",
        cache_manager: Optional[CacheManager] = None,
    ):
        """
        Initialize GPT-4 reviewer.

        Args:
            api_key: OpenAI API key.
            model_name: GPT-4 model to use.
            cache_manager: Cache manager instance.
        """
        super().__init__(cache_manager)
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name

    def critique(self, code: str) -> Dict[str, Any]:
        """Critique code using GPT-4."""
        if self.cache_manager:
            cached = self.cache_manager.get("gpt4", code, "critique")
            if cached:
                return cached["response"]

        template = self._load_prompt_template("critique_template")
        prompt = template.format(code_content=code)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.choices[0].message.content
            parsed_response = self._parse_json_response(response_text)

            if self.cache_manager:
                self.cache_manager.set("gpt4", code, "critique", parsed_response)

            return parsed_response
        except Exception as e:
            logger.error(f"Error calling GPT-4 API: {e}")
            return {"error": str(e)}

    def improve(self, code: str, critique: Dict[str, Any]) -> Dict[str, Any]:
        """Improve code based on critique."""
        if self.cache_manager:
            cached = self.cache_manager.get("gpt4", code, "improve")
            if cached:
                return cached["response"]

        template = self._load_prompt_template("improve_template")
        prompt = template.format(code_content=code, critique=json.dumps(critique, indent=2))

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.choices[0].message.content
            parsed_response = self._parse_json_response(response_text)

            if self.cache_manager:
                self.cache_manager.set("gpt4", code, "improve", parsed_response)

            return parsed_response
        except Exception as e:
            logger.error(f"Error calling GPT-4 API: {e}")
            return {"error": str(e)}

    def recritique(self, original_code: str, improved_code: str, original_critique: Dict[str, Any]) -> Dict[str, Any]:
        """Re-critique the improved code."""
        if self.cache_manager:
            cached = self.cache_manager.get("gpt4", improved_code, "recritique")
            if cached:
                return cached["response"]

        template = self._load_prompt_template("recritique_template")
        prompt = template.format(
            original_code=original_code,
            original_scores=json.dumps(original_critique.get("scores", {}), indent=2),
            improved_code=improved_code,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.choices[0].message.content
            parsed_response = self._parse_json_response(response_text)

            if self.cache_manager:
                self.cache_manager.set("gpt4", improved_code, "recritique", parsed_response)

            return parsed_response
        except Exception as e:
            logger.error(f"Error calling GPT-4 API: {e}")
            return {"error": str(e)}


class GemmaReviewer(CodeReviewModel):
    """Code review model using Gemma (via Ollama local API or HuggingFace)."""

    def __init__(
        self,
        model_name: str = "gemma:latest",
        base_url: str = "http://localhost:11434",
        cache_manager: Optional[CacheManager] = None,
    ):
        """
        Initialize Gemma reviewer.

        Args:
            model_name: Gemma model name.
            base_url: Base URL for Ollama API.
            cache_manager: Cache manager instance.
        """
        super().__init__(cache_manager)
        self.model_name = model_name
        self.base_url = base_url
        # TODO: Initialize Ollama client when ready

    def critique(self, code: str) -> Dict[str, Any]:
        """Critique code using Gemma (not implemented yet)."""
        logger.warning("Gemma reviewer not yet implemented")
        return {"error": "Gemma reviewer not yet implemented"}

    def improve(self, code: str, critique: Dict[str, Any]) -> Dict[str, Any]:
        """Improve code (not implemented yet)."""
        logger.warning("Gemma reviewer not yet implemented")
        return {"error": "Gemma reviewer not yet implemented"}

    def recritique(self, original_code: str, improved_code: str, original_critique: Dict[str, Any]) -> Dict[str, Any]:
        """Re-critique code (not implemented yet)."""
        logger.warning("Gemma reviewer not yet implemented")
        return {"error": "Gemma reviewer not yet implemented"}
