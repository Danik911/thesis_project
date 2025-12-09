# ISSUE-010: HTML/JSON Export Fails in AWS Deployment

## Status
**RESOLVED** - 2025-12-09

## Symptom
- HTML/JSON export buttons (View, HTML, JSON) work locally in Docker Compose
- Same buttons fail silently in AWS ECS deployment
- Users see export request fail with 404 or 500 error

## Root Cause

The `export_formats.py` endpoint was reading test suite files from local filesystem paths (`Path("output")` or `Path("/app/output")`), but in AWS ECS:

1. The worker service stores test suites in **S3** (not local filesystem)
2. The job's `result_uri` is `s3://bucket/key` (not `file:///path`)
3. ECS containers are ephemeral - no shared local storage between API and worker
4. The API container had no S3 GetObject permission for the output bucket

### Technical Details

**Original code** (`export_formats.py`):
```python
# This fails in AWS - files don't exist locally
output_dir = Path("output")
if not output_dir.exists():
    output_dir = Path("/app/output")
yaml_path = output_dir / job_id / "test_suite.yaml"
```

**Storage Architecture**:
- Local/Docker Compose: `file:///app/output/{job_id}/test_suite.yaml`
- AWS ECS: `s3://pharma-test-gen-output-xxx/test-suites/{job_id}/test_suite.yaml`

## Files Modified

| File | Change |
|------|--------|
| `main/api/export_formats.py` | Complete rewrite to support S3 and file:// URIs, added authentication |
| `aws/terraform/main.tf` | Added S3 GetObject permission to API task role |

## Solution

### 1. Updated `export_formats.py`

- Added proper authentication (was missing - security issue!)
- Added job repository lookup to get `result_uri`
- Added S3 retrieval using `aiobotocore` (already a dependency)
- Kept file:// support for local development
- Added comprehensive error messages

**Key changes**:
```python
async def _get_job_content(job_id, job_repository, job_lock, db_job_repo, user):
    # Get job from repository
    job = await db_job_repo.get_job(job_id)

    # Handle S3 URI
    if result_uri.startswith("s3://"):
        return await _get_content_from_s3(result_uri, job_id)

    # Handle file:// URI (local dev)
    if result_uri.startswith("file://"):
        return _get_content_from_file(result_uri, job_id)
```

### 2. Added IAM Permission

**In `aws/terraform/main.tf`** (API task role):
```hcl
# S3 Output Bucket - Read test suites for export endpoints (HTML/JSON)
{
  Effect = "Allow"
  Action = [
    "s3:GetObject"
  ]
  Resource = "arn:aws:s3:::${var.output_bucket}/*"
}
```

## Deployment Steps

1. Apply Terraform changes:
```bash
cd aws/terraform
terraform apply
```

2. Rebuild and deploy API service:
```bash
# From project root
python aws/scripts/redeploy.py --api
```

## Prevention

- Export endpoints must always use job repository to get storage URI
- Never assume local filesystem access in cloud deployments
- All new endpoints accessing artifacts must handle both `s3://` and `file://` URIs

## Related Issues

- ISSUE-001: CloudFront 404 errors (similar routing issue)

## References

- PRP Task 7.1: Multi-Format Test Suite Export
- `main/src/adapters/s3_adapter.py` - S3 storage adapter pattern
