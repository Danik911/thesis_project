import { useEffect, useRef, useState } from 'react';
import { getApiBaseUrl } from '@/lib/authenticatedFetch';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  edits_applied?: Array<{
    sheet: string;
    action: string;
    target: Record<string, string>;
    changes?: Record<string, unknown>;
    reason: string;
  }>;
  edits_rejected?: Array<{
    raw_args: string;
    error: string;
  }>;
}

interface ChatInterfaceProps {
  jobId: string;
  onMDAUpdate: (updatedMda: Record<string, unknown>) => void;
  disabled?: boolean;
}

const SUGGESTIONS = [
  'What analyses did you extract from the PDF?',
  'Change the units of ABSORBANCE_595 to AU',
  'Why is DYE_VOLUME result type K?',
];

export default function ChatInterface({ jobId, onMDAUpdate, disabled }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (overrideInput?: string) => {
    const text = (overrideInput ?? input).trim();
    if (!text || isLoading || disabled) return;

    const userMessage: ChatMessage = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/lims/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: jobId, message: text }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(body.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: data.response,
        edits_applied: data.edits_applied,
        edits_rejected: data.edits_rejected,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      if (data.mda_template) {
        onMDAUpdate(data.mda_template);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const turnCount = messages.filter((m) => m.role === 'assistant').length;

  return (
    <div className="flex flex-col h-[500px] rounded-xl bg-slate-800/50 border border-slate-700/50">
      {/* Header */}
      <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700/50 flex items-center gap-2">
        <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
          />
        </svg>
        <h3 className="text-sm font-medium text-slate-300">LabAI Copilot</h3>
        {turnCount > 0 && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25">
            {turnCount} {turnCount === 1 ? 'turn' : 'turns'}
          </span>
        )}
      </div>

      {/* Messages container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && !isLoading ? (
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <p className="text-slate-500 text-sm">Your AI copilot for MDA refinement. Ask questions or request changes — you remain in control.</p>
            <div className="flex flex-wrap justify-center gap-2 max-w-md">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => {
                    setInput(suggestion);
                  }}
                  disabled={disabled}
                  className="px-3 py-1.5 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-lg hover:bg-emerald-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className="max-w-[80%] space-y-2">
                  <div
                    className={`px-4 py-3 rounded-xl text-sm whitespace-pre-wrap ${
                      msg.role === 'user'
                        ? 'bg-emerald-600/20 border border-emerald-500/30 text-emerald-100'
                        : 'bg-slate-700/50 border border-slate-600/30 text-slate-200'
                    }`}
                  >
                    {msg.content}
                  </div>

                  {/* Edit badges for assistant messages */}
                  {msg.role === 'assistant' && msg.edits_applied && msg.edits_applied.length > 0 && (
                    <div className="space-y-1 pl-1">
                      {msg.edits_applied.map((edit, editIdx) => (
                        <div
                          key={editIdx}
                          className="flex items-start gap-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20"
                        >
                          <svg
                            className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <span className="text-xs text-emerald-400 font-mono">
                            {edit.action} on {edit.sheet}: {edit.reason}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {msg.role === 'assistant' && msg.edits_rejected && msg.edits_rejected.length > 0 && (
                    <div className="space-y-1 pl-1">
                      {msg.edits_rejected.map((rej, rejIdx) => (
                        <div
                          key={rejIdx}
                          className="flex items-start gap-1.5 px-2.5 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20"
                        >
                          <svg
                            className="w-3.5 h-3.5 text-red-400 mt-0.5 shrink-0"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <span className="text-xs text-red-400 font-mono">Rejected: {rej.error}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="px-4 py-3 rounded-xl bg-slate-700/50 border border-slate-600/30 flex items-center gap-1">
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error display */}
      {error && (
        <div className="mx-4 mb-2 p-3 rounded-lg bg-red-500/10 border border-red-500/30">
          <p className="text-red-400 text-xs font-medium">Chat Error</p>
          <p className="text-red-300 text-xs mt-0.5 font-mono">{error}</p>
        </div>
      )}

      {/* Input area */}
      <div className="p-3 border-t border-slate-700/50 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? 'Chat disabled' : 'Ask a question or request an edit...'}
          disabled={disabled || isLoading}
          className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900/50 border border-slate-700/50 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        />
        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || isLoading || disabled}
          className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
            !input.trim() || isLoading || disabled
              ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
              : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20'
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
