"""
Test suite for Clerk JWT authentication in FastAPI endpoints.

Tests JWT verification, authentication failures, authorization checks,
and ALCOA+ audit logging with Clerk user context.
"""

import io
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.app import app
from api.audit import initialize_audit_logger
from api.dependencies import (
    get_job_lock,
    get_job_queue,
    get_job_repository,
    get_storage_adapter,
    initialize_job_infrastructure,
    require_clerk_user,
)
from api.models import ClerkClaims, JobRecord


@pytest.fixture
def test_client() -> TestClient:
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_storage() -> AsyncMock:
    """Create mock storage adapter."""
    storage = AsyncMock()
    storage.save_artifact.return_value = "file:///output/test_urs.txt"
    storage.generate_download_url.return_value = "http://localhost/download/test"
    return storage


@pytest.fixture(autouse=True)
def setup_audit_logger(tmp_path: Path) -> None:
    """Initialize audit logger with temporary directory."""
    audit_dir = tmp_path / "audit"
    initialize_audit_logger(str(audit_dir))


@pytest.fixture
def job_infrastructure() -> tuple:
    """Initialize job infrastructure for testing."""
    return initialize_job_infrastructure()


class TestClerkJWTVerification:
    """Test Clerk JWT token verification logic."""

    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Set up mock Clerk environment variables."""
        # Generate mock RSA key pair for testing
        private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj
MzEfYyjiWA4R4/M2bS1+fWIcPm15j7A3U+odCatY5VEdzjg2Q4r3IZ7lgkUn19cD
q6t0zPZ0zfhFvCMiF7FjZqWqnKmKj/wQKbCgJPCp+qEsOmQx8cCLEDANBgkqhkiG
9w0BAQEFAAOCAg8AMIICCgKCAgEAuVSU1LfVLPHCozMxH2Mo4lgOEePzNm0tfn1i
HD5teY+wN1PqHQmrWOVRHc44NkOK9yGe5YJH3B2d+s6QgwPlFpEJt+15cIgmWpPD
0wOvP0P1fBPvF7QMN2p9zp2c5V8CfCj3x+x5I+w0J4Ew/Bw+yQlC3bCGEL1l7s0X
1E2tRIjgI9Y+VD1T3q+5chvU7YZCKvYmP5rExV3bVTl4I2KWy4u0rBv6g1aQ4N+G
pFqD2V+T9X0N9xwZ2W8qF4B5cA4Jn3xW7D7H1F4vP9uXEQ+TpPK2LQC7VJT1+fVx
fCMiF7FjZqWqnKmKj/wQKbCgJPCp+qEsOmQx8cAgECAwEAAQ==
-----END PRIVATE KEY-----"""

        public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu1SU1LfVLPHCozMxH2Mo
