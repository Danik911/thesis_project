---
description: Quick redeployment of ECS services without Docker builds or Terraform. Use after secrets/config changes or to recover from failed deployments. Takes 2-5 minutes.
argument-hint: [--api|--worker|--frontend|--all] [--status]
---

# Quick Redeploy ECS Services

Fast redeployment without Docker builds or Terraform. Registers task definitions from JSON files and forces new deployments.

**Arguments:** $ARGUMENTS

**Estimated time:** 2-5 minutes

**Production URL:** https://csvgeneration.com/

---

## CRITICAL WARNING

**This command does NOT rebuild Docker images!**

If you made code changes, use `/deploy` instead. The `redeploy.py` script only:
1. Registers task definitions from JSON files
2. Forces ECS to restart with the **same existing image**
3. Invalidates CloudFront cache

Your code changes will NOT appear unless you rebuild and push new Docker images.

See `main/docs/issues/ISSUE-004-redeploy-doesnt-rebuild-images.md` for details.

---

## When to Use This Command

| Scenario | Use `/redeploy` | Use `/deploy` |
|----------|-----------------|---------------|
| Code changes in Python/TypeScript | NO | YES |
| Secrets/config changes only | YES | - |
| Restart after task failures | YES | - |
| Fresh deploy after `/destroy` | NO | YES |
| Test same code with different env vars | YES | - |

---

## Use Cases

- Secrets were lost after Terraform apply
- Task definition configuration changed
- Need quick recovery without full rebuild
- Just want to restart services

## Arguments

| Argument | Description |
|----------|-------------|
| `--api` | Redeploy API service only |
| `--worker` | Redeploy Worker service only |
| `--frontend` | Redeploy Frontend service only |
| `--all` | Redeploy all services (default) |
| `--status` | Check service status only (no redeployment) |
| `--wait` | Wait for services to be healthy after redeployment |

## Execution

### Step 1: Parse Arguments

Arguments provided: `$ARGUMENTS`

Determine mode:
- If `--status` present: Status check only
- If `--api`, `--worker`, or `--frontend`: Specific service
- Otherwise: All services

### Step 2: Check Current Status (if --status)

If `--status` is in arguments, run status check only:

```bash
python aws/scripts/redeploy.py --status-only
```

Then STOP and report status to user.

### Step 3: Run Redeploy Script

Build the redeploy command based on arguments:

```bash
python aws/scripts/redeploy.py $ARGUMENTS --wait
```

The script will:
1. Find latest task definition JSON file for each service
2. Register the task definition with ECS
3. Force new deployment of the service
4. Wait for services to be healthy (with `--wait`)
5. Invalidate CloudFront cache (for frontend)

### Step 4: Verify Task Definition Revision

**IMPORTANT:** ECS can silently run wrong task definition revision (ISSUE-006).

Verify the correct revision is running:

```bash
# Check which revision each service is using
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api pharma-test-gen-frontend pharma-test-gen-worker \
  --query "services[*].{name:serviceName,taskDef:taskDefinition}" \
  --output table \
  --region eu-west-2
```

If the revision number doesn't match the latest, force update to the correct revision:

```bash
# Get latest revision number
aws ecs list-task-definitions --family-prefix pharma-test-gen-api --sort DESC --max-items 1 --region eu-west-2

# Force update to specific revision
aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-api \
  --task-definition pharma-test-gen-api:REVISION_NUMBER \
  --force-new-deployment --region eu-west-2
```

### Step 5: Verify Services Healthy

After script completes, verify services are healthy:

```bash
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api pharma-test-gen-frontend pharma-test-gen-worker \
  --query "services[*].{name:serviceName,status:status,running:runningCount,desired:desiredCount}" \
  --output table \
  --region eu-west-2
```

### Step 6: Verify Endpoints

Test the production endpoints:

```bash
curl -s -o /dev/null -w "%{http_code}" https://csvgeneration.com/health
# Should return 200
```

### Step 7: Report Results

Report to user:
- Which services were redeployed
- Task definition revisions in use
- Current health status
- Any errors encountered

## Task Definition Files

The redeploy script uses these JSON files:

| Service | File Pattern |
|---------|--------------|
| API | `aws/terraform/task-definition-api-v*.json` |
| Worker | `aws/terraform/task-definition-worker-v*.json` |
| Frontend | `aws/terraform/task-definition-frontend-v*.json` |

The script automatically finds the latest version (highest `v*` number).

## Examples

**Check status only:**
```
/redeploy --status
```

**Redeploy API service:**
```
/redeploy --api
```

**Redeploy all services:**
```
/redeploy --all
```
or just:
```
/redeploy
```

**Redeploy frontend and wait:**
```
/redeploy --frontend --wait
```

## Troubleshooting

### Code Changes Not Appearing (ISSUE-004)

**Symptom:** Made code changes, ran redeploy, but old behavior persists.

**Cause:** `redeploy.py` doesn't rebuild Docker images.

**Fix:** Use `/deploy` instead, or manually build and push new images.

### API Returns 500: CLERK_PEM_PUBLIC_KEY Missing (ISSUE-006)

**Symptom:** API returns `{"detail":"CRITICAL: Authentication system not configured"}`

**Cause:** ECS is running wrong task definition revision (missing secrets).

**Fix:**
```bash
# Check which revision is running
aws ecs describe-services --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api \
  --query "services[0].taskDefinition" --region eu-west-2

# Get latest revision with all secrets
aws ecs list-task-definitions --family-prefix pharma-test-gen-api --sort DESC --max-items 1 --region eu-west-2

# Update to correct revision
aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-api \
  --task-definition pharma-test-gen-api:CORRECT_REVISION \
  --force-new-deployment --region eu-west-2
```

### Service Stuck in DRAINING

The old task is stopping but new one hasn't started:
```bash
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api \
  --query 'services[0].events[0:5]' \
  --region eu-west-2
```

### Task Definition Not Found

Ensure the JSON file exists:
```bash
ls aws/terraform/task-definition-api-v*.json
```

### Secrets Missing in Task Definition

Check if secrets are in the task definition JSON:
```bash
cat aws/terraform/task-definition-api-v20.json | grep -A 5 "secrets"
```

Required secrets for API:
- `CLERK_PEM_PUBLIC_KEY`
- `CLERK_ISSUER`
- `OPENROUTER_API_KEY`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `DATABASE_URL`

### API S3 403 Forbidden (ISSUE-005)

**Symptom:** API returns S3 AccessDenied errors.

**Cause:** Task role missing IAM policies after destroy/deploy cycle.

**Fix:** Re-attach IAM policies to `pharma-test-gen-api-task-role`. See `main/docs/issues/ISSUE-005-rebuild-uses-wrong-image-tag.md`.

For more troubleshooting, invoke the `aws-deployment` skill.

## When to Use Full Deploy Instead

Use `/deploy` instead of `/redeploy` when:
- Code changes require new Docker images
- Terraform infrastructure needs updates
- First deployment after `/destroy`
- ECR images are missing
