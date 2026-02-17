# Task L6 — Full HITL UI: Chat, Review Flow, Real-Time Updates, Export

**Phase:** 6 (Full HITL UI) | **PRP Tasks Merged:** L6.1, L6.2, L6.3, L6.4
**Dependencies:** Task L5 (E2E Testing), Task L3 (MDAViewer component)
**Branch:** `prjoject_p_protatype`

---

## Objective

Build the complete demo-ready UI: Upload PDF -> AI extraction -> MDA table display -> chat refinement with real-time table updates -> human approval -> XLSX download. This is the final phase that makes the PoC stakeholder-presentable.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/frontend/components/ChatInterface.tsx` | Chat UI: message history, input field, streaming indicator, edit action highlights |
| `main/frontend/components/LIMSStepIndicator.tsx` | Pipeline stage indicator (Extract -> Review -> Approve -> Export) |

## Files to Modify

| File | Change |
|------|--------|
| `main/frontend/pages/lims.tsx` | Major rewrite: multi-step flow with jobId state, status polling, ChatInterface, approve + export buttons |
| `main/frontend/components/MDAViewer.tsx` | Add modification highlighting for changed cells, accept refresh callback |

---

## Implementation Details

### 1. ChatInterface.tsx — Chat Panel

```tsx
import { useState, useRef, useEffect } from 'react';
import { getApiBaseUrl } from '@/lib/authenticatedFetch';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  edits?: Array<{
    sheet: string;
    action: string;
    target: Record<string, string>;
    reason: string;
    error?: string;
  }>;
}

interface ChatInterfaceProps {
  jobId: string;
  onMDAUpdate: (updatedMda: Record<string, unknown>) => void;
  disabled?: boolean;
}

export default function ChatInterface({ jobId, onMDAUpdate, disabled }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading || disabled) return;

    const userMsg: ChatMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/lims/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: jobId, message: input }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: data.response,
        edits: data.edits_applied,
      };
      setMessages(prev => [...prev, assistantMsg]);

      // Notify parent of MDA updates
      if (data.updated_mda) {
        onMDAUpdate(data.updated_mda);
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${err instanceof Error ? err.message : String(err)}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[500px] rounded-xl bg-slate-800/50 border border-slate-700/50">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700/50 bg-slate-800/80">
        <h3 className="text-sm font-medium text-emerald-400">MDA Review Chat</h3>
        <p className="text-xs text-slate-500">Ask questions or request modifications</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center mt-8 space-y-2">
            <p className="text-slate-500 text-sm">
              Ask questions about the extraction or request modifications.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {['Why was this classified as K-type?',
                'Change units to mg/mL',
                'Explain the analysis structure'].map(suggestion => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="text-xs px-3 py-1.5 rounded-full bg-slate-700/50 text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all border border-slate-600/30"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] px-4 py-3 rounded-xl text-sm ${
              msg.role === 'user'
                ? 'bg-emerald-600/20 text-emerald-100 border border-emerald-500/30'
                : 'bg-slate-700/50 text-slate-200 border border-slate-600/30'
            }`}>
              <p className="whitespace-pre-wrap">{msg.content}</p>

              {/* Edit action badges */}
              {msg.edits && msg.edits.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-600/30 space-y-1">
                  {msg.edits.map((edit, j) => (
                    <div key={j} className={`text-xs px-2 py-1 rounded ${
                      edit.error
                        ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    }`}>
                      {edit.error
                        ? `Rejected: ${edit.error}`
                        : `${edit.action} on ${edit.sheet}: ${edit.reason}`}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="px-4 py-3 rounded-xl bg-slate-700/50 border border-slate-600/30">
              <div className="flex items-center gap-2 text-slate-400 text-sm">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                Thinking...
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-slate-700/50 flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
          placeholder={disabled ? 'Chat disabled' : 'Ask about the MDA or request changes...'}
          disabled={disabled || loading}
          className="flex-1 bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 transition-colors"
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || loading || disabled}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg text-sm font-medium transition-all"
        >
          {loading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
}
```

### 2. LIMSStepIndicator.tsx — Pipeline Stage Indicator

Adapted from thesis `JobProgress.tsx` STAGE_LABELS/STAGE_ICONS pattern:

```tsx
interface LIMSStepIndicatorProps {
  currentStatus: string;
}

const LIMS_STAGES = [
  { key: 'EXTRACTING', label: 'Extracting', icon: '📄' },
  { key: 'GENERATING', label: 'Generating MDA', icon: '⚙️' },
  { key: 'PENDING_REVIEW', label: 'Review & Chat', icon: '👤' },
  { key: 'APPROVED', label: 'Approved', icon: '✅' },
  { key: 'EXPORTED', label: 'Exported', icon: '📥' },
];

export default function LIMSStepIndicator({ currentStatus }: LIMSStepIndicatorProps) {
  const currentIndex = LIMS_STAGES.findIndex(s => s.key === currentStatus);

  return (
    <div className="flex items-center gap-1 overflow-x-auto py-4">
      {LIMS_STAGES.map((stage, idx) => (
        <div key={stage.key} className="flex items-center gap-1">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all whitespace-nowrap ${
            idx < currentIndex
              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25'
              : idx === currentIndex
              ? 'bg-blue-500/15 text-blue-400 border border-blue-500/40 shadow-lg shadow-blue-500/10'
              : 'bg-slate-800 text-slate-500 border border-slate-700'
          }`}>
            <span>{stage.icon}</span>
            {stage.label}
          </div>
          {idx < LIMS_STAGES.length - 1 && (
            <div className={`w-4 h-px ${idx < currentIndex ? 'bg-emerald-500/50' : 'bg-slate-700'}`} />
          )}
        </div>
      ))}
    </div>
  );
}
```

### 3. lims.tsx Major Rewrite — Multi-Step Flow

The page transforms from a simple upload+JSON display to a full multi-step HITL flow:

```tsx
// New state management
const [jobId, setJobId] = useState<string | null>(null);
const [jobStatus, setJobStatus] = useState<string>('');
const [mdaData, setMdaData] = useState<Record<string, unknown> | null>(null);

