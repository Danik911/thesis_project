# ISSUE-006: API Service Running Wrong Task Definition Revision

## Date
2025-12-08

## Symptom
API endpoints return 500 Internal Server Error with the message:
```
{"detail":"CRITICAL: Authentication system not configured (missing CLERK_PEM_PUBLIC_KEY)"}
```

Specifically observed on:
- `POST /jobs` - Job submission fails
- `GET /jobs` - Job listing fails
- Any endpoint requiring authentication

The API container is running and health checks pass (`GET /health` returns 200), but authentication fails.

---

## Root Cause

The ECS service was running **task definition revision 32** instead of **revision 33**.

| Revision | Secrets |
|----------|---------|
| **32** (wrong) | Only `DATABASE_URL` |
| **33** (correct) | `DATABASE_URL`, `CLERK_PEM_PUBLIC_KEY`, `CLERK_ISSUER`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` |

**Why This Happens:**
1. New task definition registered with all secrets (creates revision 33)
2. Service update command doesn't specify revision explicitly
3. Service continues using previous revision (32)
4. Circuit breaker may roll back to older revision after health check failures

---

## Diagnosis

### Step 1: Check which revision the service is using

```bash
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api \
  --query "services[0].taskDefinition" \
  --region eu-west-2

# Output: "arn:aws:ecs:eu-west-2:275333454012:task-definition/pharma-test-gen-api:32"
# ↑ Wrong! Should be revision 33
```

### Step 2: Compare secrets between revisions

```bash
# Check revision 32 secrets
aws ecs describe-task-definition \
  --task-definition pharma-test-gen-api:32 \
  --query "taskDefinition.containerDefinitions[0].secrets" \
  --region eu-west-2

# Output: [{"name": "DATABASE_URL", ...}]  ← Missing Clerk secrets!

# Check revision 33 secrets
aws ecs describe-task-definition \
  --task-definition pharma-test-gen-api:33 \
  --query "taskDefinition.containerDefinitions[0].secrets" \
  --region eu-west-2

# Output: [{"name": "DATABASE_URL", ...}, {"name": "CLERK_PEM_PUBLIC_KEY", ...}, ...]
```

### Step 3: Check CloudWatch logs for confirmation

```bash
aws logs filter-log-events \
  --log-group-name /ecs/pharma-test-gen/api \
  --filter-pattern "CLERK_PEM_PUBLIC_KEY" \
  --limit 10 \
  --region eu-west-2
```

If you see "CLERK_PEM_PUBLIC_KEY not configured" errors, the wrong revision is running.

---

## Fix

Explicitly specify the correct task definition revision:

```bash
aws ecs update-service \
  --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-api \
  --task-definition pharma-test-gen-api:33 \
  --force-new-deployment \
  --region eu-west-2
```

Then wait for deployment to complete:

```bash
# Check deployment status
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api \
  --query "services[0].{taskDef:taskDefinition,running:runningCount,deployments:deployments[*].{status:status,revision:taskDefinition,rolloutState:rolloutState}}" \
  --region eu-west-2
```

Expected output after fix:
```json
{
  "taskDef": "arn:aws:ecs:eu-west-2:275333454012:task-definition/pharma-test-gen-api:33",
  "running": 1,
  "deployments": [{
    "status": "PRIMARY",
    "revision": "...:33",
    "rolloutState": "COMPLETED"
  }]
}
```

---

## Verify Fix

Check CloudWatch logs for successful LangFuse initialization (indicates all secrets loaded):

```bash
aws logs filter-log-events \
  --log-group-name /ecs/pharma-test-gen/api \
  --log-stream-name-prefix api/api/ \
  --filter-pattern "LangFuse initialized successfully" \
  --limit 5 \
  --region eu-west-2
```

Test the endpoint:
```bash
curl -s -o /dev/null -w "%{http_code}" https://d861au413p5o2.cloudfront.net/health
# Should return 200
```

---

## Prevention

1. **Always specify revision explicitly** when updating services:
   ```bash
   aws ecs update-service --task-definition pharma-test-gen-api:LATEST_REVISION ...
   ```

2. **Check the latest revision** before updating:
   ```bash
   aws ecs describe-task-definition \
     --task-definition pharma-test-gen-api \
     --query "taskDefinition.revision"
   ```

3. **Verify secrets** in new task definitions before deployment:
   ```bash
   aws ecs describe-task-definition \
     --task-definition pharma-test-gen-api:NEW_REVISION \
     --query "taskDefinition.containerDefinitions[0].secrets[*].name"
   ```

4. **Monitor deployment rolloutState** - if it shows `COMPLETED` but with wrong revision, the circuit breaker may have rolled back.

---

## Related Issues

- **ISSUE-005**: Task definition has hardcoded old image tag (similar pattern - wrong task def config)
- **ISSUE-007 in DEPLOY_DESTROY_FIXES.md**: API Task Definition Missing Secrets After Redeploy (root cause of missing secrets)

---

## Quick Reference

```bash
# What revision is running?
aws ecs describe-services --cluster pharma-test-gen-cluster --services pharma-test-gen-api --query "services[0].taskDefinition" --region eu-west-2

# What's the latest revision?
aws ecs list-task-definitions --family-prefix pharma-test-gen-api --sort DESC --max-items 1 --region eu-west-2

# Update to specific revision
aws ecs update-service --cluster pharma-test-gen-cluster --service pharma-test-gen-api --task-definition pharma-test-gen-api:33 --force-new-deployment --region eu-west-2

# Check deployment progress
aws ecs describe-services --cluster pharma-test-gen-cluster --services pharma-test-gen-api --query "services[0].deployments" --region eu-west-2
```
