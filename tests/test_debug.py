#!/usr/bin/env python3

import os
import sys

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from source.logic.code_ast_parser import collect_method_usages


def test_method_collection():
    # Test with the current directory and a Python file
    root_dir = "/Users/ahmadkhorashadi/code_projects/codewise"
    test_file = "/Users/ahmadkhorashadi/code_projects/codewise/code_evaluator.py"

    print(f"Testing method collection...")
    print(f"Root directory: {root_dir}")
    print(f"Test file: {test_file}")

    try:
        result = collect_method_usages(root_dir, test_file)
        print(f"Found {len(result)} methods with usages")

        for method_pointer, call_site_infos in result.items():
            print(f"Method: {method_pointer.method_id.method_name}")
            print(f"  File: {method_pointer.file_path}")
            print(f"  Usages: {len(call_site_infos)}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_method_collection()
