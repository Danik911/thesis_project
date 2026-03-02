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

## Exit Criteria

Use [validation-acceptance.md](./validation-acceptance.md) as the pass/fail gate for handover acceptance.
