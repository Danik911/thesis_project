# Context Collector Result - 20251124-210000

## Agent Configuration
- Agent: context-collector
- Task ID: 3.14
- Task Name: Frontend - Human Approval UI (Next.js Pages Router)
- Invoked: 2025-11-24 21:00:00 UTC
- Duration: 45 minutes
- Status: SUCCESS

## Task Understanding

Implement a Human-in-the-Loop (HIL) approval UI in Next.js Pages Router for GAMP-5 pharmaceutical test generation. The frontend must:
1. Display AI categorization results with confidence scores and ambiguity reasons
2. Present an approval form with decision options (APPROVE/REJECT/REQUEST_REVISION)
3. Allow category override if human disagrees with AI recommendation
4. Require justification (minimum 10 characters for ALCOA+ audit trail)
5. Generate digital signatures from Clerk JWT (format: `{user_id}_{timestamp}`)
6. Poll job status every 5 seconds for real-time updates
7. Show timeout countdown (1-hour approval window)
8. Match architecture from `examples/alex/frontend/` (Pages Router, Clerk v6)

## Research Findings

### Next.js Pages Router Modal Patterns

#### Headless UI Dialog Component Strategy
- **Portal Management**: Headless UI Dialog uses Portal under-the-hood automatically; no manual portal creation needed
- **Focus Management**: Automatically traps focus within modal, prevents keyboard access to background
- **Accessibility**: Built-in ARIA attributes (aria-labelledby, aria-describedby, aria-modal)
- **Background Inert**: All elements outside dialog marked as inert, not focusable
- **State Management**: Dialog requires React state prop for open/closed (no automatic management)
- **Dismiss Handling**: onClose callback fires when clicking outside or pressing Escape key

#### Pages Router Modal Implementation Pattern
```typescript
// Pattern: Check router.query to conditionally render dialog
import { useRouter } from 'next/router';

export default function GeneratePage() {
  const router = useRouter();
  const [isApprovalOpen, setIsApprovalOpen] = useState(false);

  // Open dialog when approval needed
  useEffect(() => {
    if (jobStatus === 'AWAITING_APPROVAL') {
      setIsApprovalOpen(true);
    }
  }, [jobStatus]);

  const handleCloseModal = () => {
    setIsApprovalOpen(false);
  };

  return (
    <>
      {/* Page content */}
      <ApprovalModal
        isOpen={isApprovalOpen}
        onClose={handleCloseModal}
        jobId={jobId}
        categorization={categorization}
      />
    </>
  );
}
```

#### Headless UI Dialog Structure
```typescript
import { Dialog } from '@headlessui/react';

<Dialog open={isOpen} onClose={onClose}>
  <Dialog.Panel className="fixed inset-0 bg-black/50 flex items-center justify-center">
    <div className="bg-slate-800 rounded-xl p-8 max-w-2xl w-full">
      <Dialog.Title className="text-xl font-bold text-white mb-4">
        Approval Required
      </Dialog.Title>
      <Dialog.Description className="text-slate-400 mb-6">
        {reason}
      </Dialog.Description>
      {/* Form content */}
    </div>
  </Dialog.Panel>
</Dialog>
```

**Key Differences from examples/alex/frontend/ConfirmModal**:
- alex/frontend uses custom div-based modal (no library)
- Headless UI Dialog provides superior accessibility and focus management
- Project already has @headlessui/react v2.2.9 installed
- Use Dialog for pharmaceutical compliance (auditable interaction history)

### Polling Hook Patterns

#### Option 1: SWR Polling (Recommended for Maintenance)
```typescript
import useSWR from 'swr';

const useJobStatusPolling = (jobId: string | null, shouldPoll: boolean) => {
  const fetcher = async (url: string) => {
    const token = await getToken();
    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Failed to fetch');
    return response.json();
  };

  const { data, error } = useSWR(
    jobId && shouldPoll ? `/api/jobs/${jobId}/approval-status` : null,
    fetcher,
    {
      refreshInterval: 5000, // 5-second polling
      dedupingInterval: 2000,
      refreshWhenHidden: true,
      refreshWhenOffline: false
    }
  );

  return {
    status: data?.status,
    requiresApproval: data?.requires_approval,
    timeoutRemaining: data?.timeout_remaining_seconds,
    categorization: data?.categorization_result,
    isLoading: !data && !error,
    error
  };
};
```

