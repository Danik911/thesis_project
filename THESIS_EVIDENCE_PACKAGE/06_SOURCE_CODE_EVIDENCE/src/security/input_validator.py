"""
Pharmaceutical Input Security Validator - OWASP LLM01 Protection

This module provides comprehensive input validation and prompt injection detection
for pharmaceutical LLM systems, focusing on OWASP LLM01 (Prompt Injection) 
mitigation with >95% effectiveness target.

CRITICAL: NO FALLBACKS OR PERMISSIVE VALIDATION
- All security violations result in explicit failures
- No sanitization that could mask attack attempts
- Complete diagnostic information for regulatory compliance
- Human consultation triggered for security policy violations
"""

import logging
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .security_config import (
    OWASPCategory,
    SecurityThreatLevel,
    security_config,
)

logger = logging.getLogger(__name__)


@dataclass
class SecurityValidationResult:
    """
    Result of security validation with complete diagnostic information.
    
    CRITICAL: No ambiguous or partial results - explicit pass/fail only.
    """
    is_valid: bool
    threat_level: SecurityThreatLevel
    owasp_category: OWASPCategory
    confidence_score: float  # 0.0-1.0, genuine confidence (no artificial values)
    detected_patterns: list[str]
    validation_details: dict[str, any]
    processing_time_ms: int
    validation_id: UUID
    timestamp: datetime
    error_message: str | None = None


