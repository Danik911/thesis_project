# =============================================================================
# Route 53 DNS Module
# =============================================================================

resource "aws_route53_zone" "main" {
  count = var.create_hosted_zone ? 1 : 0
  name  = var.domain_name

  tags = {
    Name        = "${var.project_name}-zone"
    Environment = var.environment
    GAMP5       = "true"
  }
}

data "aws_route53_zone" "existing" {
  count = var.create_hosted_zone ? 0 : 1
  name  = var.domain_name
}

locals {
  zone_id = var.create_hosted_zone ? aws_route53_zone.main[0].zone_id : data.aws_route53_zone.existing[0].zone_id
}

# API subdomain (api.yourdomain.com)
# Routes through CloudFront for HTTPS termination, CloudFront routes /jobs*, /api/*, /health* to API ALB
resource "aws_route53_record" "api" {
  zone_id = local.zone_id
  name    = var.api_subdomain
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_zone_id
    evaluate_target_health = false
  }
}

# Frontend subdomain (app.yourdomain.com or www.yourdomain.com)
resource "aws_route53_record" "frontend" {
  zone_id = local.zone_id
  name    = var.frontend_subdomain
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_zone_id
    evaluate_target_health = false
  }
}

# Root domain (yourdomain.com) - optional
resource "aws_route53_record" "root" {
  count   = var.create_root_record ? 1 : 0
  zone_id = local.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_zone_id
    evaluate_target_health = false
  }
}