// Status polling (for EXTRACTING and GENERATING phases)
useEffect(() => {
  if (!jobId || ['PENDING_REVIEW', 'APPROVED', 'EXPORTED'].includes(jobStatus)) return;
  const interval = setInterval(async () => {
    const resp = await fetch(`${getApiBaseUrl()}/lims/status/${jobId}`);
    if (resp.ok) {
      const data = await resp.json();
      setJobStatus(data.status);
      if (data.mda_template) setMdaData(data.mda_template);
    }
  }, 3000);
  return () => clearInterval(interval);
}, [jobId, jobStatus]);

// Approve handler
const handleApprove = async () => {
  const resp = await fetch(`${getApiBaseUrl()}/lims/approve/${jobId}`, { method: 'POST' });
  if (resp.ok) {
    setJobStatus('APPROVED');
  }
};

// Export handler
const handleExport = () => {
  window.open(`${getApiBaseUrl()}/lims/export/${jobId}`, '_blank');
  setJobStatus('EXPORTED');
};

// MDA update handler (from chat edits)
const handleMDAUpdate = (updated: Record<string, unknown>) => {
  setMdaData(updated);
};

// Layout structure:
// 1. Upload area (only visible when no job active)
// 2. <LIMSStepIndicator currentStatus={jobStatus} />
// 3. Conditional rendering based on status:
//    - EXTRACTING/GENERATING: Loading spinner
//    - PENDING_REVIEW: <MDAViewer> + <ChatInterface> + <ApproveButton>
//    - APPROVED: <MDAViewer> + <ExportButton>
//    - EXPORTED: <MDAViewer> + success message
```

Key UI sections for PENDING_REVIEW:

```tsx
{jobStatus === 'PENDING_REVIEW' && mdaData && (
  <>
    {/* MDA Table Viewer */}
    <MDAViewer data={mdaData} validated={true} />

    {/* Two-column: Chat + Actions */}
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
      <div className="lg:col-span-2">
        <ChatInterface
          jobId={jobId!}
          onMDAUpdate={handleMDAUpdate}
        />
      </div>
      <div className="space-y-4">
        {/* Approve button */}
        <button
          onClick={handleApprove}
          className="w-full px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-medium text-sm transition-all shadow-lg shadow-emerald-600/20"
        >
          Approve & Finalize
        </button>
        <p className="text-xs text-slate-500 text-center">
          Review the MDA and chat with AI before approving.
          This action cannot be undone.
        </p>
      </div>
    </div>
  </>
)}

