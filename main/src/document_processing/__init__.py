"""
Document Processing Module for Pharmaceutical Test Generation System

This module provides document processing capabilities using LlamaParse
for extracting structured information from URS documents, including:
- Text extraction with structure preservation
- Chart and diagram extraction
- Metadata extraction for traceability
- Section identification and parsing

The module is designed to work seamlessly with the GAMP-5 categorization
workflow, providing structured document data for analysis.
"""

from .chart_extractor import ChartExtractor
from .document_processor import DocumentProcessor
from .llama_parse_client import LlamaParseClient
from .metadata_extractor import MetadataExtractor
from .section_identifier import SectionIdentifier

__all__ = [
    "ChartExtractor",
    "DocumentProcessor",
    "LlamaParseClient",
    "MetadataExtractor",
    "SectionIdentifier"
]
