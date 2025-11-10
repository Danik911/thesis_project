# Context Collector Result - 20251110-140530

## Agent Configuration
- Agent: context-collector
- Task ID: 1.1
- Task Name: Implement Dual-Mode Storage Adapter
- Phase: 1 - Backend Abstraction
- Invoked: 2025-11-10 14:05:30
- Duration: 15 minutes
- Status: SUCCESS

---

## Task Understanding

Task 1.1 requires implementing a storage abstraction layer that:
1. Writes URS documents and generated test suites to either local filesystem (dev) or S3 (AWS) based on configuration
2. Persists metadata (category, timestamps, authorship) for audit trail compliance with GAMP-5
3. Provides helper methods for retrieving artifacts and generating pre-signed URLs for frontend downloads
4. Uses dependency injection to decouple storage provider from workflow logic
5. Enforces SSE-KMS encryption and bucket policies when using S3
6. Names S3 keys deterministically for compliance auditing

The adapter must be async-first (compatible with LlamaIndex 0.12.0+ workflows) and must explicitly handle errors without fallback logic.

---

## Research Findings

### Python Storage Patterns

#### Async File I/O with aiofiles

**Best Practice Pattern:**
```python
import aiofiles
from pathlib import Path

async def write_file(filepath: str, content: bytes) -> None:
    """Async file write with proper resource management."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)  # Create directories

    async with aiofiles.open(filepath, mode='wb') as f:
        await f.write(content)  # CRITICAL: Always await

async def read_file(filepath: str) -> bytes:
    """Async file read with explicit error handling."""
    try:
        async with aiofiles.open(filepath, mode='rb') as f:
            return await f.read()
    except FileNotFoundError as e:
        # NO FALLBACK: Fail explicitly with diagnostics
        raise FileNotFoundError(f"File not found: {filepath}") from e
    except Exception as e:
        # Explicit error propagation for audit compliance
        raise RuntimeError(f"Failed to read {filepath}: {str(e)}") from e
```

**Critical Gotchas:**
- ALWAYS use `async with` context managers (not regular `with`)
- ALWAYS `await` all aiofiles operations - forgetting await returns coroutine, not data
- Use `pathlib.Path` for cross-platform path handling (Windows/Linux)
- Implement semaphores to limit concurrent file operations: `asyncio.Semaphore(10)`
- aiofiles uses thread pool internally - true async at network/OS level, but thread-bound for disk I/O

#### Protocol-Based Storage Abstraction

Use Python's `typing.Protocol` for contract-based interface (preferred over ABC for async):

```python
from typing import Protocol, AsyncIterator
from abc import abstractmethod

class StorageProvider(Protocol):
    """Storage adapter contract - supports both local and S3 implementations."""

    async def save_artifact(self, artifact_id: str, content: bytes,
                           metadata: dict) -> str:
        """Save artifact and return path/URI."""
        ...

    async def retrieve_artifact(self, artifact_id: str) -> bytes:
        """Retrieve artifact by ID."""
        ...

    async def delete_artifact(self, artifact_id: str) -> None:
        """Delete artifact by ID."""
        ...

    async def list_artifacts(self, prefix: str) -> AsyncIterator[str]:
        """List artifact IDs with given prefix."""
        ...

    async def generate_download_url(self, artifact_id: str,
                                   expiry_seconds: int = 3600) -> str:
        """Generate pre-signed download URL (S3) or local path (filesystem)."""
        ...
```

#### Dependency Injection Pattern

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class StorageConfig:
    """Storage configuration - loaded from environment via Pydantic."""
    storage_mode: str  # "local" or "s3"
    local_base_path: str = "output"
    aws_region: str = "eu-west-2"
    test_output_bucket: str = ""  # Required for S3 mode
    kms_key_id: str = ""  # KMS key ARN for SSE-KMS
    retention_days: int = 2555  # 7 years for pharmaceutical records

class WorkflowWithStorage:
    """Workflow depends on storage adapter through injection."""

    def __init__(self, storage: StorageProvider, config: StorageConfig):
        self.storage = storage
        self.config = config

    async def save_test_suite(self, job_id: str, suite_data: dict) -> str:
        """Save test suite using injected storage adapter."""
        metadata = {
            "gamp_category": str(suite_data.get("category")),
            "job_id": job_id,
            "created_at": datetime.utcnow().isoformat(),
            "author": "pharmaceutical_test_generator"
        }

        content = json.dumps(suite_data, indent=2).encode('utf-8')
        return await self.storage.save_artifact(
            f"test-suites/{job_id}.json",
            content,
            metadata
        )
