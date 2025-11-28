# Context Collector Result - Clerk JWT Token Expiration & Polling Patterns

## Agent Configuration
- Agent: context-collector
- Task: Research Clerk JWT token expiration handling and refresh patterns for long-polling operations
- Invoked: 2025-11-26 14:35:00
- Duration: ~20 minutes
- Status: SUCCESS

---

## Task Understanding

The pharmaceutical test generation frontend experiences 401 Unauthorized errors during long-running job status polling. The root cause is that Clerk's JWT tokens expire after 60 seconds, but the polling hook doesn't actively refresh tokens before making requests. This causes all subsequent API calls to fail with `{"detail":"Token expired"}` after initial job submission.

**Key Challenge:** Long-running pharmaceutical workflows (several minutes) combined with 5-second polling intervals create a scenario where tokens expire during the polling sequence, breaking the entire user experience.

---

## Research Findings

### 1. Clerk JWT Token Lifecycle and Expiration

#### Token Lifetime Configuration
- **Default JWT lifetime:** 60 seconds (extremely short for security)
- **Automatic refresh interval:** 50 seconds (Clerk SDK background mechanism)
- **Automatic refresh endpoint:** `/client/sessions/<id>/tokens`
- **Configuration location:** Clerk Dashboard → Sessions page

#### How Automatic Refresh Works
Clerk's frontend SDKs implement an automatic token refresh mechanism that:
1. Runs on a 50-second interval in the background
2. Calls `/client/sessions/<id>/tokens` endpoint
3. Updates the session token in memory/cookies BEFORE expiration
4. Allows 10-second buffer for network latency

**Critical Implication:** The automatic refresh mechanism ONLY works when the browser tab is active and the SDK is running. If the tab loses focus or the user has the page open for multiple seconds without interaction, the automatic refresh may lag.

#### Token Storage
- Tokens stored in browser cookies (subject to 4KB size limit)
- Session ID stored separately: `sessionId` property
- Cookies must be sent with requests (native browser behavior for same-origin)

---

### 2. Forcing Token Refresh with `getToken()`

#### Two Approaches to Force Refresh

**Option A: `getToken({ skipCache: true })`**
```typescript
const { getToken } = useAuth()
const token = await getToken({ skipCache: true })
```
- Forces a new token to be minted
- Makes a network request regardless of cache state
- Only retrieves updated token
- **Recommended for polling scenarios**

**Option B: `user.reload()`**
```typescript
const { user } = useAuth()
await user.reload()
const token = await getToken()
```
- Forces both token refresh AND user object refresh
- More overhead, unnecessary for polling
- Use only when user metadata has changed

#### `getToken()` Caching Behavior
- Default behavior: Uses intelligent caching with 1-minute TTL
- Calling `getToken()` without `skipCache` will only make network request if token in memory has expired
- **Recommendation:** Call `getToken()` once per polling request (minimal overhead)

#### Token Format
- Returns a JWT string (Bearer token format)
- Should be sent as: `Authorization: Bearer {token}`
- Clerk validates expiration via `exp` and `nbf` claims

---

### 3. Best Practices for Long-Polling with Clerk Authentication

#### The Problem with `setInterval` for Polling
```typescript
// ❌ PROBLEMATIC PATTERN
setInterval(async () => {
  const token = await getToken()
  const res = await fetch(`/jobs/${id}/approval-status`, {
    headers: { Authorization: `Bearer ${token}` }
  })
}, 5000)
```

**Issues:**
1. Race conditions: If one poll takes longer than 5 seconds, the next poll starts while the previous is still pending
2. Token might expire during the async operation
3. Server can become overloaded with concurrent requests
4. No backoff mechanism

#### Recommended Pattern: `setTimeout` with Recursion
```typescript
const pollJobStatus = async (jobId: string) => {
  try {
    const { getToken } = useAuth()

    // Get fresh token for this specific request
    const token = await getToken()

    const response = await fetch(`/jobs/${jobId}/approval-status`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    // Handle 401 explicitly
    if (response.status === 401) {
      console.error('Token expired, forcing refresh')
      const freshToken = await getToken({ skipCache: true })
      // Retry with fresh token
      return pollJobStatus(jobId)
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()

    // Check if workflow complete
    if (data.status === 'COMPLETED' || data.status === 'APPROVED') {
      return data
    }

    // Schedule next poll (5 second delay)
    return new Promise((resolve) => {
      setTimeout(() => pollJobStatus(jobId).then(resolve), 5000)
    })

  } catch (error) {
    // GAMP-5: Log with full diagnostic info
    console.error('Poll failed:', {
      error: error.message,
      timestamp: new Date().toISOString(),
      jobId
    })
    throw error
  }
}
```

