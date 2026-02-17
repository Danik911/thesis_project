# LIMS-004: Full HITL UI — Chat, Review Flow, Real-Time Updates, Export

**Date:** 2026-02-17
**Status:** Implementation complete, pending user verification
**Branch:** `prjoject_p_protatype`
**Task:** L6 (Phase 6 of AI4LIMS PoC)

---

## Summary

Transformed the simple upload+display LIMS page into a full demo-ready multi-step Human-In-The-Loop (HITL) workflow: Upload PDF -> AI Extraction -> MDA Table Review -> Chat Refinement -> Human Approval -> XLSX Export. This is the final UI phase of the AI4LIMS PoC.

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `main/frontend/components/LIMSStepIndicator.tsx` | Horizontal 5-stage pipeline indicator (EXTRACTING -> GENERATING -> PENDING_REVIEW -> APPROVED -> EXPORTED) | ~120 |
| `main/frontend/components/ChatInterface.tsx` | Chat panel for MDA refinement via POST /lims/chat with edit badges, suggestion chips, auto-scroll | ~260 |

## Files Modified

| File | Change |
|------|--------|
| `main/frontend/components/MDAViewer.tsx` | Added optional `highlightedCells?: Set<string>` and `title?: string` props for cell-level highlighting of chat edits (~15 lines) |
| `main/frontend/pages/lims.tsx` | Major rewrite from 297 to 641 lines — multi-step HITL flow with 6 conditional views, Framer Motion transitions, two-column review layout |

## Architecture

### State Machine (Frontend mirrors backend)
```
IDLE -> EXTRACTING -> GENERATING -> PENDING_REVIEW -> APPROVED -> EXPORTED
                                                          |
                                                        FAILED
```

### Conditional Views

| Status | View |
|--------|------|
| IDLE | Drag-drop PDF upload area + Extract button |
| EXTRACTING/GENERATING | Loading card with animated extraction stages + shimmer bar |
| PENDING_REVIEW | Summary bar + MDAViewer (3/5 cols) + ChatInterface (2/5 cols) + Approve button |
| APPROVED | Success banner + MDAViewer + Download XLSX button |
| EXPORTED | Success banner + MDAViewer + Download Again button |
| FAILED | Red error card with full error detail |

### Key Design Decisions

1. **Plain `fetch()`** — LIMS routes have no auth (not `authenticatedFetch`)
2. **No localStorage persistence** — PoC with in-memory backend, single-session
3. **`window.open()` for export** — triggers browser download directly from binary endpoint
4. **Defensive polling** — 3s interval during EXTRACTING/GENERATING (extract is synchronous so rarely fires)
5. **Framer Motion** — `AnimatePresence mode="wait"` for smooth view transitions

### Component Tree (Review State)
```
lims.tsx
  ├── LIMSStepIndicator (currentStatus)
  ├── Summary bar (filename, size, analyses count)
  ├── Grid (lg:grid-cols-5)
  │   ├── MDAViewer (col-span-3) — 4-tab table with highlighting
  │   └── ChatInterface (col-span-2) — chat + edit badges
  └── Approve button
```

## Backend Endpoints Used (all from L4)

| Endpoint | Method | Used By |
|----------|--------|---------|
| `/lims/extract` | POST | handleExtract — upload PDF, get job_id + mda_template |
| `/lims/status/{job_id}` | GET | Status polling (defensive) |
| `/lims/chat` | POST | ChatInterface — send message, get edits + updated MDA |
| `/lims/approve/{job_id}` | POST | handleApprove — HITL approval gate |
| `/lims/export/{job_id}` | GET | handleExport — download XLSX binary |

## Issues Encountered

No issues encountered during implementation. Frontend build passes cleanly with zero new errors or warnings.

## Verification Steps

1. Start backend: `uv run uvicorn main.api.app:app --port 8080`
2. Start frontend: `cd main/frontend && npm run dev`
3. Open http://localhost:3000/lims
4. Upload `demo_data/AND_ACS_DYE-LAB-2499.pdf`
5. See step indicator progress through extraction stages
6. See 4-tab MDA table in PENDING_REVIEW state
7. Send chat message, see response with edit badges, MDA table refreshes
8. Click "Approve MDA Template" -> step indicator advances to APPROVED
9. Click "Download XLSX" -> browser downloads file
10. Click "Start Over" -> return to upload view
11. Verify thesis pages still work: `/generate`, `/history`

## Dependencies

- `framer-motion` ^12.23.24 (already in package.json)
- `@heroicons/react` ^2.2.0 (already in package.json)
- No new packages required

## Next Steps

- User manual verification of full workflow
- L5 (backend E2E tests) completion by separate agent
- L7 (Docker packaging) if applicable
