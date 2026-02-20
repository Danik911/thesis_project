# ISSUE-036: LIMS Extract 401 from Duplicate `LIMS_LLAMAEXTRACT_API_KEY` in `.env.local`

## Date
2026-02-19

## Status
RESOLVED (2026-02-19)

## Symptom
`POST /lims/extract` returned:

`Pipeline failed: ApiError: status_code: 401, body: {'detail': 'Invalid API Key. Please check your region ...'}`

while `POST /lims/classify` succeeded.

## Root Cause
`.env.local` contained two `LIMS_LLAMAEXTRACT_API_KEY` entries. The first entry was a placeholder value and took precedence when environment was loaded, causing LlamaExtract authentication to fail.

## Files Modified

| File | Change |
|------|--------|
| `.env.local` | Removed placeholder `LIMS_LLAMAEXTRACT_API_KEY=llx-placeholder` to keep only the real key |

## Validation
- Confirmed exactly one `LIMS_LLAMAEXTRACT_API_KEY` remains in `.env.local`.
- API restart is required for the corrected env value to be loaded.

## Prevention Guidance
- Keep one definition per key in `.env.local`.
- Avoid placeholder production-like keys in active env files.
- Add periodic env key duplication checks during local troubleshooting.
