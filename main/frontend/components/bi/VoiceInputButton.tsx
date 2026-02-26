import { useRef, useState } from 'react';

interface VoiceInputButtonProps {
  languageCode: string;
  disabled?: boolean;
  onTranscript: (text: string) => void;
  onError: (message: string) => void;
}

type VoiceState = 'idle' | 'listening' | 'processing';

interface BrowserSpeechRecognitionResult {
  isFinal: boolean;
  0: { transcript: string };
}

interface BrowserSpeechRecognitionEvent {
  resultIndex: number;
  results: BrowserSpeechRecognitionResult[];
}

interface BrowserSpeechRecognitionErrorEvent {
  error: string;
}

interface BrowserSpeechRecognition {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  onstart: (() => void) | null;
  onresult: ((event: BrowserSpeechRecognitionEvent) => void) | null;
  onerror: ((event: BrowserSpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
}

type SpeechRecognitionCtor = new () => BrowserSpeechRecognition;

declare global {
  interface Window {
    webkitSpeechRecognition?: SpeechRecognitionCtor;
    SpeechRecognition?: SpeechRecognitionCtor;
  }
}

export default function VoiceInputButton({
  languageCode,
  disabled = false,
  onTranscript,
  onError,
}: VoiceInputButtonProps) {
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null);

  const stopRecognition = () => {
    const recognition = recognitionRef.current;
    recognitionRef.current = null;
    if (recognition) {
      recognition.stop();
    }
  };

  const startRecognition = () => {
    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition;

    if (!Recognition) {
      onError('Browser speech recognition is not available in this environment.');
      return;
    }

    const recognition = new Recognition();
    recognitionRef.current = recognition;
    recognition.lang = languageCode;
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    let finalTranscript = '';

    recognition.onstart = () => {
      setVoiceState('listening');
    };

    recognition.onresult = (event: BrowserSpeechRecognitionEvent) => {
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index];
        const transcript = result[0]?.transcript?.trim();
        if (result.isFinal && transcript) {
          finalTranscript = transcript;
        }
      }
    };

    recognition.onerror = (event: BrowserSpeechRecognitionErrorEvent) => {
      setVoiceState('idle');
      onError(`Voice recognition failed: ${event.error}`);
    };

    recognition.onend = () => {
      setVoiceState('idle');
      if (finalTranscript) {
        onTranscript(finalTranscript);
      }
      recognitionRef.current = null;
    };

    try {
      setVoiceState('processing');
      recognition.start();
    } catch (error) {
      setVoiceState('idle');
      onError(error instanceof Error ? error.message : 'Failed to start voice recognition');
    }
  };

  const handleClick = () => {
    if (disabled) {
      return;
    }

    if (voiceState === 'listening' || voiceState === 'processing') {
      stopRecognition();
      setVoiceState('idle');
      return;
    }

    startRecognition();
  };

  const isActive = voiceState === 'listening' || voiceState === 'processing';

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      title={isActive ? 'Stop voice input' : 'Start voice input'}
      className={`px-3 py-2.5 rounded-xl text-sm font-medium transition-all border ${
        disabled
          ? 'bg-slate-700 text-slate-500 border-slate-700 cursor-not-allowed'
          : isActive
            ? 'bg-cyan-600/20 border-cyan-500/40 text-cyan-200'
            : 'bg-slate-900/50 border-slate-700/50 text-slate-300 hover:border-cyan-500/40'
      }`}
    >
      <span className="inline-flex items-center gap-1.5">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3zm-7 11a7 7 0 0014 0m-7 7v4m-4 0h8"
          />
        </svg>
        {isActive ? 'Listening' : 'Voice'}
      </span>
    </button>
  );
}
