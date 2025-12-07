# ISSUE-004: redeploy.py Doesn't Rebuild Docker Images

## Date
2025-12-07

## Symptom
After making code changes to frontend files and running `redeploy.py --frontend`:
- ECS service restarts successfully
- CloudFront cache is invalidated
- **BUT code changes are NOT visible in the deployed application**
- Debug logs added to code don't appear in browser console
- The same old behavior persists

## Root Cause
`redeploy.py` does **NOT** rebuild Docker images. It only:
1. Registers the task definition from JSON file
2. Forces ECS to redeploy existing tasks with the **same image**
3. Invalidates CloudFront cache

The Docker image tag in the task definition (e.g., `langfuse-fix-v2-20251206`) points to an image built days ago. Local code changes exist only in the filesystem, not in the deployed container.

## How to Verify

Check which image the ECS task is using:
```bash
# Get running task ARN
aws ecs list-tasks --cluster pharma-test-gen-cluster --service-name pharma-test-gen-frontend --region eu-west-2

# Check the image being used
aws ecs describe-tasks --cluster pharma-test-gen-cluster --tasks <task-arn> --region eu-west-2 --query 'tasks[0].containers[0].image'
```

If the image tag is old (check the date in the tag), your code changes aren't deployed.

## Solution: Full Deployment Process for Code Changes

### Step 1: Login to ECR
```bash
wsl -e bash -c "aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 275333454012.dkr.ecr.eu-west-2.amazonaws.com"
```

### Step 2: Build and Push New Docker Image
```bash
wsl -e bash -c "cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project && \
docker buildx build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_BASE_URL='' \
  --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY='<your-clerk-key>' \
  -t 275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-frontend:<new-tag> \
  --push \
  -f Dockerfile.frontend ."
```

Use a descriptive tag with date, e.g., `trace-fix-v3-20251207`

### Step 3: Update Task Definition
Edit `aws/terraform/task-definition-frontend-v15.json`:
```json
"image": "275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-frontend:<new-tag>"
```

### Step 4: Redeploy
```bash
python aws/scripts/redeploy.py --frontend --wait
```

## Quick Reference

| Scenario | Command | Rebuilds Image? |
|----------|---------|-----------------|
| Code changes | Steps 1-4 above | YES (manual) |
| Config changes only | `redeploy.py --frontend` | NO |
| Full deployment | `python aws/scripts/deploy.py` | YES (automated) |
| Status check | `redeploy.py --status-only` | NO |

## Key Files

| File | Purpose |
|------|---------|
| `Dockerfile.frontend` | Docker build instructions |
| `aws/terraform/task-definition-frontend-v15.json` | ECS task config with image tag |
| `aws/scripts/redeploy.py` | Quick redeploy (no rebuild) |
| `aws/scripts/deploy.py` | Full deploy with image rebuild |

## Prevention

1. **Always verify image tag** after deployment if code changes don't appear
2. **Use `deploy.py`** for code changes (slower but handles everything)
3. **Use `redeploy.py`** only for:
   - Restarting services after config changes
   - Recovering from task failures
   - Testing same code with different environment variables
4. **Add visible debug logs** to verify code is actually deployed
5. **Check ECR image timestamps** if in doubt:
   ```bash
   aws ecr describe-images --repository-name pharma-test-gen-frontend --region eu-west-2 --query 'imageDetails[*].[imageTags,imagePushedAt]' --output table
   ```

## Related Issues

- ISSUE-003: The code fix for Langfuse trace was correct, but appeared not to work because of this deployment issue
