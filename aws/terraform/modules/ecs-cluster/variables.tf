# =============================================================================
# ECS Cluster Module Variables
# =============================================================================

variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "enable_container_insights" {
  description = "Enable Container Insights for CloudWatch metrics (GAMP-5 requirement)"
  type        = bool
  default     = true
}

variable "service_connect_namespace" {
  description = "Cloud Map namespace ARN for Service Connect (optional)"
  type        = string
  default     = null
}

variable "fargate_base_capacity" {
  description = "Base number of tasks to run on Fargate (before Spot)"
  type        = number
  default     = 1
}

variable "fargate_weight" {
  description = "Weight for Fargate capacity provider"
  type        = number
  default     = 1
}

variable "enable_fargate_spot" {
  description = "Enable Fargate Spot for cost savings"
  type        = bool
  default     = false
}

variable "fargate_spot_weight" {
  description = "Weight for Fargate Spot capacity provider"
  type        = number
  default     = 0
}
