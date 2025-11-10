# GitHub OIDC Provider for GitHub Actions
# Allows GitHub Actions to assume AWS IAM roles without long-lived credentials

data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com",
  ]

  thumbprint_list = [
    data.tls_certificate.github.certificates[0].sha1_fingerprint,
  ]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-github-oidc"
    }
  )
}

# Data source to reference the OIDC provider
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  depends_on = [aws_iam_openid_connect_provider.github]
}
