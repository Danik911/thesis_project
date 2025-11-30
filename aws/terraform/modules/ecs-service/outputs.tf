# =============================================================================
# ECS Service Module Outputs
# =============================================================================

output "service_id" {
  description = "ECS service ID"
  value       = aws_ecs_service.this.id
}

output "service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.this.name
}

output "service_arn" {
  description = "ECS service ARN"
  value       = aws_ecs_service.this.id
}

output "task_definition_arn" {
  description = "Task definition ARN"
  value       = aws_ecs_task_definition.this.arn
}

output "task_definition_family" {
  description = "Task definition family"
  value       = aws_ecs_task_definition.this.family
}

output "task_definition_revision" {
  description = "Task definition revision"
  value       = aws_ecs_task_definition.this.revision
}

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.this.name
}

output "log_group_arn" {
  description = "CloudWatch log group ARN"
  value       = aws_cloudwatch_log_group.this.arn
}

output "autoscaling_target_id" {
  description = "Auto scaling target ID"
  value       = var.enable_autoscaling ? aws_appautoscaling_target.this[0].id : null
}
