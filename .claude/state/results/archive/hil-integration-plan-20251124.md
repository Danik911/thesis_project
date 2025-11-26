# Human-in-the-Loop (HIL) Integration - Complete Implementation Plan

**Date**: 2025-11-24
**Agent**: Main Orchestrator
**Context**: Tasks 3.12, 3.13, 3.14 - Universal ambiguity detection with HIL approval workflow

---

## Executive Summary

This document provides the comprehensive plan for integrating Human-in-the-Loop (HIL) functionality into the pharmaceutical test generation system. The integration addresses a critical safety issue: the categorization agent was assigning GAMP-5 categories with 100% confidence despite ambiguous User Requirement Specifications (URS).

**Core Principle**: **"When in doubt, ask human"** - NO GUESSING.

**Scope**: 3 tasks covering agent enhancement, backend API, and frontend UI
**Total Estimated Effort**: 18-25 hours
**Impact**: CRITICAL - Enables safe categorization with human oversight per GAMP-5, ICH Q9, and EU AI Act Article 14

---

## Problem Statement

### Issue Identified
From Langfuse trace analysis (`trace-with-observations-772eca9341e79a1114c99b5748b2ab23.json`):

**Job ID**: `ee6b41db-bc3d-4a8e-ae4a-84f8b5dca704`
**URS Description**: "Personalized Medicine Orchestration Platform"
**User Label**: "Ambiguous (4/5)"
**AI Output**: Category 4, confidence=**100%**, requires_human_review=**false**
**Expected**: Category 4 OR 5, confidence<85%, requires_human_review=**true**

### Root Cause
1. Categorization prompt lacks explicit ambiguity detection rules
2. Agent can claim high confidence without justifying certainty
3. No mechanism to detect ambiguity signals ("optional custom modules", hybrid characteristics)
4. Confidence threshold too low (0.8) - allows borderline cases to pass

### Impact
- ❌ Incorrect categorizations lead to invalid test suites
- ❌ Regulatory non-compliance (GAMP-5, ICH Q9 require human oversight for uncertainty)
- ❌ EU AI Act Article 14 violation (high-risk AI must allow human intervention)

---

## Solution Architecture

### Three-Phase Implementation

```
PHASE 1: Categorization Agent Enhancement (Task 3.12)
  ├─ Refactor prompt with universal ambiguity detection rules
  ├─ Add ambiguity signal keywords (all category boundaries)
  ├─ Enforce conservative stance ("justify certainty, not uncertainty")
  ├─ Update schema: +4 fields (has_ambiguity_signals, ambiguity_details, requires_human_review, alternative_categories)
  └─ Raise confidence threshold: 0.8 → 0.85

PHASE 2: Backend API Integration (Task 3.13)
  ├─ Add job status states (AWAITING_APPROVAL, APPROVED, REJECTED)
  ├─ Create approval_decisions table (ALCOA+ audit trail)
  ├─ Implement POST /jobs/{job_id}/approval endpoint
  ├─ Implement GET /jobs/{job_id}/status endpoint (with approval details)
  ├─ Update worker to pause/resume workflows
  └─ Handle timeout (1 hour → auto-reject)

PHASE 3: Frontend Approval UI (Task 3.14)
  ├─ Create ApprovalModal component (Headless UI)
  ├─ Implement job status polling hook (5-second interval)
  ├─ Integrate into Generate page
  ├─ Add approval badges to Job History
  └─ Clerk integration for digital signatures
```

---

## Task 3.12: Categorization Agent - Universal Ambiguity Detection

### Objective
Refactor GAMP-5 categorization agent to detect **ANY** ambiguity across all category boundaries (1/3, 3/4, 4/5) and trigger HIL when uncertain.

### Key Changes

#### 1. Enhanced Prompt with Universal Ambiguity Rules

**New Detection Rules**:
- **Category 1 vs 3**: Infrastructure OR application software?
- **Category 3 vs 4**: Pure COTS (no config) OR configured?
- **Category 4 vs 5**: Configured OR custom-developed?
- **Multiple interpretations**: Conflicting indicators present?
- **Vague URS**: Missing critical details?
- **Boundary cases**: Hybrid systems with 2+ category characteristics?