```

---

### AWS S3 Integration Best Practices

#### Async S3 Client Configuration

Use `aiobotocore` for true async S3 operations (preferred over blocking boto3 in thread pool):

```python
from aiobotocore.session import get_session
import asyncio

class S3StorageAdapter:
    """AWS S3 storage adapter with async/await support."""

    def __init__(self, bucket: str, region: str = "eu-west-2",
                 kms_key_id: str = None):
        self.bucket = bucket
        self.region = region
        self.kms_key_id = kms_key_id
        self.session = get_session()
        self._semaphore = asyncio.Semaphore(5)  # Limit concurrent S3 ops

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup handled by context manager
        pass

    async def save_artifact(self, key: str, content: bytes,
                          metadata: dict) -> str:
        """Upload artifact with SSE-KMS encryption and metadata."""
        async with self._semaphore:
            async with self.session.create_client('s3', region_name=self.region) as client:
                put_kwargs = {
                    'Bucket': self.bucket,
                    'Key': key,
                    'Body': content,
                    'ServerSideEncryption': 'aws:kms',  # REQUIRED for compliance
                    'Metadata': self._format_metadata(metadata)
                }

                if self.kms_key_id:
                    put_kwargs['SSEKMSKeyId'] = self.kms_key_id

                try:
                    response = await client.put_object(**put_kwargs)
                    # S3 NOW HAS STRONG CONSISTENCY - no eventual consistency issues
                    return f"s3://{self.bucket}/{key}"
                except Exception as e:
                    # NO FALLBACK: Fail explicitly with full diagnostics
                    raise RuntimeError(
                        f"S3 put_object failed for key={key}: {str(e)}\n"
                        f"Bucket={self.bucket}, Region={self.region}, "
                        f"KMS Key={self.kms_key_id}"
                    ) from e

    async def retrieve_artifact(self, key: str) -> bytes:
        """Download artifact from S3."""
        async with self._semaphore:
            async with self.session.create_client('s3', region_name=self.region) as client:
                try:
                    response = await client.get_object(Bucket=self.bucket, Key=key)
                    # Note: response['Body'] is async reader
                    async with response['Body'] as stream:
                        return await stream.read()
                except client.exceptions.NoSuchKey as e:
                    raise FileNotFoundError(f"Artifact not found in S3: {key}") from e
                except Exception as e:
                    raise RuntimeError(f"S3 get_object failed for key={key}: {str(e)}") from e

    async def generate_download_url(self, key: str,
                                   expiry_seconds: int = 3600) -> str:
        """Generate pre-signed URL for artifact download (24-hour default)."""
        async with self.session.create_client('s3', region_name=self.region) as client:
            try:
                url = await client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': key},
                    ExpiresIn=expiry_seconds
                )
                return url
            except Exception as e:
                raise RuntimeError(
                    f"Failed to generate pre-signed URL for key={key}: {str(e)}"
                ) from e

    @staticmethod
    def _format_metadata(metadata: dict) -> dict:
        """Format metadata dict for S3 object metadata (max 2KB per AWS limits)."""
        # S3 metadata values must be strings
        s3_metadata = {}
        for key, value in metadata.items():
            # Sanitize metadata key names (alphanumeric, hyphen only)
            clean_key = ''.join(c if c.isalnum() or c == '-' else '_' for c in key)
            # Convert value to string
            s3_metadata[clean_key] = str(value)[:256]  # Max 256 chars per value
        return s3_metadata
```

#### SSE-KMS Encryption Configuration

**S3 Bucket Policy Requirements (for GAMP-5 compliance):**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyUnencryptedObjectUploads",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::pharma-test-bucket/*",
            "Condition": {
                "StringNotEquals": {
                    "s3:x-amz-server-side-encryption": "aws:kms"
                }
            }
        },
        {
            "Sid": "DenyIncorrectKmsKey",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::pharma-test-bucket/*",
            "Condition": {
                "StringNotEquals": {
                    "s3:x-amz-server-side-encryption-aws-kms-key-id": "arn:aws:kms:eu-west-2:ACCOUNT_ID:key/KMS_KEY_ID"
                }
            }
        }
    ]
}
```

