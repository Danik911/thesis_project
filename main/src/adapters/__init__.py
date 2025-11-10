"""
Storage adapter module for dual-mode (local/S3) artifact storage.

Provides GAMP-5 compliant storage abstraction for pharmaceutical test generation
artifacts with support for both local filesystem (development) and AWS S3 (production).
"""

from src.adapters.local_adapter import LocalStorageAdapter
from src.adapters.s3_adapter import S3StorageAdapter
from src.adapters.storage import StorageFactory, StorageProvider

__all__ = [
    "LocalStorageAdapter",
    "S3StorageAdapter",
    "StorageFactory",
    "StorageProvider",
]
