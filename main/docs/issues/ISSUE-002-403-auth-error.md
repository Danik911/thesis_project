# ISSUE-002: 403 Authentication Error on Job Details Page

## Date
2025-12-06

## Symptom
Clicking "View Details" on the History page returned a 403 Forbidden error:
```
GET https://d3ij3pn3g49dzz.cloudfront.net/jobs/{job_id} 403 (Forbidden)
{"detail": "Not authenticated"}
```

The History page loaded jobs correctly, but the Job Details page (`/jobs/[id]`) failed.

## Root Cause
The `jobs/[id].tsx` page used the `authenticatedFetch()` helper with `TokenManager` singleton, while the working `history.tsx` page used a simpler direct `fetch()` pattern.

The `TokenManager` had timing issues with token retrieval:
1. First load of job details page had no cached token
2. TokenManager tried to refresh, but there were timing issues with how `getToken` was bound
3. The `{ skipCache: true }` option might behave differently than direct calls

## Files Modified

### `main/frontend/pages/jobs/[id].tsx`
Replaced `authenticatedFetch()` calls with direct `fetch()` pattern (same as working `history.tsx`):

**Before:**
```typescript
const jobRes = await authenticatedFetch(`${apiUrl}/jobs/${id}`, getToken);
```

**After:**
```typescript
const token = await getToken();
if (!token) {
  throw new Error('Not authenticated');
}

const jobRes = await fetch(`${apiUrl}/jobs/${id}`, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
});
```

Updated all three fetch locations:
1. `fetchJobDetails()` - main job status fetch
2. `handleDownload()` - test suite download
3. Langfuse trace fetch useEffect

## Solution
Use consistent direct fetch pattern across all pages:
1. Call `await getToken()` directly from Clerk's `useAuth()`
2. Include token in fetch headers manually
3. Handle missing token explicitly

## Prevention
- Prefer simple, direct patterns over abstraction layers for authentication
- If using helpers, ensure they're tested in all navigation scenarios
- The `authenticatedFetch` helper is still useful for polling with retry logic, but simpler one-time fetches can use direct pattern

## Related
- `history.tsx` uses direct fetch (works correctly)
- `generate.tsx` uses `authenticatedFetch` for polling (has retry logic for token expiration)
