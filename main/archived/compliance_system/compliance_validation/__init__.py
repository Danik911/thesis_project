"""
Compliance Validation Framework for Pharmaceutical Test Generation

This module provides comprehensive compliance validation capabilities for
GAMP-5, 21 CFR Part 11, and ALCOA+ assessment with full audit trail support.

Key Features:
- GAMP-5 categorization and lifecycle validation
- 21 CFR Part 11 electronic records and signatures verification
- ALCOA+ data integrity assessment with weighted scoring
- Evidence collection and traceability matrix
- Gap analysis and remediation planning
- NO FALLBACK BEHAVIORS - all errors surface explicitly

Components:
- models: Core data models and validation structures
- evidence_collector: Evidence gathering and template management
- gamp5_assessor: GAMP-5 compliance assessment
- cfr_part11_verifier: 21 CFR Part 11 verification
- alcoa_scorer: ALCOA+ scoring and assessment
- gap_analyzer: Gap identification and analysis
- remediation_planner: CAPA and remediation planning
- compliance_workflow: Main orchestration workflow
"""

from .alcoa_scorer import ALCOAScorer
from .cfr_part11_verifier import CFRPart11Verifier
from .compliance_workflow import ComplianceWorkflow
from .evidence_collector import EvidenceCollector
from .gamp5_assessor import GAMP5Assessor
from .gap_analyzer import GapAnalyzer
from .models import (
    ComplianceFramework,
    ComplianceResult,
    ComplianceStatus,
    Evidence,
    EvidenceType,
    Gap,
    GapSeverity,
    RemediationPlan,
    RemediationStatus,
    TraceabilityMatrix,
    ValidationTemplate,
)
from .remediation_planner import RemediationPlanner

__all__ = [
    # Core Models
    "ComplianceResult",
    "Evidence",
    "Gap",
    "RemediationPlan",
    "ValidationTemplate",
    "TraceabilityMatrix",

    # Enums
    "ComplianceFramework",
    "ComplianceStatus",
    "EvidenceType",
    "GapSeverity",
    "RemediationStatus",

    # Core Components
    "EvidenceCollector",
    "GAMP5Assessor",
    "CFRPart11Verifier",
    "ALCOAScorer",
    "GapAnalyzer",
    "RemediationPlanner",
    "ComplianceWorkflow"
]
