#!/usr/bin/env python3
import os
import sys

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from source.logic.code_ast_parser import collect_method_usages


def test_specific_file():
    # Test with the specific file that's causing issues
    root_dir = "/Users/ahmadkhorashadi/code_projects/codewise"
    test_file = "/Users/ahmadkhorashadi/code_projects/codewise/source/logic/analyze_cognitive_complexity.py"

    print(f"Testing parsing of: {test_file}")

    # First, try to parse the file directly
    try:
        with open(test_file, 'r') as f:
            content = f.read()
            print(f"File content length: {len(content)} characters")

        # Try basic AST parsing
        with open(test_file, 'r') as f:
            print("✓ Basic AST parsing successful")

        # Try our custom parsing
        result = collect_method_usages(root_dir, test_file)
        print(f"✓ Custom parsing successful, found {len(result)} methods")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_specific_file()
