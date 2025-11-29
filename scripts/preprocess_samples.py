"""
Preprocess code samples and generate AST metadata.

This script:
1. Validates all code samples (checks syntax)
2. Extracts AST information (functions, classes, variables)
3. Generates metadata JSON with code statistics
4. Flags any samples that fail validation
"""

import ast
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CodeMetadataExtractor:
    """Extract metadata from Python code using AST."""

    @staticmethod
    def extract_metadata(code: str, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from a Python code sample.

        Args:
            code: The Python source code
            file_path: Path to the file (for reference)

        Returns:
            Dictionary with metadata, or None if parsing fails
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return None

        metadata = {
            "file_path": str(file_path),
            "total_lines": len(code.split("\n")),
            "functions": [],
            "classes": [],
            "variables": [],
            "imports": [],
            "has_docstring": False,
            "complexity_metrics": {},
        }

        # Extract functions and classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_metadata = {
                    "name": node.name,
                    "lineno": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "has_docstring": ast.get_docstring(node) is not None,
                    "decorators": [ast.unparse(d) for d in node.decorator_list],
                }
                metadata["functions"].append(func_metadata)

            elif isinstance(node, ast.ClassDef):
                class_metadata = {
                    "name": node.name,
                    "lineno": node.lineno,
                    "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                    "has_docstring": ast.get_docstring(node) is not None,
                }
                metadata["classes"].append(class_metadata)

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    metadata["imports"].append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        metadata["imports"].append(f"{node.module}.{alias.name}")

            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if isinstance(node, ast.Name):
                    metadata["variables"].append(node.id)

        # Check module-level docstring
        module_docstring = ast.get_docstring(tree)
        if module_docstring:
            metadata["has_docstring"] = True

        # Extract complexity metrics
        metadata["complexity_metrics"] = CodeMetadataExtractor._calculate_complexity(tree)

        return metadata

    @staticmethod
    def _calculate_complexity(tree: ast.AST) -> Dict[str, int]:
        """Calculate basic code complexity metrics."""
        metrics = {
            "num_functions": 0,
            "num_classes": 0,
            "num_loops": 0,
            "num_conditionals": 0,
            "max_nesting_depth": 0,
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics["num_functions"] += 1
            elif isinstance(node, ast.ClassDef):
                metrics["num_classes"] += 1
            elif isinstance(node, (ast.For, ast.While)):
                metrics["num_loops"] += 1
            elif isinstance(node, (ast.If, ast.IfExp)):
                metrics["num_conditionals"] += 1

        return metrics

    @staticmethod
    def extract_variable_names(code: str) -> List[str]:
        """Extract all variable names from code."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    names.add(node.value.id)

        return sorted(list(names))


class DatasetPreprocessor:
    """Preprocess all samples in the dataset."""

    def __init__(
        self,
        dataset_dir: str = "datasets/original_code",
        output_file: str = "intermediate/parsed_code_metadata.json",
    ):
        """Initialize preprocessor."""
        self.dataset_dir = Path(dataset_dir)
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

    def preprocess_all(self) -> Dict[str, Any]:
        """Preprocess all .py files in the dataset."""
        logger.info(f"Starting preprocessing of dataset in {self.dataset_dir}")

        metadata_index = {
            "created_at": str(Path(__file__).stem),
            "total_samples": 0,
            "valid_samples": 0,
            "invalid_samples": 0,
            "samples": {},
            "errors": [],
        }

        # Find all .py files
        py_files = sorted(self.dataset_dir.glob("sample_*.py"))

        if not py_files:
            logger.warning(f"No sample files found in {self.dataset_dir}")
            return metadata_index

        logger.info(f"Found {len(py_files)} sample files")

        for py_file in py_files:
            sample_id = py_file.stem
            metadata_index["total_samples"] += 1

            try:
                with open(py_file, "r") as f:
                    code = f.read()

                # Extract metadata
                metadata = CodeMetadataExtractor.extract_metadata(code, py_file)

                if metadata is None:
                    logger.warning(f"Failed to parse {sample_id}")
                    metadata_index["invalid_samples"] += 1
                    metadata_index["errors"].append({"sample_id": sample_id, "error": "Syntax error"})
                else:
                    # Add variable names
                    metadata["variable_names"] = CodeMetadataExtractor.extract_variable_names(code)
                    metadata_index["samples"][sample_id] = metadata
                    metadata_index["valid_samples"] += 1
                    logger.info(f"✓ Processed {sample_id}")

            except Exception as e:
                logger.error(f"Error processing {sample_id}: {e}")
                metadata_index["invalid_samples"] += 1
                metadata_index["errors"].append({"sample_id": sample_id, "error": str(e)})

        # Write output
        logger.info(f"Writing metadata to {self.output_file}")
        with open(self.output_file, "w") as f:
            json.dump(metadata_index, f, indent=2)

        # Summary
        logger.info(
            f"\nPreprocessing complete:"
            f"\n  Total samples: {metadata_index['total_samples']}"
            f"\n  Valid samples: {metadata_index['valid_samples']}"
            f"\n  Invalid samples: {metadata_index['invalid_samples']}"
        )

        return metadata_index


def main():
    """Main entry point."""
    preprocessor = DatasetPreprocessor()
    result = preprocessor.preprocess_all()

    # Print summary
    print("\n" + "=" * 60)
    print("PREPROCESSING SUMMARY")
    print("=" * 60)
    print(f"Total samples: {result['total_samples']}")
    print(f"Valid samples: {result['valid_samples']}")
    print(f"Invalid samples: {result['invalid_samples']}")

    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  - {error['sample_id']}: {error['error']}")

    print(f"\nMetadata saved to: {preprocessor.output_file}")


if __name__ == "__main__":
    main()
