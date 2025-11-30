# =============================================================================
# ALB Module Variables
# =============================================================================

variable "name" {
  description = "Name of the Application Load Balancer"
  type        = string
}

variable "service_name" {
  description = "Name of the service this ALB serves"
  type        = string
}

variable "internal" {
  description = "Whether the ALB is internal (private) or internet-facing"
  type        = bool
  default     = false
}

variable "security_group_ids" {
  description = "List of security group IDs for the ALB"
  type        = list(string)
}

variable "subnet_ids" {
  description = "List of subnet IDs for the ALB"
  type        = list(string)
}

variable "vpc_id" {
  description = "VPC ID for the target group"
  type        = string
}

variable "target_port" {
  description = "Port the target container listens on"
  type        = number
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS (optional for dev)"
  type        = string
  default     = null
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection (recommended for production)"
  type        = bool
  default     = false
}

variable "idle_timeout" {
  description = "Idle timeout in seconds"
  type        = number
  default     = 60
}

# Health check configuration
variable "health_check_path" {
  description = "Health check endpoint path"
  type        = string
  default     = "/health"
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

variable "healthy_threshold" {
  description = "Number of consecutive successes for healthy status"
  type        = number
  default     = 2
}

variable "unhealthy_threshold" {
  description = "Number of consecutive failures for unhealthy status"
  type        = number
  default     = 3
}

variable "health_check_matcher" {
  description = "HTTP response codes to consider healthy"
  type        = string
  default     = "200"
}

variable "deregistration_delay" {
  description = "Deregistration delay in seconds"
  type        = number
  default     = 30
}

# Stickiness configuration
variable "enable_stickiness" {
  description = "Enable session stickiness"
  type        = bool
  default     = false
}

variable "stickiness_duration" {
  description = "Stickiness duration in seconds"
  type        = number
  default     = 86400  # 1 day
}

# Access logging
variable "access_logs_bucket" {
  description = "S3 bucket for access logs (optional)"
  type        = string
  default     = null
}

variable "access_logs_prefix" {
  description = "S3 prefix for access logs"
  type        = string
  default     = "alb-logs"
}
