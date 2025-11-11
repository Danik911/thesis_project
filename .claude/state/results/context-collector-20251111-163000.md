# Context Collector Result - 20251111-163000

## Agent Configuration
- Agent: context-collector
- Task ID: 1.4
- Invoked: 2025-11-11T16:30:00Z
- Duration: 25 minutes
- Status: SUCCESS

## Task Understanding

Task 1.4 aims to integrate Clerk authentication with the existing FastAPI application to replace mock user authentication with production-grade JWT verification. This integration must:

1. Validate Clerk JWT tokens using EU endpoints for data residency compliance
2. Extract authenticated user context (Clerk user ID from `sub` claim) for job traceability
3. Propagate user identity through GAMP-5 audit logs (ALCOA+ compliance)
4. Implement fail-closed authentication (401 on any failure, NO FALLBACK LOGIC)
5. Provide developer-friendly testing with Clerk test mode
6. Cache JWKS keys to minimize latency while respecting key rotation
7. Handle clock skew tolerance for JWT expiration validation

The implementation must integrate seamlessly with the existing FastAPI app structure from Task 1.3 (main/api/app.py, dependencies.py, models.py, audit.py) while maintaining pharmaceutical compliance standards.

---

## Research Findings

### Clerk Python SDK Integration

**Official Package:**
- **Package Name:** `clerk-backend-api`
- **Latest Version:** 4.0.0 (released Nov 10, 2025)
- **Python Compatibility:** >=3.9.2 (includes Python 3.12, 3.13, 3.14)
- **Installation:** `uv add clerk-backend-api`
- **Repository:** https://github.com/clerk/clerk-sdk-python
- **PyPI:** https://pypi.org/project/clerk-backend-api/

**Key Features:**
- Auto-generated from Clerk's OpenAPI specification
- Full async/await support with `AsyncClient`
- Context manager protocol for resource management
- Built-in `authenticate_request()` method for JWT verification
- Supports both sync and async operations

**JWT Verification API:**

The clerk-backend-api SDK provides a high-level `authenticate_request()` method:

```python
from clerk_backend_api import Clerk
from clerk_backend_api.security import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions
import httpx

sdk = Clerk(bearer_auth=os.getenv('CLERK_SECRET_KEY'))
request_state = sdk.authenticate_request(
    request,  # httpx.Request object
    AuthenticateRequestOptions(
        authorized_parties=['https://example.com']
    )
)

if request_state.is_signed_in:
    # Access verified payload
    user_id = request_state.payload.get('sub')
```

**Alternative: Manual JWT Verification with PyJWT**

For more control and networkless verification (recommended for FastAPI):

```python
import jwt
from jwt import PyJWTError

CLERK_PUBLIC_KEY = os.getenv("CLERK_PEM_PUBLIC_KEY")  # PEM format
CLERK_ISSUER = os.getenv("CLERK_ISSUER")  # e.g., "https://your-instance.clerk.accounts.dev"

try:
    payload = jwt.decode(
        token,
        CLERK_PUBLIC_KEY,
        algorithms=["RS256"],
        issuer=CLERK_ISSUER,
        options={
            "verify_exp": True,
            "verify_iat": True,
            "leeway": 10  # Clock skew tolerance in seconds
        }
    )
    user_id = payload.get('sub')
    user_email = payload.get('email')
except jwt.ExpiredSignatureError:
    raise HTTPException(status_code=401, detail="Token expired")
except jwt.InvalidIssuerError:
    raise HTTPException(status_code=401, detail="Invalid token issuer")
except jwt.InvalidSignatureError:
    raise HTTPException(status_code=401, detail="Invalid token signature")
except PyJWTError as e:
    raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")
```

**EU Endpoint Configuration:**

For GDPR/data residency compliance, configure Clerk SDK to use EU endpoints:

```python
# US endpoint (default)
clerk = Clerk(
    bearer_auth=os.getenv('CLERK_SECRET_KEY'),
    server_url="https://api.clerk.com/v1"
)

# EU endpoint (for pharmaceutical data residency)
clerk = Clerk(
    bearer_auth=os.getenv('CLERK_SECRET_KEY'),
    server_url="https://eu-api.clerk.com/v1"
)
```

**JWKS Endpoint URLs:**
- **US JWKS:** `https://api.clerk.com/v1/jwks`
- **EU JWKS:** `https://eu-api.clerk.com/v1/jwks`
- **Frontend API JWKS:** `https://{frontend-api-url}/.well-known/jwks.json`

**JWKS Caching Strategy:**

```python
import time
from typing import Optional
import httpx

class JWKSCache:
    """Cache JWKS keys with TTL for performance optimization"""

    def __init__(self, ttl_seconds: int = 900):  # 15 minutes default
        self.cache: Optional[dict] = None
        self.cache_time: Optional[float] = None
        self.ttl_seconds = ttl_seconds

    def get(self) -> Optional[dict]:
        if self.cache and time.time() - self.cache_time < self.ttl_seconds:
            return self.cache
        return None

    def set(self, jwks: dict):
        self.cache = jwks
        self.cache_time = time.time()

# Global cache instance
jwks_cache = JWKSCache(ttl_seconds=900)  # 15 minutes

async def get_jwks(endpoint: str = "https://eu-api.clerk.com/v1/jwks") -> dict:
    cached = jwks_cache.get()
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        response = await client.get(endpoint)
        response.raise_for_status()
        jwks = response.json()
        jwks_cache.set(jwks)
        return jwks
```

