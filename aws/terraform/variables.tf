# =============================================================================
# Input Variables for ECS Fargate Infrastructure
# =============================================================================
# GAMP-5 Compliance: All critical values are parameterized (no hardcoding)
# Task 4.1: ECS & Fargate Deployment Infrastructure
#
# IMPORTANT: Variables without defaults are REQUIRED and must be provided
# via tfvars file or -var flags. This ensures NO FALLBACK LOGIC.

# -----------------------------------------------------------------------------
# General Configuration
# -----------------------------------------------------------------------------

variable "aws_region" {
  description = "AWS region for resources (eu-west-2 for GDPR compliance)"
  type        = string
  default     = "eu-west-2"
}

variable "environment" {
  description = "Deployment environment (staging, production)"
  type        = string

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be 'staging' or 'production'."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "pharma-test-gen"
}

# -----------------------------------------------------------------------------
# VPC and Networking
# -----------------------------------------------------------------------------

variable "vpc_id" {
  description = "VPC ID for ECS deployment (REQUIRED - no fallback)"
  type        = string
  # NO DEFAULT - must be explicitly provided
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS tasks (REQUIRED)"
  type        = list(string)
  # NO DEFAULT - must be explicitly provided
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for ALB (REQUIRED)"
  type        = list(string)
  # NO DEFAULT - must be explicitly provided
}

variable "assign_public_ip" {
  description = "Assign public IP to ECS tasks (required for public subnets without NAT Gateway)"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Database Configuration (RDS PostgreSQL)
# -----------------------------------------------------------------------------
# Note: aurora_* variables are DEPRECATED - RDS PostgreSQL module is now used
# These remain for backwards compatibility but are no longer required

variable "aurora_cluster_arn" {
  description = "DEPRECATED: ARN of Aurora Serverless v2 cluster (no longer used)"
  type        = string
  default     = ""  # No longer required - RDS module used instead
}

variable "aurora_secret_arn" {
  description = "DEPRECATED: ARN of Secrets Manager secret for Aurora (no longer used)"
  type        = string
  default     = ""  # No longer required - RDS module creates its own secret
}

variable "aurora_database_name" {
  description = "DEPRECATED: Aurora database name (no longer used)"
  type        = string
  default     = "pharma_test_gen"
}

# -----------------------------------------------------------------------------
# S3 Buckets
# -----------------------------------------------------------------------------

# ChromaDB bucket is created automatically in main.tf (Task 4.2)
# Named: ${project_name}-chromadb-${account_id}

variable "output_bucket" {
  description = "S3 bucket for test suite output storage (REQUIRED)"
  type        = string
  # NO DEFAULT - must be explicitly provided
}

# -----------------------------------------------------------------------------
# Bedrock Configuration
# -----------------------------------------------------------------------------

variable "bedrock_region" {
  description = "AWS region for Bedrock (may differ from main region)"
  type        = string
  default     = "us-east-1"  # DeepSeek V3 availability
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for LLM inference"
  type        = string
  default     = "deepseek.deepseek-v3-0324"
}

variable "llm_model" {
  description = "LLM model ID for test generation via OpenRouter (e.g., google/gemini-2.5-flash-lite, deepseek/deepseek-chat-v3.1)"
  type        = string
  default     = "google/gemini-2.5-flash-lite"
}

# -----------------------------------------------------------------------------
# SSL/TLS Configuration
# -----------------------------------------------------------------------------

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS (REQUIRED for production, empty for HTTP-only staging)"
  type        = string
  default     = ""  # Empty for HTTP-only staging; MUST be set for production
}

# -----------------------------------------------------------------------------
# Container Image Tags
# -----------------------------------------------------------------------------

variable "api_image_tag" {
  description = "Docker image tag for API service"
  type        = string
  default     = "latest"
  # WARNING: Use semantic versioning (v1.2.3) for production, not 'latest'
}

variable "worker_image_tag" {
  description = "Docker image tag for Worker service"
  type        = string
  default     = "latest"
  # WARNING: Use semantic versioning (v1.2.3) for production, not 'latest'
}

variable "frontend_image_tag" {
  description = "Docker image tag for Frontend service"
  type        = string
  default     = "latest"
  # WARNING: Use semantic versioning (v1.2.3) for production, not 'latest'
}

# -----------------------------------------------------------------------------
# API Service Configuration (FastAPI)
# -----------------------------------------------------------------------------

variable "api_cpu" {
  description = "CPU units for API task (1024 = 1 vCPU)"
  type        = number
  default     = 2048  # 2 vCPU
}

variable "api_memory" {
  description = "Memory in MB for API task"
  type        = number
  default     = 4096  # 4 GB
}

variable "api_desired_count" {
  description = "Initial desired count for API service"
  type        = number
  default     = 2
}

variable "api_min_capacity" {
  description = "Minimum number of API tasks (auto scaling)"
  type        = number
  default     = 2
}

