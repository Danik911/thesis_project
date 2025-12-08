# =============================================================================
# ECR Repository Module
# =============================================================================
# GAMP-5 Compliance:
# - MUTABLE tags for staging (allows staging-latest overwrites)
# - Timestamp tags (staging-YYYYMMDD-HHMMSS) provide audit trail
# - Scan on push for security vulnerability detection
# - Lifecycle policies for compliance-aware image management
# NOTE: Production should use IMMUTABLE tags

# Create ECR repositories for each service
resource "aws_ecr_repository" "this" {
  for_each = var.repositories

  name                 = "${var.project_name}-${each.key}"
  image_tag_mutability = "MUTABLE"  # Staging: Allow staging-latest overwrites (timestamp tags provide audit trail)

  # Encryption configuration
  encryption_configuration {
    encryption_type = "AES256"  # Use KMS for enhanced security if required
  }

  # Security scanning on push
  image_scanning_configuration {
    scan_on_push = true
  }

  # Force deletion only in non-production (GAMP-5 data retention)
  force_delete = var.environment != "production"

  tags = {
    Service = each.key
    GAMP5   = "true"
  }

  lifecycle {
    # Prevent accidental deletion of ECR repositories (images are valuable)
    # Remove from state with `terraform state rm` if intentional deletion needed
    prevent_destroy = true
  }
}

# Lifecycle policies to manage image retention
resource "aws_ecr_lifecycle_policy" "this" {
  for_each = var.repositories

  repository = aws_ecr_repository.this[each.key].name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last ${var.keep_tagged_images} production images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v", "prod-", "release-"]
          countType     = "imageCountMoreThan"
          countNumber   = var.keep_tagged_images
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Expire untagged images after ${var.untagged_expiry_days} days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = var.untagged_expiry_days
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 3
        description  = "Keep staging images for ${var.staging_expiry_days} days"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["staging-", "dev-", "test-"]
          countType     = "sinceImagePushed"
          countUnit     = "days"
          countNumber   = var.staging_expiry_days
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# Repository policy for cross-account access (if needed)
resource "aws_ecr_repository_policy" "this" {
  for_each = var.cross_account_principals != null ? var.repositories : {}

  repository = aws_ecr_repository.this[each.key].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCrossAccountPull"
        Effect    = "Allow"
        Principal = {
          AWS = var.cross_account_principals
        }
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability"
        ]
      }
    ]
  })
}
