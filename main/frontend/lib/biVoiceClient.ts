import { getApiBaseUrl } from '@/lib/authenticatedFetch';

export interface BIVoiceSessionBootstrap {
  voice_session_id: string;
  session_id: string;
  expires_at: string;
  stt: {
    provider: string;
    language_code: string;
    sample_rate_hz: number;
    transcribe_region: string;
    aws_transcribe_streaming: string;
  };
  tts: {
    enabled: boolean;
    provider: string | null;
    voice_id: string | null;
    output_format: string | null;
    region: string | null;
  };
}

export async function startVoiceSession(sessionId: string): Promise<BIVoiceSessionBootstrap> {
  const response = await fetch(`${getApiBaseUrl()}/bi/voice/session/${sessionId}`, {
    method: 'POST',
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Failed to start voice session (${response.status})`);
  }

  return response.json() as Promise<BIVoiceSessionBootstrap>;
}

export async function synthesizeVoiceResponse(sessionId: string, text: string): Promise<Blob> {
  const response = await fetch(`${getApiBaseUrl()}/bi/voice/tts/${sessionId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Failed to synthesize speech (${response.status})`);
  }

  return response.blob();
}
