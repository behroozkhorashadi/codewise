"""
Batch Processor - Runs the entire pipeline on a dataset.

This module handles:
1. Loading all samples from a dataset
2. Coordinating sample processing across models
3. Tracking progress and state
4. CLI interface for pipeline execution
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from source.pipeline.cache_manager import CacheManager
from source.pipeline.model_api import ClaudeReviewer, GemmaReviewer, GPT4Reviewer
from source.pipeline.pipeline_logger import PipelineLogger
from source.pipeline.sample_processor import SampleProcessor


class BatchProcessor:
    """Manages batch processing of code samples."""

    def __init__(
        self,
        config_file: str = "config.yaml",
        dataset_dir: str = "datasets/original_code",
        output_dir: str = "outputs",
    ):
        """
        Initialize batch processor.

        Args:
            config_file: Path to config YAML file.
            dataset_dir: Directory containing code samples.
            output_dir: Directory for outputs.
        """
        self.config = self._load_config(config_file)
        self.dataset_dir = Path(dataset_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.logger = PipelineLogger(
            log_dir=self.config.get("logging", {}).get("log_dir", "logs"),
            log_level=self.config.get("logging", {}).get("level", "INFO"),
        )
        self.cache_manager = CacheManager(
            cache_dir=self.config.get("pipeline", {}).get("cache_path", "intermediate/cache")
        )
        self.sample_processor = SampleProcessor(output_dir=str(self.output_dir), logger_instance=self.logger)

        # Load metadata
        self.pipeline_metadata = self._load_pipeline_metadata()

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        with open(config_path) as f:
            return yaml.safe_load(f)

    def _load_pipeline_metadata(self) -> Dict[str, Any]:
        """Load pipeline metadata."""
        metadata_file = Path("intermediate/pipeline_metadata.json")
        if metadata_file.exists():
            with open(metadata_file) as f:
                return json.load(f)
        return {
            "pipeline_version": "1.0",
            "execution_state": {"status": "initialized"},
            "samples_processed": [],
        }

    def _save_pipeline_metadata(self) -> None:
        """Save pipeline metadata."""
        metadata_file = Path("intermediate/pipeline_metadata.json")
        with open(metadata_file, "w") as f:
            json.dump(self.pipeline_metadata, f, indent=2)

    def load_samples(self) -> List[Dict[str, str]]:
        """
        Load all code samples from the dataset directory.

        Returns:
            List of dicts with 'sample_id' and 'code'.
        """
        samples = []
        py_files = sorted(self.dataset_dir.glob("sample_*.py"))

        if not py_files:
            raise FileNotFoundError(f"No sample files found in {self.dataset_dir}")

        for py_file in py_files:
            sample_id = py_file.stem
            with open(py_file) as f:
                code = f.read()
            samples.append({"sample_id": sample_id, "code": code})

        return samples

    def initialize_models(self) -> List[tuple]:
        """
        Initialize the configured models.

        Returns:
            List of tuples (model_instance, model_name).
        """
        models = []
        models_config = self.config.get("models", {})

        # Claude
        if models_config.get("claude", {}).get("enabled"):
            api_key = self._get_api_key("ANTHROPIC_API_KEY")
            claude = ClaudeReviewer(
                api_key=api_key,
                model_name=models_config["claude"]["model_name"],
                cache_manager=self.cache_manager,
            )
            models.append((claude, "claude"))

        # GPT-4
        if models_config.get("gpt4", {}).get("enabled"):
            api_key = self._get_api_key("OPENAI_API_KEY")
            gpt4 = GPT4Reviewer(
                api_key=api_key,
                model_name=models_config["gpt4"]["model_name"],
                cache_manager=self.cache_manager,
            )
            models.append((gpt4, "gpt4"))

        # Gemma
        if models_config.get("gemma", {}).get("enabled"):
            base_url = models_config.get("gemma", {}).get("base_url", "http://localhost:11434")
            gemma = GemmaReviewer(
                model_name=models_config["gemma"]["model_name"],
                base_url=base_url,
                cache_manager=self.cache_manager,
            )
            models.append((gemma, "gemma"))

        if not models:
            raise ValueError("No models enabled in config")

        return models

    def _get_api_key(self, env_var: str) -> str:
        """Get API key from environment or .env file."""
        import os

        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(f"API key {env_var} not found in environment or .env file")
        return api_key

    def run(
        self,
        max_samples: Optional[int] = None,
        dry_run: bool = False,
        resume: bool = True,
    ) -> None:
        """
        Run the batch processing pipeline.

        Args:
            max_samples: Maximum number of samples to process (None = all).
            dry_run: If True, don't call LLM APIs.
            resume: If True, skip already processed samples.
        """
        print("\n" + "=" * 70)
        print("CODEWISE RESEARCH PIPELINE")
        print("=" * 70)

        # Load samples
        print(f"\nLoading samples from {self.dataset_dir}...")
        samples = self.load_samples()
        print(f"✓ Loaded {len(samples)} samples")

        # Filter already processed samples if resuming
        if resume:
            processed = self.pipeline_metadata.get("samples_processed", [])
            samples = [s for s in samples if s["sample_id"] not in processed]
            print(f"ℹ Resuming: {len(samples)} new samples to process")

        if max_samples:
            samples = samples[:max_samples]

        # Initialize models
        print(f"\nInitializing models...")
        models = self.initialize_models()
        print(f"✓ Initialized {len(models)} models: {', '.join(m[1] for m in models)}")

        if dry_run:
            print("\n⚠ DRY RUN MODE - No API calls will be made")

        # Run processing
        print(f"\nProcessing {len(samples)} samples...")
        results = self.sample_processor.process_multiple_samples(
            samples=samples,
            models=models,
            max_samples=max_samples,
            dry_run=dry_run,
        )

        # Update metadata
        for result in results:
            if result["status"] == "completed":
                sample_id = result.get("sample_id")
                if sample_id not in self.pipeline_metadata.get("samples_processed", []):
                    self.pipeline_metadata["samples_processed"].append(sample_id)

        self._save_pipeline_metadata()

        # Print summary
        self._print_summary(results)

    def _print_summary(self, results: List[Dict[str, Any]]) -> None:
        """Print summary of processing results."""
        completed = sum(1 for r in results if r["status"] == "completed")
        failed = sum(1 for r in results if r["status"] == "failed")

        print("\n" + "=" * 70)
        print("PROCESSING SUMMARY")
        print("=" * 70)
        print(f"Total samples processed: {len(results)}")
        print(f"Completed: {completed}")
        print(f"Failed: {failed}")

        if failed > 0:
            print("\nFailed samples:")
            for result in results:
                if result["status"] == "failed":
                    print(f"  - {result['sample_id']} ({result['model_name']})")

        # Print cache stats
        cache_stats = self.cache_manager.get_cache_stats()
        print(f"\nCache statistics:")
        print(f"  Cached files: {cache_stats['total_files']}")
        print(f"  Cache size: {cache_stats['total_size_mb']:.2f} MB")

        # Print API call summary
        api_summary = self.logger.get_api_call_summary()
        print(f"\nAPI call statistics:")
        print(f"  Total calls: {api_summary['total_calls']}")
        print(f"  Successful: {api_summary['successful_calls']}")
        print(f"  Cached: {api_summary['cached_calls']}")
        print(f"  Total cost: ${api_summary['total_cost_usd']:.2f}")

        print("\n" + "=" * 70)


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Codewise Research Pipeline")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--dataset",
        default="datasets/original_code",
        help="Path to dataset directory",
    )
    parser.add_argument(
        "--output",
        default="outputs",
        help="Path to output directory",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        help="Maximum samples to process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (no API calls)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Resume from previous run",
    )
    parser.add_argument(
        "--no-resume",
        action="store_false",
        dest="resume",
        help="Don't resume, process all samples",
    )

    args = parser.parse_args()

    try:
        processor = BatchProcessor(
            config_file=args.config,
            dataset_dir=args.dataset,
            output_dir=args.output,
        )
        processor.run(
            max_samples=args.max_samples,
            dry_run=args.dry_run,
            resume=args.resume,
        )
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
