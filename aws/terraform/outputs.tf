# =============================================================================
# Output Values
# =============================================================================
# GAMP-5 Compliance: Export all necessary values for audit and integration
# Task 4.1: ECS & Fargate Deployment Infrastructure

# -----------------------------------------------------------------------------
# ECR Repositories
# -----------------------------------------------------------------------------

output "ecr_repository_urls" {
  description = "Map of ECR repository URLs"
  value       = module.ecr.repository_urls
}

output "ecr_repository_arns" {
  description = "Map of ECR repository ARNs"
  value       = module.ecr.repository_arns
}

output "ecr_registry_id" {
  description = "ECR registry ID (AWS account ID)"
  value       = module.ecr.registry_id
}

# -----------------------------------------------------------------------------
# ECS Cluster
# -----------------------------------------------------------------------------

output "ecs_cluster_id" {
  description = "ECS cluster ID"
  value       = module.ecs_cluster.cluster_id
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN"
  value       = module.ecs_cluster.cluster_arn
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs_cluster.cluster_name
}

# -----------------------------------------------------------------------------
# ECS Services
# -----------------------------------------------------------------------------

output "api_service_name" {
  description = "API ECS service name"
  value       = module.ecs_api.service_name
}

output "api_task_definition_arn" {
  description = "API task definition ARN"
  value       = module.ecs_api.task_definition_arn
}

output "worker_service_name" {
  description = "Worker ECS service name"
  value       = module.ecs_worker.service_name
}

output "worker_task_definition_arn" {
  description = "Worker task definition ARN"
  value       = module.ecs_worker.task_definition_arn
}

output "frontend_service_name" {
  description = "Frontend ECS service name"
  value       = module.ecs_frontend.service_name
}

output "frontend_task_definition_arn" {
  description = "Frontend task definition ARN"
  value       = module.ecs_frontend.task_definition_arn
}

# -----------------------------------------------------------------------------
# Load Balancers
# -----------------------------------------------------------------------------

output "api_alb_dns_name" {
  description = "API ALB DNS name"
  value       = module.alb_api.alb_dns_name
}

output "api_alb_zone_id" {
  description = "API ALB hosted zone ID (for Route 53)"
  value       = module.alb_api.alb_zone_id
}

output "api_url" {
  description = "API URL (HTTPS)"
  value       = "https://${module.alb_api.alb_dns_name}"
}

output "frontend_alb_dns_name" {
  description = "Frontend ALB DNS name"
  value       = module.alb_frontend.alb_dns_name
}

output "frontend_alb_zone_id" {
  description = "Frontend ALB hosted zone ID (for Route 53)"
  value       = module.alb_frontend.alb_zone_id
}

output "frontend_url" {
  description = "Frontend URL (HTTPS)"
  value       = "https://${module.alb_frontend.alb_dns_name}"
}

# -----------------------------------------------------------------------------
# SQS Queues
# -----------------------------------------------------------------------------

output "sqs_queue_url" {
  description = "Worker jobs SQS queue URL"
  value       = module.sqs_worker.queue_url
}

output "sqs_queue_arn" {
  description = "Worker jobs SQS queue ARN"
  value       = module.sqs_worker.queue_arn
}

output "sqs_dlq_url" {
  description = "Worker jobs DLQ URL"
  value       = module.sqs_worker.dlq_url
}

output "sqs_dlq_arn" {
  description = "Worker jobs DLQ ARN"
  value       = module.sqs_worker.dlq_arn
}

# -----------------------------------------------------------------------------
# IAM Roles
# -----------------------------------------------------------------------------

output "task_execution_role_arn" {
  description = "ECS task execution role ARN"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "api_task_role_arn" {
  description = "API task role ARN"
  value       = aws_iam_role.api_task.arn
}

output "worker_task_role_arn" {
  description = "Worker task role ARN"
  value       = aws_iam_role.worker_task.arn
}

output "frontend_task_role_arn" {
  description = "Frontend task role ARN"
  value       = aws_iam_role.frontend_task.arn
}

# -----------------------------------------------------------------------------
# Security Groups
# -----------------------------------------------------------------------------

output "api_security_group_id" {
  description = "API service security group ID"
  value       = aws_security_group.api.id
}

output "worker_security_group_id" {
  description = "Worker service security group ID"
  value       = aws_security_group.worker.id
}

output "frontend_security_group_id" {
  description = "Frontend service security group ID"
  value       = aws_security_group.frontend.id
}

# -----------------------------------------------------------------------------
# CloudWatch Log Groups
# -----------------------------------------------------------------------------

output "api_log_group_name" {
  description = "API CloudWatch log group name"
  value       = module.ecs_api.log_group_name
}

output "worker_log_group_name" {
  description = "Worker CloudWatch log group name"
  value       = module.ecs_worker.log_group_name
}

output "frontend_log_group_name" {
  description = "Frontend CloudWatch log group name"
  value       = module.ecs_frontend.log_group_name
}

# -----------------------------------------------------------------------------
# Deployment Information
# -----------------------------------------------------------------------------

output "deployment_info" {
  description = "Deployment information summary"
  value = {
    environment    = var.environment
    region         = var.aws_region
    cluster_name   = module.ecs_cluster.cluster_name
    api_url        = "https://${module.alb_api.alb_dns_name}"
    frontend_url   = "https://${module.alb_frontend.alb_dns_name}"
    cloudfront_url = module.cloudfront.url
    ecr_registry   = "${module.ecr.registry_id}.dkr.ecr.${var.aws_region}.amazonaws.com"
  }
}

# -----------------------------------------------------------------------------
# CloudFront Distribution
# -----------------------------------------------------------------------------

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cloudfront.distribution_id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.cloudfront.domain_name
}

output "cloudfront_url" {
  description = "CloudFront HTTPS URL (primary access point)"
  value       = module.cloudfront.url
}
