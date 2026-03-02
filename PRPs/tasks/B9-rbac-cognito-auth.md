# Task B9 — RBAC: Amazon Cognito Authentication & Role-Based Access Control

**Phase:** 6 (Security) | **Day:** 6-8
**Dependencies:** B1-B5 (all existing BI functionality must be stable)
**Branch:** `feature/mes-agentic-bi`
**Status:** TODO
**Estimated effort:** 3 days

---

## Objective

Add role-based access control (RBAC) to the MES Agentic BI application using Amazon Cognito. Two roles — Admin (full access, all sites) and Operator (site-filtered view, read-only later). Cognito User Pool with custom attributes (`custom:site`) provides JWT tokens. FastAPI validates tokens and injects user context. Frontend uses `aws-amplify` v6 for login + token management. Infrastructure defined in Terraform for reproducible deployment and client transfer.

**Phase 2 (future, out of scope):** AWS Glue Data Catalog + Lake Formation for centralized column/row-level data governance.

---

## Files to Create

| File | Purpose |
|------|---------|
| `mes-agentic-bi/src/bi/auth.py` | Cognito JWT validation, `get_current_user()`, `require_admin()` FastAPI dependencies |
| `mes-agentic-bi/src/bi/auth_models.py` | `BIUser`, `UserRole` Pydantic models |
| `mes-agentic-bi/terraform/main.tf` | Cognito User Pool, Client, Groups, custom attributes |
| `mes-agentic-bi/terraform/variables.tf` | Pool name, region, callback URLs, environment |
| `mes-agentic-bi/terraform/outputs.tf` | `user_pool_id`, `client_id` outputs |
| `mes-agentic-bi/terraform/providers.tf` | AWS provider with configurable region |
| `mes-agentic-bi/terraform/README.md` | Client transfer instructions |
| `mes-agentic-bi/scripts/seed_cognito_users.py` | Creates 3 test users: 1 Admin + 2 Operators (PlantA, PlantB) |
| `mes-agentic-bi/frontend/pages/login.tsx` | Login page (dark theme, cyan accent) |
| `mes-agentic-bi/frontend/lib/auth.tsx` | `AuthProvider` context, `useAuth` hook, Amplify v6 config |
| `mes-agentic-bi/frontend/lib/authenticatedFetch.ts` | Fetch wrapper attaching JWT header |
| `mes-agentic-bi/frontend/components/bi/UserBadge.tsx` | Top bar: user email, role badge, site, sign out |

## Files to Modify

| File | Change |
|------|--------|
| `mes-agentic-bi/src/bi/config.py` | Add `cognito_region`, `cognito_user_pool_id`, `cognito_client_id`, `auth_enabled`, `site_column_name`, `cors_origins` |
| `mes-agentic-bi/api/app.py` | Dynamic CORS origins when `BI_AUTH_ENABLED=true` |
| `mes-agentic-bi/api/bi_router.py` | Auth dependency on all endpoints, new `/bi/me` endpoint, site filtering, pass user to `create_session`/`chat` |
| `mes-agentic-bi/api/bi_voice_router.py` | Auth dependency on voice endpoints |
| `mes-agentic-bi/src/bi/session_store.py` | Add `user_id`, `user_role`, `user_site` to `BISession`; update `create_session()` |
| `mes-agentic-bi/src/bi/copilot.py` | Accept `BIUser` in `chat()`, add role context to system prompt |
| `mes-agentic-bi/pyproject.toml` | Add `python-jose[cryptography]`, `httpx` |
| `mes-agentic-bi/frontend/package.json` | Add `aws-amplify` v6 |
| `mes-agentic-bi/frontend/pages/_app.tsx` | Wrap with `AuthProvider` |
| `mes-agentic-bi/frontend/pages/agentic-bi.tsx` | Auth guard/redirect, `UserBadge`, token passing, hide Snowflake for Operators |
| `mes-agentic-bi/frontend/components/bi/ChatDrawer.tsx` | Use `authenticatedFetch` |
| `mes-agentic-bi/frontend/components/bi/ExportButtons.tsx` | Replace `window.open()` with authenticated blob download |
| `mes-agentic-bi/frontend/components/bi/SnowflakeBrowser.tsx` | Use `authenticatedFetch`, Admin-only visibility |
| `mes-agentic-bi/.env.example` | Add all new `BI_COGNITO_*` and `NEXT_PUBLIC_BI_*` vars |
| `mes-agentic-bi/docker-compose.yml` | Add Cognito env vars to both services |

