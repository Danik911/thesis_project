# ISSUE-016: LIMS Upload Dropzone Accessibility Lint Failure

**Date:** 2026-02-17  
**Status:** Resolved  
**Category:** Frontend  
**Priority:** Medium

---

## Symptom

`npm run build` failed in `main/frontend` due to accessibility lint errors on `pages/lims.tsx`:

- `jsx-a11y/click-events-have-key-events`
- `jsx-a11y/no-static-element-interactions`

The upload dropzone used a clickable `<div>` without keyboard interaction support.

## Affected Files

| File | Area |
|------|------|
| `main/frontend/pages/lims.tsx` | PDF upload dropzone interaction |

---

## Root Cause

The dropzone was implemented with mouse-only interaction (`onClick`) on a non-interactive element, which violates accessibility requirements enforced by Next.js lint rules.

---

## Resolution

Added keyboard accessibility to the upload dropzone while preserving drag-and-drop behavior:

- Added `role="button"`
- Added `tabIndex={0}`
- Added `onKeyDown` handler to trigger file picker on `Enter` and `Space`

---

## Files Modified

| File | Change |
|------|--------|
| `main/frontend/pages/lims.tsx` | Added keyboard-accessible interaction support for the upload dropzone |

---

## Prevention Guidance

1. Any clickable non-native interactive element must include keyboard interaction.
2. Prefer native interactive elements where practical.
3. Run targeted lint checks on updated pages before full build validation.
