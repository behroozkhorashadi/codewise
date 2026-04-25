"""Tests for source/pipeline/cache_manager.py"""

import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from source.pipeline.cache_manager import CacheManager


@pytest.fixture
def cache(tmp_path):
    return CacheManager(cache_dir=str(tmp_path / "cache"))


class TestCacheManagerInit:
    def test_creates_cache_dir(self, tmp_path):
        cache_dir = tmp_path / "my_cache"
        assert not cache_dir.exists()
        CacheManager(str(cache_dir))
        assert cache_dir.exists()


class TestGenerateCacheKey:
    def test_deterministic(self, cache):
        key1 = cache._generate_cache_key("claude", "def foo(): pass", "critique")
        key2 = cache._generate_cache_key("claude", "def foo(): pass", "critique")
        assert key1 == key2

    def test_different_inputs_different_keys(self, cache):
        key1 = cache._generate_cache_key("claude", "def foo(): pass", "critique")
        key2 = cache._generate_cache_key("gpt4", "def foo(): pass", "critique")
        assert key1 != key2

    def test_whitespace_normalized(self, cache):
        key1 = cache._generate_cache_key("m", "  code  ", "t")
        key2 = cache._generate_cache_key("m", "code", "t")
        assert key1 == key2

    def test_prompt_version_affects_key(self, cache):
        key1 = cache._generate_cache_key("m", "code", "t", "1.0")
        key2 = cache._generate_cache_key("m", "code", "t", "2.0")
        assert key1 != key2


class TestCacheGet:
    def test_miss_returns_none(self, cache):
        assert cache.get("claude", "code", "critique") is None

    def test_hit_returns_data(self, cache):
        response = {"overall_score": 8}
        cache.set("claude", "code", "critique", response)
        result = cache.get("claude", "code", "critique")
        assert result is not None
        assert result["response"] == response

    def test_corrupt_file_returns_none(self, cache, tmp_path):
        key = cache._generate_cache_key("claude", "code", "critique")
        corrupt_file = cache.cache_dir / f"{key}.json"
        corrupt_file.write_text("not valid json{{{")
        result = cache.get("claude", "code", "critique")
        assert result is None


class TestCacheSet:
    def test_stores_response_with_metadata(self, cache):
        cache.set("gpt4", "def bar(): pass", "improve", {"score": 9})
        result = cache.get("gpt4", "def bar(): pass", "improve")
        assert result["model"] == "gpt4"
        assert result["prompt_type"] == "improve"
        assert "cached_at" in result
        assert result["response"] == {"score": 9}

    def test_overwrites_existing_cache(self, cache):
        cache.set("claude", "code", "critique", {"score": 7})
        cache.set("claude", "code", "critique", {"score": 9})
        result = cache.get("claude", "code", "critique")
        assert result["response"]["score"] == 9

    def test_ioerror_on_write_does_not_raise(self, cache):
        with patch("builtins.open", side_effect=IOError("disk full")):
            cache.set("m", "c", "t", {"x": 1})


class TestCacheClear:
    def test_removes_all_cache_files(self, cache):
        cache.set("m", "code1", "t", {"x": 1})
        cache.set("m", "code2", "t", {"x": 2})
        assert len(list(cache.cache_dir.glob("*.json"))) == 2
        cache.clear()
        assert len(list(cache.cache_dir.glob("*.json"))) == 0

    def test_cache_dir_still_exists_after_clear(self, cache):
        cache.clear()
        assert cache.cache_dir.exists()


class TestCacheStats:
    def test_empty_cache_stats(self, cache):
        stats = cache.get_cache_stats()
        assert stats["total_files"] == 0
        assert stats["total_size_bytes"] == 0

    def test_stats_count_files(self, cache):
        cache.set("m", "code1", "t", {"x": 1})
        cache.set("m", "code2", "t", {"x": 2})
        stats = cache.get_cache_stats()
        assert stats["total_files"] == 2
        assert stats["total_size_bytes"] > 0
        assert stats["cache_dir"] == str(cache.cache_dir)


class TestCacheClearIOError:
    def test_clear_ioerror_does_not_raise(self, cache):
        import shutil

        with patch("shutil.rmtree", side_effect=IOError("permission denied")):
            cache.clear()  # Should not raise


class TestPipelineLoggerIOErrors:
    pass
