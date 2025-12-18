# =============================================================================
# RDS Module Variables
# =============================================================================

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Deployment environment (staging, production)"
  type        = string
  default     = "staging"
}

variable "vpc_id" {
  description = "VPC ID for RDS deployment"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for RDS subnet group"
  type        = list(string)
}

variable "ecs_security_group_ids" {
  description = "Security group IDs that need access to RDS (ECS tasks)"
  type        = list(string)
}

variable "database_name" {
  description = "Name of the database to create"
  type        = string
  default     = "testgen"
}

variable "database_username" {
  description = "Master username for the database"
  type        = string
  default     = "postgres"
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro" # ~$13/month
}

variable "allocated_storage" {
  description = "Initial storage allocation in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum storage for autoscaling in GB"
  type        = number
  default     = 100
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 1 # Minimal for staging
}
