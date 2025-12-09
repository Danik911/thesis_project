# ISSUE-011: ChromaDB S3 Bucket Name Mismatch

## Status
**RESOLVED** - 2025-12-09

## Symptom
- Worker service fails to start with 403 Forbidden error
- CloudWatch logs show: `S3 download failed (403): An error occurred (403) when calling the HeadObject operation: Forbidden`
- Context Agent (RAG) never executes because worker can't initialize ChromaDB
- Workflow stalls after job submission

## Root Cause

**Configuration mismatch in `aws/terraform/main.tf`:**

The worker task definition had a hardcoded S3 bucket name that didn't match the Terraform-managed bucket:

| Component | Bucket Name | Status |
|-----------|-------------|--------|
| **Worker env var (line 713)** | `pharma-test-gen-vectors-staging` | WRONG - hardcoded |
| **Terraform bucket resource** | `pharma-test-gen-chromadb-{account_id}` | Correct |
| **IAM permissions** | `aws_s3_bucket.chromadb.arn` | Correct |
| **Upload script** | `pharma-test-gen-chromadb-275333454012` | Correct |

The worker had IAM permissions for the Terraform-managed bucket, but was configured to download from a different bucket (`pharma-test-gen-vectors-staging`) that either:
1. Didn't exist, or
2. Had no IAM permissions granted

## Files Modified

| File | Change |
|------|--------|
| `aws/terraform/main.tf` | Line 713: Changed hardcoded bucket name to Terraform resource reference |

## Solution

### Change in `main.tf` (line 713)

**Before:**
```hcl
# ChromaDB RAG Configuration (Task 4.2)
# Using existing bucket pharma-test-gen-vectors-staging (manually created during initial deployment)
{ name = "S3_CHROMADB_BUCKET", value = "pharma-test-gen-vectors-staging" },
```

**After:**
```hcl
# ChromaDB RAG Configuration (Task 4.2)
# Uses Terraform-managed bucket (aws_s3_bucket.chromadb) with IAM permissions
{ name = "S3_CHROMADB_BUCKET", value = aws_s3_bucket.chromadb.id },
```

### Deployment Steps

```bash
# 1. Apply Terraform changes
cd aws/terraform
terraform apply -var-file=environments/staging.tfvars

# 2. Force new worker deployment
aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-worker \
  --force-new-deployment --region eu-west-2

# 3. Verify worker logs show successful ChromaDB initialization
aws logs tail /ecs/pharma-test-gen/worker --since 5m --region eu-west-2 | grep chromadb
```

## Verification

CloudWatch logs after fix:
```
INFO:main.scripts.init_chromadb:Downloading ChromaDB from s3://pharma-test-gen-chromadb-275333454012/chroma_db.tar.gz
INFO:main.scripts.init_chromadb:Downloaded 20.65 MB
INFO:main.scripts.init_chromadb:ChromaDB extracted to /app/chroma_db
INFO:main.scripts.init_chromadb:DEBUG: Found 4 collections in extracted ChromaDB:
INFO:main.scripts.init_chromadb:DEBUG:   - regulatory_documents: 230 documents
INFO:main.scripts.init_chromadb:DEBUG:   - gamp5_documents: 230 documents
INFO:main.scripts.init_chromadb:DEBUG:   - best_practices: 230 documents
INFO:__main__:ChromaDB initialized from S3: /app/chroma_db
```

## Prevention

- **Never hardcode S3 bucket names** in task definitions - always use Terraform resource references
- When a Terraform resource creates a bucket, reference it via `aws_s3_bucket.<name>.id`
- IAM permissions and environment variables must reference the same bucket

## Related Issues

- ISSUE-010: HTML/JSON Export Fails in AWS (similar S3 access issue)
- 2025-12-03-chromadb-empty-collections.md: Previous ChromaDB issues

## References

- `aws/terraform/main.tf` lines 75-109 (ChromaDB bucket resource)
- `aws/terraform/main.tf` lines 319-320 (Worker IAM permissions for ChromaDB)
- `main/scripts/init_chromadb.py` (ChromaDB download and extraction logic)
