"""BI voice router for speech session bootstrap and optional Polly TTS."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from io import BytesIO
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from main.src.bi.session_store import get_session
from main.src.bi.voice_config import get_bi_voice_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["BI-Voice"])


class VoiceTTSRequest(BaseModel):
    text: str


def _audio_media_type(output_format: str) -> str:
    if output_format == "mp3":
        return "audio/mpeg"
    if output_format == "ogg_vorbis":
        return "audio/ogg"
    if output_format == "pcm":
        return "audio/wave"
    return "application/octet-stream"


@router.post("/session/{session_id}")
async def start_voice_session(session_id: str) -> dict:
    """Return client voice session metadata for BI chat voice interactions."""
    settings = get_bi_voice_settings()

    if not settings.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BI voice feature is disabled. Set BI_VOICE_ENABLED=true to enable.",
        )

    try:
        get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    return {
        "voice_session_id": uuid4().hex,
        "session_id": session_id,
        "expires_at": expires_at.isoformat(),
        "stt": {
            "provider": "browser_speech_recognition",
            "language_code": settings.language_code,
            "sample_rate_hz": settings.sample_rate_hz,
            "transcribe_region": settings.transcribe_region,
            "aws_transcribe_streaming": "planned_next",
        },
        "tts": {
            "enabled": settings.tts_enabled,
            "provider": "aws_polly" if settings.tts_enabled else None,
            "voice_id": settings.polly_voice_id if settings.tts_enabled else None,
            "output_format": settings.polly_output_format if settings.tts_enabled else None,
            "region": settings.polly_region if settings.tts_enabled else None,
        },
    }


@router.post("/tts/{session_id}")
async def synthesize_tts(session_id: str, request: VoiceTTSRequest) -> StreamingResponse:
    """Synthesize BI copilot response text to audio with AWS Polly."""
    settings = get_bi_voice_settings()

    if not settings.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BI voice feature is disabled. Set BI_VOICE_ENABLED=true to enable.",
        )

    if not settings.tts_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BI TTS is disabled. Set BI_VOICE_TTS_ENABLED=true to enable.",
        )

    if not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TTS text must not be empty.",
        )

    try:
        get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    try:
        polly = boto3.client("polly", region_name=settings.polly_region)
        response = polly.synthesize_speech(
            Text=request.text[:3000],
            OutputFormat=settings.polly_output_format,
            VoiceId=settings.polly_voice_id,
        )
    except (BotoCoreError, ClientError) as exc:
        logger.exception("BI Polly synthesis failed for session '%s': %s", session_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BI Polly synthesis failed: {type(exc).__name__}: {exc}",
        ) from exc

    audio_stream = response.get("AudioStream")
    if audio_stream is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="BI Polly synthesis failed: response did not include AudioStream",
        )

    with audio_stream:
        data = audio_stream.read()

    buffer = BytesIO(data)
    media_type = _audio_media_type(settings.polly_output_format)

    return StreamingResponse(
        content=buffer,
        media_type=media_type,
        headers={"Content-Disposition": 'inline; filename="bi_copilot_tts.mp3"'},
    )
