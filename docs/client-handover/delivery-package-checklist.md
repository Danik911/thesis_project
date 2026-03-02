# Delivery Package Checklist

Use this checklist to ensure all handover artifacts are delivered in one package.

## 1) Documentation

- [ ] [docs/client-handover/README.md](./README.md)
- [ ] [docs/client-handover/handover-overview.md](./handover-overview.md)
- [ ] [docs/client-handover/aws-migration-runbook.md](./aws-migration-runbook.md)
- [ ] [docs/client-handover/validation-acceptance.md](./validation-acceptance.md)
- [ ] [docs/client-handover/delivery-package-checklist.md](./delivery-package-checklist.md)
- [ ] [mes-agentic-bi/terraform/README.md](../../mes-agentic-bi/terraform/README.md)
- [ ] [mes-agentic-bi/terraform/CLIENT_HANDOVER_CHECKLIST.md](../../mes-agentic-bi/terraform/CLIENT_HANDOVER_CHECKLIST.md)

## 2) Infrastructure Artifacts

- [ ] [mes-agentic-bi/terraform/providers.tf](../../mes-agentic-bi/terraform/providers.tf)
- [ ] [mes-agentic-bi/terraform/variables.tf](../../mes-agentic-bi/terraform/variables.tf)
- [ ] [mes-agentic-bi/terraform/main.tf](../../mes-agentic-bi/terraform/main.tf)
- [ ] [mes-agentic-bi/terraform/outputs.tf](../../mes-agentic-bi/terraform/outputs.tf)
- [ ] [mes-agentic-bi/terraform/terraform.tfvars.example](../../mes-agentic-bi/terraform/terraform.tfvars.example)

## 3) Runtime Config Templates

- [ ] [mes-agentic-bi/.env.example](../../mes-agentic-bi/.env.example)
- [ ] Backend env matrix (client-specific values)
- [ ] Frontend env matrix (client-specific values)

## 4) Security Evidence

- [ ] JWT validation evidence (`/bi/me` with valid and invalid token)
- [ ] Operator site filtering evidence
- [ ] Session ownership enforcement evidence
- [ ] Snowflake admin-only enforcement evidence
- [ ] Voice session ownership enforcement evidence

## 5) Traceability Links

- [ ] B9 spec: [PRPs/tasks/B9-rbac-cognito-auth.md](../../PRPs/tasks/B9-rbac-cognito-auth.md)
- [ ] Hardening issue: [docs/issues/ISSUE-041-mes-bi-rbac-hardening-and-client-handover-gaps.md](../issues/ISSUE-041-mes-bi-rbac-hardening-and-client-handover-gaps.md)
- [ ] Catalog: [docs/issues/ISSUE-CATALOG.md](../issues/ISSUE-CATALOG.md)

## 6) Operational Ownership

- [ ] Client AWS owner assigned
- [ ] Client app owner assigned
- [ ] Rollback owner assigned
- [ ] Incident escalation contacts documented
