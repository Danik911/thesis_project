"""LIMS configuration loaded from environment variables.

No fallback values — missing API key raises explicit error.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, field_validator

MAX_CHROMA_L2_DISTANCE = 2.0


class LIMSConfig(BaseModel):
    """Configuration for the AI4LIMS PoC."""

    llamaextract_api_key: str
    extraction_mode: str = "multimodal"
    extraction_api: str = "llamaextract"
    extraction_target: str = "per_doc"
    extract_parse_model: str = ""
    extract_model: str = ""
    extract_cite_sources: bool = True
    extract_use_reasoning: bool = True
    extract_confidence_scores: bool = True
    extract_num_pages_context: int = 2
    extract_chunk_mode: str = "page"
    extract_page_range: str = ""
    extract_high_resolution_mode: bool = True
    extract_invalidate_cache: bool = False
    extraction_quality_gate_enabled: bool = True
    require_validated_extraction: bool = True
    extraction_max_null_ratio: float = 0.55

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
    bm25_weight: float = 0.4              # LIMS_BM25_WEIGHT
    semantic_weight: float = 0.6          # LIMS_SEMANTIC_WEIGHT
    query_augmentation_enabled: bool = True  # LIMS_QUERY_AUGMENTATION_ENABLED
    query_augmentation_max_queries: int = 4  # LIMS_QUERY_AUGMENTATION_MAX_QUERIES
    metadata_boost_enabled: bool = True      # LIMS_METADATA_BOOST_ENABLED
    priority_sheet_boost: float = 0.15       # LIMS_PRIORITY_SHEET_BOOST
    token_match_boost: float = 0.2           # LIMS_TOKEN_MATCH_BOOST

    # P1 retrieval quality + review routing controls
    retrieval_quality_gate_enabled: bool = True
    retrieval_min_results: int = 2
    retrieval_max_distance: float = 1.2
    retrieval_min_avg_token_overlap: float = 1.0
    retrieval_min_method_match_ratio: float = 0.5
    low_confidence_review_threshold: float = 0.75

    @field_validator("llamaextract_api_key")
    @classmethod
    def validate_api_key_not_empty(cls, v: str) -> str:
        if not v.strip():
            msg = (
                "LIMS_LLAMAEXTRACT_API_KEY is set but empty. "
                "Get your API key from https://cloud.llamaindex.ai"
            )
            raise ValueError(msg)
        return v

    @field_validator("extraction_mode")
    @classmethod
    def validate_extraction_mode(cls, v: str) -> str:
        allowed = {"fast", "balanced", "multimodal", "premium"}
        if v.lower() not in allowed:
            msg = f"LIMS_EXTRACTION_MODE must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return v.lower()

    @field_validator("extraction_target")
    @classmethod
    def validate_extraction_target(cls, v: str) -> str:
        allowed = {"per_doc", "per_page", "per_table_row"}
        normalized = v.strip().lower()
        if normalized not in allowed:
            msg = f"LIMS_EXTRACTION_TARGET must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return normalized

    @field_validator("extract_chunk_mode")
    @classmethod
    def validate_extract_chunk_mode(cls, v: str) -> str:
        allowed = {"page", "section"}
        normalized = v.strip().lower()
        if normalized not in allowed:
            msg = f"LIMS_EXTRACT_CHUNK_MODE must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return normalized

    @field_validator("extract_num_pages_context")
    @classmethod
    def validate_extract_num_pages_context(cls, v: int) -> int:
        if v < 0:
            msg = "LIMS_EXTRACT_NUM_PAGES_CONTEXT must be >= 0"
            raise ValueError(msg)
        return v

    @field_validator("extraction_api")
    @classmethod
    def validate_extraction_api(cls, v: str) -> str:
        allowed = {"llamaextract", "llamaparse_v2"}
        normalized = v.strip().lower()
        if normalized not in allowed:
            msg = f"LIMS_EXTRACTION_API must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return normalized

    @field_validator("classification_mode")
    @classmethod
    def validate_classification_mode(cls, v: str) -> str:
        allowed = {"rules", "llm", "hybrid"}
        normalized = v.strip().lower()
        if normalized not in allowed:
            msg = f"LIMS_CLASSIFICATION_MODE must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return normalized

    @field_validator("classification_confidence_threshold")
    @classmethod
    def validate_classification_confidence_threshold(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            msg = "LIMS_CLASSIFICATION_CONFIDENCE_THRESHOLD must be between 0.0 and 1.0"
            raise ValueError(msg)
        return v

    @field_validator("rag_similarity_threshold")
    @classmethod
    def validate_rag_similarity_threshold(cls, v: float) -> float:
        if not 0.0 <= v <= MAX_CHROMA_L2_DISTANCE:
            msg = (
                "LIMS_RAG_SIMILARITY_THRESHOLD must be between 0.0 and 2.0 "
                "(ChromaDB L2 distance range)"
            )
            raise ValueError(msg)
        return v

    @field_validator("query_augmentation_max_queries")
    @classmethod
    def validate_query_augmentation_max_queries(cls, v: int) -> int:
        if v < 1:
            msg = "LIMS_QUERY_AUGMENTATION_MAX_QUERIES must be >= 1"
            raise ValueError(msg)
        return v

    @field_validator("retrieval_min_results")
    @classmethod
    def validate_retrieval_min_results(cls, v: int) -> int:
        if v < 1:
            msg = "LIMS_RETRIEVAL_MIN_RESULTS must be >= 1"
            raise ValueError(msg)
        return v

    @field_validator("extraction_max_null_ratio")
    @classmethod
    def validate_extraction_max_null_ratio(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            msg = "LIMS_EXTRACTION_MAX_NULL_RATIO must be between 0.0 and 1.0"
            raise ValueError(msg)
        return v

    @field_validator(
        "retrieval_max_distance",
        "retrieval_min_avg_token_overlap",
        "retrieval_min_method_match_ratio",
        "low_confidence_review_threshold",
    )
    @classmethod
    def validate_unit_interval_or_positive(cls, v: float, info) -> float:
        field_name = info.field_name
        if field_name == "retrieval_min_avg_token_overlap":
            if v < 0.0:
                msg = "LIMS_RETRIEVAL_MIN_AVG_TOKEN_OVERLAP must be >= 0.0"
                raise ValueError(msg)
            return v

        if field_name == "retrieval_max_distance":
            if not 0.0 <= v <= MAX_CHROMA_L2_DISTANCE:
                msg = "LIMS_RETRIEVAL_MAX_DISTANCE must be between 0.0 and 2.0"
                raise ValueError(msg)
            return v

        if not 0.0 <= v <= 1.0:
            msg = f"{field_name} must be between 0.0 and 1.0"
            raise ValueError(msg)
        return v

    @field_validator("priority_sheet_boost", "token_match_boost")
    @classmethod
    def validate_non_negative_boost(cls, v: float) -> float:
        if v < 0.0:
            msg = "RAG boost values must be >= 0.0"
            raise ValueError(msg)
        return v


def _parse_bool_env(var_name: str, *, default: bool) -> bool:
    value = os.getenv(var_name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    msg = (
        f"{var_name} must be a boolean value "
        f"(true/false, 1/0, yes/no), got '{value}'"
    )
    raise ValueError(msg)


def get_lims_config() -> LIMSConfig:
    """Load LIMS config from LIMS_* environment variables.

    Raises:
        ValueError: If LIMS_LLAMAEXTRACT_API_KEY is missing or empty.
    """
    api_key = os.getenv("LIMS_LLAMAEXTRACT_API_KEY")
    if not api_key:
        msg = (
            "LIMS_LLAMAEXTRACT_API_KEY environment variable is not set. "
            "Get your API key from https://cloud.llamaindex.ai and add it to .env.local"
        )
        raise ValueError(msg)

    return LIMSConfig(
        llamaextract_api_key=api_key,
        extraction_mode=os.getenv("LIMS_EXTRACTION_MODE", "multimodal"),
        extraction_api=os.getenv("LIMS_EXTRACTION_API", "llamaextract"),
        extraction_target=os.getenv("LIMS_EXTRACTION_TARGET", "per_doc"),
        extract_parse_model=os.getenv("LIMS_EXTRACT_PARSE_MODEL", ""),
        extract_model=os.getenv("LIMS_EXTRACT_MODEL", ""),
        extract_cite_sources=_parse_bool_env("LIMS_EXTRACT_CITE_SOURCES", default=True),
        extract_use_reasoning=_parse_bool_env("LIMS_EXTRACT_USE_REASONING", default=True),
        extract_confidence_scores=_parse_bool_env(
            "LIMS_EXTRACT_CONFIDENCE_SCORES", default=True
        ),
        extract_num_pages_context=int(os.getenv("LIMS_EXTRACT_NUM_PAGES_CONTEXT", "2")),
        extract_chunk_mode=os.getenv("LIMS_EXTRACT_CHUNK_MODE", "page"),
        extract_page_range=os.getenv("LIMS_EXTRACT_PAGE_RANGE", ""),
        extract_high_resolution_mode=_parse_bool_env(
            "LIMS_EXTRACT_HIGH_RESOLUTION_MODE", default=True
        ),
        extract_invalidate_cache=_parse_bool_env("LIMS_EXTRACT_INVALIDATE_CACHE", default=False),
        extraction_quality_gate_enabled=_parse_bool_env(
            "LIMS_EXTRACTION_QUALITY_GATE_ENABLED",
            default=True,
        ),
        require_validated_extraction=_parse_bool_env(
            "LIMS_REQUIRE_VALIDATED_EXTRACTION",
            default=True,
        ),
        extraction_max_null_ratio=float(
            os.getenv("LIMS_EXTRACTION_MAX_NULL_RATIO", "0.55")
        ),
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
        bm25_weight=float(os.getenv("LIMS_BM25_WEIGHT", "0.4")),
        semantic_weight=float(os.getenv("LIMS_SEMANTIC_WEIGHT", "0.6")),
        query_augmentation_enabled=_parse_bool_env(
            "LIMS_QUERY_AUGMENTATION_ENABLED",
            default=True,
        ),
        query_augmentation_max_queries=int(
            os.getenv("LIMS_QUERY_AUGMENTATION_MAX_QUERIES", "4")
        ),
        metadata_boost_enabled=_parse_bool_env(
            "LIMS_METADATA_BOOST_ENABLED",
            default=True,
        ),
        priority_sheet_boost=float(os.getenv("LIMS_PRIORITY_SHEET_BOOST", "0.15")),
        token_match_boost=float(os.getenv("LIMS_TOKEN_MATCH_BOOST", "0.2")),
        retrieval_quality_gate_enabled=_parse_bool_env(
            "LIMS_RETRIEVAL_QUALITY_GATE_ENABLED",
            default=True,
        ),
        retrieval_min_results=int(os.getenv("LIMS_RETRIEVAL_MIN_RESULTS", "2")),
        retrieval_max_distance=float(os.getenv("LIMS_RETRIEVAL_MAX_DISTANCE", "1.2")),
        retrieval_min_avg_token_overlap=float(
            os.getenv("LIMS_RETRIEVAL_MIN_AVG_TOKEN_OVERLAP", "1.0")
        ),
        retrieval_min_method_match_ratio=float(
            os.getenv("LIMS_RETRIEVAL_MIN_METHOD_MATCH_RATIO", "0.5")
        ),
        low_confidence_review_threshold=float(
            os.getenv("LIMS_LOW_CONFIDENCE_REVIEW_THRESHOLD", "0.75")
        ),
    )
