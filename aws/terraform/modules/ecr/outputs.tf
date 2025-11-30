# =============================================================================
# ECR Module Outputs
# =============================================================================

output "repository_urls" {
  description = "Map of repository names to URLs"
  value       = { for k, v in aws_ecr_repository.this : k => v.repository_url }
}

output "repository_arns" {
  description = "Map of repository names to ARNs"
  value       = { for k, v in aws_ecr_repository.this : k => v.arn }
}

output "repository_names" {
  description = "Map of repository keys to full names"
  value       = { for k, v in aws_ecr_repository.this : k => v.name }
}

output "registry_id" {
  description = "ECR registry ID (AWS account ID)"
  value       = values(aws_ecr_repository.this)[0].registry_id
}
