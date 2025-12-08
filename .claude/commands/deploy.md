---
description: Deploy the pharma-test-gen system to AWS ECS/Fargate. Full 2-phase deployment with Docker builds and Terraform. Takes 15-25 minutes.
argument-hint: (no arguments)
---

# Deploy to AWS ECS/Fargate

Full deployment of the pharmaceutical test generation system to AWS.

**Estimated time:** 15-25 minutes

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

1. **Docker** is running (Docker Desktop or WSL Docker)
2. **Terraform** is installed (in WSL at ~/bin/terraform)
3. **AWS CLI** is configured with credentials
4. **Environment variables** are set:
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (for frontend build)

## Execution

### Step 1: Check Prerequisites

Verify prerequisites are met:

```bash
docker info > /dev/null 2>&1 && echo "Docker: OK" || echo "Docker: NOT RUNNING"
aws sts get-caller-identity --query Account --output text 2>/dev/null && echo "AWS: OK" || echo "AWS: NOT CONFIGURED"
```

If Docker is not running or AWS is not configured, STOP and ask the user to fix.

### Step 2: Run Deploy Script

Run the full deployment script:

```bash
python aws/scripts/deploy.py
```

Use a **20-minute timeout** as this is a long-running operation.

The script executes in 2 phases:

**Phase 1: Backend + Infrastructure** (~10-15 min)
1. Authenticate with ECR
2. Build API image (linux/amd64)
3. Build Worker image (linux/amd64)
4. Push images to ECR
5. Run Terraform plan + apply
6. Wait for ECS services healthy

**Phase 2: Frontend** (~5-10 min)
1. Build Frontend image with CloudFront-relative URLs
2. Push to ECR
3. Register new task definition
4. Update ECS service
5. Invalidate CloudFront cache

### Step 3: Verify Deployment

After script completes, verify services are healthy:

```bash
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api pharma-test-gen-frontend pharma-test-gen-worker \
  --query "services[*].{name:serviceName,status:status,running:runningCount,desired:desiredCount}" \
  --output table \
  --region eu-west-2
```

Expected: All services show `running: 1, desired: 1`

### Step 4: Verify Task Definition Revisions (ISSUE-006)

**CRITICAL:** After Terraform apply, ECS may use old task definition revisions missing secrets.

```bash
# Check which revision each service is using
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api pharma-test-gen-worker pharma-test-gen-frontend \
  --query "services[*].{name:serviceName,taskDef:taskDefinition}" \
  --output table \
  --region eu-west-2

# Verify the API task definition has all required secrets
aws ecs describe-task-definition \
  --task-definition pharma-test-gen-api \
  --query "taskDefinition.containerDefinitions[0].secrets[*].name" \
  --region eu-west-2
```

Expected secrets: `DATABASE_URL`, `CLERK_PEM_PUBLIC_KEY`, `CLERK_ISSUER`, `OPENROUTER_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`

If secrets are missing, register the golden task definition:
```bash
aws ecs register-task-definition \
  --cli-input-json file://aws/terraform/task-definition-api-v20.json \
  --region eu-west-2

aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-api \
  --task-definition pharma-test-gen-api \
  --force-new-deployment --region eu-west-2
```

### Step 5: Verify IAM Policies (ISSUE-005)

**CRITICAL:** After destroy/deploy cycle, task roles may lose IAM policies.

```bash
# Check API task role has policies
aws iam list-attached-role-policies --role-name pharma-test-gen-api-task-role
aws iam list-role-policies --role-name pharma-test-gen-api-task-role
```

If empty, IAM policies need to be re-attached. See `main/docs/issues/ISSUE-005-rebuild-uses-wrong-image-tag.md`.

### Step 6: Upload ChromaDB (if fresh deploy)

After a fresh deploy (especially after `/destroy`), ChromaDB data needs to be uploaded:

```bash
# Check if ChromaDB exists in S3
aws s3 ls s3://pharma-test-gen-vectors-staging/chroma_db.tar.gz --region eu-west-2

# If missing, upload from local
tar -czvf /tmp/chroma_db.tar.gz -C main chroma_db
aws s3 cp /tmp/chroma_db.tar.gz s3://pharma-test-gen-vectors-staging/chroma_db.tar.gz --region eu-west-2
```

### Step 7: Report Results

Report deployment URLs to user:

| Service | URL |
|---------|-----|
| Production (Route 53) | https://csvgeneration.com |
| API Health | https://csvgeneration.com/health |
| Frontend | https://csvgeneration.com/generate |

## Troubleshooting

### Docker Build Failures

1. **QEMU crash** (ARM64 host building AMD64):
   ```powershell
   wsl --shutdown
   # Wait 10 seconds, retry
   ```

2. **Out of disk space**:
   ```bash
   docker system prune -a --volumes
   ```

### Terraform Failures

1. **ECR already exists**:
   ```bash
   # Script auto-imports, but if it fails:
   wsl bash -c 'export PATH=$HOME/bin:$PATH && cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform && terraform import -var-file=environments/staging.tfvars "module.ecr.aws_ecr_repository.this[\"api\"]" pharma-test-gen-api'
   ```

2. **State lock**:
   ```bash
   wsl bash -c 'export PATH=$HOME/bin:$PATH && cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform && terraform force-unlock -force LOCK_ID'
   ```

### ECS Service Not Starting

Check service events:
```bash
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api \
  --query 'services[0].events[0:5]' \
  --region eu-west-2
```

Check task logs:
```bash
aws logs tail /ecs/pharma-test-gen/api --follow --region eu-west-2
```

### API Returns 500: Missing Secrets (ISSUE-006)

**Symptom:** `{"detail":"CRITICAL: Authentication system not configured"}`

**Cause:** Wrong task definition revision running.

**Fix:** See Step 4 above to verify and fix task definition revision.

### API S3 403 Forbidden (ISSUE-005)

**Symptom:** S3 AccessDenied errors in API logs.

**Cause:** Task role missing IAM policies after Terraform destroy/apply.

**Fix:** Re-attach policies. See `main/docs/issues/ISSUE-005-rebuild-uses-wrong-image-tag.md`.

### Worker Not Starting

**Symptom:** Worker shows `desired=1, running=0` indefinitely.

**Cause:** ChromaDB tarball missing in S3.

**Fix:** Upload ChromaDB as shown in Step 6.

For more troubleshooting, invoke the `aws-deployment` skill.

## Post-Deploy: Register Task Definitions

After initial deploy, you may need to register the golden task definitions with all secrets:

```bash
aws ecs register-task-definition \
  --cli-input-json file://aws/terraform/task-definition-api-v20.json \
  --region eu-west-2

aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-api \
  --task-definition pharma-test-gen-api \
  --force-new-deployment --region eu-west-2
```

## Cost Information

**Estimated hourly cost:** ~$0.50-1.00/hour
**Estimated monthly cost:** ~$360-720/month (if running 24/7)

Use `/destroy` command at end of day to save costs.
