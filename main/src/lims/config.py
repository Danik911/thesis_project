"""LIMS configuration loaded from environment variables.

No fallback values — missing API key raises explicit error.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, field_validator


class LIMSConfig(BaseModel):
    """Configuration for the AI4LIMS PoC."""

    llamaextract_api_key: str
    extraction_mode: str = "balanced"

    @field_validator("llamaextract_api_key")
    @classmethod
    def validate_api_key_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "LIMS_LLAMAEXTRACT_API_KEY is set but empty. "
                "Get your API key from https://cloud.llamaindex.ai"
            )
        return v

    @field_validator("extraction_mode")
    @classmethod
    def validate_extraction_mode(cls, v: str) -> str:
        allowed = {"fast", "balanced", "premium"}
        if v.lower() not in allowed:
            raise ValueError(
                f"LIMS_EXTRACTION_MODE must be one of {allowed}, got '{v}'"
            )
        return v.lower()


def get_lims_config() -> LIMSConfig:
    """Load LIMS config from LIMS_* environment variables.

    Raises:
        ValueError: If LIMS_LLAMAEXTRACT_API_KEY is missing or empty.
    """
    api_key = os.getenv("LIMS_LLAMAEXTRACT_API_KEY")
    if not api_key:
        raise ValueError(
            "LIMS_LLAMAEXTRACT_API_KEY environment variable is not set. "
            "Get your API key from https://cloud.llamaindex.ai and add it to .env.local"
        )

    return LIMSConfig(
        llamaextract_api_key=api_key,
        extraction_mode=os.getenv("LIMS_EXTRACTION_MODE", "balanced"),
    )
