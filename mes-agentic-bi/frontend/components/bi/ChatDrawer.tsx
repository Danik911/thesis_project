import { useEffect, useRef, useState } from 'react';

import VoiceInputButton from '@/components/bi/VoiceInputButton';
import { startVoiceSession, synthesizeVoiceResponse } from '@/lib/biVoiceClient';
import { authenticatedFetch } from '@/lib/authenticatedFetch';
import type { BIChatMessage, BIChatResponse, BIFilterDef } from '@/types/bi';

interface ChatDrawerProps {
  sessionId: string;
  onFiltersChanged: (copilotFilters?: BIFilterDef[]) => Promise<void>;
  getAccessToken: () => Promise<string | null>;
  onTraceId?: (traceId: string) => void;
}

const SUGGESTIONS = [
  'Show a summary of this dataset',
  'How many unique values are in each column?',
  'Remove all filters',
];

export default function ChatDrawer({
  sessionId,
  onFiltersChanged,
  getAccessToken,
  onTraceId,
}: ChatDrawerProps) {
  const [messages, setMessages] = useState<BIChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [voiceLanguageCode, setVoiceLanguageCode] = useState('en-US');
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [playVoiceResponse, setPlayVoiceResponse] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    let mounted = true;

    const bootstrapVoice = async () => {
      try {
        const response = await startVoiceSession(sessionId, getAccessToken);
        if (!mounted) return;
        setVoiceEnabled(true);
        setVoiceLanguageCode(response.stt.language_code || 'en-US');
        setTtsEnabled(Boolean(response.tts.enabled));
      } catch (bootstrapError) {
        if (!mounted) return;
        setVoiceEnabled(false);
        setTtsEnabled(false);
        setPlayVoiceResponse(false);
        const message = bootstrapError instanceof Error ? bootstrapError.message : String(bootstrapError);
        setError(message);
      }
    };

    bootstrapVoice();

    return () => {
      mounted = false;
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
    };
  }, [sessionId]);

  const playTts = async (text: string) => {
    const audioBlob = await synthesizeVoiceResponse(sessionId, text, getAccessToken);
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    currentAudioRef.current = audio;
    audio.onended = () => {
      URL.revokeObjectURL(audioUrl);
      currentAudioRef.current = null;
    };
    await audio.play();
  };

  useEffect(() => {
    if (expanded) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, expanded]);

  const handleSend = async (overrideInput?: string) => {
    const text = (overrideInput ?? input).trim();
    if (!text || isLoading) return;

    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setInput('');
    setIsLoading(true);
    setError(null);
    setExpanded(true);

    try {
      const response = await authenticatedFetch(`/bi/chat/${sessionId}`, getAccessToken, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail || `HTTP ${response.status}`);
      }

      const data: BIChatResponse = await response.json();

      if (data.langfuse_trace_id) {
        onTraceId?.(data.langfuse_trace_id);
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.response,
          tool_calls: data.tool_calls,
          filters_changed: data.filters_changed,
        },
      ]);

      if (data.filters_changed) {
        await onFiltersChanged(data.active_filters);
      }

      if (playVoiceResponse && ttsEnabled) {
        await playTts(data.response);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
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
    <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 overflow-hidden flex flex-col">
      {/* Header bar — always visible, clickable to toggle */}
      <div
        onClick={() => setExpanded((prev) => !prev)}
        className="flex items-center gap-2 px-4 py-3 bg-slate-800/80 border-b border-slate-700/50 cursor-pointer select-none shrink-0"
      >
        <svg className="w-4 h-4 text-cyan-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
          />
        </svg>
        <span className="text-sm font-medium text-slate-300">Data Copilot</span>
        {turnCount > 0 && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-400 border border-cyan-500/25">
            {turnCount} {turnCount === 1 ? 'turn' : 'turns'}
          </span>
        )}
        <div className="flex-1" />
        {ttsEnabled && (
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              setPlayVoiceResponse((prev) => !prev);
            }}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
              playVoiceResponse
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                : 'bg-slate-700/60 text-slate-400 border border-slate-600/50 hover:text-slate-300'
            }`}
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072M17.95 6.05a8 8 0 010 11.9M6.5 8.5l4-3v13l-4-3H4a1 1 0 01-1-1v-5a1 1 0 011-1h2.5z" />
            </svg>
            Voice
          </button>
        )}
        {/* Chevron icon */}
        <svg
          className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {/* Expandable body — messages + input */}
      {expanded && (
        <>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0" style={{ maxHeight: '300px' }}>
            {messages.length === 0 && !isLoading ? (
              <div className="flex flex-col items-center justify-center h-full gap-4">
                <p className="text-slate-500 text-sm text-center">
                  Ask questions about your data or apply filters using natural language.
                </p>
                <div className="flex flex-wrap justify-center gap-2 max-w-md">
                  {SUGGESTIONS.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => handleSend(suggestion)}
                      className="px-3 py-1.5 text-xs text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 rounded-lg hover:bg-cyan-500/20 transition-colors"
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
                            ? 'bg-cyan-600/20 border border-cyan-500/30 text-cyan-100'
                            : 'bg-slate-700/50 border border-slate-600/30 text-slate-200'
                        }`}
                      >
                        {msg.content}
                      </div>

                      {/* Filter action badges for assistant messages */}
                      {msg.role === 'assistant' && msg.tool_calls && msg.tool_calls.length > 0 && (
                        <div className="space-y-1 pl-1">
                          {msg.tool_calls
                            .filter((tc) => tc.tool === 'apply_filter' || tc.tool === 'remove_filter')
                            .map((tc, tcIdx) => {
                              const tcInput = (tc.input ?? {}) as {
                                column?: string;
                                operator?: string;
                                value?: string | number | boolean | null;
                              };
                              const label =
                                tc.tool === 'apply_filter'
                                  ? `Filter applied: ${tcInput.column ?? ''} ${tcInput.operator ?? ''} ${tcInput.value ?? ''}`
                                  : `Filter removed: ${tcInput.column ?? ''}`;
                              return (
                                <div
                                  key={tcIdx}
                                  className="flex items-start gap-1.5 px-2.5 py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20"
                                >
                                  <svg
                                    className="w-3.5 h-3.5 text-cyan-400 mt-0.5 shrink-0"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                  >
                                    <path
                                      fillRule="evenodd"
                                      d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L13 10.414V17a1 1 0 01-1.447.894l-4-2A1 1 0 017 15v-4.586L3.293 6.707A1 1 0 013 6V3z"
                                      clipRule="evenodd"
                                    />
                                  </svg>
                                  <span className="text-xs text-cyan-400 font-mono">{label}</span>
                                </div>
                              );
                            })}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {/* Loading dots */}
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

          {/* Error banner */}
          {error && (
            <div className="mx-3 mb-2 p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 shrink-0">
              <p className="text-red-400 text-xs font-medium">Chat Error</p>
              <p className="text-red-300 text-xs mt-0.5 font-mono">{error}</p>
            </div>
          )}

          {/* Input area */}
          <div className="p-3 border-t border-slate-700/50 flex gap-2 shrink-0">
            {voiceEnabled && (
              <VoiceInputButton
                languageCode={voiceLanguageCode}
                disabled={isLoading}
                onTranscript={(transcript) => {
                  setInput(transcript);
                  handleSend(transcript);
                }}
                onError={(message) => setError(message)}
              />
            )}

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your data or apply filters..."
              disabled={isLoading}
              className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900/50 border border-slate-700/50 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            />
            <button
              type="button"
              onClick={() => handleSend()}
              disabled={isLoading}
              className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isLoading
                  ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                  : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-600/20'
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
        </>
      )}
    </div>
  );
}
