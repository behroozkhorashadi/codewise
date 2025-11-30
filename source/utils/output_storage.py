"""Output storage and caching module for Codewise analysis results."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from source.utils.repo_state import RepositoryState


class AnalysisOutputStorage:
    """Handles saving and loading analysis results in structured JSON format."""

    DEFAULT_OUTPUT_DIR = ".codewise_cache"

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the output storage.

        Args:
            output_dir: Directory to store analysis results. Defaults to .codewise_cache
        """
        self.output_dir = output_dir or self.DEFAULT_OUTPUT_DIR
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Ensure output directory exists."""
        Path(self.output_dir).mkdir(exist_ok=True)

    def get_analysis_filename(self, root_directory: str, file_path: Optional[str], analysis_mode: str) -> str:
        """
        Generate a unique filename for the analysis output.

        Args:
            root_directory: Root directory being analyzed
            file_path: File path for single file mode (None for project mode)
            analysis_mode: Either "single_file" or "entire_project"

        Returns:
            Filename for the analysis
        """
        if analysis_mode == "single_file" and file_path:
            # Use relative path from root directory for unique naming
            rel_path = os.path.relpath(file_path, root_directory)
            # Replace path separators with underscores and remove .py extension
            safe_name = rel_path.replace(os.sep, "_").replace(".py", "")
            return f"{safe_name}_single_file.json"
        else:
            # Use root directory basename for entire project analysis
            dir_basename = os.path.basename(root_directory.rstrip(os.sep))
            return f"{dir_basename}_entire_project.json"

    def get_analysis_output_path(self, root_directory: str, file_path: Optional[str], analysis_mode: str) -> str:
        """Get the full path to the analysis output file."""
        filename = self.get_analysis_filename(root_directory, file_path, analysis_mode)
        return os.path.join(self.output_dir, filename)

    def output_exists(self, root_directory: str, file_path: Optional[str], analysis_mode: str) -> bool:
        """
        Check if analysis output already exists.

        Args:
            root_directory: Root directory being analyzed
            file_path: File path for single file mode (None for project mode)
            analysis_mode: Either "single_file" or "entire_project"

        Returns:
            True if output file exists, False otherwise
        """
        output_path = self.get_analysis_output_path(root_directory, file_path, analysis_mode)
        return os.path.exists(output_path)

    def load_analysis_output(
        self, root_directory: str, file_path: Optional[str], analysis_mode: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load existing analysis output from file.

        Args:
            root_directory: Root directory being analyzed
            file_path: File path for single file mode (None for project mode)
            analysis_mode: Either "single_file" or "entire_project"

        Returns:
            Loaded analysis data or None if file doesn't exist
        """
        output_path = self.get_analysis_output_path(root_directory, file_path, analysis_mode)

        if not os.path.exists(output_path):
            return None

        try:
            with open(output_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading analysis output from {output_path}: {e}")
            return None

    def save_analysis_output(
        self,
        root_directory: str,
        file_path: Optional[str],
        analysis_mode: str,
        analysis_results: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save analysis results to a structured JSON file.

        Args:
            root_directory: Root directory being analyzed
            file_path: File path for single file mode (None for project mode)
            analysis_mode: Either "single_file" or "entire_project"
            analysis_results: The analysis results to save
            metadata: Optional metadata to include (timestamp, version, etc.)

        Returns:
            Path to the saved file
        """
        output_path = self.get_analysis_output_path(root_directory, file_path, analysis_mode)

        # Compute repository state at time of analysis
        repo_state = RepositoryState.compute_repo_state(root_directory)
        repo_hash = RepositoryState.compute_repo_hash(repo_state)

        # Build complete output structure
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "analysis_mode": analysis_mode,
            "root_directory": root_directory,
            "file_path": file_path,
            "metadata": metadata or {},
            "repo_hash": repo_hash,  # Hash of repository state at time of analysis
            "repo_state": repo_state,  # Detailed file hashes for change detection
            "results": analysis_results,
        }

        # Ensure directory exists
        self._ensure_output_dir()

        # Write to file
        try:
            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)
        except IOError as e:
            print(f"Error saving analysis output to {output_path}: {e}")
            raise

        return output_path

    def delete_analysis_output(self, root_directory: str, file_path: Optional[str], analysis_mode: str) -> bool:
        """
        Delete analysis output file.

        Args:
            root_directory: Root directory being analyzed
            file_path: File path for single file mode (None for project mode)
            analysis_mode: Either "single_file" or "entire_project"

        Returns:
            True if file was deleted, False if it didn't exist
        """
        output_path = self.get_analysis_output_path(root_directory, file_path, analysis_mode)

        if not os.path.exists(output_path):
            return False

        try:
            os.remove(output_path)
            return True
        except OSError as e:
            print(f"Error deleting analysis output {output_path}: {e}")
            return False

    def get_all_cached_analyses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all cached analyses.

        Returns:
            Dictionary mapping filenames to their metadata
        """
        cached = {}

        if not os.path.exists(self.output_dir):
            return cached

        for filename in os.listdir(self.output_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.output_dir, filename)
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        cached[filename] = {
                            "timestamp": data.get("timestamp"),
                            "analysis_mode": data.get("analysis_mode"),
                            "root_directory": data.get("root_directory"),
                            "file_path": data.get("file_path"),
                            "result_count": len(data.get("results", [])),
                        }
                except (json.JSONDecodeError, IOError):
                    pass

        return cached

    def detect_repo_changes(
        self, root_directory: str, file_path: Optional[str], analysis_mode: str
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if repository has changed since cached analysis was created.

        Args:
            root_directory: Root directory being analyzed
            file_path: File path for single file mode (None for project mode)
            analysis_mode: Either "single_file" or "entire_project"

        Returns:
            Dictionary with change information if changes detected, None if no cached data or no changes
        """
        # Load cached data
        cached_data = self.load_analysis_output(root_directory, file_path, analysis_mode)
        if not cached_data:
            return None

        # Get cached repository state
        cached_repo_state = cached_data.get("repo_state", {})
        if not cached_repo_state:
            # Old format without repo state, assume no changes can be detected
            return None

        # Compute current repository state
        current_repo_state = RepositoryState.compute_repo_state(root_directory)

        # Detect changes
        changes = RepositoryState.detect_changes(cached_repo_state, current_repo_state)

        # If there are any changes, return the change information
        if changes['added'] or changes['removed'] or changes['modified']:
            return {
                'has_changes': True,
                'changes': changes,
                'cached_timestamp': cached_data.get('timestamp'),
            }

        return None
