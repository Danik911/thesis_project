output "user_pool_id" {
  description = "Cognito User Pool ID (use for BI_COGNITO_USER_POOL_ID)"
  value       = aws_cognito_user_pool.bi.id
}

output "user_pool_client_id" {
  description = "Cognito User Pool Client ID (use for BI_COGNITO_CLIENT_ID)"
  value       = aws_cognito_user_pool_client.bi_frontend.id
}

output "user_pool_arn" {
  description = "Cognito User Pool ARN"
  value       = aws_cognito_user_pool.bi.arn
}

output "user_pool_domain" {
  description = "Cognito User Pool Domain"
  value       = aws_cognito_user_pool_domain.bi.domain
}

output "region" {
  description = "AWS region where Cognito is deployed"
  value       = var.region
}

output "env_vars_backend" {
  description = "Backend environment variables to set"
  value = {
    BI_AUTH_ENABLED          = "true"
    BI_COGNITO_REGION        = var.region
    BI_COGNITO_USER_POOL_ID  = aws_cognito_user_pool.bi.id
    BI_COGNITO_CLIENT_ID     = aws_cognito_user_pool_client.bi_frontend.id
  }
}

output "env_vars_frontend" {
  description = "Frontend environment variables to set"
  value = {
    NEXT_PUBLIC_BI_AUTH_ENABLED          = "true"
    NEXT_PUBLIC_BI_COGNITO_USER_POOL_ID  = aws_cognito_user_pool.bi.id
    NEXT_PUBLIC_BI_COGNITO_CLIENT_ID     = aws_cognito_user_pool_client.bi_frontend.id
    NEXT_PUBLIC_BI_COGNITO_REGION        = var.region
  }
}