{jobStatus === 'APPROVED' && mdaData && (
  <>
    <MDAViewer data={mdaData} validated={true} />
    <div className="mt-6 flex justify-center">
      <button
        onClick={handleExport}
        className="px-8 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-medium transition-all shadow-lg shadow-emerald-600/20 flex items-center gap-2"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Download XLSX
      </button>
    </div>
  </>
)}
```

### 4. MDAViewer.tsx Modifications

Add support for highlighting modified cells (optional visual enhancement):

```tsx
interface MDAViewerProps {
  data: Record<string, unknown>;
  validated: boolean;
  highlightedCells?: Set<string>;  // "sheet.rowIdx.colName" keys
}
```

---

## Reusable Patterns from Thesis

| Pattern | Source | Reuse |
|---------|--------|-------|
| Stage indicator | `main/frontend/components/JobProgress.tsx` (STAGE_LABELS, STAGE_ORDER) | Adapted for LIMS stages |
| File upload | `main/frontend/pages/lims.tsx` (drag-drop) | Already in place |
| API helper | `@/lib/authenticatedFetch` (getApiBaseUrl) | Direct reuse |
| Color scheme | Emerald throughout `lims.tsx` | Maintained |
| Layout | `main/frontend/components/Layout.tsx` | Already has LIMS nav |

---

## Testing Strategy

```bash
# 1. Start backend
uv run uvicorn main.api.app:app --port 8080

# 2. Start frontend
cd main/frontend && npm run dev

# 3. Open http://localhost:3000/lims

# 4. Full visual flow:
#    a. Upload demo_data/AND_ACS_DYE-LAB-2499.pdf
#    b. See step indicator progress: Extracting -> Generating
#    c. See 4-tab MDA table when PENDING_REVIEW
#    d. Chat: "Why is DYE_VOLUME result_type K?"
#    e. Chat: "Change the units of ABSORBANCE_595 to AU"
#    f. See table update after chat modification
#    g. Click "Approve & Finalize"
#    h. See Export button appear
#    i. Click "Download XLSX"
#    j. Open XLSX in Excel — verify 4 sheets

# 5. Verify thesis pages still work:
#    - http://localhost:3000/generate
#    - http://localhost:3000/history
```

---

## Gate Criteria (Pass/Fail) — PoC DEMO-READY

- [ ] Full visual flow: Upload -> Extract -> See Table -> Chat -> Modify -> Approve -> Download XLSX
- [ ] Step indicator shows correct current pipeline stage at each step
- [ ] Chat modifications reflect immediately in MDA table
- [ ] Approve button triggers status change; export button appears after approval
- [ ] Export button downloads XLSX with correct 4-sheet structure
- [ ] Export button disabled/hidden before approval (no bypass path)
- [ ] Chat suggestion chips help user get started
- [ ] Error states handled gracefully (network errors, API errors)
- [ ] Thesis pages (`/generate`, `/history`) still accessible
- [ ] Complete flow demo in under 5 minutes

---

## Sources

- [React useEffect + Polling](https://react.dev/reference/react/useEffect) — cleanup, dependencies, intervals
- [Next.js Pages Router](https://nextjs.org/docs/pages) — client-side data fetching
- [Tailwind CSS](https://tailwindcss.com/docs) — utility classes, animations
- [Framer Motion](https://www.framer.com/motion/) — available in project for transitions (optional)
