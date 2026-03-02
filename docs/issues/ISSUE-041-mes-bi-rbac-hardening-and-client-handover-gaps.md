# ISSUE-041: MES Agentic BI RBAC Hardening and Client Handover Gaps

## Date
2026-02-27

## Symptom
B9 Cognito RBAC implementation exists but has hardening and handover gaps before client AWS migration:

1. Snowflake endpoints are hidden in UI for Operators but not admin-enforced on backend.
2. Voice endpoints are authenticated but do not enforce session ownership checks.
3. Frontend uses `aws-amplify` APIs without declaring dependency in `frontend/package.json`.
4. Terraform README references `terraform.tfvars.example`, but the template file is missing.
5. No explicit client handover migration checklist exists for Cognito + env + validation transfer.

## Error Messages / Indicators
- Potential privilege bypass risk: Operator could call `/bi/snowflake/*` routes directly.
- Dependency install drift risk: runtime/build failure when `aws-amplify` is not installed.
- Transfer friction risk: incomplete Terraform handover template and checklist.

## Affected Files
- `mes-agentic-bi/api/bi_router.py`
- `mes-agentic-bi/api/bi_voice_router.py`
- `mes-agentic-bi/frontend/package.json`
- `mes-agentic-bi/terraform/README.md`
- `mes-agentic-bi/terraform/` (missing tfvars template/checklist docs)

## Root Cause
Security controls were partially implemented in UI/auth wiring, but server-side authorization boundaries for sensitive routes and client-transfer artifacts were not fully completed.

## Files Modified

| File | Purpose |
|------|---------|
| `mes-agentic-bi/api/bi_router.py` | Enforce backend Admin-only authorization on all Snowflake routes when `BI_AUTH_ENABLED=true` |
| `mes-agentic-bi/api/bi_voice_router.py` | Enforce session ownership checks for voice session/TTS endpoints |
| `mes-agentic-bi/frontend/package.json` | Add missing `aws-amplify` runtime dependency |
| `mes-agentic-bi/terraform/README.md` | Reference handover artifacts and execution order |
| `mes-agentic-bi/terraform/terraform.tfvars.example` | Add client-editable Terraform variable template |
| `mes-agentic-bi/terraform/CLIENT_HANDOVER_CHECKLIST.md` | Add end-to-end migration checklist for client AWS transfer |

## Code Changes (Before / After)

### 1) Snowflake authorization boundary

**Before:**
- Snowflake routes required authentication but did not require Admin role server-side.
- Operator users could potentially call `/bi/snowflake/*` endpoints directly.

**After:**
- Added `_require_admin_when_auth_enabled()` and invoked it in all Snowflake endpoints:
	- `/bi/snowflake/tables`
	- `/bi/snowflake/stages/{stage_name}/files`
	- `/bi/snowflake/load/table`
	- `/bi/snowflake/load/stage-file`
- When auth is enabled, non-admin requests fail with `403`.

### 2) Voice endpoint session ownership

**Before:**
- Voice routes validated session existence but did not enforce session ownership.

**After:**
- Added `_validate_voice_session_access()`:
	- Admin can access all sessions.
	- Operator can access only sessions where `session.user_id == user.sub`.
- Applied to:
	- `POST /bi/voice/session/{session_id}`
	- `POST /bi/voice/tts/{session_id}`

### 3) Frontend dependency completeness

**Before:**
- `frontend/lib/auth.tsx` used `aws-amplify` imports without package declaration.

**After:**
- Added `"aws-amplify": "^6.15.7"` to `mes-agentic-bi/frontend/package.json`.

### 4) Terraform transfer artifacts

**Before:**
- `terraform/README.md` referenced `terraform.tfvars.example`, but file was missing.
- No dedicated migration handover checklist.

**After:**
- Added `terraform/terraform.tfvars.example`.
- Added `terraform/CLIENT_HANDOVER_CHECKLIST.md`.
- Updated `terraform/README.md` to reference both artifacts.

## Validation Performed

- IDE diagnostics: no new errors in:
	- `mes-agentic-bi/api/bi_router.py`
	- `mes-agentic-bi/api/bi_voice_router.py`

## Prevention Guidance

1. Keep all sensitive feature gating enforced server-side even when UI hides controls.
2. Require ownership checks on any endpoint that accepts `session_id`.
3. Treat dependency declaration as part of feature completion criteria.
4. For infrastructure handover tasks, require both:
	 - a `terraform.tfvars.example` template, and
	 - a migration checklist with pass/fail validation steps.

## Resolution Status
Resolved on 2026-02-27.
