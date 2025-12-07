# =============================================================================
# CloudFront Distribution Module
# =============================================================================
# GAMP-5 Compliance: HTTPS termination for pharmaceutical test generation
#
# This module manages the CloudFront distribution that:
# - Provides HTTPS access to the frontend and API
# - Routes API requests (/jobs*, /api/*, /health*) to API ALB
# - Routes all other requests to Frontend ALB
# - Automatically updates when ALB DNS names change (solves destroy/deploy issue)

locals {
  # Managed cache policies provided by AWS
  cache_disabled_policy_id         = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"  # CachingDisabled
  cache_optimized_policy_id        = "658327ea-f89d-4fab-a63d-7e88639e58f6"  # CachingOptimized

  # Managed origin request policies provided by AWS
  all_viewer_policy_id             = "216adef6-5c7f-47e4-b989-5492eafa07d3"  # AllViewer
}

resource "aws_cloudfront_distribution" "this" {
  enabled             = true
  comment             = "${var.project_name} Frontend + API HTTPS - Terraform Managed"
  price_class         = "PriceClass_100"  # Use only North America and Europe
  http_version        = "http2"
  is_ipv6_enabled     = true
  default_root_object = ""

  # -------------------------------------------------------------------------
  # Origins
  # -------------------------------------------------------------------------

  # Frontend ALB (default origin)
  origin {
    domain_name = var.frontend_alb_dns_name
    origin_id   = "frontend-alb"

    custom_origin_config {
      http_port                = 80
      https_port               = 443
      origin_protocol_policy   = "http-only"
      origin_ssl_protocols     = ["TLSv1.2"]
      origin_keepalive_timeout = 5
      origin_read_timeout      = 30
    }
  }

  # API ALB
  origin {
    domain_name = var.api_alb_dns_name
    origin_id   = "api-alb"

    custom_origin_config {
      http_port                = 80
      https_port               = 443
      origin_protocol_policy   = "http-only"
      origin_ssl_protocols     = ["TLSv1.2"]
      origin_keepalive_timeout = 5
      origin_read_timeout      = 60  # Longer timeout for API requests
    }
  }

  # -------------------------------------------------------------------------
  # Default Cache Behavior (Frontend)
  # -------------------------------------------------------------------------

  default_cache_behavior {
    target_origin_id       = "frontend-alb"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods  = ["GET", "HEAD"]

    # Disable caching for HTML pages to prevent 404 errors after deployment.
    # Next.js embeds build IDs in HTML that reference specific JS chunks.
    # If CloudFront caches old HTML with old build IDs, browsers request
    # non-existent chunks from the new deployment, causing 404s.
    # Static assets (_next/static/*) are immutable and cached by browsers.
    cache_policy_id          = local.cache_disabled_policy_id
    origin_request_policy_id = local.all_viewer_policy_id
  }

  # -------------------------------------------------------------------------
  # API Cache Behaviors (No Caching - Dynamic Content)
  # -------------------------------------------------------------------------

  # /jobs* - Job management API
  ordered_cache_behavior {
    path_pattern           = "/jobs*"
    target_origin_id       = "api-alb"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods  = ["GET", "HEAD"]

    # Disable caching for API requests
    cache_policy_id          = local.cache_disabled_policy_id
    origin_request_policy_id = local.all_viewer_policy_id
  }

  # /api/* - General API routes
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    target_origin_id       = "api-alb"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods  = ["GET", "HEAD"]

    cache_policy_id          = local.cache_disabled_policy_id
    origin_request_policy_id = local.all_viewer_policy_id
  }

  # /health* - Health check endpoint
  ordered_cache_behavior {
    path_pattern           = "/health*"
    target_origin_id       = "api-alb"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]

    cache_policy_id          = local.cache_disabled_policy_id
    origin_request_policy_id = local.all_viewer_policy_id
  }

  # -------------------------------------------------------------------------
  # SSL Certificate
  # -------------------------------------------------------------------------

  viewer_certificate {
    cloudfront_default_certificate = true
    ssl_support_method             = "vip"
    minimum_protocol_version       = "TLSv1"
  }

  # -------------------------------------------------------------------------
  # Restrictions
  # -------------------------------------------------------------------------

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # -------------------------------------------------------------------------
  # Tags
  # -------------------------------------------------------------------------

  tags = {
    Name        = "${var.project_name}-cloudfront"
    Environment = var.environment
    GAMP5       = "true"
    Component   = "cdn"
    ManagedBy   = "terraform"
  }

  # -------------------------------------------------------------------------
  # Lifecycle
  # -------------------------------------------------------------------------

  lifecycle {
    # Prevent accidental destruction of CloudFront distribution
    prevent_destroy = false  # Set to true in production
  }
}
