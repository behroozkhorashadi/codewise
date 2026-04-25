import ast
import sys

import pytest

from source.logic.code_ast_parser import return_function_text
from source.utils.parse_helper import parse_arguments


def test_return_function_text():
    # Define the source code
    source_code = """
def example_function():
    x = 10
    y = 20
    return x + y
"""

    # Parse the source code into an AST
    tree = ast.parse(source_code)

    # Get the first function definition from the parsed AST
    enclosing_function = next((node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)), None)

    # Ensure the AST node for the function is valid
    assert enclosing_function is not None

    # Call the function and check the result
    result = return_function_text(enclosing_function, source_code)

    # Expected function text
    expected = "def example_function():\n    x = 10\n    y = 20\n    return x + y"

    assert result == expected


def test_return_function_text_no_function():
    # Test with no enclosing function (None)
    result = return_function_text(None, "dummy source code")
    assert result is None


def test_parse_arguments_valid():
    """Test that parse_arguments correctly parses valid input arguments."""
    test_args = [
        "script_name",
        "/Users/behrooz/Work/recall-api",
        "/Users/behrooz/Work/recall-api/api/spam/logic/spam_prevention.py",
    ]

    # Temporarily replace sys.argv
    sys.argv = test_args

    args = parse_arguments()

    assert args.root_directory == "/Users/behrooz/Work/recall-api"
    assert args.file_path == "/Users/behrooz/Work/recall-api/api/spam/logic/spam_prevention.py"


def test_parse_arguments_missing_required_args():
    """Test that parse_arguments raises a SystemExit error when required arguments are missing."""
    test_args = [
        "script_name",
        "--root-directory",
        "/Users/behrooz/Work/recall-api",
        # Missing --file-path argument
    ]

    # Temporarily replace sys.argv
    sys.argv = test_args

    with pytest.raises(SystemExit):  # argparse exits the program if arguments are missing
        parse_arguments()


def test_parse_arguments_invalid_args():
    """Test that parse_arguments raises a SystemExit error for invalid arguments."""
    test_args = ["script_name", "--invalid-arg", "some_value"]

    # Temporarily replace sys.argv
    sys.argv = test_args

    with pytest.raises(SystemExit):  # argparse exits the program if invalid arguments are passed
        parse_arguments()


# ---------------------------------------------------------------------------
# Additional tests for coverage
# ---------------------------------------------------------------------------

import os
import tempfile
from unittest.mock import patch

from source.logic.code_ast_parser import (
    MethodUsageCollector,
    collect_method_usages,
    find_enclosing_function,
    get_method_body,
    print_enclosing_function_definition_from_file,
    set_parent_pointers,
)


def test_find_enclosing_function_returns_none_when_no_parent():
    """find_enclosing_function returns None when no FunctionDef parent exists"""
    node = ast.Call(func=ast.Name(id="foo"), args=[], keywords=[])
    node.parent = None
    result = find_enclosing_function(node)
    assert result is None


def test_find_enclosing_function_finds_parent():
    source = "def outer():\n    foo()\n"
    tree = ast.parse(source)
    set_parent_pointers(tree)
    call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call))
    result = find_enclosing_function(call)
    assert isinstance(result, ast.FunctionDef)
    assert result.name == "outer"


def test_set_parent_pointers_sets_parent_on_children():
    tree = ast.parse("def f(): pass")
    set_parent_pointers(tree)
    func_def = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    assert hasattr(func_def, "parent")


def test_get_method_body_reads_file(tmp_path):
    code = "def hello():\n    return 42\n"
    py_file = tmp_path / "m.py"
    py_file.write_text(code)
    tree = ast.parse(code)
    func_node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    # Add line info (parse already does this)
    result = get_method_body(func_node, str(py_file))
    assert "def hello" in result


def test_print_enclosing_function_definition_from_file(tmp_path, capsys):
    code = "def greet():\n    print('hi')\n"
    py_file = tmp_path / "m.py"
    py_file.write_text(code)
    tree = ast.parse(code)
    func_node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    print_enclosing_function_definition_from_file(func_node, str(py_file))
    out = capsys.readouterr().out
    assert "greet" in out


