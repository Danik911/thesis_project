# Context Collector Result - 20251130-111500

## Agent Configuration
- Agent: context-collector
- Task ID: 4.1
- Invoked: 2025-11-30T11:15:00
- Duration: 35 minutes
- Status: SUCCESS

## Task Understanding

Task 4.1 requires authoring Terraform modules for deploying a complete ECS Fargate infrastructure for a pharmaceutical test generation system with GAMP-5 compliance. The deployment includes:

1. **Three ECS Fargate services**: API (FastAPI), Worker (background processor), Frontend (Next.js)
2. **Auto scaling policies**: SQS queue depth for Worker, CPU/Memory for API/Frontend
3. **ECR integration**: Task execution role with pull permissions
4. **Secrets Manager integration**: Environment variables and secrets injection
5. **CloudWatch Container Insights**: Observability for LangFuse correlation
6. **VPC networking**: Private subnets, security groups, ALB configuration

This is a GAMP-5 compliant pharmaceutical system requiring immutable infrastructure, audit trails, and explicit error handling (NO FALLBACK LOGIC).

---

## Research Findings

### 1. Terraform AWS Provider Version

**Recommended Version**: `~> 5.0`

Based on reference examples in `examples/alex/terraform/`:
- All modules use `version = "~> 5.0"` for AWS provider
- Terraform version `>= 1.5` required
- Provider pinning is CRITICAL to prevent unexpected diffs (addresses task file warning)

```hcl
terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region  # eu-west-2 (London)
}
```

**Sources:**
- `examples/alex/terraform/6_agents/main.tf` (lines 2-9)
- Terraform Registry: https://registry.terraform.io/providers/hashicorp/aws/latest

---

### 2. ECS Cluster Configuration

**Container Insights**: MUST be enabled for CloudWatch metrics correlation with LangFuse.

```hcl
resource "aws_ecs_cluster" "main" {
  name = "pharma-test-gen-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Project     = "pharmaceutical-test-generation"
    Environment = var.environment
    ManagedBy   = "terraform"
    GAMP5       = "true"
  }
}
```

**Key Points:**
- Container Insights provides task-level CPU/memory metrics for auto scaling
- Metrics publish to CloudWatch namespace `AWS/ECS` and `ECS/ContainerInsights`
- Required for LangFuse correlation (per task file best practices)

**Sources:**
- AWS Documentation: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/deploy-container-insights-ECS-cluster.html
- Research: ECS Container Insights configuration patterns

---

### 3. ECR Repositories

**GAMP-5 Compliance**: Use `IMMUTABLE` tag mutability for production images (prevents tag overwrites, ensures audit trail).

```hcl
# ECR Repository - API Service
resource "aws_ecr_repository" "api" {
  name                 = "pharma-test-gen-api"
  image_tag_mutability = "IMMUTABLE"

  encryption_configuration {
    encryption_type = "AES256"  # KMS optional for enhanced security
  }

  image_scanning_configuration {
    scan_on_push = true  # Security best practice
  }

  tags = {
    Service     = "api"
    Project     = "pharmaceutical-test-generation"
    GAMP5       = "true"
  }
}

# Lifecycle Policy - Keep last 30 tagged images
resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 30 production images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v", "prod-"]
          countType     = "imageCountMoreThan"
          countNumber   = 30
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Expire untagged images after 7 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# Repeat for Worker and Frontend repositories
resource "aws_ecr_repository" "worker" {
  name                 = "pharma-test-gen-worker"
  image_tag_mutability = "IMMUTABLE"
  # ... same configuration
}

resource "aws_ecr_repository" "frontend" {
  name                 = "pharma-test-gen-frontend"
  image_tag_mutability = "IMMUTABLE"
  # ... same configuration
}
```

**Key Points:**
- **Immutable tags**: Once pushed, tag cannot be overwritten (GAMP-5 audit requirement)
- **Lifecycle policies**: Automatic cleanup prevents storage cost explosion
- **Scan on push**: Security vulnerability detection
- Use consistent tagging: `v1.2.3`, `prod-20251130`, etc.

**Sources:**
- Terraform Docs: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_repository
- AWS ECR Immutability: https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html

---

### 4. IAM Roles - Task Execution vs Task Role

**CRITICAL DISTINCTION:**

1. **Task Execution Role**: Used by ECS agent to pull images, inject secrets, push logs
2. **Task Role**: Used by application code to access AWS services (Aurora, S3 Vectors, Bedrock, SQS)

#### Task Execution Role (All Services)

```hcl
# Task Execution Role - Shared by all services
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "pharma-test-gen-ecs-task-execution-role"

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
    Project = "pharmaceutical-test-generation"
    GAMP5   = "true"
  }
}

# Attach AWS managed policy for basic ECS execution
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Custom policy for ECR and Secrets Manager
resource "aws_iam_role_policy" "ecs_task_execution_custom" {
  name = "pharma-test-gen-ecs-execution-custom"
  role = aws_iam_role.ecs_task_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # ECR Access (pull images)
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      # Secrets Manager Access (inject secrets into containers)
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:pharma-test-gen/*"
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
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/pharma-test-gen/*"
      }
    ]
  })
}
```

#### Task Role (Application-Specific)