4lgOEePzNm0tfn1iHD5teY+wN1PqHQmrWOVRHc44NkOK9yGe5YJFJ9fXA6urdMz2
dM34RbwjIhexY2alqpypio/8ECmwoCTwqfqhLDpkMfHAixAwDQYJKoZIhvcNAQEB
BQADggEPADCCAQoCggEBALtUlNS31SzxwqMzMR9jKOJYDhHj8zZtLX59Yhw+bXmP
sDdT6h0Jq1jlUR3OODZDivchkuWCR9wdnfrOkIMD5RaRCbfteXCIJlqTw9MDrz9D
9XwT7xe0DDdqfc6dnOVfAnwo98fseSPsNCeBMPwcPskJQt2whhC9Ze7NF9RNrUSI
4CPWPlQ9U96vuXIb1O2GQir2Jj+axMVd21U5eCNilsuLtKwb+oNWkODfhqRag9lf
k/V9DfccGdlvKheAeXAOCZ98Vuw+x9ReLz/blxEPk6Tyti0Au1SU9fn1cXwjIhex
Y2alqpypAgMBAAE=
-----END PUBLIC KEY-----"""

        monkeypatch.setenv("CLERK_PEM_PUBLIC_KEY", public_key)
        monkeypatch.setenv("CLERK_ISSUER", "https://test-instance.clerk.accounts.dev")
        monkeypatch.setenv("CLERK_JWT_AUDIENCE", "https://api.test.com")

        return {"private_key": private_key, "public_key": public_key}

    @pytest.fixture
    def valid_jwt_token(self, mock_env_vars):
        """Generate a valid JWT token for testing."""
        payload = {
            "sub": "user_2abc123xyz",
            "email": "testuser@example.com",
            "email_verified": True,
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,  # 1 hour expiration
            "iss": "https://test-instance.clerk.accounts.dev",
            "aud": "https://api.test.com",
            "azp": "https://app.test.com"
        }

        # Sign token with private key
        token = jwt.encode(
            payload,
            mock_env_vars["private_key"],
            algorithm="RS256"
        )

        return token

    @pytest.fixture
    def expired_jwt_token(self, mock_env_vars):
        """Generate an expired JWT token for testing."""
        payload = {
            "sub": "user_2abc123xyz",
            "email": "testuser@example.com",
            "email_verified": True,
            "iat": int(time.time()) - 7200,  # 2 hours ago
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
            "iss": "https://test-instance.clerk.accounts.dev",
            "aud": "https://api.test.com"
        }

        token = jwt.encode(
            payload,
            mock_env_vars["private_key"],
            algorithm="RS256"
        )

        return token

    @pytest.fixture
    def invalid_issuer_token(self, mock_env_vars):
        """Generate a token with invalid issuer."""
        payload = {
            "sub": "user_2abc123xyz",
            "email": "testuser@example.com",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "iss": "https://malicious.com",  # Wrong issuer
            "aud": "https://api.test.com"
        }

        token = jwt.encode(
            payload,
            mock_env_vars["private_key"],
            algorithm="RS256"
        )

        return token

    @pytest.mark.asyncio
    async def test_valid_token_returns_clerk_claims(
        self, mock_env_vars, valid_jwt_token
    ):
        """Test that valid JWT token returns ClerkClaims object."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_jwt_token
        )

        # Call authentication dependency
        user_claims = await require_clerk_user(credentials)

        # Verify ClerkClaims object
        assert isinstance(user_claims, ClerkClaims)
        assert user_claims.sub == "user_2abc123xyz"
        assert user_claims.email == "testuser@example.com"
        assert user_claims.email_verified is True
        assert user_claims.iss == "https://test-instance.clerk.accounts.dev"

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self, mock_env_vars, expired_jwt_token):
        """Test that expired token raises 401 HTTPException."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=expired_jwt_token
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_clerk_user(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_invalid_issuer_raises_401(
        self, mock_env_vars, invalid_issuer_token
    ):
        """Test that token with wrong issuer raises 401."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=invalid_issuer_token
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_clerk_user(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "issuer" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_invalid_signature_raises_401(self, mock_env_vars):
        """Test that token with invalid signature raises 401."""
        # Create token with different private key
        wrong_private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDifferentkey
-----END PRIVATE KEY-----"""

        payload = {
            "sub": "user_2abc123xyz",
            "email": "testuser@example.com",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "iss": "https://test-instance.clerk.accounts.dev"
        }

        # Sign with wrong key
        invalid_token = jwt.encode(
            payload,
            wrong_private_key,
            algorithm="RS256"
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=invalid_token
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_clerk_user(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_missing_sub_claim_raises_401(self, mock_env_vars):
        """Test that token missing 'sub' claim raises 401."""
        payload = {
            # Missing 'sub' claim
            "email": "testuser@example.com",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "iss": "https://test-instance.clerk.accounts.dev"
        }

        token = jwt.encode(
            payload,
            mock_env_vars["private_key"],
            algorithm="RS256"
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_clerk_user(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "user identifier" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_missing_email_claim_raises_401(self, mock_env_vars):
        """Test that token missing 'email' claim raises 401."""
        payload = {
            "sub": "user_2abc123xyz",
            # Missing 'email' claim
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "iss": "https://test-instance.clerk.accounts.dev"
        }

        token = jwt.encode(
            payload,
            mock_env_vars["private_key"],
            algorithm="RS256"
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_clerk_user(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "email" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_missing_clerk_config_raises_500(self, monkeypatch):
        """Test that missing CLERK_PEM_PUBLIC_KEY raises 500 error."""
        # Remove environment variable
        monkeypatch.delenv("CLERK_PEM_PUBLIC_KEY", raising=False)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="fake_token"
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_clerk_user(credentials)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "not configured" in exc_info.value.detail.lower()


class TestFastAPIAuthentication:
    """Test authentication integration with FastAPI routes."""

    @pytest.fixture
    def auth_headers(self):
        """Create mock authentication headers."""
        return {"Authorization": "Bearer mock_token_12345"}

    @pytest.fixture
    def mock_clerk_user(self):
        """Create mock ClerkClaims for testing."""
        return ClerkClaims(
            sub="user_2abc123xyz",
            email="testuser@example.com",
            email_verified=True,
            iat=int(time.time()),
            exp=int(time.time()) + 3600,
            iss="https://test-instance.clerk.accounts.dev"
        )

    @patch("api.dependencies.require_clerk_user")
    def test_authenticated_job_submission_logs_clerk_context(
        self, mock_require_user, test_client, mock_storage,
        job_infrastructure, mock_clerk_user, tmp_path
    ):
        """Test that job submission captures Clerk user context in audit logs."""
        # Mock authentication to return ClerkClaims
        async def mock_auth(*args, **kwargs):
            return mock_clerk_user

        mock_require_user.side_effect = mock_auth

        # Override dependencies
        queue, repo, lock = job_infrastructure
        app.dependency_overrides[get_storage_adapter] = lambda: mock_storage
        app.dependency_overrides[get_job_queue] = lambda: queue
        app.dependency_overrides[get_job_repository] = lambda: repo
        app.dependency_overrides[get_job_lock] = lambda: lock

        # Create test URS file
        urs_content = b"Test user requirements specification content"
        test_file = ("test_urs.txt", io.BytesIO(urs_content), "text/plain")

        # Submit job with authentication
        response = test_client.post(
            "/jobs",
            files={"file": test_file},
            headers={"Authorization": "Bearer mock_token"}
        )

        # Verify response
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert "job_id" in response_data
        job_id = response_data["job_id"]

        # Verify audit log captured Clerk context
        audit_dir = Path("logs/audit/jobs")
        audit_file = audit_dir / f"audit_{datetime.now(UTC).strftime('%Y%m%d')}.jsonl"

        assert audit_file.exists()

        # Read audit log
        with open(audit_file, "r") as f:
            audit_entries = [json.loads(line) for line in f if line.strip()]

        # Find job submission event
        submit_event = next(
            (e for e in audit_entries if e["event_type"] == "submit" and e["job_id"] == job_id),
            None
        )

        assert submit_event is not None
        assert submit_event["user_id"] == mock_clerk_user.sub
        assert submit_event["user_email"] == mock_clerk_user.email
        assert submit_event["token_iat"] == mock_clerk_user.iat
        assert "token_exp" in submit_event["metadata"]

    @patch("api.dependencies.require_clerk_user")
    def test_authorization_check_prevents_unauthorized_access(
        self, mock_require_user, test_client, mock_storage,
        job_infrastructure, mock_clerk_user
    ):
        """Test that users cannot access jobs owned by other users."""
        # Override dependencies
        queue, repo, lock = job_infrastructure
        app.dependency_overrides[get_storage_adapter] = lambda: mock_storage
        app.dependency_overrides[get_job_queue] = lambda: queue
        app.dependency_overrides[get_job_repository] = lambda: repo
        app.dependency_overrides[get_job_lock] = lambda: lock

        # Create job owned by different user
        different_user = ClerkClaims(
            sub="user_999different",
            email="different@example.com",
            email_verified=True,
            iat=int(time.time()),
            exp=int(time.time()) + 3600,
            iss="https://test-instance.clerk.accounts.dev"
        )

        # Mock authentication for job creation
        async def mock_auth_user1(*args, **kwargs):
            return different_user

        mock_require_user.side_effect = mock_auth_user1

        # Create job
        urs_content = b"Test content"
        test_file = ("test.txt", io.BytesIO(urs_content), "text/plain")
        response = test_client.post(
            "/jobs",
            files={"file": test_file},
            headers={"Authorization": "Bearer token1"}
        )

        job_id = response.json()["job_id"]

        # Now try to access with different user
        async def mock_auth_user2(*args, **kwargs):
            return mock_clerk_user

        mock_require_user.side_effect = mock_auth_user2

        response = test_client.get(
            f"/jobs/{job_id}",
            headers={"Authorization": "Bearer token2"}
        )

        # Verify 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "not authorized" in response.json()["detail"].lower()

        # Clean up
        app.dependency_overrides.clear()


class TestALCOAPlusCompliance:
    """Test ALCOA+ principles implementation in authentication."""

    def test_audit_log_contains_all_alcoa_plus_fields(self, tmp_path):
        """Test that audit logs include all ALCOA+ required fields."""
        from api.audit import AuditLogger
        from api.models import JobStatus

        # Create audit logger
        audit_dir = tmp_path / "audit"
        audit_logger = AuditLogger(audit_directory=str(audit_dir))

        # Log event with Clerk context
        audit_logger.log_event(
            job_id="job_test_123",
            event_type="submit",
            user_id="user_2abc123xyz",
            status=JobStatus.PENDING,
            user_email="testuser@example.com",
            token_iat=1699000000,
            ip_address="192.168.1.1",
            session_id="sess_abc123",
            metadata={"token_exp": 1699003600}
        )

        # Read audit file
        audit_file = audit_dir / f"audit_{datetime.now(UTC).strftime('%Y%m%d')}.jsonl"
        with open(audit_file, "r") as f:
            audit_record = json.loads(f.readline())

        # Verify ALCOA+ fields
        assert "user_id" in audit_record  # Attributable
        assert "user_email" in audit_record  # Attributable (human-readable)
        assert "timestamp" in audit_record  # Contemporaneous
        assert "token_iat" in audit_record  # Contemporaneous (token lifecycle)
        assert "ip_address" in audit_record  # Contemporaneous (context)
        assert "session_id" in audit_record  # Complete (event linking)
        assert "alcoa_attributable" in audit_record  # Explicit ALCOA marker
        assert "alcoa_contemporaneous" in audit_record  # Explicit ALCOA marker
        assert audit_record["alcoa_original"] is True  # Immutable

    @pytest.mark.asyncio
    async def test_no_fallback_logic_on_authentication_failure(self, monkeypatch):
        """Test that authentication failures raise explicit errors (no fallback)."""
        # Set up minimal config (will still fail on invalid token)
        monkeypatch.setenv("CLERK_PEM_PUBLIC_KEY", "fake_key")
        monkeypatch.setenv("CLERK_ISSUER", "https://test.clerk.com")

        # Create invalid credentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token_xyz"
        )

        # Verify explicit failure (no default/fallback user)
        with pytest.raises(HTTPException) as exc_info:
            # This should raise 401, NOT return a default user
            await require_clerk_user(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        # Verify error is explicit (not masked with fallback)
        assert exc_info.value.detail != ""