**Cache TTL Recommendations:**
- **Development:** 5-10 minutes (faster key rotation testing)
- **Production:** 15-30 minutes (balance freshness vs network overhead)
- **Cache control headers:** Clerk JWKS endpoints return `max-age=15` with `stale-while-revalidate=15`

**Clock Skew Handling:**

PyJWT supports `leeway` parameter for clock skew tolerance:

```python
# Recommended: 5-10 seconds tolerance
payload = jwt.decode(
    token,
    public_key,
    algorithms=["RS256"],
    options={
        "verify_exp": True,
        "leeway": 10  # Allow 10 seconds clock skew
    }
)
```

**Clock Skew Best Practices:**
- **Development:** 10-60 seconds (local system clock may drift)
- **Production:** 5-10 seconds (servers should use NTP)
- **Clerk default:** 5000ms (5 seconds) in `verifyToken()` method

---

### FastAPI Authentication Patterns

**HTTPBearer Token Extraction:**

FastAPI's `HTTPBearer` security class handles Authorization header parsing:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated

security = HTTPBearer()

async def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    token = credentials.credentials
    # Verify token and return claims
    return verified_claims
```

**HTTPBearer automatically:**
- Extracts `Authorization: Bearer <token>` header
- Validates header format
- Raises 401 if header missing or malformed
- Can be configured with `auto_error=False` for optional auth

**Dependency Injection Pattern:**

```python
# Type alias for dependency
CurrentUser = Annotated[ClerkClaims, Depends(require_clerk_user)]

# Use in route
@app.post("/jobs")
async def create_job(
    user: CurrentUser,
    job_data: dict
) -> dict:
    # user is automatically ClerkClaims object with validated JWT
    return {"created_by": user.sub}
```

**Async Compatibility:**

FastAPI supports both sync and async dependencies. For JWT verification:
- **CPU-bound operations** (cryptographic verification): Use sync functions
- **Network I/O** (JWKS fetching): Use async functions

```python
# Sync JWT verification (recommended - cryptographic operations are CPU-bound)
def verify_jwt_sync(token: str) -> dict:
    return jwt.decode(token, public_key, algorithms=["RS256"])