**Mandatory Ambiguity Keywords**:
- "optional", "customizable", "hybrid", "ambiguous", "unclear", "may include", "configurable modules"
- Conflicting requirements: "standard package with custom workflows"
- Missing information: "insufficient detail to determine category"

**Conservative Stance**:
- Agent must **justify certainty** (not uncertainty) to set `requires_human_review=false`
- Default: If unsure → `requires_human_review=true`

#### 2. Updated Schema

```python
class GAMPCategorizationResult(BaseModel):
    category: int  # 1, 3, 4, or 5
    confidence_score: float  # 0.0-1.0
    reasoning: str

    # NEW FIELDS:
    has_ambiguity_signals: bool  # ANY uncertainty detected
    ambiguity_details: str | None  # Specific reason (e.g., "Category 3/4 boundary")
    requires_human_review: bool  # MANDATORY HIL trigger
    alternative_categories: list[int] | None  # Other plausible categories
```

#### 3. Raised Confidence Threshold
- **Old**: 0.8 (80%)
- **New**: 0.85 (85%)
- ANY score < 85% → automatic `requires_human_review=true`

#### 4. Updated Logic

```python
@step
async def categorize_document(ctx: Context, ev: InputEvent) -> Union[CategorizationEvent, HumanConsultationRequiredEvent]:
    result = await categorization_agent.arun(ENHANCED_CATEGORIZATION_PROMPT)

    # CRITICAL: HIL trigger logic
    if result.requires_human_review:
        return HumanConsultationRequiredEvent(
            consultation_type="gamp5_categorization",
            reason=result.ambiguity_details,
            current_value=result.category,
            alternative_values=result.alternative_categories,
            confidence=result.confidence_score
        )

    # No HIL needed → proceed
    return CategorizationEvent(category=result.category, confidence=result.confidence_score)
```

### Files Modified
- `main/src/core/categorization_workflow.py` (~150 lines modified)

### Files Created
- `main/tests/test_categorization_ambiguity.py` (~200 lines)

### Estimated Effort
**5.5-6.5 hours**

---

## Task 3.13: Backend API - HIL Integration

### Objective
Implement backend API infrastructure to pause workflows, expose approval endpoints, and resume with human decisions. Complete ALCOA+ audit trail.

### Key Components

#### 1. New Job Status States

```python
class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    AWAITING_APPROVAL = "awaiting_approval"  # NEW
    APPROVED = "approved"                     # NEW
    REJECTED = "rejected"                     # NEW
    COMPLETED = "completed"
    FAILED = "failed"
```

#### 2. Database Schema

**New Table**: `approval_decisions`

```sql
CREATE TABLE approval_decisions (
    id UUID PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES jobs(id),

    -- AI Recommendation
    ai_category INTEGER NOT NULL,
    ai_confidence FLOAT NOT NULL,
    ai_reasoning TEXT NOT NULL,
    ambiguity_reason TEXT,
    alternative_categories INTEGER[],

    -- Human Decision
    approval_decision VARCHAR(50) NOT NULL,  -- APPROVE, REJECT, REQUEST_REVISION
    human_category INTEGER,
    justification TEXT NOT NULL,  -- Min 10 chars

    -- ALCOA+ Compliance
    user_id VARCHAR(255) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    user_role VARCHAR(100) NOT NULL,
    digital_signature VARCHAR(500) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Metadata
    ip_address VARCHAR(45),
    user_agent TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Modified Table**: `jobs`

```sql
ALTER TABLE jobs ADD COLUMN requires_approval BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN approval_reason TEXT;
ALTER TABLE jobs ADD COLUMN approval_timeout_at TIMESTAMP WITH TIME ZONE;
```

#### 3. API Endpoints

**POST /jobs/{job_id}/approval**

Request:
```json
{
  "approval_decision": "APPROVE",
  "human_category": 4,
  "justification": "Clear Category 4: configured COTS with no custom source code.",
  "user_signature": "user_2abc123_20251124_143052"
}
```

Response:
```json
{
  "job_id": "ee6b41db-...",
  "status": "APPROVED",
  "gamp_category": 4,
  "workflow_resumed": true,
  "trace_id": "langfuse-trace-xyz",
  "message": "Approval decision 'APPROVE' recorded successfully."
}
```

**GET /jobs/{job_id}/status**

Response:
```json
{
  "job_id": "ee6b41db-...",
  "status": "AWAITING_APPROVAL",
  "requires_approval": true,
  "approval_reason": "Category 4/5 ambiguity detected: 'optional custom modules'",
  "timeout_remaining_seconds": 3240,
  "categorization_result": {
    "category": 4,
    "confidence_score": 0.75,
    "has_ambiguity_signals": true,
    "ambiguity_details": "Category 4/5 boundary",
    "alternative_categories": [5]
  }
}
```

#### 4. Worker Logic

```python
async def execute_workflow(job_id: str):
    async for event in workflow.run_async():
        if isinstance(event, HumanConsultationRequiredEvent):
            # Pause workflow
            job.status = JobStatus.AWAITING_APPROVAL
            job.approval_timeout_at = datetime.utcnow() + timedelta(hours=1)
            db.commit()

            # Wait for human response (poll database)
            human_response = await wait_for_human_response(job_id, timeout=3600)

            if not human_response:
                # Timeout → reject
                job.status = JobStatus.REJECTED
                db.commit()
                return

            # Resume workflow
            workflow.send_event(human_response)
