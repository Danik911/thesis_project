# Handover Overview

## Objective

Transfer MES Agentic BI B9 RBAC capability (Cognito-based Admin/Operator access model) to the client AWS account with reproducible infrastructure, secure runtime configuration, and validated authorization behavior.

## Functional Components in Scope

### Infrastructure
- Cognito User Pool, app client, user groups, and custom attributes
- Terraform-driven deployment and client-editable variable template

References:
- [mes-agentic-bi/terraform/main.tf](../../mes-agentic-bi/terraform/main.tf)
- [mes-agentic-bi/terraform/variables.tf](../../mes-agentic-bi/terraform/variables.tf)
- [mes-agentic-bi/terraform/providers.tf](../../mes-agentic-bi/terraform/providers.tf)
- [mes-agentic-bi/terraform/outputs.tf](../../mes-agentic-bi/terraform/outputs.tf)
- [mes-agentic-bi/terraform/terraform.tfvars.example](../../mes-agentic-bi/terraform/terraform.tfvars.example)

### Backend Security
- Cognito JWT validation and role extraction
- Endpoint authorization and session ownership boundaries
- Operator site-scoped filtering

References:
- [mes-agentic-bi/src/bi/auth.py](../../mes-agentic-bi/src/bi/auth.py)
- [mes-agentic-bi/src/bi/auth_models.py](../../mes-agentic-bi/src/bi/auth_models.py)
- [mes-agentic-bi/api/bi_router.py](../../mes-agentic-bi/api/bi_router.py)
- [mes-agentic-bi/api/bi_voice_router.py](../../mes-agentic-bi/api/bi_voice_router.py)
- [mes-agentic-bi/src/bi/session_store.py](../../mes-agentic-bi/src/bi/session_store.py)

### Frontend Security Integration
- Amplify auth provider and token-aware API wrapper
- Login and password challenge flow
- Role-aware UI visibility controls

References:
- [mes-agentic-bi/frontend/lib/auth.tsx](../../mes-agentic-bi/frontend/lib/auth.tsx)
- [mes-agentic-bi/frontend/lib/authenticatedFetch.ts](../../mes-agentic-bi/frontend/lib/authenticatedFetch.ts)
- [mes-agentic-bi/frontend/pages/login.tsx](../../mes-agentic-bi/frontend/pages/login.tsx)
- [mes-agentic-bi/frontend/components/bi/UserBadge.tsx](../../mes-agentic-bi/frontend/components/bi/UserBadge.tsx)
- [mes-agentic-bi/frontend/pages/agentic-bi.tsx](../../mes-agentic-bi/frontend/pages/agentic-bi.tsx)

## Key Security Guarantees to Demonstrate

1. Auth-disabled mode (`BI_AUTH_ENABLED=false`) remains non-regressive.
2. Auth-enabled mode requires valid JWT for `/bi/*`.
3. Operators are site-restricted and session-restricted.
4. Snowflake routes are backend Admin-only.
5. Voice routes enforce session ownership.

## Dependencies

- B9 task baseline: [PRPs/tasks/B9-rbac-cognito-auth.md](../../PRPs/tasks/B9-rbac-cognito-auth.md)
- Hardening record: [docs/issues/ISSUE-041-mes-bi-rbac-hardening-and-client-handover-gaps.md](../issues/ISSUE-041-mes-bi-rbac-hardening-and-client-handover-gaps.md)

## PingFederate SSO Migration (B10)

The B9 Cognito baseline is the handover artifact for generic AWS deployments. For Pfizer's production environment, authentication switches from Cognito to **PingFederate** via the **POS Home** gateway at `pos.pfizer.com`.

Key decisions confirmed post-meeting:

- No Snowflake RLS — app-level site filtering (`_apply_site_filter()`) is sufficient.
- Auth provider changes from Cognito JWT to PingFederate opaque access_token.
- POS Home handles login and delivers a validated user object (NTID, groups, tokens) to the app.
- PoC: all authenticated users receive Admin role. Group-based RBAC is a follow-up.
- AD group naming: `GBH-dev-agenticbi-<site>-<product>-<role>`.

Full migration instructions: [pingfederate-migration-plan.md](./pingfederate-migration-plan.md)

Backend files affected:
- [mes-agentic-bi/src/bi/auth.py](../../mes-agentic-bi/src/bi/auth.py) — add PingFederate introspection path
- [mes-agentic-bi/src/bi/config.py](../../mes-agentic-bi/src/bi/config.py) — add `BI_PINGFED_*` settings

Frontend files affected:
- [mes-agentic-bi/frontend/lib/auth.tsx](../../mes-agentic-bi/frontend/lib/auth.tsx) — replace Amplify with POS Home token reader
- [mes-agentic-bi/frontend/lib/authenticatedFetch.ts](../../mes-agentic-bi/frontend/lib/authenticatedFetch.ts) — pull token from POS Home context

## Exit Criteria

Use [validation-acceptance.md](./validation-acceptance.md) as the pass/fail gate for handover acceptance.
