# Terraform Variables for Phase 0 IAM Roles
# Task 0.4 - Create Baseline IAM Roles and Policies

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-west-2"
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
  default     = "275333454012"
}

variable "project_name" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "pharma-test-gen"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "github_org" {
  description = "GitHub organization or username"
  type        = string
  default     = "Danik911"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "thesis_project"
}

variable "github_branch" {
  description = "GitHub branch for deployments"
  type        = string
  default     = "main"
}

# S3 Buckets
variable "s3_buckets" {
  description = "S3 buckets used by the application"
  type = object({
    cloudtrail_logs = string
    config_logs     = string
    compliance      = string
    tfstate         = string
    frontend        = string
  })
  default = {
    cloudtrail_logs = "pharma-cloudtrail-logs-eu"
    config_logs     = "pharma-config-logs-eu"
    compliance      = "pharma-test-output-compliance"
    tfstate         = "pharma-tfstate-eu"
    frontend        = "pharma-frontend-eu"
  }
}

# Bedrock Configuration
variable "bedrock_model_id" {
  description = "Bedrock model ID to restrict access to"
  type        = string
  default     = "deepseek-ai.DeepSeek-V3"
}

# Tags
variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "Pharmaceutical Test Generation"
    ManagedBy   = "Terraform"
    Compliance  = "GAMP-5"
    Environment = "Production"
    Region      = "eu-west-2"
  }
}
