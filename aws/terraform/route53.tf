# =============================================================================
# Route 53 DNS Configuration for csvgeneration.com
# =============================================================================

module "route53" {
  source = "./modules/route53"

  project_name = var.project_name
  environment  = var.environment

  # Domain configuration
  domain_name         = var.domain_name
  create_hosted_zone  = var.create_hosted_zone
  api_subdomain       = var.api_subdomain
  frontend_subdomain  = var.frontend_subdomain
  create_root_record  = var.create_root_record

  # ALB and CloudFront endpoints
  api_alb_dns_name       = module.alb_api.alb_dns_name
  api_alb_zone_id        = module.alb_api.alb_zone_id
  cloudfront_domain_name = module.cloudfront.domain_name
  cloudfront_zone_id     = "Z2FDTNDATAQYW2" # CloudFront global zone
}

# ACM Certificate for custom domain (must be in us-east-1 for CloudFront)
resource "aws_acm_certificate" "cloudfront" {
  count             = var.domain_name != "" ? 1 : 0
  provider          = aws.us_east_1
  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = [
    "*.${var.domain_name}"
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "${var.project_name}-cloudfront-cert"
    Environment = var.environment
    GAMP5       = "true"
  }
}

# DNS validation records
resource "aws_route53_record" "cert_validation" {
  for_each = var.domain_name != "" ? {
    for dvo in aws_acm_certificate.cloudfront[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  zone_id = module.route53.zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60
}

# Certificate validation
resource "aws_acm_certificate_validation" "cloudfront" {
  count                   = var.domain_name != "" ? 1 : 0
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.cloudfront[0].arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}