class PharmaceuticalInputSecurityWrapper:
    """
    Comprehensive input security validator for pharmaceutical LLM systems.
    
    Implements OWASP LLM01 (Prompt Injection) protection with pharmaceutical
    compliance requirements (GAMP-5, ALCOA+, 21 CFR Part 11).
    
    CRITICAL OPERATING PRINCIPLES:
    - NO FALLBACKS: All violations result in explicit failures
    - NO SANITIZATION: Security issues are exposed, not masked
    - COMPLETE DIAGNOSTICS: Full audit trail for regulatory compliance
    - EXPLICIT FAILURES: Human consultation required for security violations
    """

    def __init__(self):
        self.config = security_config
        self.validation_cache: dict[str, SecurityValidationResult] = {}
        self._initialize_detection_engine()

    def _initialize_detection_engine(self) -> None:
        """Initialize the security detection engine with pharmaceutical patterns."""
        logger.info("Initializing pharmaceutical input security validator")

        # Validate pharmaceutical compliance requirements
        is_compliant, error_msg = self.config.validate_pharmaceutical_compliance()
        if not is_compliant:
            raise RuntimeError(
                f"Pharmaceutical compliance validation failed: {error_msg}\n"
                f"NO FALLBACKS ALLOWED - Human consultation required."
            )

        logger.info("Pharmaceutical input security validator initialized successfully")

    def validate_urs_content(self,
                           urs_content: str,
                           document_name: str,
                           author: str) -> SecurityValidationResult:
        """
        Validate User Requirements Specification content for security threats.
        
        This is the primary entry point for URS security validation, implementing
        comprehensive OWASP LLM01 protection for pharmaceutical contexts.
        
        Args:
            urs_content: Raw URS document content
            document_name: URS document identifier
            author: Document author for audit trail
            
        Returns:
            SecurityValidationResult: Complete validation result with diagnostics
            
        Raises:
            ValueError: If input parameters are invalid
            RuntimeError: If validation engine fails
        """
        start_time = time.time()
        validation_id = uuid4()

        logger.info(f"[{validation_id}] Starting URS security validation for {document_name}")

        try:
            # Input parameter validation (NO FALLBACKS)
            if not isinstance(urs_content, str):
                raise ValueError(f"URS content must be string, got: {type(urs_content)}")

            if not urs_content.strip():
                raise ValueError("URS content cannot be empty - security validation requires content")

            if not document_name.strip():
                raise ValueError("Document name required for audit trail compliance")

            if not author.strip():
                raise ValueError("Author required for ALCOA+ data integrity compliance")

            # Length validation - pharmaceutical URS typically <10K chars
            if len(urs_content) > self.config.thresholds.max_input_length:
                return SecurityValidationResult(
                    is_valid=False,
                    threat_level=SecurityThreatLevel.HIGH,
                    owasp_category=OWASPCategory.LLM04_MODEL_DENIAL_OF_SERVICE,
                    confidence_score=1.0,  # Certain violation
                    detected_patterns=[f"input_length_exceeded:{len(urs_content)}"],
                    validation_details={
                        "input_length": len(urs_content),
                        "max_allowed": self.config.thresholds.max_input_length,
                        "document_name": document_name,
                        "author": author,
                    },
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    validation_id=validation_id,
                    timestamp=datetime.now(UTC),
                    error_message=f"Input length {len(urs_content)} exceeds pharmaceutical limit {self.config.thresholds.max_input_length}"
                )

            # Core prompt injection detection
            injection_result = self._detect_prompt_injection(urs_content, validation_id)

            # PII detection for pharmaceutical compliance
            pii_result = self._detect_pharmaceutical_pii(urs_content, validation_id)

            # GAMP-5 content limits validation
            gamp5_result = self._enforce_gamp5_limits(urs_content, validation_id)

            # Combine results - fail if any component fails
            final_result = self._combine_validation_results(
                [injection_result, pii_result, gamp5_result],
                validation_id,
                start_time,
                {
                    "document_name": document_name,
                    "author": author,
                    "input_length": len(urs_content),
                }
            )

            logger.info(
                f"[{validation_id}] URS security validation complete: "
                f"valid={final_result.is_valid}, threat={final_result.threat_level}, "
                f"confidence={final_result.confidence_score:.3f}"
            )

            return final_result

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"[{validation_id}] URS security validation failed: {e}")

            # Return explicit failure result (NO FALLBACKS)
            return SecurityValidationResult(
                is_valid=False,
                threat_level=SecurityThreatLevel.CRITICAL,
                owasp_category=OWASPCategory.LLM01_PROMPT_INJECTION,
                confidence_score=0.0,  # Genuine uncertainty due to validation failure
                detected_patterns=["validation_engine_failure"],
                validation_details={
                    "error": str(e),
                    "document_name": document_name,
                    "author": author,
                },
                processing_time_ms=processing_time,
                validation_id=validation_id,
                timestamp=datetime.now(UTC),
                error_message=f"Security validation engine failure: {e}"
            )

    def _detect_prompt_injection(self, content: str, validation_id: UUID) -> SecurityValidationResult:
        """
        Detect prompt injection attempts using OWASP LLM01 patterns.
        
        CRITICAL: Real injection detection - no false confidence scores.
        """
        logger.debug(f"[{validation_id}] Running prompt injection detection")

        detected_patterns = []
        max_confidence = 0.0

        # Check instruction override patterns
        for pattern in self.config.injection_patterns.instruction_overrides:
            matches = pattern.findall(content)
            if matches:
                detected_patterns.extend([f"instruction_override:{match}" for match in matches])
                max_confidence = max(max_confidence, 0.9)

        # Check system prompt attacks
        for pattern in self.config.injection_patterns.system_prompt_attacks:
            matches = pattern.findall(content)
            if matches:
                detected_patterns.extend([f"system_prompt_attack:{match}" for match in matches])
                max_confidence = max(max_confidence, 0.85)

        # Check context escape attempts
        for pattern in self.config.injection_patterns.context_escapes:
            matches = pattern.findall(content)
            if matches:
                detected_patterns.extend([f"context_escape:{match}" for match in matches])
                max_confidence = max(max_confidence, 0.8)

        # Check role hijacking
        for pattern in self.config.injection_patterns.role_hijacking:
            matches = pattern.findall(content)
            if matches:
                detected_patterns.extend([f"role_hijacking:{match}" for match in matches])
                max_confidence = max(max_confidence, 0.75)

        # Check format attacks
        for pattern in self.config.injection_patterns.format_attacks:
            matches = pattern.findall(content)
            if matches:
                detected_patterns.extend([f"format_attack:{match}" for match in matches])
                max_confidence = max(max_confidence, 0.7)

        # Determine threat level and validation status
        # CRITICAL SECURITY FIX: Zero tolerance for injection patterns in pharmaceutical systems
        is_valid = len(detected_patterns) == 0  # Any injection pattern detected = immediate block
        threat_level = self.config.get_threat_level(OWASPCategory.LLM01_PROMPT_INJECTION, max_confidence)

        return SecurityValidationResult(
            is_valid=is_valid,
            threat_level=threat_level,
            owasp_category=OWASPCategory.LLM01_PROMPT_INJECTION,
            confidence_score=max_confidence,
            detected_patterns=detected_patterns,
            validation_details={
                "total_patterns_detected": len(detected_patterns),
                "max_allowed": self.config.thresholds.max_instruction_keywords,
            },
            processing_time_ms=0,  # Will be set by caller
            validation_id=validation_id,
            timestamp=datetime.now(UTC),
        )

    def _detect_pharmaceutical_pii(self, content: str, validation_id: UUID) -> SecurityValidationResult:
        """
        Detect PII in pharmaceutical context for OWASP LLM06 protection.
        
        Enhanced PII detection including patient data, clinical trial info.
        """
        logger.debug(f"[{validation_id}] Running pharmaceutical PII detection")

        detected_patterns = []
        max_confidence = 0.0

        # Check for email addresses
        email_matches = self.config.pii_patterns.email_pattern.findall(content)
        if email_matches:
            detected_patterns.extend([f"email:{match}" for match in email_matches])
            max_confidence = max(max_confidence, 0.95)

        # Check for phone numbers
        phone_matches = self.config.pii_patterns.phone_pattern.findall(content)
        if phone_matches:
            detected_patterns.extend([f"phone:{match}" for match in phone_matches])
            max_confidence = max(max_confidence, 0.9)

        # Check for SSNs
        ssn_matches = self.config.pii_patterns.ssn_pattern.findall(content)
        if ssn_matches:
            detected_patterns.extend([f"ssn:{match}" for match in ssn_matches])
            max_confidence = max(max_confidence, 0.98)

        # Check for API keys/secrets
        api_key_matches = self.config.pii_patterns.api_key_pattern.findall(content)
        if api_key_matches:
            detected_patterns.extend([f"api_key:{match}" for match in api_key_matches])
            max_confidence = max(max_confidence, 0.92)

        # Check for patient IDs
        patient_id_matches = self.config.pii_patterns.patient_id_pattern.findall(content)
        if patient_id_matches:
            detected_patterns.extend([f"patient_id:{match}" for match in patient_id_matches])
            max_confidence = max(max_confidence, 0.88)

        # PII detection is zero-tolerance for pharmaceutical compliance
        is_valid = len(detected_patterns) == 0
        threat_level = (SecurityThreatLevel.CRITICAL if detected_patterns
                       else SecurityThreatLevel.LOW)

        return SecurityValidationResult(
            is_valid=is_valid,
            threat_level=threat_level,
            owasp_category=OWASPCategory.LLM06_SENSITIVE_INFORMATION_DISCLOSURE,
            confidence_score=max_confidence,
            detected_patterns=detected_patterns,
            validation_details={
                "pii_types_detected": len(set(p.split(":")[0] for p in detected_patterns)),
                "total_pii_instances": len(detected_patterns),
            },
            processing_time_ms=0,  # Will be set by caller
            validation_id=validation_id,
            timestamp=datetime.now(UTC),
        )

    def _enforce_gamp5_limits(self, content: str, validation_id: UUID) -> SecurityValidationResult:
        """
        Enforce GAMP-5 specific content validation limits.
        
        Pharmaceutical-specific content validation beyond general security.
        """
        logger.debug(f"[{validation_id}] Running GAMP-5 limits validation")

        validation_issues = []

        # Check for excessive special characters (potential encoding attacks)
        special_char_count = len(re.findall(r'[^\w\s\-.,;:()\[\]{}"]', content))
        special_char_ratio = special_char_count / len(content) if content else 0

        if special_char_ratio > 0.1:  # More than 10% special characters
            validation_issues.append(f"excessive_special_chars:{special_char_ratio:.3f}")

        # Check for extremely long lines (potential buffer overflow attempts)
        lines = content.split("\n")
        max_line_length = max(len(line) for line in lines) if lines else 0

        if max_line_length > 1000:  # Lines over 1000 chars suspicious
            validation_issues.append(f"excessive_line_length:{max_line_length}")

        # Check for repeated patterns (potential DoS attempts)
        repeated_pattern = re.findall(r"(.{10,})\1{3,}", content)
        if repeated_pattern:
            validation_issues.append(f"repeated_patterns:{len(repeated_pattern)}")

        is_valid = len(validation_issues) == 0
        confidence_score = 0.7 if validation_issues else 0.0
        threat_level = (SecurityThreatLevel.MEDIUM if validation_issues
                       else SecurityThreatLevel.LOW)

        return SecurityValidationResult(
            is_valid=is_valid,
            threat_level=threat_level,
            owasp_category=OWASPCategory.LLM04_MODEL_DENIAL_OF_SERVICE,
            confidence_score=confidence_score,
            detected_patterns=validation_issues,
            validation_details={
                "special_char_ratio": special_char_ratio,
                "max_line_length": max_line_length,
                "repeated_patterns_found": len(repeated_pattern),
            },
            processing_time_ms=0,  # Will be set by caller
            validation_id=validation_id,
            timestamp=datetime.now(UTC),
        )

    def _combine_validation_results(self,
                                   results: list[SecurityValidationResult],
                                   validation_id: UUID,
                                   start_time: float,
                                   metadata: dict[str, any]) -> SecurityValidationResult:
        """
        Combine multiple validation results into final assessment.
        
        CRITICAL: Fail-safe combination - any failure results in overall failure.
        """
        processing_time = int((time.time() - start_time) * 1000)

        # Any individual failure results in overall failure
        overall_valid = all(result.is_valid for result in results)

        # Highest threat level wins
        threat_levels = [result.threat_level for result in results]
        max_threat = max(threat_levels, key=lambda x: ["low", "medium", "high", "critical"].index(x.value))

        # Highest confidence score (most certain detection)
        max_confidence = max(result.confidence_score for result in results)

        # Primary OWASP category (highest threat)
        primary_category = next(
            result.owasp_category for result in results
            if result.threat_level == max_threat
        )

        # Combine all detected patterns
        all_patterns = []
        for result in results:
            all_patterns.extend(result.detected_patterns)

        # Combine validation details
        combined_details = metadata.copy()
        for i, result in enumerate(results):
            combined_details[f"component_{i}_{result.owasp_category.value}"] = result.validation_details

        return SecurityValidationResult(
            is_valid=overall_valid,
            threat_level=max_threat,
            owasp_category=primary_category,
            confidence_score=max_confidence,
            detected_patterns=all_patterns,
            validation_details=combined_details,
            processing_time_ms=processing_time,
            validation_id=validation_id,
            timestamp=datetime.now(UTC),
            error_message=None if overall_valid else f"Security validation failed: {len(all_patterns)} threats detected"
        )

    def sanitize_pharmaceutical_content(self, content: str) -> str:
        """
        CRITICAL: This method intentionally raises an error.
        
        NO SANITIZATION ALLOWED in pharmaceutical systems:
        - Sanitization masks security threats
        - Regulatory compliance requires explicit threat disclosure
        - ALCOA+ data integrity prohibits content modification
        
        Instead of sanitizing, validation must FAIL EXPLICITLY.
        """
        raise RuntimeError(
            "Content sanitization is PROHIBITED in pharmaceutical systems.\n"
            "ALCOA+ data integrity requires original content preservation.\n"
            "Security violations must be handled through explicit validation failure.\n"
            "NO FALLBACKS ALLOWED - Human consultation required."
        )
