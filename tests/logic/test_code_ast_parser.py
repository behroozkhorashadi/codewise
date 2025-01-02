import pytest

import ast
import pytest
from typing import Optional

from code_wise.logic.code_ast_parser import return_function_text


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
