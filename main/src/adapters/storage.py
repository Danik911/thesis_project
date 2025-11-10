"""
Core storage provider protocol and factory for dual-mode storage.

Defines the contract for storage providers and provides a factory for creating
appropriate adapters based on configuration.
"""

from typing import Protocol


class StorageProvider(Protocol):
    """
    Protocol defining the contract for storage providers.

    All storage implementations (local, S3, etc.) must implement this interface
    to ensure consistent behavior across different storage backends.

    GAMP-5 Compliance:
    - All methods must preserve metadata for audit trail
    - All operations must be atomic where possible
    - All failures must raise explicit exceptions with diagnostic information

    NO FALLBACK LOGIC:
    - Never return success on failure
    - Never use default values to mask errors
    - Never silently catch exceptions
    """

    async def save_artifact(
        self,
        artifact_id: str,
        content: bytes,
        metadata: dict[str, str]
    ) -> str:
        """
        Save an artifact with associated metadata.

        Args:
            artifact_id: Unique identifier for the artifact (e.g., job_id, test_suite_id)
            content: Raw artifact content as bytes
            metadata: GAMP-5 compliant metadata dict with required fields:
                - gamp_category: str (e.g., "5")
                - job_id: str
                - created_at: str (UTC ISO 8601)
                - created_by: str (user or service identifier)
                - artifact_type: str (test_suite|urs|report)

        Returns:
            Storage URI (e.g., "file:///path/to/artifact" or "s3://bucket/key")

        Raises:
            ValueError: If metadata is invalid or missing required fields
            RuntimeError: If storage operation fails (with full diagnostic info)

        CRITICAL: NO FALLBACK LOGIC - All errors must propagate with full context
        """
        ...

    async def retrieve_artifact(self, artifact_id: str) -> bytes:
        """
        Retrieve artifact content by ID.

        Args:
            artifact_id: Unique identifier for the artifact

        Returns:
            Raw artifact content as bytes

        Raises:
            FileNotFoundError: If artifact does not exist
            RuntimeError: If retrieval operation fails (with full diagnostic info)

        CRITICAL: NO FALLBACK LOGIC - Never return empty/default content on error
        """
        ...

    async def generate_download_url(
        self,
        artifact_id: str,
        expiry_seconds: int = 86400  # 24 hours default
    ) -> str:
        """
        Generate a download URL for the artifact.

        For local storage: Returns file:// URI
        For S3 storage: Returns pre-signed HTTPS URL

        Args:
            artifact_id: Unique identifier for the artifact
            expiry_seconds: URL expiry time in seconds (S3 only, default 24 hours)

        Returns:
            Download URL (file:// for local, https:// for S3)

        Raises:
            FileNotFoundError: If artifact does not exist
            RuntimeError: If URL generation fails (with full diagnostic info)

        CRITICAL: NO FALLBACK LOGIC - Never return placeholder URLs on error
        """
        ...


class StorageFactory:
    """
    Factory for creating appropriate storage provider based on configuration.

    Implements dependency injection pattern to decouple storage logic from
    workflow implementation.
    """

    @staticmethod
    def create_storage_provider(storage_mode: str, **kwargs: str | int) -> StorageProvider:
        """
        Create storage provider based on mode.

        Args:
            storage_mode: "local" or "s3"
            **kwargs: Configuration parameters for the storage provider
                For local:
                    - base_path: str (default: "output")
                For S3:
                    - bucket: str (required)
                    - region: str (default: "eu-west-2")
                    - kms_key_id: str (optional)

        Returns:
            Configured storage provider instance

        Raises:
            ValueError: If storage_mode is invalid or required parameters missing

        CRITICAL: NO FALLBACK LOGIC - Never default to local on S3 configuration failure
        """
        # Import here to avoid circular dependencies
        from src.adapters.local_adapter import LocalStorageAdapter
        from src.adapters.s3_adapter import S3StorageAdapter

        if storage_mode == "local":
            base_path = kwargs.get("base_path", "output")
            return LocalStorageAdapter(base_path=str(base_path))
        if storage_mode == "s3":
            bucket = kwargs.get("bucket")
            if not bucket:
                raise ValueError(
                    "CRITICAL: S3 storage mode requires 'bucket' parameter\n"
                    "Configuration error - cannot create S3 storage provider without bucket name"
                )

            region = kwargs.get("region", "eu-west-2")
            kms_key_id = kwargs.get("kms_key_id")

            return S3StorageAdapter(
                bucket=str(bucket),
                region=str(region),
                kms_key_id=str(kms_key_id) if kms_key_id else None
            )
        raise ValueError(
            f"CRITICAL: Invalid storage mode '{storage_mode}'\n"
            f"Supported modes: 'local', 's3'\n"
            "Configuration error - check STORAGE_MODE environment variable"
        )