#### Pre-Signed URL Generation (for Frontend Downloads)

```python
async def get_download_url(self, artifact_id: str) -> str:
    """Generate pre-signed URL for secure artifact download."""
    # For frontend: return S3 pre-signed URL
    # For local dev: return local file path
    if self.storage_mode == "s3":
        return await self.s3_adapter.generate_download_url(artifact_id)
    else:
        # Local dev: return relative path from output directory
        return f"/artifacts/{artifact_id}"
```

#### S3 Versioning for WORM Compliance

Enable on bucket creation:
```python
async def enable_versioning(self):
    """Enable S3 versioning for WORM (Write-Once-Read-Many) compliance."""
    async with self.session.create_client('s3', region_name=self.region) as client:
        await client.put_bucket_versioning(
            Bucket=self.bucket,
            VersioningConfiguration={'Status': 'Enabled'}
        )
```

**Key Point:** S3 strong consistency (as of late 2020) means metadata updates are immediately visible - no eventual consistency delays. This simplifies audit trail logic.

---

### Pharmaceutical Compliance Requirements

#### GAMP-5 Compliance for Storage

**Core Requirements:**

1. **Audit Trail with Timestamps and User IDs**
   - Every artifact must track: WHO created it, WHEN, under what circumstances
   - Metadata must include: `created_at` (ISO 8601 UTC), `created_by` (user/service ID), `gamp_category` (classification)
   - Changes must be tracked (S3 versioning + CloudTrail)

2. **Data Integrity and Unmodified Records**
   - S3 with SSE-KMS prevents unauthorized modification
   - Object Lock (if available) enforces WORM (Write-Once-Read-Many)
   - Metadata persists with object - cannot be changed post-upload

3. **System Validation**
   - Storage adapter must be validated per V-model: Requirements → Design → Build → Test → Deploy
   - Testing strategy (see below) demonstrates correct behavior

4. **Retention Management**
   - Set 7-year retention for pharmaceutical records: `retention_days=2555`
   - S3 Object Lock or lifecycle policies enforce retention
   - Audit logs retained separately with same retention policy

#### ALCOA+ Principles Applied to Storage

| Principle | Storage Implementation |
|-----------|------------------------|
| **Attributable** | Metadata includes created_by, timestamps. CloudTrail logs KMS access. S3 access logs track retrieval. |
| **Legible** | JSON artifact format is human-readable. Metadata stored as readable key-value pairs. |
| **Contemporaneous** | Timestamps recorded at creation/modification time (UTC). No backdating allowed. |
| **Original** | S3 immutable after creation (SSE prevents tampering). Versioning tracks all changes. |
| **Accurate** | Artifact content validated before storage. Metadata size/format enforced (≤2KB). |
| **Complete** | All required metadata fields captured. Artifacts stored with full context. |
| **Consistent** | Same metadata structure across all artifacts. Deterministic key naming. |
| **Enduring** | S3 durability: 99.999999999% (11 nines). Automatic replication across AZs. |
| **Available** | Pre-signed URLs enable retrieval. CloudFront can cache for low-latency access. |

#### Audit Trail Metadata Structure

```python
REQUIRED_METADATA = {
    "gamp_category": "int (1, 3, 4, or 5)",  # GAMP-5 software categorization
    "job_id": "str",                         # Unique workflow execution ID
    "created_at": "ISO 8601 UTC timestamp",  # RFC 3339 format
    "created_by": "str (user or service)",   # Attributability
    "urs_version": "str",                    # Requirements specification version
    "artifact_type": "test_suite|urs|report" # Classification
}
```

---

### Testing Strategies

#### Unit Testing with Moto and Pytest-Asyncio

**Setup Fixtures:**
```python
import pytest
import pytest_asyncio
import boto3
from moto import mock_aws
import tempfile
from pathlib import Path

@pytest.fixture
def aws_credentials(monkeypatch):
    """Mock AWS credentials for moto."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")

@pytest_asyncio.fixture
async def s3_client(aws_credentials):
    """Async S3 client with moto mock."""
    with mock_aws():
        # Note: boto3 is sync, wrap for async if needed
        client = boto3.client("s3", region_name="eu-west-2")
        yield client

@pytest_asyncio.fixture
async def s3_bucket(s3_client):
    """Create test bucket."""
    bucket_name = "test-pharma-bucket"
    s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'}
    )
    return bucket_name

@pytest.fixture
def local_temp_dir():
    """Temp directory for local storage tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
```

