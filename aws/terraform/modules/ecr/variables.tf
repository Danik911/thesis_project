# =============================================================================
# ECR Module Variables
# =============================================================================

variable "project_name" {
  description = "Project name prefix for ECR repositories"
  type        = string
}

variable "environment" {
  description = "Deployment environment (staging, production)"
  type        = string
}

variable "repositories" {
  description = "Map of repository names to create"
  type        = map(string)
  default = {
    api      = "FastAPI backend service"
    worker   = "Background job processor"
    frontend = "Next.js frontend application"
  }
}

variable "keep_tagged_images" {
  description = "Number of tagged images to keep (production)"
  type        = number
  default     = 30
}

variable "untagged_expiry_days" {
  description = "Days before untagged images expire"
  type        = number
  default     = 7
}

variable "staging_expiry_days" {
  description = "Days before staging/dev images expire"
  type        = number
  default     = 14
}

variable "cross_account_principals" {
  description = "List of AWS account ARNs for cross-account access (optional)"
  type        = list(string)
  default     = null
}
