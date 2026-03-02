## Decision Summary (Post-Meeting)

**Date of decision**: 2026-03-02

The following was confirmed with the Pfizer client after the meeting this document was prepared for:

| Decision | Outcome |
|----------|---------|
| Snowflake RLS | Not required. App-level filtering (`_apply_site_filter()`) is sufficient for PoC and production. |
| SSO Provider | PingFederate (by Ping Identity), not AWS IAM Identity Center. |
| Auth Gateway | POS Home (`pos.pfizer.com`) handles login and passes validated user object + tokens to embedded apps. |
| Token type | Opaque `access_token` (~30 min TTL) + `refresh_token`. Not a JWT — cannot be decoded locally. Must call PingFederate introspection endpoint. |
| User object | Contains: NTID, firstname, lastname, displayName, mail, domain, username, group[], tier_info, access_token, refresh_token. |
| PoC auth model | All authenticated users = Admin. Group-based RBAC is a follow-up (B10 scope). |
| Group naming | `GBH-dev-agenticbi-<site>-<product>-<role>` (e.g., `GBH-dev-agenticbi-gc-readonly`). |
| App embedding | App is a sub-route under POS Home (like `/yield`, `/anomaly`). POS Home routes `/agenticbi` to our app. |
| Next step | B10 task: PingFederate SSO migration. See [docs/client-handover/pingfederate-migration-plan.md](../../docs/client-handover/pingfederate-migration-plan.md). |

---

# Client Meeting Prep: RLS + AWS SSO Impact on RBAC

**Date**: 2026-02-27
**Context**: B9 (Cognito RBAC) is fully implemented with native Cognito auth (username/password) and app-level site filtering via `_apply_site_filter()` in `bi_router.py`. The client uses Snowflake RLS (Row-Level Security) and AWS SSO (IAM Identity Center). This document prepares for a meeting to understand how this affects our implementation.

**Current state**: All B9 code is written but untested. No Terraform applied, no npm packages installed.

---

## App Overview for Cloud Engineer

### What is this app?

**MES Agentic BI** is a web-based data analytics tool for manufacturing environments. It allows users to:
- **Upload** CSV/Excel files or **connect to Snowflake** to load production data
- **Explore data** in an interactive grid (filter, sort, search, paginate)
- **Chat with an AI copilot** that can apply filters, summarize data, and answer questions using natural language
- **Export** filtered data as PDF or Excel

### Architecture

```
┌────────────────┐     ┌─────────────────┐     ┌────────────────┐
│   Next.js      │────>│  FastAPI (Python)│────>│  Snowflake     │
│   Frontend     │ JWT │  Backend API     │ SQL │  (client data) │
│   (port 3000)  │     │  (port 8080)     │     │                │
└────────────────┘     └─────────────────┘     └────────────────┘
                              │
                              v
                       ┌─────────────────┐
                       │  Amazon Cognito  │
                       │  (User Pool)     │
                       │  JWT validation  │
                       └─────────────────┘
```

- **Frontend**: Next.js (React), runs on port 3000
- **Backend**: FastAPI (Python), runs on port 8080
- **Data**: Snowflake (client-provided) or uploaded CSV/Excel files
- **Auth**: Amazon Cognito User Pool — issues JWTs, validates on every API call
- **AI Copilot**: AWS Bedrock (Claude) for natural language data queries
- **Deployment**: Docker containers (can run on ECS, EC2, or any Docker host)

### What we built for RBAC (already done)

| Layer | What | How |
|-------|------|-----|
| **Auth** | Amazon Cognito User Pool | Terraform-managed. 2 groups: `Admin`, `Operator`. Custom attribute: `custom:site` |
| **Backend** | JWT validation on every API endpoint | Extracts role + site from Cognito JWT claims |
| **Site filtering** | Operators see only their site's data | DataFrame filtered by `custom:site` value matching a configurable column (default: `Site`) |
| **Session ownership** | Operators can't access other users' sessions | Session metadata tracks `user_id` |
| **Frontend** | Login page, role-based UI | Admin sees all features; Operator has restricted view |

### What we need from infrastructure (from the cloud engineer)

1. **SSO Integration**: If client uses AWS SSO (IAM Identity Center), we need:
   - SAML metadata URL or XML file
   - List of user attributes available via SAML assertions (email, groups, site/department)
   - ACS (Assertion Consumer Service) URL will be provided by us after Cognito setup

