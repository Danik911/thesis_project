# Common AWS Architectures with Cost Estimates

## Overview

Reference patterns for common deployment scenarios with cost estimates
for both prototype and production configurations. All costs are estimates
based on December 2025 pricing in eu-west-2 (London) region.

---

## Pattern 1: Simple API

**Use case:** Single API service with database

### Architecture
```
Internet → ALB → ECS Fargate (API) → RDS PostgreSQL
```

### Components
| Component | Service | Config |
|-----------|---------|--------|
| Load Balancer | ALB | 1 instance |
| Compute | ECS Fargate | 1 task |
| Database | RDS PostgreSQL | t3.micro |
| Storage | S3 | Output files |

### Cost Estimate

**Prototype (minimal):**
| Component | Hourly | Monthly |
|-----------|--------|---------|
| ALB | $0.02 | $16 |
| Fargate (0.5 vCPU) | $0.02 | $15 |
| RDS t3.micro | $0.02 | $15 |
| S3 (5 GB) | - | $0.12 |
| **TOTAL** | **$0.06** | **~$46** |

**Production (recommended):**
| Component | Hourly | Monthly |
|-----------|--------|---------|
| ALB | $0.02 | $16 |
| Fargate (2x 1 vCPU) | $0.08 | $58 |
| RDS t3.small Multi-AZ | $0.08 | $58 |
| S3 (50 GB) | - | $1.15 |
| **TOTAL** | **$0.18** | **~$133** |

---

## Pattern 2: API + Worker Queue

**Use case:** API with background job processing

### Architecture
```
Internet → ALB → ECS (API) → SQS → ECS (Worker)
                    ↓                    ↓
                   RDS ←←←←←←←←←←←←←←←←←←
```

### Components
| Component | Service | Config |
|-----------|---------|--------|
| Load Balancer | ALB | 1 instance |
| API | ECS Fargate | 1-2 tasks |
| Queue | SQS | Standard queue |
| Worker | ECS Fargate | 1-2 tasks |
| Database | RDS PostgreSQL | t3.micro/small |

### Cost Estimate

**Prototype:**
| Component | Hourly | Monthly |
|-----------|--------|---------|
| ALB | $0.02 | $16 |
| API Fargate (0.5 vCPU) | $0.02 | $15 |
| Worker Fargate (0.5 vCPU) | $0.02 | $15 |
| SQS | - | $0.40 (1M requests) |
| RDS t3.micro | $0.02 | $15 |
| **TOTAL** | **$0.08** | **~$61** |

**Production:**
| Component | Hourly | Monthly |
|-----------|--------|---------|
| ALB | $0.02 | $16 |
| API Fargate (2x 1 vCPU) | $0.08 | $58 |
| Worker Fargate (2x 1 vCPU) | $0.08 | $58 |
| SQS + DLQ | - | $1 |
| RDS t3.small Multi-AZ | $0.08 | $58 |
| **TOTAL** | **$0.26** | **~$191** |

---

## Pattern 3: Full Stack (This Project)

**Use case:** API + Worker + Frontend with queue

### Architecture
```
Internet → ALB (Frontend) → ECS (Next.js)
         ↓
Internet → ALB (API) → ECS (FastAPI) → SQS → ECS (Worker)
                           ↓                     ↓
                          RDS ←←←←←←←←←←←←←←←←←←
                           ↓
                          S3 (output files)
```

### Components
| Component | Service | Config |
|-----------|---------|--------|
| Frontend LB | ALB | 1 instance |
| API LB | ALB | 1 instance |
| Frontend | ECS Fargate | 1 task |
| API | ECS Fargate | 1-2 tasks |
| Worker | ECS Fargate | 1-2 tasks |
| Queue | SQS | Standard + DLQ |
| Database | RDS/Aurora | PostgreSQL |
| Storage | S3 | Output files |
| Registry | ECR | 3 repositories |

### Cost Estimate