```hcl
# Task Role - API Service
resource "aws_iam_role" "api_task_role" {
  name = "pharma-test-gen-api-task-role"

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

resource "aws_iam_role_policy" "api_task_policy" {
  name = "pharma-test-gen-api-task-policy"
  role = aws_iam_role.api_task_role.id

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
        Resource = aws_sqs_queue.worker_jobs.arn
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
resource "aws_iam_role" "worker_task_role" {
  name = "pharma-test-gen-worker-task-role"

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

resource "aws_iam_role_policy" "worker_task_policy" {
  name = "pharma-test-gen-worker-task-policy"
  role = aws_iam_role.worker_task_role.id

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
        Resource = aws_sqs_queue.worker_jobs.arn
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
      # S3 Vectors - RAG retrieval
      {
        Effect = "Allow"
        Action = [
          "s3vectors:QueryVectors",
          "s3vectors:GetVectors"
        ]
        Resource = "arn:aws:s3vectors:${var.aws_region}:${data.aws_caller_identity.current.account_id}:bucket/${var.vector_bucket}/index/*"
      },
      # Bedrock - DeepSeek V3 inference
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.bedrock_region}::foundation-model/deepseek-v3.1"
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
          "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:pharma-test-gen/langfuse-*",
          "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:pharma-test-gen/clerk-*"
        ]
      }
    ]
  })
}

# Task Role - Frontend Service (minimal permissions)
resource "aws_iam_role" "frontend_task_role" {
  name = "pharma-test-gen-frontend-task-role"

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
    Service = "frontend"
    GAMP5   = "true"
  }
}

# Frontend typically doesn't need AWS SDK access (uses API endpoints)
# If needed, add minimal policies here
```

**Key Points:**
- **DO NOT** grant task execution role application permissions (violates least privilege)
- **Task execution role** is shared across all services (pulls images, injects secrets)
- **Task roles** are service-specific (API, Worker, Frontend have different needs)
- Worker needs Bedrock, S3 Vectors, SQS (compute-intensive)
- API needs SQS send, Aurora write (lightweight)
- Frontend needs minimal/no AWS permissions (uses API endpoints)

**Sources:**
- AWS Task Execution Role: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html
- Reference: `examples/alex/terraform/6_agents/main.tf` (IAM patterns)

---

### 5. ECS Task Definitions

**Fargate Requirements:**
- `requires_compatibilities = ["FARGATE"]`
- `network_mode = "awsvpc"` (MANDATORY for Fargate)
- `cpu` and `memory` must be specified (see valid combinations below)
- `runtime_platform` optional but recommended for clarity

**Valid Fargate CPU/Memory Combinations:**

| CPU (vCPU) | Memory (GB) |
|------------|-------------|
| 256 (0.25) | 0.5, 1, 2 |
| 512 (0.5)  | 1, 2, 3, 4 |
| 1024 (1)   | 2, 3, 4, 5, 6, 7, 8 |
| 2048 (2)   | 4-16 (1 GB increments) |
| 4096 (4)   | 8-30 (1 GB increments) |

**Recommended for this project:**
- **API**: 2048 CPU / 4096 MB (handles concurrent requests)
- **Worker**: 4096 CPU / 8192 MB (LLM inference, RAG retrieval)
- **Frontend**: 512 CPU / 1024 MB (Next.js SSR)

#### API Task Definition

```hcl
resource "aws_ecs_task_definition" "api" {
  family                   = "pharma-test-gen-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_cpu       # 2048
  memory                   = var.api_memory    # 4096
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.api_task_role.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"  # AMD64 for ECS Fargate
  }

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${aws_ecr_repository.api.repository_url}:${var.api_image_tag}"
      essential = true
      cpu       = var.api_cpu
      memory    = var.api_memory

      portMappings = [
        {
          containerPort = 8080
          hostPort      = 8080
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "SQS_QUEUE_URL"
          value = aws_sqs_queue.worker_jobs.url
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = var.aurora_secret_arn
        },
        {
          name      = "CLERK_SECRET_KEY"
          valueFrom = aws_secretsmanager_secret.clerk_secret.arn
        },
        {
          name      = "LANGFUSE_SECRET_KEY"
          valueFrom = aws_secretsmanager_secret.langfuse_secret.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 10
      }

      # GAMP-5 Compliance: Read-only root filesystem
      readonlyRootFilesystem = false  # Set to true if app doesn't write to container FS

      # Linux parameters for security
      linuxParameters = {
        initProcessEnabled = true  # Use tini for PID 1 signal handling
      }
    }
  ])

  tags = {
    Service = "api"
    GAMP5   = "true"
  }
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/pharma-test-gen/api"
  retention_in_days = 7  # Adjust for compliance requirements

  tags = {
    Service = "api"
    GAMP5   = "true"
  }
}
```

#### Worker Task Definition

```hcl
resource "aws_ecs_task_definition" "worker" {
  family                   = "pharma-test-gen-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.worker_cpu       # 4096
  memory                   = var.worker_memory    # 8192
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.worker_task_role.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = "${aws_ecr_repository.worker.repository_url}:${var.worker_image_tag}"
      essential = true
      cpu       = var.worker_cpu
      memory    = var.worker_memory

      # No port mappings - worker doesn't expose HTTP endpoints

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "BEDROCK_REGION"
          value = var.bedrock_region
        },
        {
          name  = "BEDROCK_MODEL_ID"
          value = "deepseek/deepseek-chat"  # DeepSeek V3 via OpenRouter
        },
        {
          name  = "SQS_QUEUE_URL"
          value = aws_sqs_queue.worker_jobs.url
        },
        {
          name  = "VECTOR_BUCKET"
          value = var.vector_bucket
        },
        {
          name  = "OUTPUT_BUCKET"
          value = var.output_bucket
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = var.aurora_secret_arn
        },
        {
          name      = "OPENROUTER_API_KEY"
          valueFrom = aws_secretsmanager_secret.openrouter_key.arn
        },
        {
          name      = "LANGFUSE_SECRET_KEY"
          valueFrom = aws_secretsmanager_secret.langfuse_secret.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.worker.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "worker"
        }
      }

      # No healthCheck for workers (no HTTP endpoint)

      linuxParameters = {
        initProcessEnabled = true
      }
    }
  ])

  tags = {
    Service = "worker"
    GAMP5   = "true"
  }
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/pharma-test-gen/worker"
  retention_in_days = 7

  tags = {
    Service = "worker"
    GAMP5   = "true"
  }
}
```

