---
description: Deploy the pharma-test-gen system to AWS ECS/Fargate. Full 2-phase deployment with Docker builds and Terraform. Takes 15-25 minutes.
argument-hint: (no arguments)
---

# Deploy to AWS ECS/Fargate (Fire-and-Forget)

Full deployment of the pharmaceutical test generation system to AWS using GitHub Actions.

**Estimated time:** 15-20 minutes (fully automated)

**Production URL:** https://csvgeneration.com/

## What Will Be Deployed

| Service | Description |
|---------|-------------|
| API | FastAPI backend (port 8080) |
| Worker | Background job processor |
| Frontend | Next.js UI (port 3000) |
| ALBs | 2 Application Load Balancers |
| CloudFront | CDN with HTTPS |
| SQS | Job queue |

## Prerequisites

Before running, ensure:

1. **GitHub CLI** is installed and authenticated (`gh auth login`)
2. **GitHub Secret** `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is configured in repo settings
3. **OIDC IAM Role** exists in AWS (created via Terraform)

## Execution

### Option 1: Trigger GitHub Actions (Recommended)

```bash
gh workflow run deploy.yml
```

This triggers the Fire-and-Forget workflow which:
1. Builds all 3 Docker images in parallel (native AMD64, no QEMU)
2. Pushes images to ECR
3. Runs Terraform apply
4. Forces ECS service updates
5. Waits for services to stabilize
6. Runs health checks
7. Invalidates CloudFront cache

### Option 2: Push to Deploy Branch

```bash
git push origin deploy
```

Any push to the `deploy` branch automatically triggers the workflow.

### Option 3: GitHub UI

1. Go to https://github.com/Danik911/thesis_project/actions
2. Select "Deploy to AWS ECS" workflow
3. Click "Run workflow"

## Monitoring Progress

### Watch GitHub Actions

```bash
gh run watch
```

Or view in browser:
```bash
gh run list --workflow=deploy.yml
```

### Check ECS Status

```bash
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api pharma-test-gen-frontend pharma-test-gen-worker \
  --query "services[*].{name:serviceName,status:status,running:runningCount,desired:desiredCount}" \
  --output table \
  --region eu-west-2
```

## Verify Deployment

After workflow completes:

```bash
# Health check
curl -s https://csvgeneration.com/health | jq

# Frontend check
curl -sI https://csvgeneration.com/ | head -5
```

Expected: `200 OK` responses.

## Deployment URLs

| Service | URL |
|---------|-----|
| Production | https://csvgeneration.com |
| API Health | https://csvgeneration.com/health |
| Generate Page | https://csvgeneration.com/generate |

## Troubleshooting

### GitHub Actions Workflow Failed

```bash
# View recent runs
gh run list --workflow=deploy.yml --limit 5

# View specific run logs
gh run view <RUN_ID> --log-failed
```

### OIDC Authentication Error

**Symptom:** `Error: Could not assume role`

**Cause:** OIDC provider or IAM role not created.

**Fix:**
```bash
wsl -e bash -c 'cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform && terraform apply -var-file=environments/staging.tfvars -target=aws_iam_openid_connect_provider.github -target=aws_iam_role.github_actions -auto-approve'
```

### Missing NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY Secret

**Symptom:** Frontend build fails with missing env var.

**Fix:** Add the secret in GitHub repo settings:
1. Go to Settings > Secrets and variables > Actions
2. Add `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` with your Clerk publishable key

### ECS Service Not Starting

Check CloudWatch logs:
```bash
aws logs tail /ecs/pharma-test-gen/api --follow --region eu-west-2
```

### Worker Missing ChromaDB

After fresh deploy, upload ChromaDB:
```bash
tar -czvf /tmp/chroma_db.tar.gz -C main chroma_db
aws s3 cp /tmp/chroma_db.tar.gz s3://pharma-test-gen-vectors-staging/chroma_db.tar.gz --region eu-west-2
```

## Local Deployment (Fallback)

If GitHub Actions fails, use the local script:

```bash
python aws/scripts/deploy.py
```

Note: This requires QEMU and takes 40-60 minutes with ~60% reliability.

## Cost Information

**Estimated hourly cost:** ~$0.50-1.00/hour
**Estimated monthly cost:** ~$360-720/month (if running 24/7)

Use `/destroy` command at end of day to save costs.

## Related Commands

- `/redeploy` - Quick redeploy without Docker builds
- `/destroy` - Tear down infrastructure to save costs
