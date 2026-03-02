# MES Agentic BI — Client AWS Handover Checklist (B9 RBAC)

Use this checklist to migrate Cognito RBAC to the client AWS account with predictable outcomes.

## 1) Preconditions

- [ ] Client AWS account access is available (Terraform apply permissions for Cognito).
- [ ] Target domain(s) for BI frontend are finalized.
- [ ] Backend and frontend deployment pipelines can inject environment variables.
- [ ] `BI_SITE_COLUMN_NAME` value is confirmed with client dataset schema (default: `Site`).

## 2) Terraform Deployment (Client Account)

- [ ] Copy `terraform.tfvars.example` to `terraform.tfvars`.
- [ ] Set `environment`, `region`, `callback_urls`, and `logout_urls` for client domain.
- [ ] Run:
  - [ ] `terraform init`
  - [ ] `terraform plan`
  - [ ] `terraform apply`
- [ ] Record outputs:
  - [ ] `user_pool_id`
  - [ ] `user_pool_client_id`
  - [ ] `region`

## 3) Application Configuration

### Backend
- [ ] Set:
  - [ ] `BI_AUTH_ENABLED=true`
  - [ ] `BI_COGNITO_REGION=<terraform region>`
  - [ ] `BI_COGNITO_USER_POOL_ID=<terraform output>`
  - [ ] `BI_COGNITO_CLIENT_ID=<terraform output>`
  - [ ] `BI_SITE_COLUMN_NAME=<client site column>`
  - [ ] `BI_CORS_ORIGINS=<frontend URL(s)>`

### Frontend
- [ ] Set:
  - [ ] `NEXT_PUBLIC_BI_AUTH_ENABLED=true`
  - [ ] `NEXT_PUBLIC_BI_COGNITO_REGION=<terraform region>`
  - [ ] `NEXT_PUBLIC_BI_COGNITO_USER_POOL_ID=<terraform output>`
  - [ ] `NEXT_PUBLIC_BI_COGNITO_CLIENT_ID=<terraform output>`

## 4) User and Group Provisioning

- [ ] Create/seed users in Cognito User Pool.
- [ ] Verify groups exist and are assigned correctly:
  - [ ] `Admin`
  - [ ] `Operator`
- [ ] Verify Operators have `custom:site` populated.
- [ ] Optional local seed command:
  - [ ] `python scripts/seed_cognito_users.py <pool_id> <region>`

## 5) Security Validation (Pass/Fail)

- [ ] Auth disabled mode still works:
  - [ ] `BI_AUTH_ENABLED=false` allows existing PoC behavior.
- [ ] Auth enabled mode requires JWT:
  - [ ] Unauthenticated `/bi/*` requests are rejected.
- [ ] `/bi/me` returns authenticated user context.
- [ ] Site filtering works:
  - [ ] Admin sees all rows.
  - [ ] Operator sees only rows where `BI_SITE_COLUMN_NAME == custom:site`.
  - [ ] If site column is missing, Operator gets empty dataset.
- [ ] Session ownership works:
  - [ ] Operator cannot access another user’s session IDs.
  - [ ] Voice endpoints also enforce session ownership.
- [ ] Snowflake routes are backend admin-only:
  - [ ] Operator gets `403` on `/bi/snowflake/*`.

## 6) Frontend Validation

- [ ] Login page works with Cognito (`/login`).
- [ ] NEW_PASSWORD_REQUIRED flow works.
- [ ] Role badge and site label render correctly.
- [ ] Operator cannot see Snowflake tab in UI.
- [ ] Exports and chat work with authenticated token flow.

## 7) Handover Package to Client

- [ ] `terraform/` folder with state excluded from transfer.
- [ ] Environment variable matrix (backend + frontend).
- [ ] Test accounts policy (or IAM/Cognito onboarding SOP).
- [ ] Evidence bundle:
  - [ ] Terraform apply output
  - [ ] API auth/RBAC curl evidence
  - [ ] UI screenshots for Admin and Operator

## 8) Rollback Plan

- [ ] Keep `BI_AUTH_ENABLED=false` toggle documented for emergency fallback to non-auth mode.
- [ ] Preserve prior deployment image tags and env snapshots.
- [ ] Document `terraform destroy` ownership/approval process.
