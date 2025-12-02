# =============================================================================
# Main Terraform Configuration - ECS Fargate Infrastructure
# =============================================================================
# GAMP-5 Compliance: Pharmaceutical test generation infrastructure
# Task 4.1: ECS & Fargate Deployment Infrastructure
#
# This file orchestrates all modules and defines:
# - Data sources for existing resources
# - IAM roles (task execution + service-specific task roles)
# - Security groups
# - Module invocations
# - CloudWatch alarms

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# -----------------------------------------------------------------------------
# ECR Repositories
# -----------------------------------------------------------------------------

module "ecr" {
  source = "./modules/ecr"

  project_name = var.project_name
  environment  = var.environment

  repositories = {
    api      = "FastAPI backend service"
    worker   = "Background job processor"
    frontend = "Next.js frontend application"
  }

  keep_tagged_images   = 30
  untagged_expiry_days = 7
  staging_expiry_days  = 14
}

# -----------------------------------------------------------------------------
# ECS Cluster
# -----------------------------------------------------------------------------

module "ecs_cluster" {
  source = "./modules/ecs-cluster"

  cluster_name              = "${var.project_name}-cluster"
  enable_container_insights = var.enable_container_insights
}

# -----------------------------------------------------------------------------
# SQS Queue for Worker Jobs
# -----------------------------------------------------------------------------

module "sqs_worker" {
  source = "./modules/sqs"

  queue_name                 = "${var.project_name}-worker-jobs"
  visibility_timeout_seconds = var.worker_visibility_timeout
  message_retention_seconds  = 86400   # 1 day
  receive_wait_time_seconds  = 10      # Long polling
  max_receive_count          = 3       # Retries before DLQ
  dlq_retention_seconds      = 1209600 # 14 days
}

# -----------------------------------------------------------------------------
# S3 Bucket for ChromaDB RAG Storage (Task 4.2)
# -----------------------------------------------------------------------------
# Stores compressed ChromaDB tarball for worker download on startup
# Cost: ~$0.02/month for 2MB storage

resource "aws_s3_bucket" "chromadb" {
  bucket = "${var.project_name}-chromadb-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "${var.project_name}-chromadb"
    Environment = var.environment
    GAMP5       = "true"
    Component   = "rag"
  }
}

