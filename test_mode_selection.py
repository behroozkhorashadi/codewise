#!/usr/bin/env python3
"""
Test script to verify mode selection functionality
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from source.codewise_gui.codewise_ui_utils import collect_method_usages_entire_project


def test_entire_project_collection():
    """Test the entire project method collection function"""
    print("Testing entire project method collection...")

    # Test with the current project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))

    result = collect_method_usages_entire_project(project_dir)
    print(f"Found {len(result)} methods in the project")

    # Print some details about the methods found
    for method_key, (method_pointer, call_site_infos) in list(result.items())[:5]:
        print(f"  - {method_key}: {len(call_site_infos)} usage examples")

    assert len(result) > 0, "No methods found in the project"


if __name__ == "__main__":
    success = test_entire_project_collection()
    if success:
        print("✓ Mode selection functionality test passed!")
    else:
        print("✗ Mode selection functionality test failed!")
        sys.exit(1)
