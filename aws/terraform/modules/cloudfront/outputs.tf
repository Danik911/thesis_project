# =============================================================================
# CloudFront Module Outputs
# =============================================================================

output "distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.this.id
}

output "distribution_arn" {
  description = "CloudFront distribution ARN"
  value       = aws_cloudfront_distribution.this.arn
}

output "domain_name" {
  description = "CloudFront distribution domain name (e.g., d2yiysdqio0ryi.cloudfront.net)"
  value       = aws_cloudfront_distribution.this.domain_name
}

output "hosted_zone_id" {
  description = "CloudFront distribution hosted zone ID (for Route 53 alias records)"
  value       = aws_cloudfront_distribution.this.hosted_zone_id
}

output "status" {
  description = "CloudFront distribution status"
  value       = aws_cloudfront_distribution.this.status
}

output "url" {
  description = "Full HTTPS URL of the CloudFront distribution"
  value       = "https://${aws_cloudfront_distribution.this.domain_name}"
}
