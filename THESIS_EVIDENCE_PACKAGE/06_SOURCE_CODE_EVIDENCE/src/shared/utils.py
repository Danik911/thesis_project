"""
Shared utility functions for the pharmaceutical test generation system.

Provides logging setup, text processing, and event handling utilities
that support GAMP-5 compliant operations.
"""

import logging
import sys
from pathlib import Path
from typing import Any


def setup_logging(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    Setup standardized logging for the pharmaceutical system.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatter with timestamp and detailed info
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Setup handlers
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )

    # Get logger for this module
    logger = logging.getLogger(__name__)

    # Reduce noise from verbose libraries
    logging.getLogger("llama_index").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
    return logger


def chunk_large_text(text: str, max_tokens: int = 1000) -> list[dict[str, Any]]:
    """
    Chunk large text content for processing while preserving context.
    
    Args:
        text: Text content to chunk
        max_tokens: Maximum tokens per chunk
        
    Returns:
        List of chunks with metadata
    """
    if not text:
        return []

    # Simple word-based chunking (can be enhanced with token counting)
    words = text.split()
    if not words:
        return []

    chunks = []
    current_chunk = []
    current_size = 0

    # Approximate tokens as words * 1.3 (rough estimate)
    words_per_chunk = max_tokens // 1.3

    for word in words:
        current_chunk.append(word)
        current_size += 1

        if current_size >= words_per_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "tokens": len(current_chunk),  # Approximation
                "metadata": {
                    "chunk_index": len(chunks),
                    "word_count": len(current_chunk),
                    "character_count": len(chunk_text)
                }
            })
            current_chunk = []
            current_size = 0

    # Add remaining words as final chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append({
            "text": chunk_text,
            "tokens": len(current_chunk),
            "metadata": {
                "chunk_index": len(chunks),
                "word_count": len(current_chunk),
                "character_count": len(chunk_text)
            }
        })

    return chunks


def should_chunk_text(text: str, max_tokens: int = 1000) -> bool:
    """
    Determine if text should be chunked based on size.
    
    Args:
        text: Text to evaluate
        max_tokens: Maximum tokens before chunking
        
    Returns:
        bool: True if chunking is recommended
    """
    if not text:
        return False

    # Rough token estimation: words * 1.3
    word_count = len(text.split())
    estimated_tokens = word_count * 1.3

    return estimated_tokens > max_tokens


def count_tokens(text: str) -> int:
    """
    Estimate token count for text content.
    
    Args:
        text: Text to count tokens for
        
    Returns:
        int: Estimated token count
    """
    if not text:
        return 0

    # Simple word-based token estimation
    # More sophisticated implementations could use tiktoken
    words = text.split()
    return int(len(words) * 1.3)  # Rough approximation


def format_compliance_metadata(data: dict[str, Any]) -> dict[str, Any]:
    """
    Format metadata for GAMP-5 compliance requirements.
    
    Args:
        data: Raw metadata dictionary
        
    Returns:
        Dict with compliance-formatted metadata
    """
    from datetime import UTC, datetime
    from uuid import uuid4

    compliance_data = {
        "entry_id": str(uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "compliance_version": "GAMP-5",
        "alcoa_plus": {
            "attributable": True,  # Can be traced to person
            "legible": True,       # Readable format
            "contemporaneous": True,  # Recorded at time of activity
            "original": True,      # First recording
            "accurate": True       # Free from errors
        },
        "cfr_part_11": {
            "electronic_signature": None,  # To be added if required
            "audit_trail": True,
            "tamper_evident": True
        }
    }

    # Merge with original data
    compliance_data.update(data)
    return compliance_data


# Constants for text processing
MAX_SINGLE_ANSWER_TOKENS = 1000
MAX_AGGREGATED_TOKENS = 5000
