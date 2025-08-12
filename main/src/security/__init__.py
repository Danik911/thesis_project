"""
Security Assessment Framework for OWASP LLM Top 10 Compliance Testing

This module provides comprehensive security assessment capabilities for pharmaceutical
LLM systems, focusing on OWASP LLM Top 10 vulnerabilities with GAMP-5 compliance.

Key Components:
- OWASP test scenario generation (LLM01, LLM06, LLM09)
- Vulnerability detection and analysis
- Security metrics collection and reporting
- Execution harness with Phoenix monitoring
- Human-in-loop evaluation integration
- NO FALLBACKS - explicit security validation only
"""

from .owasp_test_scenarios import OWASPTestScenarios
from .security_assessment_workflow import (
    SecurityAssessmentCompleteEvent,
    SecurityAssessmentStartEvent,
    SecurityAssessmentWorkflow,
    SecurityTestExecutionEvent,
    VulnerabilityDetectedEvent,
    HumanConsultationRequiredEvent,
)
from .security_execution_harness import (
    SecurityExecutionHarness,
    run_security_assessment_experiment,
)
from .security_metrics_collector import SecurityMetricsCollector
from .vulnerability_detector import VulnerabilityDetector

# Legacy components (if they exist)
try:
    from .alcoa_compliance import ALCOAComplianceChecker
    from .owasp_validator import OWASPValidator
    LEGACY_COMPONENTS = ["ALCOAComplianceChecker", "OWASPValidator"]
except ImportError:
    LEGACY_COMPONENTS = []

__all__ = [
    # Core OWASP LLM Top 10 Security Assessment Framework
    "OWASPTestScenarios",
    "VulnerabilityDetector", 
    "SecurityMetricsCollector",
    "SecurityExecutionHarness",
    
    # Workflow Components
    "SecurityAssessmentWorkflow",
    "SecurityAssessmentStartEvent",
    "SecurityTestExecutionEvent",
    "VulnerabilityDetectedEvent",
    "HumanConsultationRequiredEvent",
    "SecurityAssessmentCompleteEvent",
    
    # Convenience Functions
    "run_security_assessment_experiment",
] + LEGACY_COMPONENTS
