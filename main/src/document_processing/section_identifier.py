"""
Section Identifier for URS Documents

This module identifies and extracts document sections from parsed URS documents.
It recognizes common pharmaceutical documentation patterns and structures.
"""

import re
import logging
from typing import List, Dict, Any, Tuple


class SectionIdentifier:
    """
    Identifies document sections in pharmaceutical URS documents.
    
    This class analyzes document structure to identify sections,
    subsections, and their hierarchical relationships.
    """
    
    def __init__(self):
        """Initialize section identifier with common patterns."""
        self.logger = logging.getLogger(__name__)
        
        # Common section headers in pharmaceutical documentation
        self.section_patterns = [
            r'^\d+\.?\s+[A-Z][A-Z\s]+$',  # 1. INTRODUCTION
            r'^[A-Z][A-Z\s]+:?\s*$',       # INTRODUCTION:
            r'^\d+\.\d+\.?\s+.+$',         # 1.1 Subsection
            r'^[IVX]+\.?\s+.+$',           # IV. Roman numerals
            r'^[A-Z]\.\s+.+$',             # A. Letter sections
        ]
        
        # Important section keywords for pharmaceutical docs
        self.important_sections = [
            "introduction", "scope", "purpose", "objective",
            "requirement", "specification", "functional",
            "technical", "system", "software", "hardware",
            "validation", "qualification", "testing",
            "security", "compliance", "regulatory",
            "risk", "assessment", "mitigation",
            "interface", "integration", "data"
        ]
        
    def identify_sections(
        self,
        full_text: str,
        parsed_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify sections in the document text.
        
        Args:
            full_text: Complete document text
            parsed_result: LlamaParse result with page data
            
        Returns:
            List of identified sections with metadata
        """
        sections = []
        
        # Split text into lines for analysis
        lines = full_text.split('\n')
        
        # Track current section
        current_section = None
        section_content = []
        section_start_line = 0
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Check if line is a section header
            if self._is_section_header(stripped_line):
                # Save previous section if exists
                if current_section:
                    sections.append(self._create_section(
                        current_section,
                        section_content,
                        section_start_line,
                        i - 1
                    ))
                
                # Start new section
                current_section = stripped_line
                section_content = []
                section_start_line = i
            else:
                # Add to current section content
                section_content.append(line)
        
        # Don't forget the last section
        if current_section:
            sections.append(self._create_section(
                current_section,
                section_content,
                section_start_line,
                len(lines) - 1
            ))
        
        # If no sections found, create a default one
        if not sections:
            sections.append({
                "title": "Document Content",
                "level": 1,
                "content": full_text,
                "start_line": 0,
                "end_line": len(lines) - 1,
                "importance": "medium",
                "subsections": []
            })
        
        # Enhance sections with additional analysis
        sections = self._enhance_sections(sections)
        
        return sections
    
    def _is_section_header(self, line: str) -> bool:
        """Check if a line is likely a section header."""
        if not line or len(line) > 100:  # Too long to be a header
            return False
            
        # Check against patterns
        for pattern in self.section_patterns:
            if re.match(pattern, line):
                return True
                
        # Check for all caps headers (common in pharma docs)
        words = line.split()
        if len(words) >= 1 and len(words) <= 5:
            if all(word.isupper() for word in words if len(word) > 2):
                return True
                
        return False
    
    def _create_section(
        self,
        title: str,
        content_lines: List[str],
        start_line: int,
        end_line: int
    ) -> Dict[str, Any]:
        """Create a section dictionary from parsed data."""
        content = '\n'.join(content_lines).strip()
        
        # Determine section level
        level = self._determine_section_level(title)
        
        # Assess importance
        importance = self._assess_section_importance(title, content)
        
        return {
            "title": title,
            "level": level,
            "content": content,
            "start_line": start_line,
            "end_line": end_line,
            "importance": importance,
            "subsections": []
        }
    
    def _determine_section_level(self, title: str) -> int:
        """Determine the hierarchical level of a section."""
        # Check for numbered sections
        if re.match(r'^\d+\.?\s+', title):
            return 1
        elif re.match(r'^\d+\.\d+\.?\s+', title):
            return 2
        elif re.match(r'^\d+\.\d+\.\d+\.?\s+', title):
            return 3
        # Check for lettered sections
        elif re.match(r'^[A-Z]\.\s+', title):
            return 2
        # Default to level 1
        return 1
    
    def _assess_section_importance(self, title: str, content: str) -> str:
        """Assess the importance of a section for GAMP-5 categorization."""
        title_lower = title.lower()
        content_lower = content.lower()
        
        # High importance sections
        high_keywords = [
            "requirement", "specification", "functional", "technical",
            "system description", "software", "validation", "qualification"
        ]
        
        for keyword in high_keywords:
            if keyword in title_lower or content_lower.count(keyword) > 3:
                return "high"
        
        # Medium importance
        medium_keywords = [
            "interface", "integration", "data", "security", "risk"
        ]
        
        for keyword in medium_keywords:
            if keyword in title_lower or content_lower.count(keyword) > 2:
                return "medium"
        
        return "low"
    
    def _enhance_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance sections with additional metadata and relationships."""
        # Build section hierarchy
        for i, section in enumerate(sections):
            if section["level"] > 1:
                # Find parent section
                for j in range(i - 1, -1, -1):
                    if sections[j]["level"] < section["level"]:
                        sections[j]["subsections"].append(i)
                        break
        
        # Add section summaries for important sections
        for section in sections:
            if section["importance"] == "high":
                section["summary"] = self._generate_section_summary(section["content"])
        
        return sections
    
    def _generate_section_summary(self, content: str) -> str:
        """Generate a brief summary of section content."""
        # Take first 200 characters or first 2 sentences
        sentences = content.split('.')
        if len(sentences) >= 2:
            return '.'.join(sentences[:2]) + '.'
        else:
            return content[:200] + '...' if len(content) > 200 else content
    
    def find_section_by_keyword(
        self,
        sections: List[Dict[str, Any]],
        keyword: str
    ) -> List[Dict[str, Any]]:
        """Find sections containing specific keywords."""
        matching_sections = []
        keyword_lower = keyword.lower()
        
        for section in sections:
            if (keyword_lower in section["title"].lower() or 
                keyword_lower in section["content"].lower()):
                matching_sections.append(section)
        
        return matching_sections
    
    def get_section_hierarchy(
        self,
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build a hierarchical tree structure of sections."""
        hierarchy = {
            "title": "Document Structure",
            "children": []
        }
        
        # Build tree structure
        level_1_sections = [s for s in sections if s["level"] == 1]
        
        for section in level_1_sections:
            node = {
                "title": section["title"],
                "importance": section["importance"],
                "children": []
            }
            
            # Add subsections
            for subsection_idx in section["subsections"]:
                subsection = sections[subsection_idx]
                node["children"].append({
                    "title": subsection["title"],
                    "importance": subsection["importance"]
                })
            
            hierarchy["children"].append(node)
        
        return hierarchy