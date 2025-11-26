# Current Task Context: 3.14

## Task File
PRPs/tasks/3.14-frontend-approval-ui.md

## Active Task
**Task ID:** 3.14
**Task Name:** Frontend - Human Approval UI (Next.js Pages Router)
**Phase:** 3 - Containerization
**Status:** in-progress
**Priority:** CRITICAL - User-facing interface for Human-in-the-Loop approval workflow
**Started:** 2025-11-24 20:42:27

---

## Task Objective
Build Next.js Pages Router frontend components to display approval requests, collect human decisions with justifications, and integrate with Clerk authentication for ALCOA+ compliant digital signatures. Match architecture from `examples/alex/frontend/` (Pages Router, Clerk v6).

## Key Requirements
1. Display AI categorization with confidence score and ambiguity reason
2. Show approval form with decision options (APPROVE/REJECT/REQUEST_REVISION)
3. Allow category override if human disagrees with AI
4. Require justification (minimum 10 characters for audit trail)
5. Pre-fill digital signature from Clerk JWT
6. Poll job status every 5 seconds for real-time updates
7. Match `examples/alex/frontend/` architecture (Pages Router, Clerk v6)

## Success Criteria

### ApprovalModal Component
1. Display AI categorization result (category, confidence, ambiguity reason, alternatives, reasoning)
2. Approval form fields (decision select, category override, justification textarea, signature)
3. Form validation (min 10 chars justification, valid category)

### Job Status Polling
4. Poll GET /jobs/{job_id}/status every 5 seconds
5. Detect AWAITING_APPROVAL status
6. Show ApprovalModal automatically when approval required
7. Display countdown timer for timeout (1 hour)

### Job Status Display
8. Job list badge: "⏳ Awaiting Approval"
9. Show ambiguity reason in tooltip/detail view
10. Display AI confidence score with color coding (Red <70%, Yellow 70-85%, Green >85%)
11. Handle timeout with clear error message

### Clerk Integration (EU endpoints)
12. Extract user_id from Clerk JWT
13. Generate digital signature: {user_id}_{timestamp}
14. Extract user email and role from Clerk claims
15. Match architecture from examples/alex/frontend/ (Pages Router, Clerk v6)

## Files to Create
1. `main/frontend/components/ApprovalModal.tsx` (~300 lines)
2. `main/frontend/hooks/useJobStatusPolling.ts` (~80 lines)

## Files to Modify
1. `main/frontend/pages/generate.tsx` - Add ApprovalModal integration
2. `main/frontend/pages/history.tsx` - Add approval status display
3. `main/frontend/package.json` - Add @headlessui/react

## Dependencies
- Task 3.12 (categorization ambiguity) - COMPLETED
- Task 3.13 (backend HIL API) - IN PROGRESS
- Clerk authentication - CONFIGURED
- Next.js Pages Router - CONFIGURED

## Compliance Requirements
- EU AI Act Article 50 (Transparency)
- 21 CFR Part 11 (Electronic Signatures)
- GAMP-5 (Human oversight)
- WCAG 2.1 AA (Accessibility)

## Task Metadata
- Task ID: 3.14
- Phase: 3 - Containerization
- Started: 2025-11-24 20:42:27
- Workflow Status: IN PROGRESS
