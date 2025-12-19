# =============================================================================
# Free Observability: X-Ray + CloudWatch Logs
# =============================================================================

# X-Ray tracing (FREE: 100K traces/month)
module "xray" {
  source = "./modules/xray"

  project_name = var.project_name
  environment  = var.environment
}

# CloudWatch Log Insights queries (FREE with existing logs)
# Note: depends_on ensures ECS modules create log groups first
resource "aws_cloudwatch_query_definition" "api_errors" {
  name = "${var.project_name}-api-errors"

  log_group_names = [
    module.ecs_api.log_group_name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /ERROR/
    | sort @timestamp desc
    | limit 100
  QUERY

  depends_on = [module.ecs_api]
}

resource "aws_cloudwatch_query_definition" "worker_performance" {
  name = "${var.project_name}-worker-performance"

  log_group_names = [
    module.ecs_worker.log_group_name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /processing_time/
    | parse @message /processing_time=(?<duration>\d+)/
    | stats avg(duration), max(duration), min(duration) by bin(5m)
  QUERY

  depends_on = [module.ecs_worker]
}

resource "aws_cloudwatch_query_definition" "categorization_accuracy" {
  name = "${var.project_name}-categorization-accuracy"

  log_group_names = [
    module.ecs_worker.log_group_name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /GAMP category/
    | parse @message /category=(?<category>\d+).*confidence=(?<confidence>[\d.]+)/
    | stats count() by category
  QUERY

  depends_on = [module.ecs_worker]
}

# CloudWatch Dashboard (FREE)
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", { stat = "Average", label = "API CPU" }],
            ["...", { stat = "Average", label = "Worker CPU" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "ECS CPU Utilization"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", { stat = "Average" }]
          ]
          period = 60
          stat   = "Average"
          region = var.aws_region
          title  = "SQS Queue Depth"
        }
      },
      {
        type = "log"
        properties = {
          query  = "SOURCE '${module.ecs_api.log_group_name}' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20"
          region = var.aws_region
          title  = "Recent API Errors"
        }
      }
    ]
  })

  depends_on = [module.ecs_api, module.ecs_worker]
}
