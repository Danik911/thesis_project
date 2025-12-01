# AWS Deployment Guide

## Overview

This directory contains Terraform infrastructure and scripts for deploying the pharmaceutical test generation system to AWS.

## Architecture

```
ECS Worker → S3 (download on startup) → In-memory ChromaDB → RAG retrieval
```

### Key Components

| Component | Resource | Purpose |
|-----------|----------|---------|
| Worker | ECS Fargate (4 vCPU, 8GB) | Process test generation jobs |
| ChromaDB Storage | S3 Bucket | Store ChromaDB tarball (~2MB) |
| Job Queue | SQS + DLQ | Async job processing |
| LLM | Bedrock (DeepSeek-V3.1) | Test case generation |

### ChromaDB RAG (Task 4.2)

The Context Provider Agent uses ChromaDB for regulatory document retrieval:

1. **S3 Storage**: Compressed ChromaDB tarball in S3 bucket
2. **Worker Startup**: Downloads and extracts to `/app/chroma_db`
3. **In-Process Query**: ChromaDB runs embedded in worker (<10ms latency)

**Cost**: ~$0.02/month (S3 storage only)

## Directory Structure

```
aws/
├── terraform/                  # Infrastructure as Code
│   ├── main.tf                # Core resources (ECS, S3, IAM, SQS)
│   ├── variables.tf           # Input variables
│   ├── outputs.tf             # Output values
│   └── modules/               # Reusable modules
│       ├── ecr/               # Container registry
│       ├── ecs-cluster/       # ECS cluster
│       ├── ecs-service/       # ECS services
│       ├── alb/               # Load balancers
│       └── sqs/               # Job queue
├── scripts/
│   ├── 1_upload_chroma_to_s3.py  # Upload ChromaDB to S3
│   ├── deploy.py                 # Deployment automation
│   ├── destroy.py                # Teardown automation
│   ├── import_ecr.sh             # Import existing ECR repos
│   └── run_local.py              # Local development
└── README.md                     # This file
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
- SQS Queue + Dead Letter Queue
- IAM Roles with least-privilege permissions

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
| ECS Fargate Worker (1 task) | ~$50 |
| S3 ChromaDB Storage (2MB) | $0.02 |
| SQS Queue | $0.50 |
| Bedrock (1000 invocations) | ~$50 |
| CloudWatch Logs | $5 |
| **Total** | **~$105/month** |

## Security

- **IAM Roles**: Least-privilege permissions
- **S3 Encryption**: AES-256 server-side
- **VPC**: Private subnets for ECS tasks
- **Secrets Manager**: API keys and credentials
- **Public Access Blocked**: S3 buckets

## Troubleshooting

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

## Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)
