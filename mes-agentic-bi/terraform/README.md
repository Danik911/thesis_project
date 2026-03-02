# MES Agentic BI — Cognito RBAC Infrastructure

Terraform configuration for Amazon Cognito User Pool with role-based access control.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.5.0
- IAM permissions for Cognito operations

## Quick Start (Development)

```bash
cd mes-agentic-bi/terraform

# Initialize Terraform
terraform init

# Review changes
terraform plan

# Apply (creates Cognito User Pool, Client, Groups)
terraform apply

# Get outputs for env vars
terraform output
```

## Client Deployment

1. Copy `terraform.tfvars.example` to `terraform.tfvars`
2. Edit values for your environment:

```hcl
environment    = "production"
pool_name      = "bi-user-pool"
region         = "eu-west-1"          # Your AWS region
callback_urls  = ["https://bi.your-domain.com/agentic-bi"]
logout_urls    = ["https://bi.your-domain.com/login"]
```

3. Run `terraform init && terraform apply`
4. Copy output values to your `.env` files (see `terraform output env_vars_backend` and `terraform output env_vars_frontend`)
5. Execute the handover runbook in `CLIENT_HANDOVER_CHECKLIST.md`

## Creating Users

After Terraform apply, create users with the seed script:

```bash
python scripts/seed_cognito_users.py <user_pool_id> [region]
```

Or create users manually in the AWS Console:
1. Go to Amazon Cognito > User Pools > select your pool
2. Click "Create user"
3. Set email, temporary password
4. After creation, add to group (Admin or Operator)
5. For Operators, set `custom:site` attribute to their site name

## Environment Variables

### Backend (.env)
```
BI_AUTH_ENABLED=true
BI_COGNITO_REGION=eu-west-1
BI_COGNITO_USER_POOL_ID=<from terraform output>
BI_COGNITO_CLIENT_ID=<from terraform output>
BI_SITE_COLUMN_NAME=Site
BI_CORS_ORIGINS=https://bi.your-domain.com
```

### Frontend (.env)
```
NEXT_PUBLIC_BI_AUTH_ENABLED=true
NEXT_PUBLIC_BI_COGNITO_USER_POOL_ID=<from terraform output>
NEXT_PUBLIC_BI_COGNITO_CLIENT_ID=<from terraform output>
NEXT_PUBLIC_BI_COGNITO_REGION=eu-west-1
```

## Destroying Resources

```bash
terraform destroy
```

This removes the Cognito User Pool and all associated users/groups.

## Handover Artifacts

- `terraform.tfvars.example` — client-editable Terraform variable template
- `CLIENT_HANDOVER_CHECKLIST.md` — end-to-end migration and validation checklist
