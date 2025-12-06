# Langfuse Trace Dashboard 403 Forbidden Error

**Date**: 2025-12-06
**Status**: RESOLVED
**Environment**: AWS ECS (eu-west-2)
**Deployed Image Tag**: `langfuse-fix-20251206`
**Resolution**: Containers were never deployed with new code due to ECR immutable tags and task definition image tag mismatch.

## Symptom

After deploying the Langfuse trace dashboard feature to AWS, the dashboard shows "Unknown Langfuse error" with 403 (Forbidden) errors in the browser console:

```
GET https://d3ij3pn3g49dzz.cloudfront.net/api/langfuse/trace?traceId=669d62f… 403 (Forbidden)
```

**Key observation**: The feature works locally with Docker Compose but fails on AWS.

---

## Investigation Process

### Phase 1: Initial Code Analysis

Used subagents to investigate frontend auth flow, backend auth config, and CloudFront configuration.

**Findings**:
1. Frontend `LangfuseTraceDashboard.tsx` used plain `fetch()` without Authorization header
2. FastAPI endpoint requires Bearer token via `CurrentUserDep` (Clerk JWT)
3. CORS configuration in `app.py` only had old CloudFront domain `d2yiysdqio0ryi.cloudfront.net`

### Phase 2: Initial Fix Attempt

1. Updated `LangfuseTraceDashboard.tsx` to use `authenticatedFetch` with `useAuth()`:
   ```typescript
   import { useAuth } from '@clerk/nextjs';
   import { authenticatedFetch } from '@/lib/authenticatedFetch';

   // Inside component
   const { getToken } = useAuth();

   // Replaced fetch with:
   const response = await authenticatedFetch(
     `/api/langfuse/trace?traceId=${encodeURIComponent(traceId)}`,
     getToken,
     {},
     controller.signal
   );
   ```

2. Added new CloudFront domain to CORS in `app.py`:
   ```python
   origins = [
       # ... local origins
       "https://d2yiysdqio0ryi.cloudfront.net",
       "https://d3ij3pn3g49dzz.cloudfront.net",  # Current production CloudFront
   ]
   ```

**Result**: Issue persisted after deployment.

### Phase 3: AWS CloudWatch Investigation

Used AWS MCP tools to query CloudWatch logs for the API service.

**Key log entries found**:
```
INFO: Starting ECS API server with LangFuse tracing enabled
INFO: 172.31.40.64:48046 - "GET /api/langfuse/trace?traceId=... HTTP/1.1" 403
```

**Finding**: Requests ARE reaching FastAPI but returning 403.

### Phase 4: Root Cause Discovery

Checked ECS running tasks and discovered **critical issue**:

| Service | Running Image Tag | Expected Tag |
|---------|------------------|--------------|
| API | `staging-20251206105702` (old) | `staging-20251206113618` (new) |
| Frontend | Deployment failed | `staging-20251206113618` |

**Root cause**: Task definition JSON files use DIFFERENT image tags than what was pushed!

| Service | Task Definition Tag | Pushed Tag |
|---------|---------------------|------------|
| API | `:chromadb-settings-fix` | `:staging-20251206113618` |
| Frontend | `:staging-nullish-fix` | `:staging-20251206113618` |

The `redeploy.py` script reads task definitions from JSON files and uses THEIR image tags.

### Phase 5: Additional Issue - Frontend Deployment Failed

The frontend ECS service deployment failed due to ALB health check issues:
- Health check expects HTTP 200
- Next.js returns HTTP 308 (redirect)
- ECS circuit breaker triggered rollback

---

## Root Cause Summary

1. **Image tag mismatch**: New code was pushed with `staging-20251206113618` tag, but task definition files specify different tags (`:chromadb-settings-fix`, `:staging-nullish-fix`)
2. **NEXT_PUBLIC_API_BASE_URL misconfigured**: Was set to `https://d3ij3pn3g49dzz.cloudfront.net` but should be empty string `""` for relative URLs

---

## Solution

Build images with the EXACT tags that task definition files expect:

```bash
# ECR Login
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 275333454012.dkr.ecr.eu-west-2.amazonaws.com

# API - use tag :chromadb-settings-fix (matches task-definition-api-v19.json)
docker buildx build --platform linux/amd64 -f Dockerfile.api.pip \
  -t 275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-api:chromadb-settings-fix \
  --push .

# Frontend - use tag :staging-nullish-fix (matches task-definition-frontend-v13.json)
docker buildx build --platform linux/amd64 -f Dockerfile.frontend \
  --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_aGVscGVkLXN0dXJnZW9uLTE5LmNsZXJrLmFjY291bnRzLmRldiQ \
  --build-arg NEXT_PUBLIC_API_BASE_URL="" \
  -t 275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-frontend:staging-nullish-fix \
  --push .

# Redeploy
python aws/scripts/redeploy.py --api --frontend --wait
```

**CRITICAL**: `NEXT_PUBLIC_API_BASE_URL=""` (empty string) makes frontend use relative URLs, which CloudFront routes correctly.

---

## Files Modified

| File | Change |
|------|--------|
| `main/frontend/components/LangfuseTraceDashboard.tsx` | Use `authenticatedFetch` with `useAuth()` |
| `main/api/app.py` | Added `d3ij3pn3g49dzz.cloudfront.net` to CORS |
| `main/api/langfuse_routes.py` | Created endpoint (previous session) |

---

## Key Learnings

1. **Always verify deployed code**: Check running container image tags match expected versions
2. **Redeploy script uses JSON task definitions**: The image tags in those files must match what you push
3. **CloudFront domain is permanent**: It doesn't change when you destroy/deploy services (only if you destroy CloudFront itself)
4. **Frontend API URL should be empty**: Use relative URLs for CloudFront routing

---

## Related Files

- `aws/terraform/task-definition-api-v19.json` - API task definition
- `aws/terraform/task-definition-frontend-v13.json` - Frontend task definition
- `aws/scripts/redeploy.py` - ECS redeployment script
