# =============================================================================
# Production Environment Configuration
# =============================================================================
# GAMP-5 Compliance: Production environment with full compliance requirements
# Task 4.1: ECS & Fargate Deployment Infrastructure
#
# Usage: terraform apply -var-file=environments/production.tfvars
#
# IMPORTANT: Review all values before applying to production!

# -----------------------------------------------------------------------------
# General Configuration
# -----------------------------------------------------------------------------

environment  = "production"
project_name = "pharma-test-gen"
aws_region   = "eu-west-2"  # London (GDPR compliance)

# -----------------------------------------------------------------------------
# Networking (REQUIRED - Update with your production VPC/Subnet IDs)
# -----------------------------------------------------------------------------

# vpc_id = "vpc-xxxxxxxxxxxxxxxxx"
# private_subnet_ids = ["subnet-xxxxxxxxxxxxxxxxx", "subnet-yyyyyyyyyyyyyyyyy", "subnet-zzzzzzzzzzzzzzzzz"]
# public_subnet_ids  = ["subnet-aaaaaaaaaaaaaaaa", "subnet-bbbbbbbbbbbbbbbb", "subnet-cccccccccccccccc"]

# -----------------------------------------------------------------------------
# Aurora Database (REQUIRED - From Task 4.2)
# -----------------------------------------------------------------------------

# aurora_cluster_arn   = "arn:aws:rds:eu-west-2:ACCOUNT_ID:cluster:pharma-test-gen-aurora-prod"
# aurora_secret_arn    = "arn:aws:secretsmanager:eu-west-2:ACCOUNT_ID:secret:pharma-test-gen/aurora-prod-XXXXXX"
# aurora_database_name = "pharma_test_gen"

# -----------------------------------------------------------------------------
# S3 Buckets (REQUIRED)
# -----------------------------------------------------------------------------

# vector_bucket = "pharma-test-gen-vectors-prod"
# output_bucket = "pharma-test-gen-output-prod"

# -----------------------------------------------------------------------------
# Bedrock Configuration
# -----------------------------------------------------------------------------

bedrock_region   = "us-east-1"
bedrock_model_id = "deepseek.deepseek-v3-0324"

# -----------------------------------------------------------------------------
# SSL Certificate (REQUIRED for HTTPS)
# -----------------------------------------------------------------------------

# acm_certificate_arn = "arn:aws:acm:eu-west-2:ACCOUNT_ID:certificate/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# -----------------------------------------------------------------------------
# Container Image Tags
# -----------------------------------------------------------------------------

# IMPORTANT: Use semantic versioning for production (NEVER 'latest')
# Example: v1.2.3 or prod-20251130-123456
api_image_tag      = "v1.0.0"
worker_image_tag   = "v1.0.0"
frontend_image_tag = "v1.0.0"

# -----------------------------------------------------------------------------
# API Service Configuration (Full production sizing)
# -----------------------------------------------------------------------------

api_cpu           = 2048   # 2 vCPU
api_memory        = 4096   # 4 GB
api_desired_count = 2      # High availability
api_min_capacity  = 2      # Never go below 2 for HA
api_max_capacity  = 10

# -----------------------------------------------------------------------------
# Worker Service Configuration (Full production sizing)
# -----------------------------------------------------------------------------

worker_cpu                      = 4096   # 4 vCPU (LLM inference)
worker_memory                   = 8192   # 8 GB
worker_desired_count            = 1      # Start with 1, scale on demand
worker_min_capacity             = 1
worker_max_capacity             = 20
worker_visibility_timeout       = 900    # 15 minutes
worker_target_messages_per_task = 5      # Scale when queue depth > 5 per task

# -----------------------------------------------------------------------------
# Frontend Service Configuration (Full production sizing)
# -----------------------------------------------------------------------------

frontend_cpu           = 512    # 0.5 vCPU
frontend_memory        = 1024   # 1 GB
frontend_desired_count = 2      # High availability
frontend_min_capacity  = 2      # Never go below 2 for HA
frontend_max_capacity  = 10

# -----------------------------------------------------------------------------
# Auto Scaling Configuration (Production-optimized)
# -----------------------------------------------------------------------------

cpu_target_utilization    = 70   # Target 70% CPU utilization
memory_target_utilization = 80   # Target 80% memory utilization
scale_in_cooldown         = 300  # 5 min cooldown before scale in
scale_out_cooldown        = 60   # 1 min cooldown before scale out (fast response)

# -----------------------------------------------------------------------------
# CloudWatch Configuration (GAMP-5 Compliance)
# -----------------------------------------------------------------------------

# 7-year retention for pharmaceutical compliance (2555 days = 7 years)
log_retention_days = 2555

# -----------------------------------------------------------------------------
# Feature Flags (Production hardening)
# -----------------------------------------------------------------------------

enable_deletion_protection = true  # PREVENT accidental deletion
enable_container_insights  = true  # REQUIRED for GAMP-5 audit trail

# -----------------------------------------------------------------------------
# Alerting (REQUIRED for production)
# -----------------------------------------------------------------------------

# sns_alarm_topic_arn = "arn:aws:sns:eu-west-2:ACCOUNT_ID:pharma-test-gen-alerts"