#### Frontend Task Definition

```hcl
resource "aws_ecs_task_definition" "frontend" {
  family                   = "pharma-test-gen-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.frontend_cpu       # 512
  memory                   = var.frontend_memory    # 1024
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.frontend_task_role.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = "${aws_ecr_repository.frontend.repository_url}:${var.frontend_image_tag}"
      essential = true
      cpu       = var.frontend_cpu
      memory    = var.frontend_memory

      portMappings = [
        {
          containerPort = 3000
          hostPort      = 3000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "NODE_ENV"
          value = "production"
        },
        {
          name  = "NEXT_PUBLIC_API_BASE_URL"
          value = "https://${aws_lb.api.dns_name}"  # ALB DNS or CloudFront
        }
      ]

      secrets = [
        {
          name      = "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
          valueFrom = aws_secretsmanager_secret.clerk_publishable.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "frontend"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:3000/api/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 15
      }

      linuxParameters = {
        initProcessEnabled = true
      }
    }
  ])

  tags = {
    Service  = "frontend"
    GAMP5    = "true"
  }
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/pharma-test-gen/frontend"
  retention_in_days = 7

  tags = {
    Service = "frontend"
    GAMP5   = "true"
  }
}
```

**Key Points:**
- **Secrets injection**: Use `secrets` field (NOT `environment`) for sensitive data
- **Health checks**: Required for ALB integration, optional for workers
- **Log configuration**: awslogs driver pushes to CloudWatch for Container Insights
- **initProcessEnabled**: Use tini for proper signal handling (matches Dockerfile ENTRYPOINT)
- **CPU/Memory**: Task-level AND container-level must match (Fargate requirement)

**Sources:**
- Terraform Docs: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_task_definition
- AWS Task Definition Parameters: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html
- Secrets Injection: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html

---

### 6. VPC and Networking Configuration

**Best Practice for Fargate**: Private subnets + NAT Gateway (NOT public subnets with public IPs).

**Why Private Subnets?**
- **Security**: Tasks not directly exposed to internet
- **Compliance**: GAMP-5 requires network isolation for sensitive systems
- **Cost**: NAT Gateway cheaper than data transfer from public IPs at scale
- **Flexibility**: Security groups enforce inbound/outbound rules

#### VPC Configuration

```hcl
# Fetch existing VPC (assume VPC created in earlier task)
data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["pharma-test-gen-vpc"]
  }
}

# Fetch private subnets (created in VPC module)
data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Tier"
    values = ["private"]
  }
}

# Fetch public subnets (for ALB)
data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Tier"
    values = ["public"]
  }
}
```

#### Security Groups

```hcl
# Security Group - API Service (behind ALB)
resource "aws_security_group" "api" {
  name        = "pharma-test-gen-api-sg"
  description = "Security group for API ECS tasks"
  vpc_id      = data.aws_vpc.main.id

  # Inbound from ALB only
  ingress {
    description     = "HTTP from ALB"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Outbound to internet (for Bedrock, OpenRouter, etc.)
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

# Security Group - Worker Service (no inbound, only outbound)
resource "aws_security_group" "worker" {
  name        = "pharma-test-gen-worker-sg"
  description = "Security group for Worker ECS tasks"
  vpc_id      = data.aws_vpc.main.id

  # No inbound rules (worker doesn't accept connections)

  # Outbound to internet
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

# Security Group - Frontend Service
resource "aws_security_group" "frontend" {
  name        = "pharma-test-gen-frontend-sg"
  description = "Security group for Frontend ECS tasks"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 3000
    to_port         = 3000
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
    Service = "frontend"
    GAMP5   = "true"
  }
}

# Security Group - ALB (public-facing)
resource "aws_security_group" "alb" {
  name        = "pharma-test-gen-alb-sg"
  description = "Security group for API ALB"
  vpc_id      = data.aws_vpc.main.id

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
    Component = "alb"
    GAMP5     = "true"
  }
}
```

**Key Points:**
- **Private subnets**: Tasks have private IPs only, access internet via NAT Gateway
- **ALB in public subnets**: Load balancer accepts internet traffic
- **Security groups**: Enforce least privilege (API only accepts from ALB, Worker accepts nothing)
- **NO public IP assignment**: `assign_public_ip = false` in service network configuration

**Sources:**
- AWS Fargate Networking: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-networking.html
- Best Practices: https://aws.amazon.com/blogs/compute/task-networking-in-aws-fargate/

---

### 7. Application Load Balancer and Target Groups

