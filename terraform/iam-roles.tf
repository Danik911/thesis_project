# IAM Roles for Phase 0
# Task 0.4 - Create Baseline IAM Roles and Policies

# ============================================
# 1. Deployment Role (GitHub Actions CI/CD)
# ============================================

resource "aws_iam_role" "deploy" {
  name               = "${var.project_name}-deploy"
  description        = "Role for GitHub Actions to deploy infrastructure and applications"
  assume_role_policy = data.aws_iam_policy_document.github_oidc_assume.json

  tags = merge(
    var.tags,
    {
      Name    = "${var.project_name}-deploy"
      Purpose = "CI/CD Deployment Automation"
    }
  )
}

# Trust policy for GitHub Actions OIDC
data "aws_iam_policy_document" "github_oidc_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    actions = ["sts:AssumeRoleWithWebIdentity"]

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_org}/${var.github_repo}:ref:refs/heads/${var.github_branch}"]
    }
  }
}

# ============================================
# 2. ECS Task Execution Role
# ============================================

resource "aws_iam_role" "ecs_execution" {
  name               = "${var.project_name}-ecs-execution"
  description        = "Role for ECS to pull images from ECR and write logs to CloudWatch"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json

  tags = merge(
    var.tags,
    {
      Name    = "${var.project_name}-ecs-execution"
      Purpose = "ECS Task Execution - Image Pull and Logging"
    }
  )
}

# Trust policy for ECS tasks
data "aws_iam_policy_document" "ecs_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# Attach AWS managed policy for ECS task execution
resource "aws_iam_role_policy_attachment" "ecs_execution_policy" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ============================================
# 3. ECS Task Runtime Role
# ============================================

resource "aws_iam_role" "ecs_task" {
  name               = "${var.project_name}-ecs-task"
  description        = "Role for ECS tasks to access S3, SQS, Bedrock, and Secrets Manager"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json

  tags = merge(
    var.tags,
    {
      Name    = "${var.project_name}-ecs-task"
      Purpose = "ECS Task Runtime - Application Permissions"
    }
  )
}
