"""Voice feature configuration helpers for BI."""

from __future__ import annotations

from dataclasses import dataclass

from .config import get_bi_config


@dataclass(frozen=True)
class BIVoiceSettings:
    enabled: bool
    tts_enabled: bool
    transcribe_region: str
    language_code: str
    sample_rate_hz: int
    polly_region: str
    polly_voice_id: str
    polly_output_format: str


def get_bi_voice_settings() -> BIVoiceSettings:
    config = get_bi_config()
    return BIVoiceSettings(
        enabled=config.voice_enabled,
        tts_enabled=config.voice_tts_enabled,
        transcribe_region=config.voice_transcribe_region,
        language_code=config.voice_language_code,
        sample_rate_hz=config.voice_sample_rate_hz,
        polly_region=config.voice_polly_region,
        polly_voice_id=config.voice_polly_voice_id,
        polly_output_format=config.voice_polly_output_format,
    )
