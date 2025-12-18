# =============================================================================
# RDS PostgreSQL Module
# =============================================================================
# Purpose: Persistent job storage for pharmaceutical test generation
# Lifecycle: Destroyed/recreated with infrastructure (non-production)
# Cost: ~$13/month (db.t3.micro)
#
# This module creates:
# - RDS PostgreSQL instance (db.t3.micro)
# - Security group allowing ECS tasks to connect
# - Secrets Manager secret with DATABASE_URL
# - DB subnet group for VPC deployment

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0"
    }
  }
}

# -----------------------------------------------------------------------------
# Random Password for Database
# -----------------------------------------------------------------------------

resource "random_password" "db_password" {
  length  = 32
  special = false # Avoid special chars that may cause connection string issues
}

# -----------------------------------------------------------------------------
# DB Subnet Group
# -----------------------------------------------------------------------------

resource "aws_db_subnet_group" "main" {
  name        = "${var.project_name}-db-subnet"
  description = "Subnet group for ${var.project_name} RDS instance"
  subnet_ids  = var.subnet_ids

  tags = {
    Name        = "${var.project_name}-db-subnet"
    Environment = var.environment
    Project     = var.project_name
  }
}

# -----------------------------------------------------------------------------
# Security Group for RDS
# -----------------------------------------------------------------------------

resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  description = "Security group for ${var.project_name} RDS PostgreSQL"
  vpc_id      = var.vpc_id

  # Allow inbound from ECS tasks
  ingress {
    description     = "PostgreSQL from ECS tasks"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.ecs_security_group_ids
  }

  # Allow all outbound (for updates, etc.)
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-rds-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

# -----------------------------------------------------------------------------
# RDS Parameter Group
# -----------------------------------------------------------------------------

resource "aws_db_parameter_group" "postgres" {
  name        = "${var.project_name}-postgres-params-v2" # Changed name to force recreation
  family      = "postgres16"
  description = "Parameter group for ${var.project_name} PostgreSQL"

  # Enable pg_stat_statements for query performance monitoring
  # NOTE: shared_preload_libraries is a static parameter - requires DB restart
  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }

  # Log slow queries (> 1 second)
  parameter {
    name         = "log_min_duration_statement"
    value        = "1000"
    apply_method = "immediate"
  }

  tags = {
    Name        = "${var.project_name}-postgres-params"
    Environment = var.environment
    Project     = var.project_name
  }

  lifecycle {
    create_before_destroy = true
  }
}

# -----------------------------------------------------------------------------
# RDS PostgreSQL Instance
# -----------------------------------------------------------------------------

resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-postgres"

  # Engine configuration
  engine               = "postgres"
  engine_version       = "16.6" # Latest available in eu-west-2
  instance_class       = var.instance_class
  parameter_group_name = aws_db_parameter_group.postgres.name

  # Storage configuration
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  # Database configuration
  db_name  = var.database_name
  username = var.database_username
  password = random_password.db_password.result

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  multi_az               = false # Single-AZ for staging (cost savings)

  # Backup configuration (minimal for staging)
  backup_retention_period = var.backup_retention_days
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # Staging-specific settings
  skip_final_snapshot      = true
  delete_automated_backups = true
  deletion_protection      = false
  apply_immediately        = true

  # Performance Insights (free tier)
  performance_insights_enabled = false

  tags = {
    Name        = "${var.project_name}-postgres"
    Environment = var.environment
    Project     = var.project_name
  }
}

# -----------------------------------------------------------------------------
# Secrets Manager Secret for DATABASE_URL
# -----------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "database_url" {
  name                    = "${var.project_name}/database-url-rds"
  description             = "DATABASE_URL for ${var.project_name} RDS PostgreSQL"
  recovery_window_in_days = 0 # Immediate deletion for staging

  tags = {
    Name        = "${var.project_name}-database-url"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id = aws_secretsmanager_secret.database_url.id

  # Format: postgresql://user:password@host:port/database
  secret_string = "postgresql://${var.database_username}:${random_password.db_password.result}@${aws_db_instance.main.endpoint}/${var.database_name}"
}
