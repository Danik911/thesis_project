# =============================================================================
# RDS Module Outputs
# =============================================================================

output "endpoint" {
  description = "RDS instance endpoint (host:port)"
  value       = aws_db_instance.main.endpoint
}

output "address" {
  description = "RDS instance address (host only)"
  value       = aws_db_instance.main.address
}

output "port" {
  description = "RDS instance port"
  value       = aws_db_instance.main.port
}

output "database_name" {
  description = "Name of the database"
  value       = aws_db_instance.main.db_name
}

output "database_url_secret_arn" {
  description = "ARN of the Secrets Manager secret containing DATABASE_URL"
  value       = aws_secretsmanager_secret.database_url.arn
}

output "security_group_id" {
  description = "Security group ID for RDS instance"
  value       = aws_security_group.rds.id
}

output "db_instance_id" {
  description = "RDS instance identifier"
  value       = aws_db_instance.main.id
}