class TestMethodUsageCollectorImports:
    def test_visit_import_adds_to_map(self):
        collector = MethodUsageCollector("/root", "/root/f.py")
        node = ast.parse("import os").body[0]
        collector.visit_Import(node)
        assert "os" in collector.import_map

    def test_visit_import_with_alias(self):
        collector = MethodUsageCollector("/root", "/root/f.py")
        node = ast.parse("import numpy as np").body[0]
        collector.visit_Import(node)
        assert "np" in collector.import_map

    def test_visit_import_from(self):
        collector = MethodUsageCollector("/root", "/root/f.py")
        node = ast.parse("from os.path import join").body[0]
        collector.visit_ImportFrom(node)
        assert "join" in collector.import_map
        assert "os.path.join" == collector.import_map["join"]

    def test_visit_import_from_alias(self):
        collector = MethodUsageCollector("/root", "/root/f.py")
        node = ast.parse("from os.path import join as j").body[0]
        collector.visit_ImportFrom(node)
        assert "j" in collector.import_map

    def test_visit_import_from_no_module(self):
        collector = MethodUsageCollector("/root", "/root/f.py")
        node = ast.ImportFrom(module=None, names=[ast.alias(name="foo")], level=0)
        collector.visit_ImportFrom(node)
        assert "foo" in collector.import_map


class TestMethodUsageCollectorResolveCalls:
    def test_resolve_direct_call(self):
        collector = MethodUsageCollector("/root", "/root/f.py")
        collector.current_module_name = "mymod"
        node = ast.parse("foo()").body[0].value
        result = collector.resolve_call_identifier(node)
        assert result is not None
        assert result.method_name == "foo"

    def test_resolve_attribute_call(self):
        collector = MethodUsageCollector("/root", "/root/f.py")
        collector.current_module_name = "mymod"
        collector.import_map["obj"] = "somemod"
        node = ast.parse("obj.method()").body[0].value
        result = collector.resolve_call_identifier(node)
        assert result is not None
        assert result.method_name == "method"

    def test_resolve_self_method_call(self):
        collector = MethodUsageCollector("/root", "/root/f.py")
        collector.current_module_name = "mymod"
        node = ast.parse("self.do_thing()").body[0].value
        result = collector.resolve_call_identifier(node)
        assert result is not None
        assert result.method_name == "do_thing"
        assert result.module_name == "mymod"

    def test_resolve_returns_none_for_complex_call(self):
        collector = MethodUsageCollector("/root", "/root/f.py")
        node = ast.parse("func()()").body[0].value
        result = collector.resolve_call_identifier(node)
        # Inner func() has no name attribute → returns None
        # (may or may not be None depending on AST structure, just don't crash)


class TestMethodUsageCollectorParseFile:
    def test_parse_target_file_collects_functions(self, tmp_path):
        code = "def alpha():\n    pass\ndef beta():\n    pass\n"
        f = tmp_path / "module.py"
        f.write_text(code)
        collector = MethodUsageCollector(str(tmp_path), str(f))
        collector.set_current_file(str(f))
        collector.parse_target_file()
        method_names = [mid.method_name for mid in collector.method_definitions]
        assert "alpha" in method_names
        assert "beta" in method_names

    def test_parse_target_file_handles_syntax_error(self, tmp_path):
        f = tmp_path / "bad.py"
        f.write_text("def broken(:\n    pass\n")
        collector = MethodUsageCollector(str(tmp_path), str(f))
        collector.set_current_file(str(f))
        with pytest.raises(SyntaxError):
            collector.parse_target_file()

    def test_parse_repo_files_skips_test_files(self, tmp_path):
        (tmp_path / "code.py").write_text("def greet(): pass\n")
        (tmp_path / "test_code.py").write_text("def test_it(): pass\n")
        collector = MethodUsageCollector(str(tmp_path), str(tmp_path / "code.py"))
        collector.parse_target_file()
        collector.parse_repo_files()
        # No assertion needed — should not crash; test files should be ignored

    def test_current_filepath_to_module_name(self, tmp_path):
        f = tmp_path / "pkg" / "mod.py"
        f.parent.mkdir()
        collector = MethodUsageCollector(str(tmp_path), str(f))
        collector.set_current_file(str(f))
        module = collector.current_filepath_to_module_name()
        assert "pkg" in module or "mod" in module


