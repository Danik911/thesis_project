# Context Collector Result - 2025-12-06 14:15:00

## Agent Configuration
- Agent: context-collector
- Task ID: Clerk Auth CloudFront 403 Issue
- Invoked: 2025-12-06 14:15:00
- Duration: 35 minutes
- Status: SUCCESS

## Task Understanding
Diagnose and resolve 403 Forbidden error when calling `/api/langfuse/trace` from Next.js frontend on AWS CloudFront deployment. The same call works locally via Docker Compose but fails in production due to authentication flow differences between Next.js API routes (cookie-based) and FastAPI backend (token-based).

## Research Findings

### Root Cause Analysis

#### Architecture Mismatch
**Local (Docker Compose):**
- Frontend calls `/api/langfuse/trace`
- Next.js dev server routes to `pages/api/langfuse/trace.ts`
- Next.js API route uses `getAuth(req)` which reads session cookies
- Cookies sent automatically by browser (same-origin request)
- Authentication successful

**AWS (CloudFront + ECS):**
- Frontend calls `/api/langfuse/trace`
- CloudFront routes `/api/*` to API ALB → FastAPI (line 100-111 in `aws/terraform/modules/cloudfront/main.tf`)
- FastAPI route expects `CurrentUserDep` (JWT Bearer token in Authorization header)
- Frontend sends NO Authorization header
- FastAPI returns 403 Forbidden

#### Dual Route Implementation
The project has BOTH implementations:
1. **Next.js:** `main/frontend/pages/api/langfuse/trace.ts` (cookie-based auth)
2. **FastAPI:** `main/api/langfuse_routes.py` line 156 (JWT Bearer token auth)

This is intentional but CloudFront routing bypasses Next.js routes entirely.

### Clerk Authentication Patterns

#### Cookie-Based Auth (Next.js API Routes)
From Clerk documentation:
```typescript
// Works in Next.js API routes (same-origin)
import { getAuth } from '@clerk/nextjs/server';

export default async function handler(req, res) {
  const { userId } = getAuth(req);  // Reads session cookie
  if (!userId) return res.status(401).json({ error: 'Unauthorized' });
  // ...
}
```

