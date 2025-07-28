"""
Cache Manager for Document Processing

This module provides caching functionality to avoid re-processing
documents and improve performance for the document processing pipeline.
"""

import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


class CacheManager:
    """
    Manages caching for document processing results.
    
    This class provides methods to cache and retrieve processed
    document data to avoid redundant processing.
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        cache_ttl_hours: int = 24 * 7  # 1 week default
    ):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache storage
            cache_ttl_hours: Cache time-to-live in hours
        """
        self.logger = logging.getLogger(__name__)

        # Setup cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".cache" / "pharma_doc_processor"

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=cache_ttl_hours)

        # Cache subdirectories
        self.parsed_dir = self.cache_dir / "parsed"
        self.processed_dir = self.cache_dir / "processed"
        self.metadata_dir = self.cache_dir / "metadata"

        for dir in [self.parsed_dir, self.processed_dir, self.metadata_dir]:
            dir.mkdir(exist_ok=True)

    def get_document_hash(self, file_path: Path) -> str:
        """Generate a unique hash for a document."""
        # Include file path, size, and modification time
        stat = file_path.stat()
        hash_data = f"{file_path}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.sha256(hash_data.encode()).hexdigest()

    def get_cache_path(
        self,
        document_hash: str,
        cache_type: str
    ) -> Path:
        """Get the cache file path for a document."""
        if cache_type == "parsed":
            return self.parsed_dir / f"{document_hash}.json"
        if cache_type == "processed":
            return self.processed_dir / f"{document_hash}.json"
        if cache_type == "metadata":
            return self.metadata_dir / f"{document_hash}.json"
        raise ValueError(f"Invalid cache type: {cache_type}")

    def is_cache_valid(self, cache_path: Path) -> bool:
        """Check if a cache file is still valid."""
        if not cache_path.exists():
            return False

        # Check age
        cache_age = datetime.now(UTC) - datetime.fromtimestamp(
            cache_path.stat().st_mtime, UTC
        )

        return cache_age < self.cache_ttl

    def save_to_cache(
        self,
        document_hash: str,
        data: dict[str, Any],
        cache_type: str
    ) -> None:
        """Save data to cache."""
        cache_path = self.get_cache_path(document_hash, cache_type)

        try:
            # Add cache metadata
            cache_data = {
                "data": data,
                "cache_metadata": {
                    "created_at": datetime.now(UTC).isoformat(),
                    "document_hash": document_hash,
                    "cache_type": cache_type
                }
            }

            with open(cache_path, "w") as f:
                json.dump(cache_data, f, indent=2, default=str)

            self.logger.debug(
                f"Saved {cache_type} cache for document {document_hash[:8]}..."
            )
        except Exception as e:
            self.logger.error(f"Failed to save cache: {e}")

    def load_from_cache(
        self,
        document_hash: str,
        cache_type: str
    ) -> dict[str, Any] | None:
        """Load data from cache if valid."""
        cache_path = self.get_cache_path(document_hash, cache_type)

        if not self.is_cache_valid(cache_path):
            return None

        try:
            with open(cache_path) as f:
                cache_data = json.load(f)

            self.logger.debug(
                f"Loaded {cache_type} cache for document {document_hash[:8]}..."
            )

            return cache_data["data"]
        except Exception as e:
            self.logger.error(f"Failed to load cache: {e}")
            return None

    def clear_cache(
        self,
        cache_type: str | None = None,
        older_than: timedelta | None = None
    ) -> int:
        """Clear cache files."""
        cleared_count = 0

        # Determine which directories to clear
        if cache_type:
            dirs = [self.get_cache_path("", cache_type).parent]
        else:
            dirs = [self.parsed_dir, self.processed_dir, self.metadata_dir]

        # Clear cache files
        for dir in dirs:
            for cache_file in dir.glob("*.json"):
                should_delete = True

                if older_than:
                    file_age = datetime.now(UTC) - datetime.fromtimestamp(
                        cache_file.stat().st_mtime, UTC
                    )
                    should_delete = file_age > older_than

                if should_delete:
                    try:
                        cache_file.unlink()
                        cleared_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to delete cache file: {e}")

        self.logger.info(f"Cleared {cleared_count} cache files")
        return cleared_count

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "total_size_mb": 0,
            "file_counts": {
                "parsed": 0,
                "processed": 0,
                "metadata": 0
            },
            "oldest_file": None,
            "newest_file": None
        }

        oldest_time = None
        newest_time = None

        # Gather statistics
        for cache_type, dir in [
            ("parsed", self.parsed_dir),
            ("processed", self.processed_dir),
            ("metadata", self.metadata_dir)
        ]:
            for cache_file in dir.glob("*.json"):
                # Count files
                stats["file_counts"][cache_type] += 1

                # Add to total size
                stats["total_size_mb"] += cache_file.stat().st_size / (1024 * 1024)

                # Track oldest/newest
                mtime = cache_file.stat().st_mtime
                if oldest_time is None or mtime < oldest_time:
                    oldest_time = mtime
                    stats["oldest_file"] = str(cache_file)
                if newest_time is None or mtime > newest_time:
                    newest_time = mtime
                    stats["newest_file"] = str(cache_file)

        # Add timestamps
        if oldest_time:
            stats["oldest_file_age_hours"] = (
                datetime.now(UTC) - datetime.fromtimestamp(oldest_time, UTC)
            ).total_seconds() / 3600

        if newest_time:
            stats["newest_file_age_hours"] = (
                datetime.now(UTC) - datetime.fromtimestamp(newest_time, UTC)
            ).total_seconds() / 3600

        return stats
