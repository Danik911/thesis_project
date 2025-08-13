"""
Pharmaceutical Output Security Scanner - OWASP LLM06 Protection

This module provides comprehensive output scanning and security validation
for pharmaceutical LLM systems, focusing on OWASP LLM06 (Insecure Output Handling)
and LLM06 (Sensitive Information Disclosure) protection.

CRITICAL: NO FALLBACKS IN OUTPUT SECURITY
- All sensitive data detected results in explicit failures
- No sanitization that could mask security issues
- Complete regulatory compliance validation (ALCOA+, 21 CFR Part 11)
- Pharmaceutical-specific PII and proprietary data protection
"""

import logging
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from .security_config import (
    OWASPCategory,
    SecurityThreatLevel,
    security_config,
)

logger = logging.getLogger(__name__)


@dataclass
class OutputSecurityScanResult:
    """
    Result of comprehensive output security scanning.
    
    Provides complete diagnostic information for regulatory compliance.
    """
    is_secure: bool
    threat_level: SecurityThreatLevel
    owasp_category: OWASPCategory
    confidence_score: float  # 0.0-1.0, genuine detection confidence
    detected_threats: list[str]
    pii_detected: list[dict[str, str]]
    secrets_detected: list[dict[str, str]]
    compliance_issues: list[str]
    scan_details: dict[str, Any]
    processing_time_ms: int
    scan_id: UUID
    timestamp: datetime
    error_message: str | None = None


