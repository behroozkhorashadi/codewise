
import argparse

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect method usages in a given project directory and file.")
    parser.add_argument("root_directory", type=str, help="The root directory of the project.")
    parser.add_argument("file_path", type=str, help="The file path to analyze.")
    return parser.parse_args()