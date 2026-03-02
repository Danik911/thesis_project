import { authenticatedFetch } from '@/lib/authenticatedFetch';

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

export async function startVoiceSession(
  sessionId: string,
  getAccessToken: () => Promise<string | null>,
): Promise<BIVoiceSessionBootstrap> {
  const response = await authenticatedFetch(
    `/bi/voice/session/${sessionId}`,
    getAccessToken,
    { method: 'POST' },
  );

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Failed to start voice session (${response.status})`);
  }

  return response.json() as Promise<BIVoiceSessionBootstrap>;
}

export async function synthesizeVoiceResponse(
  sessionId: string,
  text: string,
  getAccessToken: () => Promise<string | null>,
): Promise<Blob> {
  const response = await authenticatedFetch(
    `/bi/voice/tts/${sessionId}`,
    getAccessToken,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    },
  );

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Failed to synthesize speech (${response.status})`);
  }

  return response.blob();
}
