main.js:1838 Download the React DevTools for a better development experience: https://reactjs.org/link/react-devtools
websocket.js:39 [HMR] connected
reportAccessibility.ts:35 [Accessibility] axe-core initialized successfully
clerk.browser.js:19 Clerk: Clerk has been loaded with development keys. Development instances have strict usage limits and should not be used when deploying your application to production. Learn more: https://clerk.com/docs/deployments/overview
warnOnce @ clerk.browser.js:19
load @ clerk.browser.js:5
loadClerkJS @ index.mjs:1653
_IsomorphicClerk @ index.mjs:1522
getOrCreateInstance @ index.mjs:1548
useLoadedIsomorphicClerk @ index.mjs:1826
ClerkContextProvider @ index.mjs:1757
renderWithHooks @ react-dom.development.js:15486
mountIndeterminateComponent @ react-dom.development.js:20098
beginWork @ react-dom.development.js:21621
beginWork$1 @ react-dom.development.js:27460
performUnitOfWork @ react-dom.development.js:26591
workLoopSync @ react-dom.development.js:26500
renderRootSync @ react-dom.development.js:26468
performConcurrentWorkOnRoot @ react-dom.development.js:25772
workLoop @ scheduler.development.js:266
flushWork @ scheduler.development.js:239
performWorkUntilDeadline @ scheduler.development.js:533
tokenManager.ts:86 [TokenManager] Starting token refresh...
generate.tsx:621 [DEBUG] No localStorage state to restore
index.mjs:256 New axe issues
index.mjs:276 serious: Elements must meet minimum color contrast ratio thresholds https://dequeuniversity.com/rules/axe/4.11/color-contrast?application=axeAPI
tokenManager.ts:127 [TokenManager] Token refreshed successfully
generate.tsx:349 [DEBUG] handleGenerate called
generate.tsx:350 [DEBUG] Selected file: urs-001.md (1874 bytes)
generate.tsx:360 [DEBUG] API URL: http://localhost:8080
generate.tsx:364 [DEBUG] Sending POST /jobs request with authenticated fetch...
generate.tsx:369 [DEBUG] POST /jobs response: 201 Created
generate.tsx:386 [DEBUG] Job created: 55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:415 [DEBUG] Starting poll for job 55296045-71f8-4936-a120-98a29ff4ff75 at http://localhost:8080
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
useJobStatusPolling.ts:86 [HIL-POLL] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:219 [PROGRESS-DEBUG] Progress increased: null → 65
generate.tsx:236 [PROGRESS-DEBUG] Stage updated: null → agent_execution
generate.tsx:240 [PROGRESS-DEBUG] Stage label updated: Executing AI Agents
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: hil_waiting, label: Awaiting Human Approval, progress: 30%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: AWAITING_APPROVAL, stage: hil_waiting, label: Awaiting Human Approval, progress: 30%
generate.tsx:571 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 awaiting human approval - triggering modal
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'awaiting_approval', current_stage: 'hil_waiting', current_stage_label: 'Awaiting Human Approval', progress_percentage: 30}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: AWAITING_APPROVAL
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 30 (keeping: 65 )
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: AWAITING_APPROVAL, stage: hil_waiting, label: Awaiting Human Approval, progress: 30%
generate.tsx:571 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 awaiting human approval - triggering modal
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: AWAITING_APPROVAL, stage: hil_waiting, label: Awaiting Human Approval, progress: 30%
generate.tsx:571 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 awaiting human approval - triggering modal
ApprovalModal.tsx:143 Approval submitted successfully: {job_id: '55296045-71f8-4936-a120-98a29ff4ff75', status: 'approved', gamp_category: 3, workflow_resumed: true, trace_id: null, …}
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'approved', current_stage: 'hil_waiting', current_stage_label: 'Awaiting Human Approval', progress_percentage: 30}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: APPROVED
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 30 (keeping: 65 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: APPROVED, stage: hil_waiting, label: Awaiting Human Approval, progress: 30%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'approved', current_stage: 'planning', current_stage_label: 'Planning Test Strategy', progress_percentage: 45}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: APPROVED
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 45 (keeping: 65 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: APPROVED, stage: planning, label: Planning Test Strategy, progress: 45%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:580 [DEBUG] Status changed: APPROVED → PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
tokenManager.ts:86 [TokenManager] Starting token refresh...
tokenManager.ts:127 [TokenManager] Token refreshed successfully
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
useJobStatusPolling.ts:86 [HIL-POLL] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
useJobStatusPolling.ts:86 [HIL-POLL] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
useJobStatusPolling.ts:86 [HIL-POLL] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
useJobStatusPolling.ts:86 [HIL-POLL] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
useJobStatusPolling.ts:86 [HIL-POLL] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
useJobStatusPolling.ts:86 [HIL-POLL] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
useJobStatusPolling.ts:119  GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75/approval-status 401 (Unauthorized)
eval @ useJobStatusPolling.ts:119
setInterval
eval @ useJobStatusPolling.ts:192
commitHookEffectListMount @ react-dom.development.js:23184
commitPassiveMountOnFiber @ react-dom.development.js:24960
commitPassiveMountEffects_complete @ react-dom.development.js:24925
commitPassiveMountEffects_begin @ react-dom.development.js:24912
commitPassiveMountEffects @ react-dom.development.js:24900
flushPassiveEffectsImpl @ react-dom.development.js:27073
flushPassiveEffects @ react-dom.development.js:27018
eval @ react-dom.development.js:26803
workLoop @ scheduler.development.js:266
flushWork @ scheduler.development.js:239
performWorkUntilDeadline @ scheduler.development.js:533
useJobStatusPolling.ts:130 [HIL-POLL] JWT expired (401), coordinated refresh, retry 1/5 in 2000ms...
eval @ useJobStatusPolling.ts:130
setInterval
eval @ useJobStatusPolling.ts:192
commitHookEffectListMount @ react-dom.development.js:23184
commitPassiveMountOnFiber @ react-dom.development.js:24960
commitPassiveMountEffects_complete @ react-dom.development.js:24925
commitPassiveMountEffects_begin @ react-dom.development.js:24912
commitPassiveMountEffects @ react-dom.development.js:24900
flushPassiveEffectsImpl @ react-dom.development.js:27073
flushPassiveEffects @ react-dom.development.js:27018
eval @ react-dom.development.js:26803
workLoop @ scheduler.development.js:266
flushWork @ scheduler.development.js:239
performWorkUntilDeadline @ scheduler.development.js:533
authenticatedFetch.ts:65  GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75 401 (Unauthorized)
authenticatedFetch @ authenticatedFetch.ts:65
await in authenticatedFetch
eval @ generate.tsx:432
setInterval
eval @ generate.tsx:417
handleGenerate @ generate.tsx:394
await in handleGenerate
callCallback @ react-dom.development.js:4164
invokeGuardedCallbackDev @ react-dom.development.js:4213
invokeGuardedCallback @ react-dom.development.js:4277
invokeGuardedCallbackAndCatchFirstError @ react-dom.development.js:4291
executeDispatch @ react-dom.development.js:9041
processDispatchQueueItemsInOrder @ react-dom.development.js:9073
processDispatchQueue @ react-dom.development.js:9086
dispatchEventsForPlugins @ react-dom.development.js:9097
eval @ react-dom.development.js:9288
batchedUpdates$1 @ react-dom.development.js:26174
batchedUpdates @ react-dom.development.js:3991
dispatchEventForPluginEventSystem @ react-dom.development.js:9287
dispatchEventWithEnableCapturePhaseSelectiveHydrationWithoutDiscreteEventReplay @ react-dom.development.js:6465
dispatchEvent @ react-dom.development.js:6457
dispatchDiscreteEvent @ react-dom.development.js:6430
eval @ generate.tsx:149
setTimeout
handleTemplateSubmit @ generate.tsx:145
eval @ TemplateEditor.tsx:106
callCallback @ react-dom.development.js:4164
invokeGuardedCallbackDev @ react-dom.development.js:4213
invokeGuardedCallback @ react-dom.development.js:4277
invokeGuardedCallbackAndCatchFirstError @ react-dom.development.js:4291
executeDispatch @ react-dom.development.js:9041
processDispatchQueueItemsInOrder @ react-dom.development.js:9073
processDispatchQueue @ react-dom.development.js:9086
dispatchEventsForPlugins @ react-dom.development.js:9097
eval @ react-dom.development.js:9288
batchedUpdates$1 @ react-dom.development.js:26174
batchedUpdates @ react-dom.development.js:3991
dispatchEventForPluginEventSystem @ react-dom.development.js:9287
dispatchEventWithEnableCapturePhaseSelectiveHydrationWithoutDiscreteEventReplay @ react-dom.development.js:6465
dispatchEvent @ react-dom.development.js:6457
dispatchDiscreteEvent @ react-dom.development.js:6430
authenticatedFetch.ts:71 [API] JWT expired (401), coordinated refresh, retry 1/5 in 2000ms...
authenticatedFetch @ authenticatedFetch.ts:71
await in authenticatedFetch
eval @ generate.tsx:432
setInterval
eval @ generate.tsx:417
handleGenerate @ generate.tsx:394
await in handleGenerate
callCallback @ react-dom.development.js:4164
invokeGuardedCallbackDev @ react-dom.development.js:4213
invokeGuardedCallback @ react-dom.development.js:4277
invokeGuardedCallbackAndCatchFirstError @ react-dom.development.js:4291
executeDispatch @ react-dom.development.js:9041
processDispatchQueueItemsInOrder @ react-dom.development.js:9073
processDispatchQueue @ react-dom.development.js:9086
dispatchEventsForPlugins @ react-dom.development.js:9097
eval @ react-dom.development.js:9288
batchedUpdates$1 @ react-dom.development.js:26174
batchedUpdates @ react-dom.development.js:3991
dispatchEventForPluginEventSystem @ react-dom.development.js:9287
dispatchEventWithEnableCapturePhaseSelectiveHydrationWithoutDiscreteEventReplay @ react-dom.development.js:6465
dispatchEvent @ react-dom.development.js:6457
dispatchDiscreteEvent @ react-dom.development.js:6430
eval @ generate.tsx:149
setTimeout
handleTemplateSubmit @ generate.tsx:145
eval @ TemplateEditor.tsx:106
callCallback @ react-dom.development.js:4164
invokeGuardedCallbackDev @ react-dom.development.js:4213
invokeGuardedCallback @ react-dom.development.js:4277
invokeGuardedCallbackAndCatchFirstError @ react-dom.development.js:4291
executeDispatch @ react-dom.development.js:9041
processDispatchQueueItemsInOrder @ react-dom.development.js:9073
processDispatchQueue @ react-dom.development.js:9086
dispatchEventsForPlugins @ react-dom.development.js:9097
eval @ react-dom.development.js:9288
batchedUpdates$1 @ react-dom.development.js:26174
batchedUpdates @ react-dom.development.js:3991
dispatchEventForPluginEventSystem @ react-dom.development.js:9287
dispatchEventWithEnableCapturePhaseSelectiveHydrationWithoutDiscreteEventReplay @ react-dom.development.js:6465
dispatchEvent @ react-dom.development.js:6457
dispatchDiscreteEvent @ react-dom.development.js:6430
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
tokenManager.ts:86 [TokenManager] Starting token refresh...
tokenManager.ts:81 [TokenManager] Waiting for existing token refresh...
tokenManager.ts:127 [TokenManager] Token refreshed successfully
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
useJobStatusPolling.ts:156 [HIL-POLL] Request aborted (navigation/unmount)
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: oq_generation, label: Generating Test Cases, progress: 85%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: oq_generation, label: Generating Test Cases, progress: 85%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'oq_generation', current_stage_label: 'Generating Test Cases', progress_percentage: 85}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: oq_generation, label: Generating Test Cases, progress: 85%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: planning, label: Planning Test Strategy, progress: 45%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
tokenManager.ts:86 [TokenManager] Starting token refresh...
tokenManager.ts:81 [TokenManager] Waiting for existing token refresh...
tokenManager.ts:127 [TokenManager] Token refreshed successfully
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
tokenManager.ts:86 [TokenManager] Starting token refresh...
tokenManager.ts:127 [TokenManager] Token refreshed successfully
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
useJobStatusPolling.ts:86 [HIL-POLL] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
useJobStatusPolling.ts:86 [HIL-POLL] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
useJobStatusPolling.ts:86 [HIL-POLL] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
useJobStatusPolling.ts:86 [HIL-POLL] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
useJobStatusPolling.ts:86 [HIL-POLL] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
tokenManager.ts:86 [TokenManager] Starting token refresh...
tokenManager.ts:127 [TokenManager] Token refreshed successfully
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: agent_execution, label: Executing AI Agents, progress: 65%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:420 [DEBUG] Skipping poll - previous request still in flight
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'agent_execution', current_stage_label: 'Executing AI Agents', progress_percentage: 65}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 65 (keeping: 85 )
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: oq_generation, label: Generating Test Cases, progress: 85%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'oq_generation', current_stage_label: 'Generating Test Cases', progress_percentage: 85}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: PROCESSING, stage: oq_generation, label: Generating Test Cases, progress: 85%
generate.tsx:430 [DEBUG] Polling job status: GET http://localhost:8080/jobs/55296045-71f8-4936-a120-98a29ff4ff75
generate.tsx:487 [DEBUG] Job 55296045-71f8-4936-a120-98a29ff4ff75 status: COMPLETED, stage: completion, label: Finalizing Results, progress: 100%
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'processing', current_stage: 'oq_generation', current_stage_label: 'Generating Test Cases', progress_percentage: 85}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: PROCESSING
generate.tsx:224 [PROGRESS-DEBUG] Ignoring backward progress: 85 (keeping: 100 )
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'completed', current_stage: 'completion', current_stage_label: 'Finalizing Results', progress_percentage: 100}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: COMPLETED
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'completed', current_stage: 'completion', current_stage_label: 'Finalizing Results', progress_percentage: 100}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: COMPLETED
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'completed', current_stage: 'completion', current_stage_label: 'Finalizing Results', progress_percentage: 100}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: COMPLETED
generate.tsx:207 [PROGRESS-DEBUG] approvalStatus received: {status: 'completed', current_stage: 'completion', current_stage_label: 'Finalizing Results', progress_percentage: 100}
generate.tsx:252 [PROGRESS-DEBUG] Setting status to: COMPLETED
