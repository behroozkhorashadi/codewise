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
