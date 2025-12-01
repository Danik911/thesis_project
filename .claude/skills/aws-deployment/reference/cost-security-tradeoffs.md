# Cost vs Security Tradeoffs for Prototypes

## Overview

This guide helps make informed decisions about cost vs security for
**prototype/learning/portfolio** projects. Production deployments require
different considerations.

---

## Decision Framework

### Question 1: What's the purpose?

| Purpose | Cost Priority | Security Priority |
|---------|---------------|-------------------|
| Learning AWS | HIGH | LOW |
| Portfolio demo | HIGH | MEDIUM |
| MVP testing | MEDIUM | MEDIUM |
| Client prototype | MEDIUM | HIGH |
| Production | LOW | HIGH |

### Question 2: What data is involved?

| Data Type | Security Requirement |
|-----------|---------------------|
| Test data only | Minimal |
| Personal data (dev) | Basic encryption |
| PII/PHI | Full compliance |
| Financial | Full compliance |

---

## What to Skip for Prototypes

### Safe to Skip (Save Money)

| Feature | Production Cost | Prototype Alternative |
|---------|----------------|----------------------|
| Multi-AZ RDS | ~$200/month extra | Single AZ |
| NAT Gateway | ~$32/month | Use public subnets |
| WAF | ~$5/month + rules | Skip entirely |
| CloudTrail | ~$2/month | Skip or minimal |
| S3 Object Lock | Compliance cost | Standard S3 |
| Reserved capacity | Upfront cost | On-demand only |
| Private endpoints | ~$7/endpoint/month | Public endpoints |

### NEVER Skip (Even for Prototypes)

| Feature | Why Essential |
|---------|--------------|
| VPC isolation | Prevents accidental exposure |
| Security groups | Basic firewall protection |
| IAM least privilege | Limits blast radius |
| HTTPS (if public) | Prevents credential theft |
| Encryption at rest | AWS default, free |
| Private ECR | Don't expose container images |

---

## Cost Comparison: Prototype vs Production

### Simple API (FastAPI + Database)

| Component | Prototype | Production |
|-----------|-----------|------------|
| Compute | 1x Fargate 0.5 vCPU | 2x Fargate 2 vCPU |
| Database | RDS t3.micro single-AZ | Aurora Serverless Multi-AZ |
| Load Balancer | 1 ALB | 1 ALB + WAF |
| Networking | Public subnets | Private + NAT Gateway |
| **Monthly Cost** | **~$50** | **~$400** |

### Container Orchestration (ECS)

| Component | Prototype | Production |
|-----------|-----------|------------|
| Tasks | 1-2 per service | 2-4 per service |
| vCPU | 0.25-0.5 per task | 1-2 per task |
| Memory | 0.5-1 GB | 2-4 GB |
| Auto-scaling | Disabled | Enabled |
| **Monthly Cost** | **~$30** | **~$200** |

### Full Stack (API + Worker + Frontend + DB)

| Component | Prototype | Production |
|-----------|-----------|------------|
| ECS Fargate | 3 tasks minimal | 6+ tasks |
| RDS/Aurora | t3.micro | r6g.large |
| ALB | 1 shared | 2 separate |
| S3 | Standard | Standard + replication |
| SQS | Standard | Standard + DLQ |
| CloudWatch | Basic | Enhanced + alarms |
| **Monthly Cost** | **~$100** | **~$800** |

---

## Security Minimums by Project Type

### Learning Project
- [x] VPC with public subnets
- [x] Security groups (restrictive)
- [x] IAM roles (least privilege)
- [ ] HTTPS (optional for local testing)
- [ ] WAF
- [ ] Private subnets

### Portfolio Demo
- [x] VPC with public subnets
- [x] Security groups (restrictive)
- [x] IAM roles (least privilege)
- [x] HTTPS (free with ACM)
- [ ] WAF
- [ ] Private subnets

### MVP/Client Prototype
- [x] VPC with public/private subnets
- [x] Security groups (restrictive)
- [x] IAM roles (least privilege)
- [x] HTTPS required
- [x] Basic WAF rules
- [ ] Full compliance

---

## Free Tier Optimization

### Always Use Free Tier When Available

| Service | Free Tier | When It Ends |
|---------|-----------|--------------|
| EC2 t2.micro | 750 hrs/month | 12 months |
| RDS t2.micro | 750 hrs/month | 12 months |
| S3 | 5 GB storage | Never |
| Lambda | 1M requests/month | Never |
| CloudWatch | 10 custom metrics | Never |
| SQS | 1M requests/month | Never |

### Fargate Has NO Free Tier
Fargate charges from minute one:
- 0.25 vCPU = ~$0.01/hour
- 0.5 vCPU = ~$0.02/hour
- 1 vCPU = ~$0.04/hour

**For pure learning:** Consider EC2 with free tier instead

---

## Cost Saving Tips for Prototypes

### 1. Destroy When Not Using
```bash
# End of day
python aws/scripts/destroy.py

# Next morning
python aws/scripts/deploy.py
```
**Savings:** ~70% if only running 8 hours/day

### 2. Use Minimal Task Sizes
```hcl
# Prototype
cpu    = 256   # 0.25 vCPU
memory = 512   # 0.5 GB

# Production
cpu    = 1024  # 1 vCPU
memory = 2048  # 2 GB
```

### 3. Single Tasks Only
```hcl
# Prototype
desired_count = 1

# Production
desired_count = 2  # minimum for HA
```

### 4. Skip NAT Gateway
```hcl
# Prototype - use public subnets only
# Save ~$32/month

# Production - use private subnets with NAT
```

### 5. Use Spot Instances (EC2 only)
```hcl
# Up to 90% savings
# But can be interrupted
```

---

## When to Upgrade Security

**Upgrade from prototype security when:**
1. Handling real user data (not test data)
2. Going live to actual users
3. Storing credentials or secrets
4. Processing payments
5. Regulatory requirements apply

**Signs you need production security:**
- "Can I share this URL with my team?"
- "Users are signing up"
- "We're processing real orders"
- "Compliance audit coming"

---

## Security Scanning with Checkov (AWS CCAPI MCP)

Validate infrastructure security before deployment using built-in Checkov scanning.

### Security Scan Workflow

```
# 1. Generate CloudFormation code
code_token = mcp__aws-ccapi-mcp__generate_infrastructure_code(
  resource_type="AWS::ECS::Service",
  properties={...},
  credentials_token="..."
)

# 2. Explain the generated code (show to user)
explained = mcp__aws-ccapi-mcp__explain(generated_code_token=code_token)

# 3. Run Checkov security scan
scan_result = mcp__aws-ccapi-mcp__run_checkov(explained_token=explained.token)
```

### Handling Security Findings

| Finding Severity | Prototype Response | Production Response |
|------------------|-------------------|---------------------|
| CRITICAL | Review, may block | Must fix before deploy |
| HIGH | Review, user decision | Should fix |
| MEDIUM | Accept with note | Review |
| LOW | Accept | Accept |

### Common Checkov Findings

| Finding | Prototype Action | Production Action |
|---------|-----------------|-------------------|
| Public S3 bucket | Accept for demo data | Block - never allow |
| No encryption at rest | Accept | Require KMS encryption |
| Overly permissive SG | Accept with justification | Restrict to minimum |
| No logging enabled | Skip for cost | Enable CloudTrail/CloudWatch |
| No backup configured | Skip | Enable automated backups |
