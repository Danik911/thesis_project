# AWS Deployment Troubleshooting

Common issues and fixes for pharma-test-gen deployment.

## Issue Matrix

| Symptom | Root Cause | Fix |
|---------|------------|-----|
| Worker S3 403 Forbidden | ChromaDB tarball deleted during destroy | Re-upload: `aws s3 cp chroma_db.tar.gz s3://pharma-test-gen-vectors-staging/` |
| Worker desiredCount=0 | Scaled down during destroy | Scale up: `aws ecs update-service --desired-count 1` |
| `uv: command not found` in WSL | uv not installed in Ubuntu | Use `python3` directly instead of `uv run` |
| Terraform state locked | Previous run crashed | `terraform force-unlock <LOCK_ID>` |
| ECR login failed | Token expired | Re-run ECR login command |
| Docker buildx not found | buildx not installed | `docker buildx create --use` |
| Health check 308 redirect | Frontend routing issue | Check Next.js config, ensure `/` returns 200 |
| Task failed to start | Image pull error | Verify ECR image exists and tag is correct |

---

## Detailed Fixes

### Worker 403 S3 Error

**Error:**
```
RuntimeError: S3 download failed (403): An error occurred (403) when calling the HeadObject operation: Forbidden
```

**Cause:** `destroy.py` empties S3 buckets including ChromaDB data.

**Fix:**
```bash
# 1. Create tarball from local ChromaDB
tar -czvf /tmp/chroma_db.tar.gz -C main chroma_db

# 2. Upload to S3
aws s3 cp /tmp/chroma_db.tar.gz s3://pharma-test-gen-vectors-staging/chroma_db.tar.gz --region eu-west-2

# 3. Force worker redeployment
aws ecs update-service --cluster pharma-test-gen-cluster --service pharma-test-gen-worker --force-new-deployment --region eu-west-2
```

---

### Worker Not Starting After Redeploy

**Symptom:** Worker shows `desired=1, running=0` indefinitely

**Cause:** Service was scaled to 0 during destroy.

**Fix:**
```bash
aws ecs update-service \
  --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-worker \
  --desired-count 1 \
  --force-new-deployment \
  --region eu-west-2
```

---

### LangFuse Credentials Missing Warning

**Warning:**
```
LangFuse credentials missing. Required environment variables:
  - LANGFUSE_PUBLIC_KEY (current: MISSING)
```

**Impact:** Non-blocking. Traces will be local only.

**Fix (optional):** Add to task definition environment:
```json
{
  "name": "LANGFUSE_PUBLIC_KEY",
  "value": "pk_xxx"
},
{
  "name": "LANGFUSE_SECRET_KEY",
  "value": "sk_xxx"
}
```

---

### Terraform State Lock

**Error:**
```
Error: Error acquiring the state lock
```

**Fix:**
```bash
# Get lock ID from error message, then:
terraform force-unlock <LOCK_ID>
```

---

## Health Check URLs

| Service | Endpoint |
|---------|----------|
| API | `http://{API_ALB}/health` |
| Frontend | `http://{FRONTEND_ALB}/` |

---

## Log Locations

| Service | CloudWatch Log Group |
|---------|---------------------|
| API | `/ecs/pharma-test-gen/api` |
| Worker | `/ecs/pharma-test-gen/worker` |
| Frontend | `/ecs/pharma-test-gen/frontend` |
