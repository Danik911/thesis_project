# =============================================================================
# Application Load Balancer Module
# =============================================================================
# GAMP-5 Compliance:
# - TLS 1.3 for secure communications
# - Access logging for audit trail
# - HTTP to HTTPS redirect (security requirement)

# Application Load Balancer
resource "aws_lb" "this" {
  name               = var.name
  internal           = var.internal
  load_balancer_type = "application"
  security_groups    = var.security_group_ids
  subnets            = var.subnet_ids

  enable_deletion_protection = var.enable_deletion_protection
  enable_http2               = true
  idle_timeout               = var.idle_timeout

  # Access logging for audit trail (optional)
  dynamic "access_logs" {
    for_each = var.access_logs_bucket != null ? [1] : []
    content {
      bucket  = var.access_logs_bucket
      prefix  = var.access_logs_prefix
      enabled = true
    }
  }

  tags = {
    Component = "alb"
    GAMP5     = "true"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Target Group
resource "aws_lb_target_group" "this" {
  name        = "${var.name}-tg"
  port        = var.target_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"  # REQUIRED for Fargate

  health_check {
    enabled             = true
    healthy_threshold   = var.healthy_threshold
    unhealthy_threshold = var.unhealthy_threshold
    timeout             = var.health_check_timeout
    interval            = var.health_check_interval
    path                = var.health_check_path
    protocol            = "HTTP"
    matcher             = var.health_check_matcher
  }

  # Deregistration delay (faster deployments)
  deregistration_delay = var.deregistration_delay

  # Stickiness (optional, for session affinity)
  dynamic "stickiness" {
    for_each = var.enable_stickiness ? [1] : []
    content {
      type            = "lb_cookie"
      cookie_duration = var.stickiness_duration
      enabled         = true
    }
  }

  tags = {
    Service = var.service_name
    GAMP5   = "true"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# HTTPS Listener (primary) - only created when certificate is provided
resource "aws_lb_listener" "https" {
  count = var.certificate_arn != null && var.certificate_arn != "" ? 1 : 0

  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"  # TLS 1.3 (GAMP-5 security)
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

# Local variable for certificate check
locals {
  has_certificate = var.certificate_arn != null && var.certificate_arn != ""
}

# HTTP Listener (redirect to HTTPS or forward directly)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = local.has_certificate ? "redirect" : "forward"

    # Redirect to HTTPS if certificate is configured
    dynamic "redirect" {
      for_each = local.has_certificate ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }

    # Forward to target group if no certificate (development/staging only)
    target_group_arn = local.has_certificate ? null : aws_lb_target_group.this.arn
  }
}