resource "aws_s3_bucket_versioning" "chromadb" {
  bucket = aws_s3_bucket.chromadb.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "chromadb" {
  bucket = aws_s3_bucket.chromadb.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "chromadb" {
  bucket = aws_s3_bucket.chromadb.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# -----------------------------------------------------------------------------
# IAM Roles
# -----------------------------------------------------------------------------

# Task Execution Role (shared by all services)
# Used by ECS agent to pull images, inject secrets, push logs
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    GAMP5 = "true"
  }
}

# Attach AWS managed policy for basic ECS execution
resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Custom policy for task execution (ECR + Secrets Manager)
resource "aws_iam_role_policy" "ecs_task_execution_custom" {
  name = "${var.project_name}-ecs-execution-custom"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Secrets Manager access (inject secrets into containers)
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}/*",
          var.aurora_secret_arn  # Allow access to the Aurora/placeholder secret
        ]
      },
      # CloudWatch Logs (push container logs)
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/${var.project_name}/*"
      }
    ]
  })
}

# Task Role - API Service
resource "aws_iam_role" "api_task" {
  name = "${var.project_name}-api-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Service = "api"
    GAMP5   = "true"
  }
}

resource "aws_iam_role_policy" "api_task" {
  name = "${var.project_name}-api-task-policy"
  role = aws_iam_role.api_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # SQS - Send messages to worker queue
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = module.sqs_worker.queue_arn
      },
      # Aurora Data API - Job metadata storage
      {
        Effect = "Allow"
        Action = [
          "rds-data:ExecuteStatement",
          "rds-data:BatchExecuteStatement",
          "rds-data:BeginTransaction",
          "rds-data:CommitTransaction",
          "rds-data:RollbackTransaction"
        ]
        Resource = var.aurora_cluster_arn
      },
      # Secrets Manager - Aurora credentials
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = var.aurora_secret_arn
      }
    ]
  })
}

# Task Role - Worker Service
resource "aws_iam_role" "worker_task" {
  name = "${var.project_name}-worker-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Service = "worker"
    GAMP5   = "true"
  }
}

resource "aws_iam_role_policy" "worker_task" {
  name = "${var.project_name}-worker-task-policy"
  role = aws_iam_role.worker_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # SQS - Receive/delete messages
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ]
        Resource = module.sqs_worker.queue_arn
      },
      # S3 - Write test suites
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:GetObject"
        ]
        Resource = "arn:aws:s3:::${var.output_bucket}/*"
      },
      # S3 ChromaDB - Download RAG database on startup (Task 4.2)
      # Using existing bucket pharma-test-gen-vectors-staging (manually created during initial deployment)
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "arn:aws:s3:::pharma-test-gen-vectors-staging/*"
      },
      # Bedrock - DeepSeek V3 inference
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.bedrock_region}::foundation-model/*",
          "arn:aws:bedrock:${var.bedrock_region}:*:inference-profile/*"
        ]
      },
      # Aurora Data API
      {
        Effect = "Allow"
        Action = [
          "rds-data:ExecuteStatement",
          "rds-data:BatchExecuteStatement",
          "rds-data:BeginTransaction",
          "rds-data:CommitTransaction",
          "rds-data:RollbackTransaction"
        ]
        Resource = var.aurora_cluster_arn
      },
      # Secrets Manager
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          var.aurora_secret_arn,
          "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}/langfuse-*",
          "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}/openrouter-*"
        ]
      }
    ]
  })
}

# Task Role - Frontend Service (minimal permissions)
resource "aws_iam_role" "frontend_task" {
  name = "${var.project_name}-frontend-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Service  = "frontend"
    GAMP5    = "true"
  }
}

# Frontend typically doesn't need AWS SDK access (uses API endpoints)
# Add minimal policies if needed in the future

# -----------------------------------------------------------------------------
# Security Groups
# -----------------------------------------------------------------------------

# ALB Security Group (API)
resource "aws_security_group" "alb_api" {
  name        = "${var.project_name}-alb-api-sg"
  description = "Security group for API ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP from internet (redirect to HTTPS)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Outbound to API tasks"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Component = "alb-api"
    GAMP5     = "true"
  }
}

# ALB Security Group (Frontend)
resource "aws_security_group" "alb_frontend" {
  name        = "${var.project_name}-alb-frontend-sg"
  description = "Security group for Frontend ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP from internet (redirect to HTTPS)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Outbound to Frontend tasks"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Component = "alb-frontend"
    GAMP5     = "true"
  }
}

# API Service Security Group
resource "aws_security_group" "api" {
  name        = "${var.project_name}-api-sg"
  description = "Security group for API ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    description     = "HTTP from ALB"
    from_port       = var.api_port
    to_port         = var.api_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_api.id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Service = "api"
    GAMP5   = "true"
  }
}

# Worker Service Security Group
resource "aws_security_group" "worker" {
  name        = "${var.project_name}-worker-sg"
  description = "Security group for Worker ECS tasks"
  vpc_id      = var.vpc_id

  # No inbound rules (worker doesn't accept connections)

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Service = "worker"
    GAMP5   = "true"
  }
}

# Frontend Service Security Group
resource "aws_security_group" "frontend" {
  name        = "${var.project_name}-frontend-sg"
  description = "Security group for Frontend ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    description     = "HTTP from ALB"
    from_port       = var.frontend_port
    to_port         = var.frontend_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_frontend.id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Service  = "frontend"
    GAMP5    = "true"
  }
}

# -----------------------------------------------------------------------------
# Application Load Balancers
# -----------------------------------------------------------------------------

module "alb_api" {
  source = "./modules/alb"

  name                       = "${var.project_name}-api-alb"
  service_name               = "api"
  vpc_id                     = var.vpc_id
  subnet_ids                 = var.public_subnet_ids
  security_group_ids         = [aws_security_group.alb_api.id]
  target_port                = var.api_port
  health_check_path          = var.api_health_check_path
  certificate_arn            = var.acm_certificate_arn
  enable_deletion_protection = var.enable_deletion_protection
}

module "alb_frontend" {
  source = "./modules/alb"

  name                       = "${var.project_name}-frontend-alb"
  service_name               = "frontend"
  vpc_id                     = var.vpc_id
  subnet_ids                 = var.public_subnet_ids
  security_group_ids         = [aws_security_group.alb_frontend.id]
  target_port                = var.frontend_port
  health_check_path          = var.frontend_health_check_path
  certificate_arn            = var.acm_certificate_arn
  enable_deletion_protection = var.enable_deletion_protection
}

# -----------------------------------------------------------------------------
# ECS Services
# -----------------------------------------------------------------------------

# API Service
module "ecs_api" {
  source = "./modules/ecs-service"

  project_name       = var.project_name
  service_name       = "api"
  aws_region         = var.aws_region
  cluster_id         = module.ecs_cluster.cluster_id
  cluster_name       = module.ecs_cluster.cluster_name
  ecr_repository_url = module.ecr.repository_urls["api"]
  image_tag          = var.api_image_tag

  cpu    = var.api_cpu
  memory = var.api_memory

  execution_role_arn = aws_iam_role.ecs_task_execution.arn
  task_role_arn      = aws_iam_role.api_task.arn

  subnet_ids         = var.private_subnet_ids
  security_group_ids = [aws_security_group.api.id]
  assign_public_ip   = var.assign_public_ip
  target_group_arn   = module.alb_api.target_group_arn
  container_port     = var.api_port

  environment_variables = [
    { name = "ENVIRONMENT", value = var.environment },
    { name = "AWS_REGION", value = var.aws_region },
    { name = "SQS_QUEUE_URL", value = module.sqs_worker.queue_url },
    { name = "DATABASE_NAME", value = var.aurora_database_name },
    { name = "AURORA_CLUSTER_ARN", value = var.aurora_cluster_arn }
  ]

  secrets = [
    { name = "DATABASE_URL", valueFrom = var.aurora_secret_arn }
  ]

  health_check_command      = ["CMD-SHELL", "curl -f http://localhost:${var.api_port}${var.api_health_check_path} || exit 1"]
  health_check_grace_period = 60

  desired_count             = var.api_desired_count
  min_capacity              = var.api_min_capacity
  max_capacity              = var.api_max_capacity
  cpu_target_utilization    = var.cpu_target_utilization
  memory_target_utilization = var.memory_target_utilization
  scale_in_cooldown         = var.scale_in_cooldown
  scale_out_cooldown        = var.scale_out_cooldown
  log_retention_days        = var.log_retention_days

  # Dependencies are inferred through resource references
}

# Worker Service
module "ecs_worker" {
  source = "./modules/ecs-service"

  project_name       = var.project_name
  service_name       = "worker"
  aws_region         = var.aws_region
  cluster_id         = module.ecs_cluster.cluster_id
  cluster_name       = module.ecs_cluster.cluster_name
  ecr_repository_url = module.ecr.repository_urls["worker"]
  image_tag          = var.worker_image_tag

  cpu    = var.worker_cpu
  memory = var.worker_memory

  execution_role_arn = aws_iam_role.ecs_task_execution.arn
  task_role_arn      = aws_iam_role.worker_task.arn

  subnet_ids         = var.private_subnet_ids
  security_group_ids = [aws_security_group.worker.id]
  assign_public_ip   = var.assign_public_ip
  target_group_arn   = null  # Worker has no ALB
  container_port     = null  # Worker has no HTTP endpoint

  environment_variables = [
    { name = "ENVIRONMENT", value = var.environment },
    { name = "AWS_REGION", value = var.aws_region },
    { name = "BEDROCK_REGION", value = var.bedrock_region },
    { name = "BEDROCK_MODEL_ID", value = var.bedrock_model_id },
    { name = "SQS_QUEUE_URL", value = module.sqs_worker.queue_url },
    { name = "OUTPUT_BUCKET", value = var.output_bucket },
    { name = "DATABASE_NAME", value = var.aurora_database_name },
    { name = "AURORA_CLUSTER_ARN", value = var.aurora_cluster_arn },
    # ChromaDB RAG Configuration (Task 4.2)
    # Using existing bucket pharma-test-gen-vectors-staging (manually created during initial deployment)
    { name = "S3_CHROMADB_BUCKET", value = "pharma-test-gen-vectors-staging" },
    { name = "S3_CHROMADB_KEY", value = "chroma_db.tar.gz" },
    { name = "RAG_VECTOR_STORE_PATH", value = "/app/chroma_db" }
  ]

  secrets = [
    { name = "DATABASE_URL", valueFrom = var.aurora_secret_arn }
  ]

  health_check_command = null  # Worker has no health check endpoint

  desired_count             = var.worker_desired_count
  min_capacity              = var.worker_min_capacity
  max_capacity              = var.worker_max_capacity
  cpu_target_utilization    = null  # Worker scales on SQS, not CPU
  memory_target_utilization = null  # Worker scales on SQS, not memory
  # SQS scaling disabled for initial deployment (requires queue data)
  # Re-enable after first messages are in queue:
  # sqs_queue_name            = module.sqs_worker.queue_name
  sqs_queue_name            = null
  sqs_target_value          = var.worker_target_messages_per_task
  sqs_scale_in_cooldown     = 600  # 10 minutes to prevent thrashing
  scale_out_cooldown        = var.scale_out_cooldown
  log_retention_days        = var.log_retention_days

  # Dependencies are inferred through resource references
}

# Frontend Service
module "ecs_frontend" {
  source = "./modules/ecs-service"

  project_name       = var.project_name
  service_name       = "frontend"
  aws_region         = var.aws_region
  cluster_id         = module.ecs_cluster.cluster_id
  cluster_name       = module.ecs_cluster.cluster_name
  ecr_repository_url = module.ecr.repository_urls["frontend"]
  image_tag          = var.frontend_image_tag

  cpu    = var.frontend_cpu
  memory = var.frontend_memory

  execution_role_arn = aws_iam_role.ecs_task_execution.arn
  task_role_arn      = aws_iam_role.frontend_task.arn

  subnet_ids         = var.private_subnet_ids
  security_group_ids = [aws_security_group.frontend.id]
  assign_public_ip   = var.assign_public_ip
  target_group_arn   = module.alb_frontend.target_group_arn
  container_port     = var.frontend_port

  environment_variables = [
    { name = "NODE_ENV", value = "production" },
    { name = "NEXT_PUBLIC_API_BASE_URL", value = "https://${module.alb_api.alb_dns_name}" }
  ]

  # Clerk authentication secrets from Secrets Manager
  secrets = [
    {
      name      = "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}/clerk:NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY::"
    },
    {
      name      = "CLERK_SECRET_KEY"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}/clerk:CLERK_SECRET_KEY::"
    }
  ]

  health_check_command      = ["CMD-SHELL", "curl -f http://localhost:${var.frontend_port}${var.frontend_health_check_path} || exit 1"]
  health_check_start_period = 15  # Next.js takes longer to start
  health_check_grace_period = 90

  desired_count             = var.frontend_desired_count
  min_capacity              = var.frontend_min_capacity
  max_capacity              = var.frontend_max_capacity
  cpu_target_utilization    = var.cpu_target_utilization
  memory_target_utilization = var.memory_target_utilization
  scale_in_cooldown         = var.scale_in_cooldown
  scale_out_cooldown        = var.scale_out_cooldown
  log_retention_days        = var.log_retention_days

  # Dependencies are inferred through resource references
}

# -----------------------------------------------------------------------------
# CloudWatch Alarms
# -----------------------------------------------------------------------------

# DLQ Monitoring - Alert when messages appear in DLQ
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  count = var.sns_alarm_topic_arn != "" ? 1 : 0

  alarm_name          = "${var.project_name}-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 0
  alarm_description   = "Alert when messages appear in DLQ (indicates processing failures)"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = module.sqs_worker.dlq_name
  }

  alarm_actions = [var.sns_alarm_topic_arn]

  tags = {
    Component = "monitoring"
    GAMP5     = "true"
  }
}

# API High Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  count = var.sns_alarm_topic_arn != "" ? 1 : 0

  alarm_name          = "${var.project_name}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert when API returns high number of 5XX errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = module.alb_api.alb_arn
    TargetGroup  = module.alb_api.target_group_arn
  }

  alarm_actions = [var.sns_alarm_topic_arn]

  tags = {
    Component = "monitoring"
    GAMP5     = "true"
  }
}

# -----------------------------------------------------------------------------
# Outputs (Task 4.2 - ChromaDB RAG)
# -----------------------------------------------------------------------------

output "chromadb_bucket_name" {
  description = "S3 bucket name for ChromaDB RAG storage"
  value       = aws_s3_bucket.chromadb.id
}

output "chromadb_bucket_arn" {
  description = "S3 bucket ARN for ChromaDB RAG storage"
  value       = aws_s3_bucket.chromadb.arn
}
