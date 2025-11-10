"""
AWS S3 storage adapter implementation.

Provides GAMP-5 compliant S3 storage for production environments with:
- SSE-KMS encryption for data at rest
- Object metadata for audit trail (ALCOA+ compliant)
- Pre-signed URLs for secure artifact retrieval
- Semaphore-based concurrency control
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from aiobotocore.session import get_session
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3StorageAdapter:
    """
    AWS S3 storage adapter with GAMP-5 compliance features.

    Features:
    - True async S3 operations using aiobotocore
    - SSE-KMS encryption for all artifacts
    - Object metadata for ALCOA+ audit trail (max 2KB)
    - Pre-signed URLs with configurable expiry (default 24 hours)
    - Semaphore for concurrency control (max 5 concurrent S3 operations)
    - Explicit error handling with full AWS diagnostic information

    S3 Key Structure:
        test-suites/{job_id}.json          # Deterministic naming for audit trail

    CRITICAL: NO FALLBACK LOGIC
    - All AWS errors propagate with full context
    - Never return success on S3 API failure
    - Never fallback to local storage on S3 unavailability
    - Strong consistency guarantees (S3 native)
    """

    def __init__(
        self,
        bucket: str,
        region: str = "eu-west-2",
        kms_key_id: str | None = None
    ) -> None:
        """
        Initialize S3 storage adapter.

        Args:
            bucket: S3 bucket name for artifact storage
            region: AWS region (default: eu-west-2 for EU data residency)
            kms_key_id: KMS key ARN/ID for SSE-KMS encryption (optional)

        Raises:
            ValueError: If bucket name is invalid
        """
        if not bucket:
            raise ValueError(
                "CRITICAL: S3 bucket name is required\n"
                "Configuration error - cannot initialize S3 adapter without bucket"
            )

        self.bucket = bucket
        self.region = region
        self.kms_key_id = kms_key_id
        self.session = get_session()
        self._semaphore = asyncio.Semaphore(5)  # Limit concurrent S3 operations

        logger.info(
            f"S3StorageAdapter initialized:\n"
            f"Bucket: {self.bucket}\n"
            f"Region: {self.region}\n"
            f"KMS Key ID: {self.kms_key_id or 'Default (aws/s3)'}"
        )

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

    def _format_metadata(self, metadata: dict[str, str]) -> dict[str, str]:
        """
        Format metadata for S3 object metadata (HTTP headers).

        S3 object metadata constraints:
        - Max 2KB total size
        - Keys and values must be ASCII
        - Keys prefixed with 'x-amz-meta-' by AWS

        Args:
            metadata: Original metadata dictionary

        Returns:
            Formatted metadata suitable for S3

        Raises:
            ValueError: If metadata exceeds 2KB limit
        """
        # Add storage-specific fields
        from datetime import UTC
        formatted = {
            **metadata,
            "storage-mode": "s3",
            "storage-bucket": self.bucket,
            "storage-region": self.region,
            "storage-timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z")
        }

        # Validate size (S3 limit: 2KB)
        metadata_str = json.dumps(formatted)
        metadata_size = len(metadata_str.encode("utf-8"))

        if metadata_size > 2048:  # 2KB limit
            raise ValueError(
                f"CRITICAL: Metadata exceeds S3 2KB limit\n"
                f"Size: {metadata_size} bytes\n"
                f"Limit: 2048 bytes\n"
                f"Metadata: {formatted}\n"
                "Reduce metadata field sizes or move extended data to artifact body"
            )

        return formatted

    def _build_s3_key(self, artifact_id: str, artifact_type: str) -> str:
        """
        Build deterministic S3 key for artifact.

        Args:
            artifact_id: Unique identifier (typically job_id)
            artifact_type: Type of artifact (test_suite, urs, report)

        Returns:
            S3 key path (e.g., "test-suites/job-123.json")
        """
        # Deterministic naming for audit trail and compliance
        type_prefix = {
            "test_suite": "test-suites",
            "urs": "urs-documents",
            "report": "reports"
        }.get(artifact_type, "artifacts")

        return f"{type_prefix}/{artifact_id}.json"

    async def save_artifact(
        self,
        artifact_id: str,
        content: bytes,
        metadata: dict[str, str]
    ) -> str:
        """
        Save artifact to S3 with SSE-KMS encryption and metadata.

        Args:
            artifact_id: Unique identifier
            content: Artifact content as bytes
            metadata: GAMP-5 compliant metadata

        Returns:
            s3:// URI for the saved artifact

        Raises:
            ValueError: If metadata invalid or exceeds size limit
            RuntimeError: If S3 put_object fails
        """
        async with self._semaphore:
            # Validate metadata first (fail fast)
            self._validate_metadata(metadata)

            # Format and validate metadata size
            formatted_metadata = self._format_metadata(metadata)

            # Build S3 key
            s3_key = self._build_s3_key(artifact_id, metadata["artifact_type"])

            try:
                async with self.session.create_client(
                    "s3",
                    region_name=self.region
                ) as client:
                    # Prepare put_object arguments
                    put_kwargs = {
                        "Bucket": self.bucket,
                        "Key": s3_key,
                        "Body": content,
                        "ServerSideEncryption": "aws:kms",
                        "Metadata": formatted_metadata,
                        "ContentType": "application/json"
                    }

                    # Add KMS key if specified
                    if self.kms_key_id:
                        put_kwargs["SSEKMSKeyId"] = self.kms_key_id

                    # Upload to S3
                    response = await client.put_object(**put_kwargs)

                    uri = f"s3://{self.bucket}/{s3_key}"
                    logger.info(
                        f"Artifact saved to S3 successfully:\n"
                        f"Artifact ID: {artifact_id}\n"
                        f"S3 URI: {uri}\n"
                        f"Size: {len(content)} bytes\n"
                        f"ETag: {response.get('ETag', 'N/A')}\n"
                        f"Encryption: SSE-KMS"
                    )

                    return uri

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                error_message = e.response.get("Error", {}).get("Message", str(e))

                raise RuntimeError(
                    f"CRITICAL: S3 put_object failed\n"
                    f"Artifact ID: {artifact_id}\n"
                    f"S3 Key: {s3_key}\n"
                    f"Bucket: {self.bucket}\n"
                    f"Region: {self.region}\n"
                    f"AWS Error Code: {error_code}\n"
                    f"AWS Error Message: {error_message}\n"
                    "Check AWS credentials, bucket permissions, and KMS key access"
                ) from e

            except Exception as e:
                raise RuntimeError(
                    f"CRITICAL: Unexpected error during S3 artifact save\n"
                    f"Artifact ID: {artifact_id}\n"
                    f"S3 Key: {s3_key}\n"
                    f"Bucket: {self.bucket}\n"
                    f"Error: {e!s}\n"
                    "Check network connectivity and AWS service availability"
                ) from e

    async def retrieve_artifact(self, artifact_id: str) -> bytes:
        """
        Retrieve artifact from S3.

        Note: Requires artifact_type to build S3 key. For retrieval without type,
        use get_artifact_metadata first to determine type, or try common types.

        Args:
            artifact_id: Unique identifier

        Returns:
            Artifact content as bytes

        Raises:
            FileNotFoundError: If artifact does not exist in S3
            RuntimeError: If S3 get_object fails
        """
        async with self._semaphore:
            # Try common artifact types (test_suite most common)
            attempted_keys = []

            for artifact_type in ["test_suite", "urs", "report"]:
                s3_key = self._build_s3_key(artifact_id, artifact_type)
                attempted_keys.append(s3_key)

                try:
                    async with self.session.create_client(
                        "s3",
                        region_name=self.region
                    ) as client:
                        response = await client.get_object(
                            Bucket=self.bucket,
                            Key=s3_key
                        )

                        # Read body content
                        content = await response["Body"].read()

                        logger.info(
                            f"Artifact retrieved from S3 successfully:\n"
                            f"Artifact ID: {artifact_id}\n"
                            f"S3 Key: {s3_key}\n"
                            f"Size: {len(content)} bytes"
                        )

                        return content

                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")
                    if error_code == "NoSuchKey":
                        # Try next artifact type
                        continue
                    # Other S3 errors (permission, etc.)
                    raise RuntimeError(
                        f"CRITICAL: S3 get_object failed\n"
                        f"Artifact ID: {artifact_id}\n"
                        f"S3 Key: {s3_key}\n"
                        f"Bucket: {self.bucket}\n"
                        f"AWS Error Code: {error_code}\n"
                        f"AWS Error Message: {e.response.get('Error', {}).get('Message', str(e))}\n"
                        "Check AWS credentials and bucket permissions"
                    ) from e

            # If we get here, artifact not found in any location
            raise FileNotFoundError(
                f"CRITICAL: Artifact not found in S3\n"
                f"Artifact ID: {artifact_id}\n"
                f"Bucket: {self.bucket}\n"
                f"Attempted keys: {attempted_keys}\n"
                "Artifact may have been deleted or never created"
            )

    async def generate_download_url(
        self,
        artifact_id: str,
        expiry_seconds: int = 86400
    ) -> str:
        """
        Generate pre-signed S3 URL for artifact download.

        Args:
            artifact_id: Unique identifier
            expiry_seconds: URL expiry time in seconds (default 24 hours)

        Returns:
            Pre-signed HTTPS URL

        Raises:
            FileNotFoundError: If artifact does not exist
            RuntimeError: If URL generation fails
        """
        async with self._semaphore:
            # Try common artifact types
            attempted_keys = []

            for artifact_type in ["test_suite", "urs", "report"]:
                s3_key = self._build_s3_key(artifact_id, artifact_type)
                attempted_keys.append(s3_key)

                try:
                    async with self.session.create_client(
                        "s3",
                        region_name=self.region
                    ) as client:
                        # Verify object exists
                        await client.head_object(Bucket=self.bucket, Key=s3_key)

                        # Generate pre-signed URL
                        presigned_url = await client.generate_presigned_url(
                            ClientMethod="get_object",
                            Params={"Bucket": self.bucket, "Key": s3_key},
                            ExpiresIn=expiry_seconds
                        )

                        logger.info(
                            f"Generated pre-signed URL for artifact:\n"
                            f"Artifact ID: {artifact_id}\n"
                            f"S3 Key: {s3_key}\n"
                            f"Expiry: {expiry_seconds} seconds"
                        )

                        return presigned_url

                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")
                    if error_code in ["NoSuchKey", "404"]:
                        # Try next artifact type
                        continue
                    # Other S3 errors
                    raise RuntimeError(
                        f"CRITICAL: Failed to generate pre-signed URL\n"
                        f"Artifact ID: {artifact_id}\n"
                        f"S3 Key: {s3_key}\n"
                        f"Bucket: {self.bucket}\n"
                        f"AWS Error Code: {error_code}\n"
                        f"AWS Error Message: {e.response.get('Error', {}).get('Message', str(e))}"
                    ) from e

            # If we get here, artifact not found
            raise FileNotFoundError(
                f"CRITICAL: Cannot generate URL for non-existent artifact\n"
                f"Artifact ID: {artifact_id}\n"
                f"Bucket: {self.bucket}\n"
                f"Attempted keys: {attempted_keys}\n"
                "Artifact must exist before URL generation"
            )

    async def get_artifact_metadata(self, artifact_id: str) -> dict[str, Any]:
        """
        Retrieve metadata for an artifact from S3 object metadata.

        Args:
            artifact_id: Unique identifier

        Returns:
            Metadata dictionary

        Raises:
            FileNotFoundError: If artifact does not exist
            RuntimeError: If metadata retrieval fails
        """
        async with self._semaphore:
            # Try common artifact types
            attempted_keys = []

            for artifact_type in ["test_suite", "urs", "report"]:
                s3_key = self._build_s3_key(artifact_id, artifact_type)
                attempted_keys.append(s3_key)

                try:
                    async with self.session.create_client(
                        "s3",
                        region_name=self.region
                    ) as client:
                        response = await client.head_object(
                            Bucket=self.bucket,
                            Key=s3_key
                        )

                        # Extract metadata from response
                        metadata = response.get("Metadata", {})

                        logger.info(f"Retrieved metadata for artifact: {artifact_id}")

                        return metadata

                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")
                    if error_code in ["NoSuchKey", "404"]:
                        # Try next artifact type
                        continue
                    raise RuntimeError(
                        f"CRITICAL: Failed to retrieve metadata from S3\n"
                        f"Artifact ID: {artifact_id}\n"
                        f"S3 Key: {s3_key}\n"
                        f"Bucket: {self.bucket}\n"
                        f"AWS Error Code: {error_code}\n"
                        f"AWS Error Message: {e.response.get('Error', {}).get('Message', str(e))}"
                    ) from e

            # If we get here, artifact not found
            raise FileNotFoundError(
                f"CRITICAL: Metadata not found for artifact\n"
                f"Artifact ID: {artifact_id}\n"
                f"Bucket: {self.bucket}\n"
                f"Attempted keys: {attempted_keys}\n"
                "Metadata required for GAMP-5 audit trail"
            )
