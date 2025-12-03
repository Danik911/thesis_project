# =============================================================================
# CloudFront Module Variables
# =============================================================================

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (staging, production)"
  type        = string
}

variable "frontend_alb_dns_name" {
  description = "DNS name of the Frontend ALB (e.g., pharma-test-gen-frontend-alb-xxx.eu-west-2.elb.amazonaws.com)"
  type        = string
}

variable "api_alb_dns_name" {
  description = "DNS name of the API ALB (e.g., pharma-test-gen-api-alb-xxx.eu-west-2.elb.amazonaws.com)"
  type        = string
}

variable "price_class" {
  description = "CloudFront price class (PriceClass_100 = US/EU only, PriceClass_200 = US/EU/Asia, PriceClass_All = All)"
  type        = string
  default     = "PriceClass_100"
}

variable "aliases" {
  description = "List of custom domain names (CNAMEs) for the distribution"
  type        = list(string)
  default     = []
}

variable "acm_certificate_arn" {
  description = "ARN of ACM certificate for custom domain (must be in us-east-1)"
  type        = string
  default     = null
}

variable "web_acl_id" {
  description = "WAF Web ACL ID to associate with the distribution"
  type        = string
  default     = null
}