#### Parametrized Testing for Both Modes

```python
@pytest.fixture(params=["local", "s3"])
async def storage_adapter(request, local_temp_dir, s3_client, s3_bucket):
    """Parametrized fixture runs tests against both storage modes."""
    if request.param == "local":
        from your_module import LocalStorageAdapter
        return LocalStorageAdapter(str(local_temp_dir))
    else:
        from your_module import S3StorageAdapter
        return S3StorageAdapter(bucket=s3_bucket, region="eu-west-2")

@pytest.mark.asyncio
async def test_save_and_retrieve_artifact(storage_adapter):
    """Test artifact persistence in both local and S3 modes."""
    artifact_id = "test-001"
    content = b"Test artifact content"
    metadata = {
        "gamp_category": "4",
        "created_by": "test_runner",
        "created_at": "2025-11-10T14:00:00Z"
    }

    # Save
    path = await storage_adapter.save_artifact(artifact_id, content, metadata)
    assert path is not None

    # Retrieve
    retrieved = await storage_adapter.retrieve_artifact(artifact_id)
    assert retrieved == content

@pytest.mark.asyncio
async def test_artifact_metadata_persistence(storage_adapter):
    """Verify metadata persists with artifact (GAMP-5 audit trail)."""
    artifact_id = "metadata-test"
    metadata = {
        "gamp_category": "3",
        "created_by": "validation_engine",
        "created_at": "2025-11-10T14:05:00Z",
        "urs_version": "2.1"
    }

    await storage_adapter.save_artifact(
        artifact_id,
        b"content",
        metadata
    )

    # Verify metadata can be retrieved (S3: check object metadata)
    # This tests that GAMP-5 audit trail is preserved
```

#### Integration Testing with Docker Compose

```bash
# docker-compose test environment with local moto server
docker-compose -f docker-compose.test.yml up
pytest -m integration --storage-mode s3
```

---

### Implementation Gotchas

#### Async Context Manager Pitfalls

**❌ WRONG - Will fail:**
```python
# Regular with statement with async function - FAILS
with aiofiles.open(path) as f:
    content = await f.read()  # Error: object does not support async context manager

# Forgetting await - Gets coroutine object, not bytes
async with aiofiles.open(path) as f:
    content = f.read()  # Wrong: content is coroutine, not bytes
```

**✅ CORRECT:**
```python
async with aiofiles.open(path, mode='rb') as f:
    content = await f.read()  # Proper async/await pattern
```

#### Path Handling Cross-Platform

**❌ WRONG - Windows incompatible:**
```python
path = "output/test_suites/test-001.json"  # Breaks on Windows with backslashes
full_path = "output" + "/" + filename  # Path separator issues
```

**✅ CORRECT:**
```python
from pathlib import Path
path = Path("output") / "test_suites" / "test-001.json"  # Cross-platform
full_path = Path("output").joinpath(filename)  # Handles separators
```

#### S3 Consistency Model (RESOLVED)

**OLD CONCERN (2020 and earlier):** S3 had eventual consistency for new object creation.
**CURRENT BEHAVIOR (2021+):** S3 provides **strong consistency** for all operations.

This means:
- No need to poll or retry on missing metadata
- Metadata updates visible immediately after successful write
- CloudTrail audit logs available immediately
- Simplifies workflow logic

#### Error Handling - NO FALLBACKS

**❌ WRONG - Fallback logic forbidden in GAMP-5 context:**
```python
async def save_artifact(self, artifact_id, content):
    try:
        await self.s3_client.put_object(...)
    except Exception:
        # FORBIDDEN: Don't fall back to local storage
        await self.local_storage.write(...)
        return "fallback_path"  # Hides failure from audit trail
```

**✅ CORRECT - Explicit failure:**
```python
async def save_artifact(self, artifact_id, content, metadata):
    try:
        response = await self.s3_client.put_object(
            Bucket=self.bucket,
            Key=f"artifacts/{artifact_id}",
            Body=content,
            Metadata=metadata
        )
        return response  # Full response for audit
    except Exception as e:
        # FAIL EXPLICITLY with complete diagnostics
        raise RuntimeError(
            f"CRITICAL: Artifact storage failed\n"
            f"Artifact ID: {artifact_id}\n"
            f"Error: {str(e)}\n"
            f"Context: {self._get_debug_context()}"
        ) from e
```

