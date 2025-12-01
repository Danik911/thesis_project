# =============================================================================
# ECS Service Module (Reusable for API, Worker, Frontend)
# =============================================================================
# GAMP-5 Compliance:
# - Deployment circuit breaker with auto rollback (NO FALLBACK - fail explicitly)
# - Task definition versioning for audit trail
# - CloudWatch logging for all containers

# -----------------------------------------------------------------------------
# CloudWatch Log Group
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "this" {
  name              = "/ecs/${var.project_name}/${var.service_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Service = var.service_name
    GAMP5   = "true"
  }
}

# -----------------------------------------------------------------------------
# ECS Task Definition
# -----------------------------------------------------------------------------

resource "aws_ecs_task_definition" "this" {
  family                   = "${var.project_name}-${var.service_name}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  # Runtime platform (required for ARM64 or custom settings)
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = var.cpu_architecture
  }

  container_definitions = jsonencode([
    {
      name      = var.service_name
      image     = "${var.ecr_repository_url}:${var.image_tag}"
      essential = true
      cpu       = var.cpu
      memory    = var.memory

      # Port mappings (only for services with HTTP endpoints)
      portMappings = var.container_port != null ? [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ] : []

      # Environment variables (non-sensitive)
      environment = var.environment_variables

      # Secrets from Secrets Manager/Parameter Store
      secrets = var.secrets

      # CloudWatch logging
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.this.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = var.service_name
        }
      }

      # Health check (only for services with HTTP endpoints)
      healthCheck = var.container_port != null && var.health_check_command != null ? {
        command     = var.health_check_command
        interval    = var.health_check_interval
        timeout     = var.health_check_timeout
        retries     = var.health_check_retries
        startPeriod = var.health_check_start_period
      } : null

      # Linux parameters for proper signal handling
      linuxParameters = {
        initProcessEnabled = true  # Use tini for PID 1 (matches Dockerfile)
      }

      # Disable pseudo terminal (not needed for services)
      pseudoTerminal = false
    }
  ])

  tags = {
    Service = var.service_name
    GAMP5   = "true"
  }
}

# -----------------------------------------------------------------------------
# ECS Service
# -----------------------------------------------------------------------------

resource "aws_ecs_service" "this" {
  name            = "${var.project_name}-${var.service_name}"
  cluster         = var.cluster_id
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"
  platform_version = "LATEST"

  # Network configuration (REQUIRED for Fargate)
  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = var.security_group_ids
    assign_public_ip = var.assign_public_ip  # True for public subnets without NAT
  }

  # Load balancer integration (only for API and Frontend)
  dynamic "load_balancer" {
    for_each = var.target_group_arn != null ? [1] : []
    content {
      target_group_arn = var.target_group_arn
      container_name   = var.service_name
      container_port   = var.container_port
    }
  }

  # Deployment configuration with circuit breaker
  # GAMP-5: NO FALLBACK - failed deployments trigger automatic rollback
  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100

  deployment_circuit_breaker {
    enable   = true
    rollback = true  # Auto rollback on deployment failure
  }

  # Health check grace period (only when ALB is attached)
  health_check_grace_period_seconds = var.target_group_arn != null ? var.health_check_grace_period : null

  # ECS managed tags and propagation
  enable_ecs_managed_tags = true
  propagate_tags          = "SERVICE"

  # Lifecycle: Ignore desired_count changes (auto scaling manages this)
  lifecycle {
    ignore_changes = [desired_count]
  }

  # Dependencies are inferred through resource references
  # Note: depends_on requires static list, cannot use variables

  tags = {
    Service = var.service_name
    GAMP5   = "true"
  }
}

# -----------------------------------------------------------------------------
# Auto Scaling Target
# -----------------------------------------------------------------------------

resource "aws_appautoscaling_target" "this" {
  count = var.enable_autoscaling ? 1 : 0

  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${var.cluster_name}/${aws_ecs_service.this.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# -----------------------------------------------------------------------------
# Auto Scaling Policies - CPU
# -----------------------------------------------------------------------------

resource "aws_appautoscaling_policy" "cpu" {
  count = var.enable_autoscaling && var.cpu_target_utilization != null ? 1 : 0

  name               = "${var.service_name}-cpu-target-tracking"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.this[0].resource_id
  scalable_dimension = aws_appautoscaling_target.this[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.this[0].service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = var.cpu_target_utilization
    scale_in_cooldown  = var.scale_in_cooldown
    scale_out_cooldown = var.scale_out_cooldown

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

# -----------------------------------------------------------------------------
# Auto Scaling Policies - Memory
# -----------------------------------------------------------------------------

resource "aws_appautoscaling_policy" "memory" {
  count = var.enable_autoscaling && var.memory_target_utilization != null ? 1 : 0

  name               = "${var.service_name}-memory-target-tracking"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.this[0].resource_id
  scalable_dimension = aws_appautoscaling_target.this[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.this[0].service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = var.memory_target_utilization
    scale_in_cooldown  = var.scale_in_cooldown
    scale_out_cooldown = var.scale_out_cooldown

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
  }
}

# -----------------------------------------------------------------------------
# Auto Scaling Policies - SQS (for Worker only)
# -----------------------------------------------------------------------------

resource "aws_appautoscaling_policy" "sqs" {
  count = var.enable_autoscaling && var.sqs_queue_name != null ? 1 : 0

  name               = "${var.service_name}-sqs-target-tracking"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.this[0].resource_id
  scalable_dimension = aws_appautoscaling_target.this[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.this[0].service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = var.sqs_target_value
    scale_in_cooldown  = var.sqs_scale_in_cooldown
    scale_out_cooldown = var.scale_out_cooldown

    customized_metric_specification {
      metrics {
        id          = "messages_per_task"
        expression  = "messages / MAX([tasks, 1])"  # Avoid division by zero
        return_data = true
      }

      metrics {
        id = "messages"
        metric_stat {
          metric {
            metric_name = "ApproximateNumberOfMessagesVisible"
            namespace   = "AWS/SQS"
            dimensions {
              name  = "QueueName"
              value = var.sqs_queue_name
            }
          }
          stat = "Average"
        }
      }

      metrics {
        id = "tasks"
        metric_stat {
          metric {
            metric_name = "RunningTaskCount"
            namespace   = "ECS/ContainerInsights"
            dimensions {
              name  = "ClusterName"
              value = var.cluster_name
            }
            dimensions {
              name  = "ServiceName"
              value = aws_ecs_service.this.name
            }
          }
          stat = "Average"
        }
      }
    }
  }
}
