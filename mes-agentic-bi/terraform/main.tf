# ---------------------------------------------------------------------------
# Cognito User Pool for MES Agentic BI RBAC
# ---------------------------------------------------------------------------

resource "aws_cognito_user_pool" "bi" {
  name = "${var.environment}-${var.pool_name}"

  # Self-signup disabled — admin creates users (internal tool)
  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  # Password policy
  password_policy {
    minimum_length                   = var.password_minimum_length
    require_uppercase                = true
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7
  }

  # Email verification
  auto_verified_attributes = ["email"]

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Custom attributes
  schema {
    name                = "site"
    attribute_data_type = "String"
    mutable             = true

    string_attribute_constraints {
      min_length = 0
      max_length = 256
    }
  }

  schema {
    name                = "role"
    attribute_data_type = "String"
    mutable             = true

    string_attribute_constraints {
      min_length = 0
      max_length = 64
    }
  }

  # Username configuration — use email as username
  username_configuration {
    case_sensitive = false
  }

  username_attributes = ["email"]

  tags = {
    Environment = var.environment
    Project     = "mes-agentic-bi"
    ManagedBy   = "terraform"
  }
}

# ---------------------------------------------------------------------------
# User Pool Domain (required for hosted UI, optional for custom flows)
# ---------------------------------------------------------------------------

resource "aws_cognito_user_pool_domain" "bi" {
  domain       = "${var.environment}-${var.pool_name}"
  user_pool_id = aws_cognito_user_pool.bi.id
}

# ---------------------------------------------------------------------------
# User Pool Client (SPA — no client secret)
# ---------------------------------------------------------------------------

resource "aws_cognito_user_pool_client" "bi_frontend" {
  name         = "${var.environment}-bi-frontend"
  user_pool_id = aws_cognito_user_pool.bi.id

  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
  ]

  # Token validity
  access_token_validity  = 60
  id_token_validity      = 60
  refresh_token_validity = 30

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }

  # OAuth settings
  callback_urls                = var.callback_urls
  logout_urls                  = var.logout_urls
  allowed_oauth_flows          = ["code"]
  allowed_oauth_scopes         = ["openid", "email", "profile"]
  supported_identity_providers = ["COGNITO"]

  allowed_oauth_flows_user_pool_client = true

  # Read custom attributes in tokens
  read_attributes = [
    "email",
    "email_verified",
    "custom:site",
    "custom:role",
  ]

  write_attributes = [
    "email",
    "custom:site",
    "custom:role",
  ]
}

# ---------------------------------------------------------------------------
# User Groups
# ---------------------------------------------------------------------------

resource "aws_cognito_user_group" "admin" {
  name         = "Admin"
  user_pool_id = aws_cognito_user_pool.bi.id
  description  = "Full access to all sites and all features"
}

resource "aws_cognito_user_group" "operator" {
  name         = "Operator"
  user_pool_id = aws_cognito_user_pool.bi.id
  description  = "Read-only access, site-filtered data"
}