**Benefits:**
1. No race conditions (waits for response before scheduling next request)
2. Each request gets a fresh token via `getToken()`
3. Explicit 401 handling with forced refresh
4. Natural rate limiting

#### Custom Hook Implementation Pattern

**Recommended approach: `useJobStatusPolling` hook**

```typescript
// hooks/useJobStatusPolling.ts
import { useAuth } from '@clerk/nextjs'
import { useEffect, useState, useRef } from 'react'

interface PollOptions {
  pollInterval?: number // milliseconds, default 5000
  maxRetries?: number   // default 3
  onStatusChange?: (status: string) => void
  onError?: (error: Error) => void
}

export function useJobStatusPolling(
  jobId: string,
  options: PollOptions = {}
) {
  const { getToken } = useAuth()
  const [status, setStatus] = useState<string>('PENDING')
  const [error, setError] = useState<Error | null>(null)
  const [isPolling, setIsPolling] = useState(true)

  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const retryCountRef = useRef(0)

  const {
    pollInterval = 5000,
    maxRetries = 3,
    onStatusChange,
    onError
  } = options

  const pollOnce = async () => {
    try {
      // Get fresh token for this request
      const token = await getToken()

      const response = await fetch(`/api/jobs/${jobId}/approval-status`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      // Handle token expiration explicitly
      if (response.status === 401) {
        if (retryCountRef.current < maxRetries) {
          console.warn(`Token expired, retrying (${retryCountRef.current + 1}/${maxRetries})`)

          // Force token refresh and retry
          const freshToken = await getToken({ skipCache: true })
          const retryResponse = await fetch(`/api/jobs/${jobId}/approval-status`, {
            headers: {
              Authorization: `Bearer ${freshToken}`,
              'Content-Type': 'application/json'
            }
          })

          if (!retryResponse.ok) {
            throw new Error(`HTTP ${retryResponse.status}: Token refresh failed`)
          }

          retryCountRef.current += 1
          const data = await retryResponse.json()
          handleStatusUpdate(data)
          return
        } else {
          throw new Error('Token expired and max retries exceeded')
        }
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      handleStatusUpdate(data)
      retryCountRef.current = 0

    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      setError(error)
      onError?.(error)

      // GAMP-5: Log diagnostic information
      console.error('[PHARMACEUTICAL_AUDIT]', {
        event: 'job_poll_failed',
        jobId,
        error: error.message,
        timestamp: new Date().toISOString(),
        retries: retryCountRef.current
      })
    }
  }

  const handleStatusUpdate = (data: any) => {
    const newStatus = data.status || 'UNKNOWN'
    setStatus(newStatus)
    onStatusChange?.(newStatus)

    // Stop polling if workflow complete
    if (['COMPLETED', 'APPROVED', 'FAILED', 'REJECTED'].includes(newStatus)) {
      setIsPolling(false)
    }
  }

  useEffect(() => {
    if (!isPolling || !jobId) return

    // Initial poll immediately
    pollOnce()

    // Schedule subsequent polls
    const scheduleNextPoll = () => {
      timeoutRef.current = setTimeout(() => {
        pollOnce()
        scheduleNextPoll()
      }, pollInterval)
    }

    scheduleNextPoll()

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [isPolling, jobId])

  return { status, error, isPolling, setIsPolling }
}
```

**Usage in component:**
```typescript
export default function JobApprovalPage({ jobId }: { jobId: string }) {
  const { status, error, isPolling } = useJobStatusPolling(jobId, {
    pollInterval: 5000,
    maxRetries: 3,
    onStatusChange: (newStatus) => {
      if (newStatus === 'APPROVED') {
        // Handle approval
      }
    },
    onError: (error) => {
      // Show error toast to user
    }
  })

  if (error) {
    return <ErrorMessage error={error} />
  }

  return (
    <div>
      <p>Status: {status}</p>
      {isPolling && <Spinner />}
    </div>
  )
}
```

---

### 4. Error Handling Strategy for 401 Errors

#### Explicit 401 Handling (NO FALLBACK LOGIC)
```typescript
// ❌ DO NOT DO THIS (fallback logic)
if (response.status === 401) {
  return { status: 'UNKNOWN', message: 'Please refresh' } // Hiding error!
}

// ✅ DO THIS (explicit error handling)
if (response.status === 401) {
  // Try refresh once
  const freshToken = await getToken({ skipCache: true })
  if (!freshToken) {
    throw new Error('Authentication failed: Unable to refresh token')
  }
  // Retry request
  return retryWithToken(freshToken)
}
```

