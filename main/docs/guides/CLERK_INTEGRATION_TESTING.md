# Clerk Authentication Integration Testing Guide

## Overview

This guide explains how to test Clerk JWT authentication with real credentials. **Status: ✅ VERIFIED WORKING** (Task 1.4 completed 2025-11-11).

## Final Working Configuration

### Environment Setup (.env.local)

```bash
# Clerk Authentication Configuration
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_aGVscGVkLXN0dXJnZW9uLTE5LmNsZXJrLmFjY291bnRzLmRldiQ
CLERK_SECRET_KEY=sk_test_FAVbd05h2Ec19W7GwAzHNJcOaznToLtV8f6RLXtTOF
CLERK_JWKS_URL=https://helped-sturgeon-19.clerk.accounts.dev/.well-known/jwks.json

# Required for JWT verification in FastAPI backend
CLERK_ISSUER=https://helped-sturgeon-19.clerk.accounts.dev
# CLERK_JWT_AUDIENCE is optional - session tokens don't include 'aud' claim
# CLERK_JWT_AUDIENCE=https://helped-sturgeon-19.clerk.accounts.dev
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzRHba6EbVdh7cRyyiTE6
bFCcwig6EmfnQiFHr1h8AjBvhJIfM/tc6YG/Tjg8xv0VgEMN4ZGLAta7wCJDmB/h
Kxj/j7dsNN7cVg2qCoF2bZD3/jRMEzhbdiJm2HaSZwJ6LjFgm9bmsX0WHWWUuRHY
ErNEQesT9A30QVcRGr1GadB3otwXl5dNI408qurjw2CV4c9UroxixM5Yxgt5LIxC
drXAzI7/tktvJbaze31wD0DWCLMpxYu1OFnUEd6rIvEtzSFNU/87kRi5w3drjIyW
FMg+CyGu6ARwIwcETzEOnp1UfmcibXkUTbCztRwcWE58kibZnmJ/3X8MXPgJyBDc
FQIDAQAB
-----END PUBLIC KEY-----"
```

**Critical Configuration Notes:**
1. **CLERK_JWT_AUDIENCE must be commented out** - Clerk session tokens don't include 'aud' claim
2. **Environment variables loaded via python-dotenv** in `main/api/app.py`
3. **Server restart required** after .env.local changes (reload not sufficient for env vars)

## Manual Integration Testing (✅ VERIFIED WORKING)

### Step 1: Start FastAPI Server

```bash
cd C:\Users\anteb\Desktop\Courses\Projects\thesis_project
uv run uvicorn main.api.app:app --reload --port 8000
```

**Important:** Server must be restarted (not just reloaded) after .env.local changes.

### Step 2: Generate Fresh Clerk JWT Token

**⚠️ Token Expiry:** Clerk session tokens expire after 60 seconds. Generate immediately before testing!

```bash
uv run python main/scripts/create_clerk_session.py user_35KgiAcvIC0tdtFvJUN1vDkrNYc
```

Output:
```
Loaded environment variables from .env.local
Creating session for user: user_35KgiAcvIC0tdtFvJUN1vDkrNYc

Session created: sess_XXXXX

JWT Token generated:
eyJhbGciOiJSUzI1NiIs...
```

### Step 3: Test Authentication

**Using Python script (recommended):**
```bash
uv run python main/scripts/test_clerk_auth.py "<JWT_TOKEN>" test_urs.txt
```

Expected Output:
```
Testing authentication with Clerk JWT...
Endpoint: http://localhost:8000/jobs
File: test_urs.txt

Status Code: 201
Response:
{"job_id":"61f608fa-f708-4818-9091-4ddaac3f49f3","status":"pending",...}

SUCCESS! Clerk authentication working!
```

**Using curl (Windows PowerShell):**
```bash
curl -X POST http://localhost:8000/jobs `
  -H "Authorization: Bearer <JWT_TOKEN>" `
  -F "file=@test_urs.txt"
```

### Step 4: Verify Audit Logs

```bash
Get-Content logs\audit\jobs\audit_YYYYMMDD.jsonl | Select-Object -Last 1
```

