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
    standards_collection: str = "lims_standards"
    calculations_collection: str = "calculation_patterns"
    classification_mode: str = "hybrid"
    classification_confidence_threshold: float = 0.8
    upload_dir: str = "./uploads/lims"
    output_dir: str = "./output/lims"

    # RAG tuning parameters
    rag_mda_top_k: int = 3                 # LIMS_RAG_MDA_TOP_K
    rag_standards_top_k: int = 5           # LIMS_RAG_STANDARDS_TOP_K
    rag_chunk_max_size: int = 2000         # LIMS_RAG_CHUNK_MAX_SIZE
    rag_similarity_threshold: float = 0.0  # LIMS_RAG_SIMILARITY_THRESHOLD (0=no filter)

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

    @field_validator("classification_mode")
    @classmethod
    def validate_classification_mode(cls, v: str) -> str:
        allowed = {"rules", "llm", "hybrid"}
        normalized = v.strip().lower()
        if normalized not in allowed:
            raise ValueError(
                f"LIMS_CLASSIFICATION_MODE must be one of {allowed}, got '{v}'"
            )
        return normalized

    @field_validator("classification_confidence_threshold")
    @classmethod
    def validate_classification_confidence_threshold(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(
                "LIMS_CLASSIFICATION_CONFIDENCE_THRESHOLD must be between 0.0 and 1.0"
            )
        return v

    @field_validator("rag_similarity_threshold")
    @classmethod
    def validate_rag_similarity_threshold(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError(
                "LIMS_RAG_SIMILARITY_THRESHOLD must be between 0.0 and 2.0 "
                "(ChromaDB L2 distance range)"
            )
        return v


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
        standards_collection=os.getenv("LIMS_STANDARDS_COLLECTION", "lims_standards"),
        calculations_collection=os.getenv(
            "LIMS_CALCULATIONS_COLLECTION",
            "calculation_patterns",
        ),
        classification_mode=os.getenv("LIMS_CLASSIFICATION_MODE", "hybrid"),
        classification_confidence_threshold=float(
            os.getenv("LIMS_CLASSIFICATION_CONFIDENCE_THRESHOLD", "0.8")
        ),
        upload_dir=os.getenv("LIMS_UPLOAD_DIR", "./uploads/lims"),
        output_dir=os.getenv("LIMS_OUTPUT_DIR", "./output/lims"),
        rag_mda_top_k=int(os.getenv("LIMS_RAG_MDA_TOP_K", "3")),
        rag_standards_top_k=int(os.getenv("LIMS_RAG_STANDARDS_TOP_K", "5")),
        rag_chunk_max_size=int(os.getenv("LIMS_RAG_CHUNK_MAX_SIZE", "2000")),
        rag_similarity_threshold=float(
            os.getenv("LIMS_RAG_SIMILARITY_THRESHOLD", "0.0")
        ),
    )