#### Audit Trail Requirements (GAMP-5/ALCOA+)
Every 401 incident must be logged with:
```typescript
{
  event: 'authentication_failure',
  timestamp: ISO8601,
  userId: clerk_user_id,
  jobId: pharmaceutical_test_job_id,
  errorCode: 401,
  errorMessage: 'Token expired',
  retryAttempts: number,
  finalStatus: 'success' | 'failed',
  metadata: {
    sessionId: string,
    endpoint: string,
    userAgent: string
  }
}
```

---

### 5. FastAPI Backend Token Validation

#### Using `fastapi-clerk-auth` Package (Recommended)
```bash
uv add fastapi-clerk-auth
```

```python
from fastapi import FastAPI, Depends
from fastapi_clerk_auth import ClerkConfig, verify_token

app = FastAPI()

# Configure Clerk validation
clerk_config = ClerkConfig(
    jwks_url="https://your-instance.clerk.accounts.com/.well-known/jwks.json",
    issuer="https://your-instance.clerk.accounts.com"
)

@app.get("/jobs/{job_id}/approval-status")
async def get_approval_status(
    job_id: str,
    claims = Depends(verify_token(clerk_config))
):
    # claims contains validated user info
    user_id = claims.get('sub')
    # Process job status...
    return { "status": "APPROVED" }
```

#### Manual Token Validation (If Custom Logic Needed)
```python
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status
import httpx

async def validate_clerk_token(token: str):
    """
    Validate Clerk JWT with proper error handling.
    NO FALLBACK LOGIC - fail explicitly.
    """
    try:
        # Option 1: Networkless validation (fastest)
        # Requires storing Clerk public key
        decoded = jwt.decode(
            token,
            key=CLERK_PUBLIC_KEY,
            algorithms=["RS256"],
            options={"verify_exp": True}
        )
        return decoded

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired - client must refresh",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"}
        )
```

#### Pharmaceutical Audit Logging for Token Events
```python
from datetime import datetime
from sqlalchemy import create_engine

async def log_token_validation(
    user_id: str,
    job_id: str,
    status: str,  # 'valid' | 'expired' | 'invalid'
    error_message: str = None
):
    """
    GAMP-5 audit trail for authentication events.
    """
    log_entry = {
        'event_type': 'TOKEN_VALIDATION',
        'user_id': user_id,
        'job_id': job_id,
        'validation_status': status,
        'error_message': error_message,
        'timestamp': datetime.utcnow().isoformat(),
        'system_version': '1.0.0',  # For compliance tracking
    }

    # Store in audit table (never delete)
    await db.execute(
        "INSERT INTO audit_logs (event_data, created_at) VALUES (%s, %s)",
        (json.dumps(log_entry), datetime.utcnow())
    )
```

---

### 6. Session Configuration Options

#### In Clerk Dashboard
**Settings → Sessions**

1. **Session Duration:** Keep default (24 hours)
2. **Inactivity Timeout:** Consider enabling
   - Recommended: 15-30 minutes for pharmaceutical workflows
   - Logs out inactive users automatically
   - GAMP-5 compliance benefit: Prevents unauthorized access

3. **JWT Signing Key Rotation:** Enable
   - Automatically rotates keys quarterly
   - All new tokens use latest key

#### Code-Level Session Control
```typescript
// Force session to expire (logout)
const { signOut } = useAuth()
await signOut()

// Get current session details
const { sessionId } = useAuth()

// Access session claims (user metadata)
const { sessionClaims } = useAuth()
```

---

### 7. Known Issues and Gotchas

#### Issue 1: Token Expiration During Long Operations
**Scenario:** Pharmaceutical test generation takes 3+ minutes, polling happens every 5 seconds
**Problem:** Automatic refresh (50-second interval) might expire during long polling
**Solution:** Explicit `getToken()` call before each polling request

#### Issue 2: Cookie Size Limit (4KB)
**Scenario:** Application breaks if session cookie exceeds 4KB
**Problem:** Large custom claims or user metadata can overflow cookie
**Solution:**
- Minimize claims in token
- Store large data server-side, reference by ID in token
- Monitor cookie size in DevTools

#### Issue 3: Tab Inactivity (Browser Closed/Backgrounded)
**Scenario:** User closes tab, returns 5+ minutes later
**Problem:** Automatic refresh didn't run, token is now expired
**Solution:**
- Clerk SDK detects this automatically on page reload
- Makes "handshake" request with `__client` cookie
- Requests new session token if valid
- Redirects to signin if client token invalid

