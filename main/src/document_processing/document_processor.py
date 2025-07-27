"""
Document Processor for Pharmaceutical URS Documents

This module provides the main document processing pipeline that coordinates
various components to extract structured information from URS documents.
It integrates LlamaParse, section identification, metadata extraction,
and chart processing into a unified workflow.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime, UTC
from uuid import uuid4

from .llama_parse_client import LlamaParseClient
from .section_identifier import SectionIdentifier
from .metadata_extractor import MetadataExtractor
from .chart_extractor import ChartExtractor


class DocumentProcessor:
    """
    Main document processing coordinator for URS documents.
    
    This class orchestrates the complete document processing pipeline,
    from parsing raw documents to extracting structured information
    ready for GAMP-5 categorization.
    """
    
    def __init__(
        self,
        llama_parse_client: Optional[LlamaParseClient] = None,
        section_identifier: Optional[SectionIdentifier] = None,
        metadata_extractor: Optional[MetadataExtractor] = None,
        chart_extractor: Optional[ChartExtractor] = None,
        verbose: bool = False
    ):
        """
        Initialize document processor with component instances.
        
        Args:
            llama_parse_client: LlamaParse client instance
            section_identifier: Section identification component
            metadata_extractor: Metadata extraction component
            chart_extractor: Chart extraction component
            verbose: Enable verbose logging
        """
        self.logger = logging.getLogger(__name__)
        if verbose:
            self.logger.setLevel(logging.DEBUG)
            
        # Initialize components or use provided instances
        self.llama_parse_client = llama_parse_client or LlamaParseClient(verbose=verbose)
        self.section_identifier = section_identifier or SectionIdentifier()
        self.metadata_extractor = metadata_extractor or MetadataExtractor()
        self.chart_extractor = chart_extractor or ChartExtractor()
        
    def process_document(
        self,
        file_path: Union[str, Path],
        document_name: Optional[str] = None,
        document_version: Optional[str] = None,
        author: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Process a complete URS document through the pipeline.
        
        Args:
            file_path: Path to the document file
            document_name: Optional document name override
            document_version: Document version
            author: Document author
            use_cache: Whether to use cached parsing results
            
        Returns:
            Structured document data containing:
            {
                "document_id": Unique document identifier,
                "metadata": Document metadata,
                "content": Full document text,
                "sections": Identified sections with content,
                "charts": Extracted charts and diagrams,
                "tables": Extracted tables,
                "requirements": Extracted requirements,
                "processing_info": Processing metadata
            }
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
            
        self.logger.info(f"Processing document: {file_path.name}")
        processing_start = datetime.now(UTC)
        
        try:
            # Step 1: Parse document with LlamaParse
            parsed_result = self.llama_parse_client.parse_document(
                file_path, use_cache=use_cache
            )
            
            # Step 2: Extract full text content
            full_text = self.llama_parse_client.extract_text(parsed_result)
            
            # Step 3: Identify document sections
            sections = self.section_identifier.identify_sections(
                full_text, parsed_result
            )
            
            # Step 4: Extract metadata
            metadata = self.metadata_extractor.extract_metadata(
                parsed_result,
                document_name=document_name or file_path.name,
                document_version=document_version,
                author=author
            )
            
            # Step 5: Process charts and diagrams
            charts = self.chart_extractor.process_charts(
                parsed_result.get("charts", []),
                file_path
            )
            
            # Step 6: Extract tables and requirements
            tables = self._extract_tables(sections)
            requirements = self._extract_requirements(sections)
            
            # Build final result
            processing_time = (datetime.now(UTC) - processing_start).total_seconds()
            
            result = {
                "document_id": str(uuid4()),
                "metadata": metadata,
                "content": full_text,
                "sections": sections,
                "charts": charts,
                "tables": tables,
                "requirements": requirements,
                "processing_info": {
                    "processing_time_seconds": processing_time,
                    "cache_hit": parsed_result.get("cache_hit", False),
                    "page_count": parsed_result["metadata"]["page_count"],
                    "chart_count": len(charts),
                    "table_count": len(tables),
                    "requirement_count": len(requirements),
                    "timestamp": datetime.now(UTC).isoformat()
                }
            }
            
            self.logger.info(
                f"Document processed successfully: "
                f"{len(sections)} sections, {len(charts)} charts, "
                f"{len(tables)} tables, {len(requirements)} requirements"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Document processing failed: {e}")
            raise
            
    def _extract_tables(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract tables from document sections."""
        tables = []
        table_id = 0
        
        for section in sections:
            content = section.get("content", "")
            
            # Simple table detection (can be enhanced)
            if "[table" in content.lower() or "| " in content:
                # Extract table-like structures
                lines = content.split("\n")
                in_table = False
                table_lines = []
                
                for line in lines:
                    if "|" in line and len(line.split("|")) > 2:
                        in_table = True
                        table_lines.append(line)
                    elif in_table and line.strip() == "":
                        # End of table
                        if table_lines:
                            table_id += 1
                            tables.append({
                                "id": f"table_{table_id}",
                                "section": section["title"],
                                "content": "\n".join(table_lines),
                                "type": "structured"
                            })
                        in_table = False
                        table_lines = []
                        
        return tables
        
    def _extract_requirements(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract requirements from document sections."""
        requirements = []
        req_id = 0
        
        # Keywords that indicate requirements
        req_keywords = [
            "shall", "must", "will", "should", "requirement",
            "the system shall", "the software shall"
        ]
        
        for section in sections:
            content = section.get("content", "")
            sentences = content.split(".")
            
            for sentence in sentences:
                sentence_lower = sentence.lower().strip()
                
                # Check if sentence contains requirement keywords
                if any(keyword in sentence_lower for keyword in req_keywords):
                    req_id += 1
                    requirements.append({
                        "id": f"REQ_{req_id:03d}",
                        "section": section["title"],
                        "text": sentence.strip() + ".",
                        "type": self._classify_requirement(sentence_lower)
                    })
                    
        return requirements
        
    def _classify_requirement(self, requirement_text: str) -> str:
        """Classify requirement type based on content."""
        if "performance" in requirement_text or "speed" in requirement_text:
            return "performance"
        elif "security" in requirement_text or "authentication" in requirement_text:
            return "security"
        elif "interface" in requirement_text or "ui" in requirement_text:
            return "interface"
        elif "data" in requirement_text or "database" in requirement_text:
            return "data"
        elif "integration" in requirement_text or "api" in requirement_text:
            return "integration"
        else:
            return "functional"
            
    def create_categorization_input(
        self,
        processed_document: Dict[str, Any]
    ) -> str:
        """
        Create formatted input for GAMP-5 categorization from processed document.
        
        Args:
            processed_document: Output from process_document()
            
        Returns:
            Formatted text suitable for categorization agent
        """
        lines = []
        
        # Add document header
        metadata = processed_document["metadata"]
        lines.append(f"DOCUMENT: {metadata['document_name']}")
        lines.append(f"VERSION: {metadata['document_version']}")
        lines.append(f"TYPE: {metadata['document_type']}")
        lines.append("")
        
        # Add key sections
        for section in processed_document["sections"]:
            if section["importance"] == "high":
                lines.append(f"## {section['title']}")
                lines.append(section["content"][:1000])  # Limit content length
                lines.append("")
                
        # Add requirements summary
        if processed_document["requirements"]:
            lines.append("## KEY REQUIREMENTS")
            for req in processed_document["requirements"][:10]:  # Top 10 requirements
                lines.append(f"- {req['text']}")
            lines.append("")
            
        # Add technical indicators
        lines.append("## TECHNICAL INDICATORS")
        lines.append(f"- Total Requirements: {len(processed_document['requirements'])}")
        lines.append(f"- Contains Tables: {len(processed_document['tables']) > 0}")
        lines.append(f"- Contains Diagrams: {len(processed_document['charts']) > 0}")
        
        # Add any detected software types
        content_lower = processed_document["content"].lower()
        if "lims" in content_lower:
            lines.append("- Mentions LIMS (Laboratory Information Management System)")
        if "erp" in content_lower:
            lines.append("- Mentions ERP (Enterprise Resource Planning)")
        if "custom" in content_lower:
            lines.append("- Contains 'custom' references")
            
        return "\n".join(lines)