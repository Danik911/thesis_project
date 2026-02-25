# AWS Deployment Guide

ECS Fargate deployment for pharmaceutical test generation system.

**Live URL:** https://csvgeneration.com
**Region:** eu-west-2 (London)
**Account:** 275333454012

---

## Architecture

```
                    Route 53 (csvgeneration.com)
                              │
                              ▼
                    CloudFront (E1DTSJYZQGK50L)
                    ACM Cert: *.csvgeneration.com
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
     /* (default)        /jobs*, /api/*      Worker (SQS)
           │                  │                  │
           ▼                  ▼                  ▼
    Frontend ALB          API ALB           SQS Queue
         │                    │                  │
         ▼                    ▼                  ▼
    ECS Frontend         ECS API            ECS Worker
    (0.25 vCPU)         (1 vCPU)           (2 vCPU)
    Next.js 14          FastAPI            LlamaIndex
```

### Services

| Service | Resources | Image Tag | Task Definition |
|---------|-----------|-----------|-----------------|
| Frontend | 0.25 vCPU / 0.5 GB | staging-latest | v13 |
| API | 1 vCPU / 2 GB | staging-latest | v21 |
| Worker | 2 vCPU / 4 GB | staging-latest | v24 |

---

## Quick Commands

```bash
# Check service status
python aws/scripts/redeploy.py --status-only

# Redeploy all services (no Docker builds)
python aws/scripts/redeploy.py

# Redeploy specific service
python aws/scripts/redeploy.py --api
python aws/scripts/redeploy.py --worker
python aws/scripts/redeploy.py --frontend

# Full deployment with Terraform
python aws/scripts/deploy.py

# Destroy infrastructure (preserves ECR, S3)
python aws/scripts/destroy.py --yes --skip-ecr
```

---

## Deployment Steps

### Prerequisites

```bash
# AWS CLI configured
aws configure
# Region: eu-west-2, Output: json

# Terraform in WSL
wsl -e bash -c "terraform --version"
```

### 1. Deploy Infrastructure

```bash
cd aws/terraform
terraform init
terraform plan
terraform apply
```

Creates: ECS Cluster, ALBs, CloudFront, SQS, IAM Roles, S3 Buckets

### 2. Build and Push Images

```bash
# Login to ECR
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 275333454012.dkr.ecr.eu-west-2.amazonaws.com

# Build and push (from WSL)
docker build -t pharma-test-gen-api -f Dockerfile.api.pip .
docker tag pharma-test-gen-api:latest 275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-api:staging-latest
docker push 275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-api:staging-latest
```

### 3. Register Task Definitions

After `terraform apply`, register golden task definitions with secrets:

```bash
# API (includes Clerk, OpenRouter, LangFuse secrets)
aws ecs register-task-definition \
  --cli-input-json file://aws/terraform/task-definition-api-v19.json \
  --region eu-west-2

# Worker
aws ecs register-task-definition \
  --cli-input-json file://aws/terraform/task-definition-worker-v21.json \
  --region eu-west-2

# Frontend
aws ecs register-task-definition \
  --cli-input-json file://aws/terraform/task-definition-frontend-v13.json \
  --region eu-west-2
```

### 4. Force Service Update

```bash
for service in api worker frontend; do
  aws ecs update-service \
    --cluster pharma-test-gen-cluster \
    --service pharma-test-gen-${service} \
    --force-new-deployment \
    --region eu-west-2
done
```

### 5. Verify Health

```bash
# Wait for stability
aws ecs wait services-stable \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api pharma-test-gen-worker pharma-test-gen-frontend

# Health check
curl https://csvgeneration.com/health
```

---

## DNS & SSL Configuration

### Route 53

| Record | Type | Target |
|--------|------|--------|
| csvgeneration.com | A (Alias) | CloudFront E1DTSJYZQGK50L |
| app.csvgeneration.com | A (Alias) | CloudFront E1DTSJYZQGK50L |
| api.csvgeneration.com | A (Alias) | CloudFront E1DTSJYZQGK50L |

### CloudFront Behaviors

| Path | Origin | Cache |
|------|--------|-------|
| `/jobs*` | API ALB | Disabled |
| `/api/*` | API ALB | Disabled |
| `/bi/*` | API ALB | Disabled |
| `/health*` | API ALB | Disabled |
| `/*` (default) | Frontend ALB | Optimized |

---

## Environment Variables

Set via Secrets Manager and task definitions:

