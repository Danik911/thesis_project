"""
Metadata Extractor for URS Documents

This module extracts metadata from pharmaceutical URS documents,
including document properties, compliance information, and traceability data.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC


class MetadataExtractor:
    """
    Extracts metadata from pharmaceutical URS documents.
    
    This class identifies and extracts various metadata elements
    required for regulatory compliance and traceability.
    """
    
    def __init__(self):
        """Initialize metadata extractor with patterns."""
        self.logger = logging.getLogger(__name__)
        
        # Patterns for extracting metadata
        self.patterns = {
            "document_id": [
                r'Document\s+ID\s*:\s*([A-Z0-9\-]+)',
                r'Doc\s+#\s*:\s*([A-Z0-9\-]+)',
                r'URS\s+ID\s*:\s*([A-Z0-9\-]+)'
            ],
            "version": [
                r'Version\s*:\s*([\d\.]+)',
                r'Rev\s*:\s*([\d\.]+)',
                r'Revision\s*:\s*([\d\.]+)'
            ],
            "date": [
                r'Date\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Created\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Updated\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            "author": [
                r'Author\s*:\s*([A-Za-z\s\.]+)',
                r'Created\s+by\s*:\s*([A-Za-z\s\.]+)',
                r'Prepared\s+by\s*:\s*([A-Za-z\s\.]+)'
            ],
            "reviewer": [
                r'Reviewed\s+by\s*:\s*([A-Za-z\s\.]+)',
                r'Reviewer\s*:\s*([A-Za-z\s\.]+)'
            ],
            "approver": [
                r'Approved\s+by\s*:\s*([A-Za-z\s\.]+)',
                r'Approver\s*:\s*([A-Za-z\s\.]+)'
            ]
        }
        
        # Compliance keywords
        self.compliance_keywords = {
            "gamp": ["gamp", "gamp-5", "gamp 5", "gamp5"],
            "gxp": ["gxp", "glp", "gmp", "gcp"],
            "cfr": ["21 cfr part 11", "cfr part 11", "part 11"],
            "iso": ["iso 13485", "iso 9001", "iso 27001"],
            "ich": ["ich q7", "ich q9", "ich q10"]
        }
        
        # Document type indicators
        self.doc_type_indicators = {
            "urs": ["user requirement", "urs", "user requirements specification"],
            "frs": ["functional requirement", "frs", "functional specification"],
            "sds": ["software design", "sds", "design specification"],
            "vp": ["validation plan", "vp", "validation protocol"],
            "iq": ["installation qualification", "iq protocol"],
            "oq": ["operational qualification", "oq protocol"],
            "pq": ["performance qualification", "pq protocol"]
        }
        
    def extract_metadata(
        self,
        parsed_result: Dict[str, Any],
        document_name: Optional[str] = None,
        document_version: Optional[str] = None,
        author: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract metadata from parsed document.
        
        Args:
            parsed_result: LlamaParse result
            document_name: Override document name
            document_version: Override version
            author: Override author
            
        Returns:
            Dictionary containing extracted metadata
        """
        # Get first page text for header extraction
        first_page_text = ""
        if parsed_result.get("pages"):
            first_page_text = parsed_result["pages"][0].get("text", "")
        
        # Extract basic metadata
        metadata = {
            "document_name": document_name or parsed_result["metadata"]["file_name"],
            "document_version": document_version or self._extract_version(first_page_text),
            "author": author or self._extract_author(first_page_text),
            "document_type": self._determine_document_type(first_page_text),
            "compliance_standards": self._extract_compliance_standards(first_page_text),
            "approval_status": self._extract_approval_status(first_page_text),
            "traceability": self._extract_traceability_info(first_page_text),
            "file_metadata": parsed_result["metadata"],
            "extraction_timestamp": datetime.now(UTC).isoformat()
        }
        
        # Extract additional metadata from patterns
        for field, patterns in self.patterns.items():
            if field not in ["version", "author"]:  # Already handled
                value = self._extract_with_patterns(first_page_text, patterns)
                if value:
                    metadata[field] = value
        
        # Add quality indicators
        metadata["quality_indicators"] = self._assess_document_quality(parsed_result)
        
        return metadata
    
    def _extract_with_patterns(self, text: str, patterns: List[str]) -> Optional[str]:
        """Extract value using multiple regex patterns."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_version(self, text: str) -> str:
        """Extract document version."""
        version = self._extract_with_patterns(text, self.patterns["version"])
        return version or "1.0"
    
    def _extract_author(self, text: str) -> str:
        """Extract document author."""
        author = self._extract_with_patterns(text, self.patterns["author"])
        return author or "Unknown"
    
    def _determine_document_type(self, text: str) -> str:
        """Determine the type of document based on content."""
        text_lower = text.lower()
        
        for doc_type, indicators in self.doc_type_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    return doc_type.upper()
        
        return "URS"  # Default to URS
    
    def _extract_compliance_standards(self, text: str) -> List[str]:
        """Extract mentioned compliance standards."""
        text_lower = text.lower()
        standards = []
        
        for standard, keywords in self.compliance_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    standards.append(standard.upper())
                    break
        
        return list(set(standards))  # Remove duplicates
    
    def _extract_approval_status(self, text: str) -> Dict[str, Any]:
        """Extract document approval status."""
        status = {
            "is_approved": False,
            "approval_date": None,
            "approver": None,
            "reviewer": None
        }
        
        # Check for approval signatures
        reviewer = self._extract_with_patterns(text, self.patterns["reviewer"])
        approver = self._extract_with_patterns(text, self.patterns["approver"])
        
        if reviewer:
            status["reviewer"] = reviewer
        if approver:
            status["approver"] = approver
            status["is_approved"] = True
            
            # Try to find approval date
            date_match = self._extract_with_patterns(text, self.patterns["date"])
            if date_match:
                status["approval_date"] = date_match
        
        return status
    
    def _extract_traceability_info(self, text: str) -> Dict[str, Any]:
        """Extract traceability information."""
        traceability = {
            "references": [],
            "supersedes": None,
            "related_documents": []
        }
        
        # Extract references to other documents
        ref_patterns = [
            r'References?\s*:\s*([^\n]+)',
            r'See\s+also\s*:\s*([^\n]+)',
            r'Related\s+documents?\s*:\s*([^\n]+)'
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                refs = match.group(1).split(',')
                traceability["references"].extend([ref.strip() for ref in refs])
        
        # Check for superseded documents
        supersede_match = re.search(
            r'Supersedes?\s*:\s*([^\n]+)',
            text,
            re.IGNORECASE
        )
        if supersede_match:
            traceability["supersedes"] = supersede_match.group(1).strip()
        
        return traceability
    
    def _assess_document_quality(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess document quality indicators."""
        quality = {
            "completeness_score": 0.0,
            "structure_score": 0.0,
            "compliance_score": 0.0,
            "overall_score": 0.0,
            "warnings": []
        }
        
        # Assess completeness (based on page count and content)
        page_count = len(parsed_result.get("pages", []))
        if page_count >= 10:
            quality["completeness_score"] = 1.0
        elif page_count >= 5:
            quality["completeness_score"] = 0.7
        else:
            quality["completeness_score"] = 0.4
            quality["warnings"].append("Document may be incomplete (low page count)")
        
        # Assess structure (based on sections and formatting)
        if parsed_result.get("charts") or parsed_result.get("tables"):
            quality["structure_score"] = 0.8
        else:
            quality["structure_score"] = 0.5
        
        # Assess compliance (based on metadata presence)
        if self._extract_approval_status(parsed_result.get("pages", [{}])[0].get("text", ""))["is_approved"]:
            quality["compliance_score"] = 0.9
        else:
            quality["compliance_score"] = 0.5
            quality["warnings"].append("Document appears to be unapproved")
        
        # Calculate overall score
        quality["overall_score"] = (
            quality["completeness_score"] * 0.3 +
            quality["structure_score"] * 0.3 +
            quality["compliance_score"] * 0.4
        )
        
        return quality
    
    def extract_change_history(self, text: str) -> List[Dict[str, Any]]:
        """Extract document change history if present."""
        changes = []
        
        # Look for change history section
        change_section_match = re.search(
            r'Change\s+History.*?\n(.*?)(?=\n\n|\Z)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if change_section_match:
            change_text = change_section_match.group(1)
            # Parse change entries (common format: Version | Date | Description | Author)
            lines = change_text.strip().split('\n')
            
            for line in lines:
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 3:
                        changes.append({
                            "version": parts[0],
                            "date": parts[1] if len(parts) > 1 else None,
                            "description": parts[2] if len(parts) > 2 else None,
                            "author": parts[3] if len(parts) > 3 else None
                        })
        
        return changes