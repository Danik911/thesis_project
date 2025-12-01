# AWS Deployment Scripts

This directory contains deployment automation scripts for the Pharmaceutical Test Generation system.

## Folder Structure

```
aws/
├── scripts/                    # Active deployment scripts (this folder)
│   ├── deploy.py              # Deploy to AWS
│   ├── destroy.py             # Tear down AWS
│   ├── run_local.py           # Run local Docker stack
│   └── README.md              # This file
├── terraform/                  # Infrastructure as Code
│   ├── main.tf                # Main Terraform config
│   ├── variables.tf           # Input variables
│   ├── outputs.tf             # Output values
│   ├── backend.tf             # S3 backend config
│   ├── modules/               # Reusable Terraform modules
│   │   ├── alb/              # Application Load Balancer
│   │   ├── ecr/              # Container Registry
│   │   ├── ecs-cluster/      # ECS Cluster
│   │   ├── ecs-service/      # ECS Service + Task Definition
│   │   └── sqs/              # SQS Queues
│   └── environments/          # Environment-specific vars
│       ├── staging.tfvars
│       └── production.tfvars
├── iam-policies/              # IAM policy definitions (JSON)
├── docs/                      # AWS documentation
│   └── AWS-ARCHITECTURE.md    # Architecture overview
└── archive/                   # Deprecated/utility scripts
    ├── legacy/               # Old shell scripts (pre-Python)
    └── utils/                # One-time troubleshooting scripts
```

## Scripts Overview

| Script | Purpose | Environment |
|--------|---------|-------------|
| `deploy.py` | Deploy to AWS ECS/Fargate | AWS Production/Staging |
| `destroy.py` | Tear down AWS infrastructure | AWS Production/Staging |
| `run_local.py` | Run local development stack | Local Docker |

## Prerequisites

### For AWS Deployment (`deploy.py`, `destroy.py`)

1. **AWS CLI** - Configured with appropriate credentials
   ```bash
   aws configure
   ```

2. **Terraform** - Version 1.9+ (installed in WSL2 at ~/bin/terraform)
   ```bash
   terraform --version
   ```

3. **Docker** - Running in WSL2
   ```bash
   docker info
   ```

4. **IAM Permissions** - User/role must have Phase0CompletePolicy attached with:
   - ECR (create/push images)
   - ECS (manage clusters, services, tasks)
   - EC2 (VPC, subnets, security groups, ALB)
   - SQS (create queues)
   - CloudWatch (logs)
   - IAM (create roles/policies)
   - S3 (create buckets)
   - Application Auto Scaling

### For Local Development (`run_local.py`)

1. **Docker** with Docker Compose v2
2. **Environment file** `.env.local` with required API keys

## Usage

### Deploy to AWS

```bash
# From project root
python aws/scripts/deploy.py

# Or with uv
uv run aws/scripts/deploy.py
```

The script will:
1. Check prerequisites (Docker, Terraform, AWS CLI)
2. Authenticate with Amazon ECR
3. Create ECR repositories if they don't exist
4. Build Docker images for linux/amd64 (Fargate requirement)
5. Push images to ECR with staging tags
6. Run Terraform plan and apply
7. Wait for ECS services to be healthy
8. Display deployment URLs and cost information

**Estimated time:** 15-25 minutes

### Destroy AWS Infrastructure

```bash
# From project root
python aws/scripts/destroy.py

# Or with uv
uv run aws/scripts/destroy.py
```

The script will:
1. Display detailed warning and ask for confirmation
2. Empty S3 buckets (vectors and output)
3. Scale down ECS services to 0
4. Run Terraform destroy
5. Optionally delete ECR images
6. Clean up local Terraform artifacts

**Preserved resources** (for quick re-deployment):
- S3 bucket: `pharma-test-gen-terraform-state` (~$0.02/month)
- DynamoDB table: `pharma-test-gen-terraform-locks` (~$0.00/month)
- ECR repositories (unless you choose to delete images)

### Run Local Development

```bash
# From project root
python aws/scripts/run_local.py

# Or with uv
uv run aws/scripts/run_local.py
```

The script will:
1. Check Docker and Docker Compose installation
2. Validate `.env.local` exists
3. Validate `docker-compose.dev.yml` syntax
4. Build and start all services
5. Wait for services to be healthy
6. Display service URLs

**Services started:**
- PostgreSQL (port 5432) - Database with pgvector
- LocalStack (port 4566) - AWS SQS mock
- API (port 8080) - FastAPI application
- Worker - Background job processor
- Frontend (port 3000) - Next.js UI

