# Terraform Provider Configuration
# Task 0.4 - AWS and TLS providers
# Note: Backend configuration is in backend.tf

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

# AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# TLS Provider (for GitHub OIDC certificate)
provider "tls" {}
