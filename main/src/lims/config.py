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
    extraction_api: str = "llamaextract"

    # MDA generation via OpenRouter (L4a)
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-5"
    chromadb_path: str = "./chroma_db_lims"
    upload_dir: str = "./uploads/lims"
    output_dir: str = "./output/lims"

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

    @field_validator("extraction_api")
    @classmethod
    def validate_extraction_api(cls, v: str) -> str:
        allowed = {"llamaextract", "llamaparse_v2"}
        normalized = v.strip().lower()
        if normalized not in allowed:
            raise ValueError(
                f"LIMS_EXTRACTION_API must be one of {allowed}, got '{v}'"
            )
        return normalized


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
        extraction_api=os.getenv("LIMS_EXTRACTION_API", "llamaextract"),
        openrouter_api_key=os.getenv("LIMS_OPENROUTER_API_KEY", ""),
        openrouter_model=os.getenv("LIMS_OPENROUTER_MODEL", "openai/gpt-5"),
        chromadb_path=os.getenv("LIMS_CHROMADB_PATH", "./chroma_db_lims"),
        upload_dir=os.getenv("LIMS_UPLOAD_DIR", "./uploads/lims"),
        output_dir=os.getenv("LIMS_OUTPUT_DIR", "./output/lims"),
    )
