# =============================================================================
# ECS Cluster Module
# =============================================================================
# GAMP-5 Compliance:
# - Container Insights enabled for audit trail and performance monitoring
# - CloudWatch metrics correlation with LangFuse observability

resource "aws_ecs_cluster" "this" {
  name = var.cluster_name

  # Enable Container Insights for CloudWatch metrics (GAMP-5 requirement)
  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }

  # Service Connect namespace (optional, for service mesh)
  dynamic "service_connect_defaults" {
    for_each = var.service_connect_namespace != null ? [1] : []
    content {
      namespace = var.service_connect_namespace
    }
  }

  tags = {
    GAMP5 = "true"
  }
}

# Cluster capacity providers for Fargate
resource "aws_ecs_cluster_capacity_providers" "this" {
  cluster_name = aws_ecs_cluster.this.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = var.fargate_base_capacity
    weight            = var.fargate_weight
    capacity_provider = "FARGATE"
  }

  # Use Fargate Spot for cost savings on non-critical workloads
  dynamic "default_capacity_provider_strategy" {
    for_each = var.enable_fargate_spot ? [1] : []
    content {
      weight            = var.fargate_spot_weight
      capacity_provider = "FARGATE_SPOT"
    }
  }
}
