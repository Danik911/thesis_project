"""
Local filesystem storage adapter implementation.

Provides GAMP-5 compliant local storage for development and testing environments.
All artifacts stored with accompanying metadata JSON files for audit trail.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles

logger = logging.getLogger(__name__)


class LocalStorageAdapter:
    """
    Local filesystem storage adapter with GAMP-5 compliant metadata.

    Stores artifacts in local filesystem with accompanying .meta.json files
    containing ALCOA+ compliant metadata for audit trail.

    Features:
    - Async file I/O using aiofiles
    - Cross-platform path handling (Windows/Linux)
    - Semaphore for concurrency control (max 10 concurrent operations)
    - Atomic metadata persistence alongside artifacts
    - Explicit error handling with full diagnostic information

    Directory Structure:
        base_path/
        ├── {artifact_id}.json          # Artifact content
        └── {artifact_id}.meta.json     # GAMP-5 metadata

    CRITICAL: NO FALLBACK LOGIC
    - All errors raise explicit exceptions with full context
    - Never return success on filesystem failure
    - Never use default/placeholder values
    """

    def __init__(self, base_path: str = "output") -> None:
        """
        Initialize local storage adapter.

        Args:
            base_path: Base directory for artifact storage (default: "output")

        Raises:
            RuntimeError: If base_path creation fails
        """
        self.base_path = Path(base_path).resolve()
        self._semaphore = asyncio.Semaphore(10)  # Limit concurrent file operations

        # Ensure base directory exists
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"LocalStorageAdapter initialized: base_path={self.base_path}")
        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: Failed to create storage directory\n"
                f"Path: {self.base_path}\n"
                f"Error: {e!s}\n"
                "Cannot proceed without writable storage directory"
            ) from e

    def _validate_metadata(self, metadata: dict[str, str]) -> None:
        """
        Validate GAMP-5 required metadata fields.

        Args:
            metadata: Metadata dictionary to validate

        Raises:
            ValueError: If required fields missing or invalid
        """
        required_fields = [
            "gamp_category",
            "job_id",
            "created_at",
            "created_by",
            "artifact_type"
        ]

        missing_fields = [field for field in required_fields if field not in metadata]
        if missing_fields:
            raise ValueError(
                f"CRITICAL: Missing required GAMP-5 metadata fields\n"
                f"Missing: {missing_fields}\n"
                f"Required: {required_fields}\n"
                f"Provided metadata: {metadata}\n"
                "Cannot store artifact without complete audit trail metadata"
            )

        # Validate GAMP category
        try:
            category = int(metadata["gamp_category"])
            if category not in [1, 3, 4, 5]:
                raise ValueError(f"Invalid GAMP category: {category}")
        except (ValueError, KeyError) as e:
            raise ValueError(
                f"CRITICAL: Invalid GAMP category in metadata\n"
                f"Value: {metadata.get('gamp_category', 'MISSING')}\n"
                f"Valid categories: 1, 3, 4, 5\n"
                f"Error: {e!s}"
            ) from e

        # Validate artifact type
        valid_types = ["test_suite", "urs", "report"]
        artifact_type = metadata.get("artifact_type")
        if artifact_type not in valid_types:
            raise ValueError(
                f"CRITICAL: Invalid artifact type in metadata\n"
                f"Value: {artifact_type}\n"
                f"Valid types: {valid_types}\n"
                "Artifact type required for compliance categorization"
            )

        # Validate timestamp format (ISO 8601 UTC)
        try:
            datetime.fromisoformat(metadata["created_at"].replace("Z", "+00:00"))
        except (ValueError, KeyError) as e:
            raise ValueError(
                f"CRITICAL: Invalid timestamp format in metadata\n"
                f"Value: {metadata.get('created_at', 'MISSING')}\n"
                f"Required format: ISO 8601 UTC (e.g., '2025-11-10T12:00:00Z')\n"
                f"Error: {e!s}"
            ) from e

    async def save_artifact(
        self,
        artifact_id: str,
        content: bytes,
        metadata: dict[str, str]
    ) -> str:
        """
        Save artifact to local filesystem with metadata.

        Args:
            artifact_id: Unique identifier (used as filename)
            content: Artifact content as bytes
            metadata: GAMP-5 compliant metadata

        Returns:
            file:// URI for the saved artifact

        Raises:
            ValueError: If metadata invalid
            RuntimeError: If file write fails
        """
        async with self._semaphore:
            # Validate metadata first (fail fast)
            self._validate_metadata(metadata)

            # Construct file paths
            # Sanitize artifact_id: replace backslashes with forward slashes (Windows safety)
            artifact_id_safe = artifact_id.replace("\\", "/")
            # CRITICAL: Preserve original file extension (don't append .json)
            # artifact_id may already include extension: "job_id/test_suite.yaml"
            # Result: /app/output/job_id/test_suite.yaml (not .yaml.json)
            artifact_path = self.base_path / artifact_id_safe
            metadata_path = self.base_path / f"{artifact_id_safe}.meta.json"

            try:
                # CRITICAL: Create parent directories if artifact_id contains slashes
                # Example: artifact_id="fa7a84d2.../test_suite.yaml" creates /app/output/fa7a84d2.../
                #
                # IMPORTANT: Check if path exists as FILE (not directory)
                # Python's mkdir(exist_ok=True) only ignores existing DIRECTORIES
                # If path exists as FILE, it raises FileExistsError regardless of exist_ok=True
                artifact_path_parent = artifact_path.parent

                if artifact_path_parent.exists() and not artifact_path_parent.is_dir():
                    raise RuntimeError(
                        f"CRITICAL: Cannot create directory - path exists as FILE\n"
                        f"Path: {artifact_path_parent}\n"
                        f"This is likely from a previous failed job attempt.\n"
                        f"Manual cleanup required: docker exec pharma-worker-dev rm -f {artifact_path_parent}\n"
                        f"Then retry the job."
                    )

                # Safe to create directory (path is directory or doesn't exist)
                artifact_path_parent.mkdir(parents=True, exist_ok=True)

                # Same check for metadata path
                metadata_path_parent = metadata_path.parent
                if metadata_path_parent != artifact_path_parent:
                    if metadata_path_parent.exists() and not metadata_path_parent.is_dir():
                        raise RuntimeError(
                            f"CRITICAL: Cannot create directory - path exists as FILE\n"
                            f"Path: {metadata_path_parent}\n"
                            f"Manual cleanup required: docker exec pharma-worker-dev rm -f {metadata_path_parent}"
                        )
                    metadata_path_parent.mkdir(parents=True, exist_ok=True)

                logger.debug(
                    f"Ensured directory exists for artifact: {artifact_path_parent}"
                )

                # Write artifact content
                async with aiofiles.open(artifact_path, "wb") as f:
                    await f.write(content)

                # Write metadata (with enhanced audit fields)
                from datetime import UTC
                enhanced_metadata = {
                    **metadata,
                    "storage_mode": "local",
                    "storage_path": str(artifact_path),
                    "storage_timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "file_size_bytes": len(content)
                }

                async with aiofiles.open(metadata_path, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(enhanced_metadata, indent=2))

                uri = artifact_path.as_uri()
                logger.info(
                    f"Artifact saved successfully: {artifact_id}\n"
                    f"Path: {artifact_path}\n"
                    f"Size: {len(content)} bytes\n"
                    f"URI: {uri}"
                )

                return uri

            except Exception as e:
                # Clean up partial writes
                for path in [artifact_path, metadata_path]:
                    if path.exists():
                        try:
                            path.unlink()
                        except Exception as cleanup_error:
                            logger.error(
                                f"Failed to clean up partial write: {path}\n"
                                f"Error: {cleanup_error}"
                            )

                raise RuntimeError(
                    f"CRITICAL: Failed to save artifact to local storage\n"
                    f"Artifact ID: {artifact_id}\n"
                    f"Path: {artifact_path}\n"
                    f"Error: {e!s}\n"
                    f"Storage directory: {self.base_path}\n"
                    "Check filesystem permissions and available disk space"
                ) from e

    async def retrieve_artifact(self, artifact_id: str) -> bytes:
        """
        Retrieve artifact from local filesystem.

        Args:
            artifact_id: Unique identifier

        Returns:
            Artifact content as bytes

        Raises:
            FileNotFoundError: If artifact does not exist
            RuntimeError: If read operation fails
        """
        async with self._semaphore:
            # CRITICAL: Preserve original extension (don't append .json)
            # Try artifact_id as-is first (new format without .json)
            artifact_id_safe = artifact_id.replace("\\", "/")
            artifact_path = self.base_path / artifact_id_safe

            # Backward compatibility: If file doesn't exist, try with .json appended (old format)
            if not artifact_path.exists():
                artifact_path_legacy = self.base_path / f"{artifact_id_safe}.json"
                if artifact_path_legacy.exists():
                    artifact_path = artifact_path_legacy
                    logger.debug(f"Using legacy .json path for backward compatibility: {artifact_path}")
                else:
                    raise FileNotFoundError(
                        f"CRITICAL: Artifact not found in local storage\n"
                        f"Artifact ID: {artifact_id}\n"
                        f"Tried paths: {self.base_path / artifact_id_safe}, {artifact_path_legacy}\n"
                        f"Storage directory: {self.base_path}\n"
                        "Artifact may have been deleted or never created"
                    )

            try:
                async with aiofiles.open(artifact_path, "rb") as f:
                    content = await f.read()

                logger.info(
                    f"Artifact retrieved successfully: {artifact_id}\n"
                    f"Path: {artifact_path}\n"
                    f"Size: {len(content)} bytes"
                )

                return content

            except Exception as e:
                raise RuntimeError(
                    f"CRITICAL: Failed to retrieve artifact from local storage\n"
                    f"Artifact ID: {artifact_id}\n"
                    f"Path: {artifact_path}\n"
                    f"Error: {e!s}\n"
                    "Check filesystem permissions and file integrity"
                ) from e

    async def generate_download_url(
        self,
        artifact_id: str,
        expiry_seconds: int = 86400
    ) -> str:
        """
        Generate file:// URL for local artifact.

        Args:
            artifact_id: Unique identifier
            expiry_seconds: Ignored for local storage (no expiry)

        Returns:
            file:// URI for the artifact

        Raises:
            FileNotFoundError: If artifact does not exist
        """
        artifact_path = self.base_path / f"{artifact_id}.json"

        if not artifact_path.exists():
            raise FileNotFoundError(
                f"CRITICAL: Cannot generate URL for non-existent artifact\n"
                f"Artifact ID: {artifact_id}\n"
                f"Expected path: {artifact_path}\n"
                f"Storage directory: {self.base_path}\n"
                "Artifact must exist before URL generation"
            )

        uri = artifact_path.as_uri()
        logger.info(f"Generated download URL for {artifact_id}: {uri}")

        return uri

    async def get_artifact_metadata(self, artifact_id: str) -> dict[str, Any]:
        """
        Retrieve metadata for an artifact.

        Args:
            artifact_id: Unique identifier

        Returns:
            Metadata dictionary

        Raises:
            FileNotFoundError: If metadata file does not exist
            RuntimeError: If metadata read/parse fails
        """
        async with self._semaphore:
            metadata_path = self.base_path / f"{artifact_id}.meta.json"

            if not metadata_path.exists():
                raise FileNotFoundError(
                    f"CRITICAL: Metadata not found for artifact\n"
                    f"Artifact ID: {artifact_id}\n"
                    f"Expected path: {metadata_path}\n"
                    f"Storage directory: {self.base_path}\n"
                    "Metadata required for GAMP-5 audit trail"
                )

            try:
                async with aiofiles.open(metadata_path, encoding="utf-8") as f:
                    content = await f.read()
                    metadata = json.loads(content)

                logger.info(f"Retrieved metadata for artifact: {artifact_id}")

                return metadata

            except Exception as e:
                raise RuntimeError(
                    f"CRITICAL: Failed to retrieve metadata from local storage\n"
                    f"Artifact ID: {artifact_id}\n"
                    f"Path: {metadata_path}\n"
                    f"Error: {e!s}\n"
                    "Metadata file may be corrupted or unreadable"
                ) from e
