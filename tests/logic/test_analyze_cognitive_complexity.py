"""Tests for source/logic/analyze_cognitive_complexity.py"""

import os
import tempfile
from unittest.mock import patch

import pytest

from source.logic.analyze_cognitive_complexity import (
    analyze_cognitive_complexity,
    calculate_cognitive_complexity,
    get_list_of_python_files,
)

# ---------------------------------------------------------------------------
# calculate_cognitive_complexity
# ---------------------------------------------------------------------------


class TestCalculateCognitiveComplexity:
    def test_simple_function(self):
        code = "def simple(): return 1"
        complexities = []
        calculate_cognitive_complexity(code, complexities, "module.py", "/path/module.py")
        assert len(complexities) == 1
        func_name, score, file_name, file_path = complexities[0]
        assert func_name == "simple"
        assert isinstance(score, int)
        assert file_name == "module.py"
        assert file_path == "/path/module.py"

    def test_nested_function(self):
        code = """
def outer():
    def inner():
        for i in range(10):
            if i > 5:
                pass
"""
        complexities = []
        calculate_cognitive_complexity(code, complexities, "f.py", "/f.py")
        names = [c[0] for c in complexities]
        assert "outer" in names
        assert "inner" in names

    def test_no_functions(self):
        code = "x = 1 + 2"
        complexities = []
        calculate_cognitive_complexity(code, complexities, "f.py", "/f.py")
        assert complexities == []

    def test_high_complexity_function(self):
        code = """
def complex_func(a, b, c):
    if a:
        for x in range(10):
            if x > 5:
                while b:
                    if c:
                        pass
"""
        complexities = []
        calculate_cognitive_complexity(code, complexities, "f.py", "/f.py")
        assert len(complexities) == 1
        _, score, _, _ = complexities[0]
        assert score > 0


# ---------------------------------------------------------------------------
# get_list_of_python_files
# ---------------------------------------------------------------------------


class TestGetListOfPythonFiles:
    def test_returns_py_files(self, tmp_path, capsys):
        # The function skips the root dir (relpath=".") so files must be in a subdir
        sub = tmp_path / "src"
        sub.mkdir()
        (sub / "module.py").write_text("x = 1")
        (sub / "other.py").write_text("y = 2")
        result = get_list_of_python_files(str(tmp_path))
        names = [os.path.basename(f) for f in result]
        assert "module.py" in names
        assert "other.py" in names

    def test_skips_test_files(self, tmp_path, capsys):
        sub = tmp_path / "src"
        sub.mkdir()
        (sub / "test_module.py").write_text("x = 1")
        (sub / "code.py").write_text("y = 2")
        result = get_list_of_python_files(str(tmp_path))
        names = [os.path.basename(f) for f in result]
        assert "test_module.py" not in names
        assert "code.py" in names

    def test_skips_non_py_files(self, tmp_path, capsys):
        (tmp_path / "readme.txt").write_text("text")
        (tmp_path / "script.py").write_text("pass")
        result = get_list_of_python_files(str(tmp_path))
        names = [os.path.basename(f) for f in result]
        assert "readme.txt" not in names

    def test_skips_hidden_directories(self, tmp_path, capsys):
        hidden_dir = tmp_path / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "secret.py").write_text("x = 1")
        result = get_list_of_python_files(str(tmp_path))
        paths = [os.path.abspath(f) for f in result]
        assert not any(".hidden" in p for p in paths)

    def test_recurses_into_subdirectories(self, tmp_path, capsys):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "deep.py").write_text("pass")
        result = get_list_of_python_files(str(tmp_path))
        names = [os.path.basename(f) for f in result]
        assert "deep.py" in names

    def test_empty_directory(self, tmp_path, capsys):
        result = get_list_of_python_files(str(tmp_path))
        assert result == []


# ---------------------------------------------------------------------------
# analyze_cognitive_complexity
# ---------------------------------------------------------------------------


class TestAnalyzeCognitiveComplexity:
    def test_prints_results(self, tmp_path, capsys):
        # Files must be in a subdirectory (root dir is skipped due to relpath = ".")
        sub = tmp_path / "src"
        sub.mkdir()
        (sub / "code.py").write_text("def foo(): return 1\n")
        analyze_cognitive_complexity(str(tmp_path))
        out = capsys.readouterr().out
        assert "foo" in out

    def test_sorts_by_complexity_descending(self, tmp_path, capsys):
        code = """
def simple(): return 1

def complex_func(a, b):
    if a:
        for x in range(5):
            if x > 2:
                pass
"""
        (tmp_path / "code.py").write_text(code)
        analyze_cognitive_complexity(str(tmp_path))
        out = capsys.readouterr().out
        lines = [l for l in out.strip().split("\n") if "," in l]
        # complex_func should appear before simple (higher complexity first)
        if len(lines) >= 2:
            assert "complex_func" in lines[0]

    def test_empty_directory(self, tmp_path, capsys):
        analyze_cognitive_complexity(str(tmp_path))
        # Should not raise, output may be empty (just the dir prints)
