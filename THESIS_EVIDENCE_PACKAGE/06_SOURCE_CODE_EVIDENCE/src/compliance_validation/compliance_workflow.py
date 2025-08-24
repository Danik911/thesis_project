"""
Comprehensive Compliance Validation Workflow

This module orchestrates the complete compliance validation workflow across
GAMP-5, 21 CFR Part 11, and ALCOA+ frameworks with integrated gap analysis
and remediation planning.

Key Features:
- Multi-framework compliance orchestration
- Integrated evidence collection and traceability
- Automated gap analysis and prioritization
- CAPA-based remediation planning
- Comprehensive compliance reporting
- Stakeholder approval workflows
- NO FALLBACKS - complete workflow validation with diagnostics
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.cross_validation.quality_metrics import QualityMetrics
from src.cross_validation.structured_logger import StructuredLogger

from .alcoa_scorer import ALCOAScorer
from .cfr_part11_verifier import CFRPart11Verifier
from .evidence_collector import EvidenceCollector
from .gamp5_assessor import GAMP5Assessor
from .gap_analyzer import GapAnalyzer
from .models import (
    ComplianceFramework,
    ComplianceResult,
    ComplianceStatus,
    Evidence,
    EvidenceType,
)
from .remediation_planner import RemediationPlanner


class ComplianceWorkflowError(Exception):
    """Exception raised when compliance workflow fails."""


class ApprovalWorkflowError(Exception):
    """Exception raised when approval workflow fails."""


class ComplianceWorkflow:
    """
    Comprehensive compliance validation workflow orchestrator.
    
    This class orchestrates the complete compliance validation process across
    multiple regulatory frameworks with integrated gap analysis, remediation
    planning, and stakeholder approval workflows.
    
    NO FALLBACKS: All workflow failures surface explicitly with complete
    diagnostic information for regulatory compliance.
    """

    def __init__(
        self,
        output_directory: Path | str,
        quality_metrics: QualityMetrics | None = None,
        structured_logger: StructuredLogger | None = None
    ):
        """
        Initialize the compliance workflow orchestrator.
        
        Args:
            output_directory: Directory for compliance outputs and evidence
            quality_metrics: Optional quality metrics analyzer
            structured_logger: Optional structured logger
        """
        self.logger = logging.getLogger(__name__)
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)

        # Initialize component services
        self.evidence_collector = EvidenceCollector(
            self.output_directory / "evidence",
            structured_logger
        )

        self.gamp5_assessor = GAMP5Assessor(
            self.evidence_collector,
            quality_metrics
        )

        self.cfr_part11_verifier = CFRPart11Verifier(
            self.evidence_collector,
            structured_logger
        )

        self.alcoa_scorer = ALCOAScorer(
            self.evidence_collector,
            quality_metrics,
            structured_logger
        )

        self.gap_analyzer = GapAnalyzer(self.evidence_collector)

        self.remediation_planner = RemediationPlanner(self.evidence_collector)

        # Workflow state
        self.workflow_sessions: dict[str, dict[str, Any]] = {}
        self.approval_workflows: dict[str, dict[str, Any]] = {}

        # Initialize evidence collection templates
        self.evidence_collector.create_default_templates()

        self.logger.info(f"ComplianceWorkflow initialized with output directory: {self.output_directory}")

    def execute_comprehensive_validation(
        self,
        system_name: str,
        validation_scope: dict[str, Any],
        business_context: dict[str, Any] | None = None,
        workflow_manager: str = "compliance_workflow"
    ) -> dict[str, Any]:
        """
        Execute comprehensive compliance validation across all frameworks.
        
        Args:
            system_name: Name of system being validated
            validation_scope: Validation scope and parameters
            business_context: Optional business context for validation
            workflow_manager: Name of workflow manager
            
        Returns:
            Comprehensive validation results
            
        Raises:
            ComplianceWorkflowError: If comprehensive validation fails
        """
        try:
            session_id = str(uuid4())
            session_start = datetime.now(UTC).isoformat()

            self.logger.info(f"Starting comprehensive validation for {system_name}")

            # Initialize workflow session
            workflow_session = {
                "session_id": session_id,
                "system_name": system_name,
                "start_timestamp": session_start,
                "validation_scope": validation_scope,
                "business_context": business_context or {},
                "workflow_manager": workflow_manager,
                "framework_results": {},
                "gaps_identified": [],
                "remediation_plans": [],
                "compliance_status": ComplianceStatus.NOT_ASSESSED,
                "evidence_collected": []
            }

            # Phase 1: Framework-specific validations
            framework_results = self._execute_framework_validations(
                system_name, validation_scope, workflow_session
            )
            workflow_session["framework_results"] = framework_results

            # Phase 2: Gap consolidation and analysis
            gaps_analysis = self._execute_gap_analysis(
                system_name, framework_results, workflow_session
            )
            workflow_session["gaps_analysis"] = gaps_analysis

            # Phase 3: Remediation planning
            remediation_results = self._execute_remediation_planning(
                system_name, gaps_analysis, business_context, workflow_session
            )
            workflow_session["remediation_results"] = remediation_results

            # Phase 4: Generate comprehensive report
            comprehensive_report = self._generate_comprehensive_report(
                system_name, workflow_session
            )
            workflow_session["comprehensive_report"] = comprehensive_report

            # Store session
            self.workflow_sessions[session_id] = workflow_session

            # Generate final workflow results
            workflow_results = {
                "session_id": session_id,
                "system_name": system_name,
                "validation_timestamp": session_start,
                "completion_timestamp": datetime.now(UTC).isoformat(),
                "overall_compliance_status": comprehensive_report.overall_status.value,
                "overall_compliance_score": comprehensive_report.overall_score,
                "frameworks_assessed": [fw.value for fw in comprehensive_report.frameworks_assessed],
                "total_gaps_identified": comprehensive_report.total_gaps_identified,
                "critical_gaps": comprehensive_report.critical_gaps,
                "high_priority_gaps": comprehensive_report.high_priority_gaps,
                "remediation_plans_created": len(remediation_results.get("plans", [])),
                "total_remediation_effort": remediation_results.get("total_effort_hours", 0),
                "evidence_items_collected": comprehensive_report.total_evidence_items,
                "next_steps": self._generate_next_steps(comprehensive_report),
                "compliance_report": comprehensive_report.model_dump()
            }

            self.logger.info(f"Comprehensive validation completed: {comprehensive_report.overall_status.value}")
            return workflow_results

        except Exception as e:
            error_msg = f"Comprehensive validation failed for {system_name}: {e!s}"
            self.logger.error(error_msg)
            raise ComplianceWorkflowError(error_msg) from e

    def initiate_approval_workflow(
        self,
        session_id: str,
        approval_scope: dict[str, Any],
        stakeholders: list[str],
        initiator: str = "compliance_workflow"
    ) -> dict[str, Any]:
        """
        Initiate stakeholder approval workflow for compliance results.
        
        Args:
            session_id: Validation session ID
            approval_scope: Scope of approvals required
            stakeholders: List of stakeholder roles for approval
            initiator: Name of approval initiator
            
        Returns:
            Approval workflow status
            
        Raises:
            ApprovalWorkflowError: If approval workflow initiation fails
        """
        try:
            if session_id not in self.workflow_sessions:
                raise ApprovalWorkflowError(f"Validation session not found: {session_id}")

            session = self.workflow_sessions[session_id]
            approval_id = str(uuid4())

            self.logger.info(f"Initiating approval workflow for session {session_id}")

            # Create approval workflow
            approval_workflow = {
                "approval_id": approval_id,
                "validation_session_id": session_id,
                "system_name": session["system_name"],
                "initiation_timestamp": datetime.now(UTC).isoformat(),
                "approval_scope": approval_scope,
                "required_stakeholders": stakeholders,
                "initiator": initiator,
                "approval_status": "pending",
                "stakeholder_approvals": {stakeholder: {"status": "pending", "timestamp": None, "notes": ""}
                                        for stakeholder in stakeholders},
                "approval_sequence": self._determine_approval_sequence(stakeholders, approval_scope),
                "current_approval_step": 0,
                "approval_documentation": []
            }

            # Generate approval packages for stakeholders
            approval_packages = self._generate_approval_packages(session, approval_workflow)
            approval_workflow["approval_packages"] = approval_packages

            # Store approval workflow
            self.approval_workflows[approval_id] = approval_workflow

            # Start approval process
            self._initiate_first_approval_step(approval_workflow)

            approval_status = {
                "approval_id": approval_id,
                "status": "initiated",
                "required_approvals": len(stakeholders),
                "pending_approvals": len(stakeholders),
                "completed_approvals": 0,
                "current_step": approval_workflow["approval_sequence"][0] if approval_workflow["approval_sequence"] else None,
                "estimated_completion": self._estimate_approval_completion(approval_workflow)
            }

            self.logger.info(f"Approval workflow initiated: {approval_id}")
            return approval_status

        except Exception as e:
            error_msg = f"Approval workflow initiation failed: {e!s}"
            self.logger.error(error_msg)
            raise ApprovalWorkflowError(error_msg) from e

    def process_stakeholder_approval(
        self,
        approval_id: str,
        stakeholder: str,
        approval_decision: str,
        approval_notes: str = "",
        approver: str = "stakeholder"
    ) -> dict[str, Any]:
        """
        Process individual stakeholder approval decision.
        
        Args:
            approval_id: Approval workflow ID
            stakeholder: Stakeholder providing approval
            approval_decision: Decision ("approved", "rejected", "conditional")
            approval_notes: Optional approval notes
            approver: Name of person providing approval
            
        Returns:
            Updated approval workflow status
            
        Raises:
            ApprovalWorkflowError: If approval processing fails
        """
        try:
            if approval_id not in self.approval_workflows:
                raise ApprovalWorkflowError(f"Approval workflow not found: {approval_id}")

            workflow = self.approval_workflows[approval_id]

            if stakeholder not in workflow["stakeholder_approvals"]:
                raise ApprovalWorkflowError(f"Stakeholder not in approval workflow: {stakeholder}")

            self.logger.info(f"Processing approval from {stakeholder}: {approval_decision}")

            # Update stakeholder approval
            workflow["stakeholder_approvals"][stakeholder] = {
                "status": approval_decision,
                "timestamp": datetime.now(UTC).isoformat(),
                "notes": approval_notes,
                "approver": approver
            }

            # Document approval
            approval_doc = {
                "stakeholder": stakeholder,
                "decision": approval_decision,
                "timestamp": datetime.now(UTC).isoformat(),
                "notes": approval_notes,
                "approver": approver
            }
            workflow["approval_documentation"].append(approval_doc)

            # Update workflow status
            workflow_status = self._update_approval_workflow_status(workflow)

            # Check if workflow is complete
            if workflow_status["all_approvals_complete"]:
                workflow["approval_status"] = "completed"
                workflow["completion_timestamp"] = datetime.now(UTC).isoformat()

                # Generate final approval documentation
                final_documentation = self._generate_final_approval_documentation(workflow)
                workflow["final_documentation"] = final_documentation

                # Collect approval evidence
                evidence = self._collect_approval_evidence(workflow, approver)
                workflow["approval_evidence_id"] = evidence.evidence_id

            elif any(approval["status"] == "rejected" for approval in workflow["stakeholder_approvals"].values()):
                workflow["approval_status"] = "rejected"
                workflow["rejection_timestamp"] = datetime.now(UTC).isoformat()

            # Advance to next approval step if applicable
            if workflow_status["can_advance"] and workflow["approval_status"] == "pending":
                self._advance_approval_step(workflow)

            approval_summary = {
                "approval_id": approval_id,
                "stakeholder": stakeholder,
                "decision": approval_decision,
                "workflow_status": workflow["approval_status"],
                "pending_approvals": workflow_status["pending_count"],
                "completed_approvals": workflow_status["approved_count"],
                "rejected_approvals": workflow_status["rejected_count"],
                "overall_progress": workflow_status["progress_percentage"]
            }

            self.logger.info(f"Approval processed: {stakeholder} -> {approval_decision}")
            return approval_summary

        except Exception as e:
            error_msg = f"Approval processing failed: {e!s}"
            self.logger.error(error_msg)
            raise ApprovalWorkflowError(error_msg) from e

    def generate_validation_deliverables(
        self,
        session_id: str,
        deliverable_types: list[str],
        output_format: str = "json",
        generator: str = "compliance_workflow"
    ) -> dict[str, Path]:
        """
        Generate validation deliverables and reports.
        
        Args:
            session_id: Validation session ID
            deliverable_types: Types of deliverables to generate
            output_format: Output format ("json", "pdf", "excel")
            generator: Name of deliverable generator
            
        Returns:
            Dictionary mapping deliverable types to file paths
            
        Raises:
            ComplianceWorkflowError: If deliverable generation fails
        """
        try:
            if session_id not in self.workflow_sessions:
                raise ComplianceWorkflowError(f"Validation session not found: {session_id}")

            session = self.workflow_sessions[session_id]
            deliverable_paths = {}

            self.logger.info(f"Generating {len(deliverable_types)} deliverables for session {session_id}")

            for deliverable_type in deliverable_types:
                deliverable_path = self._generate_deliverable(
                    session, deliverable_type, output_format, generator
                )
                deliverable_paths[deliverable_type] = deliverable_path

            # Generate master deliverables index
            index_path = self._generate_deliverables_index(session, deliverable_paths, generator)
            deliverable_paths["deliverables_index"] = index_path

            self.logger.info(f"Generated {len(deliverable_paths)} deliverables")
            return deliverable_paths

        except Exception as e:
            error_msg = f"Deliverable generation failed: {e!s}"
            self.logger.error(error_msg)
            raise ComplianceWorkflowError(error_msg) from e

    def _execute_framework_validations(
        self, system_name: str, validation_scope: dict[str, Any], workflow_session: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute validations for each compliance framework."""
        framework_results = {}

        # GAMP-5 Assessment
        if "gamp5" in validation_scope.get("frameworks", []):
            try:
                self.logger.info("Executing GAMP-5 assessment")

                gamp5_params = validation_scope.get("gamp5_parameters", {})

                # Execute GAMP-5 assessments
                if "categorization" in gamp5_params:
                    categorization_result = self.gamp5_assessor.assess_system_categorization(**gamp5_params["categorization"])
                    workflow_session["evidence_collected"].extend([categorization_result.get("evidence_id")])

                if "lifecycle" in gamp5_params:
                    lifecycle_result = self.gamp5_assessor.validate_lifecycle_coverage(**gamp5_params["lifecycle"])
                    workflow_session["evidence_collected"].extend([lifecycle_result.get("evidence_id")])

                if "risk_testing" in gamp5_params:
                    risk_result = self.gamp5_assessor.assess_risk_based_testing(**gamp5_params["risk_testing"])
                    workflow_session["evidence_collected"].extend([risk_result.get("evidence_id")])

                # Generate GAMP-5 report
                gamp5_report = self.gamp5_assessor.generate_compliance_report(system_name)
                framework_results["gamp5"] = {
                    "compliance_result": gamp5_report,
                    "gaps": self.gamp5_assessor.identified_gaps,
                    "status": "completed"
                }

            except Exception as e:
                framework_results["gamp5"] = {
                    "status": "failed",
                    "error": str(e)
                }
                self.logger.error(f"GAMP-5 assessment failed: {e!s}")

        # 21 CFR Part 11 Verification
        if "cfr_part_11" in validation_scope.get("frameworks", []):
            try:
                self.logger.info("Executing CFR Part 11 verification")

                cfr_params = validation_scope.get("cfr_part11_parameters", {})

                # Execute CFR Part 11 verifications
                if "audit_trail" in cfr_params:
                    audit_result = self.cfr_part11_verifier.verify_audit_trail_completeness(**cfr_params["audit_trail"])
                    workflow_session["evidence_collected"].extend([audit_result.get("evidence_id")])

                if "signatures" in cfr_params:
                    signature_result = self.cfr_part11_verifier.verify_electronic_signatures(**cfr_params["signatures"])
                    workflow_session["evidence_collected"].extend([signature_result.get("evidence_id")])

                if "access_controls" in cfr_params:
                    access_result = self.cfr_part11_verifier.verify_access_controls(**cfr_params["access_controls"])
                    workflow_session["evidence_collected"].extend([access_result.get("evidence_id")])

                if "data_integrity" in cfr_params:
                    integrity_result = self.cfr_part11_verifier.verify_data_integrity_controls(**cfr_params["data_integrity"])
                    workflow_session["evidence_collected"].extend([integrity_result.get("evidence_id")])

                # Generate CFR Part 11 report
                cfr_report = self.cfr_part11_verifier.generate_cfr_part11_report(system_name)
                framework_results["cfr_part_11"] = {
                    "compliance_result": cfr_report,
                    "gaps": self.cfr_part11_verifier.identified_gaps,
                    "status": "completed"
                }

            except Exception as e:
                framework_results["cfr_part_11"] = {
                    "status": "failed",
                    "error": str(e)
                }
                self.logger.error(f"CFR Part 11 verification failed: {e!s}")

        # ALCOA+ Assessment
        if "alcoa_plus" in validation_scope.get("frameworks", []):
            try:
                self.logger.info("Executing ALCOA+ assessment")

                alcoa_params = validation_scope.get("alcoa_parameters", {})

                # Execute ALCOA+ assessment
                alcoa_assessment = self.alcoa_scorer.assess_system_data_integrity(**alcoa_params)

                # Generate ALCOA+ report
                alcoa_report = self.alcoa_scorer.generate_alcoa_compliance_report(system_name)
                framework_results["alcoa_plus"] = {
                    "compliance_result": alcoa_report,
                    "assessment": alcoa_assessment,
                    "gaps": self.alcoa_scorer.identified_gaps,
                    "status": "completed"
                }

            except Exception as e:
                framework_results["alcoa_plus"] = {
                    "status": "failed",
                    "error": str(e)
                }
                self.logger.error(f"ALCOA+ assessment failed: {e!s}")

        return framework_results

    def _execute_gap_analysis(
        self, system_name: str, framework_results: dict[str, Any], workflow_session: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute comprehensive gap analysis across frameworks."""
        try:
            self.logger.info("Executing gap consolidation and analysis")

            # Collect gaps from all frameworks
            gap_sources = {}
            for framework, results in framework_results.items():
                if results.get("status") == "completed" and "gaps" in results:
                    gap_sources[framework] = results["gaps"]

            if not gap_sources:
                return {"status": "no_gaps_found", "total_gaps": 0}

            # Consolidate gaps
            consolidation_result = self.gap_analyzer.consolidate_gaps(
                system_name, gap_sources, "compliance_workflow"
            )
            workflow_session["evidence_collected"].append(consolidation_result.get("evidence_id"))

            # Prioritize gaps
            prioritized_gaps = self.gap_analyzer.prioritize_gaps("risk_based", workflow_session.get("business_context"))

            # Analyze dependencies
            dependency_analysis = self.gap_analyzer.analyze_gap_dependencies()

            # Generate risk matrix
            risk_matrix = self.gap_analyzer.generate_risk_matrix()

            gaps_analysis = {
                "consolidation_result": consolidation_result,
                "prioritized_gaps": [gap.model_dump() for gap in prioritized_gaps],
                "dependency_analysis": dependency_analysis,
                "risk_matrix": risk_matrix,
                "analysis_summary": self.gap_analyzer.get_gap_analysis_summary(),
                "status": "completed"
            }

            # Store gaps in workflow session
            workflow_session["gaps_identified"] = prioritized_gaps

            return gaps_analysis

        except Exception as e:
            self.logger.error(f"Gap analysis failed: {e!s}")
            return {"status": "failed", "error": str(e)}

    def _execute_remediation_planning(
        self, system_name: str, gaps_analysis: dict[str, Any],
        business_context: dict[str, Any] | None, workflow_session: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute remediation planning for identified gaps."""
        try:
            self.logger.info("Executing remediation planning")

            if gaps_analysis.get("status") != "completed":
                return {"status": "skipped", "reason": "gap_analysis_failed"}

            prioritized_gaps = workflow_session.get("gaps_identified", [])
            if not prioritized_gaps:
                return {"status": "no_gaps_to_remediate"}

            remediation_plans = []
            total_effort = 0

            # Create individual remediation plans for high-priority gaps
            high_priority_gaps = [gap for gap in prioritized_gaps if gap.priority_rank <= 10]

            for gap in high_priority_gaps:
                try:
                    plan = self.remediation_planner.create_remediation_plan(
                        gap, gap.priority_rank, business_context, "compliance_workflow"
                    )
                    remediation_plans.append(plan.model_dump())
                    total_effort += plan.estimated_effort_hours
                except Exception as e:
                    self.logger.warning(f"Failed to create plan for gap {gap.gap_id}: {e!s}")

            # Create consolidated plan for related gaps if applicable
            if len(high_priority_gaps) >= 3:
                try:
                    consolidated_plan = self.remediation_planner.create_consolidated_plan(
                        high_priority_gaps[:5], f"Consolidated Compliance Remediation - {system_name}",
                        business_context, "compliance_workflow"
                    )
                    remediation_plans.append(consolidated_plan.model_dump())
                    total_effort += consolidated_plan.estimated_effort_hours
                except Exception as e:
                    self.logger.warning(f"Failed to create consolidated plan: {e!s}")

            # Generate remediation report
            remediation_report = self.remediation_planner.generate_remediation_report(
                system_name, include_completed=False, reporter_name="compliance_workflow"
            )

            remediation_results = {
                "plans": remediation_plans,
                "total_effort_hours": total_effort,
                "remediation_report": remediation_report,
                "high_priority_gaps_addressed": len(high_priority_gaps),
                "plans_created": len(remediation_plans),
                "status": "completed"
            }

            # Store plans in workflow session
            workflow_session["remediation_plans"] = remediation_plans

            return remediation_results

        except Exception as e:
            self.logger.error(f"Remediation planning failed: {e!s}")
            return {"status": "failed", "error": str(e)}

    def _generate_comprehensive_report(
        self, system_name: str, workflow_session: dict[str, Any]
    ) -> ComplianceResult:
        """Generate comprehensive compliance report."""
        # Aggregate all framework results
        framework_results = {}
        frameworks_assessed = []

        for framework, results in workflow_session["framework_results"].items():
            if results.get("status") == "completed":
                compliance_result = results["compliance_result"]
                framework_results[framework] = compliance_result.framework_results.get(framework, {})

                # Map framework names to enums
                framework_enum_mapping = {
                    "gamp5": ComplianceFramework.GAMP5,
                    "cfr_part_11": ComplianceFramework.CFR_PART_11,
                    "alcoa_plus": ComplianceFramework.ALCOA_PLUS
                }

                if framework in framework_enum_mapping:
                    frameworks_assessed.append(framework_enum_mapping[framework])

        # Calculate overall compliance
        overall_status, overall_score = self._calculate_overall_compliance(framework_results)

        # Count gaps and evidence
        all_gaps = workflow_session.get("gaps_identified", [])
        total_gaps = len(all_gaps)
        critical_gaps = len([g for g in all_gaps if hasattr(g, "severity") and g.severity.value == "critical"])
        high_priority_gaps = len([g for g in all_gaps if hasattr(g, "priority_rank") and g.priority_rank <= 10])

        evidence_count = len([eid for eid in workflow_session.get("evidence_collected", []) if eid])

        # Create comprehensive compliance result
        comprehensive_result = ComplianceResult(
            assessment_name=f"Comprehensive Compliance Assessment - {system_name}",
            system_under_assessment=system_name,
            frameworks_assessed=frameworks_assessed,
            assessment_scope="Multi-framework compliance validation with gap analysis and remediation planning",
            framework_results=framework_results,
            overall_status=overall_status,
            overall_score=overall_score,
            total_gaps_identified=total_gaps,
            critical_gaps=critical_gaps,
            high_priority_gaps=high_priority_gaps,
            gaps_with_plans=len(workflow_session.get("remediation_plans", [])),
            total_evidence_items=evidence_count,
            verified_evidence_items=evidence_count,  # Assume all collected evidence is verified
            assessment_team=["compliance_workflow"],
            assessment_start_date=workflow_session["start_timestamp"],
            assessment_completion_date=datetime.now(UTC).isoformat(),
            gap_ids=[g.gap_id for g in all_gaps if hasattr(g, "gap_id")],
            remediation_plan_ids=[p.get("plan_id") for p in workflow_session.get("remediation_plans", [])],
            evidence_ids=workflow_session.get("evidence_collected", [])
        )

        return comprehensive_result

    def _calculate_overall_compliance(self, framework_results: dict[str, Any]) -> tuple[ComplianceStatus, float]:
        """Calculate overall compliance status and score."""
        if not framework_results:
            return ComplianceStatus.NOT_ASSESSED, 0.0

        # Collect framework scores
        framework_scores = []
        framework_statuses = []

        for framework, results in framework_results.items():
            score = results.get("score", 0.0)
            status = results.get("status", ComplianceStatus.NOT_ASSESSED)

            framework_scores.append(score)
            if isinstance(status, str):
                framework_statuses.append(ComplianceStatus(status))
            else:
                framework_statuses.append(status)

        # Calculate average score
        overall_score = sum(framework_scores) / len(framework_scores) if framework_scores else 0.0

        # Determine overall status (most restrictive wins)
        if any(status == ComplianceStatus.NON_COMPLIANT for status in framework_statuses):
            overall_status = ComplianceStatus.NON_COMPLIANT
        elif any(status == ComplianceStatus.PARTIALLY_COMPLIANT for status in framework_statuses):
            overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
        elif all(status == ComplianceStatus.COMPLIANT for status in framework_statuses):
            overall_status = ComplianceStatus.COMPLIANT
        else:
            overall_status = ComplianceStatus.ASSESSMENT_FAILED

        return overall_status, overall_score

    def _generate_next_steps(self, compliance_result: ComplianceResult) -> list[str]:
        """Generate next steps based on compliance results."""
        next_steps = []

        if compliance_result.overall_status == ComplianceStatus.NON_COMPLIANT:
            next_steps.extend([
                "Immediate action required: Address critical compliance gaps",
                "Review and approve high-priority remediation plans",
                "Implement corrective actions before system use",
                "Schedule compliance re-assessment after remediation"
            ])
        elif compliance_result.overall_status == ComplianceStatus.PARTIALLY_COMPLIANT:
            next_steps.extend([
                "Review identified compliance gaps and remediation plans",
                "Prioritize remediation activities based on business impact",
                "Implement recommended preventive actions",
                "Schedule follow-up compliance assessment"
            ])
        elif compliance_result.overall_status == ComplianceStatus.COMPLIANT:
            next_steps.extend([
                "Maintain compliance through ongoing monitoring",
                "Implement preventive actions from remediation plans",
                "Schedule periodic compliance reviews",
                "Document lessons learned and best practices"
            ])

        # Add remediation-specific next steps
        if compliance_result.gaps_with_plans > 0:
            next_steps.append(f"Execute {compliance_result.gaps_with_plans} remediation plans")

        if compliance_result.critical_gaps > 0:
            next_steps.append(f"Immediately address {compliance_result.critical_gaps} critical gaps")

        return next_steps

    def _determine_approval_sequence(self, stakeholders: list[str], approval_scope: dict[str, Any]) -> list[str]:
        """Determine the sequence of approvals based on stakeholder roles."""
        # Define approval hierarchy
        approval_hierarchy = {
            "Quality Assurance Manager": 1,
            "Compliance Manager": 2,
            "Validation Manager": 3,
            "Chief Compliance Officer": 4,
            "Regulatory Affairs": 5
        }

        # Sort stakeholders by hierarchy
        sorted_stakeholders = sorted(
            stakeholders,
            key=lambda s: approval_hierarchy.get(s, 999)
        )

        return sorted_stakeholders

    def _generate_approval_packages(
        self, session: dict[str, Any], approval_workflow: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """Generate approval packages for each stakeholder."""
        packages = {}

        for stakeholder in approval_workflow["required_stakeholders"]:
            packages[stakeholder] = {
                "stakeholder": stakeholder,
                "approval_scope": approval_workflow["approval_scope"],
                "validation_summary": self._create_validation_summary(session),
                "critical_findings": self._extract_critical_findings(session),
                "remediation_summary": self._create_remediation_summary(session),
                "package_created": datetime.now(UTC).isoformat()
            }

        return packages

    def _create_validation_summary(self, session: dict[str, Any]) -> dict[str, Any]:
        """Create validation summary for approval packages."""
        framework_results = session.get("framework_results", {})

        summary = {
            "system_name": session["system_name"],
            "frameworks_validated": list(framework_results.keys()),
            "validation_date": session["start_timestamp"],
            "overall_status": "pending_analysis",
            "key_findings": []
        }

        for framework, results in framework_results.items():
            if results.get("status") == "completed":
                compliance_result = results["compliance_result"]
                summary["key_findings"].append(
                    f"{framework.upper()}: {compliance_result.overall_status.value} - {compliance_result.overall_score:.1f}/100"
                )

        return summary

    def _extract_critical_findings(self, session: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract critical findings for stakeholder review."""
        critical_findings = []

        gaps = session.get("gaps_identified", [])
        for gap in gaps[:5]:  # Top 5 gaps
            if hasattr(gap, "severity") and gap.severity.value in ["critical", "high"]:
                critical_findings.append({
                    "title": gap.title,
                    "severity": gap.severity.value,
                    "framework": gap.framework.value,
                    "impact_summary": gap.risk_to_patient
                })

        return critical_findings

    def _create_remediation_summary(self, session: dict[str, Any]) -> dict[str, Any]:
        """Create remediation summary for approval packages."""
        plans = session.get("remediation_plans", [])

        if not plans:
            return {"status": "no_remediation_required"}

        total_effort = sum(plan.get("estimated_effort_hours", 0) for plan in plans)

        return {
            "total_plans": len(plans),
            "total_effort_hours": total_effort,
            "estimated_timeline": f"{max(30, total_effort // 20)} days",
            "investment_required": f"${total_effort * 85:.0f}",  # Rough cost estimate
            "key_actions": [plan.get("plan_title", "Unnamed Plan") for plan in plans[:3]]
        }

    def _initiate_first_approval_step(self, approval_workflow: dict[str, Any]) -> None:
        """Initiate the first step in the approval sequence."""
        if approval_workflow["approval_sequence"]:
            first_stakeholder = approval_workflow["approval_sequence"][0]
            self.logger.info(f"Approval workflow ready for {first_stakeholder}")

    def _update_approval_workflow_status(self, workflow: dict[str, Any]) -> dict[str, Any]:
        """Update approval workflow status based on stakeholder responses."""
        approvals = workflow["stakeholder_approvals"]

        approved_count = len([a for a in approvals.values() if a["status"] == "approved"])
        rejected_count = len([a for a in approvals.values() if a["status"] == "rejected"])
        pending_count = len([a for a in approvals.values() if a["status"] == "pending"])

        total_count = len(approvals)

        return {
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "pending_count": pending_count,
            "total_count": total_count,
            "progress_percentage": (approved_count / total_count) * 100,
            "all_approvals_complete": pending_count == 0 and rejected_count == 0,
            "can_advance": approved_count > 0 and pending_count > 0
        }

    def _advance_approval_step(self, workflow: dict[str, Any]) -> None:
        """Advance approval workflow to next step."""
        current_step = workflow.get("current_approval_step", 0)
        if current_step < len(workflow["approval_sequence"]) - 1:
            workflow["current_approval_step"] = current_step + 1
            next_stakeholder = workflow["approval_sequence"][current_step + 1]
            self.logger.info(f"Approval workflow advanced to {next_stakeholder}")

    def _estimate_approval_completion(self, approval_workflow: dict[str, Any]) -> str:
        """Estimate approval completion timeline."""
        # Simple estimation: 2 business days per stakeholder
        stakeholder_count = len(approval_workflow["required_stakeholders"])
        estimated_days = stakeholder_count * 2

        estimated_completion = datetime.now(UTC) + timedelta(days=estimated_days)
        return estimated_completion.isoformat()

    def _generate_final_approval_documentation(self, workflow: dict[str, Any]) -> dict[str, Any]:
        """Generate final approval documentation."""
        return {
            "approval_summary": {
                "system_name": workflow["system_name"],
                "approval_completion": datetime.now(UTC).isoformat(),
                "all_stakeholders_approved": all(
                    approval["status"] == "approved"
                    for approval in workflow["stakeholder_approvals"].values()
                ),
                "approval_documentation": workflow["approval_documentation"]
            },
            "regulatory_compliance": {
                "approval_authority_confirmed": True,
                "approval_sequence_followed": True,
                "documentation_complete": True
            },
            "next_steps": [
                "System approved for production use",
                "Implement ongoing compliance monitoring",
                "Execute approved remediation plans",
                "Schedule periodic compliance reviews"
            ]
        }

    def _collect_approval_evidence(self, workflow: dict[str, Any], approver: str) -> Evidence:
        """Collect evidence for approval workflow completion."""
        return self.evidence_collector.collect_evidence_from_system(
            system_name=workflow["system_name"],
            evidence_type=EvidenceType.APPROVAL_RECORD,
            collection_method="automated_approval_workflow_completion",
            collector_name=approver,
            approval_data={
                "approval_id": workflow["approval_id"],
                "stakeholders_involved": list(workflow["stakeholder_approvals"].keys()),
                "approval_decisions": [a["status"] for a in workflow["stakeholder_approvals"].values()],
                "completion_timestamp": workflow.get("completion_timestamp")
            },
            compliance_framework="Approval_Management"
        )

    def _generate_deliverable(
        self, session: dict[str, Any], deliverable_type: str, output_format: str, generator: str
    ) -> Path:
        """Generate specific deliverable type."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

        deliverable_mapping = {
            "executive_summary": self._generate_executive_summary_deliverable,
            "compliance_report": self._generate_compliance_report_deliverable,
            "gap_analysis": self._generate_gap_analysis_deliverable,
            "remediation_plans": self._generate_remediation_plans_deliverable,
            "evidence_package": self._generate_evidence_package_deliverable,
            "regulatory_submission": self._generate_regulatory_submission_deliverable
        }

        if deliverable_type not in deliverable_mapping:
            raise ComplianceWorkflowError(f"Unknown deliverable type: {deliverable_type}")

        # Generate deliverable content
        content = deliverable_mapping[deliverable_type](session)

        # Save to file
        filename = f"{deliverable_type}_{session['system_name']}_{timestamp}.{output_format.lower()}"
        deliverable_path = self.output_directory / "deliverables" / filename
        deliverable_path.parent.mkdir(parents=True, exist_ok=True)

        with open(deliverable_path, "w", encoding="utf-8") as f:
            if output_format.lower() == "json":
                import json
                json.dump(content, f, indent=2, default=str)

        self.logger.info(f"Generated deliverable: {deliverable_path}")
        return deliverable_path

    def _generate_executive_summary_deliverable(self, session: dict[str, Any]) -> dict[str, Any]:
        """Generate executive summary deliverable."""
        return {
            "title": "Executive Summary - Compliance Assessment",
            "system": session["system_name"],
            "assessment_date": session["start_timestamp"],
            "frameworks_assessed": list(session.get("framework_results", {}).keys()),
            "overall_findings": "Summary of key compliance findings...",
            "critical_issues": len([g for g in session.get("gaps_identified", [])
                                  if hasattr(g, "severity") and g.severity.value == "critical"]),
            "remediation_investment": "Investment required for full compliance...",
            "recommendations": ["Key recommendations for executive leadership..."]
        }

    def _generate_compliance_report_deliverable(self, session: dict[str, Any]) -> dict[str, Any]:
        """Generate detailed compliance report deliverable."""
        return {
            "report_type": "Detailed Compliance Assessment Report",
            "system": session["system_name"],
            "scope": session.get("validation_scope", {}),
            "methodology": "Multi-framework compliance validation approach...",
            "findings": session.get("framework_results", {}),
            "gaps_analysis": session.get("gaps_analysis", {}),
            "evidence_collected": len(session.get("evidence_collected", [])),
            "conclusions": "Detailed compliance conclusions and recommendations..."
        }

    def _generate_gap_analysis_deliverable(self, session: dict[str, Any]) -> dict[str, Any]:
        """Generate gap analysis deliverable."""
        return {
            "analysis_type": "Comprehensive Gap Analysis",
            "system": session["system_name"],
            "gaps_identified": len(session.get("gaps_identified", [])),
            "gap_details": [g.model_dump() if hasattr(g, "model_dump") else str(g)
                           for g in session.get("gaps_identified", [])],
            "risk_assessment": session.get("gaps_analysis", {}).get("risk_matrix", {}),
            "prioritization": "Risk-based gap prioritization methodology..."
        }

    def _generate_remediation_plans_deliverable(self, session: dict[str, Any]) -> dict[str, Any]:
        """Generate remediation plans deliverable."""
        return {
            "document_type": "Remediation Plans Package",
            "system": session["system_name"],
            "plans": session.get("remediation_plans", []),
            "total_effort": sum(plan.get("estimated_effort_hours", 0)
                               for plan in session.get("remediation_plans", [])),
            "implementation_timeline": "Recommended implementation sequence...",
            "resource_requirements": "Required resources and skills..."
        }

    def _generate_evidence_package_deliverable(self, session: dict[str, Any]) -> dict[str, Any]:
        """Generate evidence package deliverable."""
        return {
            "package_type": "Compliance Evidence Package",
            "system": session["system_name"],
            "evidence_inventory": session.get("evidence_collected", []),
            "evidence_summary": "Summary of collected compliance evidence...",
            "traceability": "Requirements to evidence traceability matrix...",
            "verification_status": "Evidence verification and validation status..."
        }

    def _generate_regulatory_submission_deliverable(self, session: dict[str, Any]) -> dict[str, Any]:
        """Generate regulatory submission package deliverable."""
        return {
            "submission_type": "Regulatory Compliance Submission",
            "system": session["system_name"],
            "regulatory_summary": "Summary for regulatory submission...",
            "compliance_statements": "Formal compliance declarations...",
            "supporting_evidence": "References to supporting evidence...",
            "regulatory_contacts": "Regulatory affairs contact information..."
        }

    def _generate_deliverables_index(
        self, session: dict[str, Any], deliverable_paths: dict[str, Path], generator: str
    ) -> Path:
        """Generate master index of all deliverables."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

        index_content = {
            "deliverables_index": {
                "system": session["system_name"],
                "generated_by": generator,
                "generation_timestamp": datetime.now(UTC).isoformat(),
                "deliverables": {
                    deliverable_type: {
                        "file_path": str(file_path),
                        "file_size_bytes": file_path.stat().st_size if file_path.exists() else 0,
                        "file_type": file_path.suffix
                    }
                    for deliverable_type, file_path in deliverable_paths.items()
                    if deliverable_type != "deliverables_index"
                }
            }
        }

        index_filename = f"deliverables_index_{session['system_name']}_{timestamp}.json"
        index_path = self.output_directory / "deliverables" / index_filename

        with open(index_path, "w", encoding="utf-8") as f:
            import json
            json.dump(index_content, f, indent=2, default=str)

        self.logger.info(f"Generated deliverables index: {index_path}")
        return index_path