Source: [Clerk Next.js auth() reference](https://clerk.com/docs/references/nextjs/auth)

#### Token-Based Auth (External APIs)
From Clerk documentation:
```typescript
// Required for cross-origin/external API calls
import { useAuth } from '@clerk/nextjs';

const { getToken } = useAuth();
const token = await getToken();

const response = await fetch('/api/endpoint', {
  headers: {
    Authorization: `Bearer ${token}`
  }
});
```

Source: [Clerk Backend Requests Documentation](https://clerk.com/docs/backend-requests/making-requests)

#### Key Insight from Clerk Docs
"In order to pass the session token using the browser Fetch API, it should be put inside a Bearer token in the Authorization header. To retrieve the session token, use the `getToken` method from the `useAuth()` hook. Be mindful that `getToken` is an async function that returns a Promise which needs to be resolved."

Source: [Clerk Cross-origin Requests](https://clerk.com/docs/backend-requests/making/cross-origin)

### Existing Infrastructure (Already Implemented!)

#### authenticatedFetch Utility
The project already has `main/frontend/lib/authenticatedFetch.ts` with:
- Token management via TokenManager singleton
- Coordinated 401 retry logic (prevents "retry storms")
- Exponential backoff (2s, 4s, 8s, 16s, 32s)
- Max 5 retries for long-running workflows
- NO FALLBACK LOGIC (complies with CLAUDE.md requirements)

```typescript
// From main/frontend/lib/authenticatedFetch.ts (lines 36-79)
export async function authenticatedFetch(
    url: string,
    getToken: ClerkGetToken,
    options: RequestInit = {},
    signal?: AbortSignal,
    retryCount: number = 0
): Promise<Response> {
    tokenManager.setGetTokenFn(getToken);
    const shouldForceRefresh = retryCount > 0;
    const token = await tokenManager.getToken(shouldForceRefresh);

    if (!token) {
        throw new Error('Authentication token not available. Please sign in again.');
    }

    const fetchOptions: RequestInit = {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${token}`,
        },
        ...(signal ? { signal } : {}),
    };

    const response = await fetch(url, fetchOptions);

    if (response.status === 401 && retryCount < MAX_RETRIES) {
        const delay = Math.pow(2, retryCount + 1) * 1000;
        console.warn(`[API] JWT expired (401), coordinated refresh, retry ${retryCount + 1}/${MAX_RETRIES} in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
        return authenticatedFetch(url, getToken, options, signal, retryCount + 1);
    }

    return response;
}
```

### Recommended Approach

#### Solution: Use Existing authenticatedFetch Utility

**File to Modify:** `main/frontend/components/LangfuseTraceDashboard.tsx`

**Current Code (Line 414):**
```typescript
const response = await fetch(`/api/langfuse/trace?traceId=${encodeURIComponent(traceId)}`, {
  signal: controller.signal,
});
```

**Fixed Code:**
```typescript
import { useAuth } from '@clerk/nextjs';
import { authenticatedFetch } from '@/lib/authenticatedFetch';

export default function LangfuseTraceDashboard({ traceId, traceUrl, jobId }) {
  const { getToken } = useAuth();  // Add this hook

  // Inside useEffect:
  const response = await authenticatedFetch(
    `/api/langfuse/trace?traceId=${encodeURIComponent(traceId)}`,
    getToken,
    { signal: controller.signal }
  );
}
```

**Why This Works:**
1. `useAuth()` provides `getToken` function (client-side)
2. `authenticatedFetch` calls `getToken()` to retrieve JWT
3. JWT added to `Authorization: Bearer {token}` header
4. FastAPI's `CurrentUserDep` validates JWT (lines 286-403 in `main/api/dependencies.py`)
5. Request succeeds on AWS (CloudFront → API ALB → FastAPI)
6. Also works locally (FastAPI validates same JWT)

#### No CloudFront Changes Required
CloudFront routing is correct:
- `/api/*` → API ALB → FastAPI ✅
- `/` → Frontend ALB → Next.js ✅

Next.js API routes can remain for server-side rendering if needed, but frontend should call FastAPI directly.

### Implementation Gotchas

#### 1. Client Component Requirement
`useAuth()` is a React hook - component MUST have `'use client'` directive.

**Check:** `LangfuseTraceDashboard.tsx` is already a client component (uses `useState`, `useEffect`).

#### 2. Token Expiration
Clerk JWTs expire after 60 seconds by default.

**Handled:** `authenticatedFetch` already implements retry logic with token refresh.

#### 3. CORS Headers
CloudFront may require CORS configuration for Authorization headers.

**Current Status:** Check CloudFront cache behavior for `/api/*` paths - currently uses `AllViewer` origin request policy (line 96 in `aws/terraform/modules/cloudfront/main.tf`).

**Verification Needed:** Confirm `Authorization` header is forwarded to origin.

From Terraform config:
```hcl
# Line 95-96: cloudfront/main.tf
cache_policy_id          = local.cache_disabled_policy_id
origin_request_policy_id = local.all_viewer_policy_id  # AllViewer policy
```

The `AllViewer` policy forwards all headers including `Authorization` ✅

#### 4. Component Prop Changes
`LangfuseTraceDashboard` currently doesn't accept `getToken` as prop - needs to import `useAuth()` directly.

**Implementation:** Add `useAuth()` hook inside component (preferred pattern from Clerk docs).

### Required Libraries/Versions

No new dependencies required - all utilities already implemented:
- `@clerk/nextjs` (already installed)
- `main/frontend/lib/authenticatedFetch.ts` (already exists)
- `main/frontend/lib/tokenManager.ts` (already exists)

### Pharmaceutical Compliance (GAMP-5)

#### ALCOA+ Principles
- **Attributable:** JWT contains user ID (`sub` claim) - logged by FastAPI
- **Legible:** Clerk JWTs are standard JSON Web Tokens
- **Contemporaneous:** Short-lived tokens (60s) ensure fresh authentication
- **Original:** Token issued by Clerk (trusted source)
- **Accurate:** JWT signature verified by FastAPI using Clerk public key

#### Audit Trail Requirements
From `main/api/dependencies.py` (lines 286-403):
- All auth failures logged explicitly (NO FALLBACK LOGIC)
- Token expiration logged: `logger.info("JWT expired")`
- Invalid signatures logged: `logger.warning("Invalid JWT signature")`
- Missing claims logged: `logger.warning("JWT missing 'sub' claim")`

**Compliance Status:** ✅ PASS

### Alternative Approaches (Not Recommended)

#### Option B: Change CloudFront Routing
Modify `aws/terraform/modules/cloudfront/main.tf` to route `/api/langfuse/*` to Frontend ALB.

**Pros:** No frontend code changes
**Cons:**
- Inconsistent routing pattern
- Harder to maintain
- Breaks RESTful API design
- Next.js API routes duplicate FastAPI logic

#### Option C: Accept Both Cookie and Token Auth
Modify FastAPI `CurrentUserDep` to accept either cookies OR Bearer tokens.

**Pros:** Works in both environments
**Cons:**
- Violates security best practices
- Cookies not sent cross-origin by default
- FastAPI doesn't natively handle Clerk cookies
- More complex authentication logic

#### Option D: Use Next.js API Route as Proxy
Keep calling Next.js route, which proxies to FastAPI with token.

**Pros:** Minimal frontend changes
**Cons:**
- Extra network hop (latency)
- Unnecessary complexity
- Doubles logging/monitoring overhead

### CloudFront Configuration Review

From `aws/terraform/modules/cloudfront/main.tf`:

**API Path Routing (Lines 100-111):**
```hcl
ordered_cache_behavior {
  path_pattern           = "/api/*"
  target_origin_id       = "api-alb"
  viewer_protocol_policy = "redirect-to-https"
  compress               = true

  allowed_methods = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
  cached_methods  = ["GET", "HEAD"]

  cache_policy_id          = local.cache_disabled_policy_id  # No caching
  origin_request_policy_id = local.all_viewer_policy_id      # Forward all headers
}
```

**Key Settings:**
- ✅ HTTPS enforced
- ✅ Caching disabled for API routes
- ✅ All viewer headers forwarded (includes Authorization)
- ✅ All HTTP methods allowed

**No CloudFront changes needed.**

## Next Agent Guidance

### For task-executor:

1. **Modify Component:**
   - File: `main/frontend/components/LangfuseTraceDashboard.tsx`
   - Add: `import { useAuth } from '@clerk/nextjs'`
   - Add: `import { authenticatedFetch } from '@/lib/authenticatedFetch'`
   - Add: `const { getToken } = useAuth()` inside component
   - Replace: `fetch(...)` with `authenticatedFetch(..., getToken, ...)`
   - Line: 414 (inside useEffect)

2. **Test Cases:**
   - Local: Verify still works with Docker Compose
   - AWS: Verify 403 error resolved
   - Token Expiry: Verify retry logic works (wait 60s)
   - Error Handling: Verify explicit auth errors (no fallback)

3. **Verification:**
   - Check CloudWatch logs for successful JWT validation
   - Confirm LangFuse dashboard renders on AWS
   - Verify no CORS errors in browser console

4. **Rollback Plan:**
   - If fails, revert component changes
   - Check CloudFront logs for header forwarding
   - Verify Clerk public key configured in API environment

### For debugger (if task-executor fails):

**Potential Issues:**
1. `useAuth()` returns null - user not authenticated
2. `getToken()` returns null - session expired
3. FastAPI rejects token - clock skew or wrong public key
4. CloudFront strips Authorization header - verify origin request policy

**Debug Commands:**
```bash
# Check CloudFront distribution settings
aws cloudfront get-distribution --id E3CO1HBNMIUKPB

# Check API container logs
aws logs tail /aws/ecs/pharma-test-gen-api --follow

# Check Clerk environment variables
aws ecs describe-task-definition --task-definition pharma-test-gen-api:latest | grep -A5 CLERK
```

## Files Referenced

### Project Files
- `main/frontend/components/LangfuseTraceDashboard.tsx` - Component to modify
- `main/frontend/lib/authenticatedFetch.ts` - Existing auth utility
- `main/frontend/lib/tokenManager.ts` - Token coordination logic
- `main/api/dependencies.py` - FastAPI JWT validation
- `main/api/langfuse_routes.py` - FastAPI trace endpoint
- `main/frontend/pages/api/langfuse/trace.ts` - Next.js API route (deprecated for AWS)
- `main/frontend/middleware.ts` - Clerk middleware config
- `aws/terraform/modules/cloudfront/main.tf` - CloudFront routing
- `.claude/state/prp-workflow-state.md` - Current workflow state
- `CLAUDE.md` - Project compliance requirements

### Documentation Sources
- [Clerk Next.js auth() reference](https://clerk.com/docs/references/nextjs/auth)
- [Clerk Backend Requests: Making requests](https://clerk.com/docs/backend-requests/making-requests)
- [Clerk Backend Requests: Cross-origin](https://clerk.com/docs/backend-requests/making/cross-origin)
- [Clerk Session Tokens](https://clerk.com/docs/guides/sessions/session-tokens)
- [Clerk clerkMiddleware() reference](https://clerk.com/docs/reference/nextjs/clerk-middleware)
- [Clerk useAuth() hook](https://clerk.com/docs/expo/reference/hooks/use-auth)
- [Next.js Authentication Guide](https://nextjs.org/docs/pages/guides/authentication)

### Context7 Library References
- `/clerk/clerk-nextjs-app-quickstart` - Client-side auth hooks example
- `/vercel/next.js` - Next.js framework documentation

## Summary

**Problem:** Frontend calls `/api/langfuse/trace` without Authorization header, causing 403 on AWS where CloudFront routes to FastAPI (requires JWT).

**Solution:** Use existing `authenticatedFetch` utility with `useAuth()` hook to add Bearer token to requests.

**Impact:**
- ✅ Minimal code change (1 component, ~5 lines)
- ✅ No infrastructure changes
- ✅ No new dependencies
- ✅ GAMP-5 compliant (explicit auth, audit trail)
- ✅ Works in both local and AWS environments

**Confidence Level:** HIGH - All utilities already implemented, pattern matches Clerk official docs, CloudFront configuration verified correct.