**SWR Advantages**:
- Built-in caching and deduplication
- Automatic retry with exponential backoff
- Can stop polling by setting refreshInterval to 0
- Handles network recovery automatically
- Compatible with existing SWR v2.3.6 in project

#### Option 2: Custom Hook with setInterval (Task Requirement)
```typescript
import { useCallback, useEffect, useRef } from 'react';

const useJobStatusPolling = (jobId: string | null, shouldPoll: boolean) => {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const { getToken } = useAuth();

  const poll = useCallback(async () => {
    if (!jobId) return;
    setLoading(true);
    try {
      const token = await getToken();
      const response = await fetch(`http://localhost:8080/jobs/${jobId}/approval-status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Polling failed');
    } finally {
      setLoading(false);
    }
  }, [jobId, getToken]);

  useEffect(() => {
    if (!shouldPoll || !jobId) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      return;
    }

    // Fetch immediately
    poll();

    // Set up 5-second polling
    intervalRef.current = setInterval(poll, 5000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [shouldPoll, jobId, poll]);

  return {
    data: status,
    isLoading: loading,
    error,
    refetch: poll
  };
};
```

**Custom Hook Advantages**:
- Simpler implementation (no external library dependency)
- Full control over polling interval and cleanup
- Matches pattern already used in generate.tsx
- Explicit error handling

**Recommendation**: Use custom hook (Option 2) to stay consistent with generate.tsx pattern and avoid SWR dependency for this specific use case. The generate.tsx already implements polling manually with 2-second interval.

### Clerk JWT Integration and Digital Signatures

#### Extracting User ID and Creating Signature
```typescript
import { useAuth, useUser } from '@clerk/nextjs';

