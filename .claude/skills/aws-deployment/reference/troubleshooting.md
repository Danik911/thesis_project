# AWS Deployment Troubleshooting

Common issues and fixes for pharma-test-gen deployment.

**Production URL:** https://csvgeneration.com/

## Issue Matrix

| Symptom | Root Cause | Fix | Issue Reference |
|---------|------------|-----|-----------------|
| Code changes don't appear after redeploy | `redeploy.py` doesn't rebuild images | Use `/deploy` for code changes | ISSUE-004 |
| API 500: CLERK_PEM_PUBLIC_KEY missing | Wrong task definition revision | Verify and update to correct revision | ISSUE-006 |
| API S3 403 Forbidden | Task role missing IAM policies | Re-attach policies to task role | ISSUE-005 |
| CloudFront 404 on navigation | Cached old Next.js build IDs | Run cache invalidation (auto in redeploy.py) | ISSUE-001 |
| ALB health check failing with 308 | Missing trailing slash | Update health check path to `/api/health/` | ISSUE-005 |
| Worker S3 403 Forbidden | ChromaDB tarball deleted during destroy | Re-upload: `aws s3 cp chroma_db.tar.gz s3://pharma-test-gen-vectors-staging/` | - |
| Worker desiredCount=0 | Scaled down during destroy | Scale up: `aws ecs update-service --desired-count 1` | - |
| `uv: command not found` in WSL | uv not installed in Ubuntu | Use `python3` directly instead of `uv run` | - |
| Terraform state locked | Previous run crashed | `terraform force-unlock <LOCK_ID>` | - |
| ECR login failed | Token expired | Re-run ECR login command | - |
| Docker buildx not found | buildx not installed | `docker buildx create --use` | - |
| Task failed to start | Image pull error | Verify ECR image exists and tag is correct | - |

---

## Detailed Fixes

### Code Changes Not Appearing (ISSUE-004)

**Error:** Made code changes, ran `/redeploy`, but old behavior persists.

**Cause:** `redeploy.py` doesn't rebuild Docker images. It only:
1. Registers task definitions from JSON files
2. Forces ECS to restart with the **same existing image**
3. Invalidates CloudFront cache

**Fix:** Use `/deploy` for code changes, or manually build and push:
```bash
# ECR login
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 275333454012.dkr.ecr.eu-west-2.amazonaws.com

# Build and push (example for frontend)
docker buildx build --platform linux/amd64 -f Dockerfile.frontend \
  --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY='pk_test_xxx' \
  -t 275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-frontend:staging-latest \
  --push .

# Then redeploy
python aws/scripts/redeploy.py --frontend
```

See `main/docs/issues/ISSUE-004-redeploy-doesnt-rebuild-images.md` for details.

---

### API 500: Missing Secrets (ISSUE-006)

**Error:**
```json
{"detail":"CRITICAL: Authentication system not configured (missing CLERK_PEM_PUBLIC_KEY)"}
```

**Cause:** ECS is running wrong task definition revision (missing secrets).

**Diagnosis:**
```bash
# Check which revision is running
aws ecs describe-services --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api \
  --query "services[0].taskDefinition" --region eu-west-2

# Check secrets in that revision
aws ecs describe-task-definition --task-definition pharma-test-gen-api \
  --query "taskDefinition.containerDefinitions[0].secrets[*].name" --region eu-west-2
```

**Fix:**
```bash
# Get latest revision with all secrets
aws ecs list-task-definitions --family-prefix pharma-test-gen-api --sort DESC --max-items 1 --region eu-west-2

# Update to correct revision (replace XX with actual revision number)
aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-api \
  --task-definition pharma-test-gen-api:XX \
  --force-new-deployment --region eu-west-2
```

See `main/docs/issues/ISSUE-006-api-task-definition-revision.md` for details.

---

### API S3 403 Forbidden (ISSUE-005)

**Error:**
```
RuntimeError: S3 download failed (403): An error occurred (403) when calling the HeadObject operation: Forbidden
```

**Cause:** Task role `pharma-test-gen-api-task-role` has no IAM policies attached (lost during Terraform destroy/apply).

**Diagnosis:**
```bash
aws iam list-attached-role-policies --role-name pharma-test-gen-api-task-role
# {\"AttachedPolicies\": []}

aws iam list-role-policies --role-name pharma-test-gen-api-task-role
# {\"PolicyNames\": []}
```

**Fix:** Re-attach IAM policies. See `main/docs/issues/ISSUE-005-rebuild-uses-wrong-image-tag.md` for the policy JSON.

---

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
| Production (Route 53) | `https://csvgeneration.com/` |
| API Health | `https://csvgeneration.com/health` |
| Frontend | `https://csvgeneration.com/generate` |

### Internal ALB URLs (for debugging)
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

### View logs for specific issues
```bash
# Check for CLERK_PEM_PUBLIC_KEY errors
aws logs filter-log-events \
  --log-group-name /ecs/pharma-test-gen/api \
  --filter-pattern "CLERK_PEM_PUBLIC_KEY" \
  --limit 10 \
  --region eu-west-2

# Check for S3 403 errors
aws logs filter-log-events \
  --log-group-name /ecs/pharma-test-gen/api \
  --filter-pattern "403" \
  --limit 10 \
  --region eu-west-2
```
