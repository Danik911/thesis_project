output "zone_id" {
  description = "Route 53 hosted zone ID"
  value       = local.zone_id
}

output "zone_name_servers" {
  description = "Name servers for the hosted zone"
  value       = var.create_hosted_zone ? aws_route53_zone.main[0].name_servers : []
}

output "api_fqdn" {
  description = "API fully qualified domain name"
  value       = aws_route53_record.api.fqdn
}

output "frontend_fqdn" {
  description = "Frontend fully qualified domain name"
  value       = aws_route53_record.frontend.fqdn
}

output "root_fqdn" {
  description = "Root domain fully qualified domain name"
  value       = var.create_root_record ? aws_route53_record.root[0].fqdn : null
}
