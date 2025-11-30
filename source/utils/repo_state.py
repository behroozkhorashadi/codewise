"""Repository state tracking module for detecting code changes."""

import hashlib
import os
from pathlib import Path
from typing import Dict, Optional


class RepositoryState:
    """Tracks the state of a repository via file hashes."""

    def __init__(self):
        """Initialize the repository state tracker."""
        pass

    @staticmethod
    def _compute_file_hash(file_path: str) -> str:
        """
        Compute SHA256 hash of a file's contents.

        Args:
            file_path: Path to the file

        Returns:
            Hex digest of the file's SHA256 hash
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files efficiently
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except (IOError, OSError):
            # Return empty hash for unreadable files
            return ""

    @staticmethod
    def compute_repo_state(root_directory: str) -> Dict[str, str]:
        """
        Compute hash state of all Python files in a repository.

        Args:
            root_directory: Root directory of the repository

        Returns:
            Dictionary mapping file paths to their SHA256 hashes
        """
        file_hashes = {}

        for root, dirs, files in os.walk(root_directory):
            # Skip common directories that shouldn't affect analysis
            dirs[:] = [
                d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'venv', 'node_modules', '.codewise_cache']
            ]

            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    file_path = os.path.join(root, file)
                    file_hash = RepositoryState._compute_file_hash(file_path)
                    if file_hash:  # Only include successfully hashed files
                        file_hashes[file_path] = file_hash

        return file_hashes

    @staticmethod
    def compute_repo_hash(file_hashes: Dict[str, str]) -> str:
        """
        Compute a single hash representing the entire repository state.

        Args:
            file_hashes: Dictionary of file paths to file hashes

        Returns:
            Single hash representing the repository state
        """
        sha256_hash = hashlib.sha256()

        # Sort for consistent ordering
        for file_path in sorted(file_hashes.keys()):
            file_hash = file_hashes[file_path]
            # Combine file path and hash to ensure changes in file location or content are detected
            combined = f"{file_path}:{file_hash}".encode('utf-8')
            sha256_hash.update(combined)

        return sha256_hash.hexdigest()

    @staticmethod
    def detect_changes(old_state: Dict[str, str], new_state: Dict[str, str]) -> Dict[str, list]:
        """
        Detect changes between two repository states.

        Args:
            old_state: Previous repository state (file path -> hash)
            new_state: Current repository state (file path -> hash)

        Returns:
            Dictionary with 'added', 'removed', and 'modified' file lists
        """
        changes = {
            'added': [],
            'removed': [],
            'modified': [],
        }

        old_files = set(old_state.keys())
        new_files = set(new_state.keys())

        # Files that were added
        changes['added'] = list(new_files - old_files)

        # Files that were removed
        changes['removed'] = list(old_files - new_files)

        # Files that were modified (existed in both but hash changed)
        for file_path in old_files & new_files:
            if old_state[file_path] != new_state[file_path]:
                changes['modified'].append(file_path)

        return changes

    @staticmethod
    def has_changes(old_state: Dict[str, str], new_state: Dict[str, str]) -> bool:
        """
        Check if there are any changes between two repository states.

        Args:
            old_state: Previous repository state
            new_state: Current repository state

        Returns:
            True if any changes detected, False otherwise
        """
        changes = RepositoryState.detect_changes(old_state, new_state)
        return bool(changes['added'] or changes['removed'] or changes['modified'])
