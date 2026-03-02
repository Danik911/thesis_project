# AWS Migration Runbook (Client Account)

## Phase 1 — Preparation

- Confirm target domain(s) and callback/logout URLs.
- Confirm client site column name for RBAC filtering (`BI_SITE_COLUMN_NAME`).
- Confirm deployment owners for backend and frontend env vars.

Inputs:
- [mes-agentic-bi/terraform/terraform.tfvars.example](../../mes-agentic-bi/terraform/terraform.tfvars.example)
- [mes-agentic-bi/.env.example](../../mes-agentic-bi/.env.example)

## Phase 2 — Terraform Deployment

From WSL (project policy):

```bash
wsl -e bash -c "cd mes-agentic-bi/terraform && terraform init"
wsl -e bash -c "cd mes-agentic-bi/terraform && terraform plan"
wsl -e bash -c "cd mes-agentic-bi/terraform && terraform apply"
```

Capture outputs:
- `user_pool_id`
- `user_pool_client_id`
- `region`

References:
- [mes-agentic-bi/terraform/README.md](../../mes-agentic-bi/terraform/README.md)
- [mes-agentic-bi/terraform/outputs.tf](../../mes-agentic-bi/terraform/outputs.tf)

## Phase 3 — Runtime Configuration

### Backend
Set and deploy:
- `BI_AUTH_ENABLED=true`
- `BI_COGNITO_REGION`
- `BI_COGNITO_USER_POOL_ID`
- `BI_COGNITO_CLIENT_ID`
- `BI_SITE_COLUMN_NAME`
- `BI_CORS_ORIGINS`

### Frontend
Set and deploy:
- `NEXT_PUBLIC_BI_AUTH_ENABLED=true`
- `NEXT_PUBLIC_BI_COGNITO_REGION`
- `NEXT_PUBLIC_BI_COGNITO_USER_POOL_ID`
- `NEXT_PUBLIC_BI_COGNITO_CLIENT_ID`

References:
- [mes-agentic-bi/src/bi/config.py](../../mes-agentic-bi/src/bi/config.py)
- [mes-agentic-bi/api/app.py](../../mes-agentic-bi/api/app.py)
- [mes-agentic-bi/frontend/lib/auth.tsx](../../mes-agentic-bi/frontend/lib/auth.tsx)

## Phase 4 — User Provisioning

Option A: Scripted seeding

```bash
python mes-agentic-bi/scripts/seed_cognito_users.py <pool_id> <region>
```

Option B: Manual Cognito console provisioning
- Add groups: `Admin`, `Operator`
- Set operator `custom:site`

References:
- [mes-agentic-bi/scripts/seed_cognito_users.py](../../mes-agentic-bi/scripts/seed_cognito_users.py)

## Phase 5 — Security and Functional Validation

Execute all pass/fail checks in:
- [validation-acceptance.md](./validation-acceptance.md)
- [mes-agentic-bi/terraform/CLIENT_HANDOVER_CHECKLIST.md](../../mes-agentic-bi/terraform/CLIENT_HANDOVER_CHECKLIST.md)

## Phase 6 — Sign-off and Handover

- Package required artifacts listed in [delivery-package-checklist.md](./delivery-package-checklist.md)
- Conduct joint review with client
- Record final acceptance evidence
