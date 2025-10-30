"""
21 CFR Part 11 Verification System

This module provides comprehensive 21 CFR Part 11 compliance verification
for electronic records and signatures, audit trails, access controls,
and data integrity requirements.

Key Features:
- Electronic records and signatures validation
- Audit trail completeness verification (100% target)
- Access control and authentication testing
- Data integrity controls validation
- Integration with structured logging from cross-validation
- NO FALLBACKS - explicit verification failures with diagnostics
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

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


class CFRPart11VerificationError(Exception):
    """Exception raised when CFR Part 11 verification fails."""


class AuditTrailVerificationError(Exception):
    """Exception raised when audit trail verification fails."""


class ElectronicSignatureError(Exception):
    """Exception raised when electronic signature verification fails."""


class CFRPart11Verifier:
    """
    21 CFR Part 11 compliance verifier for pharmaceutical systems.
    
    This class provides comprehensive verification of electronic records
    and signatures compliance including audit trails, access controls,
    and data integrity requirements.
    
    NO FALLBACKS: All verification failures surface explicitly with
    complete diagnostic information for regulatory compliance.
    """

    def __init__(
        self,
        evidence_collector: EvidenceCollector,
        structured_logger: StructuredLogger | None = None
    ):
        """
        Initialize the CFR Part 11 verifier.
        
        Args:
            evidence_collector: Evidence collector for gathering compliance evidence
            structured_logger: Optional structured logger for audit trail analysis
        """
        self.logger = logging.getLogger(__name__)
        self.evidence_collector = evidence_collector
        self.structured_logger = structured_logger

        # Verification state
        self.current_verification: dict[str, Any] = {}
        self.identified_gaps: list[Gap] = []

        # CFR Part 11 requirements
        self.audit_trail_requirements = self._define_audit_trail_requirements()
        self.electronic_signature_requirements = self._define_electronic_signature_requirements()
        self.access_control_requirements = self._define_access_control_requirements()
        self.data_integrity_requirements = self._define_data_integrity_requirements()

        self.logger.info("CFRPart11Verifier initialized")

    def verify_audit_trail_completeness(
        self,
        system_name: str,
        audit_data: dict[str, Any],
        target_completeness: float = 1.0,
        verifier_name: str = "cfr_part11_verifier"
    ) -> dict[str, Any]:
        """
        Verify audit trail completeness against 21 CFR Part 11 requirements.
        
        Args:
            system_name: Name of system being verified
            audit_data: Audit trail data for analysis
            target_completeness: Target completeness (default 100% = 1.0)
            verifier_name: Name of verifier performing assessment
            
        Returns:
            Audit trail verification results
            
        Raises:
            AuditTrailVerificationError: If audit trail verification fails
        """
        try:
            verification_id = str(uuid4())
            verification_timestamp = datetime.now(UTC).isoformat()

            self.logger.info(f"Verifying audit trail completeness for {system_name}")

            # Verify audit trail configuration
            config_verification = self._verify_audit_trail_configuration(audit_data)

            # Analyze audit trail coverage
            coverage_analysis = self._analyze_audit_trail_coverage(audit_data)

            # Validate audit trail integrity
            integrity_verification = self._verify_audit_trail_integrity(audit_data)

            # Check event completeness
            event_completeness = self._verify_audit_event_completeness(audit_data)

            # Calculate overall completeness score
            completeness_score = self._calculate_audit_completeness_score(
                config_verification, coverage_analysis, integrity_verification, event_completeness
            )

            # Determine compliance status
            compliance_status = self._determine_audit_trail_compliance(
                completeness_score, target_completeness
            )

            verification_result = {
                "verification_id": verification_id,
                "system_name": system_name,
                "verification_timestamp": verification_timestamp,
                "target_completeness": target_completeness,
                "actual_completeness": completeness_score,
                "compliance_status": compliance_status.value,
                "configuration_verification": config_verification,
                "coverage_analysis": coverage_analysis,
                "integrity_verification": integrity_verification,
                "event_completeness": event_completeness,
                "requirements_met": completeness_score >= target_completeness
            }

            # Identify gaps if non-compliant
            if compliance_status != ComplianceStatus.COMPLIANT:
                gaps = self._identify_audit_trail_gaps(
                    system_name, verification_result, target_completeness
                )
                verification_result["gaps_identified"] = [gap.gap_id for gap in gaps]
                self.identified_gaps.extend(gaps)

            # Collect verification evidence
            evidence = self._collect_audit_trail_evidence(
                system_name, verification_result, verifier_name
            )
            verification_result["evidence_id"] = evidence.evidence_id

            # Store verification
            self.current_verification["audit_trail"] = verification_result

            self.logger.info(f"Audit trail verification completed: {completeness_score:.3f} completeness")
            return verification_result

        except Exception as e:
            error_msg = f"Audit trail verification failed for {system_name}: {e!s}"
            self.logger.error(error_msg)
            raise AuditTrailVerificationError(error_msg) from e

    def verify_electronic_signatures(
        self,
        system_name: str,
        signature_data: dict[str, Any],
        verifier_name: str = "cfr_part11_verifier"
    ) -> dict[str, Any]:
        """
        Verify electronic signature compliance with 21 CFR Part 11.
        
        Args:
            system_name: Name of system being verified
            signature_data: Electronic signature implementation data
            verifier_name: Name of verifier performing assessment
            
        Returns:
            Electronic signature verification results
            
        Raises:
            ElectronicSignatureError: If electronic signature verification fails
        """
        try:
            verification_id = str(uuid4())
            verification_timestamp = datetime.now(UTC).isoformat()

            self.logger.info(f"Verifying electronic signatures for {system_name}")

            # Verify signature components
            component_verification = self._verify_signature_components(signature_data)

            # Validate signature implementation
            implementation_validation = self._validate_signature_implementation(signature_data)

            # Check signature manifestation
            manifestation_check = self._verify_signature_manifestation(signature_data)

            # Validate signature linking
            linking_validation = self._verify_signature_linking(signature_data)

            # Calculate compliance score
            compliance_score = self._calculate_signature_compliance_score(
                component_verification, implementation_validation,
                manifestation_check, linking_validation
            )

            # Determine compliance status
            compliance_status = self._determine_signature_compliance(compliance_score)

            verification_result = {
                "verification_id": verification_id,
                "system_name": system_name,
                "verification_timestamp": verification_timestamp,
                "compliance_score": compliance_score,
                "compliance_status": compliance_status.value,
                "component_verification": component_verification,
                "implementation_validation": implementation_validation,
                "manifestation_check": manifestation_check,
                "linking_validation": linking_validation,
                "meets_cfr_requirements": compliance_score >= 0.9
            }

            # Identify gaps if non-compliant
            if compliance_status != ComplianceStatus.COMPLIANT:
                gaps = self._identify_signature_gaps(
                    system_name, verification_result
                )
                verification_result["gaps_identified"] = [gap.gap_id for gap in gaps]
                self.identified_gaps.extend(gaps)

            # Collect verification evidence
            evidence = self._collect_signature_evidence(
                system_name, verification_result, verifier_name
            )
            verification_result["evidence_id"] = evidence.evidence_id

            # Store verification
            self.current_verification["electronic_signatures"] = verification_result

            self.logger.info(f"Electronic signature verification completed: {compliance_score:.3f} score")
            return verification_result

        except Exception as e:
            error_msg = f"Electronic signature verification failed for {system_name}: {e!s}"
            self.logger.error(error_msg)
            raise ElectronicSignatureError(error_msg) from e

    def verify_access_controls(
        self,
        system_name: str,
        access_control_data: dict[str, Any],
        verifier_name: str = "cfr_part11_verifier"
    ) -> dict[str, Any]:
        """
        Verify access control and authentication compliance.
        
        Args:
            system_name: Name of system being verified
            access_control_data: Access control implementation data
            verifier_name: Name of verifier performing assessment
            
        Returns:
            Access control verification results
            
        Raises:
            CFRPart11VerificationError: If access control verification fails
        """
        try:
            verification_id = str(uuid4())
            verification_timestamp = datetime.now(UTC).isoformat()

            self.logger.info(f"Verifying access controls for {system_name}")

            # Verify role-based access control
            rbac_verification = self._verify_role_based_access(access_control_data)

            # Check authentication mechanisms
            auth_verification = self._verify_authentication_mechanisms(access_control_data)

            # Validate session controls
            session_verification = self._verify_session_controls(access_control_data)

            # Check privileged access controls
            privileged_verification = self._verify_privileged_access(access_control_data)

            # Calculate compliance score
            compliance_score = self._calculate_access_control_compliance(
                rbac_verification, auth_verification,
                session_verification, privileged_verification
            )

            # Determine compliance status
            compliance_status = self._determine_access_control_compliance(compliance_score)

            verification_result = {
                "verification_id": verification_id,
                "system_name": system_name,
                "verification_timestamp": verification_timestamp,
                "compliance_score": compliance_score,
                "compliance_status": compliance_status.value,
                "rbac_verification": rbac_verification,
                "authentication_verification": auth_verification,
                "session_verification": session_verification,
                "privileged_verification": privileged_verification,
                "meets_access_requirements": compliance_score >= 0.9
            }

            # Identify gaps if non-compliant
            if compliance_status != ComplianceStatus.COMPLIANT:
                gaps = self._identify_access_control_gaps(
                    system_name, verification_result
                )
                verification_result["gaps_identified"] = [gap.gap_id for gap in gaps]
                self.identified_gaps.extend(gaps)

            # Collect verification evidence
            evidence = self._collect_access_control_evidence(
                system_name, verification_result, verifier_name
            )
            verification_result["evidence_id"] = evidence.evidence_id

            # Store verification
            self.current_verification["access_controls"] = verification_result

            self.logger.info(f"Access control verification completed: {compliance_score:.3f} score")
            return verification_result

        except Exception as e:
            error_msg = f"Access control verification failed for {system_name}: {e!s}"
            self.logger.error(error_msg)
            raise CFRPart11VerificationError(error_msg) from e

    def verify_data_integrity_controls(
        self,
        system_name: str,
        data_integrity_data: dict[str, Any],
        verifier_name: str = "cfr_part11_verifier"
    ) -> dict[str, Any]:
        """
        Verify data integrity controls compliance.
        
        Args:
            system_name: Name of system being verified
            data_integrity_data: Data integrity implementation data
            verifier_name: Name of verifier performing assessment
            
        Returns:
            Data integrity verification results
            
        Raises:
            CFRPart11VerificationError: If data integrity verification fails
        """
        try:
            verification_id = str(uuid4())
            verification_timestamp = datetime.now(UTC).isoformat()

            self.logger.info(f"Verifying data integrity controls for {system_name}")

            # Verify data protection measures
            protection_verification = self._verify_data_protection(data_integrity_data)

            # Check backup and recovery
            backup_verification = self._verify_backup_recovery(data_integrity_data)

            # Validate data transfer integrity
            transfer_verification = self._verify_data_transfer_integrity(data_integrity_data)

            # Check data retention controls
            retention_verification = self._verify_data_retention(data_integrity_data)

            # Calculate compliance score
            compliance_score = self._calculate_data_integrity_compliance(
                protection_verification, backup_verification,
                transfer_verification, retention_verification
            )

            # Determine compliance status
            compliance_status = self._determine_data_integrity_compliance(compliance_score)

            verification_result = {
                "verification_id": verification_id,
                "system_name": system_name,
                "verification_timestamp": verification_timestamp,
                "compliance_score": compliance_score,
                "compliance_status": compliance_status.value,
                "protection_verification": protection_verification,
                "backup_verification": backup_verification,
                "transfer_verification": transfer_verification,
                "retention_verification": retention_verification,
                "meets_integrity_requirements": compliance_score >= 0.9
            }

            # Identify gaps if non-compliant
            if compliance_status != ComplianceStatus.COMPLIANT:
                gaps = self._identify_data_integrity_gaps(
                    system_name, verification_result
                )
                verification_result["gaps_identified"] = [gap.gap_id for gap in gaps]
                self.identified_gaps.extend(gaps)

            # Collect verification evidence
            evidence = self._collect_data_integrity_evidence(
                system_name, verification_result, verifier_name
            )
            verification_result["evidence_id"] = evidence.evidence_id

            # Store verification
            self.current_verification["data_integrity"] = verification_result

            self.logger.info(f"Data integrity verification completed: {compliance_score:.3f} score")
            return verification_result

        except Exception as e:
            error_msg = f"Data integrity verification failed for {system_name}: {e!s}"
            self.logger.error(error_msg)
            raise CFRPart11VerificationError(error_msg) from e

    def generate_cfr_part11_report(
        self,
        system_name: str,
        verifier_name: str = "cfr_part11_verifier"
    ) -> ComplianceResult:
        """
        Generate comprehensive 21 CFR Part 11 compliance report.
        
        Args:
            system_name: Name of system being verified
            verifier_name: Name of verifier generating report
            
        Returns:
            Comprehensive CFR Part 11 compliance result
            
        Raises:
            CFRPart11VerificationError: If report generation fails
        """
        try:
            if not self.current_verification:
                raise CFRPart11VerificationError("No verifications performed. Run verifications before generating report.")

            # Aggregate verification results
            framework_results = {
                "cfr_part_11": {
                    "audit_trail": self.current_verification.get("audit_trail", {}),
                    "electronic_signatures": self.current_verification.get("electronic_signatures", {}),
                    "access_controls": self.current_verification.get("access_controls", {}),
                    "data_integrity": self.current_verification.get("data_integrity", {})
                }
            }

            # Calculate overall compliance
            overall_status, overall_score = self._calculate_overall_cfr_compliance(framework_results)

            # Create compliance result
            compliance_result = ComplianceResult(
                assessment_name=f"21 CFR Part 11 Compliance Verification - {system_name}",
                system_under_assessment=system_name,
                frameworks_assessed=[ComplianceFramework.CFR_PART_11],
                assessment_scope="21 CFR Part 11 electronic records, signatures, audit trails, access controls, and data integrity",
                framework_results=framework_results,
                overall_status=overall_status,
                overall_score=overall_score,
                total_gaps_identified=len(self.identified_gaps),
                critical_gaps=len([g for g in self.identified_gaps if g.severity == GapSeverity.CRITICAL]),
                high_priority_gaps=len([g for g in self.identified_gaps if g.severity == GapSeverity.HIGH]),
                assessment_team=[verifier_name],
                assessment_start_date=datetime.now(UTC).isoformat(),
                gap_ids=[gap.gap_id for gap in self.identified_gaps]
            )

            # Add framework-specific results
            compliance_result.add_framework_result(ComplianceFramework.CFR_PART_11, {
                "status": overall_status,
                "score": overall_score,
                "audit_trail_compliant": self.current_verification.get("audit_trail", {}).get("compliance_status") == "compliant",
                "signatures_compliant": self.current_verification.get("electronic_signatures", {}).get("compliance_status") == "compliant",
                "access_controls_compliant": self.current_verification.get("access_controls", {}).get("compliance_status") == "compliant",
                "data_integrity_compliant": self.current_verification.get("data_integrity", {}).get("compliance_status") == "compliant"
            })

            self.logger.info(f"CFR Part 11 compliance report generated: {overall_status.value}")
            return compliance_result

        except Exception as e:
            error_msg = f"CFR Part 11 compliance report generation failed: {e!s}"
            self.logger.error(error_msg)
            raise CFRPart11VerificationError(error_msg) from e

    def _define_audit_trail_requirements(self) -> dict[str, Any]:
        """Define 21 CFR Part 11 audit trail requirements."""
        return {
            "required_events": [
                "user_login",
                "user_logout",
                "record_creation",
                "record_modification",
                "record_deletion",
                "configuration_changes",
                "security_events",
                "system_access_attempts"
            ],
            "required_attributes": [
                "timestamp",
                "user_identity",
                "action_performed",
                "record_identifier",
                "old_values",
                "new_values",
                "reason_for_change"
            ],
            "integrity_requirements": [
                "tamper_evidence",
                "time_synchronization",
                "secure_storage",
                "retention_period",
                "export_capability"
            ]
        }

    def _define_electronic_signature_requirements(self) -> dict[str, Any]:
        """Define 21 CFR Part 11 electronic signature requirements."""
        return {
            "signature_components": [
                "unique_user_identification",
                "authentication_method",
                "signature_timestamp",
                "signature_meaning",
                "record_linkage"
            ],
            "authentication_methods": [
                "username_password",
                "biometric",
                "digital_certificate",
                "multi_factor_authentication"
            ],
            "manifestation_requirements": [
                "printed_form_display",
                "electronic_display",
                "signature_details",
                "signer_identification",
                "signature_date_time"
            ]
        }

    def _define_access_control_requirements(self) -> dict[str, Any]:
        """Define 21 CFR Part 11 access control requirements."""
        return {
            "authentication": [
                "unique_user_identification",
                "password_complexity",
                "account_lockout",
                "session_timeout",
                "multi_factor_authentication"
            ],
            "authorization": [
                "role_based_access",
                "least_privilege",
                "privilege_escalation_controls",
                "periodic_access_review"
            ],
            "monitoring": [
                "access_attempt_logging",
                "privileged_action_logging",
                "anomaly_detection",
                "real_time_alerts"
            ]
        }

    def _define_data_integrity_requirements(self) -> dict[str, Any]:
        """Define 21 CFR Part 11 data integrity requirements."""
        return {
            "protection_measures": [
                "data_encryption",
                "access_controls",
                "version_control",
                "change_tracking"
            ],
            "backup_recovery": [
                "regular_backups",
                "backup_integrity_checks",
                "recovery_procedures",
                "recovery_testing"
            ],
            "transfer_integrity": [
                "secure_protocols",
                "checksums_hashes",
                "transmission_logs",
                "error_detection"
            ],
            "retention": [
                "retention_periods",
                "archival_procedures",
                "retrieval_capabilities",
                "disposal_procedures"
            ]
        }

    def _verify_audit_trail_configuration(self, audit_data: dict[str, Any]) -> dict[str, Any]:
        """Verify audit trail configuration against requirements."""
        config = audit_data.get("configuration", {})

        verification_result = {
            "events_configured": 0,
            "attributes_configured": 0,
            "integrity_controls": 0,
            "configuration_score": 0.0
        }

        # Check event coverage
        configured_events = config.get("monitored_events", [])
        required_events = self.audit_trail_requirements["required_events"]

        events_covered = len([e for e in required_events if e in configured_events])
        verification_result["events_configured"] = events_covered

        # Check attribute coverage
        configured_attributes = config.get("captured_attributes", [])
        required_attributes = self.audit_trail_requirements["required_attributes"]

        attributes_covered = len([a for a in required_attributes if a in configured_attributes])
        verification_result["attributes_configured"] = attributes_covered

        # Check integrity controls
        configured_controls = config.get("integrity_controls", [])
        required_controls = self.audit_trail_requirements["integrity_requirements"]

        controls_implemented = len([c for c in required_controls if c in configured_controls])
        verification_result["integrity_controls"] = controls_implemented

        # Calculate overall configuration score
        total_requirements = len(required_events) + len(required_attributes) + len(required_controls)
        total_configured = events_covered + attributes_covered + controls_implemented

        verification_result["configuration_score"] = total_configured / total_requirements if total_requirements > 0 else 0.0

        return verification_result

    def _analyze_audit_trail_coverage(self, audit_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze actual audit trail coverage from logs."""
        logs = audit_data.get("audit_logs", [])

        coverage_analysis = {
            "total_log_entries": len(logs),
            "event_type_coverage": {},
            "time_period_coverage": {},
            "user_coverage": {},
            "coverage_completeness": 0.0
        }

        if not logs:
            return coverage_analysis

        # Analyze event type coverage
        event_types = [log.get("event_type") for log in logs]
        required_events = self.audit_trail_requirements["required_events"]

        for event_type in required_events:
            count = event_types.count(event_type)
            coverage_analysis["event_type_coverage"][event_type] = count

        # Calculate coverage completeness
        covered_events = len([e for e in required_events if coverage_analysis["event_type_coverage"].get(e, 0) > 0])
        coverage_analysis["coverage_completeness"] = covered_events / len(required_events)

        return coverage_analysis

    def _verify_audit_trail_integrity(self, audit_data: dict[str, Any]) -> dict[str, Any]:
        """Verify audit trail integrity controls."""
        integrity_data = audit_data.get("integrity_verification", {})

        integrity_result = {
            "tamper_evidence": integrity_data.get("tamper_evidence", False),
            "time_synchronization": integrity_data.get("time_sync", False),
            "secure_storage": integrity_data.get("encrypted_storage", False),
            "retention_compliance": integrity_data.get("retention_period", 0) >= 2555,  # 7 years in days
            "export_capability": integrity_data.get("export_available", False),
            "integrity_score": 0.0
        }

        # Calculate integrity score
        integrity_checks = [
            integrity_result["tamper_evidence"],
            integrity_result["time_synchronization"],
            integrity_result["secure_storage"],
            integrity_result["retention_compliance"],
            integrity_result["export_capability"]
        ]

        integrity_result["integrity_score"] = sum(integrity_checks) / len(integrity_checks)

        return integrity_result

    def _verify_audit_event_completeness(self, audit_data: dict[str, Any]) -> dict[str, Any]:
        """Verify completeness of individual audit events."""
        logs = audit_data.get("audit_logs", [])
        required_attributes = self.audit_trail_requirements["required_attributes"]

        completeness_result = {
            "total_events": len(logs),
            "complete_events": 0,
            "incomplete_events": 0,
            "missing_attribute_analysis": {},
            "completeness_percentage": 0.0
        }

        if not logs:
            return completeness_result

        # Analyze each log entry
        for log_entry in logs:
            missing_attributes = []
            for attribute in required_attributes:
                if attribute not in log_entry or log_entry[attribute] is None:
                    missing_attributes.append(attribute)

            if not missing_attributes:
                completeness_result["complete_events"] += 1
            else:
                completeness_result["incomplete_events"] += 1
                for attr in missing_attributes:
                    completeness_result["missing_attribute_analysis"][attr] = \
                        completeness_result["missing_attribute_analysis"].get(attr, 0) + 1

        # Calculate completeness percentage
        total_events = completeness_result["total_events"]
        complete_events = completeness_result["complete_events"]

        completeness_result["completeness_percentage"] = \
            (complete_events / total_events * 100) if total_events > 0 else 0.0

        return completeness_result

    def _calculate_audit_completeness_score(
        self, config_verification: dict, coverage_analysis: dict,
        integrity_verification: dict, event_completeness: dict
    ) -> float:
        """Calculate overall audit trail completeness score."""
        config_score = config_verification.get("configuration_score", 0.0)
        coverage_score = coverage_analysis.get("coverage_completeness", 0.0)
        integrity_score = integrity_verification.get("integrity_score", 0.0)
        completeness_score = event_completeness.get("completeness_percentage", 0.0) / 100.0

        # Weighted average: configuration 20%, coverage 30%, integrity 25%, completeness 25%
        overall_score = (config_score * 0.2) + (coverage_score * 0.3) + \
                       (integrity_score * 0.25) + (completeness_score * 0.25)

        return overall_score

    def _determine_audit_trail_compliance(
        self, completeness_score: float, target_completeness: float
    ) -> ComplianceStatus:
        """Determine audit trail compliance status."""
        if completeness_score >= target_completeness:
            return ComplianceStatus.COMPLIANT
        if completeness_score >= (target_completeness * 0.8):
            return ComplianceStatus.PARTIALLY_COMPLIANT
        return ComplianceStatus.NON_COMPLIANT

    def _verify_signature_components(self, signature_data: dict[str, Any]) -> dict[str, Any]:
        """Verify electronic signature components."""
        components = signature_data.get("signature_components", {})
        required_components = self.electronic_signature_requirements["signature_components"]

        verification_result = {
            "components_implemented": 0,
            "component_details": {},
            "component_score": 0.0
        }

        for component in required_components:
            implemented = component in components and components[component] is not None
            verification_result["component_details"][component] = {
                "implemented": implemented,
                "details": components.get(component, "Not implemented")
            }
            if implemented:
                verification_result["components_implemented"] += 1

        verification_result["component_score"] = \
            verification_result["components_implemented"] / len(required_components)

        return verification_result

    def _validate_signature_implementation(self, signature_data: dict[str, Any]) -> dict[str, Any]:
        """Validate electronic signature implementation."""
        implementation = signature_data.get("implementation", {})

        validation_result = {
            "authentication_method": implementation.get("authentication_method", "unknown"),
            "authentication_valid": False,
            "unique_identification": implementation.get("unique_identification", False),
            "non_repudiation": implementation.get("non_repudiation", False),
            "implementation_score": 0.0
        }

        # Validate authentication method
        valid_methods = self.electronic_signature_requirements["authentication_methods"]
        validation_result["authentication_valid"] = \
            validation_result["authentication_method"] in valid_methods

        # Calculate implementation score
        implementation_checks = [
            validation_result["authentication_valid"],
            validation_result["unique_identification"],
            validation_result["non_repudiation"]
        ]

        validation_result["implementation_score"] = sum(implementation_checks) / len(implementation_checks)

        return validation_result

    def _verify_signature_manifestation(self, signature_data: dict[str, Any]) -> dict[str, Any]:
        """Verify signature manifestation requirements."""
        manifestation = signature_data.get("manifestation", {})
        required_manifestation = self.electronic_signature_requirements["manifestation_requirements"]

        manifestation_result = {
            "manifestation_elements": 0,
            "manifestation_details": {},
            "manifestation_score": 0.0
        }

        for element in required_manifestation:
            present = element in manifestation and manifestation[element]
            manifestation_result["manifestation_details"][element] = {
                "present": present,
                "implementation": manifestation.get(element, "Not implemented")
            }
            if present:
                manifestation_result["manifestation_elements"] += 1

        manifestation_result["manifestation_score"] = \
            manifestation_result["manifestation_elements"] / len(required_manifestation)

        return manifestation_result

    def _verify_signature_linking(self, signature_data: dict[str, Any]) -> dict[str, Any]:
        """Verify signature linking to records."""
        linking_data = signature_data.get("record_linking", {})

        linking_result = {
            "cryptographic_linking": linking_data.get("cryptographic_linking", False),
            "tamper_evidence": linking_data.get("tamper_evidence", False),
            "signature_preservation": linking_data.get("signature_preservation", False),
            "linking_score": 0.0
        }

        # Calculate linking score
        linking_checks = [
            linking_result["cryptographic_linking"],
            linking_result["tamper_evidence"],
            linking_result["signature_preservation"]
        ]

        linking_result["linking_score"] = sum(linking_checks) / len(linking_checks)

        return linking_result

    def _calculate_signature_compliance_score(
        self, component_verification: dict, implementation_validation: dict,
        manifestation_check: dict, linking_validation: dict
    ) -> float:
        """Calculate overall electronic signature compliance score."""
        component_score = component_verification.get("component_score", 0.0)
        implementation_score = implementation_validation.get("implementation_score", 0.0)
        manifestation_score = manifestation_check.get("manifestation_score", 0.0)
        linking_score = linking_validation.get("linking_score", 0.0)

        # Equal weighting for all signature aspects
        return (component_score + implementation_score + manifestation_score + linking_score) / 4.0

    def _determine_signature_compliance(self, compliance_score: float) -> ComplianceStatus:
        """Determine electronic signature compliance status."""
        if compliance_score >= 0.95:
            return ComplianceStatus.COMPLIANT
        if compliance_score >= 0.8:
            return ComplianceStatus.PARTIALLY_COMPLIANT
        return ComplianceStatus.NON_COMPLIANT

    def _verify_role_based_access(self, access_data: dict[str, Any]) -> dict[str, Any]:
        """Verify role-based access control implementation."""
        rbac_data = access_data.get("role_based_access", {})

        rbac_result = {
            "roles_defined": len(rbac_data.get("defined_roles", [])),
            "permissions_mapped": rbac_data.get("permissions_mapped", False),
            "least_privilege": rbac_data.get("least_privilege_implemented", False),
            "role_separation": rbac_data.get("role_separation", False),
            "rbac_score": 0.0
        }

        # Calculate RBAC score
        rbac_checks = [
            rbac_result["roles_defined"] > 0,
            rbac_result["permissions_mapped"],
            rbac_result["least_privilege"],
            rbac_result["role_separation"]
        ]

        rbac_result["rbac_score"] = sum(rbac_checks) / len(rbac_checks)

        return rbac_result

    def _verify_authentication_mechanisms(self, access_data: dict[str, Any]) -> dict[str, Any]:
        """Verify authentication mechanisms."""
        auth_data = access_data.get("authentication", {})

        auth_result = {
            "password_complexity": auth_data.get("password_complexity", False),
            "account_lockout": auth_data.get("account_lockout", False),
            "session_timeout": auth_data.get("session_timeout", False),
            "multi_factor_auth": auth_data.get("multi_factor_authentication", False),
            "authentication_score": 0.0
        }

        # Calculate authentication score
        auth_checks = [
            auth_result["password_complexity"],
            auth_result["account_lockout"],
            auth_result["session_timeout"],
            auth_result["multi_factor_auth"]
        ]

        auth_result["authentication_score"] = sum(auth_checks) / len(auth_checks)

        return auth_result

    def _verify_session_controls(self, access_data: dict[str, Any]) -> dict[str, Any]:
        """Verify session control implementation."""
        session_data = access_data.get("session_controls", {})

        session_result = {
            "session_timeout": session_data.get("timeout_configured", False),
            "concurrent_sessions": session_data.get("concurrent_session_limits", False),
            "session_monitoring": session_data.get("session_monitoring", False),
            "secure_logout": session_data.get("secure_logout", False),
            "session_score": 0.0
        }

        # Calculate session control score
        session_checks = [
            session_result["session_timeout"],
            session_result["concurrent_sessions"],
            session_result["session_monitoring"],
            session_result["secure_logout"]
        ]

        session_result["session_score"] = sum(session_checks) / len(session_checks)

        return session_result

    def _verify_privileged_access(self, access_data: dict[str, Any]) -> dict[str, Any]:
        """Verify privileged access controls."""
        privileged_data = access_data.get("privileged_access", {})

        privileged_result = {
            "privileged_users_identified": len(privileged_data.get("privileged_users", [])),
            "additional_authentication": privileged_data.get("additional_authentication", False),
            "privileged_monitoring": privileged_data.get("enhanced_monitoring", False),
            "access_review": privileged_data.get("periodic_review", False),
            "privileged_score": 0.0
        }

        # Calculate privileged access score
        privileged_checks = [
            privileged_result["privileged_users_identified"] > 0,
            privileged_result["additional_authentication"],
            privileged_result["privileged_monitoring"],
            privileged_result["access_review"]
        ]

        privileged_result["privileged_score"] = sum(privileged_checks) / len(privileged_checks)

        return privileged_result

    def _calculate_access_control_compliance(
        self, rbac_verification: dict, auth_verification: dict,
        session_verification: dict, privileged_verification: dict
    ) -> float:
        """Calculate overall access control compliance score."""
        rbac_score = rbac_verification.get("rbac_score", 0.0)
        auth_score = auth_verification.get("authentication_score", 0.0)
        session_score = session_verification.get("session_score", 0.0)
        privileged_score = privileged_verification.get("privileged_score", 0.0)

        # Equal weighting for all access control aspects
        return (rbac_score + auth_score + session_score + privileged_score) / 4.0

    def _determine_access_control_compliance(self, compliance_score: float) -> ComplianceStatus:
        """Determine access control compliance status."""
        if compliance_score >= 0.9:
            return ComplianceStatus.COMPLIANT
        if compliance_score >= 0.75:
            return ComplianceStatus.PARTIALLY_COMPLIANT
        return ComplianceStatus.NON_COMPLIANT

    def _verify_data_protection(self, data_integrity_data: dict[str, Any]) -> dict[str, Any]:
        """Verify data protection measures."""
        protection_data = data_integrity_data.get("protection_measures", {})

        protection_result = {
            "data_encryption": protection_data.get("encryption_at_rest", False),
            "transmission_encryption": protection_data.get("encryption_in_transit", False),
            "access_controls": protection_data.get("data_access_controls", False),
            "version_control": protection_data.get("version_control", False),
            "change_tracking": protection_data.get("change_tracking", False),
            "protection_score": 0.0
        }

        # Calculate protection score
        protection_checks = [
            protection_result["data_encryption"],
            protection_result["transmission_encryption"],
            protection_result["access_controls"],
            protection_result["version_control"],
            protection_result["change_tracking"]
        ]

        protection_result["protection_score"] = sum(protection_checks) / len(protection_checks)

        return protection_result

    def _verify_backup_recovery(self, data_integrity_data: dict[str, Any]) -> dict[str, Any]:
        """Verify backup and recovery capabilities."""
        backup_data = data_integrity_data.get("backup_recovery", {})

        backup_result = {
            "regular_backups": backup_data.get("scheduled_backups", False),
            "backup_integrity": backup_data.get("integrity_checks", False),
            "recovery_procedures": backup_data.get("recovery_procedures_documented", False),
            "recovery_testing": backup_data.get("recovery_testing", False),
            "offsite_storage": backup_data.get("offsite_storage", False),
            "backup_score": 0.0
        }

        # Calculate backup score
        backup_checks = [
            backup_result["regular_backups"],
            backup_result["backup_integrity"],
            backup_result["recovery_procedures"],
            backup_result["recovery_testing"],
            backup_result["offsite_storage"]
        ]

        backup_result["backup_score"] = sum(backup_checks) / len(backup_checks)

        return backup_result

    def _verify_data_transfer_integrity(self, data_integrity_data: dict[str, Any]) -> dict[str, Any]:
        """Verify data transfer integrity controls."""
        transfer_data = data_integrity_data.get("data_transfer", {})

        transfer_result = {
            "secure_protocols": transfer_data.get("secure_protocols", False),
            "checksums_hashes": transfer_data.get("integrity_verification", False),
            "transmission_logs": transfer_data.get("transfer_logging", False),
            "error_detection": transfer_data.get("error_detection", False),
            "transfer_score": 0.0
        }

        # Calculate transfer integrity score
        transfer_checks = [
            transfer_result["secure_protocols"],
            transfer_result["checksums_hashes"],
            transfer_result["transmission_logs"],
            transfer_result["error_detection"]
        ]

        transfer_result["transfer_score"] = sum(transfer_checks) / len(transfer_checks)

        return transfer_result

    def _verify_data_retention(self, data_integrity_data: dict[str, Any]) -> dict[str, Any]:
        """Verify data retention controls."""
        retention_data = data_integrity_data.get("data_retention", {})

        retention_result = {
            "retention_periods_defined": retention_data.get("retention_policy", False),
            "archival_procedures": retention_data.get("archival_process", False),
            "retrieval_capabilities": retention_data.get("data_retrieval", False),
            "disposal_procedures": retention_data.get("secure_disposal", False),
            "retention_score": 0.0
        }

        # Calculate retention score
        retention_checks = [
            retention_result["retention_periods_defined"],
            retention_result["archival_procedures"],
            retention_result["retrieval_capabilities"],
            retention_result["disposal_procedures"]
        ]

        retention_result["retention_score"] = sum(retention_checks) / len(retention_checks)

        return retention_result

    def _calculate_data_integrity_compliance(
        self, protection_verification: dict, backup_verification: dict,
        transfer_verification: dict, retention_verification: dict
    ) -> float:
        """Calculate overall data integrity compliance score."""
        protection_score = protection_verification.get("protection_score", 0.0)
        backup_score = backup_verification.get("backup_score", 0.0)
        transfer_score = transfer_verification.get("transfer_score", 0.0)
        retention_score = retention_verification.get("retention_score", 0.0)

        # Equal weighting for all data integrity aspects
        return (protection_score + backup_score + transfer_score + retention_score) / 4.0

    def _determine_data_integrity_compliance(self, compliance_score: float) -> ComplianceStatus:
        """Determine data integrity compliance status."""
        if compliance_score >= 0.9:
            return ComplianceStatus.COMPLIANT
        if compliance_score >= 0.75:
            return ComplianceStatus.PARTIALLY_COMPLIANT
        return ComplianceStatus.NON_COMPLIANT

    def _identify_audit_trail_gaps(
        self, system_name: str, verification_result: dict[str, Any], target_completeness: float
    ) -> list[Gap]:
        """Identify audit trail compliance gaps."""
        gaps = []

        actual_completeness = verification_result.get("actual_completeness", 0.0)
        if actual_completeness < target_completeness:
            gap = Gap(
                title="Audit Trail Completeness Below Target",
                description=f"Audit trail completeness {actual_completeness:.3f} below target {target_completeness:.3f}",
                framework=ComplianceFramework.CFR_PART_11,
                requirement_reference="21 CFR Part 11.10(e) - Audit Trail Requirements",
                severity=GapSeverity.HIGH,
                risk_to_patient="Medium - audit trail gaps affect traceability",
                risk_to_product="High - incomplete audit trail affects accountability",
                risk_to_data="High - data integrity monitoring compromised",
                compliance_exposure="Critical - regulatory requirement for complete audit trails",
                root_cause="Incomplete audit trail configuration or monitoring",
                current_state_description=f"Completeness: {actual_completeness:.3f}",
                required_state_description=f"Target completeness: {target_completeness:.3f}",
                identified_by="cfr_part11_verifier",
                identification_method="audit_trail_completeness_analysis"
            )
            gaps.append(gap)

        return gaps

    def _identify_signature_gaps(
        self, system_name: str, verification_result: dict[str, Any]
    ) -> list[Gap]:
        """Identify electronic signature compliance gaps."""
        gaps = []

        compliance_score = verification_result.get("compliance_score", 0.0)
        if compliance_score < 0.9:
            gap = Gap(
                title="Electronic Signature Non-Compliance",
                description=f"Electronic signature compliance score {compliance_score:.3f} below required threshold",
                framework=ComplianceFramework.CFR_PART_11,
                requirement_reference="21 CFR Part 11.50 - Electronic Signature Requirements",
                severity=GapSeverity.CRITICAL,
                risk_to_patient="High - invalid signatures affect record authenticity",
                risk_to_product="Critical - product release decisions may lack proper authorization",
                risk_to_data="High - data authenticity and non-repudiation compromised",
                compliance_exposure="Critical - regulatory requirement for valid electronic signatures",
                root_cause="Electronic signature implementation deficiencies",
                current_state_description=f"Compliance score: {compliance_score:.3f}",
                required_state_description="Compliance score ≥ 0.9",
                identified_by="cfr_part11_verifier",
                identification_method="electronic_signature_compliance_analysis"
            )
            gaps.append(gap)

        return gaps

    def _identify_access_control_gaps(
        self, system_name: str, verification_result: dict[str, Any]
    ) -> list[Gap]:
        """Identify access control compliance gaps."""
        gaps = []

        compliance_score = verification_result.get("compliance_score", 0.0)
        if compliance_score < 0.9:
            gap = Gap(
                title="Access Control Deficiencies",
                description=f"Access control compliance score {compliance_score:.3f} below required threshold",
                framework=ComplianceFramework.CFR_PART_11,
                requirement_reference="21 CFR Part 11.10(d) - Access Control Requirements",
                severity=GapSeverity.HIGH,
                risk_to_patient="Medium - unauthorized access affects data reliability",
                risk_to_product="High - inadequate controls affect product integrity",
                risk_to_data="High - data access controls compromised",
                compliance_exposure="High - regulatory requirement for access controls",
                root_cause="Incomplete access control implementation",
                current_state_description=f"Compliance score: {compliance_score:.3f}",
                required_state_description="Compliance score ≥ 0.9",
                identified_by="cfr_part11_verifier",
                identification_method="access_control_compliance_analysis"
            )
            gaps.append(gap)

        return gaps

    def _identify_data_integrity_gaps(
        self, system_name: str, verification_result: dict[str, Any]
    ) -> list[Gap]:
        """Identify data integrity compliance gaps."""
        gaps = []

        compliance_score = verification_result.get("compliance_score", 0.0)
        if compliance_score < 0.9:
            gap = Gap(
                title="Data Integrity Control Deficiencies",
                description=f"Data integrity compliance score {compliance_score:.3f} below required threshold",
                framework=ComplianceFramework.CFR_PART_11,
                requirement_reference="21 CFR Part 11.10(a) - Data Integrity Requirements",
                severity=GapSeverity.HIGH,
                risk_to_patient="High - data integrity affects patient safety decisions",
                risk_to_product="High - compromised data affects product quality",
                risk_to_data="Critical - fundamental data integrity compromised",
                compliance_exposure="Critical - core regulatory requirement",
                root_cause="Insufficient data integrity control implementation",
                current_state_description=f"Compliance score: {compliance_score:.3f}",
                required_state_description="Compliance score ≥ 0.9",
                identified_by="cfr_part11_verifier",
                identification_method="data_integrity_compliance_analysis"
            )
            gaps.append(gap)

        return gaps

    def _collect_audit_trail_evidence(
        self, system_name: str, verification_result: dict[str, Any], verifier_name: str
    ) -> Evidence:
        """Collect evidence for audit trail verification."""
        return self.evidence_collector.collect_evidence_from_system(
            system_name=system_name,
            evidence_type=EvidenceType.AUDIT_LOG,
            collection_method="automated_cfr_part11_audit_trail_verification",
            collector_name=verifier_name,
            verification_data=verification_result,
            compliance_framework="21 CFR Part 11"
        )

    def _collect_signature_evidence(
        self, system_name: str, verification_result: dict[str, Any], verifier_name: str
    ) -> Evidence:
        """Collect evidence for electronic signature verification."""
        return self.evidence_collector.collect_evidence_from_system(
            system_name=system_name,
            evidence_type=EvidenceType.CONFIGURATION,
            collection_method="automated_cfr_part11_signature_verification",
            collector_name=verifier_name,
            verification_data=verification_result,
            compliance_framework="21 CFR Part 11"
        )

    def _collect_access_control_evidence(
        self, system_name: str, verification_result: dict[str, Any], verifier_name: str
    ) -> Evidence:
        """Collect evidence for access control verification."""
        return self.evidence_collector.collect_evidence_from_system(
            system_name=system_name,
            evidence_type=EvidenceType.TEST_RESULT,
            collection_method="automated_cfr_part11_access_control_verification",
            collector_name=verifier_name,
            verification_data=verification_result,
            compliance_framework="21 CFR Part 11"
        )

    def _collect_data_integrity_evidence(
        self, system_name: str, verification_result: dict[str, Any], verifier_name: str
    ) -> Evidence:
        """Collect evidence for data integrity verification."""
        return self.evidence_collector.collect_evidence_from_system(
            system_name=system_name,
            evidence_type=EvidenceType.PROCESS_RECORD,
            collection_method="automated_cfr_part11_data_integrity_verification",
            collector_name=verifier_name,
            verification_data=verification_result,
            compliance_framework="21 CFR Part 11"
        )

    def _calculate_overall_cfr_compliance(
        self, framework_results: dict[str, Any]
    ) -> tuple[ComplianceStatus, float]:
        """Calculate overall CFR Part 11 compliance status and score."""
        cfr_results = framework_results.get("cfr_part_11", {})

        # Get individual verification scores
        audit_score = cfr_results.get("audit_trail", {}).get("actual_completeness", 0.0)
        signature_score = cfr_results.get("electronic_signatures", {}).get("compliance_score", 0.0)
        access_score = cfr_results.get("access_controls", {}).get("compliance_score", 0.0)
        integrity_score = cfr_results.get("data_integrity", {}).get("compliance_score", 0.0)

        # Calculate weighted overall score
        # Audit trails and data integrity get higher weight as they're core to CFR Part 11
        overall_score = (audit_score * 0.3) + (signature_score * 0.25) + \
                       (access_score * 0.2) + (integrity_score * 0.25)
        overall_score_percentage = overall_score * 100

        # Determine overall status
        if overall_score >= 0.95:
            overall_status = ComplianceStatus.COMPLIANT
        elif overall_score >= 0.8:
            overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            overall_status = ComplianceStatus.NON_COMPLIANT

        return overall_status, overall_score_percentage
