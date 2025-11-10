# Terraform Variable Values
# Task 0.4 - Configuration values for Phase 0

# AWS Configuration
aws_region     = "eu-west-2"
aws_account_id = "275333454012"

# Project Configuration
project_name = "pharma-test-gen"
environment  = "prod"

# GitHub Configuration
github_org    = "Danik911"
github_repo   = "thesis_project"
github_branch = "main"

# S3 Buckets (existing)
s3_buckets = {
  cloudtrail_logs = "pharma-cloudtrail-logs-eu"
  config_logs     = "pharma-config-logs-eu"
  compliance      = "pharma-test-output-compliance"
  tfstate         = "pharma-tfstate-eu"
  frontend        = "pharma-frontend-eu" # Will be created in Phase 2
}

# Bedrock Model
bedrock_model_id = "deepseek-ai.DeepSeek-V3"

# Tags
tags = {
  Project     = "Pharmaceutical Test Generation"
  ManagedBy   = "Terraform"
  Compliance  = "GAMP-5"
  Environment = "Production"
  Region      = "eu-west-2"
  Owner       = "Danik911"
}