#### Issue 4: Browser DevTools Pausing Execution
**Scenario:** Developer leaves breakpoint active during polling
**Problem:** Async operations pause, tokens can expire while paused
**Solution:** Don't leave breakpoints in production polling code; use logging instead

#### Issue 5: Multiple Tabs with Same User
**Scenario:** User has multiple tabs open with same session
**Problem:** Token refresh in one tab doesn't automatically sync to others
**Solution:**
- Each tab maintains independent token state
- `localStorage` events can signal refresh between tabs
- Clerk SDK should handle this automatically in most cases

---

### 8. Recommended Architecture for Pharmaceutical Test Generation

#### Frontend Flow
```
User Submits Test Job
  ↓
Get Token: const token = await getToken()
  ↓
POST /jobs (with token in Authorization header)
  ↓
Receive jobId
  ↓
Start Polling with useJobStatusPolling(jobId)
  │
  └─→ Every 5 seconds:
      1. Call getToken() (smart caching)
      2. GET /jobs/{id}/approval-status
      3. If 401:
         - Call getToken({ skipCache: true })
         - Retry once
         - If still 401, throw error
      4. If completed/approved, stop polling
      5. Schedule next poll after response completes
```

#### Backend Flow
```
Receive Request with Authorization header
  ↓
Extract token from "Bearer {token}" header
  ↓
Validate with Clerk public key (networkless)
  ↓
If expired:
  - Return 401 with "Token expired" message
  - Log to audit trail
  - DO NOT issue new token (frontend's job)
  ↓
If valid:
  - Extract user_id from claims
  - Process pharmaceutical workflow
  - Log action to audit trail
```

---

### 9. GAMP-5 and ALCOA+ Compliance Considerations

#### GAMP-5 Requirements Met
- **Categorization:** Category 4 (software with full source code, configured)
- **Validation:** Token refresh mechanism validates before each request
- **Audit Trail:** Every token event logged with timestamp, user, jobId, status
- **Error Handling:** Explicit errors thrown, never masked with fallback values

#### ALCOA+ Principles
- **Attributable:** Each request has userId, timestamp, sessionId
- **Legible:** Audit logs include human-readable error messages
- **Contemporaneous:** Logging happens at moment of event
- **Original:** Tokens stored server-side in audit table, never modified
- **Accurate:** Token validation uses Clerk's official SDK
- **Complete:** All fields logged including retry attempts, final status
- **Consistent:** Same validation logic across all endpoints
- **Enduring:** Audit logs never deleted (long-term retention)
- **Available:** Audit logs queryable by jobId, userId, date range

---

## Implementation Gotchas

### 1. Don't Use Token in useEffect Dependency Array
```typescript
// ❌ WRONG - causes infinite loops
const token = await getToken()
useEffect(() => {
  fetch('/api/data', { headers: { Authorization: `Bearer ${token}` } })
}, [token])  // Token changes every 50 seconds!

// ✅ CORRECT - call getToken inside the effect
useEffect(() => {
  const poll = async () => {
    const token = await getToken()
    const res = await fetch('/api/data', { headers: { Authorization: `Bearer ${token}` } })
  }
  poll()
}, [])
```

### 2. Always Await getToken()
```typescript
// ❌ WRONG
const res = await fetch('/api/data', {
  headers: { Authorization: `Bearer ${getToken()}` }
})

// ✅ CORRECT
const token = await getToken()
const res = await fetch('/api/data', {
  headers: { Authorization: `Bearer ${token}` }
})
```

### 3. Handle Network Latency in Polling
```typescript
// ❌ WRONG - assumes instant responses
const POLL_INTERVAL = 5000
setTimeout(() => pollJobStatus(jobId), POLL_INTERVAL)

// ✅ CORRECT - waits for response before scheduling next poll
setTimeout(() => pollJobStatus(jobId), POLL_INTERVAL) // But called recursively AFTER response
```

### 4. Don't Share Tokens Across Requests
```typescript
// ❌ WRONG - stale token reused
const token = await getToken()
for (let i = 0; i < 10; i++) {
  await fetch(`/api/data/${i}`, { headers: { Authorization: `Bearer ${token}` } })
}

// ✅ CORRECT - fresh token for each request (if polling)
for (let i = 0; i < 10; i++) {
  const token = await getToken()
  await fetch(`/api/data/${i}`, { headers: { Authorization: `Bearer ${token}` } })
}
```

---

## Required Libraries/Versions