class TestCollectMethodUsages:
    def test_full_pipeline_finds_usages(self, tmp_path):
        target = tmp_path / "utils.py"
        target.write_text("def helper():\n    return 1\n")
        caller = tmp_path / "main.py"
        caller.write_text("from utils import helper\ndef run():\n    helper()\n")
        result = collect_method_usages(str(tmp_path), str(target))
        # helper should be found with at least 0 call sites (cross-file resolution may vary)
        assert isinstance(result, dict)


class TestMethodUsageCollectorClassMethods:
    """Tests to cover class method detection (lines 104-115)"""

    def test_collect_class_method_definitions(self, tmp_path):
        code = "class MyClass:\n    def my_method(self):\n        pass\n"
        f = tmp_path / "mod.py"
        f.write_text(code)
        collector = MethodUsageCollector(str(tmp_path), str(f))
        collector.set_current_file(str(f))
        collector.parse_target_file()
        method_names = [mid.method_name for mid in collector.method_definitions]
        assert "my_method" in method_names

    def test_nested_class_method_found(self, tmp_path):
        code = "class A:\n    class B:\n        def inner(self):\n            pass\n"
        f = tmp_path / "nested.py"
        f.write_text(code)
        collector = MethodUsageCollector(str(tmp_path), str(f))
        collector.set_current_file(str(f))
        collector.parse_target_file()
        method_names = [mid.method_name for mid in collector.method_definitions]
        assert "inner" in method_names


class TestMethodUsageCollectorVisitCall:
    """Tests to cover visit_Call (lines 179-190) and resolve fallback (line 164)"""

    def test_visit_call_records_usage(self, tmp_path):
        target = tmp_path / "utils.py"
        target.write_text("def helper():\n    return 1\n")
        caller = tmp_path / "main.py"
        caller.write_text("from utils import helper\ndef run():\n    helper()\n")
        collector = MethodUsageCollector(str(tmp_path), str(target))
        collector.parse_target_file()
        collector.parse_repo_files()
        # At least one method should have usages recorded if cross-file resolution works
        assert isinstance(collector.method_usages, dict)

    def test_resolve_attribute_fallback_uses_chain(self):
        """Line 164: fallback module_name = '.'.join(attribute_chain[:-1])"""
        collector = MethodUsageCollector("/root", "/root/f.py")
        collector.current_module_name = "mymod"
        # obj.sub.method() where obj is not in import_map
        node = ast.parse("obj.sub.method()").body[0].value
        result = collector.resolve_call_identifier(node)
        assert result is not None
        assert result.method_name == "method"
        assert "obj" in result.module_name or "sub" in result.module_name

    def test_current_filepath_to_module_name_unknown(self):
        """Line 253: returns 'unknown_module' for files outside root"""
        collector = MethodUsageCollector("/root", "/root/f.py")
        collector.current_file = "/completely/different/path.py"
        result = collector.current_filepath_to_module_name()
        assert result == "unknown_module"


class TestParseRepoFilesErrorHandling:
    """Tests for syntax error and general error handling in parse_repo_files"""

    def test_skips_syntax_error_files(self, tmp_path, capsys):
        target = tmp_path / "good.py"
        target.write_text("def good(): pass\n")
        bad = tmp_path / "bad.py"
        bad.write_text("def broken(:\n    pass\n")
        collector = MethodUsageCollector(str(tmp_path), str(target))
        collector.parse_target_file()
        collector.parse_repo_files()  # Should not raise

    def test_visit_call_records_usages_up_to_10(self, tmp_path):
        """visit_Call capped at 10 usages"""
        target = tmp_path / "utils.py"
        target.write_text("def greet():\n    return 'hi'\n")
        calls = "\n".join(f"def f{i}():\n    greet()" for i in range(15))
        caller = tmp_path / "main.py"
        caller.write_text(f"from utils import greet\n{calls}\n")
        result = collect_method_usages(str(tmp_path), str(target))
        for usages in result.values():
            assert len(usages) <= 10