# Async for network calls
async def fetch_jwks_async(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

**Context Propagation:**

FastAPI's dependency system automatically propagates user context through request lifecycle:

```python
@app.post("/jobs")
async def create_job(
    request: Request,
    user: CurrentUser,
    storage: StorageAdapterDep
) -> dict:
    # User context available in all dependencies
    # Can pass to audit logger, storage adapter, etc.
    await audit_logger.log_event(
        event_type="JOB_CREATED",
        user=user,  # ClerkClaims object
        request=request,
        metadata={"action": "create_job"}
    )
```

**HTTPException 401 Error Handling:**

```python
from fastapi import HTTPException, status

class ClerkAuthenticationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

# Usage
if not token:
    raise ClerkAuthenticationError("Missing authentication token")
```

**Global Exception Handler for Auth Errors:**

```python
@app.exception_handler(ClerkAuthenticationError)
async def clerk_auth_exception_handler(request: Request, exc: ClerkAuthenticationError):
    # Log authentication failure for GAMP-5 audit trail
    await auth_audit_logger.log_authentication_failure(
        failure_reason=exc.detail,
        request=request
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": "Authentication failed"},  # Generic message
        headers=exc.headers
    )
```

---

### Pharmaceutical Compliance

**GAMP-5 Traceability Requirements:**

GAMP-5 (Good Automated Manufacturing Practice) requires complete user traceability for all actions affecting regulated data:

1. **User Identity Capture:** Extract `sub` claim (Clerk user ID) from JWT
2. **Job Linkage:** Associate every job record with authenticated Clerk user
3. **Audit Trail:** Log all authentication events (success, failure, token refresh)
4. **Immutability:** Append-only audit logs with no modification capability
5. **Retention:** 7-year minimum retention for pharmaceutical records

**Implementation:**

```python
# models.py - Updated JobRecord
class JobRecord(BaseModel):
    job_id: str
    user_id: str  # Clerk user ID from sub claim
    user_email: str  # Clerk email for human-readable attribution
    created_at: datetime
    status: JobStatus

    # GAMP-5 metadata
    gamp_category: str
    created_by_token_iat: int  # Token issued-at timestamp for lifecycle tracking

    @classmethod
    def from_clerk_user(cls, job_id: str, user: ClerkClaims, **kwargs):
        return cls(
            job_id=job_id,
            user_id=user.sub,
            user_email=user.email,
            created_by_token_iat=user.iat,
            **kwargs
        )
```

**ALCOA+ Principles for Authentication:**

ALCOA+ extends ALCOA (Attributable, Legible, Contemporaneous, Original, Accurate) with three additional principles:

| Principle | Implementation for Authentication |
|-----------|----------------------------------|
| **Attributable** | Capture `sub` (Clerk user ID), `email`, IP address, user-agent |
| **Legible** | Structured JSON logging, human-readable timestamps |
| **Contemporaneous** | Log at time of event (not batched), include `iat` and current timestamp |
| **Original** | Append-only logs, cryptographic integrity (SHA-256 hashes) |
| **Accurate** | Validate all JWT claims before logging, reject incomplete tokens |
| **Complete** | Include full token lifecycle data (`iat`, `exp`, `aud`, `iss`), request context |
| **Consistent** | Standard format across all events, version-controlled schemas |
| **Enduring** | 7+ year retention, immutable storage (consider S3 Object Lock) |
| **Available** | Queryable via audit log API, searchable by user/job/date |

**Audit Trail Requirements:**

```python
# audit.py - Extended AuditLogEntry
class AuditLogEntry(BaseModel):
    timestamp: datetime  # Contemporaneous
    job_id: Optional[str]
    event_type: str  # "AUTH_SUCCESS", "AUTH_FAILURE", "TOKEN_REFRESH", "JOB_CREATED"
    user_id: str  # Clerk sub claim (Attributable)
    user_email: str  # Human-readable attribution
    status: str  # "success", "failure"

    # ALCOA+ metadata
    ip_address: Optional[str]  # Client IP for contemporaneous context
    user_agent: Optional[str]  # Browser/client identification
    token_iat: Optional[int]  # Token issued-at for lifecycle tracking
    token_exp: Optional[int]  # Token expiration for security analysis
    session_id: Optional[str]  # Link related authentication events

    # Compliance metadata
    metadata: dict[str, Any]  # Complete context (ALCOA+)
    event_hash: Optional[str]  # Cryptographic integrity (SHA-256)
```

**Authentication Event Logging:**

Must log these events for GAMP-5 compliance:

1. **AUTH_SUCCESS:** User successfully authenticated with valid JWT
2. **AUTH_FAILURE:** Authentication failed (expired token, invalid signature, missing token)
3. **TOKEN_REFRESH:** User refreshed authentication token (track session continuity)
4. **JOB_CREATED:** User created job (link to authenticated identity)
5. **JOB_ACCESSED:** User accessed job status/results (authorization check)
6. **AUTH_LOGOUT:** User logged out (optional, depends on frontend implementation)

**Data Sanitization (CRITICAL):**

NEVER log sensitive data in audit trails:

```python
# ❌ NEVER LOG:
audit_logger.log_event(metadata={"token": actual_jwt_token})  # Exposes credentials

# ✅ ALWAYS LOG:
audit_logger.log_event(metadata={
    "token_iat": user.iat,
    "token_exp": user.exp,
    "user_id": user.sub,
    "email": user.email
})
```

**21 CFR Part 11 Considerations:**

While not in scope for MVP, be aware of future requirements:

- Electronic signatures (Clerk user action = signature)
- Audit trail review capabilities (query API for job history)
- System validation documentation (test evidence)
- Access controls (role-based authorization - future task)

---

### JWT Security Best Practices

**JWKS Key Caching:**

Clerk JWKS endpoints return cache control headers:
- `Cache-Control: max-age=15, stale-while-revalidate=15, stale-if-error=86400`
- **Interpretation:** Cache for 15 seconds, allow stale for 15 seconds while revalidating, use stale for up to 24 hours during errors

**Recommended Cache Strategy:**

```python
class JWKSCache:
    def __init__(self, ttl_seconds: int = 900, stale_ttl_seconds: int = 86400):
        self.cache: Optional[dict] = None
        self.cache_time: Optional[float] = None
        self.ttl_seconds = ttl_seconds
        self.stale_ttl_seconds = stale_ttl_seconds

    def get(self, allow_stale: bool = False) -> Optional[dict]:
        if not self.cache:
            return None

        age = time.time() - self.cache_time

        if age < self.ttl_seconds:
            return self.cache  # Fresh

        if allow_stale and age < self.stale_ttl_seconds:
            return self.cache  # Stale but acceptable during errors

        return None  # Expired
```

**Key Rotation Handling:**

Clerk automatically rotates JWKS keys periodically. Your implementation must:

1. Cache keys with TTL (15-30 minutes)
2. Refresh on cache expiration
3. Handle verification failures gracefully (retry with fresh keys)
4. Never fail permanently due to key rotation

```python
async def verify_jwt_with_retry(token: str, max_retries: int = 1) -> dict:
    for attempt in range(max_retries + 1):
        try:
            jwks = await get_jwks()
            # Verify token with cached keys
            return jwt.decode(token, jwks, algorithms=["RS256"])
        except jwt.InvalidSignatureError:
            if attempt < max_retries:
                # Key might have rotated, invalidate cache and retry
                jwks_cache.invalidate()
                continue
            raise
```

**Clock Skew Tolerance:**

Recommended values:

- **Development:** 60 seconds (local machines may have clock drift)
- **Staging:** 10 seconds (CI/CD environments)
- **Production:** 5 seconds (NTP-synchronized servers)

**Implementation:**

```python
# PyJWT
payload = jwt.decode(
    token,
    public_key,
    algorithms=["RS256"],
    options={"leeway": 10}  # 10 seconds tolerance
)

# Clerk verifyToken() (JavaScript/TypeScript)
const payload = await clerk.verifyToken(token, {
    clockSkewInMs: 5000  // 5 seconds = 5000ms
});
```

**Audience Validation:**

The `aud` (audience) claim identifies intended recipients. Configure based on your API:

```python
CLERK_JWT_AUDIENCE = os.getenv("CLERK_JWT_AUDIENCE")  # e.g., "https://api.example.com"

payload = jwt.decode(
    token,
    public_key,
    algorithms=["RS256"],
    audience=CLERK_JWT_AUDIENCE  # Validates aud claim matches
)
```

**Note:** Clerk session tokens may not include `aud` by default. Check your Clerk Dashboard JWT template configuration.

**Authorized Parties (azp) Validation:**

The `azp` claim contains the Origin header from the request. Validate to prevent CSRF:

```python
AUTHORIZED_ORIGINS = [
    "http://localhost:3000",  # Development
    "https://example.com",    # Production
    "https://app.example.com" # Production subdomain
]

azp = payload.get('azp')
if azp not in AUTHORIZED_ORIGINS:
    raise HTTPException(
        status_code=401,
        detail="Token not authorized for this origin"
    )
```

**Error Handling - Fail Closed:**

CRITICAL: All authentication errors MUST result in 401, NO FALLBACK LOGIC:

```python
# ✅ CORRECT - Fail closed
try:
    payload = jwt.decode(token, key, algorithms=["RS256"])
except jwt.ExpiredSignatureError:
    raise HTTPException(status_code=401, detail="Token expired")
except Exception as e:
    raise HTTPException(status_code=401, detail="Authentication failed")

# ❌ WRONG - Fallback logic
try:
    payload = jwt.decode(token, key, algorithms=["RS256"])
except jwt.ExpiredSignatureError:
    payload = {"sub": "anonymous", "confidence": 0.0}  # NEVER DO THIS
```

**Log Sanitization:**

Never log tokens or sensitive claims:

```python
# ❌ NEVER LOG:
logger.info(f"Received token: {token}")
logger.debug(f"JWT payload: {payload}")

# ✅ ALWAYS LOG:
logger.info(f"Authentication attempt for user: {payload.get('sub')}")
logger.debug(f"Token issued at: {payload.get('iat')}, expires: {payload.get('exp')}")
```

---

### Implementation Gotchas

**Common Clerk SDK Configuration Errors:**

1. **Wrong environment variable names:**
   - ❌ `CLERK_API_KEY` (doesn't exist)
   - ✅ `CLERK_SECRET_KEY` (Backend API authentication)

2. **Missing PEM key headers/footers:**
   - JWT verification requires proper PEM format:
   ```
   -----BEGIN PUBLIC KEY-----
   MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
   -----END PUBLIC KEY-----
   ```

3. **US vs EU endpoint confusion:**
   - Default SDK uses `https://api.clerk.com/v1` (US)
   - Must explicitly configure `server_url="https://eu-api.clerk.com/v1"` for EU

4. **JWKS endpoint mismatch:**
   - SDK endpoint and JWKS endpoint must match regions
   - US SDK + EU JWKS = verification failure

**EU Endpoint Configuration Mistakes:**

1. **Partial EU configuration:**
   - Must configure BOTH Backend API endpoint AND JWKS endpoint
   - Frontend API must also use EU endpoints

2. **Mixed region tokens:**
   - Tokens issued by US Frontend API cannot be verified with EU JWKS
   - Ensure all Clerk instances (frontend + backend) use same region

**Test Mode Setup Issues:**

1. **Development vs Production instances:**
   - Development instances have relaxed security (up to 100 test users)
   - Production instances require domain verification
   - Cannot mix dev tokens with prod verification

2. **Test token generation:**
   - Recommended: Create test users via Backend API, generate session tokens
   - Alternative: Use Clerk test mode with fixed OTP codes
   - Avoid: Manually crafted JWTs (won't match Clerk's signature)

**Integration with Existing FastAPI App:**

From Task 1.3, the app has:
- `main/api/dependencies.py` with `get_current_user()` returning `"mock_user_dev_001"`
- `main/api/models.py` with `JobRecord` having `user_id: str`
- `main/api/audit.py` with `AuditLogger.log_event()` accepting `user_id: str`

**Migration strategy:**

1. **Replace `get_current_user()` with `require_clerk_user()`:**
   ```python
   # OLD (dependencies.py)
   def get_current_user() -> str:
       return "mock_user_dev_001"

   # NEW (dependencies.py)
   async def require_clerk_user(
       credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
   ) -> ClerkClaims:
       # JWT verification logic
       return ClerkClaims(**verified_payload)
   ```

2. **Update type alias:**
   ```python
   # OLD
   CurrentUserDep = Annotated[str, Depends(get_current_user)]

   # NEW
   CurrentUserDep = Annotated[ClerkClaims, Depends(require_clerk_user)]
   ```

3. **Update route signatures:**
   ```python
   # OLD
   @app.post("/jobs")
   async def submit_job(user_id: CurrentUserDep) -> dict:
       # user_id is "mock_user_dev_001"

   # NEW
   @app.post("/jobs")
   async def submit_job(user: CurrentUserDep) -> dict:
       # user is ClerkClaims object
       user_id = user.sub
       user_email = user.email
   ```

4. **Update audit logging calls:**
   ```python
   # OLD
   audit_logger.log_event(
       job_id=job_id,
       event_type="submit",
       user_id=user_id,  # String "mock_user_dev_001"
       status=JobStatus.PENDING,
       metadata={}
   )

   # NEW
   audit_logger.log_event(
       job_id=job_id,
       event_type="submit",
       user_id=user.sub,  # Clerk user ID from JWT
       user_email=user.email,  # NEW: Add email for ALCOA+
       status=JobStatus.PENDING,
       metadata={
           "token_iat": user.iat,
           "token_exp": user.exp
       }
   )
   ```

**Known Package Compatibility Issues:**

1. **PyJWT < 2.9.0 with Python 3.12:**
   - Issue: Missing Python 3.12 support
   - Solution: Use PyJWT >= 2.9.0

2. **python-jose cryptography backend:**
   - Issue: `python-jose` requires explicit cryptography installation
   - Solution: `uv add python-jose[cryptography]` (includes bracket notation)

3. **FastAPI + HTTPBearer async:**
   - Issue: HTTPBearer works with both sync/async, but some middleware expects async
   - Solution: Make `require_clerk_user()` async for consistency

---

### Recommended Approach

**High-Level Implementation Strategy:**

1. **Install Clerk SDK and JWT libraries**
   - `uv add clerk-backend-api pyjwt cryptography`

2. **Create ClerkClaims Pydantic model**
   - Add to `main/api/models.py`
   - Include `sub`, `email`, `iat`, `exp`, `iss` fields

3. **Implement `require_clerk_user()` dependency**
   - Add to `main/api/dependencies.py`
   - Use HTTPBearer for token extraction
   - Verify JWT with PyJWT and Clerk public key
   - Return ClerkClaims object or raise 401

4. **Update existing FastAPI endpoints**
   - Replace `CurrentUserDep` (str) with `CurrentUserDep` (ClerkClaims)
   - Update route signatures to use `user: CurrentUserDep`
   - Extract `user.sub` and `user.email` in route handlers

5. **Extend audit logging**
   - Update `audit.py` to accept ClerkClaims or user metadata
   - Add `user_email`, `token_iat`, `ip_address` fields to AuditLogEntry
   - Create authentication event logging methods

6. **Create authentication audit logger**
   - New file: `main/api/auth_audit.py`
   - Methods: `log_authentication_success()`, `log_authentication_failure()`, `log_token_refresh()`

7. **Implement JWKS caching**
   - Create `JWKSCache` class in `main/api/auth.py`
   - Configure 15-minute TTL with stale-while-revalidate
   - Handle key rotation gracefully

8. **Add global exception handler**
   - Register `ClerkAuthenticationError` handler in app.py
   - Log all auth failures for GAMP-5 compliance
   - Return generic 401 messages (no detail leakage)

9. **Create comprehensive test suite**
   - New file: `main/tests/test_api_auth.py`
   - Fixtures: `mock_clerk_token`, `mock_expired_token`, `auth_headers`
   - Tests: Valid token (200), missing token (401), expired token (401), invalid signature (401)
   - Mock audit logging calls

10. **Document environment variables**
    - Update README or create `.env.example`
    - Required: `CLERK_SECRET_KEY`, `CLERK_PEM_PUBLIC_KEY`, `CLERK_ISSUER`
    - Optional: `CLERK_JWT_AUDIENCE`, `CLERK_SERVER_URL`

---

### Required Libraries/Versions

**Primary Dependencies:**

```
clerk-backend-api==4.0.0
pyjwt==2.9.0
cryptography>=42.0.0
httpx>=0.27.0  # For async JWKS fetching
```

**Rationale:**

- **clerk-backend-api 4.0.0:** Latest stable, Python 3.12 compatible, released Nov 10, 2025
- **PyJWT 2.9.0:** Adds Python 3.12 support, required for RS256 verification
- **cryptography >=42.0.0:** Backend for PyJWT RS256 operations, Python 3.12 compatible
- **httpx >=0.27.0:** Async HTTP client for JWKS fetching (already in project for boto3)

**Alternative JWT Library:**

```
python-jose[cryptography]==3.3.0  # Alternative to PyJWT
```

Use if you prefer python-jose over PyJWT. Both support RS256 and Python 3.12.

**Development/Testing Dependencies:**

```
pytest-mock>=3.12.0  # For mocking Clerk JWT verification
freezegun>=1.4.0     # For mocking datetime in tests
```

**Installation Command:**

```bash
# All required dependencies
uv add clerk-backend-api pyjwt cryptography httpx

# Development dependencies
uv add --dev pytest-mock freezegun
```

**Package Version Notes:**

- Pin exact versions for reproducible builds
- clerk-backend-api uses semantic versioning (MAJOR.MINOR.PATCH)
- PyJWT 2.9.0+ required for Python 3.12 (earlier versions lack support)
- cryptography auto-updated by PyJWT, but specify >=42.0.0 for Python 3.12 wheels

---

### Integration with Existing Code

**Files to Modify:**

1. **main/api/models.py** (Add ClerkClaims model)
   - New: `ClerkClaims(BaseModel)` for JWT payload validation
   - Update: `AuditLogEntry` to include `user_email`, `token_iat`, `ip_address`, `session_id`
   - Update: `JobRecord` to include `user_email` (optional, for human-readable audit)

2. **main/api/dependencies.py** (Replace mock auth with Clerk)
   - Replace: `get_current_user()` with `require_clerk_user()`
   - Add: `HTTPBearer` security instance
   - Add: `ClerkAuthenticationError` exception class
   - Update: `CurrentUserDep` type alias from `str` to `ClerkClaims`
   - Keep: Existing dependencies (`get_storage_adapter`, `get_job_queue`, etc.)

3. **main/api/audit.py** (Extend for Clerk context)
   - Update: `log_event()` to accept `user_email: str`, `token_iat: int`, `ip_address: str`
   - Add: `_enrich_metadata()` method to include token metadata
   - Add: `_generate_session_id()` for linking related events
   - Maintain: Existing ALCOA+ compliance structure

4. **main/api/app.py** (Update routes, add exception handler)
   - Update: `/jobs` POST endpoint to use `user: CurrentUserDep` (ClerkClaims)
   - Update: `/jobs/{job_id}` GET endpoint to use `user: CurrentUserDep`
   - Update: Audit log calls to include `user.email`, `user.iat`
   - Add: Global exception handler for `ClerkAuthenticationError`
   - Add: Authentication audit logging in exception handler

**Files to Create:**

1. **main/api/auth.py** (Clerk authentication utilities)
   - `ClerkAuthenticationError(HTTPException)` - Custom 401 exception
   - `require_clerk_user()` - JWT verification dependency
   - `JWKSCache` - JWKS key caching class
   - `get_jwks()` - Async JWKS fetching with cache
   - `verify_jwt_with_retry()` - JWT verification with key rotation handling

2. **main/api/auth_audit.py** (Authentication-specific audit logging)
   - `AuthenticationAuditLogger(AuditLogger)` - Extends base AuditLogger
   - `log_authentication_success()` - Log successful JWT verification
   - `log_authentication_failure()` - Log authentication errors (GAMP-5 critical)
   - `log_token_refresh()` - Log token refresh events (session continuity)

3. **main/tests/test_api_auth.py** (Authentication test suite)
   - Fixtures: `mock_clerk_token`, `mock_expired_token`, `auth_headers`, `clerk_user`
   - Tests: Valid token (200), missing token (401), expired token (401), invalid signature (401)
   - Tests: Audit logging captures Clerk context
   - Tests: Authorization checks (user can only access own jobs)
   - Mocks: PyJWT `decode()`, audit logger `log_event()`

4. **.env.example** (Environment variable template)
   - Document all required Clerk environment variables
   - Provide example values (placeholder keys)
   - Include comments explaining each variable

**Detailed File Changes:**

**main/api/models.py:**

```python
# ADD NEW MODEL
class ClerkClaims(BaseModel):
    """Clerk JWT payload model - Pydantic v2 compatible"""
    sub: str = Field(..., description="Clerk user ID")
    email: str = Field(..., description="User email address")
    email_verified: bool = Field(default=False)
    iat: int = Field(..., description="Issued at timestamp (Unix epoch)")
    exp: int = Field(..., description="Expiration timestamp (Unix epoch)")
    iss: str = Field(..., description="Issuer (Clerk issuer URL)")
    aud: str | None = Field(default=None, description="Audience")
    azp: str | None = Field(default=None, description="Authorized parties")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sub": "user_2j5k7x9m2n",
                "email": "user@example.com",
                "email_verified": True,
                "iat": 1699000000,
                "exp": 1699003600,
                "iss": "https://your-instance.clerk.accounts.dev"
            }
        }
    )

# UPDATE EXISTING MODEL
class AuditLogEntry(BaseModel):
    """Audit log entry for GAMP-5/ALCOA+ compliance."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    job_id: str
    event_type: str
    user_id: str  # Clerk user ID (sub claim)
    status: JobStatus
    metadata: dict[str, Any] = Field(default_factory=dict)

    # NEW FIELDS for ALCOA+ compliance
    user_email: str | None = Field(default=None, description="User email for attribution")
    token_iat: int | None = Field(default=None, description="Token issued-at timestamp")
    ip_address: str | None = Field(default=None, description="Client IP address")
    session_id: str | None = Field(default=None, description="Session identifier for event linking")
```

**main/api/dependencies.py:**

```python
# ADD IMPORTS
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWTError
import os
from .models import ClerkClaims

# ADD SECURITY INSTANCE
security = HTTPBearer()

# ADD ENVIRONMENT VARIABLES
CLERK_PEM_PUBLIC_KEY = os.getenv("CLERK_PEM_PUBLIC_KEY")
CLERK_ISSUER = os.getenv("CLERK_ISSUER")
CLERK_JWT_AUDIENCE = os.getenv("CLERK_JWT_AUDIENCE")  # Optional

# REPLACE get_current_user()
async def require_clerk_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> ClerkClaims:
    """
    Verify Clerk JWT and return user claims.

    Raises:
        HTTPException: 401 if token invalid (FAIL CLOSED - NO FALLBACK)
    """
    token = credentials.credentials

    try:
        # Verify JWT using Clerk's public key
        payload = jwt.decode(
            token,
            CLERK_PEM_PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=CLERK_ISSUER,
            audience=CLERK_JWT_AUDIENCE if CLERK_JWT_AUDIENCE else None,
            options={
                "verify_exp": True,
                "leeway": 10  # 10 seconds clock skew tolerance
            }
        )

        # Validate required claims
        if "sub" not in payload or "email" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Parse into ClerkClaims model
        return ClerkClaims(**payload)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except (jwt.DecodeError, PyJWTError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        # FAIL CLOSED: Any unexpected error = 401
        logger.exception("Unexpected authentication error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

# UPDATE TYPE ALIAS
CurrentUserDep = Annotated[ClerkClaims, Depends(require_clerk_user)]
```

**main/api/app.py:**

```python
# UPDATE ROUTE
@app.post("/jobs", response_model=JobSubmitResponse, status_code=status.HTTP_201_CREATED)
async def submit_job(
    file: ValidatedFileDep,
    storage: StorageAdapterDep,
    job_queue: JobQueueDep,
    job_repository: JobRepositoryDep,
    job_lock: JobLockDep,
    user: CurrentUserDep  # Changed from user_id: CurrentUserDep (str) to user: CurrentUserDep (ClerkClaims)
) -> JobSubmitResponse:
    """Submit URS file for async processing."""
    try:
        job_id = str(uuid.uuid4())
        logger.info(f"Submitting job {job_id} for user {user.sub}")  # Changed user_id to user.sub

        # ... (file processing code unchanged) ...

        # Create job record with Clerk user context
        job_record = JobRecord(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.now(UTC),
            urs_filename=file.filename or "unknown.txt",
            urs_storage_key=storage_key,
            urs_hash=urs_hash,
            urs_size_bytes=len(urs_content),
            user_id=user.sub,  # Clerk user ID
            user_email=user.email  # NEW: Add email for audit trail
        )

        # ... (repository and queue code unchanged) ...

        # Log to audit trail with Clerk context
        audit_logger = get_audit_logger()
        audit_logger.log_event(
            job_id=job_id,
            event_type="submit",
            user_id=user.sub,  # Changed from user_id to user.sub
            user_email=user.email,  # NEW: Add email
            status=JobStatus.PENDING,
            token_iat=user.iat,  # NEW: Add token issued-at
            metadata={
                "urs_filename": file.filename,
                "urs_size_bytes": len(urs_content),
                "urs_hash": urs_hash,
                "storage_key": storage_key,
                "token_exp": user.exp  # NEW: Add token expiration
            }
        )

        return JobSubmitResponse(...)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Job submission failed: {e}")
        raise HTTPException(...)

# ADD EXCEPTION HANDLER
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled errors.

    CRITICAL: NO FALLBACK LOGIC - All errors logged and reported explicitly
    """
    logger.exception(f"Unhandled exception: {exc}")

    # If authentication error, log to auth audit trail
    if isinstance(exc, HTTPException) and exc.status_code == 401:
        from .auth_audit import get_auth_audit_logger
        auth_audit = get_auth_audit_logger()
        await auth_audit.log_authentication_failure(
            failure_reason=str(exc.detail),
            request=request
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR if not isinstance(exc, HTTPException) else exc.status_code,
        content={
            "detail": f"CRITICAL: {str(exc)}",
            "type": type(exc).__name__
        }
    )
```

---

### Environment Variables Required

Create `.env` file or configure in deployment environment:

```bash
# Clerk Authentication (REQUIRED)
CLERK_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Backend API authentication
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nMIIBIjAN...\n-----END PUBLIC KEY-----"  # JWT verification

# Clerk Configuration (REQUIRED)
CLERK_ISSUER=https://your-instance.clerk.accounts.dev  # JWT issuer validation

# Clerk Configuration (OPTIONAL)
CLERK_JWT_AUDIENCE=https://api.example.com  # JWT audience validation (optional)
CLERK_SERVER_URL=https://eu-api.clerk.com/v1  # EU endpoint for data residency (default: US)

# Existing Environment Variables (from Task 1.3)
ENVIRONMENT=local
USE_S3=false
RAG_MODE=chromadb
```

**Environment Variable Details:**

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `CLERK_SECRET_KEY` | Yes | Backend API authentication key | `sk_test_abc123...` |
| `CLERK_PEM_PUBLIC_KEY` | Yes | PEM-formatted public key for JWT verification | `-----BEGIN PUBLIC KEY-----\n...` |
| `CLERK_ISSUER` | Yes | Clerk issuer URL for JWT validation | `https://your-instance.clerk.accounts.dev` |
| `CLERK_JWT_AUDIENCE` | No | Expected audience claim (optional) | `https://api.example.com` |
| `CLERK_SERVER_URL` | No | Clerk Backend API endpoint (default: US) | `https://eu-api.clerk.com/v1` |

**How to Obtain Values:**

1. **CLERK_SECRET_KEY:**
   - Clerk Dashboard → API Keys → Secret Key
   - Copy the key starting with `sk_test_` (development) or `sk_live_` (production)

2. **CLERK_PEM_PUBLIC_KEY:**
   - Clerk Dashboard → API Keys → Show JWT public key → PEM Public Key
   - Copy entire key including headers/footers: `-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----`
   - Replace literal `\n` with actual newlines when storing in `.env`

3. **CLERK_ISSUER:**
   - Clerk Dashboard → Home → Frontend API URL
   - Use the `.clerk.accounts.dev` URL (development) or your custom domain (production)
   - Example: `https://your-instance.clerk.accounts.dev`

4. **CLERK_JWT_AUDIENCE (optional):**
   - Configure in Clerk Dashboard → JWT Templates → Default → Audience
   - Set to your API base URL (e.g., `https://api.example.com`)
   - Leave blank if not configured in Clerk

5. **CLERK_SERVER_URL (optional):**
   - For EU data residency: `https://eu-api.clerk.com/v1`
   - For US (default): `https://api.clerk.com/v1`
   - Only required if using EU endpoints

---

## Next Agent Guidance

**For task-executor:**

1. **Install Dependencies First:**
   ```bash
   cd C:\Users\anteb\Desktop\Courses\Projects\thesis_project
   uv add clerk-backend-api==4.0.0 pyjwt==2.9.0 cryptography
   uv add --dev pytest-mock freezegun
   ```

2. **Create ClerkClaims Model:**
   - Edit `main/api/models.py`
   - Add `ClerkClaims(BaseModel)` with all JWT claims (`sub`, `email`, `iat`, `exp`, `iss`, `aud`, `azp`)
   - Update `AuditLogEntry` to include `user_email`, `token_iat`, `ip_address`, `session_id`
   - Use Pydantic v2 `Field()` with descriptions

3. **Implement Authentication Dependency:**
   - Edit `main/api/dependencies.py`
   - Add `HTTPBearer` security instance
   - Replace `get_current_user()` with `require_clerk_user()`
   - Use PyJWT `jwt.decode()` with RS256 algorithm
   - Set `leeway=10` for clock skew tolerance
   - Raise HTTPException(401) on ANY verification failure (NO FALLBACK)
   - Update `CurrentUserDep` type alias to `Annotated[ClerkClaims, Depends(require_clerk_user)]`

4. **Update Existing Endpoints:**
   - Edit `main/api/app.py`
   - Change route signatures: `user: CurrentUserDep` (now ClerkClaims, not str)
   - Extract user ID: `user.sub` (instead of `user_id` string)
   - Extract email: `user.email`
   - Update audit log calls to include `user_email=user.email`, `token_iat=user.iat`

5. **Extend Audit Logging:**
   - Edit `main/api/audit.py`
   - Update `log_event()` signature to accept `user_email`, `token_iat`, `ip_address`
   - Add methods: `_enrich_metadata()`, `_generate_session_id()`
   - Maintain existing ALCOA+ compliance structure

6. **Create Authentication Audit Logger:**
   - Create new file: `main/api/auth_audit.py`
   - Extend `AuditLogger` class
   - Add methods: `log_authentication_success()`, `log_authentication_failure()`, `log_token_refresh()`
   - Log authentication failures with ANONYMOUS user context

7. **Implement JWKS Caching:**
   - Create new file: `main/api/auth.py`
   - Add `JWKSCache` class with 15-minute TTL
   - Add `get_jwks()` async function with httpx
   - Handle key rotation gracefully (retry on signature error)

8. **Add Global Exception Handler:**
   - Edit `main/api/app.py`
   - Register exception handler for authentication errors
   - Log all 401 errors to auth audit trail
   - Return generic error messages (no detail leakage)

9. **Create Comprehensive Tests:**
   - Create new file: `main/tests/test_api_auth.py`
   - Fixtures: `mock_clerk_token`, `mock_expired_token`, `auth_headers`
   - Test cases: Valid token (200), missing token (401), expired token (401), invalid signature (401)
   - Mock PyJWT `decode()` and audit logger calls
   - Verify audit logs capture Clerk context

10. **Document Environment Variables:**
    - Create `.env.example` file
    - Document all Clerk environment variables
    - Provide placeholder values with comments

**Critical Implementation Requirements:**

- ✅ **FAIL CLOSED:** All authentication errors MUST return 401, NO FALLBACK LOGIC
- ✅ **NO TOKEN LOGGING:** Never log JWT tokens or sensitive claims
- ✅ **ALCOA+ COMPLIANCE:** Capture user_id, email, IP, token iat/exp in audit logs
- ✅ **EU ENDPOINTS:** Configure for data residency compliance (if required)
- ✅ **CLOCK SKEW:** Set 10-second tolerance for JWT expiration
- ✅ **JWKS CACHING:** Implement 15-minute TTL with key rotation handling
- ✅ **ASYNC COMPATIBLE:** Use async dependencies where appropriate
- ✅ **TYPE SAFETY:** Use Pydantic v2 models with proper Field() definitions
- ✅ **COMPREHENSIVE TESTS:** Cover all authentication scenarios (success, failures, edge cases)

**Integration Checklist:**

- [ ] Dependencies installed (`clerk-backend-api`, `pyjwt`, `cryptography`)
- [ ] ClerkClaims model created in models.py
- [ ] require_clerk_user() dependency implemented in dependencies.py
- [ ] CurrentUserDep type alias updated
- [ ] Existing routes updated to use ClerkClaims
- [ ] Audit logging extended with Clerk context
- [ ] Authentication audit logger created
- [ ] JWKS caching implemented
- [ ] Global exception handler added
- [ ] Tests created and passing
- [ ] Environment variables documented
- [ ] NO FALLBACK LOGIC violations = 0

**Testing Commands:**

```bash
# Run authentication tests
pytest main/tests/test_api_auth.py -v

# Run all API tests
pytest main/tests/test_api_*.py -v

# Type checking
mypy main/api/

# Linting
ruff check main/api/
```

**Expected Test Results:**

- ✅ 15+ tests passing (authentication + existing job tests)
- ✅ Mypy: No type errors
- ✅ Ruff: No linting errors
- ✅ NO FALLBACK LOGIC violations: 0

---

## Files Referenced

### Official Documentation
1. Clerk Backend API Documentation: https://clerk.com/docs/reference/backend-api
2. Clerk Backend SDK GitHub: https://github.com/clerk/clerk-sdk-python
3. Clerk JWT Verification Guide: https://clerk.com/docs/backend-requests/verify-jwts
4. Clerk API Endpoints (EU vs US): https://clerk.com/docs/guides/development/endpoints
5. PyPI - clerk-backend-api: https://pypi.org/project/clerk-backend-api/
6. PyPI - PyJWT: https://pypi.org/project/PyJWT/
7. PyJWT Documentation: https://pyjwt.readthedocs.io
8. FastAPI Security Tutorial: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
9. Pydantic v2 Documentation: https://docs.pydantic.dev/latest/

### Research Sources
10. Perplexity Deep Research: Clerk Python SDK comprehensive integration guide
11. Perplexity Search: EU endpoint configuration and data residency
12. Perplexity Search: PyJWT Python 3.12 compatibility and RS256 verification
13. TestDriven.io: FastAPI JWT Authentication Tutorial (https://testdriven.io/blog/fastapi-jwt-auth/)
14. Lamona Tech Blog: Clerk + FastAPI Integration (https://blog.lamona.tech/how-to-authenticate-api-requests-with-clerk-and-fastapi-6ac5196cace7)

### Existing Codebase Files (Task 1.3)
15. main/api/app.py - FastAPI application with job endpoints
16. main/api/models.py - Pydantic v2 models (JobRecord, AuditLogEntry, JobStatus)
17. main/api/dependencies.py - Dependency injection (get_current_user mock)
18. main/api/audit.py - GAMP-5/ALCOA+ audit logging
19. main/api/worker.py - Background job processor
20. main/tests/test_api_jobs.py - Existing job submission tests

### Standards & Compliance
21. GAMP-5 Guidelines: Good Automated Manufacturing Practice
22. ALCOA+ Principles: Data Integrity in Pharmaceutical Systems
23. 21 CFR Part 11: Electronic Records and Signatures (FDA)
24. GDPR: General Data Protection Regulation (EU data residency)

---

**Research Complete:** All information gathered for Task 1.4 Clerk authentication integration. Ready for task-executor implementation phase.
