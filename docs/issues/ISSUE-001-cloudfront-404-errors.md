# ISSUE-001: CloudFront 404 Errors After Deployment

## Date
2025-12-06

## Symptom
After redeploying the frontend service, users encountered 404 errors on navigation:
```
GET https://d3ij3pn3g49dzz.cloudfront.net/_next/data/qLbmFD8psrVrfidTPm_Bb/history.json 404 (Not Found)
GET https://d3ij3pn3g49dzz.cloudfront.net/_next/data/qLbmFD8psrVrfidTPm_Bb/generate.json 404 (Not Found)
```

## Root Cause
CloudFront cached HTML pages containing old Next.js build IDs. After deployment:
1. New container has build ID `XYZ789`
2. CloudFront still serves cached HTML with old build ID `ABC123`
3. Browser requests `/_next/data/ABC123/history.json`
4. New server only has `/_next/data/XYZ789/` → 404

Next.js embeds unique build IDs into HTML pages that reference specific JavaScript chunks. When CloudFront caches these HTML pages, the cached build ID no longer matches the deployed server.

## Files Modified

### 1. `aws/terraform/modules/cloudfront/main.tf`
Changed `default_cache_behavior.cache_policy_id` from `CachingOptimized` to `CachingDisabled`:

```hcl
default_cache_behavior {
  # Disable caching for HTML pages to prevent 404 errors after deployment.
  # Next.js embeds build IDs in HTML that reference specific JS chunks.
  cache_policy_id = local.cache_disabled_policy_id  # Was: cache_optimized_policy_id
}
```

### 2. `aws/scripts/redeploy.py`
Added automatic CloudFront cache invalidation function (Phase 5):

```python
def invalidate_cloudfront_cache(distribution_id: str = CLOUDFRONT_DISTRIBUTION_ID) -> bool:
    """Invalidate CloudFront cache after deployment."""
    cmd = [
        "aws", "cloudfront", "create-invalidation",
        "--distribution-id", distribution_id,
        "--paths", "/*",
        "--region", "us-east-1",  # CloudFront is global
    ]
    # ...
```

## Solution
1. **Immediate fix**: Invalidate CloudFront cache manually
   ```bash
   aws cloudfront create-invalidation --distribution-id E393L8ZUFJ4ND8 --paths "/*"
   ```

2. **Permanent fix**:
   - Changed Terraform to disable HTML caching
   - Added automatic cache invalidation to `redeploy.py`

## Prevention
- Always use `redeploy.py` for frontend deployments (auto-invalidates cache)
- Consider using immutable asset patterns for static files

## Related
- GAMP-5 compliance: Users must always see latest validated content
- CloudFront distribution: `E393L8ZUFJ4ND8` (d3ij3pn3g49dzz.cloudfront.net)