#### Semaphore/Concurrency Limits

**❌ WRONG - Unlimited concurrent operations:**
```python
tasks = [self.s3_client.put_object(...) for i in range(1000)]
await asyncio.gather(*tasks)  # Opens 1000 concurrent connections - FAILS
```

**✅ CORRECT - Bounded concurrency:**
```python
self._semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent S3 ops

async def save_artifact(self, artifact_id, content, metadata):
    async with self._semaphore:
        # Only 5 concurrent operations at a time
        await self.s3_client.put_object(...)
```

#### Metadata Size Limits

S3 object metadata has hard limits:
- Max 2 KB total per object
- Max 256 characters per value
- Keys must be alphanumeric + hyphens

**Implementation:**
```python
def _validate_metadata(self, metadata: dict) -> dict:
    """Ensure metadata fits S3 constraints (2KB max)."""
    total_size = 0
    validated = {}

    for key, value in metadata.items():
        # Sanitize key
        clean_key = ''.join(c if c.isalnum() or c == '-' else '_' for c in key)
        # Truncate value to 256 chars
        str_value = str(value)[:256]

        item_size = len(clean_key) + len(str_value)
        total_size += item_size

        if total_size > 2048:
            raise ValueError(f"Metadata exceeds 2KB limit. Size: {total_size}")

        validated[clean_key] = str_value

    return validated
```

---

### Recommended Approach

#### File Structure

Create storage module at: `main/src/adapters/storage.py`

```
main/src/adapters/
├── __init__.py
├── storage.py           # Core storage adapter implementation
├── local_adapter.py     # LocalStorageAdapter class
├── s3_adapter.py        # S3StorageAdapter class
└── config.py            # StorageConfig (use existing Pydantic settings)
```

#### Class Hierarchy

```python
# Protocol for interface contract
class StorageProvider(Protocol):
    async def save_artifact(...) -> str: ...
    async def retrieve_artifact(...) -> bytes: ...

# Local implementation
class LocalStorageAdapter:
    def __init__(self, base_path: str)
    async def save_artifact(...) -> str
    async def retrieve_artifact(...) -> bytes

# S3 implementation
class S3StorageAdapter:
    def __init__(self, bucket: str, region: str, kms_key_id: str)
    async def save_artifact(...) -> str
    async def retrieve_artifact(...) -> bytes

# Factory for dependency injection
class StorageFactory:
    @staticmethod
    async def create(config: StorageConfig) -> StorageProvider
```

#### Configuration Approach

Extend existing `Pydantic` settings in `main/src/shared/config.py`:

```python
@dataclass
class StorageAdapterConfig:
    """Storage configuration for dual-mode adapter."""

    storage_mode: str = Field(
        default=os.getenv("STORAGE_MODE", "local"),
        description="local or s3"
    )
    local_base_path: str = Field(
        default="output",
        description="Base path for local storage"
    )
    aws_region: str = Field(
        default="eu-west-2",
        description="AWS region for S3"
    )
    test_output_bucket: str = Field(
        default=os.getenv("TEST_OUTPUT_BUCKET", ""),
        description="S3 bucket name for test artifacts"
    )
    kms_key_id: str = Field(
        default=os.getenv("KMS_KEY_ID", ""),
        description="KMS key ARN for S3 SSE-KMS encryption"
    )
    artifact_retention_days: int = Field(
        default=2555,  # 7 years
        description="Retention period for pharmaceutical records"
    )
```

#### Error Handling Strategy

NO fallback logic. Use explicit error propagation with full context:

```python
class StorageException(Exception):
    """Base exception for storage operations."""
    def __init__(self, operation: str, artifact_id: str,
                 original_error: Exception, context: dict):
        self.operation = operation
        self.artifact_id = artifact_id
        self.original_error = original_error
        self.context = context

        message = (
            f"Storage operation '{operation}' failed\n"
            f"Artifact: {artifact_id}\n"
            f"Error: {str(original_error)}\n"
            f"Context: {json.dumps(context, indent=2)}"
        )
        super().__init__(message)
```