2. **Snowflake RLS**: If client has Row-Level Security:
   - How is user context passed? (session variable name, Snowflake role, `CURRENT_USER()`)
   - Service account credentials for the app, OR confirmation that individual users provide their own Snowflake credentials
   - The RLS policy SQL (so we can verify our integration matches)

3. **Network / Deployment**:
   - Where will the app be deployed? (ECS, EC2, on-prem Docker)
   - VPC / subnet for Snowflake connectivity (private link?)
   - Domain name + SSL certificate for the frontend (needed for Cognito callback URLs)
   - Any firewall rules or IP allowlisting needed?

---

## Meeting Questions (Copy-Paste Ready)

### 1. AWS SSO / Identity

| # | Question | Why It Matters |
|---|----------|----------------|
| 1a | **Which SSO identity provider do you use?** (AWS IAM Identity Center, Azure AD, Okta, ADFS, other) | Determines SAML vs OIDC federation config in Cognito |
| 1b | **Do you want users to log in via your corporate SSO portal?** (i.e., no separate username/password for the BI app) | If yes, we add SAML federation to Cognito. If no, we keep native Cognito users |
| 1c | **What user attributes does your SSO provide?** (email, groups, department, site/location, role) | We need to map SSO claims to Cognito attributes (`custom:site`, `cognito:groups`) |
| 1d | **How are roles (Admin vs Operator) determined?** (SSO group membership, directory attribute, manual assignment) | Determines whether we use Cognito groups or map from SSO groups |
| 1e | **How is a user's site/plant determined?** (SSO attribute, directory field, manually assigned per user) | Critical for RLS — this maps to the `custom:site` attribute used for data filtering |

### 2. Snowflake RLS

| # | Question | Why It Matters |
|---|----------|----------------|
| 2a | **Do you use Snowflake Row Access Policies?** (i.e., `CREATE ROW ACCESS POLICY`) | Confirms database-level RLS exists |
| 2b | **How does RLS determine which rows a user sees?** (Snowflake role, session variable, `CURRENT_USER()`) | Determines how we pass user context to Snowflake |
| 2c | **Does the BI app connect to Snowflake with a shared service account or individual user accounts?** | Service account + session variable = we set context per-query. Individual accounts = RLS uses `CURRENT_USER()` |
| 2d | **If service account: what session variable does the RLS policy check?** (e.g., `CURRENT_SITE`, `CURRENT_CUSTOMER_ID`) | We need to `ALTER SESSION SET <variable> = '<user_site>'` before each query |
| 2e | **Which tables/views have RLS policies applied?** (all, specific tables, specific schemas) | Determines if we can rely entirely on RLS or still need app-level filtering for some data |
| 2f | **What happens if no session variable is set?** (see all data, see nothing, error) | Critical for security — we need to know the fail-safe behavior |

### 3. Integration

| # | Question | Why It Matters |
|---|----------|----------------|
| 3a | **Is there SCIM provisioning between your SSO and Snowflake?** (auto user/group sync) | If yes, Snowflake users already mirror SSO identities |
| 3b | **Do you want CSV/Excel uploads to also respect site filtering?** (or is it Snowflake-only) | Determines if we keep app-level `_apply_site_filter()` for uploads |
| 3c | **Can you share: (1) your SSO SAML metadata XML, (2) the Snowflake RLS policy SQL, (3) the session variable name?** | We need these to configure the integration |
| 3d | **What are the callback URLs for the BI app?** (production domain, staging, etc.) | Needed for Cognito/SSO redirect configuration |

---

## Impact Analysis: What Changes Per Scenario

### Scenario A: AWS SSO Federation (most likely)

**What changes in our B9 implementation:**

| File | Change |
|------|--------|
| `terraform/main.tf` | Add `aws_cognito_identity_provider` resource (SAML type) with client's metadata URL + attribute mapping |
| `terraform/variables.tf` | Add `saml_metadata_url`, `saml_provider_name` variables |
| `terraform/main.tf` (client resource) | Add `supported_identity_providers` to user pool client, add OAuth `code` flow + callback/logout URLs |
| `frontend/lib/auth.tsx` | Add "Sign in with SSO" button that triggers `signInWithRedirect({ provider: 'IdentityCenter' })` via Amplify |
| `frontend/pages/login.tsx` | Add SSO button alongside (or replacing) username/password form |
| `src/bi/auth.py` | **No change** — JWT validation stays the same. Cognito issues the JWT regardless of whether user logged in natively or via SAML |
| `src/bi/auth_models.py` | **No change** — claims structure is the same |
| `api/bi_router.py` | **No change** — `_apply_site_filter()` still works (reads `user.site` from JWT) |

