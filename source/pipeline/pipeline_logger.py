"""
Pipeline logging system for tracking execution, API calls, and errors.

This module provides structured logging for the research pipeline.
"""

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


class PipelineLogger:
    """Centralized logging for the pipeline."""

    def __init__(
        self,
        log_dir: str = "logs",
        log_level: str = "INFO",
        enable_file_logging: bool = True,
    ):
        """
        Initialize pipeline logger.

        Args:
            log_dir: Directory to store log files.
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
            enable_file_logging: Whether to write logs to file.
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        self.logger = logging.getLogger("codewise_pipeline")
        self.logger.setLevel(getattr(logging, log_level))

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level))
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (rotating)
        if enable_file_logging:
            log_file = self.log_dir / "pipeline.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
            )
            file_handler.setLevel(getattr(logging, log_level))
            file_formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        self.api_call_log_file = self.log_dir / "api_calls.jsonl"
        self.logger.info("Pipeline logger initialized")

    def log_api_call(
        self,
        model_name: str,
        prompt_type: str,
        sample_id: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        status: str = "success",
        error_message: Optional[str] = None,
        cached: bool = False,
    ) -> None:
        """
        Log an API call with detailed metrics.

        Args:
            model_name: Name of the model (claude, gpt4, gemma)
            prompt_type: Type of prompt (critique, improve, recritique)
            sample_id: ID of the code sample
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost_usd: Estimated cost in USD
            status: Status of call (success, error)
            error_message: Error message if status is error
            cached: Whether response was cached
        """
        call_log = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model": model_name,
            "prompt_type": prompt_type,
            "sample_id": sample_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": cost_usd,
            "status": status,
            "error_message": error_message,
            "cached": cached,
        }

        # Log to console
        cache_note = " (cached)" if cached else ""
        self.logger.info(
            f"API Call: {model_name}/{prompt_type}/{sample_id} - "
            f"Tokens: {input_tokens+output_tokens} - Cost: ${cost_usd:.6f}{cache_note}"
        )

        # Log to file (JSONL format for easy parsing)
        try:
            with open(self.api_call_log_file, "a") as f:
                f.write(json.dumps(call_log) + "\n")
        except IOError as e:
            self.logger.error(f"Failed to write API call log: {e}")

    def log_sample_processing(
        self,
        sample_id: str,
        status: str,
        model_name: str,
        phase: str,
        message: str = "",
    ) -> None:
        """
        Log sample processing status.

        Args:
            sample_id: ID of the code sample
            status: Status (started, completed, failed)
            model_name: Name of the model
            phase: Phase of processing (critique, improve, recritique)
            message: Additional message
        """
        self.logger.info(f"Sample {sample_id} - {status.upper()} ({model_name}/{phase}): {message}")

    def log_error(self, sample_id: str, error: Exception) -> None:
        """
        Log an error during processing.

        Args:
            sample_id: ID of the code sample
            error: The exception that occurred
        """
        self.logger.error(f"Sample {sample_id} - Error: {str(error)}", exc_info=True)

    def get_api_call_summary(self) -> dict:
        """
        Parse API call log and return summary statistics.

        Returns:
            Dictionary with API call statistics
        """
        if not self.api_call_log_file.exists():
            return {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "cached_calls": 0,
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "by_model": {},
                "by_prompt_type": {},
            }

        stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "cached_calls": 0,
            "total_cost_usd": 0.0,
            "total_tokens": 0,
            "by_model": {},
            "by_prompt_type": {},
        }

        try:
            with open(self.api_call_log_file, "r") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        stats["total_calls"] += 1

                        if log_entry["status"] == "success":
                            stats["successful_calls"] += 1
                        else:
                            stats["failed_calls"] += 1

                        if log_entry.get("cached"):
                            stats["cached_calls"] += 1

                        stats["total_cost_usd"] += log_entry.get("cost_usd", 0)
                        stats["total_tokens"] += log_entry.get("total_tokens", 0)

                        # Track by model
                        model = log_entry["model"]
                        if model not in stats["by_model"]:
                            stats["by_model"][model] = {"calls": 0, "cost_usd": 0.0}
                        stats["by_model"][model]["calls"] += 1
                        stats["by_model"][model]["cost_usd"] += log_entry.get("cost_usd", 0)

                        # Track by prompt type
                        prompt_type = log_entry["prompt_type"]
                        if prompt_type not in stats["by_prompt_type"]:
                            stats["by_prompt_type"][prompt_type] = {"calls": 0, "cost_usd": 0.0}
                        stats["by_prompt_type"][prompt_type]["calls"] += 1
                        stats["by_prompt_type"][prompt_type]["cost_usd"] += log_entry.get("cost_usd", 0)

                    except json.JSONDecodeError:
                        continue
        except IOError as e:
            self.logger.error(f"Failed to read API call log: {e}")

        return stats


def get_logger(name: str = "codewise_pipeline") -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
