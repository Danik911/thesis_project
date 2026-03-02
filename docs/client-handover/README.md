# Client Handover Documentation

Central handover index for transferring the MES Agentic BI RBAC (B9) implementation to a client AWS environment.

## Scope

This package covers:
- Cognito RBAC infrastructure handover (B9 baseline)
- PingFederate SSO migration plan for Pfizer POS Home deployment (B10)
- Backend and frontend environment handover
- Security validation and acceptance criteria
- Delivery artifacts and sign-off evidence

## Start Here

1. [Handover Overview](./handover-overview.md)
2. [AWS Migration Runbook](./aws-migration-runbook.md)
3. [Snowflake Integration Guide](./snowflake-integration-guide.md)
4. [Validation and Acceptance](./validation-acceptance.md)
5. [Delivery Package Checklist](./delivery-package-checklist.md)
6. [PingFederate SSO Migration Plan](./pingfederate-migration-plan.md) — Pfizer POS Home integration (B10)

## Authoritative Source Links

- B9 task specification: [PRPs/tasks/B9-rbac-cognito-auth.md](../../PRPs/tasks/B9-rbac-cognito-auth.md)
- Terraform handover checklist (service-level): [mes-agentic-bi/terraform/CLIENT_HANDOVER_CHECKLIST.md](../../mes-agentic-bi/terraform/CLIENT_HANDOVER_CHECKLIST.md)
- Terraform module README: [mes-agentic-bi/terraform/README.md](../../mes-agentic-bi/terraform/README.md)
- Hardened implementation issue record: [docs/issues/ISSUE-041-mes-bi-rbac-hardening-and-client-handover-gaps.md](../issues/ISSUE-041-mes-bi-rbac-hardening-and-client-handover-gaps.md)
- Issue catalog: [docs/issues/ISSUE-CATALOG.md](../issues/ISSUE-CATALOG.md)

## Handover Outcome

Handover is considered ready when all items in [Validation and Acceptance](./validation-acceptance.md) and [Delivery Package Checklist](./delivery-package-checklist.md) are marked complete and verified by both teams.
