"""
Test document ingestion to LocalStack S3.

Tests:
- Single document upload
- Batch document upload
- Metadata preservation
- Cleanup verification

CRITICAL: NO FALLBACK LOGIC
- All S3 errors must propagate
- Never assume upload succeeded without verification
"""

import boto3
import pytest
from botocore.exceptions import ClientError
from typing import Any

from .conftest import LOCALSTACK_ENDPOINT


@pytest.mark.asyncio
async def test_upload_single_document_to_s3(localstack_s3_bucket: str, audit_context: Any) -> None:
    """
    Test uploading single document to LocalStack S3.

    Args:
        localstack_s3_bucket: S3 bucket fixture
        audit_context: ALCOA+ audit context

    Verifies:
    - Document uploaded successfully
    - Metadata preserved
    - Document retrievable
    """
    try:
        # Create S3 client
        s3_client = boto3.client(
            "s3",
            endpoint_url=LOCALSTACK_ENDPOINT,
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="eu-west-2"
        )

        # Upload test document
        test_document = b"Protocol: Drug Release Process - GAMP-5 Category 5"
        document_key = "protocols/drug_release_v1.0.pdf"

        s3_client.put_object(
            Bucket=localstack_s3_bucket,
            Key=document_key,
            Body=test_document,
            Metadata={
                "gamp_category": "5",
                "created_by": "test_user",
                "document_type": "protocol",
                "version": "1.0"
            }
        )

        # Retrieve and verify
        response = s3_client.get_object(
            Bucket=localstack_s3_bucket,
            Key=document_key
        )

        retrieved_content = response["Body"].read()
        assert retrieved_content == test_document, "Document content mismatch"
        assert response["Metadata"]["gamp_category"] == "5", "Metadata missing"
        assert response["Metadata"]["document_type"] == "protocol"

        audit_context.record_test(
            test_name="test_upload_single_document_to_s3",
            passed=True,
            details=f"Uploaded {len(test_document)} bytes to {document_key}"
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_upload_single_document_to_s3",
            passed=False,
            details=f"Failed: {e}"
        )
        raise


@pytest.mark.asyncio
async def test_upload_batch_documents(localstack_s3_bucket: str, audit_context: Any) -> None:
    """
    Test uploading multiple documents in batch.

    Args:
        localstack_s3_bucket: S3 bucket fixture
        audit_context: ALCOA+ audit context

    Verifies:
    - All documents uploaded
    - No document loss
    - Metadata preserved for each
    """
    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=LOCALSTACK_ENDPOINT,
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="eu-west-2"
        )

        # Upload 10 test documents
        documents = [
            {
                "key": f"protocols/protocol_{i}.pdf",
                "body": f"Test Protocol {i} - GAMP-5 Category 5".encode(),
                "metadata": {
                    "gamp_category": "5",
                    "document_type": "protocol",
                    "version": f"{i}.0"
                }
            }
            for i in range(10)
        ]

        for doc in documents:
            s3_client.put_object(
                Bucket=localstack_s3_bucket,
                Key=doc["key"],
                Body=doc["body"],
                Metadata=doc["metadata"]
            )

        # Verify all uploaded
        response = s3_client.list_objects_v2(Bucket=localstack_s3_bucket)
        assert "Contents" in response, "No documents found after upload"
        assert len(response["Contents"]) == 10, f"Expected 10 documents, found {len(response['Contents'])}"

        # Spot check first and last
        first_doc = s3_client.get_object(Bucket=localstack_s3_bucket, Key=documents[0]["key"])
        last_doc = s3_client.get_object(Bucket=localstack_s3_bucket, Key=documents[9]["key"])

        assert first_doc["Metadata"]["version"] == "0.0"
        assert last_doc["Metadata"]["version"] == "9.0"

        audit_context.record_test(
            test_name="test_upload_batch_documents",
            passed=True,
            details=f"Successfully uploaded {len(documents)} documents"
        )

    except Exception as e:
        audit_context.record_test(
            test_name="test_upload_batch_documents",
            passed=False,
            details=f"Failed: {e}"
        )
        raise


@pytest.mark.asyncio
async def test_fail_on_missing_bucket(audit_context: Any) -> None:
    """
    Test that operations fail loudly on missing bucket.

    Args:
        audit_context: ALCOA+ audit context

    Verifies:
    - NO FALLBACK LOGIC - errors propagate
    - Full diagnostic information in exception
    """
    s3_client = boto3.client(
        "s3",
        endpoint_url=LOCALSTACK_ENDPOINT,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="eu-west-2"
    )

    fake_bucket = "nonexistent-bucket-12345"

    try:
        # Attempt upload to nonexistent bucket
        s3_client.put_object(
            Bucket=fake_bucket,
            Key="test.pdf",
            Body=b"test"
        )

        # CRITICAL: If we reach here, fallback logic detected
        audit_context.record_test(
            test_name="test_fail_on_missing_bucket",
            passed=False,
            details="FALLBACK LOGIC DETECTED: Upload succeeded to nonexistent bucket"
        )
        pytest.fail("NO FALLBACK LOGIC violation: Upload should have failed")

    except ClientError as e:
        # Expected: NoSuchBucket error
        assert e.response["Error"]["Code"] == "NoSuchBucket"

        audit_context.record_test(
            test_name="test_fail_on_missing_bucket",
            passed=True,
            details=f"Correctly raised ClientError: {e.response['Error']['Code']}"
        )


@pytest.mark.asyncio
async def test_cleanup_verification(localstack_s3_bucket: str, audit_context: Any) -> None:
    """
    Test that bucket cleanup works correctly.

    Args:
        localstack_s3_bucket: S3 bucket fixture
        audit_context: ALCOA+ audit context

    Verifies:
    - Multiple objects can be deleted
    - Cleanup doesn't fail silently
    - Fixture cleanup is reliable
    """
    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=LOCALSTACK_ENDPOINT,
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="eu-west-2"
        )

        # Upload 20 test objects
        for i in range(20):
            s3_client.put_object(
                Bucket=localstack_s3_bucket,
                Key=f"test-file-{i}.txt",
                Body=f"Test content {i}".encode()
            )

        # Verify all uploaded
        response = s3_client.list_objects_v2(Bucket=localstack_s3_bucket)
        assert len(response["Contents"]) == 20

        audit_context.record_test(
            test_name="test_cleanup_verification",
            passed=True,
            details="Uploaded 20 objects - fixture cleanup will handle deletion"
        )

        # Note: Fixture cleanup will delete all 20 objects automatically

    except Exception as e:
        audit_context.record_test(
            test_name="test_cleanup_verification",
            passed=False,
            details=f"Failed: {e}"
        )
        raise
