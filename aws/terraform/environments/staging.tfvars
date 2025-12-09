# =============================================================================
# Staging Environment Configuration
# =============================================================================
# GAMP-5 Compliance: Staging environment for testing before production
# Task 4.1: ECS & Fargate Deployment Infrastructure
#
# Usage: terraform apply -var-file=environments/staging.tfvars

# -----------------------------------------------------------------------------
# General Configuration
# -----------------------------------------------------------------------------

environment  = "staging"
project_name = "pharma-test-gen"
aws_region   = "eu-west-2"

# Domain configuration (required for Route53 module)
domain_name        = "csvgeneration.com"
create_hosted_zone = false  # Using existing Route53 hosted zone

# -----------------------------------------------------------------------------
# Networking (Updated with actual VPC/Subnet IDs)
# -----------------------------------------------------------------------------

vpc_id = "vpc-07de5cd5ef4073ad4"

# Using default VPC subnets (all public) for staging
# For production, create private subnets with NAT Gateway
private_subnet_ids = ["subnet-0809d351e731b6c9d", "subnet-05a62658586e5cbaa", "subnet-04c12c181726055dc"]
public_subnet_ids  = ["subnet-0809d351e731b6c9d", "subnet-05a62658586e5cbaa", "subnet-04c12c181726055dc"]

# Assign public IP to tasks (required for staging with public subnets and no NAT)
assign_public_ip = true

# -----------------------------------------------------------------------------
# Aurora Database (SKIPPED for initial testing - saves ~$3/hour)
# Set to placeholder values - ECS will start but won't connect to database
# Complete Task 4.2 to deploy real Aurora cluster
# -----------------------------------------------------------------------------

aurora_cluster_arn   = "arn:aws:rds:eu-west-2:275333454012:cluster:placeholder"
aurora_secret_arn    = "arn:aws:secretsmanager:eu-west-2:275333454012:secret:pharma-test-gen/database-url-dDBDUm"
aurora_database_name = "pharma_test_gen"

# -----------------------------------------------------------------------------
# S3 Buckets (Created with versioning enabled)
# -----------------------------------------------------------------------------

output_bucket = "pharma-test-gen-output-staging"

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

# Use semantic versioning for staging deployments
api_image_tag      = "staging-latest"
worker_image_tag   = "staging-latest"
frontend_image_tag = "staging-latest"

# -----------------------------------------------------------------------------
# API Service Configuration (Reduced for staging)
# -----------------------------------------------------------------------------

api_cpu           = 1024   # 1 vCPU (half of production)
api_memory        = 2048   # 2 GB
api_desired_count = 1      # Single instance for staging
api_min_capacity  = 1
api_max_capacity  = 3

# -----------------------------------------------------------------------------
# Worker Service Configuration (Reduced for staging)
# -----------------------------------------------------------------------------

worker_cpu           = 2048  # 2 vCPU (half of production)
worker_memory        = 4096  # 4 GB
worker_desired_count = 1
worker_min_capacity  = 1
worker_max_capacity  = 5

# -----------------------------------------------------------------------------
# Frontend Service Configuration (Reduced for staging)
# -----------------------------------------------------------------------------

frontend_cpu           = 256   # 0.25 vCPU (half of production)
frontend_memory        = 512   # 0.5 GB
frontend_desired_count = 1
frontend_min_capacity  = 1
frontend_max_capacity  = 3

# -----------------------------------------------------------------------------
# Auto Scaling (More aggressive for staging testing)
# -----------------------------------------------------------------------------

cpu_target_utilization    = 60  # Lower threshold for easier testing
memory_target_utilization = 70
scale_in_cooldown         = 60   # Faster scale-in for testing
scale_out_cooldown        = 30   # Faster scale-out for testing

# -----------------------------------------------------------------------------
# CloudWatch Configuration
# -----------------------------------------------------------------------------

log_retention_days = 7  # Short retention for staging

# -----------------------------------------------------------------------------
# Feature Flags
# -----------------------------------------------------------------------------

enable_deletion_protection = false  # Allow deletion in staging
enable_container_insights  = true   # Keep insights for debugging

# -----------------------------------------------------------------------------
# Alerting (Optional)
# -----------------------------------------------------------------------------

# sns_alarm_topic_arn = ""  # No alerting for staging