**Key insight**: SSO federation is mostly a **Terraform + frontend login page** change. The backend auth (JWT validation, role extraction, site filtering) is **unchanged** because Cognito normalizes all identities into the same JWT format.

**Attribute mapping concern**: If the SSO provides site info as `department` or `location`, we map it to `custom:site` in Cognito's SAML attribute mapping. If SSO provides groups like `BI-Admin` / `BI-Operator`, we can map them to Cognito groups via a [Lambda pre-token-generation trigger](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html).

### Scenario B: Snowflake RLS with Service Account

**What changes:**

| File | Change |
|------|--------|
| `src/bi/snowflake_connector.py` | Before each query, execute `ALTER SESSION SET <rls_variable> = '<user_site>'`. After query, reset to `NULL` |
| `api/bi_router.py` | Pass `user.site` to Snowflake connector functions. **Keep** `_apply_site_filter()` as defense-in-depth |
| `src/bi/config.py` | Add `snowflake_rls_variable` setting (e.g., `BI_SNOWFLAKE_RLS_VAR=CURRENT_SITE`) |
| `.env.example` | Add `BI_SNOWFLAKE_RLS_VAR` |
| `frontend/components/bi/SnowflakeBrowser.tsx` | May remove per-user credential fields if using service account (credentials come from env vars) |

**Snowflake connector change** (conceptual):
```python
# Before query
cursor.execute(f"ALTER SESSION SET {rls_variable} = %s", (user_site,))
# Execute query — RLS automatically filters rows
result = cursor.execute("SELECT * FROM table").fetch_pandas_all()
# Reset context
cursor.execute(f"ALTER SESSION UNSET {rls_variable}")
```

**Important**: Even with Snowflake RLS, we should **keep** `_apply_site_filter()` for CSV/Excel uploads (no RLS there).

### Scenario C: Snowflake RLS with Individual User Accounts

**What changes:**

| File | Change |
|------|--------|
| `frontend/components/bi/SnowflakeBrowser.tsx` | Keep as-is — users provide their own Snowflake credentials |
| `src/bi/snowflake_connector.py` | **No change** — RLS applies automatically via `CURRENT_USER()` |
| `api/bi_router.py` | `_apply_site_filter()` becomes redundant for Snowflake data (RLS handles it). **Keep it** for uploads |

This is the simplest scenario — minimal code changes.

### Scenario D: Both SSO + Snowflake RLS (Combined)

Combine changes from Scenario A + B (or A + C). The SSO provides identity; Snowflake RLS provides data filtering. Our app-level filtering becomes defense-in-depth.

---

## Implementation Plan (Post-Meeting)

After the meeting, based on answers, we add these changes **on top of** existing B9 code:

### Step 1: SSO Federation (if confirmed)
1. Get SAML metadata XML/URL from client
2. Add `aws_cognito_identity_provider` to Terraform
3. Add attribute mapping (SSO claims -> Cognito attributes)
4. If needed: Lambda pre-token-generation trigger for group mapping
5. Update login page with SSO redirect button
6. Test: SSO login -> JWT -> backend validates -> correct role/site

### Step 2: Snowflake RLS Integration (if confirmed)
1. Get RLS policy details + session variable name from client
2. Update `snowflake_connector.py` to set session variable before queries
3. Add `BI_SNOWFLAKE_RLS_VAR` config setting
4. If service account: add `BI_SNOWFLAKE_*` env vars for shared credentials
5. Test: query with different user contexts -> verify row filtering

### Step 3: Keep Defense-in-Depth
- **Keep** `_apply_site_filter()` for CSV uploads (no database RLS there)
- **Keep** session ownership validation
- **Keep** copilot RBAC context in system prompt

---

## Verification Checklist

1. **SSO flow**: Corporate login -> redirect -> Cognito JWT -> app access with correct role/site
2. **Snowflake RLS**: Query as Admin -> all rows. Query as Operator -> only their site's rows (at DB level)
3. **CSV upload**: Still app-level filtered (RLS doesn't apply to in-memory DataFrames)
4. **Fallback**: `BI_AUTH_ENABLED=false` still works for local dev (no regression)