| Variable | Service | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | API, Worker | LLM access |
| `LANGFUSE_PUBLIC_KEY` | API, Worker | Observability |
| `LANGFUSE_SECRET_KEY` | API, Worker | Observability |
| `CLERK_SECRET_KEY` | API | Authentication |
| `CLERK_PEM_PUBLIC_KEY` | API | JWT validation |
| `SQS_QUEUE_URL` | API, Worker | Job queue |
| `S3_CHROMADB_BUCKET` | Worker | RAG database |
| `BI_BEDROCK_REGION` | API | Bedrock region for BI copilot (us-east-1) |
| `BI_BEDROCK_MODEL_ID` | API | Bedrock model ID for BI copilot |

---

## Model Configuration

| Environment | Model | Config Location |
|-------------|-------|-----------------|
| AWS Production | `deepseek/deepseek-chat-v3.1` | Task definition JSON |
| Local Dev | `google/gemini-2.5-flash-lite` | `.env.local` |

**Switching models:**
```bash
# Edit task definitions
aws/terraform/task-definition-api-v19.json
aws/terraform/task-definition-worker-v21.json

# Redeploy
python aws/scripts/redeploy.py --api --worker
```

---

## MES Agentic BI Copilot (AWS Bedrock)

The BI data copilot PoC uses AWS Bedrock Converse API for natural language data filtering. It runs on the existing API service — no new ECS infrastructure is required.

### Model

| Setting | Value |
|---------|-------|
| Model ID | `us.anthropic.claude-3-5-sonnet-20241022-v2:0` |
| Inference type | US cross-region inference profile |
| Bedrock region | `us-east-1` (different from main app region `eu-west-2`) |
| Routes | `/bi/*` |
| Local compose file | `docker-compose.bi.yml` |

### IAM Permissions

The ECS task role for the API service must include the following Bedrock actions:

```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
}
```

### Model Access

Before the copilot can invoke the model, access must be enabled in the AWS Console:

1. Open **AWS Console** -> **Amazon Bedrock** -> **Model access** (ensure region is `us-east-1`)
2. Request access for **Claude 3.5 Sonnet v2** (`anthropic.claude-3-5-sonnet-20241022-v2:0`)
3. Wait for status to change to **Access granted**

### Credentials

| Environment | Auth method |
|-------------|-------------|
| Local dev | `~/.aws/credentials` (default profile, region `us-east-1`) |
| Production (ECS) | ECS task IAM role (no static credentials needed) |

### Environment Variables

| Variable | Example value | Description |
|----------|--------------|-------------|
| `BI_BEDROCK_REGION` | `us-east-1` | AWS region where Bedrock is called |
| `BI_BEDROCK_MODEL_ID` | `us.anthropic.claude-3-5-sonnet-20241022-v2:0` | Cross-region inference profile ID |

---

## Cost Estimate (Monthly)

| Component | Cost |
|-----------|------|
| ECS Fargate (3 services) | ~$75 |
| ALBs (2) | ~$30 |
| CloudFront | ~$10 |
| SQS | ~$0.50 |
| S3 | ~$2 |
| CloudWatch | ~$5 |
| **Total** | **~$120** |

---

## Recovery Procedures

### Quick Recovery (Task Definitions Only)

```bash
python aws/scripts/redeploy.py --wait
```

### Full Recovery (After Destroy)

```bash
# 1. Deploy infrastructure
python aws/scripts/deploy.py

# 2. Register task definitions
aws ecs register-task-definition --cli-input-json file://aws/terraform/task-definition-api-v19.json --region eu-west-2
aws ecs register-task-definition --cli-input-json file://aws/terraform/task-definition-worker-v21.json --region eu-west-2
aws ecs register-task-definition --cli-input-json file://aws/terraform/task-definition-frontend-v13.json --region eu-west-2

# 3. Force redeploy
python aws/scripts/redeploy.py --wait

# 4. Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id E1DTSJYZQGK50L --paths '/*'
```

### Preserved Resources

After `destroy.py`, these remain for quick redeploy:
- ECR repositories (3)
- S3: `pharma-test-gen-terraform-state`
- S3: `pharma-test-gen-chromadb-*`
- DynamoDB: `pharma-test-gen-terraform-locks`

---

## Directory Structure

```
aws/
├── terraform/
│   ├── main.tf                           # Core resources
│   ├── variables.tf
│   ├── outputs.tf
│   ├── environments/staging.tfvars
│   ├── modules/                          # ECR, ECS, ALB, CloudFront, SQS
│   ├── task-definition-api-v19.json      # Golden API config
│   ├── task-definition-worker-v21.json   # Golden Worker config
│   └── task-definition-frontend-v13.json # Golden Frontend config
├── scripts/
│   ├── deploy.py                         # Full deployment
│   ├── destroy.py                        # Teardown
│   └── redeploy.py                       # Quick updates
└── docs/
    └── AWS-ARCHITECTURE.md               # Detailed architecture
```
