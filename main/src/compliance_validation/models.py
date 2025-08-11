"""
Compliance Validation Data Models

This module defines the core data structures for compliance validation
including evidence tracking, gap analysis, and remediation planning.

Key Features:
- Evidence collection and traceability
- Standardized validation templates
- Gap identification and classification
- CAPA-based remediation planning
- Full audit trail support
- NO FALLBACKS - explicit validation and error handling
"""

import json
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class ComplianceFramework(str, Enum):
    """Compliance frameworks supported by the validation system."""
    GAMP5 = "GAMP-5"
    CFR_PART_11 = "21 CFR Part 11"
    ALCOA_PLUS = "ALCOA+"
    ISO_13485 = "ISO 13485"
    ICH_Q9 = "ICH Q9"


class ComplianceStatus(str, Enum):
    """Compliance assessment status values."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_ASSESSED = "not_assessed"
    ASSESSMENT_FAILED = "assessment_failed"


class EvidenceType(str, Enum):
    """Types of compliance evidence."""
    DOCUMENT = "document"
    TEST_RESULT = "test_result"
    AUDIT_LOG = "audit_log"
    CONFIGURATION = "configuration"
    PROCESS_RECORD = "process_record"
    TRAINING_RECORD = "training_record"
    APPROVAL_RECORD = "approval_record"
    TECHNICAL_SPECIFICATION = "technical_specification"


class GapSeverity(str, Enum):
    """Gap severity levels for prioritization."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class RemediationStatus(str, Enum):
    """Remediation plan status tracking."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    VERIFICATION = "verification"
    COMPLETED = "completed"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"


class Evidence(BaseModel):
    """
    Evidence record for compliance validation.
    
    Tracks all evidence collected during compliance assessment
    with full traceability and audit trail support.
    """
    evidence_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique evidence identifier")
    evidence_type: EvidenceType = Field(description="Type of evidence")
    title: str = Field(description="Evidence title/name")
    description: str = Field(description="Detailed evidence description")

    # Source information
    source_system: str | None = Field(default=None, description="System that generated the evidence")
    source_document: str | None = Field(default=None, description="Source document path/reference")
    source_section: str | None = Field(default=None, description="Specific section or location")

    # Collection metadata
    collected_by: str = Field(description="Person/system that collected the evidence")
    collection_timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    collection_method: str = Field(description="How the evidence was collected")

    # Content
    evidence_content: dict[str, Any] = Field(default_factory=dict, description="Structured evidence content")
    file_attachments: list[str] = Field(default_factory=list, description="Attached files/documents")

    # Validation
    is_verified: bool = Field(default=False, description="Whether evidence has been verified")
    verified_by: str | None = Field(default=None, description="Who verified the evidence")
    verification_timestamp: str | None = Field(default=None, description="When verification occurred")
    verification_notes: str | None = Field(default=None, description="Verification notes")

    # Traceability
    requirement_ids: list[str] = Field(default_factory=list, description="Requirements this evidence supports")
    test_case_ids: list[str] = Field(default_factory=list, description="Test cases this evidence relates to")

    # Quality attributes
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Evidence completeness (0-1)")
    reliability_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Evidence reliability (0-1)")

    @validator("collection_timestamp", "verification_timestamp", pre=True)
    def validate_timestamps(cls, v):
        """Validate timestamp format."""
        if v is None:
            return v
        if isinstance(v, str):
            try:
                datetime.fromisoformat(v.replace("Z", "+00:00"))
                return v
            except ValueError:
                raise ValueError(f"Invalid timestamp format: {v}")
        return v


class ValidationTemplate(BaseModel):
    """
    Template for standardized validation activities.
    
    Defines the structure and requirements for different types of
    compliance validation activities.
    """
    template_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique template identifier")
    template_name: str = Field(description="Template name")
    framework: ComplianceFramework = Field(description="Compliance framework this template supports")
    template_version: str = Field(default="1.0", description="Template version")

    # Template definition
    description: str = Field(description="Template purpose and scope")
    required_evidence_types: list[EvidenceType] = Field(description="Required evidence types")
    validation_steps: list[dict[str, Any]] = Field(description="Step-by-step validation instructions")
    acceptance_criteria: list[str] = Field(description="Criteria for passing validation")

    # Quality requirements
    minimum_evidence_count: int = Field(default=1, description="Minimum number of evidence items required")
    required_completeness_threshold: float = Field(default=0.9, ge=0.0, le=1.0, description="Minimum completeness score")
    required_reliability_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="Minimum reliability score")

    # Template metadata
    created_by: str = Field(description="Template creator")
    creation_timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    approved_by: str | None = Field(default=None, description="Template approver")
    approval_timestamp: str | None = Field(default=None, description="Approval timestamp")

    # Usage tracking
    usage_count: int = Field(default=0, description="How many times this template has been used")
    last_used_timestamp: str | None = Field(default=None, description="When template was last used")


class TraceabilityMatrix(BaseModel):
    """
    Traceability matrix linking requirements, tests, and evidence.
    
    Provides full traceability from requirements through testing to 
    compliance evidence for regulatory audit support.
    """
    matrix_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique matrix identifier")
    matrix_name: str = Field(description="Matrix name/identifier")
    project_id: str = Field(description="Project or system identifier")

    # Matrix content
    requirements: dict[str, dict[str, Any]] = Field(default_factory=dict, description="Requirements catalog")
    test_cases: dict[str, dict[str, Any]] = Field(default_factory=dict, description="Test cases catalog")
    evidence_items: dict[str, dict[str, Any]] = Field(default_factory=dict, description="Evidence catalog")

    # Mappings
    requirement_test_mapping: dict[str, list[str]] = Field(default_factory=dict, description="Requirements to test cases")
    test_evidence_mapping: dict[str, list[str]] = Field(default_factory=dict, description="Test cases to evidence")

    # Coverage analysis
    requirements_coverage: dict[str, float] = Field(default_factory=dict, description="Coverage percentage per requirement")
    overall_coverage_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Overall coverage percentage")

    # Matrix metadata
    created_timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_updated_timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    created_by: str = Field(description="Matrix creator")

    def add_requirement(self, req_id: str, requirement_data: dict[str, Any]) -> None:
        """Add a requirement to the matrix."""
        self.requirements[req_id] = requirement_data
        self.requirement_test_mapping[req_id] = []
        self.requirements_coverage[req_id] = 0.0
        self.last_updated_timestamp = datetime.now(UTC).isoformat()

    def add_test_case(self, test_id: str, test_data: dict[str, Any]) -> None:
        """Add a test case to the matrix."""
        self.test_cases[test_id] = test_data
        self.test_evidence_mapping[test_id] = []
        self.last_updated_timestamp = datetime.now(UTC).isoformat()

    def add_evidence(self, evidence_id: str, evidence_data: dict[str, Any]) -> None:
        """Add evidence to the matrix."""
        self.evidence_items[evidence_id] = evidence_data
        self.last_updated_timestamp = datetime.now(UTC).isoformat()

    def link_requirement_to_test(self, req_id: str, test_id: str) -> None:
        """Link a requirement to a test case."""
        if req_id not in self.requirements:
            raise ValueError(f"Requirement {req_id} not found in matrix")
        if test_id not in self.test_cases:
            raise ValueError(f"Test case {test_id} not found in matrix")

        if test_id not in self.requirement_test_mapping[req_id]:
            self.requirement_test_mapping[req_id].append(test_id)
            self.last_updated_timestamp = datetime.now(UTC).isoformat()

    def link_test_to_evidence(self, test_id: str, evidence_id: str) -> None:
        """Link a test case to evidence."""
        if test_id not in self.test_cases:
            raise ValueError(f"Test case {test_id} not found in matrix")
        if evidence_id not in self.evidence_items:
            raise ValueError(f"Evidence {evidence_id} not found in matrix")

        if evidence_id not in self.test_evidence_mapping[test_id]:
            self.test_evidence_mapping[test_id].append(evidence_id)
            self.last_updated_timestamp = datetime.now(UTC).isoformat()

    def calculate_coverage(self) -> float:
        """Calculate overall coverage percentage."""
        if not self.requirements:
            return 0.0

        total_coverage = 0.0
        for req_id in self.requirements:
            # Calculate coverage based on linked tests with evidence
            linked_tests = self.requirement_test_mapping.get(req_id, [])
            if not linked_tests:
                self.requirements_coverage[req_id] = 0.0
                continue

            tests_with_evidence = sum(1 for test_id in linked_tests
                                    if self.test_evidence_mapping.get(test_id, []))
            req_coverage = (tests_with_evidence / len(linked_tests)) * 100
            self.requirements_coverage[req_id] = req_coverage
            total_coverage += req_coverage

        self.overall_coverage_percentage = total_coverage / len(self.requirements)
        return self.overall_coverage_percentage


class Gap(BaseModel):
    """
    Compliance gap identification and classification.
    
    Records gaps found during compliance assessment with
    detailed analysis and remediation tracking.
    """
    gap_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique gap identifier")
    title: str = Field(description="Gap title/summary")
    description: str = Field(description="Detailed gap description")

    # Classification
    framework: ComplianceFramework = Field(description="Compliance framework where gap was found")
    requirement_reference: str = Field(description="Specific requirement reference")
    severity: GapSeverity = Field(description="Gap severity level")

    # Impact assessment
    risk_to_patient: str = Field(description="Risk to patient safety")
    risk_to_product: str = Field(description="Risk to product quality")
    risk_to_data: str = Field(description="Risk to data integrity")
    compliance_exposure: str = Field(description="Regulatory compliance exposure")

    # Root cause analysis
    root_cause: str = Field(description="Identified root cause")
    contributing_factors: list[str] = Field(default_factory=list, description="Contributing factors")

    # Current state
    current_state_description: str = Field(description="Current state description")
    required_state_description: str = Field(description="Required state description")

    # Gap metadata
    identified_by: str = Field(description="Who identified the gap")
    identification_timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    identification_method: str = Field(description="How gap was identified")

    # Evidence
    supporting_evidence_ids: list[str] = Field(default_factory=list, description="Evidence supporting gap identification")

    # Tracking
    is_approved: bool = Field(default=False, description="Whether gap has been approved for remediation")
    approved_by: str | None = Field(default=None, description="Gap approver")
    approval_timestamp: str | None = Field(default=None, description="Gap approval timestamp")


class RemediationPlan(BaseModel):
    """
    CAPA-based remediation plan for compliance gaps.
    
    Defines corrective and preventive actions to address
    identified compliance gaps with full tracking.
    """
    plan_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique plan identifier")
    gap_id: str = Field(description="Gap this plan addresses")
    plan_title: str = Field(description="Remediation plan title")
    plan_description: str = Field(description="Detailed remediation approach")

    # CAPA structure
    corrective_actions: list[dict[str, Any]] = Field(default_factory=list, description="Corrective actions")
    preventive_actions: list[dict[str, Any]] = Field(default_factory=list, description="Preventive actions")

    # Planning
    estimated_effort_hours: int = Field(description="Estimated effort in hours")
    required_resources: list[str] = Field(default_factory=list, description="Required resources")
    dependencies: list[str] = Field(default_factory=list, description="Dependencies on other plans")

    # Responsibility
    owner: str = Field(description="Remediation owner")
    assigned_team: list[str] = Field(default_factory=list, description="Assigned team members")
    reviewer: str | None = Field(default=None, description="Plan reviewer")
    approver: str | None = Field(default=None, description="Plan approver")

    # Timeline
    planned_start_date: str | None = Field(default=None, description="Planned start date")
    planned_completion_date: str | None = Field(default=None, description="Planned completion date")
    actual_start_date: str | None = Field(default=None, description="Actual start date")
    actual_completion_date: str | None = Field(default=None, description="Actual completion date")

    # Status tracking
    status: RemediationStatus = Field(default=RemediationStatus.PLANNED, description="Current status")
    percent_complete: int = Field(default=0, ge=0, le=100, description="Completion percentage")

    # Verification
    verification_plan: str = Field(description="How remediation will be verified")
    verification_evidence_required: list[str] = Field(default_factory=list, description="Required verification evidence")
    verification_completed: bool = Field(default=False, description="Whether verification is complete")
    verification_results: str | None = Field(default=None, description="Verification results")

    # Change tracking
    configuration_changes: list[dict[str, Any]] = Field(default_factory=list, description="Required configuration changes")
    process_changes: list[dict[str, Any]] = Field(default_factory=list, description="Required process changes")
    documentation_updates: list[str] = Field(default_factory=list, description="Required documentation updates")

    # Plan metadata
    created_by: str = Field(description="Plan creator")
    creation_timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_updated_by: str | None = Field(default=None, description="Last updater")
    last_updated_timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    def add_corrective_action(self, action: dict[str, Any]) -> None:
        """Add a corrective action to the plan."""
        if "action_id" not in action:
            action["action_id"] = str(uuid4())
        if "status" not in action:
            action["status"] = "planned"
        if "created_timestamp" not in action:
            action["created_timestamp"] = datetime.now(UTC).isoformat()

        self.corrective_actions.append(action)
        self.last_updated_timestamp = datetime.now(UTC).isoformat()

    def add_preventive_action(self, action: dict[str, Any]) -> None:
        """Add a preventive action to the plan."""
        if "action_id" not in action:
            action["action_id"] = str(uuid4())
        if "status" not in action:
            action["status"] = "planned"
        if "created_timestamp" not in action:
            action["created_timestamp"] = datetime.now(UTC).isoformat()

        self.preventive_actions.append(action)
        self.last_updated_timestamp = datetime.now(UTC).isoformat()

    def update_progress(self, new_percent: int, notes: str = "") -> None:
        """Update completion progress."""
        if not 0 <= new_percent <= 100:
            raise ValueError("Percent complete must be between 0 and 100")

        self.percent_complete = new_percent
        if new_percent == 100:
            self.status = RemediationStatus.VERIFICATION
            if not self.actual_completion_date:
                self.actual_completion_date = datetime.now(UTC).isoformat()
        elif new_percent > 0:
            self.status = RemediationStatus.IN_PROGRESS
            if not self.actual_start_date:
                self.actual_start_date = datetime.now(UTC).isoformat()

        self.last_updated_timestamp = datetime.now(UTC).isoformat()


class ComplianceResult(BaseModel):
    """
    Overall compliance assessment result.
    
    Aggregates all compliance assessment activities into a
    comprehensive result with evidence and recommendations.
    """
    result_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique result identifier")
    assessment_name: str = Field(description="Assessment name/identifier")
    system_under_assessment: str = Field(description="System or component assessed")

    # Assessment scope
    frameworks_assessed: list[ComplianceFramework] = Field(description="Frameworks included in assessment")
    assessment_scope: str = Field(description="Detailed assessment scope")
    exclusions: list[str] = Field(default_factory=list, description="Items excluded from assessment")

    # Results by framework
    framework_results: dict[str, dict[str, Any]] = Field(default_factory=dict, description="Results per framework")
    overall_status: ComplianceStatus = Field(description="Overall compliance status")
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Overall compliance score (0-100)")

    # Evidence summary
    total_evidence_items: int = Field(default=0, description="Total evidence items collected")
    verified_evidence_items: int = Field(default=0, description="Verified evidence items")
    evidence_completeness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Evidence completeness")

    # Gap analysis
    total_gaps_identified: int = Field(default=0, description="Total gaps identified")
    critical_gaps: int = Field(default=0, description="Critical gaps count")
    high_priority_gaps: int = Field(default=0, description="High priority gaps count")

    # Remediation
    gaps_with_plans: int = Field(default=0, description="Gaps with remediation plans")
    remediation_coverage_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Remediation coverage")

    # Assessment metadata
    assessment_team: list[str] = Field(description="Assessment team members")
    assessment_start_date: str = Field(description="Assessment start date")
    assessment_completion_date: str | None = Field(default=None, description="Assessment completion date")

    # Quality assurance
    reviewed_by: str | None = Field(default=None, description="Result reviewer")
    review_timestamp: str | None = Field(default=None, description="Review timestamp")
    approved_by: str | None = Field(default=None, description="Result approver")
    approval_timestamp: str | None = Field(default=None, description="Approval timestamp")

    # References
    evidence_ids: list[str] = Field(default_factory=list, description="Evidence supporting this result")
    gap_ids: list[str] = Field(default_factory=list, description="Gaps identified in this assessment")
    remediation_plan_ids: list[str] = Field(default_factory=list, description="Associated remediation plans")
    traceability_matrix_id: str | None = Field(default=None, description="Associated traceability matrix")

    def add_framework_result(self, framework: ComplianceFramework, result_data: dict[str, Any]) -> None:
        """Add results for a specific framework."""
        self.framework_results[framework.value] = result_data

        # Update overall status based on framework results
        self._update_overall_status()

    def _update_overall_status(self) -> None:
        """Update overall compliance status based on framework results."""
        if not self.framework_results:
            self.overall_status = ComplianceStatus.NOT_ASSESSED
            return

        framework_statuses = []
        total_score = 0.0

        for framework, result in self.framework_results.items():
            status = result.get("status", ComplianceStatus.NOT_ASSESSED)
            score = result.get("score", 0.0)

            framework_statuses.append(status)
            total_score += score

        # Calculate overall score
        self.overall_score = total_score / len(self.framework_results)

        # Determine overall status
        if all(status == ComplianceStatus.COMPLIANT for status in framework_statuses):
            self.overall_status = ComplianceStatus.COMPLIANT
        elif any(status == ComplianceStatus.NON_COMPLIANT for status in framework_statuses):
            self.overall_status = ComplianceStatus.NON_COMPLIANT
        elif any(status == ComplianceStatus.PARTIALLY_COMPLIANT for status in framework_statuses):
            self.overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
        elif all(status == ComplianceStatus.NOT_ASSESSED for status in framework_statuses):
            self.overall_status = ComplianceStatus.NOT_ASSESSED
        else:
            self.overall_status = ComplianceStatus.ASSESSMENT_FAILED

    def export_to_file(self, output_path: Path) -> None:
        """Export compliance result to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2, default=str)

    @classmethod
    def load_from_file(cls, file_path: Path) -> "ComplianceResult":
        """Load compliance result from JSON file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Compliance result file not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        return cls(**data)
