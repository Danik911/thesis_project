"""
ALCOA+ Data Integrity Assessment and Scoring System

This module provides comprehensive ALCOA+ data integrity assessment with
weighted scoring, evidence-based evaluation, and gap identification for
pharmaceutical data integrity compliance.

Key Features:
- 9 ALCOA+ attributes assessment (Attributable, Legible, Contemporaneous, 
  Original, Accurate, Complete, Consistent, Enduring, Available)
- 2x weight for Original and Accurate attributes
- Target >9/10 overall score validation
- Evidence-based assessment with traceability
- Gap identification and remediation planning
- NO FALLBACKS - explicit assessment failures with diagnostics
"""

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field
from src.cross_validation.quality_metrics import QualityMetrics
from src.cross_validation.structured_logger import StructuredLogger

from .evidence_collector import EvidenceCollector
from .models import (
    ComplianceFramework,
    ComplianceResult,
    ComplianceStatus,
    Evidence,
    EvidenceType,
    Gap,
    GapSeverity,
)


class ALCOAAttribute(str, Enum):
    """ALCOA+ data integrity attributes."""
    ATTRIBUTABLE = "attributable"
    LEGIBLE = "legible"
    CONTEMPORANEOUS = "contemporaneous"
    ORIGINAL = "original"  # 2x weight
    ACCURATE = "accurate"  # 2x weight
    COMPLETE = "complete"
    CONSISTENT = "consistent"
    ENDURING = "enduring"
    AVAILABLE = "available"


class ALCOAScoring(BaseModel):
    """Individual ALCOA+ attribute scoring results."""
    attribute: ALCOAAttribute = Field(description="ALCOA+ attribute being scored")
    score: float = Field(ge=0.0, le=1.0, description="Attribute score (0-1)")
    weight: float = Field(default=1.0, description="Attribute weight (2x for Original/Accurate)")
    weighted_score: float = Field(description="Score × weight")
    assessment_criteria: list[str] = Field(description="Criteria used for assessment")
    evidence_items: list[str] = Field(default_factory=list, description="Evidence supporting the score")
    gaps_identified: list[str] = Field(default_factory=list, description="Gaps found in this attribute")
    assessment_notes: str = Field(default="", description="Detailed assessment notes")


class ALCOAAssessment(BaseModel):
    """Comprehensive ALCOA+ assessment results."""
    assessment_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique assessment identifier")
    system_name: str = Field(description="System being assessed")
    assessment_timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    # Individual attribute scores
    attribute_scores: dict[str, ALCOAScoring] = Field(description="Scores for each ALCOA+ attribute")

    # Overall scoring
    total_possible_score: float = Field(description="Maximum possible weighted score")
    total_actual_score: float = Field(description="Actual weighted score achieved")
    overall_score: float = Field(ge=0.0, le=10.0, description="Overall ALCOA+ score (0-10)")

    # Target compliance
    target_score: float = Field(default=9.0, description="Target ALCOA+ score")
    meets_target: bool = Field(description="Whether overall score meets target")

    # Assessment details
    data_samples_assessed: int = Field(description="Number of data samples assessed")
    assessment_scope: str = Field(description="Scope of ALCOA+ assessment")

    # Compliance status
    compliance_status: ComplianceStatus = Field(description="Overall compliance status")

    # Evidence and gaps
    total_evidence_items: int = Field(description="Total evidence items collected")
    total_gaps_identified: int = Field(description="Total gaps identified")
    critical_gaps: int = Field(description="Number of critical gaps")


class ALCOAAssessmentError(Exception):
    """Exception raised when ALCOA+ assessment fails."""


