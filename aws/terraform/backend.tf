# =============================================================================
# Terraform Backend Configuration
# =============================================================================
# GAMP-5 Compliance: State stored in S3 with versioning and encryption
# Task 4.1: ECS & Fargate Deployment Infrastructure
#
# Prerequisites:
# - S3 bucket created in Task 0.3
# - DynamoDB table for state locking
#
# IMPORTANT: Backend configuration cannot use variables.
# Update the bucket name if your account ID differs.

terraform {
  backend "s3" {
    # S3 bucket for state storage (created in Task 0.3)
    bucket = "pharma-test-gen-terraform-state"

    # Unique key for this infrastructure component
    key = "ecs/terraform.tfstate"

    # Region for the S3 bucket
    region = "eu-west-2"

    # Server-side encryption (GAMP-5 requirement)
    encrypt = true

    # DynamoDB table for state locking (prevents concurrent modifications)
    dynamodb_table = "pharma-test-gen-terraform-locks"

    # Enable versioning for audit trail (ALCOA+ compliance)
    # Note: Versioning is configured on the S3 bucket, not here
  }
}
