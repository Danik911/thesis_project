"""
Comprehensive test suite for dual-mode storage adapter (local/S3).

Tests both local filesystem and S3 storage modes using parametrized fixtures
to ensure identical behavior across storage backends.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from moto import mock_aws

from src.adapters import (
    LocalStorageAdapter,
    S3StorageAdapter,
    StorageFactory,
    StorageProvider,
)


# Test fixtures for parametrization


@pytest.fixture
def local_temp_dir(tmp_path: Path) -> Path:
    """Create temporary directory for local storage tests."""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    return storage_dir


@pytest.fixture
def valid_metadata() -> dict[str, str]:
    """Provide valid GAMP-5 compliant metadata for tests."""
    from datetime import UTC
    return {
        "gamp_category": "5",
        "job_id": "test-job-123",
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "created_by": "test-user",
        "artifact_type": "test_suite"
    }


@pytest.fixture
def sample_artifact_content() -> bytes:
    """Provide sample artifact content."""
    return json.dumps({
        "test_suite": "Sample Test Suite",
        "tests": [
            {"id": 1, "name": "Test 1"},
            {"id": 2, "name": "Test 2"}
        ]
    }).encode("utf-8")


@pytest.fixture(params=["local", "s3"])
def storage_adapter(
    request: pytest.FixtureRequest,
    local_temp_dir: Path
) -> StorageProvider:
    """
    Parametrized fixture that returns both local and S3 adapters.

    Tests using this fixture will run twice - once with local storage
    and once with S3 storage, ensuring identical behavior.
    """
    if request.param == "local":
        return LocalStorageAdapter(base_path=str(local_temp_dir))
    else:
        # S3 adapter (mocked) - Create bucket inline within mock context
        import boto3
        from moto import mock_aws

        # Store mock context in adapter for cleanup
        mock_context = mock_aws()
        mock_context.__enter__()

        bucket_name = "test-pharma-artifacts"
        s3_client = boto3.client("s3", region_name="eu-west-2")
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"}
        )

        adapter = S3StorageAdapter(bucket=bucket_name, region="eu-west-2")

        # Store mock context reference for potential cleanup
        adapter._mock_context = mock_context  # type: ignore

        return adapter


# Core functionality tests


@pytest.mark.asyncio
async def test_save_and_retrieve_artifact(
    storage_adapter: StorageProvider,
    valid_metadata: dict[str, str],
    sample_artifact_content: bytes
) -> None:
    """Test saving and retrieving artifacts in both storage modes."""
    artifact_id = "test-artifact-001"

    # Save artifact
    uri = await storage_adapter.save_artifact(
        artifact_id=artifact_id,
        content=sample_artifact_content,
        metadata=valid_metadata
    )

    # Verify URI format
    assert uri is not None
    assert isinstance(uri, str)
    if isinstance(storage_adapter, LocalStorageAdapter):
        assert uri.startswith("file://")
    else:
        assert uri.startswith("s3://")

    # Retrieve artifact
    retrieved_content = await storage_adapter.retrieve_artifact(artifact_id)

    # Verify content matches
    assert retrieved_content == sample_artifact_content


@pytest.mark.asyncio
async def test_artifact_metadata_persistence(
    storage_adapter: StorageProvider,
    valid_metadata: dict[str, str],
    sample_artifact_content: bytes
) -> None:
    """Test that metadata is properly persisted with artifacts."""
    artifact_id = "test-artifact-002"

    # Save artifact with metadata
    await storage_adapter.save_artifact(
        artifact_id=artifact_id,
        content=sample_artifact_content,
        metadata=valid_metadata
    )

    # Retrieve metadata (if adapter supports it)
    if hasattr(storage_adapter, "get_artifact_metadata"):
        retrieved_metadata = await storage_adapter.get_artifact_metadata(artifact_id)

        # Verify all required fields present
        for field in ["gamp_category", "job_id", "created_at", "created_by", "artifact_type"]:
            assert field in retrieved_metadata


@pytest.mark.asyncio
async def test_generate_download_url(
    storage_adapter: StorageProvider,
    valid_metadata: dict[str, str],
    sample_artifact_content: bytes
) -> None:
    """Test download URL generation for both storage modes."""
    artifact_id = "test-artifact-003"

    # Save artifact first
    await storage_adapter.save_artifact(
        artifact_id=artifact_id,
        content=sample_artifact_content,
        metadata=valid_metadata
    )

    # Generate download URL
    url = await storage_adapter.generate_download_url(
        artifact_id=artifact_id,
        expiry_seconds=3600
    )

    # Verify URL format
    assert url is not None
    assert isinstance(url, str)
    if isinstance(storage_adapter, LocalStorageAdapter):
        assert url.startswith("file://")
    else:
        assert url.startswith("https://")


@pytest.mark.asyncio
async def test_error_handling_file_not_found(
    storage_adapter: StorageProvider
) -> None:
    """Test that FileNotFoundError is raised for non-existent artifacts."""
    non_existent_id = "non-existent-artifact"

    # Attempt to retrieve non-existent artifact
    with pytest.raises(FileNotFoundError) as exc_info:
        await storage_adapter.retrieve_artifact(non_existent_id)

    # Verify error message contains diagnostic information
    error_message = str(exc_info.value)
    assert "CRITICAL" in error_message
    assert non_existent_id in error_message


@pytest.mark.asyncio
async def test_invalid_metadata_missing_fields(
    storage_adapter: StorageProvider,
    sample_artifact_content: bytes
) -> None:
    """Test that ValueError is raised for incomplete metadata."""
    artifact_id = "test-artifact-004"

    # Invalid metadata (missing required fields)
    invalid_metadata = {
        "job_id": "test-job-123"
        # Missing: gamp_category, created_at, created_by, artifact_type
    }

    # Attempt to save with invalid metadata
    with pytest.raises(ValueError) as exc_info:
        await storage_adapter.save_artifact(
            artifact_id=artifact_id,
            content=sample_artifact_content,
            metadata=invalid_metadata
        )

    # Verify error message contains diagnostic information
    error_message = str(exc_info.value)
    assert "CRITICAL" in error_message
    assert "Missing required GAMP-5 metadata fields" in error_message


@pytest.mark.asyncio
async def test_invalid_gamp_category(
    storage_adapter: StorageProvider,
    valid_metadata: dict[str, str],
    sample_artifact_content: bytes
) -> None:
    """Test that ValueError is raised for invalid GAMP category."""
    artifact_id = "test-artifact-005"

    # Invalid GAMP category
    invalid_metadata = {
        **valid_metadata,
        "gamp_category": "99"  # Invalid category
    }

    # Attempt to save with invalid category
    with pytest.raises(ValueError) as exc_info:
        await storage_adapter.save_artifact(
            artifact_id=artifact_id,
            content=sample_artifact_content,
            metadata=invalid_metadata
        )

    # Verify error message
    error_message = str(exc_info.value)
    assert "CRITICAL" in error_message
    assert "Invalid GAMP category" in error_message


@pytest.mark.asyncio
async def test_invalid_artifact_type(
    storage_adapter: StorageProvider,
    valid_metadata: dict[str, str],
    sample_artifact_content: bytes
) -> None:
    """Test that ValueError is raised for invalid artifact type."""
    artifact_id = "test-artifact-006"

    # Invalid artifact type
    invalid_metadata = {
        **valid_metadata,
        "artifact_type": "invalid_type"
    }

    # Attempt to save with invalid type
    with pytest.raises(ValueError) as exc_info:
        await storage_adapter.save_artifact(
            artifact_id=artifact_id,
            content=sample_artifact_content,
            metadata=invalid_metadata
        )

    # Verify error message
    error_message = str(exc_info.value)
    assert "CRITICAL" in error_message
    assert "Invalid artifact type" in error_message


@pytest.mark.asyncio
async def test_invalid_timestamp_format(
    storage_adapter: StorageProvider,
    valid_metadata: dict[str, str],
    sample_artifact_content: bytes
) -> None:
    """Test that ValueError is raised for invalid timestamp format."""
    artifact_id = "test-artifact-007"

    # Invalid timestamp format
    invalid_metadata = {
        **valid_metadata,
        "created_at": "not-a-valid-timestamp"
    }

    # Attempt to save with invalid timestamp
    with pytest.raises(ValueError) as exc_info:
        await storage_adapter.save_artifact(
            artifact_id=artifact_id,
            content=sample_artifact_content,
            metadata=invalid_metadata
        )

    # Verify error message
    error_message = str(exc_info.value)
    assert "CRITICAL" in error_message
    assert "Invalid timestamp format" in error_message


@pytest.mark.asyncio
async def test_concurrent_operations(
    storage_adapter: StorageProvider,
    valid_metadata: dict[str, str],
    sample_artifact_content: bytes
) -> None:
    """Test concurrent save operations with semaphore control."""
    num_concurrent = 20  # More than semaphore limits

    async def save_artifact(index: int) -> str:
        artifact_id = f"concurrent-artifact-{index}"
        return await storage_adapter.save_artifact(
            artifact_id=artifact_id,
            content=sample_artifact_content,
            metadata={
                **valid_metadata,
                "job_id": f"concurrent-job-{index}"
            }
        )

    # Run concurrent saves
    results = await asyncio.gather(
        *[save_artifact(i) for i in range(num_concurrent)]
    )

    # Verify all succeeded
    assert len(results) == num_concurrent
    for result in results:
        assert result is not None


# Storage factory tests


def test_storage_factory_local_mode(local_temp_dir: Path) -> None:
    """Test StorageFactory creates LocalStorageAdapter."""
    adapter = StorageFactory.create_storage_provider(
        storage_mode="local",
        base_path=str(local_temp_dir)
    )

    assert isinstance(adapter, LocalStorageAdapter)


@mock_aws
def test_storage_factory_s3_mode(s3_bucket: str) -> None:
    """Test StorageFactory creates S3StorageAdapter."""
    adapter = StorageFactory.create_storage_provider(
        storage_mode="s3",
        bucket=s3_bucket,
        region="eu-west-2"
    )

    assert isinstance(adapter, S3StorageAdapter)


def test_storage_factory_invalid_mode() -> None:
    """Test StorageFactory raises error for invalid mode."""
    with pytest.raises(ValueError) as exc_info:
        StorageFactory.create_storage_provider(
            storage_mode="invalid_mode"
        )

    error_message = str(exc_info.value)
    assert "CRITICAL" in error_message
    assert "Invalid storage mode" in error_message


def test_storage_factory_s3_missing_bucket() -> None:
    """Test StorageFactory raises error when S3 bucket missing."""
    with pytest.raises(ValueError) as exc_info:
        StorageFactory.create_storage_provider(
            storage_mode="s3"
            # Missing bucket parameter
        )

    error_message = str(exc_info.value)
    assert "CRITICAL" in error_message
    assert "bucket" in error_message.lower()


# Cross-platform path tests (Windows/Linux)


@pytest.mark.asyncio
async def test_cross_platform_paths(
    local_temp_dir: Path,
    valid_metadata: dict[str, str],
    sample_artifact_content: bytes
) -> None:
    """Test that paths work correctly on both Windows and Linux."""
    adapter = LocalStorageAdapter(base_path=str(local_temp_dir))
    artifact_id = "test-artifact-008"

    # Save artifact
    uri = await adapter.save_artifact(
        artifact_id=artifact_id,
        content=sample_artifact_content,
        metadata=valid_metadata
    )

    # Verify URI is valid on current platform
    assert uri.startswith("file://")

    # Verify file exists using pathlib (cross-platform)
    artifact_path = local_temp_dir / f"{artifact_id}.json"
    assert artifact_path.exists()

    # Retrieve artifact
    retrieved_content = await adapter.retrieve_artifact(artifact_id)
    assert retrieved_content == sample_artifact_content


# Local adapter specific tests


@pytest.mark.asyncio
async def test_local_adapter_metadata_file_creation(
    local_temp_dir: Path,
    valid_metadata: dict[str, str],
    sample_artifact_content: bytes
) -> None:
    """Test that LocalStorageAdapter creates .meta.json files."""
    adapter = LocalStorageAdapter(base_path=str(local_temp_dir))
    artifact_id = "test-artifact-009"

    # Save artifact
    await adapter.save_artifact(
        artifact_id=artifact_id,
        content=sample_artifact_content,
        metadata=valid_metadata
    )

    # Verify metadata file exists
    metadata_path = local_temp_dir / f"{artifact_id}.meta.json"
    assert metadata_path.exists()

    # Verify metadata content
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata_content = json.load(f)

    # Check all required fields present
    for field in ["gamp_category", "job_id", "created_at", "created_by", "artifact_type"]:
        assert field in metadata_content

    # Check enhanced fields added by adapter
    assert "storage_mode" in metadata_content
    assert metadata_content["storage_mode"] == "local"


# S3 adapter specific tests


@pytest.mark.asyncio
async def test_s3_adapter_encryption(
    valid_metadata: dict[str, str],
    sample_artifact_content: bytes
) -> None:
    """Test that S3StorageAdapter enforces SSE-KMS encryption."""
    import boto3
    from moto import mock_aws

    with mock_aws():
        # Create bucket
        s3_client = boto3.client("s3", region_name="eu-west-2")
        bucket_name = "test-pharma-artifacts"
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"}
        )

        # Create adapter
        adapter = S3StorageAdapter(bucket=bucket_name, region="eu-west-2")
        artifact_id = "test-artifact-010"

        # Save artifact
        await adapter.save_artifact(
            artifact_id=artifact_id,
            content=sample_artifact_content,
            metadata=valid_metadata
        )

        # Verify encryption via boto3 head_object
        s3_key = f"test-suites/{artifact_id}.json"

        response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)

        # Check encryption is set
        assert "ServerSideEncryption" in response
        assert response["ServerSideEncryption"] == "aws:kms"


@pytest.mark.asyncio
async def test_s3_adapter_metadata_in_object_metadata(
    valid_metadata: dict[str, str],
    sample_artifact_content: bytes
) -> None:
    """Test that S3StorageAdapter stores metadata in S3 object metadata."""
    import boto3
    from moto import mock_aws

    with mock_aws():
        # Create bucket
        s3_client = boto3.client("s3", region_name="eu-west-2")
        bucket_name = "test-pharma-artifacts"
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"}
        )

        # Create adapter
        adapter = S3StorageAdapter(bucket=bucket_name, region="eu-west-2")
        artifact_id = "test-artifact-011"

        # Save artifact
        await adapter.save_artifact(
            artifact_id=artifact_id,
            content=sample_artifact_content,
            metadata=valid_metadata
        )

        # Verify metadata via boto3
        s3_key = f"test-suites/{artifact_id}.json"

        response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)

        # Check metadata is present
        assert "Metadata" in response
        metadata = response["Metadata"]

        # Verify required fields in metadata
        for field in ["gamp_category", "job_id", "created_at", "created_by", "artifact_type"]:
            assert field in metadata


@pytest.mark.asyncio
async def test_s3_adapter_metadata_size_limit(
    valid_metadata: dict[str, str],
    sample_artifact_content: bytes
) -> None:
    """Test that S3StorageAdapter validates metadata size (2KB limit)."""
    import boto3
    from moto import mock_aws

    with mock_aws():
        # Create bucket
        s3_client = boto3.client("s3", region_name="eu-west-2")
        bucket_name = "test-pharma-artifacts"
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"}
        )

        # Create adapter
        adapter = S3StorageAdapter(bucket=bucket_name, region="eu-west-2")
        artifact_id = "test-artifact-012"

        # Create oversized metadata (>2KB)
        large_metadata = {
            **valid_metadata,
            "large_field": "x" * 3000  # Exceeds 2KB limit
        }

        # Attempt to save with oversized metadata
        with pytest.raises(ValueError) as exc_info:
            await adapter.save_artifact(
                artifact_id=artifact_id,
                content=sample_artifact_content,
                metadata=large_metadata
            )

        # Verify error message
        error_message = str(exc_info.value)
        assert "CRITICAL" in error_message
        assert "exceeds S3 2KB limit" in error_message


# NO FALLBACK LOGIC verification tests


@pytest.mark.asyncio
async def test_no_fallback_on_missing_artifact(
    storage_adapter: StorageProvider
) -> None:
    """Verify NO FALLBACK LOGIC: Missing artifacts raise explicit errors."""
    non_existent_id = "never-created-artifact"

    # Should raise FileNotFoundError, NOT return empty bytes or default value
    with pytest.raises(FileNotFoundError) as exc_info:
        await storage_adapter.retrieve_artifact(non_existent_id)

    # Verify diagnostic information present
    error_message = str(exc_info.value)
    assert "CRITICAL" in error_message
    assert non_existent_id in error_message


@pytest.mark.asyncio
async def test_no_fallback_on_invalid_metadata(
    storage_adapter: StorageProvider,
    sample_artifact_content: bytes
) -> None:
    """Verify NO FALLBACK LOGIC: Invalid metadata raises explicit errors."""
    artifact_id = "test-artifact-013"

    # Completely empty metadata (no fallback to defaults)
    empty_metadata: dict[str, str] = {}

    # Should raise ValueError, NOT use default values
    with pytest.raises(ValueError) as exc_info:
        await storage_adapter.save_artifact(
            artifact_id=artifact_id,
            content=sample_artifact_content,
            metadata=empty_metadata
        )

    # Verify diagnostic information present
    error_message = str(exc_info.value)
    assert "CRITICAL" in error_message
    assert "Missing required GAMP-5 metadata fields" in error_message


@pytest.mark.asyncio
async def test_no_success_claim_on_filesystem_error(
    local_temp_dir: Path,
    valid_metadata: dict[str, str],
    sample_artifact_content: bytes
) -> None:
    """Verify NO FALLBACK LOGIC: Filesystem errors propagate with diagnostics."""
    # Create adapter with read-only directory (simulate permission error)
    adapter = LocalStorageAdapter(base_path=str(local_temp_dir))

    # Make directory read-only (platform-dependent)
    import os
    import stat
    os.chmod(local_temp_dir, stat.S_IRUSR | stat.S_IXUSR)

    artifact_id = "test-artifact-014"

    try:
        # Should raise RuntimeError with full diagnostic info
        with pytest.raises(RuntimeError) as exc_info:
            await adapter.save_artifact(
                artifact_id=artifact_id,
                content=sample_artifact_content,
                metadata=valid_metadata
            )

        # Verify diagnostic information
        error_message = str(exc_info.value)
        assert "CRITICAL" in error_message
        assert artifact_id in error_message

    finally:
        # Restore permissions
        os.chmod(local_temp_dir, stat.S_IRWXU)
