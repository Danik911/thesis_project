# =============================================================================
# Route 53 DNS Configuration for csvgeneration.com
# =============================================================================

module "route53" {
  source = "./modules/route53"

  project_name = var.project_name
  environment  = var.environment

  # Domain configuration
  domain_name        = var.domain_name
  create_hosted_zone = var.create_hosted_zone
  api_subdomain      = var.api_subdomain
  frontend_subdomain = var.frontend_subdomain
  create_root_record = var.create_root_record

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

# DNS validation record
# Using count instead of for_each because for_each keys must be known at plan time,
# but domain_validation_options is only known after the certificate is created.
# Base domain + wildcard share the same validation record, so we only need one.
resource "aws_route53_record" "cert_validation" {
  count = var.domain_name != "" ? 1 : 0

  allow_overwrite = true  # Handles existing records without complex import logic
  zone_id         = module.route53.zone_id
  name            = tolist(aws_acm_certificate.cloudfront[0].domain_validation_options)[0].resource_record_name
  type            = tolist(aws_acm_certificate.cloudfront[0].domain_validation_options)[0].resource_record_type
  records         = [tolist(aws_acm_certificate.cloudfront[0].domain_validation_options)[0].resource_record_value]
  ttl             = 60
}

# Certificate validation
resource "aws_acm_certificate_validation" "cloudfront" {
  count           = var.domain_name != "" ? 1 : 0
  provider        = aws.us_east_1
  certificate_arn = aws_acm_certificate.cloudfront[0].arn
  validation_record_fqdns = [aws_route53_record.cert_validation[0].fqdn]
}