```

### Files Modified
- `main/api/models.py` (~150 lines added)
- `main/api/app.py` (~200 lines added)
- `main/worker/workflow_executor.py` (~100 lines added)
- `main/config/settings.py` (~15 lines added)

### Files Created
- `main/migrations/add_approval_system.sql` (~80 lines)

### Estimated Effort
**6.5-8.5 hours**

---

## Task 3.14: Frontend - Approval UI (Next.js Pages Router)

### Objective
Build Next.js frontend components to display approval requests, collect decisions, and integrate with Clerk for digital signatures. Match `examples/alex/` architecture.

### Key Components

#### 1. ApprovalModal Component

**Features**:
- Display AI categorization with confidence score (color-coded)
- Show ambiguity reason and alternative categories
- Approval form:
  - Decision select: APPROVE / REJECT / REQUEST_REVISION
  - Category override (if human disagrees)
  - Required justification (min 10 chars)
  - Pre-filled digital signature from Clerk
- Form validation
- ALCOA+ compliance messaging

**Technology**:
- Headless UI Dialog for modal
- Clerk `useAuth()` and `useUser()` hooks
- TailwindCSS for styling

#### 2. Job Status Polling Hook

```typescript
export function useJobStatusPolling(jobId: string, intervalMs: number = 5000) {
  const [status, setStatus] = useState<JobStatus | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      const response = await fetch(`/api/jobs/${jobId}/status`, {
        headers: { Authorization: `Bearer ${await getToken()}` }
      });
      setStatus(await response.json());
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, intervalMs);

    return () => clearInterval(interval);
  }, [jobId, intervalMs]);

  return { status, loading, error };
}
```

#### 3. Generate Page Integration

```tsx
export default function GeneratePage() {
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const { status } = useJobStatusPolling(currentJobId, 5000);

  // Show approval modal when required
  const [showApprovalModal, setShowApprovalModal] = useState(false);

  useEffect(() => {
    if (status?.requires_approval && status.status === 'awaiting_approval') {
      setShowApprovalModal(true);
    }
  }, [status]);

  return (
    <div>
      {/* Job Status Display */}
      {status?.status === 'awaiting_approval' && (
        <div className="p-4 bg-yellow-50 border border-yellow-300 rounded">
          <p>⏳ Awaiting Human Approval</p>
          <p>{status.approval_reason}</p>
          <p>Timeout in: {Math.floor(status.timeout_remaining_seconds / 60)}m</p>
        </div>
      )}

      {/* Approval Modal */}
      <ApprovalModal
        isOpen={showApprovalModal}
        jobId={currentJobId}
        categorizationResult={status?.categorization_result}
        onApprovalSubmitted={() => refetch()}
      />
    </div>
  );
}
```

### Files Modified
- `main/frontend/pages/generate.tsx` (~100 lines added)
- `main/frontend/pages/history.tsx` (~50 lines added)
- `main/frontend/package.json` (~5 lines modified)

### Files Created
- `main/frontend/components/ApprovalModal.tsx` (~300 lines)
- `main/frontend/hooks/useJobStatusPolling.ts` (~80 lines)

### Estimated Effort
**6.5-7.5 hours**

---

## Workflow Sequence Diagram

```
User submits URS
    ↓