variable "api_max_capacity" {
  description = "Maximum number of API tasks (auto scaling)"
  type        = number
  default     = 10
}

variable "api_port" {
  description = "Container port for API service"
  type        = number
  default     = 8080
}

variable "api_health_check_path" {
  description = "Health check endpoint for API service"
  type        = string
  default     = "/health"
}

# -----------------------------------------------------------------------------
# Worker Service Configuration (Background Processor)
# -----------------------------------------------------------------------------

variable "worker_cpu" {
  description = "CPU units for Worker task (1024 = 1 vCPU)"
  type        = number
  default     = 4096  # 4 vCPU (LLM inference needs more compute)
}

variable "worker_memory" {
  description = "Memory in MB for Worker task"
  type        = number
  default     = 8192  # 8 GB
}

variable "worker_desired_count" {
  description = "Initial desired count for Worker service"
  type        = number
  default     = 1
}

variable "worker_min_capacity" {
  description = "Minimum number of Worker tasks (auto scaling)"
  type        = number
  default     = 1
}

variable "worker_max_capacity" {
  description = "Maximum number of Worker tasks (auto scaling)"
  type        = number
  default     = 20
}

variable "worker_visibility_timeout" {
  description = "SQS visibility timeout in seconds (should exceed worker processing time)"
  type        = number
  default     = 900  # 15 minutes
}

variable "worker_target_messages_per_task" {
  description = "Target number of SQS messages per worker task (for auto scaling)"
  type        = number
  default     = 5
}

# -----------------------------------------------------------------------------
# Frontend Service Configuration (Next.js)
# -----------------------------------------------------------------------------

variable "frontend_cpu" {
  description = "CPU units for Frontend task (1024 = 1 vCPU)"
  type        = number
  default     = 512  # 0.5 vCPU
}

variable "frontend_memory" {
  description = "Memory in MB for Frontend task"
  type        = number
  default     = 1024  # 1 GB
}

variable "frontend_desired_count" {
  description = "Initial desired count for Frontend service"
  type        = number
  default     = 2
}

variable "frontend_min_capacity" {
  description = "Minimum number of Frontend tasks (auto scaling)"
  type        = number
  default     = 2
}

variable "frontend_max_capacity" {
  description = "Maximum number of Frontend tasks (auto scaling)"
  type        = number
  default     = 10
}

variable "frontend_port" {
  description = "Container port for Frontend service"
  type        = number
  default     = 3000
}

variable "frontend_health_check_path" {
  description = "Health check endpoint for Frontend service"
  type        = string
  default     = "/api/health"
}

# -----------------------------------------------------------------------------
# Auto Scaling Configuration
# -----------------------------------------------------------------------------

variable "cpu_target_utilization" {
  description = "Target CPU utilization percentage for auto scaling"
  type        = number
  default     = 70
}

variable "memory_target_utilization" {
  description = "Target memory utilization percentage for auto scaling"
  type        = number
  default     = 80
}

variable "scale_in_cooldown" {
  description = "Cooldown period in seconds before scaling in"
  type        = number
  default     = 300  # 5 minutes
}

variable "scale_out_cooldown" {
  description = "Cooldown period in seconds before scaling out"
  type        = number
  default     = 60  # 1 minute (fast response)
}

# -----------------------------------------------------------------------------
# CloudWatch Log Configuration
# -----------------------------------------------------------------------------

variable "log_retention_days" {
  description = "CloudWatch log retention in days (2555 for 7-year GAMP-5 compliance)"
  type        = number
  default     = 7  # Use 2555 for production compliance
}

# -----------------------------------------------------------------------------
# SNS Alerting (Optional)
# -----------------------------------------------------------------------------

variable "sns_alarm_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarms (optional)"
  type        = string
  default     = ""
}

# -----------------------------------------------------------------------------
# Feature Flags
# -----------------------------------------------------------------------------

variable "enable_deletion_protection" {
  description = "Enable deletion protection for ALBs (recommended for production)"
  type        = bool
  default     = false  # Override to true in production.tfvars
}

variable "enable_container_insights" {
  description = "Enable Container Insights for ECS cluster (GAMP-5 requirement)"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# Route 53 DNS Configuration
# -----------------------------------------------------------------------------

variable "domain_name" {
  description = "Domain name (e.g., csvgeneration.com)"
  type        = string
  default     = ""
}

variable "create_hosted_zone" {
  description = "Create new Route 53 hosted zone (false = use existing)"
  type        = bool
  default     = true
}

variable "api_subdomain" {
  description = "API subdomain (e.g., api)"
  type        = string
  default     = "api"
}

variable "frontend_subdomain" {
  description = "Frontend subdomain (e.g., app or www)"
  type        = string
  default     = "app"
}

variable "create_root_record" {
  description = "Create root domain record pointing to frontend"
  type        = bool
  default     = true
}
