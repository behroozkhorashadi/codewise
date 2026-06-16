"""
Batch experiment runner — processes all Python files across a repo.

Usage:
    python -m source.experiment.batch_experiment --repo datasets/repos/requests/src/requests
    python -m source.experiment.batch_experiment --repo datasets/repos/flask/src/flask
"""

import argparse
import json
from pathlib import Path

from source.experiment.experiment_runner import run_experiment


def get_processed_files(progress_file: Path) -> set:
    if progress_file.exists():
        with open(progress_file) as f:
            return set(json.load(f))
    return set()


def save_processed_file(progress_file: Path, file_path: str) -> None:
    processed = get_processed_files(progress_file)
    processed.add(file_path)
    with open(progress_file, "w") as f:
        json.dump(list(processed), f)


def run_batch(repo_dir: str, output_dir: str, min_call_sites: int) -> None:
    repo_path = Path(repo_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    progress_file = output_path / f"{repo_path.name}_progress.json"
    processed = get_processed_files(progress_file)

    py_files = [
        f for f in sorted(repo_path.rglob("*.py")) if not f.name.startswith("test_") and "__pycache__" not in str(f)
    ]

    print(f"\nRepo: {repo_dir}")
    print(f"Python files found: {len(py_files)}")
    print(f"Already processed: {len(processed)}")
    print(f"Remaining: {len(py_files) - len(processed)}\n")

    total_methods = 0

    for py_file in py_files:
        file_str = str(py_file)

        if file_str in processed:
            print(f"Skipping (already done): {py_file.name}")
            continue

        print(f"\n--- Processing: {py_file.name} ---")
        try:
            results = run_experiment(
                repo_dir=repo_dir,
                target_file=file_str,
                output_dir=output_dir,
                min_call_sites=min_call_sites,
            )
            total_methods += len(results)
            save_processed_file(progress_file, file_str)

            if not results:
                print(f"  No methods with {min_call_sites}+ call sites — skipping.")

        except Exception as e:
            print(f"  Error processing {py_file.name}: {e}")
            continue

    print(f"\n{'='*60}")
    print(f"Batch complete. Total methods evaluated: {total_methods}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Batch experiment runner")
    parser.add_argument("--repo", required=True, help="Root directory of the repo package")
    parser.add_argument("--output", default="outputs/experiment", help="Output directory")
    parser.add_argument("--min-call-sites", type=int, default=2, help="Minimum call sites required")
    args = parser.parse_args()

    run_batch(
        repo_dir=args.repo,
        output_dir=args.output,
        min_call_sites=args.min_call_sites,
    )


if __name__ == "__main__":
    main()
