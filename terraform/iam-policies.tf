# IAM Policies for Phase 0 Roles
# Task 0.4 - Least-Privilege Policies

# ============================================
# 1. Deploy Role Policy
# ============================================

resource "aws_iam_role_policy" "deploy" {
  name   = "${var.project_name}-deploy-permissions"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.deploy_permissions.json
}

data "aws_iam_policy_document" "deploy_permissions" {
  # ECR - Push and manage images
  statement {
    sid    = "ECRFullAccess"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:DescribeRepositories",
      "ecr:DescribeImages",
      "ecr:ListImages"
    ]
    resources = ["*"]
  }

  # ECS - Deploy services and tasks
  statement {
    sid    = "ECSDeployment"
    effect = "Allow"
    actions = [
      "ecs:UpdateService",
      "ecs:DescribeServices",
      "ecs:DescribeTasks",
      "ecs:DescribeTaskDefinition",
      "ecs:RegisterTaskDefinition",
      "ecs:DeregisterTaskDefinition",
      "ecs:ListTasks",
      "ecs:ListTaskDefinitions",
      "ecs:CreateService",
      "ecs:DeleteService"
    ]
    resources = ["*"]

    condition {
      test     = "StringLike"
      variable = "aws:ResourceTag/Project"
      values   = ["Pharmaceutical Test Generation"]
    }
  }

  # IAM - Pass roles to ECS
  statement {
    sid    = "PassRoleToECS"
    effect = "Allow"
    actions = [
      "iam:PassRole"
    ]
    resources = [
      aws_iam_role.ecs_execution.arn,
      aws_iam_role.ecs_task.arn
    ]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["ecs-tasks.amazonaws.com"]
    }
  }

  # S3 - Deploy frontend to frontend bucket
  statement {
    sid    = "S3FrontendDeploy"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::${var.s3_buckets.frontend}",
      "arn:aws:s3:::${var.s3_buckets.frontend}/*"
    ]
  }

  # Secrets Manager - Create/update secrets
  statement {
    sid    = "SecretsManagerAccess"
    effect = "Allow"
    actions = [
      "secretsmanager:CreateSecret",
      "secretsmanager:UpdateSecret",
      "secretsmanager:PutSecretValue",
      "secretsmanager:DescribeSecret"
    ]
    resources = ["arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${var.project_name}/*"]
  }

  # CloudWatch Logs - View deployment logs
  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
      "logs:GetLogEvents"
    ]
    resources = ["arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:/ecs/${var.project_name}*"]
  }
}

# ============================================
# 2. ECS Execution Role Additional Policy
# ============================================

resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name   = "${var.project_name}-ecs-execution-secrets"
  role   = aws_iam_role.ecs_execution.id
  policy = data.aws_iam_policy_document.ecs_execution_secrets.json
}

data "aws_iam_policy_document" "ecs_execution_secrets" {
  # Secrets Manager - Read secrets for environment variables
  statement {
    sid    = "ReadSecrets"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ]
    resources = ["arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${var.project_name}/*"]
  }

  # SSM Parameter Store - Read parameters
  statement {
    sid    = "ReadParameters"
    effect = "Allow"
    actions = [
      "ssm:GetParameters",
      "ssm:GetParameter"
    ]
    resources = ["arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/${var.project_name}/*"]
  }
}

# ============================================
# 3. ECS Task Runtime Policy
# ============================================

resource "aws_iam_role_policy" "ecs_task" {
  name   = "${var.project_name}-ecs-task-permissions"
  role   = aws_iam_role.ecs_task.id
  policy = data.aws_iam_policy_document.ecs_task_permissions.json
}

data "aws_iam_policy_document" "ecs_task_permissions" {
  # S3 - Read/Write to compliance and output buckets
  statement {
    sid    = "S3ComplianceBucketAccess"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::${var.s3_buckets.compliance}",
      "arn:aws:s3:::${var.s3_buckets.compliance}/*"
    ]
  }

  # SQS - Send/Receive messages
  statement {
    sid    = "SQSQueueAccess"
    effect = "Allow"
    actions = [
      "sqs:SendMessage",
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl"
    ]
    resources = ["arn:aws:sqs:${var.aws_region}:${var.aws_account_id}:${var.project_name}*"]
  }

  # Bedrock - Invoke DeepSeek model only
  statement {
    sid    = "BedrockModelInvocation"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"
    ]
    resources = ["arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_model_id}"]
  }

  # Secrets Manager - Read application secrets
  statement {
    sid    = "ReadApplicationSecrets"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ]
    resources = ["arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${var.project_name}/*"]
  }

  # CloudWatch - Put custom metrics
  statement {
    sid    = "CloudWatchMetrics"
    effect = "Allow"
    actions = [
      "cloudwatch:PutMetricData"
    ]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values   = ["${var.project_name}"]
    }
  }

  # CloudWatch Logs - Create and write logs
  statement {
    sid    = "CloudWatchLogsWrite"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:/ecs/${var.project_name}*"]
  }
}