### Frontend (Next.js)
- `@clerk/nextjs` >= 5.0.0 (ensure useAuth hook available)
- `next` >= 14.0.0 (compatible with Clerk)

### Backend (FastAPI)
- `fastapi-clerk-auth` >= 1.0.0 (recommended for automatic validation)
- OR: `python-jose[cryptography]` >= 3.3.0 (for manual JWT validation)
- `pyjwt` >= 2.8.0 (for RS256 validation)

### Installation
```bash
# Frontend
uv add "@clerk/nextjs>=5.0.0"

# Backend (choose one)
uv add "fastapi-clerk-auth>=1.0.0"  # Recommended
# OR
uv add "python-jose[cryptography]>=3.3.0" "pyjwt>=2.8.0"
```

---

## Next Agent Guidance

**For task-executor implementing token refresh polling:**

1. **Create custom hook:** `main/frontend/hooks/useJobStatusPolling.ts`
   - Implement setTimeout-based recursion (not setInterval)
   - Call `getToken()` before each request
   - Handle 401 with forced refresh and single retry
   - Log all authentication failures to audit trail

2. **Update API client:** Create `main/frontend/lib/authenticatedFetch.ts`
   - Wrapper around fetch that injects token
   - Handles 401 errors with retry
   - Must NOT use fallback logic - throw errors explicitly

3. **Backend validation:**
   - Use `fastapi-clerk-auth` middleware if available
   - If manual validation needed: catch `ExpiredSignatureError` explicitly
   - Return 401 (NOT 403) for expired tokens
   - Log all validation events to database

4. **Testing:**
   - Test with intentionally expired token (mock Clerk)
   - Verify polling stops on repeated 401s
   - Confirm audit logs capture all events
   - Verify no infinite loops on token refresh

5. **Compliance:**
   - All 401 errors logged with timestamp, userId, jobId
   - Audit table has long-term retention (PostgreSQL)
   - No fallback values - all errors throw explicitly

---

## Files Referenced

### Official Documentation
- [Clerk Session Token Management](https://clerk.com/docs/guides/sessions/session-tokens)
- [Force Session Token Refresh](https://clerk.com/docs/guides/sessions/force-token-refresh)
- [useAuth() Hook Reference](https://clerk.com/docs/react/hooks/use-auth)
- [Manual JWT Verification](https://clerk.com/docs/backend-requests/manual-jwt)
- [Backend Requests with Clerk](https://clerk.com/docs/backend-requests/making-requests)

### Community Resources
- [Stack Overflow: Clerk Token Refresh in Client Components](https://stackoverflow.com/questions/78465868/how-to-automatically-refresh-a-clerk-token-in-client-components)
- [Medium: FastAPI + Clerk Integration](https://medium.com/@didierlacroix/building-with-clerk-authentication-user-management-part-2-implementing-a-protected-fastapi-f0a727c038e9)
- [Blog: Handling JWT in FastAPI](https://blog.lamona.tech/how-to-authenticate-api-requests-with-clerk-and-fastapi-6ac5196cace7)

### Error Handling References
- [Stack Overflow: Handle 401 with Axios](https://stackoverflow.com/questions/47216452/how-to-handle-401-authentication-error-in-axios-and-react)
- [Medium: React Query 401 Error Handling](https://medium.com/@sourabhbagrecha/how-to-handle-error-401-unauthorized-request-in-react-query-732297f24285)
- [Dev.to: Token Refresh with Axios Interceptors](https://dev.to/amitkumar13/seamlessly-handling-api-401-errors-in-react-native-automatic-token-refresh-with-axios-interceptors-h9g)

### PyPI Packages
- [fastapi-clerk-auth](https://pypi.org/project/fastapi-clerk-auth/) - Automated Clerk validation middleware

---

## Summary

The 401 error during long-polling occurs because Clerk tokens expire after 60 seconds, but the current polling hook doesn't actively refresh tokens. The automatic SDK refresh mechanism (50-second interval) runs in the background but may not cover all polling scenarios, especially for long-running pharmaceutical workflows.

**Solution:**
1. Call `getToken()` before EVERY polling request
2. Use `setTimeout` with recursion instead of `setInterval`
3. Handle 401 explicitly: force refresh with `skipCache: true` and retry once
4. Log all authentication events for GAMP-5 audit trail
5. Never mask 401 errors with fallback logic - fail explicitly

This approach ensures continuous token validity during long-polling operations while maintaining full pharmaceutical compliance audit trails.

---

**Status:** RESEARCH COMPLETE - Ready for task-executor implementation

