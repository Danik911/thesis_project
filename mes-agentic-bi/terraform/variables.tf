variable "environment" {
  description = "Environment name (e.g., dev, staging, production)"
  type        = string
  default     = "dev"
}

variable "pool_name" {
  description = "Base name for the Cognito User Pool"
  type        = string
  default     = "bi-user-pool"
}

variable "region" {
  description = "AWS region for Cognito resources"
  type        = string
  default     = "eu-west-1"
}

variable "callback_urls" {
  description = "Allowed callback URLs for the Cognito client (login redirects)"
  type        = list(string)
  default     = ["http://localhost:3000/agentic-bi"]
}

variable "logout_urls" {
  description = "Allowed logout URLs for the Cognito client"
  type        = list(string)
  default     = ["http://localhost:3000/login"]
}

variable "password_minimum_length" {
  description = "Minimum password length"
  type        = number
  default     = 12
}
