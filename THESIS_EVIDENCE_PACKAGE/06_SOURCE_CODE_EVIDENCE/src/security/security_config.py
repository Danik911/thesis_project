"""
OWASP Security Configuration for LLM Top 10 Compliance

This module defines security thresholds, validation rules, and OWASP compliance
settings for pharmaceutical LLM systems. All configurations follow GAMP-5
requirements with NO FALLBACKS - explicit security validation only.

CRITICAL: NO FALLBACK VALUES OR DEFAULT SECURITY STATES
- All security violations result in explicit failures
- No permissive defaults that could mask security issues
- Human consultation required for security policy decisions
"""

import os
import re
from dataclasses import dataclass
from enum import Enum
from re import Pattern

from dotenv import load_dotenv

load_dotenv()


class SecurityThreatLevel(str, Enum):
    """Security threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OWASPCategory(str, Enum):
    """OWASP LLM Top 10 categories."""
    LLM01_PROMPT_INJECTION = "LLM01"
    LLM02_INSECURE_OUTPUT_HANDLING = "LLM02"
    LLM03_TRAINING_DATA_POISONING = "LLM03"
    LLM04_MODEL_DENIAL_OF_SERVICE = "LLM04"
    LLM05_SUPPLY_CHAIN_VULNERABILITIES = "LLM05"
    LLM06_SENSITIVE_INFORMATION_DISCLOSURE = "LLM06"
    LLM07_INSECURE_PLUGIN_DESIGN = "LLM07"
    LLM08_EXCESSIVE_AGENCY = "LLM08"
    LLM09_OVERRELIANCE = "LLM09"
    LLM10_MODEL_THEFT = "LLM10"


@dataclass(frozen=True)
class SecurityThresholds:
    """Security validation thresholds - NO FALLBACKS ALLOWED."""

    # LLM01: Prompt Injection Detection (TARGET: 95%+ effectiveness)
    max_input_length: int = 10000  # Pharmaceutical URS typical max length
    max_instruction_keywords: int = 0  # ZERO TOLERANCE: Any injection pattern = block
    min_confidence_threshold: float = 0.85  # Minimum confidence for safety

    # LLM06: Sensitive Information Disclosure
    pii_detection_threshold: float = 0.9  # PII detection confidence
    secrets_pattern_matches: int = 0  # Zero tolerance for secrets

    # LLM09: Overreliance Prevention
    uncertainty_threshold: float = 0.3  # Max uncertainty before human consultation
    confidence_variance_threshold: float = 0.2  # Max confidence variance

    # Performance Constraints
    max_security_overhead_ms: int = 100  # Max security processing time
    max_memory_overhead_mb: int = 50  # Max memory overhead for security

    # Pharmaceutical Compliance
    gamp5_compliance_required: bool = True  # GAMP-5 validation mandatory
    alcoa_plus_required: bool = True  # ALCOA+ data integrity mandatory
    cfr_part11_audit_required: bool = True  # 21 CFR Part 11 audit trail mandatory


@dataclass(frozen=True)
class InjectionPatterns:
    """
    Prompt injection detection patterns - based on OWASP LLM01 guidelines.
    
    CRITICAL: These patterns detect real injection attempts.
    NO FALLBACKS - any match results in explicit security failure.
    """

    # Direct instruction override attempts
    instruction_overrides: list[Pattern] = None

    # System prompt manipulation attempts
    system_prompt_attacks: list[Pattern] = None

    # Context boundary violations
    context_escapes: list[Pattern] = None

    # Role manipulation attempts
    role_hijacking: list[Pattern] = None

    # Output formatting attacks
    format_attacks: list[Pattern] = None

    def __post_init__(self):
        """Initialize compiled regex patterns."""

        # CRITICAL: Real injection patterns that actually threaten LLM security
        object.__setattr__(self, "instruction_overrides", [
            re.compile(r"(?i)ignore\s+(?:all\s+)?(?:previous\s+)?(?:instructions?|prompts?|rules?)", re.MULTILINE),
            re.compile(r"(?i)forget\s+(?:everything|all|previous|your)", re.MULTILINE),
            re.compile(r"(?i)new\s+(?:instruction|prompt|rule|system)", re.MULTILINE),
            re.compile(r"(?i)override\s+(?:system|previous|default)", re.MULTILINE),
            re.compile(r"(?i)instead\s+of.*?(?:do|say|respond|answer)", re.MULTILINE),
        ])

        object.__setattr__(self, "system_prompt_attacks", [
            re.compile(r"(?i)you\s+are\s+now", re.MULTILINE),
            re.compile(r"(?i)act\s+as\s+(?:if\s+)?(?:you\s+are)?", re.MULTILINE),
            re.compile(r"(?i)pretend\s+(?:to\s+be|that\s+you)", re.MULTILINE),
            re.compile(r"(?i)roleplay\s+as", re.MULTILINE),
            re.compile(r"(?i)simulate\s+(?:being|a)", re.MULTILINE),
        ])

        object.__setattr__(self, "context_escapes", [
            re.compile(r"(?i)break\s+out\s+of", re.MULTILINE),
            re.compile(r"(?i)escape\s+from", re.MULTILINE),
            re.compile(r"(?i)exit\s+(?:the\s+)?(?:system|context|mode)", re.MULTILINE),
            re.compile(r"(?i)end\s+(?:of\s+)?(?:input|prompt|context)", re.MULTILINE),
        ])

        object.__setattr__(self, "role_hijacking", [
            re.compile(r"(?i)(?:you\s+are|i\s+am)\s+(?:a\s+)?(?:developer|admin|system)", re.MULTILINE),
            re.compile(r"(?i)as\s+(?:an?\s+)?(?:ai|assistant|system)", re.MULTILINE),
            re.compile(r"(?i)speaking\s+as", re.MULTILINE),
        ])

        object.__setattr__(self, "format_attacks", [
            re.compile(r"(?i)output\s+in\s+(?:json|xml|html|script)", re.MULTILINE),
            re.compile(r"(?i)format\s+as\s+(?:code|script|sql)", re.MULTILINE),
            re.compile(r"(?i)return\s+raw\s+(?:data|output)", re.MULTILINE),
        ])


@dataclass(frozen=True)
class PIIPatterns:
    """
    PII detection patterns for LLM06 (Sensitive Information Disclosure).
    
    Pharmaceutical context requires enhanced PII protection including
    patient data, clinical trial information, and proprietary data.
    """

    # Email addresses
    email_pattern: Pattern = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    )

    # Phone numbers (US format)
    phone_pattern: Pattern = re.compile(
        r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
    )

    # Social Security Numbers
    ssn_pattern: Pattern = re.compile(
        r"\b\d{3}-?\d{2}-?\d{4}\b"
    )

    # Credit card numbers (basic pattern)
    credit_card_pattern: Pattern = re.compile(
        r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
    )

    # API keys and tokens (enhanced patterns)
    api_key_pattern: Pattern = re.compile(
        r'\b(?:api[_-]?key|token|secret)["\s:=\-]*[A-Za-z0-9+/\-_]{10,}\b|sk-[A-Za-z0-9]{20,}',
        re.IGNORECASE
    )

    # Pharmaceutical-specific PII
    patient_id_pattern: Pattern = re.compile(
        r'\b(?:patient[_-]?id|subject[_-]?id)["\s:=]+[A-Za-z0-9-]{6,}\b',
        re.IGNORECASE
    )


class SecurityConfig:
    """
    Central security configuration for OWASP LLM compliance.
    
    CRITICAL RULES:
    - NO FALLBACK SECURITY POLICIES
    - NO PERMISSIVE DEFAULTS
    - EXPLICIT FAILURE ON VIOLATIONS
    - HUMAN CONSULTATION FOR POLICY CHANGES
    """

    def __init__(self):
        self.thresholds = SecurityThresholds()
        self.injection_patterns = InjectionPatterns()
        self.pii_patterns = PIIPatterns()

        # Environment-based overrides (NO FALLBACKS)
        self._load_environment_overrides()

    def _load_environment_overrides(self) -> None:
        """
        Load security configuration overrides from environment.
        
        CRITICAL: Environment variables must be explicit.
        NO FALLBACKS to defaults if env vars are malformed.
        """
        try:
            # Security thresholds from environment
            if env_max_length := os.getenv("SECURITY_MAX_INPUT_LENGTH"):
                if not env_max_length.isdigit():
                    raise ValueError(f"SECURITY_MAX_INPUT_LENGTH must be integer, got: {env_max_length}")
                object.__setattr__(self.thresholds, "max_input_length", int(env_max_length))

            if env_confidence := os.getenv("SECURITY_MIN_CONFIDENCE"):
                try:
                    confidence_val = float(env_confidence)
                    if not (0.0 <= confidence_val <= 1.0):
                        raise ValueError("Confidence must be between 0.0 and 1.0")
                    object.__setattr__(self.thresholds, "min_confidence_threshold", confidence_val)
                except ValueError as e:
                    raise ValueError(f"SECURITY_MIN_CONFIDENCE invalid: {e}")

            # Performance overrides
            if env_overhead := os.getenv("SECURITY_MAX_OVERHEAD_MS"):
                if not env_overhead.isdigit():
                    raise ValueError(f"SECURITY_MAX_OVERHEAD_MS must be integer, got: {env_overhead}")
                object.__setattr__(self.thresholds, "max_security_overhead_ms", int(env_overhead))

        except Exception as e:
            raise RuntimeError(
                f"Security configuration environment override failed: {e}\n"
                f"NO FALLBACKS ALLOWED - Human consultation required."
            ) from e

    def get_threat_level(self, owasp_category: OWASPCategory,
                        confidence_score: float) -> SecurityThreatLevel:
        """
        Determine threat level for given OWASP category and confidence.
        
        Args:
            owasp_category: OWASP LLM category
            confidence_score: Detection confidence (0.0-1.0)
            
        Returns:
            SecurityThreatLevel: Determined threat level
            
        Raises:
            ValueError: If inputs are invalid (NO FALLBACKS)
        """
        if not (0.0 <= confidence_score <= 1.0):
            raise ValueError(f"Confidence score must be 0.0-1.0, got: {confidence_score}")

        # High-priority categories (prompt injection, sensitive data)
        high_priority = {OWASPCategory.LLM01_PROMPT_INJECTION,
                        OWASPCategory.LLM06_SENSITIVE_INFORMATION_DISCLOSURE}

        if owasp_category in high_priority:
            if confidence_score >= 0.9:
                return SecurityThreatLevel.CRITICAL
            if confidence_score >= 0.7:
                return SecurityThreatLevel.HIGH
            if confidence_score >= 0.5:
                return SecurityThreatLevel.MEDIUM
            return SecurityThreatLevel.LOW

        # Medium-priority categories
        medium_priority = {OWASPCategory.LLM09_OVERRELIANCE,
                          OWASPCategory.LLM04_MODEL_DENIAL_OF_SERVICE}

        if owasp_category in medium_priority:
            if confidence_score >= 0.8:
                return SecurityThreatLevel.HIGH
            if confidence_score >= 0.6:
                return SecurityThreatLevel.MEDIUM
            return SecurityThreatLevel.LOW

        # Lower-priority categories
        if confidence_score >= 0.85:
            return SecurityThreatLevel.MEDIUM
        return SecurityThreatLevel.LOW

    def validate_pharmaceutical_compliance(self) -> tuple[bool, str]:
        """
        Validate pharmaceutical compliance requirements.
        
        Returns:
            tuple: (is_compliant, error_message)
        """
        errors = []

        # GAMP-5 compliance check
        if not self.thresholds.gamp5_compliance_required:
            errors.append("GAMP-5 compliance is disabled - pharmaceutical requirement violated")

        # ALCOA+ compliance check
        if not self.thresholds.alcoa_plus_required:
            errors.append("ALCOA+ data integrity is disabled - pharmaceutical requirement violated")

        # 21 CFR Part 11 audit trail check
        if not self.thresholds.cfr_part11_audit_required:
            errors.append("21 CFR Part 11 audit trail is disabled - pharmaceutical requirement violated")

        # Security thresholds validation
        if self.thresholds.min_confidence_threshold < 0.8:
            errors.append(f"Minimum confidence threshold {self.thresholds.min_confidence_threshold} below pharmaceutical standard (0.8)")

        if errors:
            return False, "; ".join(errors)

        return True, "Pharmaceutical compliance validated"


# Global security configuration instance
security_config = SecurityConfig()