---

### Required Libraries/Versions

| Library | Version | Reason |
|---------|---------|--------|
| `aiobotocore` | `>=2.11.0` | Async S3 client for non-blocking operations |
| `aiofiles` | `>=23.2.0` | Async local file I/O with proper context managers |
| `boto3` | `>=1.29.0` | AWS SDK (required by aiobotocore) |
| `pydantic` | `>=2.0.0` | Configuration validation (already in project) |
| `pydantic-settings` | `>=2.0.0` | Environment variable loading (already in project) |
| `pytest` | `>=7.4.0` | Testing framework |
| `pytest-asyncio` | `>=0.21.0` | Async test support |
| `moto` | `>=4.2.0` | S3 mocking for tests |

**Installation:**
```bash
uv add aiobotocore@>=2.11.0
uv add aiofiles@>=23.2.0
uv add pytest-asyncio@>=0.21.0
uv add moto[s3]@>=4.2.0
```

---

### Configuration Structure (Pydantic)

```python
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

class StorageSettings(BaseSettings):
    """Storage adapter configuration from environment variables."""

    # Core settings
    storage_mode: str = Field(
        default="local",
        description="Storage backend: 'local' or 's3'",
        pattern="^(local|s3)$"
    )

    # Local storage
    local_base_path: str = Field(
        default="output",
        description="Base directory for local artifact storage"
    )

    # S3 configuration
    test_output_bucket: str = Field(
        default="",
        description="S3 bucket for test artifacts (required if storage_mode=s3)"
    )
    aws_region: str = Field(
        default="eu-west-2",
        description="AWS region"
    )
    kms_key_id: str = Field(
        default="",
        description="KMS key ARN for SSE-KMS encryption"
    )

    # GAMP-5 compliance
    artifact_retention_days: int = Field(
        default=2555,  # 7 years
        description="Retention period for pharmaceutical records"
    )
    enable_audit_logging: bool = Field(
        default=True,
        description="Enable detailed audit logging for artifact operations"
    )

    class Config:
        env_prefix = "STORAGE_"
        case_sensitive = True

    @field_validator('storage_mode')
    @classmethod
    def validate_storage_mode(cls, v: str) -> str:
        if v not in ("local", "s3"):
            raise ValueError("storage_mode must be 'local' or 's3'")
        return v

    @field_validator('test_output_bucket')
    @classmethod
    def validate_bucket_for_s3(cls, v: str, info) -> str:
        if info.data.get('storage_mode') == 's3' and not v:
            raise ValueError("test_output_bucket required when storage_mode=s3")
        return v
```

**Environment Variables:**
```bash
# Local dev
STORAGE_MODE=local
STORAGE_LOCAL_BASE_PATH=./output

# AWS production
STORAGE_MODE=s3
STORAGE_TEST_OUTPUT_BUCKET=pharma-test-artifacts-prod
STORAGE_AWS_REGION=eu-west-2
STORAGE_KMS_KEY_ID=arn:aws:kms:eu-west-2:ACCOUNT_ID:key/KEY_ID
STORAGE_ARTIFACT_RETENTION_DAYS=2555
```

---

## Next Agent Guidance

The task-executor should follow this implementation strategy:

### Phase 1: Core Adapter Structure
1. Create `main/src/adapters/storage.py` with:
   - `StorageProvider` Protocol defining interface contract
   - `StorageConfig` dataclass extending Pydantic settings
   - `StorageFactory` for dependency injection

2. Create `main/src/adapters/local_adapter.py`:
   - Implement `LocalStorageAdapter(StorageProvider)`
   - Use `aiofiles` for async file I/O
   - Include semaphore for concurrency control
   - NO fallback logic - raise explicit exceptions

3. Create `main/src/adapters/s3_adapter.py`:
   - Implement `S3StorageAdapter(StorageProvider)`
   - Use `aiobotocore` for async S3
   - Enforce SSE-KMS encryption
   - Generate pre-signed URLs (24-hour expiry default)
   - Validate metadata fits 2KB S3 limit

### Phase 2: Configuration Integration
1. Update `main/src/shared/config.py` to include `StorageSettings`
2. Add environment variable examples to `.env.example`
3. Update `Config` dataclass to include storage configuration

