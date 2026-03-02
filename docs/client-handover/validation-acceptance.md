# Validation and Acceptance (Pass/Fail)

Use this checklist for formal handover acceptance.

## A. Compatibility Gate

- [ ] Auth-disabled mode behaves like pre-RBAC baseline (`BI_AUTH_ENABLED=false`)
- [ ] No regression in upload, filter, chart, export, and chat workflows

## B. Authentication Gate

- [ ] Auth-enabled mode requires JWT on all `/bi/*` endpoints
- [ ] `/bi/me` returns accurate authenticated user context
- [ ] Invalid JWT is rejected with 401

References:
- [mes-agentic-bi/src/bi/auth.py](../../mes-agentic-bi/src/bi/auth.py)
- [mes-agentic-bi/api/bi_router.py](../../mes-agentic-bi/api/bi_router.py)

## C. Authorization Gate (RBAC)

- [ ] Admin can access all sites
- [ ] Operator is restricted to `custom:site`
- [ ] Missing site column for Operator returns empty dataset
- [ ] Operator cannot access another user session
- [ ] Snowflake routes reject Operator (`403`)
- [ ] Voice routes enforce session ownership (`403` for cross-session)

References:
- [mes-agentic-bi/api/bi_router.py](../../mes-agentic-bi/api/bi_router.py)
- [mes-agentic-bi/api/bi_voice_router.py](../../mes-agentic-bi/api/bi_voice_router.py)
- [mes-agentic-bi/src/bi/session_store.py](../../mes-agentic-bi/src/bi/session_store.py)

## D. Frontend Auth UX Gate

- [ ] Login renders correctly and routes unauthorized users to `/login`
- [ ] NEW_PASSWORD_REQUIRED flow completes successfully
- [ ] User badge shows email, role, and site (Operator)
- [ ] Operator UI does not expose Snowflake controls

References:
- [mes-agentic-bi/frontend/pages/login.tsx](../../mes-agentic-bi/frontend/pages/login.tsx)
- [mes-agentic-bi/frontend/pages/agentic-bi.tsx](../../mes-agentic-bi/frontend/pages/agentic-bi.tsx)
- [mes-agentic-bi/frontend/components/bi/UserBadge.tsx](../../mes-agentic-bi/frontend/components/bi/UserBadge.tsx)

## E. Evidence Gate

- [ ] Terraform plan/apply output archived
- [ ] API evidence (curl or Postman) for Admin and Operator scenarios archived
- [ ] UI screenshots for login, role badge, and restricted views archived
- [ ] Resolved hardening issue linked in handover notes

References:
- [docs/issues/ISSUE-041-mes-bi-rbac-hardening-and-client-handover-gaps.md](../issues/ISSUE-041-mes-bi-rbac-hardening-and-client-handover-gaps.md)

## Final Acceptance

- [ ] Client technical owner sign-off
- [ ] Delivery owner sign-off
- [ ] Production go-live date and rollback owner recorded