Expected audit log fields:
- ✅ `user_id`: "user_35KgiAcvIC0tdtFvJUN1vDkrNYc"
- ✅ `token_iat`: 1762867441 (issued-at timestamp)
- ⚠️ `user_email`: null (session tokens don't include email)
- ✅ `alcoa_attributable`: User ID captured
- ✅ `alcoa_contemporaneous`: Timestamp captured

### Frontend Integration (Future - Task 2.x)

1. **Set up Clerk frontend** (Next.js, React, etc.)
2. **Configure** with `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
3. **Sign in** as test user
4. **Extract JWT** from Clerk session: `await session.getToken()`
5. **Call FastAPI** backend with token in Authorization header

## Automated Unit Testing

The unit tests in `test_api_auth.py` use **mock RSA key pairs** to:
- Generate test JWTs with mock private key
- Verify JWTs with mock public key
- Test authentication logic without real Clerk dependency

**Note:** Mock key errors are expected in automated tests. Real Clerk public key is used by the production code, not tests.

## Verification Checklist

### Production Code ✅ VERIFIED (2025-11-11)
- ✅ JWT verification uses real Clerk public key from environment
- ✅ Issuer validation matches Clerk instance URL
- ✅ Audience validation disabled (session tokens don't have 'aud')
- ✅ Clock skew tolerance (10 seconds)
- ✅ Fail-closed error handling (401 on all auth failures)
- ✅ GAMP-5 audit logging with user_id, token_iat
- ✅ Environment variables loaded via python-dotenv
- ✅ Email claim optional (session token compatibility)

### Integration Tests ✅ PASSING (13/13)
- ✅ Job submission with ClerkClaims mock (13/13 tests pass)
- ✅ Audit logging captures Clerk context
- ✅ Authorization enforces user isolation
- ✅ NO FALLBACK LOGIC: 0 violations

### Manual Testing ✅ VERIFIED (2025-11-11)
- ✅ Obtained real Clerk JWT token (create_clerk_session.py)
- ✅ Test FastAPI POST /jobs with real token → Status 201 ✅
- ✅ Test FastAPI POST /jobs without token → Status 401 ✅
- ✅ Test FastAPI POST /jobs with expired token → Status 401 ✅
- ✅ Verified audit logs capture user_id and token_iat
- ⚠️ user_email is null (expected - session tokens don't include email)

## Troubleshooting Guide

This section documents all errors encountered during Task 1.4 integration and their solutions.

### Error 1: ModuleNotFoundError: No module named 'main.api'
**Error Message:**
```
ModuleNotFoundError: No module named 'main.api'; 'main' is not a package
```

**Cause:** Missing `main/__init__.py` file.

**Solution:** Create `main/__init__.py`:
```python
"""Main package for pharmaceutical test generation system."""
__version__ = "0.1.0"
```

### Error 2: CRITICAL: Authentication system not configured (missing CLERK_PEM_PUBLIC_KEY)
**Error Message:**
```
500: CRITICAL: Authentication system not configured (missing CLERK_PEM_PUBLIC_KEY)
```

**Cause:** FastAPI server not loading environment variables from `.env.local`.

**Solution:** Add python-dotenv loading to `main/api/app.py` BEFORE importing dependencies:
```python
from dotenv import load_dotenv
from pathlib import Path

env_file = Path(__file__).parent.parent.parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
```

**Critical:** Must load .env BEFORE importing modules that use environment variables.

### Error 3: Token is missing the "aud" claim
**Error Message:**
```
401: Token validation failed: Token is missing the "aud" claim
```

**Cause:** Clerk session tokens don't include audience ('aud') claim, but JWT verification required it.

**Solution:** Disable audience verification in `main/api/dependencies.py`:
```python
verify_options = {
    "verify_exp": True,
    "verify_iat": True,
    "verify_aud": False,  # Disable for session tokens
    "leeway": 10
}

payload = jwt.decode(
    token,
    CLERK_PEM_PUBLIC_KEY,
    algorithms=["RS256"],
    issuer=CLERK_ISSUER,
    options=verify_options
)
```

Also comment out `CLERK_JWT_AUDIENCE` in `.env.local`.

### Error 4: JWT missing 'email' claim
**Error Message:**
```
WARNING: JWT missing 'email' claim for user user_35KgiAcvIC0tdtFvJUN1vDkrNYc
```

**Cause:** Clerk session tokens may not include email claim (optional field).

**Solution:** Make email optional in `main/api/models.py`:
```python
class ClerkClaims(BaseModel):
    email: str | None = Field(default=None, description="User email (optional in session tokens)")
```

Change strict validation to warning in `require_clerk_user()`.

### Error 5: Token expired
**Error Message:**
```
401: Token expired
```

**Cause:** Clerk session tokens expire after 60 seconds.

**Solution:** Generate fresh token immediately before testing:
```bash
# Generate token
uv run python main/scripts/create_clerk_session.py user_35KgiAcvIC0tdtFvJUN1vDkrNYc

# Test immediately (within 60 seconds)
uv run python main/scripts/test_clerk_auth.py "<TOKEN>" test_urs.txt
```

### Additional Common Issues

#### Issue: "Invalid token signature"
**Solution:** Verify `CLERK_PEM_PUBLIC_KEY` matches Clerk's current public key.
**Regenerate:** Fetch from `https://your-instance.clerk.accounts.dev/.well-known/jwks.json`

#### Issue: "Invalid token issuer"
**Solution:** Ensure `CLERK_ISSUER` matches Clerk instance URL exactly.
**Current:** `https://helped-sturgeon-19.clerk.accounts.dev`

#### Issue: Environment variables not loading
**Solution:** Restart server (not reload) after `.env.local` changes.
```bash
# Stop server (Ctrl+C)
# Start fresh server
uv run uvicorn main.api.app:app --reload --port 8000
```

## Next Steps

For full end-to-end testing:
1. Create Clerk test user via Dashboard
2. Implement frontend authentication (Task 2.x)
3. Test full authentication flow: Frontend sign-in → API request → Backend verification
4. Verify audit logs in `logs/audit/jobs/audit_YYYYMMDD.jsonl`

## Security Notes

- ✅ Never commit `CLERK_SECRET_KEY` to git
- ✅ Use `.env.local` for local development (already in `.gitignore`)
- ✅ Rotate keys if accidentally exposed
- ✅ Use environment-specific keys (test vs production)
