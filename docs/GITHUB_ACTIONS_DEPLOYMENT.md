# GitHub Actions CI/CD Deployment

Automated deployment pipeline using GitHub Actions with AWS OIDC authentication.

**Trigger:** Push to `deploy` branch
**Workflow:** `.github/workflows/deploy.yml`

---

## Overview

```
Push to deploy branch
        │
        ▼
┌───────────────────┐
│  Build & Push     │  (3 parallel jobs)
│  - api            │
│  - worker         │
│  - frontend       │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Terraform Apply  │
│  (Infrastructure) │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Update Services  │
│  (Force deploy)   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Health Check &   │
│  Cache Invalidate │
└───────────────────┘
```

---

## Pipeline Jobs

### 1. Build and Push (Parallel)

Builds Docker images for all 3 services in parallel:

```yaml
strategy:
  matrix:
    service: [api, worker, frontend]
```

**Steps:**
1. Checkout code
2. Configure AWS credentials (OIDC)
3. Login to ECR
4. Build Docker image with appropriate Dockerfile
5. Push to ECR with `staging-latest` tag

**Frontend special handling:**
```bash
docker build \
  --build-arg NEXT_PUBLIC_API_BASE_URL="" \
  --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="$SECRET" \
  -f Dockerfile.frontend .
```

### 2. Deploy Infrastructure

Runs `terraform apply` after images are pushed:

```yaml
needs: build-and-push
working-directory: aws/terraform
run: terraform apply -var-file=environments/staging.tfvars -auto-approve
```

### 3. Update ECS Services

Forces new deployment to pull latest images:

```bash
for service in api worker frontend; do
  aws ecs update-service \
    --cluster pharma-test-gen-cluster \
    --service pharma-test-gen-${service} \
    --force-new-deployment
done

aws ecs wait services-stable \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api pharma-test-gen-worker pharma-test-gen-frontend
```

### 4. Health Check & Cache Invalidation

```bash
# API health check (5 retries)
curl -sf https://csvgeneration.com/health

# Frontend check
curl -sf https://csvgeneration.com/ | grep -q "<!DOCTYPE html>"

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id E1DTSJYZQGK50L \
  --paths "/*"
```

---

## OIDC Authentication

GitHub Actions authenticates to AWS using OIDC (no stored credentials):

### IAM Role

```
Role: pharma-test-gen-github-actions
ARN: arn:aws:iam::275333454012:role/pharma-test-gen-github-actions
```

### Trust Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::275333454012:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      },
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:Danik911/thesis_project:*"
      }
    }
  }]
}
```

### Required Permissions

- ECR: Push/pull images
- ECS: Update services, describe tasks
- Terraform: Full infrastructure management
- CloudFront: Create invalidations
- S3: Terraform state access
- DynamoDB: Terraform locks

---

## Secrets Configuration

### GitHub Secrets

| Secret | Description |
|--------|-------------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk frontend key |

### AWS Secrets Manager

Secrets referenced in task definitions (not in GitHub):
- `pharma-test-gen/clerk-secret-key`
- `pharma-test-gen/clerk-pem-public-key`
- `pharma-test-gen/openrouter-api-key`
- `pharma-test-gen/langfuse-public-key`
- `pharma-test-gen/langfuse-secret-key`

---

## Triggering Deployment

### Automatic (Push)

```bash
git checkout deploy
git merge main
git push origin deploy
```

### Manual (GitHub UI)

1. Go to Actions tab
2. Select "Deploy to AWS ECS"
3. Click "Run workflow"
4. Select `deploy` branch

### Manual (CLI)

```bash
gh workflow run deploy.yml --ref deploy
```

---

## Monitoring Deployment

### Watch in Terminal

```bash
gh run watch --exit-status
```

### View Logs

```bash
# List recent runs
gh run list --workflow=deploy.yml

# View specific run
gh run view <run-id> --log
```

### Check ECS Status

```bash
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api pharma-test-gen-worker pharma-test-gen-frontend \
  --query 'services[*].[serviceName,runningCount,desiredCount]' \
  --output table
```

---

## Rollback

### Quick Rollback (Previous Task Definition)

```bash
# Find previous revision
aws ecs list-task-definitions --family-prefix pharma-test-gen-api

# Update service to previous revision
aws ecs update-service \
  --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-api \
  --task-definition pharma-test-gen-api:18 \
  --region eu-west-2
```

### Full Rollback (Git Revert)

```bash
git checkout deploy
git revert HEAD
git push origin deploy
# Pipeline redeploys previous version
```

---

## Workflow File

Location: `.github/workflows/deploy.yml`

```yaml
name: Deploy to AWS ECS

on:
  push:
    branches: [deploy]
  workflow_dispatch:

permissions:
  id-token: write   # OIDC
  contents: read

env:
  AWS_REGION: eu-west-2
  ECR_REGISTRY: 275333454012.dkr.ecr.eu-west-2.amazonaws.com
  PROJECT_NAME: pharma-test-gen
  CLUSTER_NAME: pharma-test-gen-cluster

jobs:
  build-and-push:
    # ... (see full file)
  deploy-infrastructure:
    needs: build-and-push
    # ...
  update-services:
    needs: deploy-infrastructure
    # ...
  health-check:
    needs: update-services
    # ...
```

---

## Troubleshooting

### OIDC Authentication Fails

```
Error: Could not assume role with OIDC
```

**Check:**
1. Trust policy allows repo/branch
2. OIDC provider exists in IAM
3. Role has required permissions

### Terraform State Lock

```
Error: Error acquiring the state lock
```

**Fix:**
```bash
# Force unlock (use with caution)
terraform force-unlock <LOCK_ID>
```

### Health Check Fails

```
Error: API health check failed after 5 attempts
```

**Check:**
1. ECS tasks running: `aws ecs list-tasks --cluster pharma-test-gen-cluster`
2. Container logs: `aws logs tail /ecs/pharma-test-gen/api --since 5m`
3. ALB target health: Check AWS Console