**ALB Configuration for API and Frontend services** (Worker doesn't need ALB).

#### ALB for API

```hcl
# Application Load Balancer - API
resource "aws_lb" "api" {
  name               = "pharma-test-gen-api-alb"
  internal           = false  # Public-facing
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.public.ids

  enable_deletion_protection = var.environment == "production" ? true : false
  enable_http2               = true

  tags = {
    Component = "alb-api"
    GAMP5     = "true"
  }
}

# Target Group - API
resource "aws_lb_target_group" "api" {
  name        = "pharma-test-gen-api-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "ip"  # REQUIRED for Fargate

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200"
  }

  deregistration_delay = 30  # Faster draining for faster deployments

  tags = {
    Service = "api"
    GAMP5   = "true"
  }
}

# Listener - HTTPS (production)
resource "aws_lb_listener" "api_https" {
  load_balancer_arn = aws_lb.api.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"  # TLS 1.3
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

# Listener - HTTP (redirect to HTTPS)
resource "aws_lb_listener" "api_http" {
  load_balancer_arn = aws_lb.api.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}
```

#### ALB for Frontend

```hcl
# Application Load Balancer - Frontend
resource "aws_lb" "frontend" {
  name               = "pharma-test-gen-frontend-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_frontend.id]
  subnets            = data.aws_subnets.public.ids

  enable_deletion_protection = var.environment == "production" ? true : false
  enable_http2               = true

  tags = {
    Component = "alb-frontend"
    GAMP5     = "true"
  }
}

# Target Group - Frontend
resource "aws_lb_target_group" "frontend" {
  name        = "pharma-test-gen-frontend-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/api/health"  # Next.js health endpoint
    protocol            = "HTTP"
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = {
    Service = "frontend"
    GAMP5   = "true"
  }
}

# Listener - HTTPS
resource "aws_lb_listener" "frontend_https" {
  load_balancer_arn = aws_lb.frontend.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

# Listener - HTTP redirect
resource "aws_lb_listener" "frontend_http" {
  load_balancer_arn = aws_lb.frontend.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}
```

**Key Points:**
- **Target type `ip`**: REQUIRED for Fargate (not `instance`)
- **Health check path**: Must match application endpoint (`/health` for API, `/api/health` for Next.js)
- **Deregistration delay**: 30 seconds for faster blue/green deployments
- **SSL policy**: Use TLS 1.3 for security compliance
- **HTTP redirect**: Force HTTPS for production

**Sources:**
- ALB Target Groups: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group
- Health Check Optimization: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/load-balancer-healthcheck.html

---

### 8. ECS Services

#### API Service

```hcl
resource "aws_ecs_service" "api" {
  name            = "pharma-test-gen-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count  # Start with 2
  launch_type     = "FARGATE"
  platform_version = "LATEST"  # Use latest Fargate platform

  network_configuration {
    subnets          = data.aws_subnets.private.ids
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = false  # Private subnet, no public IP
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8080
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  health_check_grace_period_seconds = 60  # Allow time for app startup

  enable_ecs_managed_tags = true
  propagate_tags          = "SERVICE"

  # Ignore desired_count changes (auto scaling will manage this)
  lifecycle {
    ignore_changes = [desired_count]
  }

  depends_on = [
    aws_lb_listener.api_https,
    aws_iam_role_policy.api_task_policy
  ]

  tags = {
    Service = "api"
    GAMP5   = "true"
  }
}
```

#### Worker Service

```hcl
resource "aws_ecs_service" "worker" {
  name            = "pharma-test-gen-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count  # Start with 1
  launch_type     = "FARGATE"
  platform_version = "LATEST"

  network_configuration {
    subnets          = data.aws_subnets.private.ids
    security_groups  = [aws_security_group.worker.id]
    assign_public_ip = false
  }

  # No load_balancer block (worker doesn't expose HTTP)

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  enable_ecs_managed_tags = true
  propagate_tags          = "SERVICE"

  lifecycle {
    ignore_changes = [desired_count]
  }

  depends_on = [
    aws_iam_role_policy.worker_task_policy
  ]

  tags = {
    Service = "worker"
    GAMP5   = "true"
  }
}
```

#### Frontend Service

```hcl
resource "aws_ecs_service" "frontend" {
  name            = "pharma-test-gen-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count  # Start with 2
  launch_type     = "FARGATE"
  platform_version = "LATEST"

  network_configuration {
    subnets          = data.aws_subnets.private.ids
    security_groups  = [aws_security_group.frontend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 3000
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  health_check_grace_period_seconds = 90  # Next.js takes longer to start

  enable_ecs_managed_tags = true
  propagate_tags          = "SERVICE"

  lifecycle {
    ignore_changes = [desired_count]
  }

  depends_on = [
    aws_lb_listener.frontend_https,
    aws_iam_role_policy.frontend_task_policy
  ]

  tags = {
    Service  = "frontend"
    GAMP5    = "true"
  }
}
```

**Key Points:**
- **lifecycle.ignore_changes**: Prevent Terraform from reverting auto scaling changes
- **deployment_circuit_breaker**: Auto rollback on failed deployments (GAMP-5 resilience)
- **health_check_grace_period_seconds**: Allow app startup time before health checks
- **depends_on**: Ensure IAM policies and ALB listeners exist before service creation

**Sources:**
- Terraform Docs: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_service
- Reference: Task file example (lines 18-42)

---

### 9. Auto Scaling Policies

**Three scaling strategies:**

1. **API/Frontend**: Target tracking on CPU/Memory
2. **Worker**: Target tracking on SQS queue depth (messages per task)
3. **Worker**: Optional step scaling for burst traffic

#### Auto Scaling Targets

```hcl
# Auto Scaling Target - API
resource "aws_appautoscaling_target" "api" {
  max_capacity       = var.api_max_capacity  # 10
  min_capacity       = var.api_min_capacity  # 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Auto Scaling Target - Worker
resource "aws_appautoscaling_target" "worker" {
  max_capacity       = var.worker_max_capacity  # 20
  min_capacity       = var.worker_min_capacity  # 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.worker.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Auto Scaling Target - Frontend
resource "aws_appautoscaling_target" "frontend" {
  max_capacity       = var.frontend_max_capacity  # 10
  min_capacity       = var.frontend_min_capacity  # 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.frontend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}
```

#### Target Tracking Policies - CPU/Memory

```hcl
# API - Target Tracking CPU
resource "aws_appautoscaling_policy" "api_cpu" {
  name               = "api-cpu-target-tracking"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0  # Target 70% CPU utilization
    scale_in_cooldown  = 300   # 5 min cooldown before scale in
    scale_out_cooldown = 60    # 1 min cooldown before scale out

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

# API - Target Tracking Memory
resource "aws_appautoscaling_policy" "api_memory" {
  name               = "api-memory-target-tracking"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 80.0  # Target 80% memory utilization
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
  }
}

# Frontend - Same pattern as API
resource "aws_appautoscaling_policy" "frontend_cpu" {
  name               = "frontend-cpu-target-tracking"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.frontend.resource_id
  scalable_dimension = aws_appautoscaling_target.frontend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.frontend.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

resource "aws_appautoscaling_policy" "frontend_memory" {
  name               = "frontend-memory-target-tracking"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.frontend.resource_id
  scalable_dimension = aws_appautoscaling_target.frontend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.frontend.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 80.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
  }
}
```

#### Target Tracking Policy - SQS Queue Depth (Worker)

**CRITICAL**: Use target tracking (NOT step scaling) for SQS. Research shows target tracking is more stable and prevents oscillation.

```hcl
# CloudWatch Metric - SQS Messages Per Task
resource "aws_cloudwatch_metric_alarm" "worker_sqs_depth" {
  alarm_name          = "worker-sqs-messages-per-task"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = var.worker_target_messages_per_task  # 5 messages per task
  alarm_description   = "Track SQS queue depth for worker auto scaling"
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "messages_per_task"
    expression  = "messages / tasks"
    label       = "Messages Per Task"
    return_data = true
  }

  metric_query {
    id = "messages"
    metric {
      metric_name = "ApproximateNumberOfMessagesVisible"
      namespace   = "AWS/SQS"
      period      = 60
      stat        = "Average"
      dimensions = {
        QueueName = aws_sqs_queue.worker_jobs.name
      }
    }
  }

  metric_query {
    id = "tasks"
    metric {
      metric_name = "RunningTaskCount"
      namespace   = "ECS/ContainerInsights"
      period      = 60
      stat        = "Average"
      dimensions = {
        ClusterName = aws_ecs_cluster.main.name
        ServiceName = aws_ecs_service.worker.name
      }
    }
  }
}

# Worker - Target Tracking on SQS Queue Depth
resource "aws_appautoscaling_policy" "worker_sqs" {
  name               = "worker-sqs-target-tracking"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.worker.resource_id
  scalable_dimension = aws_appautoscaling_target.worker.scalable_dimension
  service_namespace  = aws_appautoscaling_target.worker.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = var.worker_target_messages_per_task  # 5 messages per task
    scale_in_cooldown  = 600  # 10 min (prevent thrashing)
    scale_out_cooldown = 60   # 1 min (fast response to queue buildup)

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
            dimensions = {
              QueueName = aws_sqs_queue.worker_jobs.name
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
            dimensions = {
              ClusterName = aws_ecs_cluster.main.name
              ServiceName = aws_ecs_service.worker.name
            }
          }
          stat = "Average"
        }
      }
    }
  }
}
```

**Alternative: Simpler SQS Scaling (if metric math not working)**

```hcl
# Simpler approach: Scale based on absolute queue size
resource "aws_appautoscaling_policy" "worker_sqs_simple" {
  name               = "worker-sqs-simple-tracking"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.worker.resource_id
  scalable_dimension = aws_appautoscaling_target.worker.scalable_dimension
  service_namespace  = aws_appautoscaling_target.worker.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 100  # Target 100 messages in queue
    scale_in_cooldown  = 600
    scale_out_cooldown = 60

    customized_metric_specification {
      metric_name = "ApproximateNumberOfMessagesVisible"
      namespace   = "AWS/SQS"
      statistic   = "Average"
      dimensions = {
        QueueName = aws_sqs_queue.worker_jobs.name
      }
    }
  }
}
```

**Key Points:**
- **Target tracking > Step scaling**: Research shows target tracking prevents oscillation for SQS
- **Cooldown periods**: Longer scale-in (10 min) prevents thrashing, shorter scale-out (1 min) for responsiveness
- **Messages per task**: Better metric than absolute queue size (adapts to current capacity)
- **Division by zero**: Use `MAX([tasks, 1])` to prevent division by zero when no tasks running

**Sources:**
- Auto Scaling Policies: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/appautoscaling_policy
- SQS Scaling Best Practices: https://elasticscale.com/blog/autoscale-ecs-with-sqs-queue-why-target-tracking-beats-step-scaling/
- Research: "ECS Autoscaling Based on SQS Queue Depth using Terraform"

---

### 10. SQS Queue Configuration

```hcl
resource "aws_sqs_queue" "worker_jobs" {
  name                       = "pharma-test-gen-worker-jobs"
  delay_seconds              = 0
  max_message_size           = 262144  # 256 KB
  message_retention_seconds  = 86400   # 1 day
  receive_wait_time_seconds  = 10      # Long polling
  visibility_timeout_seconds = 900     # 15 minutes (matches worker timeout)

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.worker_jobs_dlq.arn
    maxReceiveCount     = 3  # Retry 3 times before DLQ
  })

  tags = {
    Component = "queue"
    GAMP5     = "true"
  }
}

resource "aws_sqs_queue" "worker_jobs_dlq" {
  name                       = "pharma-test-gen-worker-jobs-dlq"
  message_retention_seconds  = 1209600  # 14 days

  tags = {
    Component = "dlq"
    GAMP5     = "true"
  }
}

# CloudWatch Alarm - DLQ Monitoring
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "worker-dlq-messages"
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
    QueueName = aws_sqs_queue.worker_jobs_dlq.name
  }

  alarm_actions = [var.sns_alarm_topic_arn]  # Send to SNS for notification
}
```

**Sources:**
- Reference: `examples/alex/terraform/6_agents/main.tf` (SQS configuration)

---

### 11. GAMP-5 Compliance Considerations

#### Immutable Infrastructure

1. **ECR immutable tags**: Prevents tag overwrites, ensures audit trail
2. **Terraform state**: Version-controlled infrastructure changes
3. **Task definition revisions**: ECS tracks all revisions, no in-place updates

#### Audit Trail

1. **CloudWatch Logs**: All container stdout/stderr captured with timestamps
2. **CloudWatch Container Insights**: Task-level metrics for performance auditing
3. **Terraform state**: Infrastructure changes tracked in S3 with versioning
4. **ECS deployment events**: All service updates logged to EventBridge

#### Error Handling

**NO FALLBACK LOGIC COMPLIANCE:**
- Health checks FAIL task if endpoint returns non-200
- Deployment circuit breaker ROLLS BACK failed deployments (no silent failures)
- SQS DLQ captures failed messages (no retry loops hiding errors)
- CloudWatch alarms ALERT on DLQ messages (explicit error notification)

#### Lifecycle Management

```hcl
# Prevent accidental service deletion
resource "aws_ecs_service" "api" {
  # ... other configuration

  lifecycle {
    prevent_destroy = var.environment == "production" ? true : false
    ignore_changes  = [desired_count]  # Auto scaling manages this
  }
}

# Prevent accidental ALB deletion
resource "aws_lb" "api" {
  # ... other configuration

  enable_deletion_protection = var.environment == "production" ? true : false
}
```

---

### 12. Module Structure Recommendation

```
aws/terraform/
├── main.tf                     # Root module
├── variables.tf                # Input variables
├── outputs.tf                  # Output values
├── versions.tf                 # Provider version constraints
├── backend.tf                  # S3 backend configuration (from Task 0.3)
│
├── modules/
│   ├── ecr/                    # ECR repositories
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   ├── ecs-cluster/            # ECS cluster with Container Insights
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   ├── ecs-service/            # Reusable ECS service module
│   │   ├── main.tf             # Service, task definition, auto scaling
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   ├── alb/                    # Application Load Balancer
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   └── sqs/                    # SQS queues
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
└── environments/
    ├── staging.tfvars          # Staging environment variables
    └── production.tfvars       # Production environment variables
```

**Rationale:**
- **Modular design**: Reuse ECS service module for API, Worker, Frontend
- **Environment separation**: Different tfvars files for staging/production
- **DRY principle**: Don't repeat yourself (3 services share same patterns)

---

### 13. Implementation Order

**CRITICAL**: Follow this order to avoid dependency issues.

1. **VPC/Networking** (assume already exists from earlier task)
2. **IAM Roles** (task execution + task roles)
3. **ECR Repositories** (create repos, push images)
4. **ECS Cluster** (with Container Insights)
5. **CloudWatch Log Groups** (create before task definitions reference them)
6. **Security Groups** (API, Worker, Frontend, ALB)
7. **SQS Queues** (main queue + DLQ)
8. **ALB + Target Groups** (API and Frontend)
9. **ECS Task Definitions** (API, Worker, Frontend)
10. **ECS Services** (API, Worker, Frontend)
11. **Auto Scaling Targets** (register services)
12. **Auto Scaling Policies** (CPU, Memory, SQS)
13. **CloudWatch Alarms** (DLQ monitoring)

**Terraform Dependency Management:**

```hcl
# Example: API service depends on ALB listener
resource "aws_ecs_service" "api" {
  # ... configuration

  depends_on = [
    aws_lb_listener.api_https,
    aws_iam_role_policy.api_task_policy,
    aws_cloudwatch_log_group.api
  ]
}
```

---

### 14. Common Issues and Solutions

#### Issue 1: Task Fails to Start - "CannotPullContainerError"

**Cause**: Task execution role lacks ECR permissions OR image doesn't exist.

**Solution:**
1. Verify task execution role has `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, etc.
2. Verify image exists in ECR: `aws ecr describe-images --repository-name pharma-test-gen-api`
3. Verify image tag matches task definition: `image = "${ecr_url}:v1.2.3"`

#### Issue 2: Task Fails to Start - "ResourceInitializationError: unable to pull secrets"

**Cause**: Task execution role lacks Secrets Manager permissions.

**Solution:**
1. Add `secretsmanager:GetSecretValue` to task execution role
2. Verify secret ARN is correct in task definition
3. Verify secret exists: `aws secretsmanager get-secret-value --secret-id <arn>`

#### Issue 3: Auto Scaling Not Working

**Cause**: `lifecycle.ignore_changes = [desired_count]` missing OR cooldown too long.

**Solution:**
1. Add lifecycle block to ECS service:
   ```hcl
   lifecycle {
     ignore_changes = [desired_count]
   }
   ```
2. Reduce cooldown periods (test with 60s scale-out, 300s scale-in)
3. Verify metrics publishing to CloudWatch (Container Insights enabled?)

#### Issue 4: "InvalidParameterException: Network Configuration must be provided when networkMode is 'awsvpc'"

**Cause**: Task definition has `network_mode = "awsvpc"` but service missing `network_configuration`.

**Solution:**
```hcl
resource "aws_ecs_service" "api" {
  # ...
  network_configuration {
    subnets          = data.aws_subnets.private.ids
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = false
  }
}
```

#### Issue 5: ALB Health Checks Failing

**Cause**: Security group doesn't allow ALB → Task traffic OR health check path wrong.

**Solution:**
1. Verify security group ingress:
   ```hcl
   ingress {
     from_port       = 8080
     to_port         = 8080
     protocol        = "tcp"
     security_groups = [aws_security_group.alb.id]  # NOT cidr_blocks
   }
   ```
2. Verify health check path matches app: `/health` (FastAPI) or `/api/health` (Next.js)
3. Check health check grace period (API: 60s, Frontend: 90s for Next.js startup)

#### Issue 6: Terraform Drift - "desired_count has changed"

**Cause**: Auto scaling modified desired_count, Terraform wants to revert.

**Solution:**
```hcl
lifecycle {
  ignore_changes = [desired_count]
}
```

#### Issue 7: "InvalidParameterException: Invalid CPU or memory value"

**Cause**: Invalid Fargate CPU/memory combination.

**Solution:** Use valid combinations (see table in section 5).
- Example: CPU=2048 requires Memory between 4096-16384

---

### 15. Testing Strategy

**Per task file requirements:**

1. **Terraform Plan in CI:**
   ```bash
   terraform plan -lock=false -out=plan.tfplan
   terraform show -json plan.tfplan | jq
   ```

2. **Deploy to Staging Workspace:**
   ```bash
   terraform workspace new staging
   terraform apply -var-file=environments/staging.tfvars
   ```

3. **Validate Health Checks:**
   ```bash
   # API
   curl -f https://<api-alb-dns>/health

   # Frontend
   curl -f https://<frontend-alb-dns>/api/health
   ```

4. **Test SQS Scaling:**
   ```bash
   # Send 100 messages to queue
   for i in {1..100}; do
     aws sqs send-message \
       --queue-url <queue-url> \
       --message-body "{\"job_id\": \"test-$i\"}"
   done

   # Watch auto scaling
   watch -n 5 'aws ecs describe-services \
     --cluster pharma-test-gen-cluster \
     --services pharma-test-gen-worker \
     | jq ".services[0].desiredCount"'
   ```

5. **Verify Container Insights:**
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace ECS/ContainerInsights \
     --metric-name CpuUtilized \
     --dimensions Name=ClusterName,Value=pharma-test-gen-cluster \
     --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
     --period 60 \
     --statistics Average
   ```

---

### 16. Required Libraries and Versions

**Terraform:**
- Terraform CLI: `>= 1.5.0`
- AWS Provider: `~> 5.0` (NOT `>= 5.0` to prevent major version upgrades)

**AWS Resources:**
- ECS Platform Version: `LATEST` (Fargate)
- ECR Image Tag: Use semantic versioning (e.g., `v1.2.3`)
- Python Runtime: `3.12` (from Dockerfiles)
- Node.js Runtime: `20` (from Dockerfile.frontend)

**No Python/Node packages needed for Terraform** (infrastructure only).

---

## Next Agent Guidance

**For task-executor:**

### 1. Pre-Implementation Checklist

- [ ] Verify Task 0.3 (Terraform Backend) is complete
- [ ] Verify Task 0.4 (IAM Roles) is complete
- [ ] Verify Task 3.1 (Dockerfiles) exist at project root
- [ ] Verify VPC exists with private/public subnets
- [ ] Verify ACM certificate exists for HTTPS (or create self-signed for testing)
- [ ] Collect required variables: `aurora_cluster_arn`, `aurora_secret_arn`, `vector_bucket`, etc.

### 2. Implementation Steps

1. **Create directory structure:**
   ```bash
   mkdir -p aws/terraform/modules/{ecr,ecs-cluster,ecs-service,alb,sqs}
   ```

2. **Start with ECR repositories** (simple, no dependencies)
   - Create `modules/ecr/main.tf` with 3 repositories (API, Worker, Frontend)
   - Add lifecycle policies
   - Test: `terraform plan -target=module.ecr`

3. **Create ECS cluster** with Container Insights
   - Create `modules/ecs-cluster/main.tf`
   - Test: `terraform plan -target=module.ecs_cluster`

4. **Create IAM roles** (task execution + 3 task roles)
   - Use inline policies (NOT separate aws_iam_policy resources to avoid ARN dependencies)
   - Test each role independently

5. **Create networking resources:**
   - Security groups (API, Worker, Frontend, ALB)
   - Reference existing VPC/subnets via data sources

6. **Create SQS queues** (main + DLQ)

7. **Create ALBs + Target Groups** (API and Frontend)
   - Start with HTTP listeners only (HTTPS requires ACM cert)

8. **Create ECS task definitions:**
   - API first (simplest, no Bedrock dependencies)
   - Frontend second
   - Worker last (most complex permissions)

9. **Create ECS services:**
   - API service with ALB integration
   - Frontend service with ALB integration
   - Worker service (no ALB)

10. **Create auto scaling:**
    - Start with CPU/Memory target tracking (simpler)
    - Add SQS scaling for Worker last

11. **Add CloudWatch alarms** for DLQ monitoring

### 3. Testing Commands

```bash
# Validate syntax
terraform fmt -recursive
terraform validate

# Plan with staging variables
terraform plan -var-file=environments/staging.tfvars

# Apply incrementally (NOT all at once)
terraform apply -target=module.ecr
terraform apply -target=module.ecs_cluster
# ... etc.

# Final full apply
terraform apply -var-file=environments/staging.tfvars
```

### 4. Variables to Parameterize

**Required:**
- `aws_region` (default: `eu-west-2`)
- `environment` (`staging`, `production`)
- `aurora_cluster_arn` (from Task 4.2)
- `aurora_secret_arn` (from Task 4.2)
- `vector_bucket` (from S3 Vectors task)
- `output_bucket` (for test suite storage)
- `bedrock_region` (for DeepSeek V3 access)

**Optional (with defaults):**
- `api_cpu` (default: `2048`)
- `api_memory` (default: `4096`)
- `worker_cpu` (default: `4096`)
- `worker_memory` (default: `8192`)
- `frontend_cpu` (default: `512`)
- `frontend_memory` (default: `1024`)
- `api_desired_count` (default: `2`)
- `worker_desired_count` (default: `1`)
- `frontend_desired_count` (default: `2`)

### 5. Key Files to Create

**Root Module:**
- `aws/terraform/main.tf` (module invocations)
- `aws/terraform/variables.tf` (input variables)
- `aws/terraform/outputs.tf` (ALB DNS, ECR URLs)
- `aws/terraform/versions.tf` (provider versions)
- `aws/terraform/backend.tf` (S3 backend from Task 0.3)

**Environment Variables:**
- `aws/terraform/environments/staging.tfvars`
- `aws/terraform/environments/production.tfvars`

**Modules (complete code in each):**
- `modules/ecr/main.tf`
- `modules/ecs-cluster/main.tf`
- `modules/ecs-service/main.tf` (reusable for API/Worker/Frontend)
- `modules/alb/main.tf`
- `modules/sqs/main.tf`

### 6. Critical Reminders

**NO FALLBACK LOGIC:**
- ❌ DO NOT set default values for missing secrets
- ❌ DO NOT mask ECR pull errors with local images
- ❌ DO NOT ignore health check failures
- ✅ FAIL EXPLICITLY with clear error messages
- ✅ USE deployment circuit breaker for auto rollback

**GAMP-5 Compliance:**
- ✅ Use immutable ECR tags
- ✅ Enable Container Insights
- ✅ Configure CloudWatch Logs with retention
- ✅ Add GAMP5=true tags to all resources

**Terraform Best Practices:**
- ✅ Pin provider version: `version = "~> 5.0"`
- ✅ Use lifecycle blocks to prevent drift
- ✅ Add explicit `depends_on` for complex dependencies
- ✅ Test incrementally with `-target`

---

## Files Referenced

### Documentation Sources

1. **Terraform AWS Provider Documentation**
   - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_task_definition
   - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_service
   - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/appautoscaling_policy
   - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_repository
   - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group

2. **AWS Official Documentation**
   - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html
   - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html
   - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html
   - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-networking.html
   - https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/deploy-container-insights-ECS-cluster.html

3. **Research Articles**
   - "ECS Autoscaling Based on SQS Queue Depth using Terraform" (https://chineloobitube.medium.com)
   - "Autoscale ECS with SQS Queue: Why Step Scaling Leads to Disaster" (https://elasticscale.com)
   - "Build a Production-Grade AWS ECS Fargate Cluster with Terraform" (https://medium.com/@neamulkabiremon)

### Local Project Files

1. **Reference Examples:**
   - `examples/alex/terraform/6_agents/main.tf` (IAM roles, SQS patterns)
   - `examples/alex/terraform/7_frontend/main.tf` (App Runner patterns, NOT ECS but useful for ALB)

2. **Dockerfiles (Task 3.1):**
   - `Dockerfile.api` (FastAPI with health check)
   - `Dockerfile.worker` (background worker, no health check)
   - `Dockerfile.frontend` (Next.js with standalone output)

3. **Task Files:**
   - `PRPs/tasks/4.1-terraform-ecs-deploy.md` (task requirements)
   - `PRPs/tasks/0.3-terraform-backend.md` (backend configuration)
   - `PRPs/tasks/0.4-iam-roles.md` (IAM setup)
   - `PRPs/tasks/3.1-docker-multistage.md` (Docker images)

---

## Summary

This research provides complete Terraform patterns for deploying a GAMP-5 compliant pharmaceutical test generation system on AWS ECS Fargate. Key deliverables:

1. **Complete infrastructure code examples** for ECS cluster, task definitions, services, ALB, auto scaling
2. **IAM role patterns** distinguishing task execution vs task roles
3. **Auto scaling strategies** for CPU/Memory (API/Frontend) and SQS queue depth (Worker)
4. **GAMP-5 compliance patterns** (immutable tags, audit trails, explicit errors)
5. **Implementation order** preventing dependency issues
6. **Testing strategy** matching task file requirements
7. **Common issues and solutions** for faster debugging

The task-executor has everything needed to implement Task 4.1 without external research or assumptions.

**STATUS**: Research complete. Ready for task-executor implementation.
