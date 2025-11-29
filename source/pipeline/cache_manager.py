"""
Cache manager for storing and retrieving LLM API responses.

This module provides a file-based caching system to avoid redundant API calls.
Each cached response is stored as a JSON file with a deterministic hash-based filename.
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of LLM API responses."""

    def __init__(self, cache_dir: str = "intermediate/cache"):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files.
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cache manager initialized at {self.cache_dir}")

    def _generate_cache_key(
        self,
        model_name: str,
        code_sample: str,
        prompt_type: str,
        prompt_version: str = "1.0",
    ) -> str:
        """
        Generate a deterministic cache key from input parameters.

        Args:
            model_name: Name of the model (e.g., 'claude', 'gpt4', 'gemma')
            code_sample: The code sample being evaluated
            prompt_type: Type of prompt (e.g., 'critique', 'improve', 'recritique')
            prompt_version: Version of the prompt template

        Returns:
            A deterministic hash-based cache key
        """
        # Combine inputs into a normalized string
        cache_input = f"{model_name}|{prompt_type}|{prompt_version}|{code_sample.strip()}"

        # Generate SHA256 hash
        hash_object = hashlib.sha256(cache_input.encode())
        return hash_object.hexdigest()

    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get the full file path for a cache key."""
        return self.cache_dir / f"{cache_key}.json"

    def get(
        self,
        model_name: str,
        code_sample: str,
        prompt_type: str,
        prompt_version: str = "1.0",
    ) -> Optional[dict]:
        """
        Retrieve a cached response if it exists.

        Args:
            model_name: Name of the model
            code_sample: The code sample
            prompt_type: Type of prompt
            prompt_version: Version of the prompt template

        Returns:
            Cached response dict if found, None otherwise
        """
        cache_key = self._generate_cache_key(model_name, code_sample, prompt_type, prompt_version)
        cache_file = self._get_cache_file_path(cache_key)

        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    cached_data = json.load(f)
                logger.debug(f"Cache hit for {model_name}/{prompt_type}: {cache_key[:8]}...")
                return cached_data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")
                return None

        logger.debug(f"Cache miss for {model_name}/{prompt_type}: {cache_key[:8]}...")
        return None

    def set(
        self,
        model_name: str,
        code_sample: str,
        prompt_type: str,
        response: dict,
        prompt_version: str = "1.0",
    ) -> None:
        """
        Store a response in cache.

        Args:
            model_name: Name of the model
            code_sample: The code sample
            prompt_type: Type of prompt
            response: The LLM response to cache
            prompt_version: Version of the prompt template
        """
        cache_key = self._generate_cache_key(model_name, code_sample, prompt_type, prompt_version)
        cache_file = self._get_cache_file_path(cache_key)

        # Add metadata to cached response
        cache_entry = {
            "cached_at": datetime.utcnow().isoformat() + "Z",
            "model": model_name,
            "prompt_type": prompt_type,
            "prompt_version": prompt_version,
            "cache_key": cache_key,
            "response": response,
        }

        try:
            with open(cache_file, "w") as f:
                json.dump(cache_entry, f, indent=2)
            logger.debug(f"Cached response for {model_name}/{prompt_type}: {cache_key[:8]}...")
        except IOError as e:
            logger.error(f"Failed to write cache file {cache_file}: {e}")

    def clear(self) -> None:
        """Clear all cache files."""
        import shutil

        try:
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Cache cleared")
        except IOError as e:
            logger.error(f"Failed to clear cache: {e}")

    def get_cache_stats(self) -> dict:
        """Get statistics about the cache."""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "cache_dir": str(self.cache_dir),
            "total_files": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
        }
