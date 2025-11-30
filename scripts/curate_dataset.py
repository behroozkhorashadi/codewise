"""
Script to help curate the dataset of code samples.

This script provides utilities for:
1. Downloading samples from GitHub
2. Generating samples using LLMs
3. Creating intentionally problematic samples
4. Organizing samples with metadata
"""

import csv
from pathlib import Path

# Dataset metadata structure
DATASET_METADATA_TEMPLATE = {
    "sample_id": "sample_001",
    "source": "github|llm_generated|intentionally_bad",
    "category": "utility|ml|web|data_processing|etc",
    "language": "python",
    "quality_expectation": "good|bad|average",
    "description": "Brief description of what the code does",
    "file_path": "path/to/sample.py",
    "source_url": "https://github.com/...",
    "author": "unknown",
    "license": "MIT|Apache|GPL|unknown",
    "lines_of_code": 50,
    "complexity": "low|medium|high",
    "notes": "Any special notes about this sample",
    "date_added": "2025-11-02",
}


class DatasetCurator:
    """Helper class for managing dataset curation."""

    def __init__(self, dataset_dir: str = "datasets/original_code"):
        """Initialize curator."""
        self.dataset_dir = Path(dataset_dir)
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.dataset_dir / "metadata.csv"

    def create_metadata_csv(self) -> None:
        """Create the metadata CSV file if it doesn't exist."""
        if not self.metadata_file.exists():
            with open(self.metadata_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=DATASET_METADATA_TEMPLATE.keys())
                writer.writeheader()
            print(f"✓ Created metadata file: {self.metadata_file}")
        else:
            print(f"ℹ Metadata file already exists: {self.metadata_file}")

    def add_sample(
        self,
        sample_id: str,
        code_content: str,
        source: str = "unknown",
        category: str = "utility",
        quality_expectation: str = "average",
        description: str = "",
        source_url: str = "",
        author: str = "unknown",
        license: str = "unknown",
        complexity: str = "medium",
        notes: str = "",
    ) -> None:
        """
        Add a code sample to the dataset.

        Args:
            sample_id: Unique identifier for the sample
            code_content: The Python code
            source: Source of the code
            category: Category of code
            quality_expectation: Expected quality level
            description: What the code does
            source_url: URL to original source
            author: Author name
            license: License type
            complexity: Code complexity level
            notes: Additional notes
        """
        from datetime import datetime

        # Save code file
        code_file = self.dataset_dir / f"{sample_id}.py"
        with open(code_file, "w") as f:
            f.write(code_content)

        # Calculate stats
        lines = len(code_content.strip().split("\n"))

        # Add to metadata
        metadata_row = {
            "sample_id": sample_id,
            "source": source,
            "category": category,
            "language": "python",
            "quality_expectation": quality_expectation,
            "description": description,
            "file_path": str(code_file),
            "source_url": source_url,
            "author": author,
            "license": license,
            "lines_of_code": lines,
            "complexity": complexity,
            "notes": notes,
            "date_added": datetime.now().isoformat(),
        }

        # Append to CSV
        with open(self.metadata_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=DATASET_METADATA_TEMPLATE.keys())
            writer.writerow(metadata_row)

        print(f"✓ Added sample: {sample_id} ({lines} lines)")

    def get_sample_count(self) -> int:
        """Get the number of samples in the dataset."""
        if not self.metadata_file.exists():
            return 0
        with open(self.metadata_file, "r") as f:
            return len(f.readlines()) - 1  # Subtract header

    def list_samples(self) -> None:
        """List all samples in the dataset."""
        if not self.metadata_file.exists():
            print("No samples in dataset yet.")
            return

        with open(self.metadata_file, "r") as f:
            reader = csv.DictReader(f)
            samples = list(reader)

        if not samples:
            print("No samples in dataset yet.")
            return

        print(f"\nDataset contains {len(samples)} samples:\n")
        print(f"{'ID':<15} {'Source':<15} {'Category':<15} {'Quality':<10} {'LOC':<6}")
        print("-" * 65)
        for sample in samples:
            print(
                f"{sample['sample_id']:<15} {sample['source']:<15} "
                f"{sample['category']:<15} {sample['quality_expectation']:<10} "
                f"{sample['lines_of_code']:<6}"
            )


if __name__ == "__main__":
    curator = DatasetCurator()
    curator.create_metadata_csv()

    # Example: Add a sample (for testing)
    print("\nTo add samples, use:")
    print("  curator.add_sample(sample_id='sample_001', code_content='...', ...)")
    print(f"\nCurrent sample count: {curator.get_sample_count()}")
