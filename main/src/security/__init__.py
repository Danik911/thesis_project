"""
OWASP Security Framework for Pharmaceutical LLM Systems

This module provides comprehensive OWASP LLM Top 10 security protection and assessment
capabilities for pharmaceutical LLM systems with GAMP-5 compliance.

Key Components:
- Runtime Security Protection (LLM01, LLM06, LLM09)
- Input validation and prompt injection protection
- System prompt isolation and template hardening
- Output security scanning and PII detection
- Security assessment and testing framework
- Comprehensive audit trail for regulatory compliance
- NO FALLBACKS - explicit security validation only

Runtime Protection:
- PharmaceuticalInputSecurityWrapper: Input validation and injection detection
- SecureLLMWrapper: System prompt isolation and secure LLM operations
- PharmaceuticalOutputScanner: Output security scanning and compliance validation
- SecurityConfig: Central OWASP compliance configuration

Assessment Framework:
- OWASP test scenario generation and execution
- Vulnerability detection and analysis
- Security metrics collection and reporting
- Phoenix monitoring integration
"""

# Runtime Security Protection Components (OWASP Implementation)
from .input_validator import (
    PharmaceuticalInputSecurityWrapper,
    SecurityValidationResult,
)
from .output_scanner import (
    OutputSecurityScanResult,
    PharmaceuticalOutputScanner,
)

# Security Assessment Framework Components
from .owasp_test_scenarios import OWASPTestScenarios
from .prompt_guardian import (
    PromptSecurityAudit,
    SecureLLMWrapper,
)
from .security_assessment_workflow import (
    HumanConsultationRequiredEvent,
    SecurityAssessmentCompleteEvent,
    SecurityAssessmentStartEvent,
    SecurityAssessmentWorkflow,
    SecurityTestExecutionEvent,
    VulnerabilityDetectedEvent,
)
from .security_config import (
    OWASPCategory,
    SecurityConfig,
    SecurityThreatLevel,
    SecurityThresholds,
    security_config,
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
    # Runtime Security Protection (OWASP LLM Top 10 Implementation)
    "SecurityConfig",
    "SecurityThresholds",
    "SecurityThreatLevel",
    "OWASPCategory",
    "security_config",
    "PharmaceuticalInputSecurityWrapper",
    "SecurityValidationResult",
    "SecureLLMWrapper",
    "PromptSecurityAudit",
    "PharmaceuticalOutputScanner",
    "OutputSecurityScanResult",

    # Security Assessment Framework
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