### Phase 3: Metadata Persistence
1. Implement metadata structure matching GAMP-5 audit trail requirements
2. Add helper method: `_format_audit_metadata(job_id, category, user_id, timestamp)`
3. Ensure metadata persists with both local (as JSON) and S3 (as object metadata)

### Phase 4: Download URL Generation
1. Implement `generate_download_url(artifact_id, expiry_seconds)` in both adapters
2. Local: return relative path like `/artifacts/{artifact_id}`
3. S3: return pre-signed URL with 24-hour default expiry
4. Validate expiry is within 7-day S3 limit (604800 seconds)

### Phase 5: Testing Implementation
1. Create `main/tests/test_storage_adapter.py`:
   - Use `pytest-asyncio` for async tests
   - Use `moto` to mock S3 in tests
   - Parametrize tests for both local and S3 modes
   - Test metadata persistence, error handling, cross-platform paths

2. Create integration test fixtures:
   - `local_temp_dir` fixture
   - `s3_client` and `s3_bucket` fixtures with moto mock
   - Parametrized `storage_adapter` fixture

### Critical Requirements for task-executor:
- ✅ NO FALLBACK LOGIC: Every error must propagate with full diagnostics
- ✅ Use async/await: All file and S3 operations must be async
- ✅ Protocol-based: Use `typing.Protocol` for interface contract
- ✅ Dependency injection: Accept storage adapter as constructor parameter
- ✅ GAMP-5 metadata: Include gamp_category, timestamps, attributability
- ✅ SSE-KMS: Enforce encryption for S3 operations
- ✅ Cross-platform: Use `pathlib.Path` for all file paths
- ✅ Semaphore bounds: Limit concurrent operations to prevent resource exhaustion
- ✅ Tests: Parametrized tests covering both storage modes

---

## Files Referenced

### Documentation Sources
1. boto3 S3 documentation: https://github.com/boto/boto3
2. aiobotocore documentation: https://github.com/aio-libs/aiobotocore
3. aiofiles documentation: https://github.com/tinche/aiofiles
4. Pydantic Settings: https://github.com/pydantic/pydantic-settings
5. GAMP-5 Compliance: https://www.scilife.io/blog/gamp5-for-gxp-compliant-computerized-systems
6. AWS S3 Security: https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html
7. AWS S3 Consistency: https://aws.amazon.com/s3/consistency/
8. Moto AWS Mocking: https://github.com/getmoto/moto
9. pytest-asyncio: https://github.com/pytest-dev/pytest-asyncio

### Project Files Read
- `.claude/state/prp-workflow-state.md` - Task status
- `.claude/state/current-task-context.md` - Task definition
- `PRPs/tasks/1.1-storage-adapter.md` - Task specification
- `main/src/shared/config.py` - Existing configuration patterns
- `main/src/shared/output_manager.py` - Output handling (reference for error patterns)

### Code Examples Provided
- aiobotocore async S3 operations with context managers
- aiofiles async file I/O patterns with error handling
- Protocol-based storage abstraction design
- Dependency injection factory pattern
- S3 bucket policy for SSE-KMS enforcement
- Moto/pytest fixtures for parametrized testing
- GAMP-5 metadata structure and validation

---

## Summary

Task 1.1 requires a production-grade storage abstraction layer that bridges local development and AWS S3 production deployment while maintaining GAMP-5 pharmaceutical compliance. The implementation must:

1. **Support Dual Modes**: Local filesystem (dev) and S3 (production) with identical interfaces
2. **Enforce Compliance**: GAMP-5 audit trails, ALCOA+ principles, metadata persistence
3. **Use Async Patterns**: Full async/await support compatible with LlamaIndex workflows
4. **Fail Explicitly**: NO fallback logic - all errors propagate with complete diagnostics
5. **Secure by Default**: SSE-KMS encryption, pre-signed URLs, WORM capability
6. **Test Thoroughly**: Parametrized tests validating both storage modes identically

The research has identified all necessary libraries, patterns, gotchas, and compliance requirements. task-executor can now implement with confidence using Protocol-based abstraction, aiobotocore for async S3, aiofiles for async file I/O, and comprehensive moto-based testing.

---

**Status:** Research complete - all required information gathered for implementation
**Quality Checkpoint:** All GAMP-5 and ALCOA+ requirements identified and mapped to implementation
**Next Step:** task-executor proceeds with implementation phase

