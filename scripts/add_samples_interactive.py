#!/usr/bin/env python3
"""
Interactive script to add code samples to the dataset.

Usage:
    python scripts/add_samples_interactive.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.curate_dataset import DatasetCurator


def get_multiline_input(prompt: str) -> str:
    """Get multiline input from user (end with ctrl-d or empty line)."""
    print(prompt)
    print("(Enter code, then press Ctrl-D or type 'END' on a new line)")
    lines = []
    try:
        while True:
            line = input()
            if line == "END":
                break
            lines.append(line)
    except EOFError:
        pass
    return "\n".join(lines)


def main():
    """Main interactive loop."""
    curator = DatasetCurator()
    curator.create_metadata_csv()

    print("\n" + "=" * 60)
    print("Interactive Code Sample Curator")
    print("=" * 60)

    while True:
        print(f"\nCurrent samples: {curator.get_sample_count()}")
        print("\nOptions:")
        print("  1. Add a new sample")
        print("  2. List all samples")
        print("  3. Exit")

        choice = input("\nEnter choice (1-3): ").strip()

        if choice == "1":
            print("\n--- Add New Sample ---")

            sample_id = input("Sample ID (e.g., oss_001, llm_001, bad_001): ").strip()
            if not sample_id:
                print("Error: Sample ID is required")
                continue

            print("\nEnter source type:")
            print("  1. github (open-source)")
            print("  2. llm_generated")
            print("  3. intentionally_bad")
            source_choice = input("Enter choice (1-3): ").strip()
            source_map = {"1": "github", "2": "llm_generated", "3": "intentionally_bad"}
            source = source_map.get(source_choice, "unknown")

            print("\nEnter category:")
            print("  1. utility")
            print("  2. ml")
            print("  3. web")
            print("  4. data_processing")
            print("  5. other")
            category_choice = input("Enter choice (1-5): ").strip()
            category_map = {
                "1": "utility",
                "2": "ml",
                "3": "web",
                "4": "data_processing",
                "5": "other",
            }
            category = category_map.get(category_choice, "other")

            print("\nEnter quality expectation:")
            print("  1. good")
            print("  2. average")
            print("  3. bad")
            quality_choice = input("Enter choice (1-3): ").strip()
            quality_map = {"1": "good", "2": "average", "3": "bad"}
            quality = quality_map.get(quality_choice, "average")

            description = input("\nBrief description: ").strip()
            source_url = input("Source URL (optional): ").strip()
            author = input("Author (optional): ").strip()

            print("\nEnter complexity:")
            print("  1. low")
            print("  2. medium")
            print("  3. high")
            complexity_choice = input("Enter choice (1-3): ").strip()
            complexity_map = {"1": "low", "2": "medium", "3": "high"}
            complexity = complexity_map.get(complexity_choice, "medium")

            code_content = get_multiline_input("\nEnter code content:")
            notes = input("Additional notes (optional): ").strip()

            # Add the sample
            curator.add_sample(
                sample_id=sample_id,
                code_content=code_content,
                source=source,
                category=category,
                quality_expectation=quality,
                description=description,
                source_url=source_url,
                author=author,
                complexity=complexity,
                notes=notes,
            )

            print(f"✓ Sample {sample_id} added successfully!")

        elif choice == "2":
            curator.list_samples()

        elif choice == "3":
            print("\nGoodbye!")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
