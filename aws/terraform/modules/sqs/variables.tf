# =============================================================================
# SQS Module Variables
# =============================================================================

variable "queue_name" {
  description = "Name of the SQS queue"
  type        = string
}

variable "delay_seconds" {
  description = "Delay in seconds before messages become visible"
  type        = number
  default     = 0
}

variable "max_message_size" {
  description = "Maximum message size in bytes (max 262144 = 256KB)"
  type        = number
  default     = 262144
}

variable "message_retention_seconds" {
  description = "Message retention period in seconds (1 day = 86400)"
  type        = number
  default     = 86400 # 1 day
}

variable "receive_wait_time_seconds" {
  description = "Wait time for long polling (0-20 seconds)"
  type        = number
  default     = 10 # Long polling for efficiency
}

variable "visibility_timeout_seconds" {
  description = "Visibility timeout in seconds (should exceed worker processing time)"
  type        = number
  default     = 900 # 15 minutes
}

variable "max_receive_count" {
  description = "Number of times a message is received before moving to DLQ"
  type        = number
  default     = 3
}

variable "dlq_retention_seconds" {
  description = "DLQ message retention in seconds (14 days = 1209600)"
  type        = number
  default     = 1209600 # 14 days for investigation
}
