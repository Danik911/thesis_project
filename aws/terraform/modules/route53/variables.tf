variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "domain_name" {
  description = "Domain name (e.g., example.com)"
  type        = string
}

variable "create_hosted_zone" {
  description = "Create new hosted zone (false = use existing)"
  type        = bool
  default     = false
}

variable "api_subdomain" {
  description = "API subdomain (e.g., api)"
  type        = string
  default     = "api"
}

variable "frontend_subdomain" {
  description = "Frontend subdomain (e.g., app or www)"
  type        = string
  default     = "app"
}

variable "create_root_record" {
  description = "Create root domain record"
  type        = bool
  default     = false
}

variable "api_alb_dns_name" {
  type = string
}

variable "api_alb_zone_id" {
  type = string
}

variable "cloudfront_domain_name" {
  type = string
}

variable "cloudfront_zone_id" {
  type        = string
  default     = "Z2FDTNDATAQYW2" # CloudFront zone ID (global)
}