Categorization Agent analyzes
    ↓
Detects ambiguity (Category 4/5 boundary)
    ↓
Sets requires_human_review = true
    ↓
Emits HumanConsultationRequiredEvent
    ↓
Worker pauses workflow
    ↓
Job status → AWAITING_APPROVAL
    ↓
Frontend polls /jobs/{id}/status (5s interval)
    ↓
Detects requires_approval = true
    ↓
Shows ApprovalModal
    ↓
User reviews AI recommendation
    ↓
User submits decision (APPROVE/REJECT)
    ↓
POST /jobs/{id}/approval
    ↓
Backend stores approval in audit trail
    ↓
Emits HumanResponseEvent
    ↓
Worker resumes workflow with human decision
    ↓
Job status → APPROVED → PROCESSING → COMPLETED
    ↓
Test suite generated with human-approved category
```

---

## Compliance Mapping

### GAMP-5 (Software Validation)
- ✅ **Requirement**: Conservative categorization with human oversight
- ✅ **Implementation**: Ambiguity detection triggers HIL
- ✅ **Benefit**: Reduces risk of incorrect category assignment

### ICH Q9 (Risk Management)
- ✅ **Requirement**: Escalate uncertain decisions to human experts
- ✅ **Implementation**: Confidence < 85% OR ambiguity signals → HIL
- ✅ **Benefit**: Risk-based approach to validation

### EU AI Act Article 14 (Human Oversight)
- ✅ **Requirement**: High-risk AI must allow human intervention
- ✅ **Implementation**: Explicit HIL triggers with approval UI
- ✅ **Benefit**: Regulatory compliance for pharmaceutical AI

### 21 CFR Part 11 (Electronic Records)
- ✅ **§11.10(d)**: Human oversight recorded (timestamp, user ID)
- ✅ **§11.50**: Digital signatures ({user_id}_{timestamp})
- ✅ **§11.10(e)**: Complete audit trail (approval_decisions table)

### ALCOA+ (Data Integrity)
- ✅ **Attributable**: User ID, email, role captured
- ✅ **Legible**: Plain text justification
- ✅ **Contemporaneous**: Timestamp at decision time
- ✅ **Original**: Immutable database record
- ✅ **Accurate**: Digital signature validation
- ✅ **Complete**: Full context preserved (AI + human)
- ✅ **Consistent**: Single source of truth
- ✅ **Enduring**: Permanent audit trail
- ✅ **Available**: Queryable by job_id, user_id, timestamp

---

## Testing Strategy

### Unit Tests (Task 3.12)
```python
# Test ambiguity detection
test_category_1_3_ambiguity()  # Infrastructure vs application
test_category_3_4_ambiguity()  # COTS vs configured
test_category_4_5_ambiguity()  # Configured vs custom
test_vague_urs_triggers_hil()  # Missing details
test_clear_category_no_hil()   # No ambiguity
```

### Integration Tests (Task 3.13)
- POST /approval returns 200 on success
- GET /status returns approval details
- Workflow pauses on HumanConsultationRequiredEvent
- Workflow resumes after approval
- Timeout handled correctly (auto-reject after 1 hour)

### End-to-End Tests (Task 3.14)
1. Submit ambiguous URS
2. Verify workflow pauses
3. Verify approval modal appears
4. Submit approval decision
5. Verify workflow resumes
6. Verify test suite generated with human category

### Accessibility Tests
- Keyboard navigation works
- Screen reader announces status changes
- Color contrast ≥4.5:1 (WCAG 2.1 AA)
- Focus indicators visible

---

## Risks & Mitigations

### Risk 1: Over-Triggering HIL
**Risk**: Too many jobs require human review (operational burden)
**Mitigation**: Set threshold at 85% (not 90%), focus on genuine ambiguity
**Acceptance**: <30% of jobs require HIL in production

### Risk 2: Polling Performance
**Risk**: Frontend polling every 5s creates API load
**Mitigation**: Stop polling when completed/failed, add caching
**Acceptance**: <1% of API requests are polling calls

### Risk 3: Timeout Edge Cases
**Risk**: User submits approval exactly at timeout
**Mitigation**: Backend checks timeout before accepting
**Acceptance**: Clear rejection reason, no race conditions

### Risk 4: Workflow Resumption Complexity
**Risk**: Resuming paused workflows may be complex
**Mitigation**: Use polling-based approach (simple, reliable)
**Acceptance**: Workflow resumes within 5 seconds of approval

---

## Success Criteria

### Task 3.12 (Categorization Agent)
- ✅ Detects ambiguity across ALL category boundaries (1/3, 3/4, 4/5)
- ✅ Confidence < 85% triggers HIL
- ✅ Ambiguity keywords trigger HIL
- ✅ Clear URS with high confidence → no HIL
- ✅ All tests pass

### Task 3.13 (Backend API)
- ✅ Job pauses at AWAITING_APPROVAL status
- ✅ Approval endpoints functional (POST /approval, GET /status)
- ✅ Workflow resumes after approval
- ✅ Timeout handled (auto-reject after 1 hour)
- ✅ Complete ALCOA+ audit trail

### Task 3.14 (Frontend UI)
- ✅ ApprovalModal displays AI categorization
- ✅ Form validation works
- ✅ Job status polling detects approval requirements
- ✅ Digital signature from Clerk
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Accessibility compliant (WCAG 2.1 AA)

### End-to-End Integration
- ✅ Ambiguous URS → HIL trigger → Approval modal → Workflow resumes
- ✅ Human decision stored in audit trail
- ✅ Test suite generated with human-approved category
- ✅ All HIL interactions traced in Langfuse

---

## Post-Implementation Monitoring

### Metrics to Track
1. **HIL Trigger Rate**: % of jobs requiring approval (target: <30%)
2. **Approval Response Time**: Average time to approve (target: <5 minutes)
3. **Timeout Rate**: % of approval requests timing out (target: <5%)
4. **Category Override Rate**: % of humans disagreeing with AI (target: <15%)
5. **Rejection Rate**: % of jobs rejected by human (target: <10%)

### Continuous Improvement
- Collect user feedback on ambiguity detection accuracy
- Analyze false positives (HIL triggered unnecessarily)
- Analyze false negatives (ambiguity missed)
- Refine prompt based on real-world performance

---

## Estimated Timeline

| Task | Phase | Duration | Dependencies |
|------|-------|----------|--------------|
| 3.12 | Agent Enhancement | 5.5-6.5h | None |
| 3.13 | Backend API | 6.5-8.5h | Task 3.12 |
| 3.14 | Frontend UI | 6.5-7.5h | Task 3.13 |
| **Total** | **All Phases** | **18-25h** | Sequential |

**Recommended Approach**: Execute sequentially (3.12 → 3.13 → 3.14) to ensure each layer is tested before proceeding.

---

## References

### Code Files
- [categorization_workflow.py](../../main/src/core/categorization_workflow.py)
- [human_consultation.py](../../main/src/agents/human_consultation.py)
- [events.py](../../main/src/core/events.py)
- [workflow_executor.py](../../main/worker/workflow_executor.py)
- [examples/alex/frontend/](../../examples/alex/frontend/) - Reference architecture

### Trace Analysis
- [Langfuse Trace](../../main/logs/langfuse/trace-with-observations-772eca9341e79a1114c99b5748b2ab23.json) - Original failure case

### Standards
- [GAMP-5](https://ispe.org/initiatives/regulatory-resources/gamp-5)
- [ICH Q9](https://www.ich.org/page/quality-guidelines)
- [EU AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)
- [21 CFR Part 11](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application)
- [ALCOA+](https://www.fda.gov/media/119267/download)

---

**REMEMBER: When in doubt, ask human. NO GUESSING. Complete audit trail for all decisions.**
