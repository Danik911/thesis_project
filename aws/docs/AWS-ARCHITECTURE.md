# AWS Infrastructure Architecture

Complete architecture documentation for the pharmaceutical test generation system AWS migration.

**Last Updated:** 2025-12-02 (CloudFront + Clerk authentication integration)
**Phase:** Phase 4 - AWS Deployment (Task 4.2 In Progress)
**Region:** eu-west-2 (London, UK)
**Account ID:** 275333454012

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Storage Infrastructure](#storage-infrastructure)
3. [Security & Compliance](#security--compliance)
4. [Logging & Monitoring](#logging--monitoring)
5. [IAM Roles & Policies](#iam-roles--policies)
6. [Network Architecture](#network-architecture)
7. [Cost Estimation](#cost-estimation)
8. [Compliance Mapping](#compliance-mapping)

---

## 🏗️ Architecture Overview

### Current State (Phase 4 - Task 4.2 In Progress)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       AWS Account: 275333454012                           │
│                          Region: eu-west-2                               │
│                   CloudFront: d2yiysdqio0ryi.cloudfront.net              │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                              HTTPS (TLS 1.2)
                                     │
                                     ▼
                         ┌─────────────────────┐
                         │     CloudFront      │
                         │   Distribution ID:  │
                         │   E3CO1HBNMIUKPB    │
                         └─────────┬───────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            │ /                    │ /jobs*, /api/*       │ /health*
            ▼                      ▼                      ▼
   ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
   │  Frontend ALB  │    │    API ALB     │    │    API ALB     │
   │  (HTTP origin) │    │  (HTTP origin) │    │  (HTTP origin) │
   └───────┬────────┘    └───────┬────────┘    └───────┬────────┘
           │                     │                     │
           ▼                     ▼                     ▼
   ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
   │  ECS Frontend  │    │   ECS API      │    │   ECS API      │
   │  (Task v9)     │    │  (Task v6)     │    │  (Task v6)     │
   │  Clerk Auth    │    │  Clerk JWT     │    │  Health Check  │
   └────────────────┘    └───────┬────────┘    └────────────────┘
                                 │
                                 │ SQS Queue
                                 ▼
                         ┌────────────────┐
                         │   ECS Worker   │
                         │   (Task v4)    │
                         │  ChromaDB RAG  │
                         │  (INCOMPLETE)  │
                         └────────────────┘
```

### Live Services Status

| Service | URL | Task Def | Status |
|---------|-----|----------|--------|
| CloudFront | https://d2yiysdqio0ryi.cloudfront.net | - | ✅ Deployed |
| Frontend | pharma-test-gen-frontend-alb-1050082060.eu-west-2.elb.amazonaws.com | v9 | ✅ Running |
| API | pharma-test-gen-api-alb-1013891260.eu-west-2.elb.amazonaws.com | v6 | ✅ Running |
| Worker | SQS polling | v4 | ⚠️ Missing config |

### Blocking Issues (Task 4.2)

The worker cannot complete test generation because:
1. **OpenRouter API key** - Not configured in worker environment
2. **S3 ChromaDB bucket** - Not created/uploaded (Task 4.2.3-4.2.4)
3. **LangFuse integration** - Not configured

### Foundation Services (Phase 0 Complete)

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  CloudTrail  │  │  AWS Config  │  │     KMS      │
│   (Active)   │  │   (Active)   │  │   Key: a8d2  │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ S3: pharma-  │  │ S3: pharma-  │  │ S3: pharma-  │
│ cloudtrail-  │  │ config-logs- │  │ test-output- │
│ logs-eu      │  │ eu           │  │ compliance   │
└──────────────┘  └──────────────┘  └──────────────┘

                 All encrypted at rest
                 All versioning enabled
                 All public access blocked
```

### Target State (Phase 4-5)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          AWS Infrastructure                              │
│                     Region: eu-west-2 (London, UK)                      │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │ CloudWatch   │  │ LangFuse     │  │ CloudTrail   │
         │ Logs +       │  │ Observability│  │ Audit Logs   │
         │ Metrics      │  │ Self-hosted  │  │              │
         └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 🗄️ Storage Infrastructure

### S3 Bucket Architecture

| Bucket Name | Purpose | Encryption | Versioning | Retention | Public Access |
|-------------|---------|------------|------------|-----------|---------------|
| **pharma-cloudtrail-logs-eu** | CloudTrail API call logs | AES256 + KMS | ✅ Enabled | 7 years (GAMP-5) | ❌ Blocked |
| **pharma-config-logs-eu** | AWS Config configuration snapshots | AES256 | ✅ Enabled | 7 years (GAMP-5) | ❌ Blocked |
| **pharma-test-output-compliance** | Application test generation outputs | AES256 | ✅ Enabled | 7 years (21 CFR Part 11) | ❌ Blocked |
| **pharma-tfstate-eu** | Terraform state files | AES256 | ✅ Enabled | Permanent | ❌ Blocked |

**Note:** Frontend originally planned for S3 static hosting (`pharma-frontend-eu`) but now deployed via **ECS Fargate** (containerized Next.js) to support API routes required by Task 2.3 (LangFuse observability dashboard). See "Compute" costs for frontend container pricing.

### Bucket Policies

#### CloudTrail Logs Bucket Policy
**File:** `aws/cloudtrail-logs-bucket-policy.json`

**Permissions:**
- `cloudtrail.amazonaws.com` → `s3:GetBucketAcl` (verify bucket exists)
- `cloudtrail.amazonaws.com` → `s3:PutObject` (write logs)
- Condition: `AWS:SourceArn` must match trail ARN
- Condition: `s3:x-amz-acl` must be `bucket-owner-full-control`

#### AWS Config Logs Bucket Policy
**File:** `aws/config-logs-bucket-policy.json`

**Permissions:**
- `config.amazonaws.com` → `s3:GetBucketAcl` (verify bucket exists)
- `config.amazonaws.com` → `s3:ListBucket` (check bucket contents)
- `config.amazonaws.com` → `s3:PutObject` (write configuration snapshots)
- Condition: `AWS:SourceAccount` must be `275333454012`

### Storage Costs (Estimated)

| Bucket | Avg Size/Month | S3 Standard Cost | Total/Month |
|--------|----------------|------------------|-------------|
| CloudTrail logs | ~10 GB | $0.023/GB | ~$0.23 |
| Config logs | ~5 GB | $0.023/GB | ~$0.12 |
| Test outputs | ~50 GB | $0.023/GB | ~$1.15 |
| **Total** | **~65 GB** | | **~$1.50/month** |

---

## 🔐 Security & Compliance

### KMS Key Configuration

**Key ID:** `a8d2df7b-1917-43c9-a89f-66e79c15623c`
**Key ARN:** `arn:aws:kms:eu-west-2:275333454012:key/a8d2df7b-1917-43c9-a89f-66e79c15623c`
**Alias:** (none - recommended to create: `alias/pharma-cloudtrail-key`)
**Key Rotation:** ✅ Enabled (automatic yearly rotation)
**Key Policy File:** `aws/kms-cloudtrail-policy.json`

**Key Usage:**
- CloudTrail log encryption
- S3 bucket encryption (for Terraform state - future)
- ECS task secrets encryption (future)

**Key Policy Principals:**
- `arn:aws:iam::275333454012:root` → Full KMS permissions
- `cloudtrail.amazonaws.com` → `kms:GenerateDataKey`, `kms:DescribeKey`
- Account users → `kms:Decrypt` (for reading CloudTrail logs)

### Encryption Standards

| Layer | Encryption Method | Key Management |
|-------|------------------|----------------|
| **At Rest (S3)** | AES-256 (SSE-S3) | AWS managed |
| **At Rest (CloudTrail)** | KMS (CMK) | Customer managed (a8d2df7b) |
| **In Transit** | TLS 1.2+ | AWS managed |
| **Database (Aurora)** | AES-256 | AWS managed (future) |
| **Secrets** | KMS | AWS Secrets Manager (future) |

### Public Access Controls

**All S3 buckets configured with:**
```json
{
  "BlockPublicAcls": true,
  "IgnorePublicAcls": true,
  "BlockPublicPolicy": true,
  "RestrictPublicBuckets": true
}
```

**VPC Security Groups (Future):**
- ECS tasks: No inbound from internet
- Aurora: Accessible only from ECS security group
- ALB: HTTPS only (port 443) + WAF Protected

### Network Security (New)
- **VPC Endpoints**: S3, ECR, Secrets Manager, CloudWatch (Keeps traffic private)
- **WAF (Web Application Firewall)**:
  - Rate limiting
  - SQL Injection protection
  - IP Reputation lists
- **Strict Egress**: ECS tasks only allowed outbound to specific AWS services and OpenRouter API.

---

## 📊 Logging & Monitoring

### CloudTrail Configuration

**Trail Name:** `pharma-trail`
**Trail ARN:** `arn:aws:cloudtrail:eu-west-2:275333454012:trail/pharma-trail`
**Status:** ✅ Active (logging since 2025-11-10 11:00:47 UTC)

**Configuration:**
- **Multi-region:** ✅ Yes (captures events from all regions)
- **Global services:** ✅ Yes (IAM, CloudFront, Route53)
- **Log file validation:** ✅ Enabled (SHA-256 hashing)
- **S3 bucket:** `pharma-cloudtrail-logs-eu`
- **KMS encryption:** ✅ Enabled (key: a8d2df7b)

**Events Captured:**
- All management events (API calls via AWS Console, CLI, SDKs)
- All data events (optional - not yet configured)
- All Insights events (optional - not yet configured)

**Log Delivery:**
- Delivered to: `s3://pharma-cloudtrail-logs-eu/AWSLogs/275333454012/CloudTrail/`
- Format: JSON (gzip compressed)
- Delivery frequency: Every ~5-15 minutes

### AWS Config (Planned)

**Status:** ⏸️ Not yet configured
**Target Configuration:**

**Configuration Recorder:**
- **Name:** `default`
- **Recording:** All supported resources
- **Include global resources:** ✅ Yes
- **Recording frequency:** Continuous

**Delivery Channel:**
- **S3 bucket:** `pharma-config-logs-eu`
- **SNS topic:** (optional) `pharma-config-notifications`
- **Delivery frequency:** Every 6 hours (snapshots)

**Configuration Rules (Future):**
- `encrypted-volumes` - All EBS volumes must be encrypted
- `s3-bucket-public-read-prohibited` - No public read access
- `s3-bucket-public-write-prohibited` - No public write access
- `cloudtrail-enabled` - CloudTrail must be active
- `iam-password-policy` - Strong password policy enforced
- `approved-amis-by-tag` - Only approved AMIs used

### CloudWatch (Future)

**Log Groups:**
- `/ecs/pharma-api` - API service logs
- `/ecs/pharma-worker` - Worker service logs
- `/aws/ecs/pharma-cluster` - ECS cluster events
- `/aws/lambda/pharma-*` - Lambda function logs (if any)

**Metrics & Alarms:**
- ECS CPU utilization > 80% (scaling trigger)
- ECS memory utilization > 80% (scaling trigger)
- Aurora connections > 90% (alert)
- SQS queue depth > 100 (scaling trigger)
- API 5xx errors > 10/5min (alert)

### LangFuse Observability (Future)

**Purpose:** Application-level tracing and observability
**Deployment:** Self-hosted on ECS Fargate
**Infrastructure:**
- 1 vCPU / 2 GB RAM
- Aurora PostgreSQL backend
- S3 for trace storage

**Monitoring:**
- LlamaIndex workflow traces (131 spans)
- Agent execution paths
- LLM token usage
- Latency per workflow step

---

## 🔑 IAM Roles & Policies

### Phase 0 IAM Policies

#### 1. PharmaPhase0DeploymentPolicy (Tasks 0.1-0.3)
**File:** `aws/iam-policies/phase0-deployment-policy.json`
**Attached to:** IAM user `aiengineer`

**Permissions:**
- Service Quotas (list, request increases)
- KMS (create keys, manage policies, enable rotation)
- CloudTrail (create trails, start/stop logging)
- AWS Config (create recorders, delivery channels)
- S3 (create buckets, manage policies, encryption)
- DynamoDB (create tables for Terraform locks)
- IAM (create roles for Config/CloudTrail)

#### 2. PharmaPhase0CompletePolicy (Tasks 0.1-0.4)
**File:** `aws/iam-policies/phase0-complete-policy.json`
**Attached to:** IAM user `aiengineer`

**Additional permissions beyond Phase0DeploymentPolicy:**
- ECR (create repositories, push images, get authorization)
- ECS (create clusters, task definitions, services)
- CloudWatch Logs (create log groups, streams)
- IAM (create service-linked roles for ECS)

**Total statements:** 12 (covers all Phase 0 tasks)

#### 3. PharmaTerraformBackendPolicy (Task 0.3)
**File:** `aws/iam-policies/terraform-backend-policy.json`
**Attached to:** IAM user `aiengineer`
**Policy ARN:** `arn:aws:iam::275333454012:policy/PharmaTerraformBackendPolicy`
**Status:** ✅ Active (2025-11-10)

**Permissions:**
- S3 bucket `pharma-tfstate-eu`: ListBucket, GetObject, PutObject, DeleteObject
- DynamoDB table `terraform-locks`: PutItem, GetItem, DeleteItem, DescribeTable

**Purpose:** Allows Terraform to store state in S3 and manage state locking via DynamoDB

### DynamoDB Tables

#### terraform-locks (Task 0.3)
**Purpose:** Terraform state locking
**Region:** eu-west-2
**ARN:** `arn:aws:dynamodb:eu-west-2:275333454012:table/terraform-locks`
**Status:** ✅ ACTIVE (2025-11-10)
**Billing mode:** PAY_PER_REQUEST
**Key schema:** LockID (String, HASH)

**Used by:** Terraform backend to prevent concurrent state modifications

### IAM Roles (Task 0.4)

#### 1. pharma-test-gen-ecs-execution
**Purpose:** ECS task execution (pull images, write logs)
**ARN:** `arn:aws:iam::275333454012:role/pharma-test-gen-ecs-execution`
**Status:** ✅ Active (2025-11-10)
**Trust policy:** `ecs-tasks.amazonaws.com`
**Managed by:** Terraform

**Permissions:**
- ECR: Pull images, get authorization token
- Secrets Manager: Read secrets (`pharma-test-gen/*`)
- CloudWatch Logs: Create streams, write logs
- SSM Parameter Store: Read parameters (`pharma-test-gen/*`)
- AWS managed policy: `AmazonECSTaskExecutionRolePolicy`

#### 2. pharma-test-gen-ecs-task
**Purpose:** Application runtime (Bedrock, S3, SQS access)
**ARN:** `arn:aws:iam::275333454012:role/pharma-test-gen-ecs-task`
**Status:** ✅ Active (2025-11-10)
**Trust policy:** `ecs-tasks.amazonaws.com`
**Managed by:** Terraform

**Permissions:**
- S3: Read/write `pharma-test-output-compliance` bucket
- SQS: Send/receive/delete messages in `pharma-test-gen*` queues
- Bedrock: Invoke `deepseek-ai.DeepSeek-V3` model only
- Secrets Manager: Read `pharma-test-gen/*` secrets
- CloudWatch: Put custom metrics (namespace: `pharma-test-gen`)
- CloudWatch Logs: Create log groups/streams, write logs

#### 3. pharma-test-gen-deploy
**Purpose:** CI/CD deployment (GitHub Actions)
**ARN:** `arn:aws:iam::275333454012:role/pharma-test-gen-deploy`
**Status:** ✅ Active (2025-11-10)
**Trust policy:** GitHub OIDC (`Danik911/thesis_project:main`)
**Managed by:** Terraform

**Permissions:**
- ECR: Full access (push/pull images, manage repositories)
- ECS: Deploy services, update task definitions (frontend, API, worker)
- IAM: PassRole to ECS execution and task roles
- Secrets Manager: Create/update `pharma-test-gen/*` secrets
- CloudWatch Logs: View deployment logs

**Note:** Frontend now deployed via ECS Fargate (containerized Next.js with API routes), not S3 static hosting.

### GitHub OIDC Provider (Task 0.4)

**ARN:** `arn:aws:iam::275333454012:oidc-provider/token.actions.githubusercontent.com`
**Status:** ✅ Active (2025-11-10)
**Purpose:** Allow GitHub Actions to assume AWS roles without long-lived credentials
**Trusted repository:** `Danik911/thesis_project`
**Trusted branch:** `main`

### ECR Repositories (Task 0.4)

#### pharma-test-gen-backend
**Purpose:** FastAPI backend container images
**URL:** `275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-backend`
**ARN:** `arn:aws:ecr:eu-west-2:275333454012:repository/pharma-test-gen-backend`
**Status:** ✅ Active (2025-11-10)
**Image scanning:** Enabled (scan on push)
**Encryption:** AES256
**Lifecycle policy:** Keep last 10 images

#### pharma-test-gen-worker
**Purpose:** LlamaIndex workflow worker container images
**URL:** `275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-worker`
**ARN:** `arn:aws:ecr:eu-west-2:275333454012:repository/pharma-test-gen-worker`
**Status:** ✅ Active (2025-11-10)
**Image scanning:** Enabled (scan on push)
**Encryption:** AES256
**Lifecycle policy:** Keep last 10 images

#### pharma-test-gen-frontend (Task 2.3)
**Purpose:** Next.js frontend with API routes container images
**URL:** `275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-frontend`
**ARN:** `arn:aws:ecr:eu-west-2:275333454012:repository/pharma-test-gen-frontend` (future)
**Status:** ⏸️ Planned (required for Task 4.1 deployment)
**Image scanning:** Enabled (scan on push)
**Encryption:** AES256
**Lifecycle policy:** Keep last 10 images

**Note:** Frontend now requires containerization due to Next.js API routes (Task 2.3 LangFuse integration)

---

## 🌐 Network Architecture

### Current (Phase 0)
No VPC resources yet - using AWS global services only.

### Future (Phase 4-5)

```
┌─────────────────────────────────────────────────────────────┐
│                    VPC: pharma-vpc-eu                        │
│                  CIDR: 10.0.0.0/16                          │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Public       │  │ Private      │  │ Private      │
│ Subnet A     │  │ App Subnet A │  │ DB Subnet A  │
│ 10.0.1.0/24  │  │ 10.0.11.0/24 │  │ 10.0.21.0/24 │
│              │  │              │  │              │
│ - ALB        │  │ - ECS Tasks  │  │ - Aurora     │
│ - NAT GW     │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Public       │  │ Private      │  │ Private      │
│ Subnet B     │  │ App Subnet B │  │ DB Subnet B  │
│ 10.0.2.0/24  │  │ 10.0.12.0/24 │  │ 10.0.22.0/24 │
│              │  │              │  │              │
│ - NAT GW     │  │ - ECS Tasks  │  │ - Aurora     │
│              │  │              │  │   (standby)  │
└──────────────┘  └──────────────┘  └──────────────┘
```

**Security Groups:**
- `pharma-alb-sg` - Inbound HTTPS (443) from internet
- `pharma-ecs-sg` - Inbound from ALB only
- `pharma-aurora-sg` - Inbound PostgreSQL (5432) from ECS SG only

**Network ACLs:**
- Default allow (no custom NACLs initially)

**VPC Endpoints (cost optimization):**
- S3 (Gateway endpoint - free)
- ECR (Interface endpoint - $7.50/month)
- CloudWatch Logs (Interface endpoint - $7.50/month)
- Secrets Manager (Interface endpoint - $7.50/month)

---

## 💰 Cost Estimation

### Phase 0 (Current) - Monthly Costs

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| S3 Storage | ~65 GB (logs + outputs) | $1.50 |
| S3 Requests | ~1M PUT, 10M GET | $0.50 |
| CloudTrail | 1 trail, all events | $2.00 (first trail free) |
| KMS | 1 CMK, ~10K API calls | $1.00 + $0.03 |
| Data Transfer | Minimal (logs only) | $0.10 |
| **Total (Phase 0)** | | **~$5.13/month** |

### Production (Phase 4-5) - Monthly Costs

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| **Compute** | | |
| ECS Fargate (Frontend) | 1 task × 1vCPU × 2GB × 24h (Task 2.3) | $40 |
| ECS Fargate (API) | 2 tasks × 2vCPU × 4GB × 24h | $150 |
| ECS Fargate (Worker) | 2 tasks × 4vCPU × 8GB × 12h avg | $250 |
| LangFuse | 1 task × 1vCPU × 2GB × 24h | $50 |
| **Database** | | |
| Aurora Serverless v2 | 0.5-2 ACU, PostgreSQL 15 | $150 |
| **Storage** | | |
| S3 (all buckets) | ~200 GB | $5 |
| S3 Vectors | 500K embeddings (1536 dims) | $15 |
| **LLM** | | |
| Bedrock (DeepSeek-V3.1) | 50 docs/day × 30 days | $70 |
| **Networking** | | |
| Application Load Balancer | 2 AZs, ~1M requests | $25 |
| CloudFront | 10 GB transfer | $1 |
| Data Transfer Out | ~50 GB | $4.50 |
| **Monitoring** | | |
| CloudWatch Logs | 10 GB ingestion | $5 |
| CloudWatch Metrics | Custom metrics | $3 |
| LangFuse Storage | S3 traces | $2 |
| **Queue & Secrets** | | |
| SQS | 10M requests | $4 |
| Secrets Manager | 5 secrets | $2.50 |
| **Security** | | |
| AWS WAF | Web ACL + Rules | $20 |
| VPC Endpoints | 4 Interfaces (S3 Gateway free) | $30 |
| **Total (Production)** | | **~$827/month** |

**Note:** Frontend cost increased by $40/month (ECS Fargate vs S3 static hosting) due to Task 2.3 requirement for API routes.
**Security Additions:** WAF and VPC Endpoints added for GAMP-5 compliance (+$50/month).

**With optimizations (Fargate Spot, caching, Dev Pausing):** ~$500-600/month

---

## 🛠️ Terraform Implementation Strategy

### Modular Structure
To ensure maintainability and compliance, the Terraform codebase will be modularized:

```
terraform/
├── main.tf            # Root configuration (calls modules)
├── variables.tf       # Global variables
├── outputs.tf         # Root outputs
├── backend.tf         # S3 backend configuration
├── modules/
│   ├── networking/    # VPC, Subnets, Endpoints, Security Groups
│   ├── compute/       # ECS Cluster, Fargate Services, ALB, WAF
│   ├── database/      # Aurora Serverless, Secrets Manager
│   ├── storage/       # S3 Buckets, ECR Repositories
│   └── compliance/    # CloudTrail, Config, KMS, IAM Roles
└── envs/
    ├── dev/           # Development environment variables
    └── prod/          # Production environment variables
```

### Deployment Pipeline
1. **Build**: Docker Build → Trivy Scan → ECR Push (Immutable Tag)
2. **Plan**: Terraform Plan (against new Tag)
3. **Approve**: Manual Gate (GAMP-5 Requirement)
4. **Apply**: Terraform Apply


## 📋 Compliance Mapping

### GAMP-5 Software Categorization

**System Classification:** Category 5 (Custom Application)
**Validation Required:** IQ, OQ, PQ

### ALCOA+ Data Integrity Principles

| Principle | Implementation |
|-----------|----------------|
| **Attributable** | CloudTrail captures all user actions |
| **Legible** | Logs stored in JSON format (readable) |
| **Contemporaneous** | CloudTrail logs events in real-time |
| **Original** | S3 versioning preserves original records |
| **Accurate** | Log file validation (SHA-256 hash) |
| **Complete** | Multi-region trail captures all events |
| **Consistent** | Standardized log format |
| **Enduring** | 7-year retention, immutable with Object Lock |
| **Available** | S3 versioning + cross-region replication |

### 21 CFR Part 11 (Electronic Records)

| Requirement | Implementation |
|-------------|----------------|
| **§11.10(a) Validation** | GAMP-5 validation (IQ/OQ/PQ) |
| **§11.10(b) Audit Trail** | CloudTrail + AWS Config |
| **§11.10(c) System Checks** | ECS health checks, CloudWatch alarms |
| **§11.10(e) Audit Trail** | Log file validation, KMS encryption |
| **§11.10(k) Change Control** | Terraform IaC, Git version control |
| **§11.30 Controls** | IAM, MFA, least privilege access |
| **§11.50 Signature** | Clerk authentication (EU endpoints) |
| **§11.100 Archive** | S3 7-year retention |

### EU Data Residency (GDPR)

**Region:** eu-west-2 (London, UK)
**Data Processing Agreement:** AWS GDPR DPA
**Clerk Auth:** EU endpoints configured
**Data Transfer:** No cross-border transfer outside EU

---

## 🔄 Disaster Recovery & Business Continuity

### Backup Strategy

| Resource | Backup Method | Frequency | Retention |
|----------|--------------|-----------|-----------|
| **S3 Buckets** | Versioning enabled | Continuous | 7 years |
| **Aurora DB** | Automated backups | Daily | 35 days |
| **Aurora DB** | Manual snapshots | Weekly | 7 years |
| **ECS Config** | Terraform state | On change | Permanent |
| **IAM Policies** | Git version control | On change | Permanent |

### Recovery Objectives

**RTO (Recovery Time Objective):** 4 hours
**RPO (Recovery Point Objective):** 1 hour

**Recovery Procedures:**
1. **S3 Bucket Loss:** Restore from versioned objects
2. **Aurora Failure:** Automatic failover to standby (2-3 minutes)
3. **Region Failure:** Manual failover to eu-west-1 (not yet configured)
4. **Complete Account Loss:** Restore from Terraform state + manual backups

---

## 📖 Reference Documentation

### Files in aws/ Directory

| File | Purpose |
|------|---------|
| `cloudtrail-logs-bucket-policy.json` | S3 policy for CloudTrail logs bucket |
| `config-logs-bucket-policy.json` | S3 policy for AWS Config logs bucket |
| `kms-cloudtrail-policy.json` | KMS key policy for CloudTrail encryption |
| `iam-policies/phase0-deployment-policy.json` | IAM policy for Tasks 0.1-0.3 |
| `iam-policies/phase0-complete-policy.json` | IAM policy for Tasks 0.1-0.4 |
| `iam-policies/terraform-backend-policy.json` | IAM policy for Terraform backend (Task 0.3) |
| `iam-policies/attach-phase0-policy.sh` | Script to attach Phase 0 policy |
| `iam-policies/attach-phase0-complete-policy.sh` | Script to attach complete policy |
| `iam-policies/verify-phase0-permissions.sh` | Verify Phase 0 permissions |
| `iam-policies/verify-phase0-complete-permissions.sh` | Verify complete permissions |
| `scripts/setup-separate-buckets.sh` | Script to create separate log buckets |
| `scripts/attach-terraform-backend-policy.sh` | Attach Terraform backend IAM policy |
| `scripts/create-terraform-infrastructure.sh` | Create S3 bucket and DynamoDB table for Terraform |
| `scripts/setup-terraform-backend.sh` | Install Terraform and initialize backend |
| `scripts/complete-task-0.3-terraform-backend.sh` | Master script for Task 0.3 |
| `scripts/setup-aws-config.sh` | Setup AWS Config recorder (Task 0.2) |
| `docs/TASK-0.4-IAM-ROLES-GUIDE.md` | Guide for Task 0.4 IAM roles |
| `terraform/backend.tf` | Terraform S3 backend configuration |
| `AWS-ARCHITECTURE.md` | This file |

### External References

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [GAMP 5 Guide](https://ispe.org/publications/guidance-documents/gamp-5)
- [21 CFR Part 11 Guidelines](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application)
- [AWS GDPR Center](https://aws.amazon.com/compliance/gdpr-center/)
- [CloudTrail Documentation](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html)
- [AWS Config Documentation](https://docs.aws.amazon.com/config/latest/developerguide/WhatIsConfig.html)

---

## 📞 Support & Contacts

**AWS Account Owner:** [Your Name]
**AWS Account ID:** 275333454012
**Primary Region:** eu-west-2 (London)
**Backup Region:** eu-west-1 (Ireland) - future

**Key Personnel:**
- Infrastructure Lead: [Name]
- Security Lead: [Name]
- Compliance Lead: [Name]

---

**Document Version:** 1.2
**Last Review:** 2025-12-02
**Next Review:** 2025-12-09 (weekly during Phase 4)
**Status:** Phase 4 In Progress (Task 4.2)
**Changelog:**
- 2025-12-02: Added CloudFront distribution (E3CO1HBNMIUKPB), updated live service URLs, documented blocking issues for worker
- 2025-11-11: Updated frontend deployment from S3 static hosting to ECS Fargate (Task 2.3)