**Prototype (this project):**
| Component | Hourly | Monthly |
|-----------|--------|---------|
| ALB x2 | $0.04 | $32 |
| Frontend (0.5 vCPU) | $0.02 | $15 |
| API (0.5 vCPU) | $0.02 | $15 |
| Worker (1 vCPU) | $0.04 | $29 |
| SQS | - | $0.40 |
| RDS t3.micro | $0.02 | $15 |
| S3 (10 GB) | - | $0.23 |
| ECR | - | $1 |
| CloudWatch | - | $3 |
| **TOTAL** | **$0.14** | **~$111** |

**Production:**
| Component | Hourly | Monthly |
|-----------|--------|---------|
| ALB x2 | $0.04 | $32 |
| Frontend (2x 1 vCPU) | $0.08 | $58 |
| API (2x 2 vCPU) | $0.16 | $116 |
| Worker (2x 2 vCPU) | $0.16 | $116 |
| SQS + DLQ | - | $2 |
| Aurora Serverless | $0.12 | $87 |
| S3 (100 GB) | - | $2.30 |
| ECR | - | $5 |
| CloudWatch | - | $15 |
| WAF | - | $10 |
| **TOTAL** | **$0.56** | **~$443** |

---

## Pattern 4: Static Website

**Use case:** Static frontend with CDN

### Architecture
```
Internet → CloudFront → S3 (static files)
```

### Components
| Component | Service | Config |
|-----------|---------|--------|
| CDN | CloudFront | Distribution |
| Storage | S3 | Static hosting |
| DNS | Route 53 | Optional |

### Cost Estimate

**Prototype:**
| Component | Hourly | Monthly |
|-----------|--------|---------|
| S3 (1 GB) | - | $0.02 |
| CloudFront (10 GB transfer) | - | $0.85 |
| **TOTAL** | **~$0** | **~$1** |

**Production:**
| Component | Hourly | Monthly |
|-----------|--------|---------|
| S3 (10 GB) | - | $0.23 |
| CloudFront (100 GB transfer) | - | $8.50 |
| Route 53 | - | $0.50 |
| ACM Certificate | - | Free |
| **TOTAL** | **~$0** | **~$9** |

---

## Pattern 5: Serverless API

**Use case:** Event-driven, variable traffic

### Architecture
```
Internet → API Gateway → Lambda → DynamoDB
```

### Components
| Component | Service | Config |
|-----------|---------|--------|
| API | API Gateway | REST/HTTP |
| Compute | Lambda | Pay per request |
| Database | DynamoDB | On-demand |

### Cost Estimate

**Prototype (low traffic):**
| Component | Hourly | Monthly |
|-----------|--------|---------|
| API Gateway | - | $3.50 (1M requests) |
| Lambda | - | Free tier (1M) |
| DynamoDB | - | $1.25 (1GB, 1M reads) |
| **TOTAL** | **~$0** | **~$5** |

**Note:** Serverless can be cheaper for variable/low traffic,
but more expensive than Fargate for consistent high traffic.

---

## Cost Saving Decision Tree

```
Is traffic consistent (>1 request/second)?
├── YES → Use ECS Fargate
│         └── Cheaper than Lambda at scale
└── NO → Use Lambda
         └── Pay only when running

Need persistent connections/WebSockets?
├── YES → Use ECS Fargate
│         └── Lambda has 15-min timeout
└── NO → Either works

Budget under $50/month?
├── YES → Lambda + DynamoDB
│         └── Most cost-effective
└── NO → ECS Fargate + RDS
         └── More flexibility
```

---

## Regional Price Differences

Prices vary by region. eu-west-2 (London) costs:

| Service | vs us-east-1 |
|---------|--------------|
| ECS Fargate | +10% |
| RDS | +10% |
| S3 | +5% |
| Data Transfer | Same |

**Recommendation:** Stay in eu-west-2 for EU data residency compliance.
The ~10% premium is worth it for GDPR compliance.