## Environment Files

### `.env.local` (Required for both local and AWS)

```env
# LLM (via OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-...

# Authentication (Clerk)
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...

# Observability (LangFuse)
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### `.env.development` (Optional - local overrides)

```env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

## Deployed Infrastructure

### Current Deployment (Staging)

| Resource | Value |
|----------|-------|
| ECS Cluster | `pharma-test-gen-cluster` |
| API ALB | `pharma-test-gen-api-alb-954886868.eu-west-2.elb.amazonaws.com` |
| Frontend ALB | `pharma-test-gen-frontend-alb-1431187418.eu-west-2.elb.amazonaws.com` |
| SQS Queue | `pharma-test-gen-worker-jobs` |
| Region | `eu-west-2` (London) |

### ECR Repositories

```
275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-api
275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-frontend
275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-worker
```

## Cost Information

### AWS Resources (when deployed)

| Resource | Estimated Cost |
|----------|---------------|
| ECS Fargate (3 tasks) | ~$0.12/hour |
| Application Load Balancers (2) | ~$0.04/hour |
| CloudWatch Logs | Pay per GB |
| SQS Queue | Minimal |
| **Total** | **~$0.50-1.00/hour** |

### Preserved Resources (after destroy)

| Resource | Monthly Cost |
|----------|-------------|
| S3 Terraform State | ~$0.02 |
| DynamoDB Lock Table | ~$0.00 |
| ECR Repositories | Free (storage only) |
| **Total** | **~$0.10/month** |

## Troubleshooting

### Docker Build Failures

```bash
# Check Docker is running
docker info

# Clear Docker build cache
docker builder prune -a

# Rebuild with no cache
docker compose -f docker-compose.dev.yml build --no-cache
```

### Terraform State Issues

```bash
# Run from WSL2
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform
export PATH=$HOME/bin:$PATH

# Unlock state if locked
terraform force-unlock -force <LOCK_ID>

# Refresh state
terraform refresh -var-file=environments/staging.tfvars

# Import missing resource (example: autoscaling target)
terraform import -var-file=environments/staging.tfvars \
  'module.ecs_worker.aws_appautoscaling_target.this[0]' \
  'ecs/service/pharma-test-gen-cluster/pharma-test-gen-worker/ecs:service:DesiredCount'
```

### ECS Service Not Starting

```bash
# Check service events
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api \
  --query 'services[0].events[0:5]' \
  --region eu-west-2

# Check task logs
aws logs tail /ecs/pharma-test-gen/api --follow --region eu-west-2

# Check service status
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api pharma-test-gen-frontend pharma-test-gen-worker \
  --query "services[*].{name:serviceName,status:status,running:runningCount,desired:desiredCount}" \
  --output table \
  --region eu-west-2
```

### Local Stack Issues

```bash
# View all container logs
docker compose -f docker-compose.dev.yml logs -f

# Restart specific service
docker compose -f docker-compose.dev.yml restart api

# Reset all data
docker compose -f docker-compose.dev.yml down --volumes
docker compose -f docker-compose.dev.yml up -d
```

## Archive Folder

The `../archive/` folder contains deprecated and utility scripts:

### `archive/legacy/` - Old Shell Scripts
Shell scripts from before migration to Python. Kept for reference:
- `setup-terraform-backend.sh` - Original backend setup
- `verify-*.sh` - Permission verification scripts
- `attach-*.sh` - IAM policy attachment scripts

### `archive/utils/` - Troubleshooting Utilities
One-time scripts used during deployment troubleshooting:
- `cleanup_and_apply.py` - Clean failed resources and re-apply
- `delete_ecr.py` - Delete ECR repositories
- `delete_target_groups.py` - Delete ALB target groups
- `import_*.py` - Import existing resources into Terraform state
- `finish_deploy.py` - Complete interrupted deployments

## GAMP-5 Compliance Notes

- All deployments tracked via Terraform state with full audit trail
- ECR images use IMMUTABLE tags for reproducibility
- CloudWatch logs retained per compliance requirements
- ECS deployment circuit breaker with automatic rollback (no fallback logic)
- Container Insights enabled for observability

## Related Documentation

- [AWS Architecture](../docs/AWS-ARCHITECTURE.md) - Detailed architecture overview
- [AWS Migration PRP](../../PRPs/aws-migration-updated.md) - Complete migration plan
- [Terraform Variables](../terraform/variables.tf) - All configurable parameters
- [Docker Compose](../../docker-compose.dev.yml) - Local development stack
- [IAM Policies](../iam-policies/) - IAM policy JSON definitions