class ALCOAScorer:
    """
    ALCOA+ data integrity scorer for pharmaceutical systems.
    
    This class provides comprehensive ALCOA+ assessment with weighted scoring,
    evidence collection, and gap identification for data integrity compliance.
    
    NO FALLBACKS: All assessment failures surface explicitly with complete
    diagnostic information for regulatory compliance.
    """

    def __init__(
        self,
        evidence_collector: EvidenceCollector,
        quality_metrics: QualityMetrics | None = None,
        structured_logger: StructuredLogger | None = None
    ):
        """
        Initialize the ALCOA+ scorer.
        
        Args:
            evidence_collector: Evidence collector for gathering compliance evidence
            quality_metrics: Optional quality metrics analyzer
            structured_logger: Optional structured logger for audit trail analysis
        """
        self.logger = logging.getLogger(__name__)
        self.evidence_collector = evidence_collector
        self.quality_metrics = quality_metrics
        self.structured_logger = structured_logger

        # ALCOA+ attribute weights (Original and Accurate get 2x weight)
        self.attribute_weights = {
            ALCOAAttribute.ATTRIBUTABLE: 1.0,
            ALCOAAttribute.LEGIBLE: 1.0,
            ALCOAAttribute.CONTEMPORANEOUS: 1.0,
            ALCOAAttribute.ORIGINAL: 2.0,  # 2x weight
            ALCOAAttribute.ACCURATE: 2.0,  # 2x weight
            ALCOAAttribute.COMPLETE: 1.0,
            ALCOAAttribute.CONSISTENT: 1.0,
            ALCOAAttribute.ENDURING: 1.0,
            ALCOAAttribute.AVAILABLE: 1.0
        }

        # Assessment criteria for each attribute
        self.assessment_criteria = self._define_assessment_criteria()

        # Current assessment state
        self.current_assessment: ALCOAAssessment | None = None
        self.identified_gaps: list[Gap] = []

        self.logger.info("ALCOAScorer initialized with 2x weighting for Original and Accurate")

    def assess_system_data_integrity(
        self,
        system_name: str,
        data_samples: list[dict[str, Any]],
        assessment_scope: str = "System-wide data integrity assessment",
        target_score: float = 9.0,
        assessor_name: str = "alcoa_scorer"
    ) -> ALCOAAssessment:
        """
        Assess system data integrity against ALCOA+ principles.
        
        Args:
            system_name: Name of system being assessed
            data_samples: Data samples for ALCOA+ assessment
            assessment_scope: Scope of the assessment
            target_score: Target ALCOA+ score (default 9.0/10)
            assessor_name: Name of assessor performing evaluation
            
        Returns:
            Comprehensive ALCOA+ assessment results
            
        Raises:
            ALCOAAssessmentError: If ALCOA+ assessment fails
        """
        try:
            if not data_samples:
                raise ALCOAAssessmentError("No data samples provided for ALCOA+ assessment")

            self.logger.info(f"Starting ALCOA+ assessment for {system_name} with {len(data_samples)} samples")

            # Initialize assessment
            assessment = ALCOAAssessment(
                system_name=system_name,
                assessment_scope=assessment_scope,
                target_score=target_score,
                data_samples_assessed=len(data_samples),
                attribute_scores={},
                total_possible_score=sum(self.attribute_weights.values()),
                total_actual_score=0.0,
                overall_score=0.0,
                meets_target=False,
                compliance_status=ComplianceStatus.NOT_ASSESSED,
                total_evidence_items=0,
                total_gaps_identified=0,
                critical_gaps=0
            )

            # Assess each ALCOA+ attribute
            for attribute in ALCOAAttribute:
                attribute_score = self._assess_attribute(
                    attribute, data_samples, system_name, assessor_name
                )
                assessment.attribute_scores[attribute.value] = attribute_score
                assessment.total_actual_score += attribute_score.weighted_score

            # Calculate overall score (0-10 scale)
            assessment.overall_score = (assessment.total_actual_score / assessment.total_possible_score) * 10.0
            assessment.meets_target = assessment.overall_score >= target_score

            # Determine compliance status
            assessment.compliance_status = self._determine_alcoa_compliance(
                assessment.overall_score, target_score
            )

            # Collect evidence summary
            total_evidence = sum(len(attr.evidence_items) for attr in assessment.attribute_scores.values())
            assessment.total_evidence_items = total_evidence

            # Count gaps
            total_gaps = sum(len(attr.gaps_identified) for attr in assessment.attribute_scores.values())
            assessment.total_gaps_identified = total_gaps
            assessment.critical_gaps = len([gap for gap in self.identified_gaps if gap.severity == GapSeverity.CRITICAL])

            # Store assessment
            self.current_assessment = assessment

            self.logger.info(f"ALCOA+ assessment completed: {assessment.overall_score:.2f}/10 (target: {target_score})")
            return assessment

        except Exception as e:
            error_msg = f"ALCOA+ assessment failed for {system_name}: {e!s}"
            self.logger.error(error_msg)
            raise ALCOAAssessmentError(error_msg) from e

    def _assess_attribute(
        self,
        attribute: ALCOAAttribute,
        data_samples: list[dict[str, Any]],
        system_name: str,
        assessor_name: str
    ) -> ALCOAScoring:
        """
        Assess a specific ALCOA+ attribute.
        
        Args:
            attribute: ALCOA+ attribute to assess
            data_samples: Data samples for assessment
            system_name: System name
            assessor_name: Assessor name
            
        Returns:
            Attribute scoring results
            
        Raises:
            ALCOAAssessmentError: If attribute assessment fails
        """
        try:
            self.logger.debug(f"Assessing {attribute.value} attribute")

            # Get assessment method for this attribute
            assessment_method = getattr(self, f"_assess_{attribute.value}")

            # Perform attribute-specific assessment
            score, evidence_items, gaps, notes = assessment_method(data_samples, system_name)

            # Create scoring result
            weight = self.attribute_weights[attribute]
            scoring = ALCOAScoring(
                attribute=attribute,
                score=score,
                weight=weight,
                weighted_score=score * weight,
                assessment_criteria=self.assessment_criteria[attribute.value],
                evidence_items=evidence_items,
                gaps_identified=gaps,
                assessment_notes=notes
            )

            # Create gaps if score is below threshold
            if score < 0.8:  # 80% threshold for individual attributes
                gap = self._create_attribute_gap(attribute, score, system_name)
                self.identified_gaps.append(gap)
                scoring.gaps_identified.append(gap.gap_id)

            # Collect evidence
            if evidence_items:
                evidence = self._collect_attribute_evidence(
                    system_name, attribute, scoring, assessor_name
                )
                scoring.evidence_items.append(evidence.evidence_id)

            return scoring

        except Exception as e:
            error_msg = f"Assessment failed for {attribute.value}: {e!s}"
            self.logger.error(error_msg)
            raise ALCOAAssessmentError(error_msg) from e

    def _assess_attributable(
        self, data_samples: list[dict[str, Any]], system_name: str
    ) -> tuple[float, list[str], list[str], str]:
        """Assess Attributable - unique user linkage and traceability."""
        total_score = 0.0
        evidence_items = []
        gaps = []
        assessment_details = []

        for sample in data_samples:
            score_components = []

            # Check for user identification
            if sample.get("user_id"):
                score_components.append(1.0)
                evidence_items.append(f"User ID present: {sample['user_id']}")
            else:
                score_components.append(0.0)
                gaps.append("Missing user identification")

            # Check for unique attribution
            if sample.get("created_by"):
                score_components.append(1.0)
                evidence_items.append(f"Creator attribution: {sample['created_by']}")
            else:
                score_components.append(0.0)
                gaps.append("Missing creator attribution")

            # Check for traceability links
            if sample.get("audit_trail"):
                score_components.append(1.0)
                evidence_items.append("Audit trail linkage present")
            else:
                score_components.append(0.0)
                gaps.append("Missing audit trail linkage")

            sample_score = sum(score_components) / len(score_components)
            total_score += sample_score
            assessment_details.append(f"Sample score: {sample_score:.2f}")

        average_score = total_score / len(data_samples)
        notes = f"Assessed {len(data_samples)} samples. " + "; ".join(assessment_details[:5])

        return average_score, evidence_items[:10], gaps[:10], notes

    def _assess_legible(
        self, data_samples: list[dict[str, Any]], system_name: str
    ) -> tuple[float, list[str], list[str], str]:
        """Assess Legible - readability and durable formats."""
        total_score = 0.0
        evidence_items = []
        gaps = []
        assessment_details = []

        for sample in data_samples:
            score_components = []

            # Check data format legibility
            if "format" in sample and sample["format"] in ["json", "xml", "csv", "structured"]:
                score_components.append(1.0)
                evidence_items.append(f"Structured format: {sample['format']}")
            else:
                score_components.append(0.0)
                gaps.append("Unstructured or unclear data format")

            # Check encoding and character sets
            if "encoding" in sample and sample["encoding"] in ["utf-8", "unicode"]:
                score_components.append(1.0)
                evidence_items.append(f"Standard encoding: {sample['encoding']}")
            else:
                score_components.append(0.5)  # Assume readable but not verified

            # Check for readability metadata
            if "schema" in sample or "metadata" in sample:
                score_components.append(1.0)
                evidence_items.append("Schema/metadata available for interpretation")
            else:
                score_components.append(0.0)
                gaps.append("Missing schema or metadata for interpretation")

            sample_score = sum(score_components) / len(score_components)
            total_score += sample_score
            assessment_details.append(f"Sample legibility: {sample_score:.2f}")

        average_score = total_score / len(data_samples)
        notes = f"Legibility assessment across {len(data_samples)} samples. " + "; ".join(assessment_details[:5])

        return average_score, evidence_items[:10], gaps[:10], notes

    def _assess_contemporaneous(
        self, data_samples: list[dict[str, Any]], system_name: str
    ) -> tuple[float, list[str], list[str], str]:
        """Assess Contemporaneous - timely entries and timestamps."""
        total_score = 0.0
        evidence_items = []
        gaps = []
        assessment_details = []

        for sample in data_samples:
            score_components = []

            # Check for creation timestamp
            if "created_at" in sample or "timestamp" in sample:
                score_components.append(1.0)
                timestamp = sample.get("created_at") or sample.get("timestamp")
                evidence_items.append(f"Creation timestamp present: {timestamp}")
            else:
                score_components.append(0.0)
                gaps.append("Missing creation timestamp")

            # Check timestamp format and precision
            timestamp_field = sample.get("created_at") or sample.get("timestamp")
            if timestamp_field and "T" in str(timestamp_field):  # ISO format check
                score_components.append(1.0)
                evidence_items.append("ISO format timestamp")
            else:
                score_components.append(0.5)

            # Check for modification tracking
            if "modified_at" in sample or "last_updated" in sample:
                score_components.append(1.0)
                evidence_items.append("Modification timestamp present")
            else:
                score_components.append(0.0)
                gaps.append("Missing modification timestamp")

            # Check for real-time capture indicators
            if "processing_time" in sample:
                processing_time = sample.get("processing_time", 0)
                if processing_time is not None and processing_time < 60:  # Less than 1 minute indicates near real-time
                    score_components.append(1.0)
                    evidence_items.append(f"Real-time capture: {processing_time}s")
                elif processing_time is not None:
                    score_components.append(0.7)
                else:
                    score_components.append(0.5)  # None value
            else:
                score_components.append(0.5)  # Unknown timing

            sample_score = sum(score_components) / len(score_components)
            total_score += sample_score
            assessment_details.append(f"Sample contemporaneous score: {sample_score:.2f}")

        average_score = total_score / len(data_samples)
        notes = f"Contemporaneous assessment of {len(data_samples)} samples. " + "; ".join(assessment_details[:5])

        return average_score, evidence_items[:10], gaps[:10], notes

    def _assess_original(
        self, data_samples: list[dict[str, Any]], system_name: str
    ) -> tuple[float, list[str], list[str], str]:
        """Assess Original - source records preserved; validated copies traceable (2x weight)."""
        total_score = 0.0
        evidence_items = []
        gaps = []
        assessment_details = []

        for sample in data_samples:
            score_components = []

            # Check for original record preservation
            if sample.get("is_original"):
                score_components.append(1.0)
                evidence_items.append("Original record flag present")
            else:
                score_components.append(0.0)
                gaps.append("Original record status unclear")

            # Check for version control
            if "version" in sample or "revision" in sample:
                score_components.append(1.0)
                version = sample.get("version") or sample.get("revision")
                evidence_items.append(f"Version control present: {version}")
            else:
                score_components.append(0.0)
                gaps.append("Missing version control")

            # Check for copy traceability
            if "source_document_id" in sample or "parent_record_id" in sample:
                score_components.append(1.0)
                evidence_items.append("Source traceability present")
            elif sample.get("is_original", False):
                score_components.append(1.0)  # Original doesn't need source link
            else:
                score_components.append(0.0)
                gaps.append("Copy traceability missing")

            # Check for digital signatures or checksums
            if "digital_signature" in sample or "checksum" in sample or "hash" in sample:
                score_components.append(1.0)
                evidence_items.append("Integrity verification present")
            else:
                score_components.append(0.0)
                gaps.append("Missing integrity verification")

            # Check for immutability indicators
            if "immutable" in sample or "locked" in sample:
                score_components.append(1.0)
                evidence_items.append("Immutability protection present")
            else:
                score_components.append(0.0)
                gaps.append("Immutability status unclear")

            sample_score = sum(score_components) / len(score_components)
            total_score += sample_score
            assessment_details.append(f"Sample original score: {sample_score:.2f}")

        average_score = total_score / len(data_samples)
        notes = f"Original (2x weight) assessment of {len(data_samples)} samples. " + "; ".join(assessment_details[:5])

        return average_score, evidence_items[:10], gaps[:10], notes

    def _assess_accurate(
        self, data_samples: list[dict[str, Any]], system_name: str
    ) -> tuple[float, list[str], list[str], str]:
        """Assess Accurate - correctness, controlled changes, reconciliations (2x weight)."""
        total_score = 0.0
        evidence_items = []
        gaps = []
        assessment_details = []

        for sample in data_samples:
            score_components = []

            # Check for validation indicators
            if sample.get("validated"):
                score_components.append(1.0)
                evidence_items.append("Validation status confirmed")
            else:
                score_components.append(0.0)
                gaps.append("Validation status unclear")

            # Check for accuracy verification
            if "accuracy_score" in sample or "confidence_score" in sample:
                accuracy = sample.get("accuracy_score") or sample.get("confidence_score", 0)
                if accuracy >= 0.9:
                    score_components.append(1.0)
                    evidence_items.append(f"High accuracy score: {accuracy}")
                elif accuracy >= 0.7:
                    score_components.append(0.7)
                    evidence_items.append(f"Moderate accuracy score: {accuracy}")
                else:
                    score_components.append(0.3)
                    gaps.append(f"Low accuracy score: {accuracy}")
            else:
                score_components.append(0.0)
                gaps.append("Missing accuracy metrics")

            # Check for change control
            if "change_reason" in sample or "modification_reason" in sample:
                score_components.append(1.0)
                evidence_items.append("Change control documentation present")
            else:
                score_components.append(0.0)
                gaps.append("Missing change control documentation")

            # Check for reconciliation records
            if "reconciled" in sample or "cross_verified" in sample:
                score_components.append(1.0)
                evidence_items.append("Reconciliation evidence present")
            else:
                score_components.append(0.0)
                gaps.append("Missing reconciliation evidence")

            # Check for error correction tracking
            if "corrections" in sample or "error_log" in sample:
                corrections = sample.get("corrections") or sample.get("error_log")
                if corrections:
                    score_components.append(0.8)  # Errors found but corrected
                    evidence_items.append("Error correction records present")
                else:
                    score_components.append(1.0)  # No errors found
            else:
                score_components.append(0.0)
                gaps.append("Error tracking status unknown")

            sample_score = sum(score_components) / len(score_components)
            total_score += sample_score
            assessment_details.append(f"Sample accuracy score: {sample_score:.2f}")

        average_score = total_score / len(data_samples)
        notes = f"Accurate (2x weight) assessment of {len(data_samples)} samples. " + "; ".join(assessment_details[:5])

        return average_score, evidence_items[:10], gaps[:10], notes

    def _assess_complete(
        self, data_samples: list[dict[str, Any]], system_name: str
    ) -> tuple[float, list[str], list[str], str]:
        """Assess Complete - inclusion of all data (including changes and metadata)."""
        total_score = 0.0
        evidence_items = []
        gaps = []
        assessment_details = []

        for sample in data_samples:
            score_components = []

            # Check for required field completeness
            required_fields = ["id", "timestamp", "data"]
            present_fields = [field for field in required_fields if field in sample and sample[field] is not None]
            field_completeness = len(present_fields) / len(required_fields)
            score_components.append(field_completeness)

            if field_completeness == 1.0:
                evidence_items.append("All required fields present")
            else:
                missing = [field for field in required_fields if field not in sample or sample[field] is None]
                gaps.append(f"Missing required fields: {missing}")

            # Check for metadata completeness
            metadata_fields = ["created_by", "system_version", "process_id"]
            present_metadata = [field for field in metadata_fields if field in sample and sample[field] is not None]
            metadata_completeness = len(present_metadata) / len(metadata_fields)
            score_components.append(metadata_completeness)

            if metadata_completeness >= 0.8:
                evidence_items.append(f"Comprehensive metadata: {len(present_metadata)}/{len(metadata_fields)}")
            else:
                gaps.append("Incomplete metadata")

            # Check for change history completeness
            if "change_history" in sample or "audit_trail" in sample:
                score_components.append(1.0)
                evidence_items.append("Change history present")
            else:
                score_components.append(0.0)
                gaps.append("Missing change history")

            # Check for related data completeness
            if "related_records" in sample or "dependencies" in sample:
                score_components.append(1.0)
                evidence_items.append("Related data linkage present")
            else:
                score_components.append(0.5)  # May not always be applicable

            sample_score = sum(score_components) / len(score_components)
            total_score += sample_score
            assessment_details.append(f"Sample completeness: {sample_score:.2f}")

        average_score = total_score / len(data_samples)
        notes = f"Completeness assessment of {len(data_samples)} samples. " + "; ".join(assessment_details[:5])

        return average_score, evidence_items[:10], gaps[:10], notes

    def _assess_consistent(
        self, data_samples: list[dict[str, Any]], system_name: str
    ) -> tuple[float, list[str], list[str], str]:
        """Assess Consistent - chronological order, formats, time sync."""
        total_score = 0.0
        evidence_items = []
        gaps = []
        assessment_details = []

        # Check chronological consistency across samples
        timestamps = []
        for sample in data_samples:
            timestamp = sample.get("timestamp") or sample.get("created_at")
            if timestamp:
                timestamps.append(timestamp)

        chronological_consistency = 1.0
        if len(timestamps) > 1:
            try:
                # Simple chronological check (assuming ISO format)
                sorted_timestamps = sorted(timestamps)
                if timestamps == sorted_timestamps:
                    evidence_items.append("Chronological order maintained")
                else:
                    chronological_consistency = 0.7
                    gaps.append("Chronological order inconsistencies found")
            except Exception:
                chronological_consistency = 0.5
                gaps.append("Timestamp format prevents chronological verification")

        # Check format consistency
        format_consistency = 1.0
        formats = set()
        for sample in data_samples:
            sample_format = sample.get("format") or type(sample).__name__
            formats.add(sample_format)

        if len(formats) == 1:
            evidence_items.append(f"Consistent format across samples: {list(formats)[0]}")
        else:
            format_consistency = 0.6
            gaps.append(f"Multiple formats found: {list(formats)}")

        # Check field naming consistency
        field_consistency = 1.0
        all_fields = set()
        common_fields = set()

        for i, sample in enumerate(data_samples):
            sample_fields = set(sample.keys())
            all_fields.update(sample_fields)
            if i == 0:
                common_fields = sample_fields
            else:
                common_fields = common_fields.intersection(sample_fields)

        if len(common_fields) / len(all_fields) >= 0.8:
            evidence_items.append(f"Good field consistency: {len(common_fields)} common fields")
        else:
            field_consistency = 0.7
            gaps.append("Inconsistent field structures across samples")

        # Calculate overall consistency
        consistency_components = [chronological_consistency, format_consistency, field_consistency]
        average_score = sum(consistency_components) / len(consistency_components)

        notes = f"Consistency assessment across {len(data_samples)} samples: chronological={chronological_consistency:.2f}, format={format_consistency:.2f}, fields={field_consistency:.2f}"

        return average_score, evidence_items[:10], gaps[:10], notes

    def _assess_enduring(
        self, data_samples: list[dict[str, Any]], system_name: str
    ) -> tuple[float, list[str], list[str], str]:
        """Assess Enduring - protected storage and retention."""
        total_score = 0.0
        evidence_items = []
        gaps = []
        assessment_details = []

        for sample in data_samples:
            score_components = []

            # Check for retention metadata
            if "retention_period" in sample or "expires_at" in sample:
                score_components.append(1.0)
                retention = sample.get("retention_period") or sample.get("expires_at")
                evidence_items.append(f"Retention policy defined: {retention}")
            else:
                score_components.append(0.0)
                gaps.append("Retention period not specified")

            # Check for storage protection indicators
            if "encrypted" in sample or "protected" in sample:
                score_components.append(1.0)
                evidence_items.append("Storage protection indicators present")
            else:
                score_components.append(0.0)
                gaps.append("Storage protection status unclear")

            # Check for backup indicators
            if "backed_up" in sample or "backup_status" in sample:
                score_components.append(1.0)
                evidence_items.append("Backup status documented")
            else:
                score_components.append(0.0)
                gaps.append("Backup status unknown")

            # Check for archive compatibility
            if "format" in sample and sample["format"] in ["json", "xml", "csv"]:
                score_components.append(1.0)
                evidence_items.append(f"Archive-compatible format: {sample['format']}")
            else:
                score_components.append(0.5)
                gaps.append("Archive compatibility unclear")

            sample_score = sum(score_components) / len(score_components)
            total_score += sample_score
            assessment_details.append(f"Sample enduring score: {sample_score:.2f}")

        average_score = total_score / len(data_samples)
        notes = f"Enduring assessment of {len(data_samples)} samples. " + "; ".join(assessment_details[:5])

        return average_score, evidence_items[:10], gaps[:10], notes

    def _assess_available(
        self, data_samples: list[dict[str, Any]], system_name: str
    ) -> tuple[float, list[str], list[str], str]:
        """Assess Available - retrieval on demand within SLA."""
        total_score = 0.0
        evidence_items = []
        gaps = []
        assessment_details = []

        for sample in data_samples:
            score_components = []

            # Check for accessibility indicators
            if sample.get("accessible"):
                score_components.append(1.0)
                evidence_items.append("Data marked as accessible")
            else:
                score_components.append(0.0)
                gaps.append("Accessibility status unclear")

            # Check for retrieval metadata
            if "retrieval_time" in sample:
                retrieval_time = sample.get("retrieval_time", float("inf"))
                if retrieval_time < 60:  # Under 1 minute
                    score_components.append(1.0)
                    evidence_items.append(f"Fast retrieval: {retrieval_time}s")
                elif retrieval_time < 300:  # Under 5 minutes
                    score_components.append(0.8)
                    evidence_items.append(f"Acceptable retrieval: {retrieval_time}s")
                else:
                    score_components.append(0.5)
                    gaps.append(f"Slow retrieval: {retrieval_time}s")
            else:
                score_components.append(0.0)
                gaps.append("Retrieval time not measured")

            # Check for search/query capabilities
            if "searchable" in sample or "indexed" in sample:
                score_components.append(1.0)
                evidence_items.append("Search capabilities present")
            else:
                score_components.append(0.0)
                gaps.append("Search capabilities unclear")

            # Check for format availability
            if "export_formats" in sample or "download_options" in sample:
                score_components.append(1.0)
                formats = sample.get("export_formats") or sample.get("download_options")
                evidence_items.append(f"Multiple export formats: {formats}")
            else:
                score_components.append(0.5)  # May still be available in original format

            sample_score = sum(score_components) / len(score_components)
            total_score += sample_score
            assessment_details.append(f"Sample availability: {sample_score:.2f}")

        average_score = total_score / len(data_samples)
        notes = f"Availability assessment of {len(data_samples)} samples. " + "; ".join(assessment_details[:5])

        return average_score, evidence_items[:10], gaps[:10], notes

    def _determine_alcoa_compliance(self, overall_score: float, target_score: float) -> ComplianceStatus:
        """Determine ALCOA+ compliance status."""
        if overall_score >= target_score:
            return ComplianceStatus.COMPLIANT
        if overall_score >= (target_score * 0.8):  # Within 20% of target
            return ComplianceStatus.PARTIALLY_COMPLIANT
        return ComplianceStatus.NON_COMPLIANT

    def _create_attribute_gap(self, attribute: ALCOAAttribute, score: float, system_name: str) -> Gap:
        """Create a gap for a low-scoring ALCOA+ attribute."""
        severity = GapSeverity.CRITICAL if score < 0.5 else GapSeverity.HIGH if score < 0.7 else GapSeverity.MEDIUM

        # Attribute-specific risk descriptions
        risk_descriptions = {
            ALCOAAttribute.ATTRIBUTABLE: ("High - untraceable data affects accountability",
                                        "High - data without attribution affects quality decisions"),
            ALCOAAttribute.ORIGINAL: ("Critical - modified source records affect safety decisions",
                                    "Critical - original record integrity fundamental to product quality"),
            ALCOAAttribute.ACCURATE: ("Critical - inaccurate data directly impacts patient safety",
                                    "Critical - data accuracy fundamental to product decisions"),
        }

        patient_risk, product_risk = risk_descriptions.get(attribute,
            ("Medium - data integrity issue may affect decisions", "Medium - data quality impacts product assurance"))

        return Gap(
            title=f"Low ALCOA+ Score: {attribute.value.title()}",
            description=f"ALCOA+ attribute '{attribute.value}' scored {score:.2f}, below acceptable threshold of 0.8",
            framework=ComplianceFramework.ALCOA_PLUS,
            requirement_reference=f"ALCOA+ Principle - {attribute.value.title()}",
            severity=severity,
            risk_to_patient=patient_risk,
            risk_to_product=product_risk,
            risk_to_data="High - data integrity principle compromised",
            compliance_exposure="High - regulatory expectation for ALCOA+ compliance",
            root_cause=f"Insufficient {attribute.value} controls or documentation",
            current_state_description=f"{attribute.value.title()} score: {score:.2f}",
            required_state_description=f"{attribute.value.title()} score ≥ 0.8",
            identified_by="alcoa_scorer",
            identification_method=f"alcoa_{attribute.value}_assessment"
        )

    def _collect_attribute_evidence(
        self, system_name: str, attribute: ALCOAAttribute, scoring: ALCOAScoring, assessor_name: str
    ) -> Evidence:
        """Collect evidence for ALCOA+ attribute assessment."""
        return self.evidence_collector.collect_evidence_from_system(
            system_name=system_name,
            evidence_type=EvidenceType.PROCESS_RECORD,
            collection_method=f"automated_alcoa_{attribute.value}_assessment",
            collector_name=assessor_name,
            assessment_data={
                "attribute": attribute.value,
                "score": scoring.score,
                "weighted_score": scoring.weighted_score,
                "assessment_criteria": scoring.assessment_criteria,
                "assessment_notes": scoring.assessment_notes
            },
            compliance_framework="ALCOA+"
        )

    def _define_assessment_criteria(self) -> dict[str, list[str]]:
        """Define assessment criteria for each ALCOA+ attribute."""
        return {
            "attributable": [
                "Unique user identification present",
                "Creator attribution documented",
                "Audit trail linkage established",
                "User traceability maintained"
            ],
            "legible": [
                "Structured, readable data format",
                "Standard encoding used",
                "Schema/metadata available",
                "Interpretation guidelines present"
            ],
            "contemporaneous": [
                "Creation timestamp present",
                "Modification timestamps tracked",
                "Real-time or near real-time capture",
                "Temporal sequence maintained"
            ],
            "original": [
                "Original record status identified",
                "Version control implemented",
                "Copy traceability maintained",
                "Integrity verification present",
                "Immutability protection applied"
            ],
            "accurate": [
                "Validation status confirmed",
                "Accuracy metrics available",
                "Change control documented",
                "Reconciliation performed",
                "Error correction tracked"
            ],
            "complete": [
                "Required fields present",
                "Comprehensive metadata included",
                "Change history maintained",
                "Related data linked"
            ],
            "consistent": [
                "Chronological order maintained",
                "Format consistency across records",
                "Field structure consistency",
                "Time synchronization verified"
            ],
            "enduring": [
                "Retention period defined",
                "Storage protection implemented",
                "Backup procedures established",
                "Archive-compatible format used"
            ],
            "available": [
                "Data accessibility confirmed",
                "Retrieval time within SLA",
                "Search capabilities provided",
                "Multiple export formats supported"
            ]
        }

    def generate_alcoa_compliance_report(
        self,
        system_name: str,
        assessor_name: str = "alcoa_scorer"
    ) -> ComplianceResult:
        """
        Generate comprehensive ALCOA+ compliance report.
        
        Args:
            system_name: Name of system being assessed
            assessor_name: Name of assessor generating report
            
        Returns:
            Comprehensive ALCOA+ compliance result
            
        Raises:
            ALCOAAssessmentError: If report generation fails
        """
        try:
            if not self.current_assessment:
                raise ALCOAAssessmentError("No ALCOA+ assessment performed. Run assessment before generating report.")

            assessment = self.current_assessment

            # Create compliance result
            compliance_result = ComplianceResult(
                assessment_name=f"ALCOA+ Data Integrity Assessment - {system_name}",
                system_under_assessment=system_name,
                frameworks_assessed=[ComplianceFramework.ALCOA_PLUS],
                assessment_scope=assessment.assessment_scope,
                overall_status=assessment.compliance_status,
                overall_score=assessment.overall_score,
                total_gaps_identified=assessment.total_gaps_identified,
                critical_gaps=assessment.critical_gaps,
                high_priority_gaps=len([g for g in self.identified_gaps if g.severity == GapSeverity.HIGH]),
                assessment_team=[assessor_name],
                assessment_start_date=assessment.assessment_timestamp,
                gap_ids=[gap.gap_id for gap in self.identified_gaps]
            )

            # Add framework-specific results
            alcoa_results = {
                "overall_score": assessment.overall_score,
                "target_score": assessment.target_score,
                "meets_target": assessment.meets_target,
                "data_samples_assessed": assessment.data_samples_assessed,
                "attribute_scores": {
                    attr_name: {
                        "score": attr_score.score,
                        "weighted_score": attr_score.weighted_score,
                        "weight": attr_score.weight,
                        "evidence_count": len(attr_score.evidence_items),
                        "gaps_count": len(attr_score.gaps_identified)
                    }
                    for attr_name, attr_score in assessment.attribute_scores.items()
                },
                "weighted_breakdown": {
                    "original_contribution": assessment.attribute_scores.get("original", ALCOAScoring(attribute=ALCOAAttribute.ORIGINAL, score=0.0)).weighted_score,
                    "accurate_contribution": assessment.attribute_scores.get("accurate", ALCOAScoring(attribute=ALCOAAttribute.ACCURATE, score=0.0)).weighted_score,
                    "other_attributes_total": sum(
                        score.weighted_score for name, score in assessment.attribute_scores.items()
                        if name not in ["original", "accurate"]
                    )
                }
            }

            compliance_result.framework_results = {"alcoa_plus": alcoa_results}

            # Add framework result
            compliance_result.add_framework_result(ComplianceFramework.ALCOA_PLUS, {
                "status": assessment.compliance_status,
                "score": assessment.overall_score,
                "target_achieved": assessment.meets_target
            })

            self.logger.info(f"ALCOA+ compliance report generated: {assessment.overall_score:.2f}/10")
            return compliance_result

        except Exception as e:
            error_msg = f"ALCOA+ compliance report generation failed: {e!s}"
            self.logger.error(error_msg)
            raise ALCOAAssessmentError(error_msg) from e

    def get_assessment_summary(self) -> dict[str, Any]:
        """Get summary of current ALCOA+ assessment."""
        if not self.current_assessment:
            return {"status": "no_assessment_performed"}

        assessment = self.current_assessment

        return {
            "system_name": assessment.system_name,
            "overall_score": assessment.overall_score,
            "target_score": assessment.target_score,
            "meets_target": assessment.meets_target,
            "compliance_status": assessment.compliance_status.value,
            "data_samples_assessed": assessment.data_samples_assessed,
            "total_evidence_items": assessment.total_evidence_items,
            "total_gaps_identified": assessment.total_gaps_identified,
            "critical_gaps": assessment.critical_gaps,
            "attribute_summary": {
                attr_name: {
                    "score": attr_score.score,
                    "weighted_contribution": attr_score.weighted_score,
                    "weight": attr_score.weight
                }
                for attr_name, attr_score in assessment.attribute_scores.items()
            },
            "top_performing_attributes": sorted(
                [(name, score.score) for name, score in assessment.attribute_scores.items()],
                key=lambda x: x[1], reverse=True
            )[:3],
            "lowest_performing_attributes": sorted(
                [(name, score.score) for name, score in assessment.attribute_scores.items()],
                key=lambda x: x[1]
            )[:3]
        }
