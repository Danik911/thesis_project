# Terraform Outputs
# Task 0.4 - Export role ARNs and resource details

# ============================================
# IAM Role ARNs
# ============================================

output "deploy_role_arn" {
  description = "ARN of the GitHub Actions deployment role"
  value       = aws_iam_role.deploy.arn
}

output "deploy_role_name" {
  description = "Name of the GitHub Actions deployment role"
  value       = aws_iam_role.deploy.name
}

output "ecs_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_execution.arn
}

output "ecs_execution_role_name" {
  description = "Name of the ECS task execution role"
  value       = aws_iam_role.ecs_execution.name
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task runtime role"
  value       = aws_iam_role.ecs_task.arn
}

output "ecs_task_role_name" {
  description = "Name of the ECS task runtime role"
  value       = aws_iam_role.ecs_task.name
}

# ============================================
# OIDC Provider
# ============================================

output "github_oidc_provider_arn" {
  description = "ARN of the GitHub OIDC provider"
  value       = aws_iam_openid_connect_provider.github.arn
}

# ============================================
# ECR Repositories
# ============================================

output "ecr_backend_repository_url" {
  description = "URL of the backend ECR repository"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_backend_repository_arn" {
  description = "ARN of the backend ECR repository"
  value       = aws_ecr_repository.backend.arn
}

output "ecr_worker_repository_url" {
  description = "URL of the worker ECR repository"
  value       = aws_ecr_repository.worker.repository_url
}

output "ecr_worker_repository_arn" {
  description = "ARN of the worker ECR repository"
  value       = aws_ecr_repository.worker.arn
}

# ============================================
# GitHub Actions Configuration
# ============================================

output "github_actions_role_arn" {
  description = "Role ARN to use in GitHub Actions workflow (add to repo secrets as AWS_ROLE_ARN)"
  value       = aws_iam_role.deploy.arn
}

output "github_actions_config" {
  description = "GitHub Actions workflow configuration"
  value = {
    aws_region      = var.aws_region
    role_arn        = aws_iam_role.deploy.arn
    ecr_backend_url = aws_ecr_repository.backend.repository_url
    ecr_worker_url  = aws_ecr_repository.worker.repository_url
  }
}
