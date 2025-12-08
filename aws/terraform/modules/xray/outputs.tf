output "sampling_rule_arn" {
  value = aws_xray_sampling_rule.main.arn
}

output "api_group_arn" {
  value = aws_xray_group.api.arn
}

output "worker_group_arn" {
  value = aws_xray_group.worker.arn
}
