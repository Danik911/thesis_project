# =============================================================================
# Terraform Version and Provider Requirements
# =============================================================================
# GAMP-5 Compliance: Pin provider versions to prevent unexpected diffs
# Task 4.1: ECS & Fargate Deployment Infrastructure

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      # Pin to ~> 5.0 (NOT >= 5.0) to prevent major version upgrades
      # This ensures reproducible infrastructure builds (GAMP-5 requirement)
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "pharmaceutical-test-generation"
      Environment = var.environment
      ManagedBy   = "terraform"
      GAMP5       = "true"
    }
  }
}
