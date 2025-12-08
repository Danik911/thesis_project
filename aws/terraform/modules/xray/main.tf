# =============================================================================
# AWS X-Ray Tracing Module (FREE TIER)
# =============================================================================

resource "aws_xray_sampling_rule" "main" {
  rule_name      = "${var.project_name}-sampling"
  priority       = 1000
  version        = 1
  reservoir_size = 1
  fixed_rate     = 0.05 # 5% sampling
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"

  attributes = {
    Environment = var.environment
  }
}

resource "aws_xray_group" "api" {
  group_name        = "${var.project_name}-api"
  filter_expression = "service(\"${var.project_name}-api\")"

  insights_configuration {
    insights_enabled      = false
    notifications_enabled = false
  }

  tags = {
    Service = "api"
    GAMP5   = "true"
  }
}

resource "aws_xray_group" "worker" {
  group_name        = "${var.project_name}-worker"
  filter_expression = "service(\"${var.project_name}-worker\")"

  insights_configuration {
    insights_enabled      = false
    notifications_enabled = false
  }

  tags = {
    Service = "worker"
    GAMP5   = "true"
  }
}
