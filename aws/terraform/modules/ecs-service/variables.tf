# =============================================================================
# ECS Service Module Variables
# =============================================================================

# -----------------------------------------------------------------------------
# General Configuration
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "service_name" {
  description = "Name of the service (api, worker, frontend)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

# -----------------------------------------------------------------------------
# ECS Cluster
# -----------------------------------------------------------------------------

variable "cluster_id" {
  description = "ECS cluster ID"
  type        = string
}

variable "cluster_name" {
  description = "ECS cluster name"
  type        = string
}

# -----------------------------------------------------------------------------
# Container Configuration
# -----------------------------------------------------------------------------

variable "ecr_repository_url" {
  description = "ECR repository URL for the container image"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

variable "cpu" {
  description = "CPU units for the task (1024 = 1 vCPU)"
  type        = number
}

variable "memory" {
  description = "Memory in MB for the task"
  type        = number
}

variable "cpu_architecture" {
  description = "CPU architecture (X86_64 or ARM64)"
  type        = string
  default     = "X86_64"  # AMD64 for ECS Fargate
}

variable "container_port" {
  description = "Container port (null for workers without HTTP endpoint)"
  type        = number
  default     = null
}

# -----------------------------------------------------------------------------
# IAM Roles
# -----------------------------------------------------------------------------

variable "execution_role_arn" {
  description = "ARN of the task execution role"
  type        = string
}

variable "task_role_arn" {
  description = "ARN of the task role"
  type        = string
}

# -----------------------------------------------------------------------------
# Networking
# -----------------------------------------------------------------------------

variable "subnet_ids" {
  description = "List of subnet IDs for the service"
  type        = list(string)
}

variable "security_group_ids" {
  description = "List of security group IDs for the service"
  type        = list(string)
}

variable "assign_public_ip" {
  description = "Assign public IP to tasks (required for public subnets without NAT)"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Load Balancer (optional)
# -----------------------------------------------------------------------------

variable "target_group_arn" {
  description = "Target group ARN for load balancer (null for workers)"
  type        = string
  default     = null
}

# -----------------------------------------------------------------------------
# Environment Configuration
# -----------------------------------------------------------------------------

variable "environment_variables" {
  description = "List of environment variables"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "secrets" {
  description = "List of secrets from Secrets Manager"
  type = list(object({
    name      = string
    valueFrom = string
  }))
  default = []
}

# -----------------------------------------------------------------------------
# Health Check Configuration
# -----------------------------------------------------------------------------

variable "health_check_command" {
  description = "Health check command for container"
  type        = list(string)
  default     = null
}

variable "health_check_interval" {
  description = "Health check interval in seconds"
  type        = number
  default     = 30
}

variable "health_check_timeout" {
  description = "Health check timeout in seconds"
  type        = number
  default     = 5
}

variable "health_check_retries" {
  description = "Number of health check retries"
  type        = number
  default     = 3
}

variable "health_check_start_period" {
  description = "Health check start period in seconds"
  type        = number
  default     = 10
}

variable "health_check_grace_period" {
  description = "Health check grace period for ALB (seconds)"
  type        = number
  default     = 60
}

# -----------------------------------------------------------------------------
# Service Configuration
# -----------------------------------------------------------------------------

variable "desired_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 1
}

# -----------------------------------------------------------------------------
# Auto Scaling
# -----------------------------------------------------------------------------

variable "enable_autoscaling" {
  description = "Enable auto scaling for the service"
  type        = bool
  default     = true
}

variable "min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}

variable "cpu_target_utilization" {
  description = "Target CPU utilization for auto scaling (null to disable)"
  type        = number
  default     = 70
}

variable "memory_target_utilization" {
  description = "Target memory utilization for auto scaling (null to disable)"
  type        = number
  default     = 80
}

variable "scale_in_cooldown" {
  description = "Cooldown period before scaling in (seconds)"
  type        = number
  default     = 300
}

variable "scale_out_cooldown" {
  description = "Cooldown period before scaling out (seconds)"
  type        = number
  default     = 60
}

# SQS-based scaling (for workers)
variable "sqs_queue_name" {
  description = "SQS queue name for scaling (null to disable SQS scaling)"
  type        = string
  default     = null
}

variable "sqs_target_value" {
  description = "Target messages per task for SQS scaling"
  type        = number
  default     = 5
}

variable "sqs_scale_in_cooldown" {
  description = "Cooldown period for SQS scale in (longer to prevent thrashing)"
  type        = number
  default     = 600  # 10 minutes
}

# -----------------------------------------------------------------------------
# CloudWatch Logging
# -----------------------------------------------------------------------------

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------

variable "depends_on_resources" {
  description = "List of resources this service depends on"
  type        = list(any)
  default     = []
}
