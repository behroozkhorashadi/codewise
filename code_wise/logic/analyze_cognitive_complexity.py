import ast
import os
import sys
from typing import List
from cognitive_complexity.api import get_cognitive_complexity


def analyze_cognitive_complexity(dir_path: str):
    file_list = get_list_of_python_files(dir_path)
    complexities = []
    for file_name in file_list:
        with open(file_name, "r") as f:
            file_content = f.read()
            calculate_cognitive_complexity(file_content, complexities, os.path.basename(file_name), file_name)

    complexities.sort(key=lambda x: x[1], reverse=True)

    # print(f"In file {file_path}:")
    for func_name, complexity, _file_name, file_path in complexities:
        print(f"{file_path}, {func_name}, {complexity}")


def calculate_cognitive_complexity(file_content: str, complexities: List, file_name: str, file_path: str):
    parsed_content = ast.parse(file_content)
    for node in ast.walk(parsed_content):
        if isinstance(node, ast.FunctionDef):
            complexity = get_cognitive_complexity(node)
            complexities.append((node.name, complexity, file_name, file_path))


def get_list_of_python_files(dir_path: str) -> List[str]:
    python_files = []
    for root, dirs, files in os.walk(dir_path):
        relative_path = os.path.relpath(root, dir_path)
        if relative_path.startswith("."):  # Skip hidden directories
            continue
        print(relative_path)
        for file in files:
            if file.endswith(".py") and not file.startswith("test_"):
                file_path = os.path.join(root, file)
                python_files.append(file_path)
    return python_files


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script_name.py <path_to_python_directory>")
    else:
        file_path = sys.argv[1]
        analyze_cognitive_complexity(file_path)