class PharmaceuticalOutputScanner:
    """
    Comprehensive output security scanner for pharmaceutical LLM systems.
    
    Implements OWASP LLM06 (Insecure Output Handling) protection with:
    - PII detection and blocking
    - Secrets and API key detection
    - Pharmaceutical compliance validation
    - Proprietary data protection
    - Output format validation
    
    CRITICAL OPERATING PRINCIPLES:
    - NO FALLBACKS: All security violations result in explicit failures
    - NO SANITIZATION: Security issues are exposed, not masked
    - COMPLETE SCANNING: Multi-layer security analysis
    - AUDIT EVERYTHING: Full regulatory compliance audit trail
    """

    def __init__(self):
        self.config = security_config
        self._initialize_pharmaceutical_patterns()

        logger.info("Pharmaceutical output security scanner initialized")

    def _initialize_pharmaceutical_patterns(self) -> None:
        """Initialize pharmaceutical-specific detection patterns."""

        # Enhanced patterns for pharmaceutical context
        self._pharma_patterns = {
            # Clinical trial identifiers
            "clinical_trial_id": re.compile(
                r"\b(?:trial|study)[_\s-]?(?:id|number)[:\s]*([A-Za-z0-9-]{6,20})\b",
                re.IGNORECASE
            ),

            # Drug product codes
            "drug_product_code": re.compile(
                r"\b(?:product|drug)[_\s-]?code[:\s]*([A-Za-z0-9-]{4,15})\b",
                re.IGNORECASE
            ),

            # Batch/Lot numbers
            "batch_lot_number": re.compile(
                r"\b(?:batch|lot)[_\s-]?(?:number|id)[:\s]*([A-Za-z0-9-]{4,20})\b",
                re.IGNORECASE
            ),

            # Manufacturing site codes
            "manufacturing_site": re.compile(
                r"\b(?:site|facility)[_\s-]?code[:\s]*([A-Za-z0-9-]{3,10})\b",
                re.IGNORECASE
            ),

            # Regulatory submission numbers
            "regulatory_submission": re.compile(
                r"\b(?:IND|NDA|ANDA|BLA|MAA)[_\s-]?(?:number|id)?[:\s]*([A-Za-z0-9-]{4,15})\b",
                re.IGNORECASE
            ),

            # Quality control test IDs
            "qc_test_id": re.compile(
                r"\b(?:QC|quality)[_\s-]?(?:test|check)[_\s-]?(?:id|number)[:\s]*([A-Za-z0-9-]{4,15})\b",
                re.IGNORECASE
            ),
        }

        # Secrets detection patterns (enhanced)
        self._secrets_patterns = {
            "api_key": re.compile(
                r'\b(?:api[_-]?key|apikey)["\s:=\-]*([A-Za-z0-9+/\-_]{15,})\b',
                re.IGNORECASE
            ),

            "password": re.compile(
                r'\b(?:password|passwd|pwd)["\s:=]*([A-Za-z0-9!@#$%^&*]{6,})\b',
                re.IGNORECASE
            ),

            "token": re.compile(
                r'\b(?:token|bearer)["\s:=]*([A-Za-z0-9+/=\-_]{15,})\b',
                re.IGNORECASE
            ),

            "database_connection": re.compile(
                r'\b(?:connection[_-]?string|jdbc|mongodb://|postgresql://)["\s:=]*([^\s"\']{10,})\b',
                re.IGNORECASE
            ),

            "private_key": re.compile(
                r"-----BEGIN (?:RSA )?PRIVATE KEY-----",
                re.MULTILINE
            ),
            
            # Enhanced pattern for "sk-" prefixed API keys
            "openai_api_key": re.compile(
                r'\bsk-[A-Za-z0-9]{20,}\b',
                re.IGNORECASE
            ),
        }

    def scan_for_pii(self, output_content: str, scan_id: UUID) -> tuple[list[dict[str, str]], float]:
        """
        Scan output content for personally identifiable information.
        
        Args:
            output_content: LLM output content to scan
            scan_id: Scan operation identifier
            
        Returns:
            Tuple[List[Dict], float]: (detected_pii, max_confidence)
        """
        logger.debug(f"[{scan_id}] Scanning for PII")

        detected_pii = []
        max_confidence = 0.0

        # Email addresses
        email_matches = self.config.pii_patterns.email_pattern.findall(output_content)
        for match in email_matches:
            detected_pii.append({
                "type": "email",
                "value": match,
                "confidence": 0.95,
                "position": output_content.find(match)
            })
            max_confidence = max(max_confidence, 0.95)

        # Phone numbers
        phone_matches = self.config.pii_patterns.phone_pattern.findall(output_content)
        for match in phone_matches:
            detected_pii.append({
                "type": "phone",
                "value": match,
                "confidence": 0.90,
                "position": output_content.find(match)
            })
            max_confidence = max(max_confidence, 0.90)

        # Social Security Numbers
        ssn_matches = self.config.pii_patterns.ssn_pattern.findall(output_content)
        for match in ssn_matches:
            detected_pii.append({
                "type": "ssn",
                "value": match,
                "confidence": 0.98,
                "position": output_content.find(match)
            })
            max_confidence = max(max_confidence, 0.98)

        # Credit card numbers
        cc_matches = self.config.pii_patterns.credit_card_pattern.findall(output_content)
        for match in cc_matches:
            detected_pii.append({
                "type": "credit_card",
                "value": match,
                "confidence": 0.85,
                "position": output_content.find(match)
            })
            max_confidence = max(max_confidence, 0.85)

        # Patient IDs (pharmaceutical-specific)
        patient_matches = self.config.pii_patterns.patient_id_pattern.findall(output_content)
        for match in patient_matches:
            detected_pii.append({
                "type": "patient_id",
                "value": match,
                "confidence": 0.88,
                "position": output_content.find(match)
            })
            max_confidence = max(max_confidence, 0.88)

        # Pharmaceutical-specific PII
        for pattern_name, pattern in self._pharma_patterns.items():
            matches = pattern.findall(output_content)
            for match in matches:
                detected_pii.append({
                    "type": pattern_name,
                    "value": match,
                    "confidence": 0.80,
                    "position": output_content.find(match)
                })
                max_confidence = max(max_confidence, 0.80)
        
        # Additional patient ID detection patterns
        patient_patterns = [
            re.compile(r'\bpatient\s+id[:\s]*([A-Za-z0-9]{4,15})\b', re.IGNORECASE),
            re.compile(r'\bpatient[:\s]+([A-Za-z0-9]{4,15})\b', re.IGNORECASE),
            re.compile(r'\bid[:\s]+([A-Za-z0-9]{4,15})', re.IGNORECASE),
        ]
        
        for pattern in patient_patterns:
            matches = pattern.findall(output_content)
            for match in matches:
                detected_pii.append({
                    "type": "patient_id_enhanced",
                    "value": match,
                    "confidence": 0.85,
                    "position": output_content.find(match)
                })
                max_confidence = max(max_confidence, 0.85)

        return detected_pii, max_confidence

    def detect_secrets(self, output_content: str, scan_id: UUID) -> tuple[list[dict[str, str]], float]:
        """
        Detect secrets and credentials in output content.
        
        Args:
            output_content: LLM output content to scan
            scan_id: Scan operation identifier
            
        Returns:
            Tuple[List[Dict], float]: (detected_secrets, max_confidence)
        """
        logger.debug(f"[{scan_id}] Scanning for secrets")

        detected_secrets = []
        max_confidence = 0.0

        for secret_type, pattern in self._secrets_patterns.items():
            matches = pattern.findall(output_content)
            for match in matches:
                # Assign confidence based on secret type
                confidence = {
                    "api_key": 0.92,
                    "password": 0.85,
                    "token": 0.90,
                    "database_connection": 0.95,
                    "private_key": 0.98,
                    "openai_api_key": 0.95,
                }.get(secret_type, 0.80)

                detected_secrets.append({
                    "type": secret_type,
                    "value": match,
                    "confidence": confidence,
                    "position": output_content.find(match)
                })
                max_confidence = max(max_confidence, confidence)
        
        # Additional API key patterns that might be missed
        additional_api_patterns = [
            re.compile(r'\bapi\s+key[:\s]*([A-Za-z0-9\-_]{10,})', re.IGNORECASE),
            re.compile(r'\bkey[:\s]*([A-Za-z0-9\-_]{15,})', re.IGNORECASE),
        ]
        
        for pattern in additional_api_patterns:
            matches = pattern.findall(output_content)
            for match in matches:
                detected_secrets.append({
                    "type": "api_key_additional",
                    "value": match,
                    "confidence": 0.85,
                    "position": output_content.find(match)
                })
                max_confidence = max(max_confidence, 0.85)

        return detected_secrets, max_confidence

    def validate_pharmaceutical_compliance(self,
                                         output_content: str,
                                         scan_id: UUID) -> tuple[list[str], float]:
        """
        Validate pharmaceutical compliance in output content.
        
        Args:
            output_content: LLM output content to validate
            scan_id: Scan operation identifier
            
        Returns:
            Tuple[List[str], float]: (compliance_issues, confidence)
        """
        logger.debug(f"[{scan_id}] Validating pharmaceutical compliance")

        compliance_issues = []
        max_confidence = 0.0

        # Check for inappropriate medical advice
        medical_advice_patterns = [
            r"(?i)\btake\s+\d+\s*(?:mg|mcg|g)\b",  # Dosage recommendations
            r"(?i)\b(?:discontinue|stop)\s+(?:taking|using)\b",  # Treatment advice
            r"(?i)\bdiagnosis\s+is\b",  # Diagnostic statements
            r"(?i)\brecommend\s+(?:taking|using|trying)\b",  # Treatment recommendations
        ]

        for pattern in medical_advice_patterns:
            if re.search(pattern, output_content):
                compliance_issues.append(f"inappropriate_medical_advice:{pattern}")
                max_confidence = max(max_confidence, 0.85)

        # Check for regulatory claim violations
        regulatory_claim_patterns = [
            r"(?i)\b(?:FDA|EMA)\s+approved\b",  # Regulatory approval claims
            r"(?i)\b(?:safe|effective)\s+for\s+(?:treating|curing)\b",  # Safety/efficacy claims
            r"(?i)\bclinically\s+proven\b",  # Clinical proof claims
        ]

        for pattern in regulatory_claim_patterns:
            if re.search(pattern, output_content):
                compliance_issues.append(f"regulatory_claim_violation:{pattern}")
                max_confidence = max(max_confidence, 0.90)

        # Check for proprietary information leakage
        proprietary_patterns = [
            r"(?i)\b(?:confidential|proprietary|trade\s+secret)\b",
            r"(?i)\binternal\s+(?:document|memo|email)\b",
            r"(?i)\bnot\s+for\s+(?:public|external)\s+(?:use|distribution)\b",
        ]

        for pattern in proprietary_patterns:
            if re.search(pattern, output_content):
                compliance_issues.append(f"proprietary_info_leakage:{pattern}")
                max_confidence = max(max_confidence, 0.75)

        return compliance_issues, max_confidence

    def sanitize_output(self, output_content: str) -> str:
        """
        CRITICAL: This method intentionally raises an error.
        
        NO SANITIZATION ALLOWED in pharmaceutical systems:
        - Sanitization masks security threats from audit trail
        - ALCOA+ data integrity requires complete output preservation
        - Regulatory compliance demands explicit threat disclosure
        
        Instead of sanitizing, scanning must FAIL EXPLICITLY.
        """
        raise RuntimeError(
            "Output sanitization is PROHIBITED in pharmaceutical systems.\n"
            "ALCOA+ data integrity requires original output preservation.\n"
            "Security violations must be handled through explicit scan failure.\n"
            "NO FALLBACKS ALLOWED - Human consultation required."
        )

    def comprehensive_scan(self,
                          output_content: str,
                          context: str = "general",
                          author: str = "system") -> OutputSecurityScanResult:
        """
        Perform comprehensive security scan of LLM output.
        
        This is the primary security checkpoint for all LLM outputs.
        
        Args:
            output_content: LLM output content to scan
            context: Context identifier for audit trail
            author: User identifier for audit trail
            
        Returns:
            OutputSecurityScanResult: Complete scan result with diagnostics
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If scanning engine fails
        """
        scan_id = uuid4()
        start_time = time.time()

        logger.info(f"[{scan_id}] Starting comprehensive output security scan")

        try:
            # Input validation
            if not isinstance(output_content, str):
                raise ValueError(f"output_content must be string, got: {type(output_content)}")

            if not output_content.strip():
                raise ValueError("Empty output content - security scan requires content")

            # PII Detection
            detected_pii, pii_confidence = self.scan_for_pii(output_content, scan_id)

            # Secrets Detection
            detected_secrets, secrets_confidence = self.detect_secrets(output_content, scan_id)

            # Pharmaceutical Compliance Validation
            compliance_issues, compliance_confidence = self.validate_pharmaceutical_compliance(
                output_content, scan_id
            )

            # Combine threat detection
            all_threats = []
            if detected_pii:
                all_threats.extend([f"pii:{item['type']}" for item in detected_pii])
            if detected_secrets:
                all_threats.extend([f"secret:{item['type']}" for item in detected_secrets])
            if compliance_issues:
                all_threats.extend([f"compliance:{issue}" for issue in compliance_issues])

            # Determine overall security status
            max_confidence = max([
                pii_confidence if detected_pii else 0.0,
                secrets_confidence if detected_secrets else 0.0,
                compliance_confidence if compliance_issues else 0.0,
            ])

            # Zero tolerance for PII and secrets in pharmaceutical systems
            is_secure = (len(detected_pii) == 0 and
                        len(detected_secrets) == 0 and
                        len(compliance_issues) == 0)

            # Determine primary threat category and level
            if detected_pii or detected_secrets:
                primary_category = OWASPCategory.LLM06_SENSITIVE_INFORMATION_DISCLOSURE
                threat_level = SecurityThreatLevel.CRITICAL if (detected_pii or detected_secrets) else SecurityThreatLevel.LOW
            elif compliance_issues:
                primary_category = OWASPCategory.LLM02_INSECURE_OUTPUT_HANDLING
                threat_level = SecurityThreatLevel.HIGH
            else:
                primary_category = OWASPCategory.LLM06_SENSITIVE_INFORMATION_DISCLOSURE
                threat_level = SecurityThreatLevel.LOW

            processing_time = int((time.time() - start_time) * 1000)

            result = OutputSecurityScanResult(
                is_secure=is_secure,
                threat_level=threat_level,
                owasp_category=primary_category,
                confidence_score=max_confidence,
                detected_threats=all_threats,
                pii_detected=detected_pii,
                secrets_detected=detected_secrets,
                compliance_issues=compliance_issues,
                scan_details={
                    "context": context,
                    "author": author,
                    "output_length": len(output_content),
                    "pii_types_detected": len(set(item["type"] for item in detected_pii)),
                    "secret_types_detected": len(set(item["type"] for item in detected_secrets)),
                    "compliance_violations": len(compliance_issues),
                },
                processing_time_ms=processing_time,
                scan_id=scan_id,
                timestamp=datetime.now(UTC),
                error_message=None if is_secure else f"Security scan failed: {len(all_threats)} threats detected"
            )

            logger.info(
                f"[{scan_id}] Output security scan complete: "
                f"secure={is_secure}, threats={len(all_threats)}, "
                f"confidence={max_confidence:.3f}"
            )

            return result

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"[{scan_id}] Output security scan failed: {e}")

            # Return explicit failure result (NO FALLBACKS)
            return OutputSecurityScanResult(
                is_secure=False,
                threat_level=SecurityThreatLevel.CRITICAL,
                owasp_category=OWASPCategory.LLM06_SENSITIVE_INFORMATION_DISCLOSURE,
                confidence_score=0.0,  # Genuine uncertainty due to scan failure
                detected_threats=["scan_engine_failure"],
                pii_detected=[],
                secrets_detected=[],
                compliance_issues=[],
                scan_details={
                    "error": str(e),
                    "context": context,
                    "author": author,
                },
                processing_time_ms=processing_time,
                scan_id=scan_id,
                timestamp=datetime.now(UTC),
                error_message=f"Output security scan engine failure: {e}"
            )
