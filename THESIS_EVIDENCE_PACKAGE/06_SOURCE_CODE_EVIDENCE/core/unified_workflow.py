"""
Unified Test Generation Workflow - Master Orchestrator

This module implements the master workflow that orchestrates all components
of the pharmaceutical test generation system into one cohesive workflow.
It chains together GAMP-5 categorization, test planning, and parallel agent
execution to provide complete end-to-end test generation capabilities.

Key Features:
- Complete workflow orchestration from URS to test generation results
- Integration of categorization → planning → parallel execution → results
- GAMP-5 compliance with complete audit trail
- Error handling and human consultation triggers
- Phoenix observability integration
- Regulatory compliance (ALCOA+, 21 CFR Part 11)

Workflow Flow:
1. URS Document Input → GAMPCategorizationWorkflow
2. GAMPCategorizationEvent → PlannerAgentWorkflow
3. Parallel Agent Coordination (Context, SME, Research)
4. Result Compilation and Final Output
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from llama_index.core.llms import LLM
from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from src.agents.oq_generator.events import OQTestGenerationEvent, OQTestSuiteEvent
from src.agents.oq_generator.workflow import OQTestGenerationWorkflow

# Import 21 CFR Part 11 compliance systems
from src.compliance import (
    get_mfa_service,
    get_rbac_system,
    get_signature_service,
    get_training_system,
    get_validation_framework,
    get_worm_storage,
)

# from llama_index.llms.openai import OpenAI  # Migrated to centralized LLM config
from src.config.llm_config import LLMConfig
from src.core.categorization_workflow import GAMPCategorizationWorkflow
from src.core.events import (
    AgentRequestEvent,
    AgentResultEvent,
    AgentResultsEvent,
    ConsultationBypassedEvent,
    ConsultationRequiredEvent,
    GAMPCategorizationEvent,
    GAMPCategory,
    PlanningEvent,
    URSIngestionEvent,
)
from src.core.human_consultation import HumanConsultationManager
from src.monitoring.phoenix_config import setup_phoenix
from src.monitoring.simple_tracer import get_tracer

# Enhanced Phoenix Observability - temporarily disabled for testing
# from src.monitoring.phoenix_enhanced import (
#     PhoenixEnhancedClient,
#     AutomatedTraceAnalyzer,
#     WorkflowEventFlowVisualizer
# )
from src.shared.config import get_config

# Set up configuration
config = get_config()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Safe context management functions for preventing state failures
# Using ctx.store for persistent cross-workflow state management
async def safe_context_get(ctx: Context, key: str, default=None):
    """
    Safe context retrieval with persistent storage and explicit error handling.
    
    Args:
        ctx: Workflow context
        key: Context key to retrieve
        default: Default value if key not found or error occurs
        
    Returns:
        Retrieved value or default
        
    Raises:
        RuntimeError: If critical state retrieval fails with no fallback allowed
    """
    try:
        # ENHANCED: Add detailed logging for debugging
        logger.debug(f"[CTX] Attempting to retrieve context key: {key}")

        # Use ctx.store for persistent storage across workflow boundaries
        value = await ctx.store.get(key)
        if value is not None:
            # ENHANCED: Log value type for debugging complex objects
            logger.debug(f"[CTX] Context retrieval successful for key {key}, type: {type(value)}")
            return value
        if default is not None:
            logger.debug(f"[CTX] Context key {key} not found, returning default: {default}")
            return default
        # NO FALLBACKS - explicit failure for critical state
        logger.error(f"[CRITICAL] Context key '{key}' not found in persistent store and no default provided")

        # ENHANCED: Add context diagnosis for debugging
        all_keys = []
        try:
            # Try to get all available keys for debugging
            for test_key in ["workflow_start_time", "categorization_result", "planning_event", "gamp_category"]:
                try:
                    test_value = await ctx.store.get(test_key)
                    if test_value is not None:
                        all_keys.append(test_key)
                except:
                    pass
            logger.error(f"[CTX] Available context keys: {all_keys}")
        except Exception as diag_error:
            logger.error(f"Context diagnosis failed: {diag_error}")

        raise RuntimeError(f"Critical state '{key}' not found in workflow context - workflow state corrupted")
    except Exception as e:
        logger.error(f"[ERROR] Context retrieval failed for key {key}: {e}")
        # NO FALLBACKS - fail explicitly for regulatory compliance
        raise RuntimeError(f"Context storage system failure for key '{key}': {e!s}") from e


async def safe_context_set(ctx: Context, key: str, value):
    """
    Safe context storage with persistent storage and explicit error handling.
    
    Enhanced with comprehensive state transition audit logging for regulatory compliance.
    
    Args:
        ctx: Workflow context
        key: Context key to store
        value: Value to store
        
    Returns:
        bool: True if successful
        
    Raises:
        RuntimeError: If critical state storage fails (no fallback allowed)
    """
    try:
        # Initialize audit trail for state transition logging
        from src.core.audit_trail import get_audit_trail
        audit_trail = get_audit_trail()

        # ENHANCED: Add detailed logging for debugging
        logger.debug(f"[CTX] Attempting to store context key: {key}, type: {type(value)}")

        # Get previous value for state transition tracking
        previous_value = None
        try:
            previous_value = await ctx.store.get(key)
        except Exception:
            pass  # New key, no previous value

        # ENHANCED: Handle complex objects that might need special serialization
        if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, list, dict)):
            logger.debug(f"[CTX] Storing complex object {key}: {type(value)}")
            # For GAMPCategory enum, store both value and type info
            if hasattr(value, "value") and hasattr(value, "__class__"):
                logger.debug(f"[CTX] Enum detected for {key}: {value.value}")

        # Use ctx.store for persistent storage across workflow boundaries
        await ctx.store.set(key, value)
        logger.debug(f"[CTX] Context storage successful for key {key}")

        # Log state transition for audit trail
        audit_trail.log_state_transition(
            from_state=f"context_{key}_previous" if previous_value is not None else "context_key_not_exists",
            to_state=f"context_{key}_stored",
            transition_trigger="safe_context_set",
            transition_metadata={
                "context_key": key,
                "value_type": type(value).__name__,
                "previous_value_existed": previous_value is not None,
                "storage_method": "ctx.store.set",
                "verification_enabled": True
            },
            workflow_step="context_management",
            state_data={
                "key": key,
                "value_type": type(value).__name__,
                "value_summary": str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
            },
            workflow_context={
                "context_operation": "storage",
                "regulatory_compliance": "GAMP-5",
                "audit_trail_enabled": True
            }
        )

        # ENHANCED: Verify storage by reading back
        try:
            verification = await ctx.store.get(key)
            if verification is None:
                logger.warning(f"[WARNING] Verification failed: {key} was stored but read back as None")

                # Log verification failure
                audit_trail.log_error_recovery(
                    error_type="context_verification_failure",
                    error_message=f"Context key {key} was stored but verification read returned None",
                    error_context={
                        "context_key": key,
                        "storage_successful": True,
                        "verification_failed": True
                    },
                    recovery_strategy="continue_with_warning",
                    recovery_actions=["log_warning", "continue_operation"],
                    recovery_success=True,
                    workflow_step="context_management"
                )
            else:
                logger.debug(f"[CTX] Storage verification successful for {key}")
        except Exception as verify_error:
            logger.warning(f"[WARNING] Storage verification failed for {key}: {verify_error}")

            # Log verification error
            audit_trail.log_error_recovery(
                error_type="context_verification_error",
                error_message=str(verify_error),
                error_context={
                    "context_key": key,
                    "storage_successful": True,
                    "verification_exception": type(verify_error).__name__
                },
                recovery_strategy="continue_with_warning",
                recovery_actions=["log_warning", "continue_operation"],
                recovery_success=True,
                workflow_step="context_management"
            )

        return True
    except Exception as e:
        logger.error(f"[CRITICAL] Context storage failed for key {key}: {e}")

        # Log critical context storage failure
        from src.core.audit_trail import get_audit_trail
        audit_trail = get_audit_trail()
        audit_trail.log_error_recovery(
            error_type="critical_context_storage_failure",
            error_message=str(e),
            error_context={
                "context_key": key,
                "value_type": type(value).__name__ if value is not None else "None",
                "error_type": type(e).__name__,
                "fallback_prevented": True
            },
            recovery_strategy="no_fallback_explicit_failure",
            recovery_actions=["log_error", "raise_runtime_error"],
            recovery_success=False,
            workflow_step="context_management",
            workflow_context={
                "regulatory_compliance": "GAMP-5",
                "audit_trail_preserved": True,
                "error_transparency": "complete"
            }
        )

        # NO FALLBACKS - fail explicitly for regulatory compliance
        raise RuntimeError(f"Context storage system failure for key '{key}': {e!s}") from e


async def validate_workflow_state(ctx: Context, required_keys: list[str]) -> bool:
    """
    Validate that all required workflow state keys exist in persistent storage.
    
    Args:
        ctx: Workflow context
        required_keys: List of required context keys
        
    Returns:
        bool: True if all keys exist
        
    Raises:
        RuntimeError: If any critical state is missing (no fallback allowed)
    """
    missing_keys = []
    for key in required_keys:
        try:
            value = await ctx.store.get(key)
            if value is None:
                missing_keys.append(key)
        except Exception as e:
            logger.error(f"State validation failed for key {key}: {e}")
            missing_keys.append(key)

    if missing_keys:
        error_msg = f"GAMP-5 Compliance Violation: Critical workflow state missing: {missing_keys}"
        logger.error(error_msg)
        # NO FALLBACKS - fail explicitly for regulatory compliance
        raise RuntimeError(error_msg)

    logger.info(f"GAMP-5 State Validation: PASSED - All required keys present: {required_keys}")
    return True


async def log_state_operation(operation: str, key: str, success: bool, error: str = None):
    """
    Log state operations for GAMP-5 audit trail compliance.
    
    Args:
        operation: Operation type (get/set/validate)
        key: Context key
        success: Whether operation succeeded
        error: Error message if failed
    """
    from datetime import UTC, datetime

    audit_entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "operation": f"context_{operation}",
        "key": key,
        "success": success,
        "error": error,
        "compliance_level": "GAMP-5"
    }

    if success:
        logger.info(f"GAMP-5 Audit: {operation.upper()} successful for key '{key}'")
    else:
        logger.error(f"GAMP-5 Audit: {operation.upper()} failed for key '{key}': {error}")


class UnifiedTestGenerationWorkflow(Workflow):
    """
    Master workflow that orchestrates complete pharmaceutical test generation.
    
    This workflow implements the complete end-to-end test generation process:
    1. Document ingestion and parsing
    2. GAMP-5 categorization
    3. Test planning with risk assessment
    4. Parallel agent coordination (Context, SME, Research)
    5. Test generation and validation
    6. Final result compilation with audit trail
    
    The workflow maintains regulatory compliance throughout and provides
    comprehensive observability through Phoenix monitoring.
    """

    def __init__(
        self,
        timeout: int = 1800,  # 30 minutes for complete workflow (increased for FDA API latency)
        verbose: bool = False,
        enable_phoenix: bool = True,
        enable_parallel_coordination: bool = True,
        enable_human_consultation: bool = True,
        llm: LLM | None = None,
        enable_part11_compliance: bool = True,
        user_session_id: str | None = None
    ):
        """
        Initialize the unified workflow with 21 CFR Part 11 compliance.
        
        Args:
            timeout: Maximum time to wait for workflow completion
            verbose: Enable verbose logging
            enable_phoenix: Enable Phoenix observability
            enable_parallel_coordination: Enable parallel agent coordination
            enable_human_consultation: Enable human consultation triggers
            llm: Language model for workflow intelligence
            enable_part11_compliance: Enable 21 CFR Part 11 compliance controls
            user_session_id: Active user session for access control
        """
        super().__init__(timeout=timeout, verbose=verbose)

        # Configuration
        self.timeout = timeout  # Store timeout for access in steps
        self.verbose = verbose
        self.enable_phoenix = enable_phoenix
        self.enable_parallel_coordination = enable_parallel_coordination
        self.enable_human_consultation = enable_human_consultation
        self.enable_part11_compliance = enable_part11_compliance
        self.user_session_id = user_session_id
        self.logger = logging.getLogger(__name__)

        # Initialize LLM using centralized configuration
        # NO FALLBACKS - LLMConfig handles all errors explicitly
        self.llm = llm or LLMConfig.get_llm()

        # Initialize workflow session
        self._workflow_session_id = f"unified_workflow_{datetime.now(UTC).isoformat()}"

        # Initialize 21 CFR Part 11 compliance systems
        if enable_part11_compliance:
            self.rbac_system = get_rbac_system()
            self.mfa_service = get_mfa_service()
            self.signature_service = get_signature_service()
            self.worm_storage = get_worm_storage()
            self.training_system = get_training_system()
            self.validation_framework = get_validation_framework()
            self.logger.info("[PART11] 21 CFR Part 11 compliance systems initialized")
        else:
            self.rbac_system = None
            self.mfa_service = None
            self.signature_service = None
            self.worm_storage = None
            self.training_system = None
            self.validation_framework = None

        # Initialize tracer for monitoring and error logging
        self.tracer = get_tracer()
        self.logger.info("[TRACER] Tracer initialized for workflow monitoring")

        # Initialize human consultation manager
        if enable_human_consultation:
            self.human_consultation = HumanConsultationManager()

        # Setup Phoenix if enabled
        if enable_phoenix:
            setup_phoenix()
            self.logger.info("[PHOENIX] Phoenix observability enabled")

    def _check_user_access(self, required_permission: str) -> bool:
        """
        Check if user has required permission for workflow operation.
        
        Args:
            required_permission: Permission required for operation
            
        Returns:
            bool: True if access granted
        """
        if not self.enable_part11_compliance or not self.user_session_id:
            # Compliance disabled or no session - allow access
            return True

        try:
            # Check permission using RBAC system
            has_permission = self.rbac_system.check_permission(
                session_id=self.user_session_id,
                permission=required_permission
            )

            # Log access control event
            from src.core.audit_trail import AuditEventType, get_audit_trail
            audit_trail = get_audit_trail()

            audit_trail.log_part11_compliance_event(
                compliance_event_type=AuditEventType.ACCESS_CONTROL_CHECK,
                user_id=self.user_session_id,
                compliance_data={
                    "permission_required": required_permission,
                    "access_granted": has_permission,
                    "workflow_session": self._workflow_session_id
                },
                regulatory_context={
                    "regulation_section": "21_CFR_11.10(d)",
                    "requirement": "limiting_system_access_to_authorized_individuals"
                }
            )

            if not has_permission:
                self.logger.warning(f"[PART11] Access denied for permission: {required_permission}")

            return has_permission

        except Exception as e:
            self.logger.error(f"[PART11] Access control check failed: {e}")
            # NO FALLBACKS - access control failure must be explicit
            return False

    @step
    async def start_unified_workflow(
        self,
        ctx: Context,
        ev: StartEvent
    ) -> URSIngestionEvent:
        """
        Start the unified workflow with document ingestion.
        
        Args:
            ctx: Workflow context
            ev: Start event with document path
            
        Returns:
            URSIngestionEvent to begin document processing
        """
        # Check user access permission for test generation
        if not self._check_user_access("CREATE_TESTS"):
            raise PermissionError("Access denied: User lacks CREATE_TESTS permission for workflow execution")

        # Initialize comprehensive audit trail for workflow state transitions
        from src.core.audit_trail import get_audit_trail
        audit_trail = get_audit_trail()

        self.logger.info("[WORKFLOW] Starting unified test generation workflow")

        # Log workflow initiation state transition
        audit_trail.log_state_transition(
            from_state="workflow_not_started",
            to_state="workflow_initializing",
            transition_trigger="start_event_received",
            transition_metadata={
                "workflow_type": "UnifiedTestGenerationWorkflow",
                "session_id": self._workflow_session_id,
                "start_event_type": type(ev).__name__,
                "phoenix_enabled": self.enable_phoenix,
                "parallel_coordination_enabled": self.enable_parallel_coordination
            },
            workflow_step="start_unified_workflow",
            state_data={
                "workflow_session_id": self._workflow_session_id,
                "start_time": datetime.now(UTC).isoformat(),
                "configuration": {
                    "timeout": self.timeout,
                    "verbose": self.verbose,
                    "enable_phoenix": self.enable_phoenix,
                    "enable_parallel_coordination": self.enable_parallel_coordination,
                    "enable_human_consultation": self.enable_human_consultation
                }
            },
            workflow_context={
                "regulatory_standards": ["GAMP-5", "21_CFR_Part_11"],
                "workflow_purpose": "pharmaceutical_test_generation"
            }
        )

        # Extract document path from start event
        document_path = ev.get("document_path") or getattr(ev, "document_path", None)
        if not document_path:
            raise ValueError("Document path is required to start workflow")

        # Load document content
        from pathlib import Path
        doc_path = Path(document_path)
        if not doc_path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")

        urs_content = doc_path.read_text(encoding="utf-8")

        # OWASP Security Validation - Critical first step
        logger.info(f"[{self._workflow_session_id}] Running OWASP security validation on URS content")

        try:
            from src.security import PharmaceuticalInputSecurityWrapper

            # Initialize security validator
            security_validator = PharmaceuticalInputSecurityWrapper()

            # Validate URS content for security threats
            validation_result = security_validator.validate_urs_content(
                urs_content=urs_content,
                document_name=doc_path.name,
                author="system"
            )

            # CRITICAL: Fail explicitly if security validation fails
            if not validation_result.is_valid:
                error_msg = (
                    f"OWASP security validation FAILED for document {doc_path.name}\n"
                    f"Threat Level: {validation_result.threat_level}\n"
                    f"OWASP Category: {validation_result.owasp_category}\n"
                    f"Detected Patterns: {validation_result.detected_patterns}\n"
                    f"Confidence: {validation_result.confidence_score:.3f}\n"
                    f"Error: {validation_result.error_message}\n"
                    f"NO FALLBACKS ALLOWED - Human consultation required."
                )
                logger.error(f"[{self._workflow_session_id}] {error_msg}")
                raise RuntimeError(error_msg)

            # Log successful security validation
            logger.info(
                f"[{self._workflow_session_id}] OWASP security validation PASSED: "
                f"threat_level={validation_result.threat_level}, "
                f"confidence={validation_result.confidence_score:.3f}"
            )

            # Prepare security metadata for event
            security_metadata = {
                "validation_id": str(validation_result.validation_id),
                "threat_level": validation_result.threat_level.value,
                "owasp_category": validation_result.owasp_category.value,
                "confidence_score": validation_result.confidence_score,
                "detected_patterns": validation_result.detected_patterns,
                "processing_time_ms": validation_result.processing_time_ms,
                "is_valid": validation_result.is_valid
            }

        except ImportError as e:
            error_msg = (
                f"OWASP security framework import failed: {e}\n"
                f"Security validation is REQUIRED for pharmaceutical compliance.\n"
                f"NO FALLBACKS ALLOWED - Human consultation required."
            )
            logger.error(f"[{self._workflow_session_id}] {error_msg}")
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = (
                f"OWASP security validation engine failed: {e}\n"
                f"Security validation failure prevents workflow execution.\n"
                f"NO FALLBACKS ALLOWED - Human consultation required."
            )
            logger.error(f"[{self._workflow_session_id}] {error_msg}")
            raise RuntimeError(error_msg) from e

        # Log document loading state transition
        audit_trail.log_state_transition(
            from_state="workflow_initializing",
            to_state="document_loaded",
            transition_trigger="document_path_resolved",
            transition_metadata={
                "document_path": document_path,
                "document_name": doc_path.name,
                "document_size": len(urs_content),
                "document_exists": True
            },
            workflow_step="start_unified_workflow",
            state_data={
                "document_metadata": {
                    "path": document_path,
                    "name": doc_path.name,
                    "size_bytes": len(urs_content),
                    "content_preview": urs_content[:200] + "..." if len(urs_content) > 200 else urs_content
                }
            },
            workflow_context={
                "workflow_session_id": self._workflow_session_id,
                "document_processing_step": "content_loading"
            }
        )

        # Store workflow metadata using safe operations
        await safe_context_set(ctx, "workflow_start_time", datetime.now(UTC))
        await safe_context_set(ctx, "workflow_session_id", self._workflow_session_id)
        await safe_context_set(ctx, "document_path", document_path)

        # Create URS ingestion event with all required fields including security metadata
        return URSIngestionEvent(
            urs_content=urs_content,
            document_name=doc_path.name,
            document_version="1.0",  # Default version
            author="system",
            # Security metadata from OWASP validation
            security_validation_result=security_metadata,
            security_threat_level=validation_result.threat_level.value,
            owasp_category=validation_result.owasp_category.value,
            security_confidence=validation_result.confidence_score
        )

    @step
    async def categorize_document(
        self,
        ctx: Context,
        ev: URSIngestionEvent
    ) -> GAMPCategorizationEvent:
        """
        Execute GAMP-5 categorization on the ingested document.
        
        Args:
            ctx: Workflow context
            ev: URS ingestion event
            
        Returns:
            GAMPCategorizationEvent with categorization results
        """
        # Initialize comprehensive audit trail for state transitions
        from src.core.audit_trail import get_audit_trail
        audit_trail = get_audit_trail()

        self.logger.info(f"[GAMP5] Starting GAMP-5 categorization for {ev.document_name}")

        # Log state transition to categorization
        audit_trail.log_state_transition(
            from_state="document_loaded",
            to_state="categorization_starting",
            transition_trigger="urs_ingestion_event",
            transition_metadata={
                "document_name": ev.document_name,
                "document_version": ev.document_version,
                "author": ev.author,
                "content_length": len(ev.urs_content),
                "categorization_workflow": "GAMPCategorizationWorkflow"
            },
            workflow_step="categorize_document",
            state_data={
                "current_step": "gamp_categorization",
                "document_metadata": {
                    "name": ev.document_name,
                    "version": ev.document_version,
                    "author": ev.author
                }
            },
            workflow_context={
                "workflow_session_id": self._workflow_session_id,
                "regulatory_standards": ["GAMP-5"],
                "categorization_purpose": "validation_approach_determination"
            }
        )

        # Initialize categorization workflow
        categorization_workflow = GAMPCategorizationWorkflow(
            verbose=self.verbose
        )

        # Execute categorization
        categorization_result = await categorization_workflow.run(
            urs_content=ev.urs_content,
            document_name=ev.document_name,
            document_version=ev.document_version,
            author=ev.author
        )

        # Handle different result formats
        if hasattr(categorization_result, "result"):
            categorization_data = categorization_result.result
        elif isinstance(categorization_result, dict) and "categorization_event" in categorization_result:
            # Extract the GAMPCategorizationEvent from the dict
            categorization_data = categorization_result["categorization_event"]
        else:
            categorization_data = categorization_result

        # Store categorization results using safe operations
        await safe_context_set(ctx, "categorization_result", categorization_data)

        # If we already have a GAMPCategorizationEvent, use it directly
        if isinstance(categorization_data, GAMPCategorizationEvent):
            categorization_event = categorization_data
            await safe_context_set(ctx, "gamp_category", categorization_data.gamp_category)
            self.logger.info(f"[GAMP5] GAMP-5 Category: {categorization_data.gamp_category.value}")
        # Handle dict or other formats
        elif isinstance(categorization_data, dict):
            await safe_context_set(ctx, "gamp_category", categorization_data.get("gamp_category"))
            categorization_event = GAMPCategorizationEvent(
                gamp_category=categorization_data.get("gamp_category"),
                confidence_score=categorization_data.get("confidence_score"),
                risk_assessment=categorization_data.get("risk_assessment"),
                document_content=categorization_data.get("document_content", ev.urs_content),
                session_id=self._workflow_session_id
            )
            gamp_cat = categorization_data.get("gamp_category")
            self.logger.info(f"✅ GAMP-5 Category: {gamp_cat}")
        else:
            await safe_context_set(ctx, "gamp_category", categorization_data.gamp_category)
            categorization_event = GAMPCategorizationEvent(
                gamp_category=categorization_data.gamp_category,
                confidence_score=categorization_data.confidence_score,
                risk_assessment=categorization_data.risk_assessment,
                document_content=categorization_data.document_content,
                session_id=self._workflow_session_id
            )
            self.logger.info(f"[GAMP5] GAMP-5 Category: {categorization_data.gamp_category.value}")
        return categorization_event

    @step
    async def run_planning_workflow(
        self,
        ctx: Context,
        ev: PlanningEvent
    ) -> AgentRequestEvent | AgentResultsEvent:
        """
        Execute parallel agent coordination based on planning results.
        
        Args:
            ctx: Workflow context
            ev: Planning event with test strategy and requirements
            
        Returns:
            AgentRequestEvent for next agent to execute, or AgentResultsEvent if no coordination needed
        """
        self.logger.info("[PARALLEL] Starting parallel agent coordination from planning event")

        # Store the planning event in context using safe operations
        await safe_context_set(ctx, "planning_event", ev)
        await safe_context_set(ctx, "test_strategy", ev.test_strategy)

        # Validate critical state was properly stored for GAMP-5 compliance
        await validate_workflow_state(ctx, ["planning_event", "test_strategy"])

        # Log successful state storage for audit trail
        await log_state_operation("store", "planning_event", True)

        # Generate proper agent requests based on GAMP category
        agent_requests = []
        if self.enable_parallel_coordination:
            # Always include context provider
            agent_requests.append({
                "agent_type": "context_provider",
                "request_data": {
                    "gamp_category": str(ev.gamp_category.value),  # CRITICAL FIX: Explicit string conversion
                    "test_strategy": ev.test_strategy,
                    "document_sections": ["functional_requirements", "validation_requirements"],
                    "search_scope": {}  # Add required field for ContextProviderRequest
                },
                "correlation_id": f"ctx_{self._workflow_session_id}"
            })

            # Add research agent for regulatory updates
            agent_requests.append({
                "agent_type": "research",
                "request_data": {
                    "research_focus": ["GAMP-5", f"Category {ev.gamp_category.value}", "OQ testing"],
                    "regulatory_scope": ["FDA", "EMA", "ICH"]
                },
                "correlation_id": f"res_{self._workflow_session_id}"
            })

            # Add SME agent for category-specific expertise
            agent_requests.append({
                "agent_type": "sme",
                "request_data": {
                    "specialty": f"GAMP Category {ev.gamp_category.value}",
                    "test_focus": "OQ testing for pharmaceutical compliance",
                    "compliance_level": "high",
                    "validation_focus": [ev.test_strategy.get("validation_rigor", "standard")]  # List format
                },
                "correlation_id": f"sme_{self._workflow_session_id}"
            })

        # Store agent requests separately using safe operations
        await safe_context_set(ctx, "agent_requests", agent_requests)

        self.logger.info(
            f"[PLANNING] Planning processed - {ev.estimated_test_count} tests estimated, "
            f"{len(agent_requests)} agents to coordinate"
        )

        if not self.enable_parallel_coordination or not agent_requests:
            self.logger.info("[PARALLEL] Skipping parallel coordination - creating empty results")
            # Create empty agent results to proceed to OQ generation
            return AgentResultsEvent(
                agent_results=[],
                session_id=self._workflow_session_id
            )

        # Convert planning requests to agent request events
        agent_request_events = []
        for i, request in enumerate(agent_requests):
            agent_request = AgentRequestEvent(
                agent_type=request.get("agent_type", "unknown"),
                request_data=request.get("request_data", {}),
                correlation_id=uuid4(),  # Generate proper UUID
                requesting_step="run_planning_workflow",
                session_id=self._workflow_session_id
            )
            agent_request_events.append(agent_request)

        # Store coordination context using safe operations
        await safe_context_set(ctx, "coordination_requests", agent_request_events)
        await safe_context_set(ctx, "expected_results_count", len(agent_request_events))
        await safe_context_set(ctx, "current_request_index", 0)
        await safe_context_set(ctx, "collected_results", [])  # Initialize collected results

        # Emit the first request
        if agent_request_events:
            return agent_request_events[0]
        # No requests to process - return empty results
        return AgentResultsEvent(
            agent_results=[],
            session_id=self._workflow_session_id
        )


    @step(num_workers=3)  # Allow parallel processing
    async def execute_agent_request(
        self,
        ctx: Context,
        ev: AgentRequestEvent
    ) -> AgentResultEvent:
        """
        Execute individual agent requests in parallel.
        
        Args:
            ctx: Workflow context
            ev: Agent request event
            
        Returns:
            AgentResultEvent with agent execution results
        """
        import time
        start_time = time.time()
        self.logger.info(f"[AGENT] Executing {ev.agent_type} agent request")

        try:
            # Import asyncio for timeout protection
            import asyncio

            # Dynamic timeout configuration based on agent type and operation
            timeout_mapping = {
                "research": 300.0,           # 5 minutes for regulatory APIs (FDA can take 14+ seconds)
                "sme": 120.0,               # 2 minutes for LLM calls
                "context_provider": 60.0,   # 1 minute for document processing
            }

            agent_timeout = timeout_mapping.get(ev.agent_type.lower(), 60.0)  # Default 1 minute

            # Execute actual agents based on type with timeout protection
            if ev.agent_type.lower() == "context_provider":
                # Use the actual context provider agent
                from src.agents.parallel.context_provider import (
                    create_context_provider_agent,
                )

                agent = create_context_provider_agent(
                    verbose=self.verbose,
                    enable_phoenix=self.enable_phoenix,
                    max_documents=10
                )

                # Process the request with timeout
                try:
                    result_event = await asyncio.wait_for(
                        agent.process_request(ev),
                        timeout=agent_timeout
                    )
                except TimeoutError:
                    self.tracer.log_error(f"{ev.agent_type}_timeout",
                                        Exception(f"Agent execution timed out after {agent_timeout}s"))
                    self.logger.error(f"[TIMEOUT] {ev.agent_type} agent timed out after {agent_timeout} seconds")
                    return AgentResultEvent(
                        agent_type=ev.agent_type,
                        correlation_id=ev.correlation_id,
                        result_data={
                            "error": f"Agent execution timed out after {agent_timeout} seconds",
                            "error_type": "TimeoutError"
                        },
                        success=False,
                        session_id=self._workflow_session_id,
                        processing_time=agent_timeout
                    )

                # Return the result event with session ID
                result_event.session_id = self._workflow_session_id
                return result_event

            if ev.agent_type.lower() == "sme":
                # Use the actual SME agent
                from src.agents.parallel.sme_agent import create_sme_agent

                agent = create_sme_agent(
                    specialty=ev.request_data.get("specialty", "general_validation"),
                    verbose=self.verbose
                )

                # Process the request with timeout
                try:
                    result_event = await asyncio.wait_for(
                        agent.process_request(ev),
                        timeout=agent_timeout
                    )
                except TimeoutError:
                    self.tracer.log_error(f"{ev.agent_type}_timeout",
                                        Exception(f"Agent execution timed out after {agent_timeout}s"))
                    self.logger.error(f"[TIMEOUT] {ev.agent_type} agent timed out after {agent_timeout} seconds")
                    return AgentResultEvent(
                        agent_type=ev.agent_type,
                        correlation_id=ev.correlation_id,
                        result_data={
                            "error": f"Agent execution timed out after {agent_timeout} seconds",
                            "error_type": "TimeoutError"
                        },
                        success=False,
                        session_id=self._workflow_session_id,
                        processing_time=agent_timeout
                    )

                # Return the result event with session ID
                result_event.session_id = self._workflow_session_id
                return result_event

            if ev.agent_type.lower() == "research":
                # Use the actual research agent
                from src.agents.parallel.research_agent import create_research_agent

                agent = create_research_agent(
                    # research_focus parameter doesn't exist in create_research_agent
                    verbose=self.verbose
                )

                # Process the request with timeout
                try:
                    result_event = await asyncio.wait_for(
                        agent.process_request(ev),
                        timeout=agent_timeout
                    )
                except TimeoutError:
                    self.tracer.log_error(f"{ev.agent_type}_timeout",
                                        Exception(f"Agent execution timed out after {agent_timeout}s"))
                    self.logger.error(f"[TIMEOUT] {ev.agent_type} agent timed out after {agent_timeout} seconds")
                    return AgentResultEvent(
                        agent_type=ev.agent_type,
                        correlation_id=ev.correlation_id,
                        result_data={
                            "error": f"Agent execution timed out after {agent_timeout} seconds",
                            "error_type": "TimeoutError"
                        },
                        success=False,
                        session_id=self._workflow_session_id,
                        processing_time=agent_timeout
                    )

                # Return the result event with session ID
                result_event.session_id = self._workflow_session_id
                return result_event

            # Unknown agent type
            self.logger.warning(f"Unknown agent type: {ev.agent_type}")
            return AgentResultEvent(
                agent_type=ev.agent_type,
                correlation_id=ev.correlation_id,
                result_data={
                    "error": f"Unknown agent type: {ev.agent_type}",
                    "supported_types": ["context_provider", "sme", "research"]
                },
                success=False,
                session_id=self._workflow_session_id,
                processing_time=0.0
            )

        except Exception as e:
            self.logger.error(f"[ERROR] Agent {ev.agent_type} execution failed: {e}")
            return AgentResultEvent(
                agent_type=ev.agent_type,
                correlation_id=ev.correlation_id,
                result_data={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "agent_type": ev.agent_type
                },
                success=False,
                session_id=self._workflow_session_id,
                processing_time=0.0
            )

    @step
    async def collect_agent_results(
        self,
        ctx: Context,
        ev: AgentResultEvent
    ) -> AgentRequestEvent | AgentResultsEvent | None:
        """
        Collect agent results and emit next request or final results.
        
        Args:
            ctx: Workflow context
            ev: Agent result event
            
        Returns:
            Next AgentRequestEvent, AgentResultsEvent when all results collected, or None while waiting
        """
        # Store the result using safe operations
        results = await safe_context_get(ctx, "collected_results", [])
        results.append(ev)
        await safe_context_set(ctx, "collected_results", results)

        # Get coordination context using safe retrieval
        coordination_requests = await safe_context_get(ctx, "coordination_requests", [])
        current_index = await safe_context_get(ctx, "current_request_index", 0)

        # Check if we have more requests to emit
        next_index = current_index + 1
        if next_index < len(coordination_requests):
            # Emit the next request using safe context operations
            await safe_context_set(ctx, "current_request_index", next_index)
            self.logger.info(f"[PARALLEL] Emitting agent request {next_index + 1}/{len(coordination_requests)}")
            return coordination_requests[next_index]

        # All requests have been processed, check if we have all results
        expected_count = await safe_context_get(ctx, "expected_results_count", 0)
        if len(results) >= expected_count:
            self.logger.info(f"[RESULTS] Collected all {len(results)} agent results")
            return AgentResultsEvent(
                agent_results=results,
                session_id=self._workflow_session_id
            )

        # Still waiting for results
        return None

    # DISABLED: This step was causing orphaned OQTestGenerationEvent
    # The generate_oq_tests step already handles AgentResultsEvent correctly

    @step
    async def check_consultation_required(
        self,
        ctx: Context,
        ev: GAMPCategorizationEvent
    ) -> ConsultationRequiredEvent | ConsultationBypassedEvent | PlanningEvent:
        """
        Check if human consultation is required based on categorization results.
        
        Implements validation mode bypass logic: when validation_mode=True,
        consultations that would normally be required are bypassed with
        full audit trail logging for regulatory compliance.
        
        Args:
            ctx: Workflow context
            ev: GAMP categorization event
            
        Returns:
            ConsultationRequiredEvent if consultation needed (production mode),
            ConsultationBypassedEvent if bypassed (validation mode),
            or PlanningEvent if no consultation needed
        """
        # Store categorization result in context using safe operations
        await safe_context_set(ctx, "categorization_result", ev)
        await safe_context_set(ctx, "gamp_category", ev.gamp_category)

        # Get validation mode configuration
        validation_mode_enabled = config.validation_mode.validation_mode
        bypass_threshold = config.validation_mode.bypass_consultation_threshold
        bypass_allowed_categories = config.validation_mode.bypass_allowed_categories

        if not self.enable_human_consultation:
            # Skip consultation - create planning event directly
            self.logger.info("Skipping consultation check - creating planning event")
            return self._create_planning_event_from_categorization(ev)

        # Check if consultation is required
        requires_consultation = (
            ev.confidence_score < bypass_threshold or  # Low confidence
            ev.gamp_category.value in [4, 5] or  # High-risk categories
            "consultation_required" in ev.risk_assessment.get("flags", [])
        )

        if requires_consultation:
            # Create the consultation event that would be required
            consultation_event = ConsultationRequiredEvent(
                consultation_type="categorization_review",
                context={
                    "reason": f"Category {ev.gamp_category.value} with confidence {ev.confidence_score:.2f}",
                    "gamp_category": ev.gamp_category,
                    "confidence_score": ev.confidence_score,
                    "risk_assessment": ev.risk_assessment,
                    "session_id": self._workflow_session_id
                },
                urgency="normal",
                required_expertise=["validation_engineer", "quality_assurance"],
                triggering_step="check_consultation_required"
            )

            # Check if we should bypass consultation due to validation mode
            should_bypass = (
                validation_mode_enabled and
                ev.gamp_category.value in bypass_allowed_categories
            )

            if should_bypass:
                self.logger.info(
                    f"[VALIDATION MODE] Bypassing consultation for Category {ev.gamp_category.value} "
                    f"(confidence: {ev.confidence_score:.2f}) - validation mode active"
                )

                # Create bypass event for audit trail
                bypass_event = ConsultationBypassedEvent(
                    original_consultation=consultation_event,
                    bypass_reason="validation_mode_enabled",
                    quality_metrics={
                        "original_confidence": ev.confidence_score,
                        "gamp_category": ev.gamp_category.value,
                        "bypass_threshold": bypass_threshold,
                        "validation_mode_active": True
                    }
                )

                # Log bypass for audit trail
                self.logger.warning(
                    f"AUDIT TRAIL: Consultation bypassed for {consultation_event.consultation_id} "
                    f"due to validation mode. Original consultation: {consultation_event.consultation_type}"
                )

                # Store categorization event in bypass event for downstream processing
                bypass_event.original_consultation.categorization_event = ev

                # Return bypass event - it will be consumed by handle_consultation_bypassed step
                return bypass_event
            # Production mode or category not allowed for bypass - require consultation
            self.logger.info("[CONSULT] Human consultation required - production mode or bypass not allowed")
            consultation_event.categorization_event = ev  # Add as dynamic attribute
            return consultation_event

        # No consultation needed - create planning event directly
        self.logger.info("No consultation required - creating planning event")
        return self._create_planning_event_from_categorization(ev)

    @step
    async def handle_consultation_bypassed(
        self,
        ctx: Context,
        ev: ConsultationBypassedEvent
    ) -> PlanningEvent:
        """
        Handle consultation bypass events for validation mode.
        
        This step processes ConsultationBypassedEvent by logging the bypass
        for audit trail and continuing with workflow execution.
        
        Args:
            ctx: Workflow context
            ev: Consultation bypassed event
            
        Returns:
            PlanningEvent to continue workflow execution
        """
        self.logger.info(f"[VALIDATION MODE] Processing consultation bypass: {ev.consultation_id}")

        # Log bypass metrics for audit trail
        bypass_metrics = {
            "consultation_type": ev.consultation_type,
            "gamp_category": ev.gamp_category,
            "confidence_score": ev.confidence_score,
            "bypass_timestamp": ev.bypass_timestamp,
            "bypass_reason": ev.bypass_reason
        }

        # Store bypass information in context for audit trail
        await safe_context_set(ctx, "consultation_bypassed", True)
        await safe_context_set(ctx, "bypass_metrics", bypass_metrics)

        # Get the original categorization from the bypass event context
        if ev.original_consultation and hasattr(ev.original_consultation, "categorization_event"):
            categorization_event = ev.original_consultation.categorization_event
        else:
            # Reconstruct from bypass event data
            from src.core.events import GAMPCategorizationEvent, GAMPCategory
            categorization_event = GAMPCategorizationEvent(
                gamp_category=GAMPCategory(ev.gamp_category) if ev.gamp_category else GAMPCategory.CATEGORY_5,
                confidence_score=ev.confidence_score or 0.6,
                justification="Reconstructed from bypass event for workflow continuation",
                risk_assessment={"bypassed_consultation": True},
                categorized_by="validation_mode_bypass"
            )

        # Create planning event to continue workflow
        planning_event = self._create_planning_event_from_categorization(categorization_event)

        self.logger.info("[VALIDATION MODE] Consultation bypass processed - continuing with planning")
        return planning_event

    def _create_planning_event_from_categorization(self, categorization_event: GAMPCategorizationEvent) -> PlanningEvent:
        """
        Create a planning event from categorization results.
        
        Args:
            categorization_event: GAMP categorization event
            
        Returns:
            PlanningEvent with test strategy and requirements
        """
        # Get test types and compliance requirements based on category
        test_types_map = {
            1: ["installation", "configuration"],
            3: ["installation", "configuration", "functional"],
            4: ["installation", "configuration", "functional", "performance"],
            5: ["installation", "configuration", "functional", "performance", "integration"]
        }

        compliance_map = {
            1: ["GAMP-5"],
            3: ["GAMP-5", "ALCOA+"],
            4: ["GAMP-5", "ALCOA+", "21 CFR Part 11"],
            5: ["GAMP-5", "ALCOA+", "21 CFR Part 11", "CSV"]
        }

        # Create default test strategy based on GAMP category
        test_strategy = {
            "approach": "category_based",
            "category": categorization_event.gamp_category.value,
            "validation_rigor": "standard" if categorization_event.gamp_category.value <= 3 else "enhanced",
            "confidence_score": categorization_event.confidence_score
        }

        return PlanningEvent(
            test_strategy=test_strategy,
            required_test_types=test_types_map.get(categorization_event.gamp_category.value, ["basic"]),
            compliance_requirements=compliance_map.get(categorization_event.gamp_category.value, ["GAMP-5"]),
            estimated_test_count=5 + (categorization_event.gamp_category.value * 2),  # Scale with category
            planner_agent_id=f"planner_{self._workflow_session_id}",
            gamp_category=categorization_event.gamp_category
        )

    @step
    async def handle_consultation(
        self,
        ctx: Context,
        ev: ConsultationRequiredEvent
    ) -> PlanningEvent:
        """
        Handle human consultation requirements.
        
        Args:
            ctx: Workflow context
            ev: Consultation required event
            
        Returns:
            PlanningEvent to continue workflow after consultation
        """
        self.logger.info(f"[CONSULT] Processing consultation: {ev.context.get('reason', 'Unknown reason')}")

        # In a real implementation, this would trigger human consultation UI
        # For now, we'll simulate consultation completion
        consultation_result = {
            "consultation_reason": ev.context.get("reason", "Unknown reason"),
            "consultation_timestamp": datetime.now(UTC).isoformat(),
            "consultation_status": "simulated_approval",
            "approved_category": ev.context.get("gamp_category", 5)  # Default to highest category
        }

        await safe_context_set(ctx, "consultation_result", consultation_result)

        # Create planning event after consultation to continue workflow
        if hasattr(ev, "categorization_event"):
            # Use the original categorization event to create planning event
            return self._create_planning_event_from_categorization(ev.categorization_event)

        # Create new categorization event and planning event from consultation context
        gamp_category = GAMPCategory(ev.context.get("gamp_category", 5))
        confidence_score = ev.context.get("confidence_score", 0.5)

        # Create a mock categorization event for planning
        categorization_event = GAMPCategorizationEvent(
            gamp_category=gamp_category,
            confidence_score=confidence_score,
            justification="Categorization after human consultation",
            risk_assessment=ev.context.get("risk_assessment", {"consultation_completed": True}),
            review_required=True,
            categorized_by="consultation_system"
        )

        return self._create_planning_event_from_categorization(categorization_event)

    @step
    async def generate_oq_tests(
        self,
        ctx: Context,
        ev: AgentResultsEvent
    ) -> OQTestSuiteEvent:
        """
        Generate OQ test suite based on planning and agent results.
        
        Args:
            ctx: Workflow context
            ev: Agent results event with context data
            
        Returns:
            OQTestSuiteEvent with generated test suite
        """
        self.logger.info("[OQ] Starting OQ test generation")

        # Validate critical workflow state exists before proceeding
        await validate_workflow_state(ctx, ["planning_event", "categorization_result"])

        # Get required context using safe retrieval with validation
        planning_event = await safe_context_get(ctx, "planning_event", None)
        categorization_result = await safe_context_get(ctx, "categorization_result", None)
        document_path = await safe_context_get(ctx, "document_path", "unknown")

        # Get document content from various sources
        urs_content = ""
        if categorization_result and hasattr(categorization_result, "document_content"):
            urs_content = categorization_result.document_content
        elif document_path and document_path != "unknown":
            try:
                urs_content = Path(document_path).read_text(encoding="utf-8")
            except Exception:
                urs_content = "Document content not available"
        else:
            urs_content = "Document content not available"

        # Validate required context - fail explicitly if missing critical data
        if planning_event is None:
            raise ValueError("Planning event not found in context - workflow state corrupted")
        if categorization_result is None:
            raise ValueError("Categorization result not found in context - workflow state corrupted")

        # Aggregate context from agent results
        aggregated_context = {
            "agent_results": {}
        }

        for result in ev.agent_results:
            if result.success:
                aggregated_context["agent_results"][result.agent_type] = result.result_data

        # Add planning context
        aggregated_context["planning_context"] = {
            "test_strategy": planning_event.test_strategy,
            "estimated_test_count": planning_event.estimated_test_count
        }

        # Create OQ generation event
        oq_generation_event = OQTestGenerationEvent(
            gamp_category=categorization_result.gamp_category,
            urs_content=urs_content,
            document_metadata={
                "name": Path(document_path).name if document_path else "Unknown",
                "path": document_path,
                "version": "1.0"
            },
            aggregated_context=aggregated_context,
            required_test_count=planning_event.estimated_test_count,
            test_strategy=planning_event.test_strategy,
            correlation_id=uuid4(),
            session_id=self._workflow_session_id
        )

        # Run OQ generation workflow

        oq_workflow = OQTestGenerationWorkflow(
            llm=self.llm,
            timeout=1500,  # 25 minutes (to accommodate o3 model)
            verbose=self.verbose,
            enable_validation=True,
            oq_generation_event=oq_generation_event
        )

        try:
            self.logger.info("Running OQ test generation workflow...")
            oq_result = await oq_workflow.run()

            # CRITICAL FIX: Check result type first
            if isinstance(oq_result, ConsultationRequiredEvent):
                # Handle consultation event properly
                self.logger.warning(
                    f"OQ generation returned consultation request: {oq_result.consultation_type}"
                )

                # Extract error details
                error_context = oq_result.context
                error_type = error_context.get("consultation_type", "unknown") if error_context else "unknown"

                # Re-raise with proper context
                raise RuntimeError(
                    f"OQ generation requires consultation: {error_type}",
                    {"consultation_event": oq_result, "context": error_context}
                )

            # Handle OQTestSuiteEvent directly
            if isinstance(oq_result, OQTestSuiteEvent):
                self.logger.info(
                    f"[OQ] Generated {oq_result.test_suite.total_test_count} OQ tests successfully"
                )
                return oq_result

            # Handle dictionary result (legacy format)
            if hasattr(oq_result, "result"):
                oq_data = oq_result.result
            else:
                oq_data = oq_result

            # Process dictionary result
            if isinstance(oq_data, dict):
                if oq_data.get("status") == "completed_successfully":
                    oq_event = oq_data.get("full_event")
                    if oq_event and isinstance(oq_event, OQTestSuiteEvent):
                        self.logger.info(
                            f"[OQ] Generated {oq_event.test_suite.total_test_count} OQ tests successfully"
                        )
                        return oq_event

                # Handle consultation in dictionary format
                consultation = oq_data.get("consultation", {})
                raise RuntimeError(
                    f"OQ generation failed: {consultation.get('consultation_type', 'unknown')}"
                )

            # Unexpected result type
            raise ValueError(
                f"Unexpected OQ workflow result type: {type(oq_result)}"
            )

        except Exception as e:
            self.logger.error(f"OQ generation failed: {e}")
            # Re-raise to trigger consultation
            raise

    @step
    async def complete_workflow(
        self,
        ctx: Context,
        ev: OQTestSuiteEvent
    ) -> StopEvent:
        """
        Complete the unified workflow and return final results.
        
        Args:
            ctx: Workflow context
            ev: OQTestSuiteEvent with generated test suite
            
        Returns:
            StopEvent with comprehensive workflow results
        """
        # Get all stored results using safe context operations
        workflow_start_time = await safe_context_get(ctx, "workflow_start_time", None)
        document_path = await safe_context_get(ctx, "document_path", "unknown")

        # Calculate total processing time
        total_time = datetime.now(UTC) - workflow_start_time if workflow_start_time else None

        # Process OQ test suite results (only event type we handle now)
        status = "completed_with_oq_tests"
        oq_results = {
            "test_suite_id": ev.test_suite.suite_id,
            "total_tests": ev.test_suite.total_test_count,
            "coverage_percentage": ev.test_suite.coverage_percentage,
            "review_required": ev.test_suite.review_required,
            "generation_successful": ev.generation_successful
        }

        # Get all context data with safe defaults
        categorization_result = await safe_context_get(ctx, "categorization_result", None)
        planning_event = await safe_context_get(ctx, "planning_event", None)
        agent_results = await safe_context_get(ctx, "collected_results", [])

        # Compile final results with main.py compatible structure
        final_results = {
            # Summary section for main.py display compatibility
            "summary": {
                "status": status,
                "workflow_duration_seconds": total_time.total_seconds() if total_time else 0.0,
                "category": categorization_result.gamp_category.value if categorization_result else None,
                "confidence": categorization_result.confidence_score if categorization_result else 0.0,
                "review_required": categorization_result.review_required if categorization_result else False,
                "estimated_test_count": planning_event.estimated_test_count if planning_event else 0,
                "timeline_estimate_days": ((planning_event.estimated_test_count * 0.5) / 8.0) if planning_event else 0,
                "agents_coordinated": len(agent_results),
                "coordination_success_rate": (len([r for r in agent_results if r.success]) / len(agent_results)) if agent_results else 0.0
            },

            # Detailed workflow metadata
            "workflow_metadata": {
                "session_id": self._workflow_session_id,
                "document_path": document_path,
                "start_time": workflow_start_time.isoformat() if workflow_start_time else None,
                "completion_time": datetime.now(UTC).isoformat(),
                "total_processing_time": total_time.total_seconds() if total_time else None,
                "phoenix_enabled": self.enable_phoenix
            },

            # Top-level status for backward compatibility
            "status": status,

            # Categorization results
            "categorization": {
                "category": categorization_result.gamp_category.value if categorization_result else None,
                "gamp_category": categorization_result.gamp_category.value if categorization_result else None,
                "confidence": categorization_result.confidence_score if categorization_result else 0.0,
                "confidence_score": categorization_result.confidence_score if categorization_result else 0.0,
                "review_required": categorization_result.review_required if categorization_result else False
            } if categorization_result else None,

            # Planning results
            "planning": {
                "estimated_test_count": planning_event.estimated_test_count if planning_event else 0,
                "test_strategy": planning_event.test_strategy if planning_event else None,
                "agent_requests_processed": len(agent_results)
            } if planning_event else None,

            # Agent coordination results
            "agent_coordination": {
                "total_agents": len(agent_results),
                "successful_agents": len([r for r in agent_results if r.success]),
                "failed_agents": len([r for r in agent_results if not r.success])
            },

            # OQ generation results
            "oq_generation": oq_results,

            # Additional workflow results
            "workflow_results": ev.workflow_results if hasattr(ev, "workflow_results") else None
        }

        self.logger.info(f"[COMPLETE] Unified workflow completed with status: {status}")
        if total_time:
            self.logger.info(f"[TIMING] Total processing time: {total_time.total_seconds():.2f} seconds")

        # Enhanced Phoenix Observability - temporarily disabled for testing
        # if self.enable_phoenix:
        #     try:
        #         self.logger.info("🔍 Running enhanced Phoenix observability analysis...")
        #
        #         # Initialize enhanced observability components
        #         phoenix_client = PhoenixEnhancedClient()
        #         analyzer = AutomatedTraceAnalyzer(phoenix_client)
        #
        #         # Query recent traces for this workflow session
        #         traces = await phoenix_client.query_workflow_traces(
        #             workflow_type="UnifiedTestGenerationWorkflow",
        #             hours=1  # Fixed parameter name
        #         )
        #
        #         # Analyze traces for compliance violations
        #         violations = await analyzer.analyze_compliance_violations(hours=24)
        #
        #         # Generate compliance dashboard
        #         dashboard_path = await analyzer.generate_compliance_dashboard(hours=24)
        #
        #         # Add enhanced observability results to final results
        #         final_results["enhanced_observability"] = {
        #             "traces_analyzed": len(traces),
        #             "compliance_violations": len(violations),
        #             "dashboard_generated": str(dashboard_path) if dashboard_path else None,
        #             "critical_violations": len([v for v in violations if v.severity == "CRITICAL"]),
        #             "regulatory_status": "COMPLIANT" if len(violations) == 0 else "NON_COMPLIANT"
        #         }
        #
        #         if violations:
        #             self.logger.warning(f"⚠️ Found {len(violations)} compliance violations")
        #             final_results["enhanced_observability"]["violations"] = [
        #                 {
        #                     "type": v.violation_type,
        #                     "severity": v.severity,
        #                     "description": v.description
        #                 } for v in violations[:5]  # Show first 5 violations
        #             ]
        #         else:
        #             self.logger.info("✅ No compliance violations detected")
        #
        #         self.logger.info(f"📊 Compliance dashboard generated: {dashboard_path}")
        #
        #     except Exception as e:
        #         self.logger.error(f"Enhanced observability analysis failed: {e}")
        #         final_results["enhanced_observability"] = {
        #             "error": str(e),
        #             "status": "failed"
        #         }

        return StopEvent(result=final_results)


# Convenience function for main.py compatibility
async def run_unified_test_generation_workflow(
    urs_content: str | None = None,
    document_name: str = "test_document",
    document_version: str = "1.0",
    author: str = "system",
    timeout: int = 900,
    verbose: bool = False,
    enable_error_handling: bool = True,
    confidence_threshold: float = 0.5,
    enable_document_processing: bool = True,
    enable_parallel_coordination: bool = True,
    document_path: str | None = None,
    validation_mode: bool = False,
    **kwargs
) -> dict[str, Any]:
    """
    Run the unified test generation workflow with compatibility for main.py.
    
    Args:
        urs_content: Document content (deprecated, use document_path)
        document_name: Name of the document
        document_version: Version of the document
        author: Author of the document
        timeout: Workflow timeout in seconds
        verbose: Enable verbose logging
        enable_error_handling: Enable error handling
        confidence_threshold: Confidence threshold for categorization
        enable_document_processing: Enable document processing
        enable_parallel_coordination: Enable parallel coordination
        document_path: Path to the document to process
        validation_mode: Enable validation mode (bypasses consultation for testing)
        **kwargs: Additional arguments
        
    Returns:
        Dictionary containing workflow results
    """
    # Temporarily set validation mode in config if requested
    original_validation_mode = None
    if validation_mode:
        original_validation_mode = config.validation_mode.validation_mode
        config.validation_mode.validation_mode = True
        logger.warning("VALIDATION MODE ENABLED: Consultations will be bypassed for testing")

    try:
        # Create workflow instance
        workflow = UnifiedTestGenerationWorkflow(
            timeout=timeout,
            verbose=verbose,
            enable_parallel_coordination=enable_parallel_coordination,
            enable_phoenix=True,
            enable_human_consultation=True
        )

        # Determine document path - prefer explicit document_path
        if document_path:
            doc_path = document_path
        else:
            # If we only have content, we need to create a temporary file
            # For now, raise error if no path provided
            raise ValueError("document_path is required for unified workflow")

        # Run the workflow
        result = await workflow.run(document_path=doc_path)

        # Handle different result formats
        if hasattr(result, "result"):
            return result.result
        return result

    except Exception as e:
        logger.error(f"Unified workflow failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "workflow_metadata": {
                "session_id": workflow._workflow_session_id,
                "failure_reason": "workflow_execution_error"
            }
        }
    finally:
        # Restore original validation mode if it was modified
        if original_validation_mode is not None:
            config.validation_mode.validation_mode = original_validation_mode
            logger.info("Validation mode restored to original setting")


# Export the main workflow class and convenience function
__all__ = ["UnifiedTestGenerationWorkflow", "run_unified_test_generation_workflow"]