---

## Implementation Details

### 1. Terraform — Cognito Infrastructure

- User Pool: `{env}-bi-user-pool`, self-signup disabled, email verification
- Password: 12+ chars, upper+lower+numbers+symbols
- Custom attributes: `custom:site` (String), `custom:role` (String)
- Client: SPA (no secret), SRP auth, 1h access/id token, 30d refresh
- Groups: `Admin`, `Operator`

### 2. Backend Auth — JWT Validation

- Fetch Cognito JWKS from `https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json`
- Validate RS256 JWT, check audience + issuer
- Extract `cognito:groups` → determine role (Admin > Operator)
- Extract `custom:site` → site for Operator filtering
- `BI_AUTH_ENABLED=false` (default) = no auth required, zero regression

### 3. Site Filtering (Critical RBAC)

- Applied at upload/load time, **before** `create_session()`
- Operator: `df[df[site_col] == user.site]`
- Missing Site column: return empty DataFrame (never leak data)
- All downstream operations automatically respect pre-filtered data

### 4. Session Ownership

- `BISession` stores `user_id`, `user_role`, `user_site`
- Operators can only access their own sessions
- Admins can access all sessions

### 5. Frontend Auth

- `aws-amplify` v6 (modular imports for tree-shaking)
- `AuthProvider` wraps app, provides `useAuth` hook
- `authenticatedFetch` adds `Authorization: Bearer {idToken}` to all API calls
- Login page with NEW_PASSWORD_REQUIRED handling
- Role-based UI: hide Snowflake tab for Operators

---

## Testing Strategy

```bash
# 1. Deploy Cognito
wsl -e bash -c "cd mes-agentic-bi/terraform && terraform init && terraform apply"

# 2. Seed test users
python mes-agentic-bi/scripts/seed_cognito_users.py <pool_id>

# 3. Get token
TOKEN=$(aws cognito-idp initiate-auth --client-id $CLIENT_ID --auth-flow USER_PASSWORD_AUTH --auth-parameters USERNAME=admin@test.com,PASSWORD='AdminPass123!@#' --query 'AuthenticationResult.IdToken' --output text)

# 4. Test /bi/me
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/bi/me

# 5. Test upload as Operator
TOKEN_OP=$(aws cognito-idp initiate-auth --client-id $CLIENT_ID --auth-flow USER_PASSWORD_AUTH --auth-parameters USERNAME=operator.planta@test.com,PASSWORD='OperatorA123!@#' --query 'AuthenticationResult.IdToken' --output text)
curl -X POST -H "Authorization: Bearer $TOKEN_OP" -F "file=@test_data.csv" http://localhost:8080/bi/upload
# Verify: only PlantA rows returned
```

---

## Gate Criteria (Pass/Fail)

- [ ] Terraform creates Cognito User Pool with groups and custom attributes
- [ ] `BI_AUTH_ENABLED=false` works identically to current (no regression)
- [ ] `BI_AUTH_ENABLED=true` requires valid JWT on all `/bi/*` endpoints
- [ ] Admin sees full dataset; Operator sees only their site's data
- [ ] Missing Site column for Operator returns empty grid (not all data)
- [ ] Session ownership enforced (Operator can't access other's sessions)
- [ ] Copilot system prompt includes role context
- [ ] Exports respect site filter
- [ ] Login page renders, handles first-login password challenge
- [ ] Token refresh works (session persists beyond 1h)
- [ ] No hardcoded Pool/Client IDs in source — all via env vars
- [ ] Client transfer requires only env var + tfvars changes
- [ ] Terraform README provides complete client setup guide