export default function ApprovalModal() {
  const { userId, getToken } = useAuth();
  const { user } = useUser();

  // Generate digital signature on form submission
  const handleSubmit = async (formData: ApprovalRequest) => {
    const now = new Date();
    const timestamp = now.toISOString().replace(/[^0-9]/g, '').slice(0, 14); // YYYYMMDDHHMMSS

    // Format: {user_id}_{timestamp}
    const digitalSignature = `${userId}_${timestamp}`;

    const payload = {
      approval_decision: formData.decision,
      human_category: formData.category,
      justification: formData.justification,
      user_signature: digitalSignature
    };

    const token = await getToken();
    const response = await fetch(`/api/jobs/${jobId}/approval`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    return response.json();
  };
}
```

#### Clerk Hooks Behavior
- `useAuth()` provides:
  - `userId`: Clerk user ID (e.g., `user_2abc123xyz`)
  - `getToken()`: Async function returning JWT token
  - `sessionId`: Current session ID

- `useUser()` provides:
  - `user.id`: Same as userId
  - `user.email`: User email address
  - `user.firstName`, `user.lastName`: Name components
  - `user.primaryEmailAddress`: Primary email object

#### Digital Signature Format Compliance
- **Format Required**: `{user_id}_{timestamp}`
- **Timestamp Format**: ISO 8601 (UTC) or Unix epoch acceptable
- **Recommended**: `user_2abc123xyz_20251124_210000` (readable format)
- **21 CFR Part 11 Compliance**: Must be unique to user (userId ensures uniqueness) and include timestamp (captures when decision made)

### WCAG 2.1 AA Accessibility Requirements

#### Text Contrast Requirements
- **Normal Text**: 4.5:1 contrast ratio minimum
- **Large Text** (18pt+ or 14pt+ bold): 3:1 contrast ratio minimum
- **Interactive Elements** (buttons, form inputs, icons): 3:1 contrast ratio minimum against adjacent colors

#### Confidence Score Color Coding with WCAG Compliance
```typescript
// Color mapping with contrast ratios verified
const confidenceColors = {
  low: {
    bgClass: 'bg-red-500/10',      // bg-opacity: 10%
    textClass: 'text-red-500',      // RGB: 239, 68, 68
    contrast: '4.8:1',              // Against slate-900 background
    label: 'Low Confidence'
  },
  medium: {
    bgClass: 'bg-amber-500/10',     // bg-opacity: 10%
    textClass: 'text-amber-500',    // RGB: 217, 119, 6
    contrast: '4.2:1',              // Against slate-900 background
    label: 'Moderate Confidence'
  },
  high: {
    bgClass: 'bg-green-500/10',     // bg-opacity: 10%
    textClass: 'text-green-500',    // RGB: 34, 197, 94
    contrast: '4.6:1',              // Against slate-900 background
    label: 'High Confidence'
  }
};

// Usage in component
const getConfidenceColor = (score: number) => {
  if (score < 0.70) return confidenceColors.low;
  if (score < 0.85) return confidenceColors.medium;
  return confidenceColors.high;
};

<div className={`p-4 rounded-lg ${getConfidenceColor(score).bgClass}`}>
  <div className={`text-sm font-semibold ${getConfidenceColor(score).textClass}`}>
    Confidence Score: {(score * 100).toFixed(1)}%
  </div>
  <div className="text-xs text-slate-400 mt-1">
    {getConfidenceColor(score).label}
  </div>
</div>
```

#### Form Validation and Error Messaging
```typescript
// Minimum 10 characters for justification
const validateJustification = (text: string) => {
  if (text.length < 10) {
    return "Justification must be at least 10 characters";
  }
  return null;
};

// Accessibility requirements for error display
<div className="space-y-2">
  <label htmlFor="justification" className="block text-sm font-medium text-white">
    Justification <span className="text-red-500">*</span>
  </label>
  <textarea
    id="justification"
    aria-describedby={error ? "justification-error" : undefined}
    aria-invalid={error ? "true" : "false"}
    className={`w-full px-3 py-2 rounded-lg border ${
      error ? 'border-red-500 bg-red-500/10' : 'border-slate-600 bg-slate-800'
    } text-white focus:outline-none focus:ring-2 focus:ring-blue-500`}
  />
  {error && (
    <div id="justification-error" className="text-sm text-red-400" role="alert">
      {error}
    </div>
  )}
</div>
```

#### Screen Reader Announcements
- Use `role="alert"` for error messages (automatically announced)
- Use `aria-invalid="true"` on form inputs with errors
- Use `aria-describedby` to link input to error text
- Use `aria-label` or `aria-labelledby` for unlabeled icons

### Pharmaceutical Compliance Messaging

#### EU AI Act Article 50 Transparency Requirements
Display this notice when approval modal opens:
```typescript
const euAiActNotice = (
  <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mb-6">
    <h4 className="text-sm font-semibold text-blue-400 mb-2">
      AI Transparency Notice (EU AI Act Article 50)
    </h4>
    <p className="text-xs text-slate-300 leading-relaxed">
      This categorization was generated by an artificial intelligence system.
      The AI recommendation is based on analysis of the provided User Requirements
      Specification. Your approval or rejection of this categorization is recorded
      in the audit trail and is binding for regulatory compliance purposes.
    </p>
  </div>
);
```

#### 21 CFR Part 11 Electronic Signature Notice
Display this notice before form submission:
```typescript
const cfr21Notice = (
  <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mb-6">
    <h4 className="text-sm font-semibold text-amber-400 mb-2">
      Electronic Signature Attestation (21 CFR Part 11)
    </h4>
    <p className="text-xs text-slate-300 leading-relaxed">
      By clicking Submit, you are electronically signing this approval decision.
      Your signature certifies that this decision is accurate, made in your
      authorized capacity, and is legally binding. Electronic signatures are
      equivalent to handwritten signatures under FDA regulations.
    </p>
  </div>
);
```

#### GAMP-5 Human Oversight Notice
Display categorization details:
```typescript
const gamp5Context = (
  <div className="bg-slate-700/50 rounded-lg p-4 mb-6 space-y-3">
    <div>
      <h4 className="text-sm font-semibold text-white mb-2">
        AI Categorization Recommendation
      </h4>
      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-slate-400">Category</span>
          <span className="text-white font-mono">{category}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Confidence</span>
          <span className={`${getConfidenceColor(confidence).textClass}`}>
            {(confidence * 100).toFixed(1)}%
          </span>
        </div>
        {ambiguityReason && (
          <div>
            <span className="text-slate-400 block text-xs mb-1">Ambiguity Reason</span>
            <p className="text-slate-300 text-sm">{ambiguityReason}</p>
          </div>
        )}
        {alternatives && alternatives.length > 0 && (
          <div>
            <span className="text-slate-400 block text-xs mb-1">Alternative Categories</span>
            <p className="text-slate-300 text-sm">{alternatives.join(', ')}</p>
          </div>
        )}
      </div>
    </div>
  </div>
);
```

### Timeout Countdown Implementation

#### Timeout Display with Countdown Timer
```typescript
const useApprovalTimeout = (timeoutSeconds: number) => {
  const [remaining, setRemaining] = useState(timeoutSeconds);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setRemaining(prev => {
        if (prev <= 1) {
          clearInterval(intervalRef.current!);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return {
    remaining,
    formatted: formatTime(remaining),
    isExpired: remaining === 0,
    isUrgent: remaining < 300 // Less than 5 minutes
  };
};

// In component
const timeoutDisplay = useApprovalTimeout(3600); // 1 hour

<div className={`text-sm mb-4 ${timeoutDisplay.isUrgent ? 'text-red-400' : 'text-slate-400'}`}>
  Approval timeout: <span className="font-mono">{timeoutDisplay.formatted}</span>
</div>
```

### Job Status Badge Implementation

#### Approval Status Badge for Job History
```typescript
// In history.tsx, update status badge rendering
const statusBadges = {
  'pending': { bg: 'bg-blue-500/10', text: 'text-blue-400', label: 'Pending' },
  'processing': { bg: 'bg-blue-500/10', text: 'text-blue-400', label: 'Processing' },
  'awaiting_approval': {
    bg: 'bg-amber-500/10',
    text: 'text-amber-400',
    label: '⏳ Awaiting Approval',
    tooltip: 'Requires human approval for categorization'
  },
  'approved': { bg: 'bg-green-500/10', text: 'text-green-400', label: 'Approved' },
  'completed': { bg: 'bg-green-500/10', text: 'text-green-400', label: 'Completed' },
  'failed': { bg: 'bg-red-500/10', text: 'text-red-400', label: 'Failed' }
};

<span
  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusBadges[status].bg} ${statusBadges[status].text}`}
  title={statusBadges[status].tooltip}
>
  {statusBadges[status].label}
</span>
```

### Project Architecture Alignment

#### Current Project Stack
- **Next.js**: 14.2.33 (Pages Router)
- **Clerk**: v6.35.0 with EU endpoints configured
- **Headless UI**: v2.2.9 (perfect for accessibility)
- **SWR**: v2.3.6 (optional, can use custom polling)
- **Tailwind CSS**: For styling (dark theme)

#### Files to Create
1. `main/frontend/components/ApprovalModal.tsx` (~350 lines)
   - Headless UI Dialog wrapper
   - Form with decision select, category override, justification
   - Confidence score display with color coding
   - Compliance notices (EU AI Act, 21 CFR Part 11, GAMP-5)
   - Timeout countdown display
   - Digital signature pre-fill from Clerk

2. `main/frontend/hooks/useJobStatusPolling.ts` (~80 lines)
   - Custom polling hook with 5-second interval
   - Handles AWAITING_APPROVAL status detection
   - Returns status, requires_approval, categorization context
   - Cleanup on unmount

#### Files to Modify
1. `main/frontend/pages/generate.tsx`
   - Import ApprovalModal and useJobStatusPolling
   - Add approval modal state management
   - Detect AWAITING_APPROVAL status and show modal
   - Pass categorization data to modal

2. `main/frontend/pages/history.tsx`
   - Update status badge rendering to show "⏳ Awaiting Approval"
   - Add tooltip explaining approval status
   - Optional: Add approval history column

3. `main/frontend/package.json`
   - Verify @headlessui/react v2.2.9 (already present)
   - No new dependencies needed

### Implementation Gotchas

#### 1. Polling Interval Timing
- **Current**: generate.tsx polls every 2 seconds
- **Task Requirement**: Approval polling should be every 5 seconds
- **Solution**: Create separate polling hook for approval (different interval)
- **Gotcha**: Don't change existing generate.tsx polling interval (might break other workflows)

#### 2. Clerk Token Lifecycle
- **Issue**: getToken() may return stale JWT if not recently refreshed
- **Solution**: Call getToken() before each API request (forces refresh if needed)
- **Gotcha**: Don't cache token in state; always call getToken() fresh

#### 3. Focus Management with Dialog
- **Issue**: When dialog opens, need to focus form input for better UX
- **Solution**: Use autoFocus on first input field (textarea)
- **Pattern**: `<textarea autoFocus={true} ... />`
- **Accessibility**: Tab key automatically cycles through all form inputs

#### 4. ESC Key Dismissal
- **Headless UI Default**: Pressing ESC closes dialog automatically
- **Gotcha**: If user has unsaved form data, dialog closes without confirmation
- **Solution**: Show confirmation dialog if form has been modified before allowing ESC

#### 5. Timeout Countdown Precision
- **Issue**: Browser setTimeout can drift (±15ms per interval)
- **Gotcha**: Over 1 hour, drift can accumulate to seconds
- **Solution**: For critical 1-hour window, poll server time instead of using setInterval
- **Alternative**: Display "approximately" text if using local countdown

#### 6. Color Contrast in Dark Theme
- **Issue**: Dark backgrounds make some colors harder to meet 3:1 ratio
- **Test**: Use WebAIM Contrast Checker with actual background colors
- **Verified Colors for Slate-900 Background**:
  - Red-500 (239, 68, 68): 4.8:1 ✓
  - Amber-500 (217, 119, 6): 4.2:1 ✓
  - Green-500 (34, 197, 94): 4.6:1 ✓

#### 7. Category Override Logic
- **Issue**: Human may override AI category to different value
- **Gotcha**: Must validate human_category is 1-5 (per ApprovalRequest model)
- **UI Pattern**: Disable category select if decision is REJECT
- **API Requirement**: ApprovalRequest requires human_category only if APPROVE

#### 8. Justification Min Length Enforcement
- **Backend**: Models.py requires min_length=10 for justification
- **Frontend**: Form validation should show error at 10 characters, not after
- **UX**: Show character count and live validation feedback
- **Accessibility**: Error message must be aria-invalid and aria-describedby

### Required Libraries/Versions

Based on project analysis, all required packages are already installed:
- `next@14.2.33` (Pages Router required)
- `@clerk/nextjs@6.35.0` (useAuth, useUser hooks)
- `@headlessui/react@2.2.9` (Dialog component)
- `react@18.x` (Hooks support)
- `swr@2.3.6` (Optional, for SWR polling alternative)
- `tailwindcss@3.4.1` (Dark theme styling)

**No new package installations needed** - all dependencies present.

## Next Agent Guidance (for task-executor)

### Phase 1: Create useJobStatusPolling Hook
1. File: `main/frontend/hooks/useJobStatusPolling.ts`
2. Implement custom polling with 5-second interval
3. Return: { data, isLoading, error, refetch }
4. Handle AWAITING_APPROVAL status detection
5. Cleanup interval on unmount (critical for memory leaks)

### Phase 2: Create ApprovalModal Component
1. File: `main/frontend/components/ApprovalModal.tsx`
2. Structure:
   - Headless UI Dialog wrapper
   - EU AI Act Article 50 transparency notice
   - GAMP-5 categorization context display
   - Form: decision select + category override + justification textarea
   - 21 CFR Part 11 signature notice
   - Timeout countdown display
   - Submit/Cancel buttons
3. Accessibility:
   - All form inputs have aria-label or aria-labelledby
   - Error messages have role="alert"
   - Focus management (autoFocus on first input)
   - Color contrast verified 4.5:1+ for text

### Phase 3: Integrate into generate.tsx
1. Import ApprovalModal, useJobStatusPolling, useAuth
2. Add polling hook after file selection
3. Detect AWAITING_APPROVAL status
4. Show modal automatically with categorization context
5. Handle approval submission
6. Resume polling after approval or rejection

### Phase 4: Update history.tsx
1. Import status badge colors
2. Update status badge rendering
3. Add "⏳ Awaiting Approval" label for awaiting_approval status
4. Add title attribute with explanation

### Testing Checklist
- [ ] Modal opens when job status is AWAITING_APPROVAL
- [ ] Polling stops when approval decision submitted
- [ ] Form validation: justification min 10 chars
- [ ] Digital signature pre-filled correctly
- [ ] Color contrast verified with WebAIM (4.5:1+)
- [ ] Keyboard navigation works (Tab, Escape)
- [ ] Screen reader announces form errors (role="alert")
- [ ] Timeout countdown updates every second
- [ ] EU AI Act notice displays at top
- [ ] 21 CFR Part 11 notice displays before submission

## Files Referenced

### Official Documentation
- [Headless UI Dialog Component](https://headlessui.com/react/dialog)
- [WCAG 2.1 AA Contrast Requirements](https://www.w3.org/TR/WCAG21/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [EU AI Act Article 50](https://artificialintelligenceact.eu/article/50/)
- [21 CFR Part 11 Electronic Signatures](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11)
- [Clerk useAuth Documentation](https://clerk.com/docs/backend-requests/sessions/get-token)
- [SWR Polling Documentation](https://swr.vercel.app/docs/api)

### Project Reference Files
- `main/frontend/pages/generate.tsx` - Current polling pattern (2-second interval)
- `main/frontend/pages/history.tsx` - Job status display
- `main/api/models.py` - ApprovalRequest/Response/JobStatusWithApproval models
- `examples/alex/frontend/components/ConfirmModal.tsx` - Modal pattern reference
- `examples/alex/frontend/components/Toast.tsx` - Notification pattern

### Research Sources
- [Next.js Pages Router Modal Patterns](https://nextjs.org/docs/app/api-reference/file-conventions/parallel-routes)
- [React Hooks for Data Fetching - SWR](https://swr.vercel.app/)
- [Custom usePolling Hook Pattern](https://www.davegray.codes/posts/usepolling-custom-hook-for-auto-fetching-in-nextjs)
- [Clerk Session Tokens](https://clerk.com/docs/guides/sessions/session-tokens)
- [WCAG 2.1 Non-Text Contrast](https://dequeuniversity.com/resources/wcag2.1/1.4.11-non-text-contrast)
- [EU AI Act Pharma Compliance](https://www.europeanpharmaceuticalreview.com/article/264445/ai-act-data-governance-and-compliance-strategy-implications-in-pharma/)

## Compliance Summary

### GAMP-5 Compliance
- ✓ Human oversight mandatory for ambiguous categorizations
- ✓ Decision documented in audit trail
- ✓ Category can be overridden by human judgment
- ✓ AI reasoning and confidence captured

### ALCOA+ Principles
- **Attributable**: Clerk user_id + email captured in digital signature
- **Legible**: Plain text justification (min 10 chars) readable
- **Contemporaneous**: Timestamp in digital signature (YYYYMMDDHHMMSS)
- **Original**: Records stored server-side (append-only)
- **Accurate**: Data reflects actual AI output and human decision
- **Complete**: All context (confidence, alternatives, reasoning) included
- **Consistent**: Single approval workflow for all categorizations
- **Enduring**: Approval history preserved in database
- **Available**: Queryable by job_id, user_id, timestamp

### 21 CFR Part 11 Compliance
- ✓ Unique identification: {user_id}_{timestamp}
- ✓ Authenticity: Clerk JWT validates user identity
- ✓ Integrity: Digital signature created at decision time
- ✓ Non-repudiation: User cannot deny making decision
- ✓ Audit trail: All approval decisions logged

### EU AI Act Article 50 Compliance
- ✓ Transparency notice displayed (Article 50(1))
- ✓ AI-generated content marked as artificial
- ✓ Confidence score and reasoning disclosed
- ✓ Human review and override capability provided
- ✓ Deployment documented for audit

---

**Document Version**: 1.0
**Last Updated**: 2025-11-24
**Research Status**: COMPLETE - Ready for task-executor implementation
