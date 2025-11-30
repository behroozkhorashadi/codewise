"""
Sample Processor - Processes individual code samples through the pipeline.

This module handles:
1. Loading a code sample
2. Running critique → improve → re-critique workflow
3. Saving outputs at each stage
4. Error handling and logging
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from source.pipeline.model_api import CodeReviewModel
from source.pipeline.pipeline_logger import PipelineLogger, get_logger

logger = get_logger(__name__)


class SampleProcessor:
    """Processes a single code sample through the review pipeline."""

    def __init__(
        self,
        output_dir: str = "outputs",
        logger_instance: Optional[PipelineLogger] = None,
    ):
        """
        Initialize sample processor.

        Args:
            output_dir: Base directory for outputs.
            logger_instance: Pipeline logger instance.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger_instance or PipelineLogger()

    def process_sample(
        self,
        sample_id: str,
        code: str,
        model: CodeReviewModel,
        model_name: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a single sample through the complete pipeline.

        Args:
            sample_id: Unique identifier for the sample.
            code: The Python code to process.
            model: The code review model instance.
            model_name: Name of the model (for logging/organization).
            dry_run: If True, don't actually call the model API.

        Returns:
            Dictionary with results from all phases.
        """
        logger.info(f"Starting processing of sample {sample_id} with {model_name}")

        result = {
            "sample_id": sample_id,
            "model_name": model_name,
            "status": "processing",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "phases": {},
            "errors": [],
        }

        # Create model-specific output directory
        model_output_dir = self.output_dir / model_name
        model_output_dir.mkdir(parents=True, exist_ok=True)

        # Phase 1: Critique
        logger.info(f"Phase 1/3: Critiquing {sample_id}")
        self.logger.log_sample_processing(sample_id, "started", model_name, "critique")

        try:
            if dry_run:
                critique_result = {"status": "skipped", "reason": "dry_run"}
            else:
                critique_result = model.critique(code)

            # Save critique
            critique_file = model_output_dir / f"critique_{sample_id}.json"
            self._save_result(critique_file, critique_result)
            result["phases"]["critique"] = {
                "status": "completed",
                "output_file": str(critique_file),
                "result": critique_result,
            }
            self.logger.log_sample_processing(sample_id, "completed", model_name, "critique", "Critique generated")

        except Exception as e:
            logger.error(f"Error during critique of {sample_id}: {e}")
            self.logger.log_error(sample_id, e)
            result["errors"].append({"phase": "critique", "error": str(e)})
            result["status"] = "failed"
            return result

        # Phase 2: Improve
        logger.info(f"Phase 2/3: Improving {sample_id}")
        self.logger.log_sample_processing(sample_id, "started", model_name, "improve")

        try:
            if dry_run:
                improve_result = {"status": "skipped", "reason": "dry_run"}
            else:
                improve_result = model.improve(code, critique_result)

            # Save improved code
            improve_file = model_output_dir / f"improved_{sample_id}.json"
            self._save_result(improve_file, improve_result)
            result["phases"]["improve"] = {
                "status": "completed",
                "output_file": str(improve_file),
                "result": improve_result,
            }
            self.logger.log_sample_processing(sample_id, "completed", model_name, "improve", "Code improved")

        except Exception as e:
            logger.error(f"Error during improvement of {sample_id}: {e}")
            self.logger.log_error(sample_id, e)
            result["errors"].append({"phase": "improve", "error": str(e)})
            result["status"] = "failed"
            return result

        # Phase 3: Re-critique
        logger.info(f"Phase 3/3: Re-critiquing {sample_id}")
        self.logger.log_sample_processing(sample_id, "started", model_name, "recritique")

        try:
            # Extract improved code from improve_result
            if "refactored_code" in improve_result:
                improved_code = improve_result["refactored_code"]
            elif dry_run:
                improved_code = code  # Use original for dry run
            else:
                logger.warning(f"Could not extract improved code for {sample_id}")
                improved_code = code

            if dry_run:
                recritique_result = {"status": "skipped", "reason": "dry_run"}
            else:
                recritique_result = model.recritique(code, improved_code, critique_result)

            # Save re-critique
            recritique_file = model_output_dir / f"recritique_{sample_id}.json"
            self._save_result(recritique_file, recritique_result)
            result["phases"]["recritique"] = {
                "status": "completed",
                "output_file": str(recritique_file),
                "result": recritique_result,
            }
            self.logger.log_sample_processing(sample_id, "completed", model_name, "recritique", "Re-critique generated")

        except Exception as e:
            logger.error(f"Error during re-critique of {sample_id}: {e}")
            self.logger.log_error(sample_id, e)
            result["errors"].append({"phase": "recritique", "error": str(e)})
            result["status"] = "failed"
            return result

        # Mark as successful
        result["status"] = "completed"
        logger.info(f"✓ Successfully processed sample {sample_id}")

        # Save summary
        summary_file = model_output_dir / f"summary_{sample_id}.json"
        self._save_result(summary_file, result)

        return result

    def _save_result(self, file_path: Path, result: Dict[str, Any]) -> None:
        """
        Save a result to a JSON file.

        Args:
            file_path: Path to save the file.
            result: The result dictionary.
        """
        try:
            with open(file_path, "w") as f:
                json.dump(result, f, indent=2)
            logger.debug(f"Saved result to {file_path}")
        except IOError as e:
            logger.error(f"Failed to save result to {file_path}: {e}")

    def process_multiple_samples(
        self,
        samples: List[Dict[str, str]],
        models: List[tuple],
        max_samples: Optional[int] = None,
        dry_run: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Process multiple samples across multiple models.

        Args:
            samples: List of dicts with 'sample_id' and 'code'.
            models: List of tuples (model_instance, model_name).
            max_samples: Max samples to process (None = all).
            dry_run: If True, don't call APIs.

        Returns:
            List of results from all samples.
        """
        results = []
        sample_count = min(len(samples), max_samples) if max_samples else len(samples)

        logger.info(f"Processing {sample_count} samples across {len(models)} models")

        for i, sample in enumerate(samples[:sample_count]):
            sample_id = sample["sample_id"]
            code = sample["code"]

            logger.info(f"\n--- Processing sample {i+1}/{sample_count}: {sample_id} ---")

            for model_instance, model_name in models:
                try:
                    result = self.process_sample(
                        sample_id=sample_id,
                        code=code,
                        model=model_instance,
                        model_name=model_name,
                        dry_run=dry_run,
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process {sample_id} with {model_name}: {e}")
                    results.append(
                        {
                            "sample_id": sample_id,
                            "model_name": model_name,
                            "status": "failed",
                            "error": str(e),
                        }
                    )

        logger.info(f"\nCompleted processing of {len(results)} sample-model combinations")
        return results
