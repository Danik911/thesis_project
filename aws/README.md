# AWS Deployment Guide

## Overview

This directory contains Terraform infrastructure and scripts for deploying the pharmaceutical test generation system to AWS.

> **AI4LIMS PoC**: The LIMS document extraction prototype (branch: `prjoject_p_protatype`) uses a minimal local Docker stack for development. Post-PoC, it can reuse this AWS ECS/Fargate infrastructure with additional `/lims/*` API routes.

## Current Deployment Status (Live)

**Last Updated:** 2025-12-03
**Environment:** Staging (eu-west-2 London)
**AWS Account:** 275333454012

### Live URLs

| Service | URL | Status |
|---------|-----|--------|
| **CloudFront (HTTPS)** | https://d2yiysdqio0ryi.cloudfront.net | ✅ Running |
| **Frontend ALB (HTTP)** | http://pharma-test-gen-frontend-alb-1248845402.eu-west-2.elb.amazonaws.com | ✅ Running |
| **API ALB (HTTP)** | http://pharma-test-gen-api-alb-1215564166.eu-west-2.elb.amazonaws.com | ✅ Running |
| **API Health** | https://d2yiysdqio0ryi.cloudfront.net/health | ✅ Healthy |

### CloudFront Distribution (Terraform Managed)

| Property | Value |
|----------|-------|
| **Distribution ID** | E3CO1HBNMIUKPB |
| **Domain** | d2yiysdqio0ryi.cloudfront.net |
| **SSL/TLS** | CloudFront default certificate |
| **Origins** | Frontend ALB (default), API ALB (/jobs*, /api/*, /health*) |
| **Cache Policy** | CachingDisabled for API routes |
| **Managed By** | Terraform (`aws/terraform/modules/cloudfront/`) |

**Note:** CloudFront is fully managed by Terraform. When ALBs are recreated during destroy/deploy cycles, CloudFront origins auto-update. No manual intervention needed.

### Running Services

| Service | Task Definition | Image Tag | Resources |
|---------|-----------------|-----------|-----------|
| pharma-test-gen-frontend | v13 | staging-nullish-fix | 0.25 vCPU / 0.5 GB |
| pharma-test-gen-api | v21 | chromadb-settings-fix | 1 vCPU / 2 GB |
| pharma-test-gen-worker | v24 | diagnostic-v2 | 2 vCPU / 4 GB |

**Golden Task Definitions (use after redeploy):**
- `aws/terraform/task-definition-api-v19.json` - API with all secrets (Clerk, OpenRouter, LangFuse)
- `aws/terraform/task-definition-worker-v21.json` - Worker with all secrets and ChromaDB config
- `aws/terraform/task-definition-frontend-v13.json` - Frontend without API URL env var

## Architecture

```
CloudFront (d2yiysdqio0ryi.cloudfront.net)
├── / → Frontend ALB (HTTP) → ECS Frontend
├── /jobs* → API ALB (HTTP) → ECS API
├── /api/* → API ALB (HTTP) → ECS API
└── /health* → API ALB (HTTP) → ECS API

ECS Worker → SQS Queue → Process jobs → S3 output
           → ChromaDB (embedded) → RAG retrieval
```

### Key Components

| Component | Resource | Purpose |
|-----------|----------|---------|
| Frontend | ECS Fargate (0.25 vCPU, 0.5GB) | Next.js + Clerk auth |
| API | ECS Fargate (1 vCPU, 2GB) | FastAPI job management |
| Worker | ECS Fargate (2 vCPU, 4GB) | Process test generation jobs |
| CDN | CloudFront | HTTPS termination, path routing |
| Job Queue | SQS + DLQ | Async job processing |
| Auth | Clerk (EU) | JWT authentication |
| LLM | OpenRouter (DeepSeek V3) | Test case generation |

### ChromaDB RAG (Task 4.2 - IN PROGRESS)

The Context Provider Agent uses ChromaDB for regulatory document retrieval:

1. **S3 Storage**: Compressed ChromaDB tarball in S3 bucket (PENDING)
2. **Worker Startup**: Downloads and extracts to `/app/chroma_db`
3. **In-Process Query**: ChromaDB runs embedded in worker (<10ms latency)

**Status:** Task 4.2.2-4.2.5 PENDING - Worker needs S3 ChromaDB configuration
**Cost**: ~$0.02/month (S3 storage only)

## Directory Structure

```
aws/
├── terraform/                  # Infrastructure as Code
│   ├── main.tf                # Core resources (ECS, S3, IAM, SQS)
│   ├── variables.tf           # Input variables
│   ├── outputs.tf             # Output values
│   └── modules/               # Reusable modules
│       ├── ecr/               # Container registry (prevent_destroy lifecycle)
│       ├── ecs-cluster/       # ECS cluster
│       ├── ecs-service/       # ECS services
│       ├── alb/               # Load balancers (create_before_destroy)
│       ├── cloudfront/        # CloudFront distribution (auto-updates with ALBs)
│       └── sqs/               # Job queue
├── scripts/
│   ├── 1_upload_chroma_to_s3.py      # Upload ChromaDB to S3
│   ├── deploy.py                     # Deployment automation
│   ├── destroy.py                    # Teardown automation
│   ├── DEPLOY_DESTROY_FIXES.md       # Troubleshooting guide
│   └── run_local.py                  # Local development
└── README.md                         # This file
```

## Deployment Steps

### Prerequisites

```bash
# Install AWS CLI
pip install awscli boto3

# Configure credentials
aws configure
# Enter: Access Key, Secret Key, Region (eu-west-2), Output (json)
```

### Step 1: Deploy Infrastructure

```bash
cd aws/terraform

# Initialize Terraform
terraform init

# Review changes
terraform plan

# Deploy infrastructure
terraform apply
```

This creates:
- S3 bucket for ChromaDB (`pharma-test-gen-chromadb-{account_id}`)
- ECS Cluster, Services, Task Definitions
- CloudFront distribution (HTTPS termination)
- SQS Queue + Dead Letter Queue
- IAM Roles with least-privilege permissions

### Automated Deploy/Destroy Scripts

For a streamlined workflow, use the automation scripts:

```bash
# Deploy everything (two-phase: backend first, then frontend with API URL)
python aws/scripts/deploy.py

# Destroy everything (preserves ECR repos and Terraform state)
python aws/scripts/destroy.py --yes --skip-ecr

# Redeploy after destroy (CloudFront auto-updates, no manual intervention)
python aws/scripts/deploy.py
```

**Key Features:**
- `deploy.py`: Two-phase deployment, imports existing ECR repos, health verification
- `destroy.py`: Removes ECR from state (repos kept in AWS), CloudFront destroyed cleanly
- **CloudFront auto-updates**: When ALBs change, Terraform updates CloudFront origins automatically

### Post-Redeploy: Register Golden Task Definitions

After `destroy.py` + `deploy.py`, Terraform recreates task definitions but **loses manually-added secrets** (Clerk, OpenRouter, LangFuse). Re-register the golden task definitions:

```bash
# 1. Register API task definition (includes ALL secrets)
aws ecs register-task-definition \
  --cli-input-json file://aws/terraform/task-definition-api-v19.json \
  --region eu-west-2

# 2. Register Worker task definition (includes ALL secrets)
aws ecs register-task-definition \
  --cli-input-json file://aws/terraform/task-definition-worker-v21.json \
  --region eu-west-2

# 3. Update API service
aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-api --task-definition pharma-test-gen-api \
  --force-new-deployment --region eu-west-2

# 4. Update Worker service
aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-worker --task-definition pharma-test-gen-worker \
  --force-new-deployment --region eu-west-2

# 5. Register frontend task definition (no API URL env var)
aws ecs register-task-definition \
  --cli-input-json file://aws/terraform/task-definition-frontend-v13.json \
  --region eu-west-2

# 6. Update frontend service
aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-frontend --task-definition pharma-test-gen-frontend \
  --force-new-deployment --region eu-west-2

# 7. Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id E3CO1HBNMIUKPB --paths '/*'
```

**Quick Redeploy Script** (no Terraform, just task definitions):
```bash
python aws/scripts/redeploy.py
```

See `aws/scripts/DEPLOY_DESTROY_FIXES.md` for full post-redeploy checklist and troubleshooting.

### Step 2: Upload ChromaDB to S3

```bash
# From project root
python aws/scripts/1_upload_chroma_to_s3.py
```

**What it does:**
- Creates tarball of `main/chroma_db/` directory
- Uploads to S3 bucket with versioning
- Enables encryption (AES-256)

**Output:**
```
Uploaded to s3://pharma-test-gen-chromadb-{account}/chroma_db.tar.gz
```

### Step 3: Build and Push Docker Images

```bash
# Build and push worker image
docker build -t pharma-test-gen-worker -f Dockerfile.worker.pip .
docker tag pharma-test-gen-worker:latest {ecr_url}/worker:latest
docker push {ecr_url}/worker:latest
```

### Step 4: Verify Deployment

```bash
# Check ECS service status
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-worker

# Check CloudWatch logs
aws logs tail /ecs/pharma-test-gen/worker --follow
```

## Environment Variables (Production)

Set automatically by ECS task definition:

| Variable | Description |
|----------|-------------|
| `ENVIRONMENT` | `production` |
| `S3_CHROMADB_BUCKET` | S3 bucket for ChromaDB |
| `S3_CHROMADB_KEY` | `chroma_db.tar.gz` |
| `RAG_VECTOR_STORE_PATH` | `/app/chroma_db` |
| `AWS_REGION` | `eu-west-2` |
| `SQS_QUEUE_URL` | Job queue URL |

## Updating ChromaDB (Quarterly)

When regulatory documents change:

```bash
# 1. Update local ChromaDB
python main/scripts/seed_chroma.py

# 2. Re-upload to S3
python aws/scripts/1_upload_chroma_to_s3.py

# 3. ECS worker picks up new version on next container restart
# Or force restart:
aws ecs update-service \
  --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-worker \
  --force-new-deployment
```

## Cost Estimate (Monthly)

| Component | Cost |
|-----------|------|
| ECS Fargate (3 tasks) | ~$75 |
| CloudFront distribution | ~$10 |
| S3 ChromaDB Storage (2MB) | $0.02 |
| SQS Queue | $0.50 |
| Application Load Balancers (2) | ~$30 |
| CloudWatch Logs | $5 |
| **Total** | **~$120/month** |

> **Note**: AI4LIMS PoC runs locally via `docker-compose.lims.yml`. No additional AWS costs during PoC phase.

## Security

- **IAM Roles**: Least-privilege permissions
- **S3 Encryption**: AES-256 server-side
- **VPC**: Private subnets for ECS tasks
- **Secrets Manager**: API keys and credentials
- **Public Access Blocked**: S3 buckets

## Known Issues & Workarounds

### QEMU Emulation Crashes (ARM64 Hosts)

If you're building on ARM64 (Snapdragon X Elite, Apple Silicon) and see:
```
qemu-x86_64: QEMU internal SIGBUS
fatal error: fault
```

**Solution:**
```powershell
# On Windows
wsl --shutdown
# Wait a few seconds, then retry the build
```

For production, consider using AWS CodeBuild to build AMD64 images natively.

### CloudFront-Relative URLs (Mixed Content Fix)

The frontend uses **empty** `NEXT_PUBLIC_API_BASE_URL` so API calls use relative paths:
- `/jobs` instead of `http://alb.../jobs`
- CloudFront routes `/jobs*`, `/api/*`, `/health*` to API ALB

**Important:** Frontend code uses `??` (nullish coalescing) instead of `||`:
```typescript
// CORRECT: Only falls back for null/undefined
process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8080'

// WRONG: Empty string "" is falsy, falls back to localhost
process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080'
```

This avoids Mixed Content errors (HTTPS page calling HTTP API).

### Missing Secrets After Redeploy

Terraform doesn't preserve manually-added secrets (Clerk, OpenRouter, LangFuse). After `destroy.py` + `deploy.py`:

**Symptom:**
```
CRITICAL: Authentication system not configured (missing CLERK_PEM_PUBLIC_KEY)
```

**Solution:** Register golden task definitions (see "Post-Redeploy" section above).

See `aws/scripts/DEPLOY_DESTROY_FIXES.md` for full troubleshooting guide.

---

## Troubleshooting

### ChromaDB Empty Collections (CRITICAL - 2025-12-03)

**Symptom:**
```
CRITICAL: Context Provider cannot execute - ALL ChromaDB collections are empty.
Empty collections: ['gamp5', 'regulatory', 'best_practices']
```

**Root Causes:**
1. **Tarball extraction path mismatch**: `init_chromadb.py` may extract to wrong location
2. **Collection name mismatch**: Code expects different collection names than what exists
3. **Docker images not updated**: ECS containers running old code without fixes

**Verification Steps:**
```bash
# 1. Verify S3 tarball exists and has size
aws s3 ls s3://pharma-test-gen-vectors-staging/chroma_db.tar.gz

# 2. Check tarball structure (should have chroma_db/ directory)
aws s3 cp s3://pharma-test-gen-vectors-staging/chroma_db.tar.gz - | tar -tzf - | head -20

# 3. Verify in ECS container (use ECS Exec)
aws ecs execute-command --cluster pharma-test-gen-cluster \
  --task <task-id> --container worker --interactive \
  --command "/bin/sh"

# Inside container:
ls -la /app/chroma_db/
python -c "import chromadb; c=chromadb.PersistentClient(path='/app/chroma_db'); [print(f'{col.name}: {col.count()}') for col in c.list_collections()]"
```

**Resolution (Full Redeployment Required):**
1. Destroy services: `python aws/scripts/destroy.py --yes --skip-ecr`
2. Rebuild Docker images with fixes (need AMD64 builder)
3. Redeploy: `python aws/scripts/deploy.py`
4. Re-upload ChromaDB: `python aws/scripts/1_upload_chroma_to_s3.py`
5. Restart worker service

**Full Issue Documentation:** `main/docs/issues/2025-12-03-chromadb-empty-collections.md`

### ChromaDB Download Fails

```bash
# Check S3 bucket exists and has data
aws s3 ls s3://pharma-test-gen-chromadb-{account}/

# Check worker IAM role has s3:GetObject
aws ecs describe-task-definition \
  --task-definition pharma-test-gen-worker \
  --query 'taskDefinition.taskRoleArn'
```

### Worker Not Starting

```bash
# Check CloudWatch logs for errors
aws logs tail /ecs/pharma-test-gen/worker --since 10m

# Common issues:
# - S3_CHROMADB_BUCKET not set
# - IAM permission denied
# - Insufficient memory (needs 8GB)
```

### ECS Service Unhealthy

```bash
# Check task status
aws ecs list-tasks --cluster pharma-test-gen-cluster

# Describe stopped tasks
aws ecs describe-tasks \
  --cluster pharma-test-gen-cluster \
  --tasks {task_arn}
```

## Recovery After Destroy

If infrastructure was destroyed (overnight cleanup, manual destroy, Terraform issue), use these steps to recover quickly.

### 1. Check If Services Exist

```bash
aws ecs describe-services --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api pharma-test-gen-worker pharma-test-gen-frontend \
  --region eu-west-2
```

If cluster doesn't exist, run full `terraform apply`. If services exist but tasks are failing, see step 2.

### 2. Quick Recovery (No Terraform)

When only task definitions need updating (secrets lost, config changed):

```bash
# Use the redeploy script (recommended)
python aws/scripts/redeploy.py

# Or manually:
aws ecs register-task-definition --cli-input-json file://aws/terraform/task-definition-api-v19.json --region eu-west-2
aws ecs register-task-definition --cli-input-json file://aws/terraform/task-definition-worker-v21.json --region eu-west-2
aws ecs update-service --cluster pharma-test-gen-cluster --service pharma-test-gen-api --task-definition pharma-test-gen-api --force-new-deployment --region eu-west-2
aws ecs update-service --cluster pharma-test-gen-cluster --service pharma-test-gen-worker --task-definition pharma-test-gen-worker --force-new-deployment --region eu-west-2
```

### 3. Full Recovery (Terraform + Secrets)

When infrastructure was completely destroyed:

```bash
# 1. Deploy infrastructure
cd aws/terraform && terraform init && terraform apply

# 2. Register golden task definitions (Terraform creates basic ones without secrets)
aws ecs register-task-definition --cli-input-json file://aws/terraform/task-definition-api-v19.json --region eu-west-2
aws ecs register-task-definition --cli-input-json file://aws/terraform/task-definition-worker-v21.json --region eu-west-2
aws ecs register-task-definition --cli-input-json file://aws/terraform/task-definition-frontend-v13.json --region eu-west-2

# 3. Force redeploy all services
aws ecs update-service --cluster pharma-test-gen-cluster --service pharma-test-gen-api --task-definition pharma-test-gen-api --force-new-deployment --region eu-west-2
aws ecs update-service --cluster pharma-test-gen-cluster --service pharma-test-gen-worker --task-definition pharma-test-gen-worker --force-new-deployment --region eu-west-2
aws ecs update-service --cluster pharma-test-gen-cluster --service pharma-test-gen-frontend --task-definition pharma-test-gen-frontend --force-new-deployment --region eu-west-2

# 4. Wait for services to stabilize (2-5 minutes)
aws ecs wait services-stable --cluster pharma-test-gen-cluster --services pharma-test-gen-api pharma-test-gen-worker --region eu-west-2
```

### 4. Verify Health

```bash
# Check service status
aws ecs describe-services --cluster pharma-test-gen-cluster --services pharma-test-gen-api pharma-test-gen-worker --region eu-west-2 --query 'services[*].[serviceName,runningCount,desiredCount]'

# Check API health
curl https://d2yiysdqio0ryi.cloudfront.net/health

# Check CloudWatch logs for errors
aws logs tail /ecs/pharma-test-gen/api --since 5m --region eu-west-2
aws logs tail /ecs/pharma-test-gen/worker --since 5m --region eu-west-2
```

### Common Recovery Scenarios

| Symptom | Cause | Solution |
|---------|-------|----------|
| "Missing CLERK_PEM_PUBLIC_KEY" | Secrets lost after Terraform | Register golden task definitions |
| "QEMU internal SIGBUS" | ARM64 cross-compilation crash | Run `wsl --shutdown`, retry |
| Services at 0/1 desired | Task definition outdated | Register + force redeploy |
| CloudFront 502 errors | ALBs changed, origins stale | Wait for Terraform update or invalidate cache |

---

## Destroy/Deploy Cycle Troubleshooting (2025-12-06)

This section documents issues encountered during destroy/deploy cycles and their solutions.

### Issue 1: ECR "Already Exists" Error

**Symptom:**
```
Error: creating ECR Repository (pharma-test-gen-api): RepositoryAlreadyExistsException
```

**Cause:** ECR repos have `prevent_destroy = true` and are removed from Terraform state during destroy. On redeploy, Terraform tries to create repos that already exist in AWS.

**Solution:** Use Terraform import blocks (already created in `aws/terraform/imports.tf`):
```hcl
import {
  to = module.ecr.aws_ecr_repository.this["api"]
  id = "pharma-test-gen-api"
}
```

**Prevention:** `deploy.py` includes `import_ecr_to_terraform_state()` that handles this automatically.

### Issue 2: Terraform Not in PATH (Windows)

**Symptom:**
```
terraform: command not found
```

**Cause:** Windows Git Bash doesn't have terraform in PATH.

**Solution:** All scripts (`deploy.py`, `destroy.py`) use WSL wrapper:
```python
if is_windows():
    cmd = ["wsl", "-e", "bash", "-c", f"export PATH=$HOME/bin:$PATH && {cmd}"]
```

**Prevention:** Install terraform in WSL at `~/bin/terraform`.

### Issue 3: ChromaDB S3 Bucket Empty

**Symptom:**
```
Worker at 0/1 - failing repeatedly
403 Forbidden on s3://pharma-test-gen-chromadb-*/chroma_db.tar.gz
```

**Cause:** `destroy.py` previously emptied all S3 buckets including chromadb.

**Solution (Applied):**
1. `destroy.py` now preserves chromadb bucket by default
2. `deploy.py` now includes `ensure_chromadb_in_s3()` that uploads if empty

**Manual Fix (if needed):**
```bash
# From project root (WSL)
tar -czvf /tmp/chroma_db.tar.gz -C lib chroma_db
aws s3 cp /tmp/chroma_db.tar.gz s3://pharma-test-gen-chromadb-275333454012/chroma_db.tar.gz --region eu-west-2
```

### Issue 4: IAM Policy References Wrong Bucket

**Symptom:**
```
AccessDenied when worker tries to download chromadb from S3
```

**Cause:** `main.tf` worker IAM policy hardcoded legacy bucket name (`pharma-test-gen-vectors-staging`) instead of Terraform-managed bucket.

**Solution (Applied):** Updated `main.tf` to use Terraform resource ARN:
```hcl
Resource = [
  aws_s3_bucket.chromadb.arn,
  "${aws_s3_bucket.chromadb.arn}/*"
]
```

### Issue 5: Windows Path Conversion in AWS CLI

**Symptom:**
```
aws logs tail /ecs/pharma-test-gen/worker
# Error: path converted to C:/Program Files/Git/ecs/...
```

**Cause:** Git Bash on Windows converts paths starting with `/` to Windows paths.

**Solution:** Use WSL for AWS CLI commands with paths:
```bash
wsl -e bash -c "aws logs tail /ecs/pharma-test-gen/worker --since 10m --region eu-west-2"
```

### Quick Recovery After Destroy

```bash
# 1. Deploy infrastructure (includes ECR import check, chromadb upload)
python aws/scripts/deploy.py

# 2. Register golden task definitions and wait for health
python aws/scripts/redeploy.py --wait

# 3. Verify all services healthy
python aws/scripts/redeploy.py --status-only
```

### Preserved Resources (Cost: ~$0.12/month)

After `destroy.py`, these resources are preserved for quick re-deployment:
- S3: `pharma-test-gen-terraform-state` (~$0.02/month)
- S3: `pharma-test-gen-chromadb-*` (RAG database, ~$0.08/month)
- DynamoDB: `pharma-test-gen-terraform-locks` (~$0.00/month)
- ECR repos (3): Images kept for instant redeploy (~$0.02/month)

---

## Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)
