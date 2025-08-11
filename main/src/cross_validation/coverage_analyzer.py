"""
Requirements Coverage Analysis for Cross-Validation Framework

This module provides comprehensive coverage analysis by parsing URS documents
to extract testable requirements and mapping generated tests to those requirements
with full GAMP-5 compliance and audit trail support.

Key Features:
- URS document parsing and requirement extraction
- Test-to-requirement mapping with traceability
- Coverage calculation and reporting
- Requirement traceability matrix generation
- GAMP-5 compliance validation
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """Model for a single testable requirement from URS."""
    id: str = Field(description="Unique requirement identifier")
    text: str = Field(description="Full requirement text")
    category: str = Field(description="Requirement category (functional, performance, etc.)")
    priority: str = Field(default="medium", description="Requirement priority level")
    testable: bool = Field(default=True, description="Whether requirement is testable")
    source_section: str = Field(description="Source section in URS document")
    line_number: int | None = Field(default=None, description="Line number in source document")
    gamp_relevance: str | None = Field(default=None, description="GAMP-5 relevance category")


class TestRequirementMapping(BaseModel):
    """Model for mapping tests to requirements."""
    test_id: str = Field(description="Generated test identifier")
    test_name: str = Field(description="Generated test name")
    mapped_requirements: list[str] = Field(description="List of requirement IDs covered by this test")
    coverage_confidence: float = Field(description="Confidence in the mapping (0-1)")
    mapping_method: str = Field(description="Method used for mapping (keyword, semantic, manual)")
    notes: str | None = Field(default=None, description="Additional mapping notes")


class CoverageReport(BaseModel):
    """Comprehensive coverage analysis report."""
    document_id: str = Field(description="URS document identifier")
    total_requirements: int = Field(description="Total testable requirements found")
    covered_requirements: int = Field(description="Requirements with at least one test")
    coverage_percentage: float = Field(description="Coverage percentage (0-100)")
    uncovered_requirements: list[str] = Field(description="IDs of uncovered requirements")
    over_tested_requirements: list[str] = Field(description="Requirements with multiple tests")
    test_to_requirement_mappings: list[TestRequirementMapping] = Field(description="All test mappings")
    coverage_by_category: dict[str, float] = Field(description="Coverage breakdown by category")
    meets_90_percent_target: bool = Field(description="Whether 90% coverage target is met")
    analysis_timestamp: str = Field(description="When analysis was performed")


class CoverageAnalyzer:
    """
    Requirements coverage analyzer for cross-validation experiments.

    This class provides comprehensive analysis of test coverage against
    URS requirements with full traceability and GAMP-5 compliance.
    """

    # Regular expressions for requirement extraction
    REQUIREMENT_PATTERNS = [
        r"(?i)\b(?:the system|software|application) (?:shall|must|will|should) ([^.]+\.)",
        r"(?i)\breq(?:uirement)?\s*[:\-#]?\s*([^.\n]+\.)",
        r"(?i)\b(?:FR|NFR|UR)\s*[:\-]?\s*\d+[:\-]?\s*([^.\n]+\.)",
        r"(?i)^\s*\d+\.\d+[:\-]?\s*([^.\n]+\.)",
        r"(?i)\b(?:criteria|requirement|specification)[:\-]?\s*([^.\n]+\.)"
    ]

    # Keywords for requirement categorization
    CATEGORY_KEYWORDS = {
        "functional": ["function", "feature", "capability", "operation", "process", "workflow"],
        "performance": ["performance", "speed", "time", "response", "throughput", "latency"],
        "security": ["security", "authentication", "authorization", "access", "permission", "encrypt"],
        "usability": ["user", "interface", "usability", "accessibility", "experience", "navigation"],
        "reliability": ["reliability", "availability", "uptime", "fault", "error", "exception"],
        "compliance": ["compliance", "regulation", "standard", "gamp", "fda", "validation"],
        "data": ["data", "database", "storage", "backup", "record", "information"],
        "integration": ["integration", "interface", "api", "connection", "communication"]
    }

    def __init__(self, output_directory: str | Path | None = None):
        """
        Initialize the CoverageAnalyzer.

        Args:
            output_directory: Directory to store coverage reports
        """
        self.logger = logging.getLogger(__name__)
        self.output_directory = Path(output_directory) if output_directory else Path.cwd() / "coverage_reports"
        self.output_directory.mkdir(parents=True, exist_ok=True)

        # Cache for parsed requirements
        self._requirement_cache: dict[str, list[Requirement]] = {}

        self.logger.info(f"CoverageAnalyzer initialized with output directory: {self.output_directory}")

    def extract_requirements_from_urs(self, urs_document_path: Path, document_id: str) -> list[Requirement]:
        """
        Extract testable requirements from a URS document.

        Args:
            urs_document_path: Path to the URS document
            document_id: Unique identifier for the document

        Returns:
            List of extracted requirements

        Raises:
            FileNotFoundError: If URS document is not found
            ValueError: If document cannot be parsed
        """
        if document_id in self._requirement_cache:
            self.logger.debug(f"Using cached requirements for {document_id}")
            return self._requirement_cache[document_id]

        if not urs_document_path.exists():
            msg = f"URS document not found: {urs_document_path}"
            raise FileNotFoundError(msg)

        try:
            # Read document content
            with open(urs_document_path, encoding="utf-8") as f:
                content = f.read()

            requirements = self._parse_requirements_from_text(content, document_id)

            # Cache the results
            self._requirement_cache[document_id] = requirements

            self.logger.info(f"Extracted {len(requirements)} requirements from {document_id}")
            return requirements

        except Exception as e:
            error_msg = f"Failed to extract requirements from {urs_document_path}: {e!s}"
            self.logger.exception(error_msg)
            raise ValueError(error_msg) from e

    def _parse_requirements_from_text(self, content: str, document_id: str) -> list[Requirement]:
        """
        Parse requirements from document text using pattern matching.

        Args:
            content: Document text content
            document_id: Document identifier

        Returns:
            List of extracted requirements
        """
        requirements = []
        lines = content.split("\n")
        requirement_counter = 1

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or len(line) < 20:  # Skip short lines
                continue

            # Try each pattern to extract requirements
            for pattern in self.REQUIREMENT_PATTERNS:
                matches = re.findall(pattern, line)
                for match in matches:
                    if len(match.strip()) < 10:  # Skip very short matches
                        continue

                    requirement_text = match.strip()
                    if requirement_text.endswith("."):
                        requirement_text = requirement_text[:-1]  # Remove trailing period for consistency

                    # Determine category based on keywords
                    category = self._categorize_requirement(requirement_text)

                    # Determine section (basic heuristic)
                    section = self._determine_section(line, line_num, lines)

                    requirement = Requirement(
                        id=f"{document_id}_REQ_{requirement_counter:03d}",
                        text=requirement_text,
                        category=category,
                        priority=self._determine_priority(requirement_text),
                        testable=self._is_testable(requirement_text),
                        source_section=section,
                        line_number=line_num,
                        gamp_relevance=self._determine_gamp_relevance(requirement_text)
                    )

                    requirements.append(requirement)
                    requirement_counter += 1
                    break  # Only take first match per line

        # Remove duplicates based on similar text
        return self._deduplicate_requirements(requirements)


    def _categorize_requirement(self, requirement_text: str) -> str:
        """
        Categorize requirement based on keyword analysis.

        Args:
            requirement_text: Requirement text to categorize

        Returns:
            Category string
        """
        text_lower = requirement_text.lower()

        # Count keyword matches for each category
        category_scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score

        # Return category with highest score, or 'functional' as default
        if category_scores:
            return max(category_scores, key=category_scores.get)
        return "functional"

    def _determine_priority(self, requirement_text: str) -> str:
        """
        Determine requirement priority based on text analysis.

        Args:
            requirement_text: Requirement text

        Returns:
            Priority level (high, medium, low)
        """
        text_lower = requirement_text.lower()

        high_priority_keywords = ["critical", "essential", "must", "mandatory", "required", "shall"]
        low_priority_keywords = ["should", "may", "optional", "nice to have", "desirable"]

        if any(keyword in text_lower for keyword in high_priority_keywords):
            return "high"
        if any(keyword in text_lower for keyword in low_priority_keywords):
            return "low"
        return "medium"

    def _is_testable(self, requirement_text: str) -> bool:
        """
        Determine if a requirement is testable.

        Args:
            requirement_text: Requirement text

        Returns:
            True if testable, False otherwise
        """
        text_lower = requirement_text.lower()

        # Non-testable indicators
        non_testable_keywords = [
            "documentation", "training", "support", "maintenance",
            "general", "overview", "introduction", "background"
        ]

        # Testable indicators
        testable_keywords = [
            "validate", "verify", "test", "check", "ensure", "perform",
            "execute", "calculate", "display", "process", "generate"
        ]

        if any(keyword in text_lower for keyword in non_testable_keywords):
            return False

        if any(keyword in text_lower for keyword in testable_keywords):
            return True

        # Default to testable if functional requirement
        return True

    def _determine_section(self, line: str, line_num: int, all_lines: list[str]) -> str:
        """
        Determine the section of the document where requirement was found.

        Args:
            line: Current line
            line_num: Line number
            all_lines: All document lines

        Returns:
            Section identifier
        """
        # Look backwards to find most recent section header
        for i in range(line_num - 1, max(0, line_num - 20), -1):
            line_check = all_lines[i].strip()
            if (line_check.isupper() or
                re.match(r"^\d+\.", line_check) or
                re.match(r"^[A-Z][^.]*:$", line_check)):
                return line_check[:50]  # Truncate long headers

        return "Unknown Section"

    def _determine_gamp_relevance(self, requirement_text: str) -> str:
        """
        Determine GAMP-5 relevance of requirement.

        Args:
            requirement_text: Requirement text

        Returns:
            GAMP relevance category
        """
        text_lower = requirement_text.lower()

        if any(keyword in text_lower for keyword in ["validation", "compliance", "gmp", "fda"]):
            return "validation_critical"
        if any(keyword in text_lower for keyword in ["audit", "trace", "record", "log"]):
            return "audit_trail"
        if any(keyword in text_lower for keyword in ["access", "security", "permission"]):
            return "security_critical"
        return "standard"

    def _deduplicate_requirements(self, requirements: list[Requirement]) -> list[Requirement]:
        """
        Remove duplicate requirements based on text similarity.

        Args:
            requirements: List of requirements

        Returns:
            Deduplicated list
        """
        unique_requirements = []
        seen_texts = set()

        for req in requirements:
            # Create a normalized version for comparison
            normalized_text = re.sub(r"[^\w\s]", "", req.text.lower())

            # Check if similar text already seen
            is_duplicate = False
            for seen_text in seen_texts:
                # Simple similarity check - could be enhanced with fuzzy matching
                if self._text_similarity_ratio(normalized_text, seen_text) > 0.8:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_requirements.append(req)
                seen_texts.add(normalized_text)

        return unique_requirements

    def _text_similarity_ratio(self, text1: str, text2: str) -> float:
        """
        Calculate similarity ratio between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity ratio (0-1)
        """
        # Simple Jaccard similarity for word sets
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 and not words2:
            return 1.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def map_tests_to_requirements(
        self,
        generated_tests: list[dict[str, Any]],
        requirements: list[Requirement],
        document_id: str
    ) -> list[TestRequirementMapping]:
        """
        Map generated tests to requirements using keyword and semantic analysis.

        Args:
            generated_tests: List of generated test cases
            requirements: List of extracted requirements
            document_id: Document identifier

        Returns:
            List of test-to-requirement mappings
        """
        mappings = []

        for i, test in enumerate(generated_tests):
            test_id = test.get("id", f"{document_id}_TEST_{i+1:03d}")
            test_name = test.get("name", test.get("title", f"Test {i+1}"))
            test_description = test.get("description", test.get("steps", ""))

            # Combine test text for analysis
            test_text = f"{test_name} {test_description}".lower()

            # Find matching requirements
            mapped_req_ids = []
            confidence_scores = []

            for req in requirements:
                if not req.testable:
                    continue

                # Calculate matching score
                score = self._calculate_test_requirement_match(test_text, req.text.lower())

                if score > 0.3:  # Threshold for mapping
                    mapped_req_ids.append(req.id)
                    confidence_scores.append(score)

            # Calculate overall confidence
            overall_confidence = max(confidence_scores) if confidence_scores else 0.0

            mapping = TestRequirementMapping(
                test_id=test_id,
                test_name=test_name,
                mapped_requirements=mapped_req_ids,
                coverage_confidence=overall_confidence,
                mapping_method="keyword_semantic",
                notes=f"Mapped to {len(mapped_req_ids)} requirements with max confidence {overall_confidence:.2f}"
            )

            mappings.append(mapping)

        self.logger.info(f"Created {len(mappings)} test-to-requirement mappings for {document_id}")
        return mappings

    def _calculate_test_requirement_match(self, test_text: str, requirement_text: str) -> float:
        """
        Calculate match score between test and requirement texts.

        Args:
            test_text: Test description text (lowercase)
            requirement_text: Requirement text (lowercase)

        Returns:
            Match score (0-1)
        """
        # Extract key terms from both texts
        test_words = set(re.findall(r"\b\w{4,}\b", test_text))  # Words 4+ chars
        req_words = set(re.findall(r"\b\w{4,}\b", requirement_text))

        # Remove common stop words
        stop_words = {"shall", "must", "will", "should", "system", "software", "application", "user", "data"}
        test_words = test_words - stop_words
        req_words = req_words - stop_words

        if not test_words or not req_words:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(test_words & req_words)
        union = len(test_words | req_words)

        base_score = intersection / union if union > 0 else 0.0

        # Boost score for direct phrase matches
        test_phrases = [phrase.strip() for phrase in test_text.split() if len(phrase.strip()) > 3]
        phrase_matches = sum(1 for phrase in test_phrases if phrase in requirement_text)
        phrase_boost = min(0.3, phrase_matches * 0.1)

        return min(1.0, base_score + phrase_boost)

    def calculate_coverage(
        self,
        requirements: list[Requirement],
        mappings: list[TestRequirementMapping],
        document_id: str
    ) -> CoverageReport:
        """
        Calculate comprehensive coverage metrics.

        Args:
            requirements: List of extracted requirements
            mappings: List of test-to-requirement mappings
            document_id: Document identifier

        Returns:
            Comprehensive coverage report
        """
        # Filter testable requirements only
        testable_requirements = [req for req in requirements if req.testable]
        total_requirements = len(testable_requirements)

        if total_requirements == 0:
            msg = f"No testable requirements found for {document_id}"
            raise ValueError(msg)

        # Get all covered requirement IDs
        covered_req_ids = set()
        req_test_count = {}  # Track how many tests cover each requirement

        for mapping in mappings:
            for req_id in mapping.mapped_requirements:
                covered_req_ids.add(req_id)
                req_test_count[req_id] = req_test_count.get(req_id, 0) + 1

        # Calculate coverage
        testable_req_ids = {req.id for req in testable_requirements}
        actually_covered = covered_req_ids & testable_req_ids  # Only count testable requirements

        covered_requirements = len(actually_covered)
        coverage_percentage = (covered_requirements / total_requirements) * 100

        # Find uncovered requirements
        uncovered_req_ids = [req.id for req in testable_requirements if req.id not in covered_req_ids]

        # Find over-tested requirements (more than 2 tests)
        over_tested_req_ids = [req_id for req_id, count in req_test_count.items()
                              if count > 2 and req_id in testable_req_ids]

        # Coverage by category
        coverage_by_category = {}
        categories = {req.category for req in testable_requirements}

        for category in categories:
            category_reqs = [req for req in testable_requirements if req.category == category]
            category_covered = len([req for req in category_reqs if req.id in covered_req_ids])
            category_total = len(category_reqs)

            coverage_by_category[category] = (category_covered / category_total * 100) if category_total > 0 else 0.0

        report = CoverageReport(
            document_id=document_id,
            total_requirements=total_requirements,
            covered_requirements=covered_requirements,
            coverage_percentage=coverage_percentage,
            uncovered_requirements=uncovered_req_ids,
            over_tested_requirements=over_tested_req_ids,
            test_to_requirement_mappings=mappings,
            coverage_by_category=coverage_by_category,
            meets_90_percent_target=coverage_percentage >= 90.0,
            analysis_timestamp=pd.Timestamp.now().isoformat()
        )

        self.logger.info(f"Coverage analysis for {document_id}: {coverage_percentage:.1f}% "
                        f"({covered_requirements}/{total_requirements} requirements)")

        return report

    def generate_traceability_matrix(self, report: CoverageReport, requirements: list[Requirement]) -> pd.DataFrame:
        """
        Generate a requirements traceability matrix.

        Args:
            report: Coverage report
            requirements: List of requirements

        Returns:
            DataFrame with traceability matrix
        """
        # Create requirement lookup
        {req.id: req for req in requirements}

        # Build matrix data
        matrix_data = []

        for req in requirements:
            if not req.testable:
                continue

            # Find all tests that cover this requirement
            covering_tests = []
            test_confidences = []

            for mapping in report.test_to_requirement_mappings:
                if req.id in mapping.mapped_requirements:
                    covering_tests.append(mapping.test_name)
                    test_confidences.append(mapping.coverage_confidence)

            matrix_data.append({
                "Requirement_ID": req.id,
                "Requirement_Text": req.text,
                "Category": req.category,
                "Priority": req.priority,
                "Source_Section": req.source_section,
                "GAMP_Relevance": req.gamp_relevance,
                "Covered": len(covering_tests) > 0,
                "Test_Count": len(covering_tests),
                "Covering_Tests": "; ".join(covering_tests),
                "Max_Confidence": max(test_confidences) if test_confidences else 0.0,
                "Avg_Confidence": sum(test_confidences) / len(test_confidences) if test_confidences else 0.0
            })

        df = pd.DataFrame(matrix_data)

        # Save to file
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"traceability_matrix_{report.document_id}_{timestamp}.csv"
        output_path = self.output_directory / filename

        df.to_csv(output_path, index=False)

        self.logger.info(f"Traceability matrix saved to: {output_path}")
        return df

    def save_coverage_report(self, report: CoverageReport) -> Path:
        """
        Save coverage report to JSON file.

        Args:
            report: Coverage report to save

        Returns:
            Path to saved report
        """
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"coverage_report_{report.document_id}_{timestamp}.json"
        output_path = self.output_directory / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2, default=str)

        self.logger.info(f"Coverage report saved to: {output_path}")
        return output_path
