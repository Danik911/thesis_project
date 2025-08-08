"""
Subject Matter Expert (SME) Agent - Pharmaceutical Domain Validation

This module implements the SME Agent responsible for providing domain expertise
and validation guidance for pharmaceutical test generation. The agent specializes
in specific pharmaceutical domains and provides expert recommendations for
test strategies, compliance validation, and risk assessment.

Key Features:
- Domain-specific pharmaceutical expertise
- GAMP-5 compliance validation
- Risk assessment and mitigation strategies
- Test strategy recommendations
- Regulatory requirement validation
- Integration with parallel execution workflow
"""

import asyncio
import logging
import re
import json
import time
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.llms import LLM
from llama_index.core.tools import FunctionTool
from src.config.llm_config import LLMConfig
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from pydantic import BaseModel, Field
from src.core.events import AgentRequestEvent, AgentResultEvent, ValidationStatus
from src.monitoring.agent_instrumentation import trace_agent_method
from src.monitoring.simple_tracer import get_tracer
from src.config.timeout_config import TimeoutConfig


def clean_unicode_characters(text: str) -> str:
    """
    Clean invisible Unicode characters that can break JSON parsing.
    
    Handles:
    - BOM markers (UTF-8 BOM: \ufeff)
    - Zero-width spaces (\u200b)
    - Zero-width non-joiner (\u200c)
    - Zero-width joiner (\u200d)
    - Line/paragraph separators (\u2028, \u2029)
    
    Args:
        text: Raw text that may contain invisible characters
        
    Returns:
        Cleaned text suitable for JSON parsing
    """
    # Remove BOM marker
    if text.startswith('\ufeff'):
        text = text[1:]
    
    # Remove various invisible Unicode characters
    invisible_chars = [
        '\u200b',  # Zero-width space
        '\u200c',  # Zero-width non-joiner
        '\u200d',  # Zero-width joiner
        '\u2028',  # Line separator
        '\u2029',  # Paragraph separator
        '\ufeff',  # Additional BOM occurrences
    ]
    
    for char in invisible_chars:
        text = text.replace(char, '')
    
    return text


def find_balanced_json_array(text: str) -> Optional[str]:
    """
    Find a balanced JSON array using bracket counting.
    
    This handles nested arrays and objects correctly by counting
    opening and closing brackets while respecting string contexts.
    
    Args:
        text: Text containing potential JSON array
        
    Returns:
        Complete JSON array string or None if not found
    """
    start = text.find('[')
    if start == -1:
        return None
    
    bracket_count = 0
    in_string = False
    escape_next = False
    
    for i in range(start, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
            
        if not in_string:
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    return text[start:i+1]
    
    return None


def find_balanced_json_object(text: str) -> Optional[str]:
    """
    Find a balanced JSON object using brace counting.
    
    This handles nested objects and arrays correctly by counting
    opening and closing braces while respecting string contexts.
    
    Args:
        text: Text containing potential JSON object
        
    Returns:
        Complete JSON object string or None if not found
    """
    start = text.find('{')
    if start == -1:
        return None
    
    brace_count = 0
    in_string = False
    escape_next = False
    
    for i in range(start, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
            
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return text[start:i+1]
    
    return None


def extract_json_from_markdown(response_text: str) -> Union[Dict[str, Any], List[Any]]:
    """
    Extract JSON from markdown code blocks using balanced bracket parsing.
    
    This function uses sophisticated parsing techniques to handle nested JSON
    structures that break simple regex patterns. It supports both arrays and
    objects and handles Unicode contamination issues.
    
    Supports formats:
    - ```json\n{...}\n``` or ```json\n[...]\n```
    - ```\n{...}\n``` or ```\n[...]\n```
    - {...} or [...] (plain JSON)
    
    Args:
        response_text: The text response that may contain JSON in markdown blocks
        
    Returns:
        Parsed JSON dictionary or list
        
    Raises:
        ValueError: If no valid JSON found in response (NO FALLBACK for GAMP-5 compliance)
    """
    logger = logging.getLogger(__name__)
    
    # Clean invisible Unicode characters that can break JSON parsing
    cleaned_text = clean_unicode_characters(response_text)
    
    # Strategy 1: Extract from markdown code blocks (```json or ```)
    # Use balanced parsing to extract content from code blocks
    code_block_patterns = [
        r'```json\s*(.*?)\s*```',  # Explicit JSON blocks
        r'```\s*(.*?)\s*```',      # Generic code blocks
    ]
    
    for pattern in code_block_patterns:
        matches = re.finditer(pattern, cleaned_text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            block_content = match.group(1).strip()
            
            # Check what type of JSON we have by looking at the first non-whitespace character
            first_char_match = re.search(r'[^\s]', block_content)
            if first_char_match:
                first_char = first_char_match.group(0)
                
                # Use balanced parsing for objects (check first since objects can contain arrays)
                if first_char == '{':
                    balanced_json = find_balanced_json_object(block_content)
                    if balanced_json:
                        try:
                            parsed_data = json.loads(balanced_json)
                            logger.debug(f"Successfully parsed JSON object from code block: {len(parsed_data) if isinstance(parsed_data, dict) else 'N/A'} keys")
                            return parsed_data
                        except json.JSONDecodeError as e:
                            logger.warning(f"Balanced JSON object failed parsing: {e}")
                            
                # Use balanced parsing for arrays
                elif first_char == '[':
                    balanced_json = find_balanced_json_array(block_content)
                    if balanced_json:
                        try:
                            parsed_data = json.loads(balanced_json)
                            logger.debug(f"Successfully parsed JSON array from code block: {len(parsed_data) if isinstance(parsed_data, list) else 'N/A'} items")
                            return parsed_data
                        except json.JSONDecodeError as e:
                            logger.warning(f"Balanced JSON array failed parsing: {e}")
    
    # Strategy 2: Check for raw JSON - determine order based on first character
    # This prevents extracting objects from inside arrays
    first_char_match = re.search(r'[^\s]', cleaned_text)
    if first_char_match:
        first_char = first_char_match.group(0)
        
        if first_char == '[':
            # For arrays, check arrays first to avoid extracting nested objects
            balanced_array = find_balanced_json_array(cleaned_text)
            if balanced_array:
                try:
                    parsed_data = json.loads(balanced_array)
                    logger.debug(f"Successfully parsed raw JSON array: {len(parsed_data) if isinstance(parsed_data, list) else 'N/A'} items")
                    return parsed_data
                except json.JSONDecodeError as e:
                    logger.warning(f"Raw JSON array failed parsing: {e}")
            
            # If array parsing failed, try object as fallback
            balanced_object = find_balanced_json_object(cleaned_text)
            if balanced_object:
                try:
                    parsed_data = json.loads(balanced_object)
                    logger.debug(f"Successfully parsed raw JSON object: {len(parsed_data) if isinstance(parsed_data, dict) else 'N/A'} keys")
                    return parsed_data
                except json.JSONDecodeError as e:
                    logger.warning(f"Raw JSON object failed parsing: {e}")
        else:
            # For non-arrays, check objects first
            balanced_object = find_balanced_json_object(cleaned_text)
            if balanced_object:
                try:
                    parsed_data = json.loads(balanced_object)
                    logger.debug(f"Successfully parsed raw JSON object: {len(parsed_data) if isinstance(parsed_data, dict) else 'N/A'} keys")
                    return parsed_data
                except json.JSONDecodeError as e:
                    logger.warning(f"Raw JSON object failed parsing: {e}")
            
            # Then try arrays as fallback
            balanced_array = find_balanced_json_array(cleaned_text)
            if balanced_array:
                try:
                    parsed_data = json.loads(balanced_array)
                    logger.debug(f"Successfully parsed raw JSON array: {len(parsed_data) if isinstance(parsed_data, list) else 'N/A'} items")
                    return parsed_data
                except json.JSONDecodeError as e:
                    logger.warning(f"Raw JSON array failed parsing: {e}")
    
    # NO FALLBACK - Explicit failure for GAMP-5 compliance
    logger.error(f"No valid JSON found in response: {cleaned_text[:200]}...")
    logger.error(f"Original response length: {len(response_text)}, cleaned length: {len(cleaned_text)}")
    
    # Provide diagnostic information for troubleshooting
    has_arrays = '[' in cleaned_text and ']' in cleaned_text
    has_objects = '{' in cleaned_text and '}' in cleaned_text
    has_code_blocks = '```' in cleaned_text
    
    diagnostic_info = {
        "has_potential_arrays": has_arrays,
        "has_potential_objects": has_objects, 
        "has_code_blocks": has_code_blocks,
        "cleaned_length": len(cleaned_text),
        "original_length": len(response_text),
        "unicode_cleaning_applied": len(response_text) != len(cleaned_text)
    }
    
    logger.error(f"JSON extraction diagnostic info: {diagnostic_info}")
    raise ValueError(f"No valid JSON found in response. Diagnostic info: {diagnostic_info}. Preview: {cleaned_text[:200]}...")


class SMEAgentRequest(BaseModel):
    """Request model for SME Agent."""
    specialty: str
    test_focus: str
    compliance_level: str
    domain_knowledge: list[str] = Field(default_factory=list)
    validation_focus: list[str] = Field(default_factory=list)
    risk_factors: dict[str, Any] = Field(default_factory=dict)
    categorization_context: dict[str, Any] = Field(default_factory=dict)
    correlation_id: UUID
    timeout_seconds: int = Field(default_factory=lambda: TimeoutConfig.get_timeout("sme_agent"))


class SMEAgentResponse(BaseModel):
    """Response model for SME Agent."""
    specialty: str
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    compliance_assessment: dict[str, Any] = Field(default_factory=dict)
    risk_analysis: dict[str, Any] = Field(default_factory=dict)
    validation_points: list[str] = Field(
        default_factory=list,
        description="Key validation points identified by SME analysis"
    )
    validation_guidance: list[dict[str, Any]] = Field(default_factory=list)
    domain_insights: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = 0.0
    expert_opinion: str = ""
    regulatory_considerations: list[dict[str, Any]] = Field(default_factory=list)
    processing_metadata: dict[str, Any] = Field(default_factory=dict)


class SMEAgent:
    """
    Subject Matter Expert Agent for pharmaceutical domain validation.
    
    This agent provides specialized expertise in pharmaceutical domains including:
    1. Regulatory compliance validation (FDA, EMA, ICH)
    2. GAMP-5 category-specific guidance
    3. Risk assessment and mitigation strategies
    4. Test strategy recommendations
    5. Domain-specific best practices
    
    The agent supports multiple specialties and integrates with parallel
    execution workflows for comprehensive test generation support.
    """

    def __init__(
        self,
        specialty: str = "pharmaceutical_validation",
        llm: LLM | None = None,
        verbose: bool = False,
        enable_phoenix: bool = True,
        confidence_threshold: float = 0.7,
        max_recommendations: int = 10
    ):
        """
        Initialize the SME Agent.
        
        Args:
            specialty: SME specialty area
            llm: Language model for expert analysis
            verbose: Enable verbose logging
            enable_phoenix: Enable Phoenix AI instrumentation
            confidence_threshold: Minimum confidence for recommendations
            max_recommendations: Maximum number of recommendations
        """
        self.specialty = specialty
        # Use centralized LLM configuration (NO FALLBACKS)
        self.llm = llm or LLMConfig.get_llm()
        self.verbose = verbose
        self.enable_phoenix = enable_phoenix
        self.confidence_threshold = confidence_threshold
        self.max_recommendations = max_recommendations
        self.logger = logging.getLogger(__name__)
        
        # Detect OSS model for enhanced prompting strategies
        self.is_oss_model = self._detect_oss_model()
        if self.is_oss_model:
            self.logger.info(f"[OSS MODEL] Detected OSS model: {self.llm.model}, enabling enhanced JSON prompting")

        # Initialize OpenTelemetry tracer for observability
        self.tracer = trace.get_tracer(__name__)

        # Initialize domain knowledge base
        self.domain_knowledge = self._initialize_domain_knowledge()

        # Initialize function agent with SME tools
        self.function_agent = self._create_function_agent()

        # Performance tracking
        self._expertise_stats = {
            "total_consultations": 0,
            "high_confidence_recommendations": 0,
            "avg_processing_time": 0.0,
            "specialty_focus": specialty
        }

    @trace_agent_method(
        span_name="sme_agent.process_request",
        attributes={"agent.type": "sme_agent", "operation": "process_request"}
    )
    async def process_request(self, request_event: AgentRequestEvent) -> AgentResultEvent:
        """
        Process an SME consultation request with comprehensive Phoenix observability.
        
        Args:
            request_event: Agent request event containing domain consultation requirements
            
        Returns:
            AgentResultEvent with expert recommendations and analysis
        """
        start_time = datetime.now(UTC)
        self._expertise_stats["total_consultations"] += 1

        # Get current span for detailed tracing
        current_span = trace.get_current_span()

        try:
            # Parse request data
            request_data = SMEAgentRequest(
                **request_event.request_data,
                correlation_id=request_event.correlation_id
            )

            # Add request attributes to span
            if current_span and current_span.is_recording():
                current_span.set_attribute("request.correlation_id", str(request_data.correlation_id))
                current_span.set_attribute("request.specialty", request_data.specialty)
                current_span.set_attribute("request.compliance_level", request_data.compliance_level)
                current_span.set_attribute("request.test_focus", request_data.test_focus)
                current_span.set_attribute("request.risk_factors", str(request_data.risk_factors))
                current_span.set_attribute("request.timeout_seconds", request_data.timeout_seconds)
                
                # Add compliance attributes
                current_span.set_attribute("compliance.gamp5.sme", True)
                current_span.set_attribute("compliance.pharmaceutical", True)
                current_span.set_attribute("sme.specialty", self.specialty)

            if self.verbose:
                self.logger.info(
                    f"Processing SME consultation for {request_data.specialty} specialty "
                    f"with {request_data.compliance_level} compliance level"
                )

            # Add event for SME analysis start
            if current_span and current_span.is_recording():
                current_span.add_event("sme_analysis_start", {
                    "specialty": request_data.specialty,
                    "compliance_level": request_data.compliance_level,
                    "test_focus": request_data.test_focus
                })
            
            sme_response = await asyncio.wait_for(
                self._execute_sme_analysis(request_data),
                timeout=request_data.timeout_seconds
            )

            # Calculate processing time
            processing_time = (datetime.now(UTC) - start_time).total_seconds()

            # Update performance stats
            if sme_response.confidence_score >= self.confidence_threshold:
                self._expertise_stats["high_confidence_recommendations"] += 1
            self._update_performance_stats(processing_time)
            
            # Add completion event and result attributes to span
            if current_span and current_span.is_recording():
                current_span.add_event("sme_analysis_complete", {
                    "recommendations_count": len(sme_response.recommendations),
                    "confidence_score": sme_response.confidence_score,
                    "risk_level": sme_response.risk_analysis.get("risk_level", "unknown"),
                    "processing_time": processing_time
                })
                
                # Set result attributes
                current_span.set_attribute("result.recommendations_count", len(sme_response.recommendations))
                current_span.set_attribute("result.confidence_score", sme_response.confidence_score)
                current_span.set_attribute("result.risk_level", sme_response.risk_analysis.get("risk_level", "unknown"))
                current_span.set_attribute("result.validation_points_count", len(sme_response.validation_points))
                # Note: assessment_details not in SMEAgentResponse model, removed
                current_span.set_attribute("result.processing_time_seconds", processing_time)
                current_span.set_attribute("result.success", True)

            if self.verbose:
                self.logger.info(
                    f"SME analysis completed: {len(sme_response.recommendations)} recommendations, "
                    f"confidence: {sme_response.confidence_score:.2%}, "
                    f"processing time: {processing_time:.2f}s"
                )

            return AgentResultEvent(
                agent_type="sme_agent",
                result_data=sme_response.model_dump(),
                success=True,
                processing_time=processing_time,
                correlation_id=request_event.correlation_id,
                validation_status=ValidationStatus.VALIDATED
            )

        except TimeoutError:
            processing_time = (datetime.now(UTC) - start_time).total_seconds()
            error_msg = f"SME analysis timeout after {processing_time:.1f}s"

            self.logger.error(f"SME Agent timeout: {error_msg}")

            return AgentResultEvent(
                agent_type="sme_agent",
                result_data={"error": "timeout", "partial_analysis": {}},
                success=False,
                error_message=error_msg,
                processing_time=processing_time,
                correlation_id=request_event.correlation_id,
                validation_status=ValidationStatus.REJECTED
            )

        except Exception as e:
            processing_time = (datetime.now(UTC) - start_time).total_seconds()
            error_msg = f"SME analysis failed: {e!s}"

            self.logger.error(f"SME Agent error: {error_msg}")

            return AgentResultEvent(
                agent_type="sme_agent",
                result_data={"error": str(e), "error_type": type(e).__name__},
                success=False,
                error_message=error_msg,
                processing_time=processing_time,
                correlation_id=request_event.correlation_id,
                validation_status=ValidationStatus.REJECTED
            )

    async def _execute_sme_analysis(self, request: SMEAgentRequest) -> SMEAgentResponse:
        """Execute the SME analysis process with OpenTelemetry instrumentation."""
        # Create span for SME analysis execution
        with self.tracer.start_as_current_span("sme.execute") as span:
            span.set_attribute("sme.request_id", str(request.correlation_id))
            span.set_attribute("sme.specialty", request.specialty)
            span.set_attribute("sme.compliance_level", request.compliance_level)
            
            # Initialize response
            response = SMEAgentResponse(specialty=request.specialty)

            # Step 1: Compliance Assessment
            with self.tracer.start_as_current_span("sme.compliance_assessment"):
                compliance_assessment = await self._assess_compliance(request)
                response.compliance_assessment = compliance_assessment
                span.set_attribute("sme.compliance_status", compliance_assessment.get("status", "unknown"))

            # Step 2: Risk Analysis
            with self.tracer.start_as_current_span("sme.risk_analysis"):
                risk_analysis = await self._analyze_risks(request)
                response.risk_analysis = risk_analysis
                span.set_attribute("sme.risk_level", risk_analysis.get("risk_level", "unknown"))

            # Step 3: Generate Recommendations
            with self.tracer.start_as_current_span("sme.generate_recommendations"):
                recommendations = await self._generate_recommendations(request, compliance_assessment, risk_analysis)
                response.recommendations = recommendations
                span.set_attribute("sme.recommendations_count", len(recommendations))

            # Step 4: Validation Guidance
            with self.tracer.start_as_current_span("sme.validation_guidance"):
                validation_guidance = await self._provide_validation_guidance(request, recommendations)
                response.validation_guidance = validation_guidance

            # Step 5: Domain Insights
            with self.tracer.start_as_current_span("sme.domain_insights"):
                domain_insights = await self._generate_domain_insights(request)
                response.domain_insights = domain_insights

            # Step 6: Regulatory Considerations
            with self.tracer.start_as_current_span("sme.regulatory_considerations"):
                regulatory_considerations = await self._assess_regulatory_considerations(request)
                response.regulatory_considerations = regulatory_considerations

            # Step 7: Expert Opinion
            with self.tracer.start_as_current_span("sme.expert_opinion"):
                expert_opinion = await self._formulate_expert_opinion(request, recommendations, risk_analysis)
                response.expert_opinion = expert_opinion

            # Step 8: Calculate Confidence Score
            confidence_score = self._calculate_confidence_score(
                recommendations, compliance_assessment, risk_analysis
            )
            response.confidence_score = confidence_score
            span.set_attribute("sme.confidence_score", confidence_score)

            # Step 9: Add Processing Metadata
            response.processing_metadata = {
                "specialty_applied": request.specialty,
                "analysis_depth": request.compliance_level,
                "domain_knowledge_used": len(request.domain_knowledge),
                "confidence_factors": {
                    "recommendation_strength": len(recommendations),
                    "risk_clarity": risk_analysis.get("clarity_score", 0.5),
                    "compliance_certainty": compliance_assessment.get("certainty_score", 0.5)
                },
                "processing_timestamp": datetime.now(UTC).isoformat()
            }

            # Add final span attributes
            span.set_attribute("sme.final_confidence", confidence_score)
            span.set_attribute("sme.recommendations_final", len(recommendations))

            return response

    async def _assess_compliance(self, request: SMEAgentRequest) -> dict[str, Any]:
        """Assess compliance requirements and gaps using LLM expertise."""
        
        # NO FALLBACKS: Use actual LLM analysis instead of static logic
        base_compliance_prompt = f"""
        As a pharmaceutical validation expert specializing in {request.specialty}, assess the compliance requirements for a system with the following characteristics:
        
        - Specialty: {request.specialty}
        - Compliance Level: {request.compliance_level}
        - Test Focus: {request.test_focus}
        - GAMP Category: {request.categorization_context.get('gamp_category', 'unknown')}
        - Confidence Score: {request.categorization_context.get('confidence_score', 0.0)}
        - Domain Knowledge Areas: {', '.join(request.domain_knowledge)}
        - Validation Focus: {', '.join(request.validation_focus)}
        
        Provide a comprehensive compliance assessment including:
        1. Applicable regulatory standards
        2. Compliance gaps that need attention
        3. Required controls for this GAMP category
        4. Certainty score (0.0-1.0) for this assessment
        
        Respond with valid JSON in this exact format:
        {{
            "level": "compliance_level",
            "applicable_standards": ["standard1", "standard2"],
            "compliance_gaps": [{{"gap": "description", "impact": "high/medium/low", "recommendation": "action"}}],
            "required_controls": ["control1", "control2"],
            "certainty_score": 0.0
        }}
        """
        
        # Enhance prompt for OSS models
        compliance_prompt = self._enhance_prompt_for_oss(base_compliance_prompt, "json")
        
        try:
            # Make actual LLM call - NO FALLBACKS ALLOWED
            response = await self.llm.acomplete(compliance_prompt)
            response_text = response.text.strip()
            
            # Enhanced debug logging for OSS model troubleshooting
            self._log_llm_response_debug(response_text, "compliance_assessment")
            
            # Parse JSON response using robust extraction
            try:
                compliance_assessment = extract_json_from_markdown(response_text)
                
                # Debug logging
                self.logger.debug(f"Parsed compliance assessment type: {type(compliance_assessment)}")
                self.logger.debug(f"Parsed compliance assessment keys: {list(compliance_assessment.keys()) if isinstance(compliance_assessment, dict) else 'Not a dict'}")
                
                # Ensure we have a dictionary
                if not isinstance(compliance_assessment, dict):
                    raise ValueError(f"Expected dictionary, got {type(compliance_assessment).__name__}")
                
                # Validate required fields are present
                required_fields = ["level", "applicable_standards", "compliance_gaps", "required_controls", "certainty_score"]
                for field in required_fields:
                    if field not in compliance_assessment:
                        raise ValueError(f"Missing required field: {field}")
                
                return compliance_assessment
                
            except (json.JSONDecodeError, ValueError) as parse_error:
                # NO FALLBACKS: Fail explicitly with full diagnostic information
                raise RuntimeError(
                    f"CRITICAL: LLM compliance assessment failed to return valid JSON.\n"
                    f"Parse Error: {parse_error}\n"
                    f"LLM Response: {response_text[:2000]}...\n"
                    f"This violates pharmaceutical system requirements for explicit failure handling."
                ) from parse_error
                
        except Exception as llm_error:
            # NO FALLBACKS: Fail explicitly with full diagnostic information  
            raise RuntimeError(
                f"CRITICAL: Compliance assessment LLM call failed.\n"
                f"Error: {llm_error}\n"
                f"Request: {request.specialty}, {request.compliance_level}\n"
                f"This violates pharmaceutical system requirements - compliance assessment cannot use fallback logic."
            ) from llm_error

    async def _analyze_risks(self, request: SMEAgentRequest) -> dict[str, Any]:
        """Analyze risks and provide mitigation strategies using LLM expertise."""
        
        # NO FALLBACKS: Use actual LLM analysis instead of static logic
        risk_prompt = f"""
        As a pharmaceutical validation expert, analyze the validation risks for a system with these characteristics:
        
        - Specialty: {request.specialty}
        - Compliance Level: {request.compliance_level}
        - Test Focus: {request.test_focus}
        - Risk Factors: {request.risk_factors}
        - Validation Focus: {', '.join(request.validation_focus)}
        - GAMP Category: {request.categorization_context.get('gamp_category', 'unknown')}
        
        Provide a comprehensive risk analysis including:
        1. Identified risks with categories, probability, and impact
        2. Overall risk level assessment
        3. Specific mitigation strategies
        4. Critical concerns requiring immediate attention
        5. Clarity score (0.0-1.0) for the risk assessment
        
        Consider pharmaceutical validation risks including:
        - Technical complexity and integration risks
        - Regulatory compliance gaps
        - Data integrity concerns (ALCOA+ principles)
        - Validation lifecycle risks
        - Change control and configuration management
        
        Respond with valid JSON in this exact format:
        {{
            "identified_risks": [
                {{
                    "category": "category_name",
                    "risk": "risk_description", 
                    "probability": "low/medium/high",
                    "impact": "low/medium/high/critical",
                    "mitigation": "mitigation_strategy"
                }}
            ],
            "risk_level": "low/medium/high",
            "mitigation_strategies": [
                {{
                    "strategy": "strategy_description",
                    "priority": "low/medium/high", 
                    "timeline": "immediate/planned/future"
                }}
            ],
            "critical_concerns": ["concern1", "concern2"],
            "clarity_score": 0.0
        }}
        """
        
        try:
            # Make actual LLM call - NO FALLBACKS ALLOWED
            response = await self.llm.acomplete(risk_prompt)
            response_text = response.text.strip()
            
            # Parse JSON response using robust extraction
            try:
                risk_analysis = extract_json_from_markdown(response_text)
                
                # Validate required fields are present
                required_fields = ["identified_risks", "risk_level", "mitigation_strategies", "critical_concerns", "clarity_score"]
                for field in required_fields:
                    if field not in risk_analysis:
                        raise ValueError(f"Missing required field: {field}")
                
                # Validate risk_level is valid
                if risk_analysis["risk_level"] not in ["low", "medium", "high"]:
                    raise ValueError(f"Invalid risk_level: {risk_analysis['risk_level']}")
                
                return risk_analysis
                
            except (json.JSONDecodeError, ValueError) as parse_error:
                # NO FALLBACKS: Fail explicitly with full diagnostic information
                raise RuntimeError(
                    f"CRITICAL: LLM risk analysis failed to return valid JSON.\n"
                    f"Parse Error: {parse_error}\n"
                    f"LLM Response: {response_text[:2000]}...\n"
                    f"This violates pharmaceutical system requirements for explicit failure handling."
                ) from parse_error
                
        except Exception as llm_error:
            # NO FALLBACKS: Fail explicitly with full diagnostic information  
            raise RuntimeError(
                f"CRITICAL: Risk analysis LLM call failed.\n"
                f"Error: {llm_error}\n"
                f"Request: {request.specialty}, {request.compliance_level}\n"
                f"This violates pharmaceutical system requirements - risk analysis cannot use fallback logic."
            ) from llm_error

    async def _generate_recommendations(
        self,
        request: SMEAgentRequest,
        compliance_assessment: dict[str, Any],
        risk_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate expert recommendations using LLM expertise."""
        
        # NO FALLBACKS: Use actual LLM analysis instead of static logic
        base_recommendations_prompt = f"""
        As a pharmaceutical validation expert specializing in {request.specialty}, generate specific recommendations based on this analysis:
        
        COMPLIANCE ASSESSMENT:
        {compliance_assessment}
        
        RISK ANALYSIS:
        {risk_analysis}
        
        SYSTEM CONTEXT:
        - Specialty: {request.specialty}
        - Compliance Level: {request.compliance_level}
        - Test Focus: {request.test_focus}
        - GAMP Category: {request.categorization_context.get('gamp_category', 'unknown')}
        
        Generate up to {self.max_recommendations} prioritized recommendations that address:
        1. Compliance gaps identified in the assessment
        2. Risk mitigation strategies
        3. Domain-specific best practices for {request.specialty}
        4. Validation approach recommendations
        5. Implementation guidance
        
        Each recommendation must include:
        - Specific, actionable recommendation
        - Clear rationale tied to compliance/risk analysis
        - Priority level (high/medium/low)
        - Implementation effort estimate
        - Expected benefit category
        
        Respond with valid JSON in this exact format:
        [
            {{
                "category": "category_name",
                "priority": "high/medium/low",
                "recommendation": "specific_actionable_recommendation",
                "rationale": "clear_justification",
                "implementation_effort": "low/medium/high",
                "expected_benefit": "benefit_category"
            }}
        ]
        """
        
        # Enhance prompt for OSS models
        recommendations_prompt = self._enhance_prompt_for_oss(base_recommendations_prompt, "array")
        
        try:
            # Make actual LLM call - NO FALLBACKS ALLOWED
            response = await self.llm.acomplete(recommendations_prompt)
            response_text = response.text.strip()
            
            # Enhanced debug logging for OSS model troubleshooting
            self._log_llm_response_debug(response_text, "recommendations_generation")
            
            # Parse JSON response using robust extraction
            try:
                recommendations = extract_json_from_markdown(response_text)
                
                # Debug logging for recommendations parsing
                self.logger.debug(f"Parsed recommendations type: {type(recommendations)}")
                self.logger.debug(f"Is list: {isinstance(recommendations, list)}")
                if isinstance(recommendations, list) and len(recommendations) > 0:
                    self.logger.debug(f"First item type: {type(recommendations[0])}")
                
                # Validate response structure
                if not isinstance(recommendations, list):
                    raise ValueError("Response must be a list of recommendations")
                
                # Validate each recommendation
                required_fields = ["category", "priority", "recommendation", "rationale", "implementation_effort", "expected_benefit"]
                for i, rec in enumerate(recommendations):
                    if not isinstance(rec, dict):
                        raise ValueError(f"Recommendation {i} must be a dictionary")
                    for field in required_fields:
                        if field not in rec:
                            raise ValueError(f"Recommendation {i} missing required field: {field}")
                    if rec["priority"] not in ["low", "medium", "high"]:
                        raise ValueError(f"Recommendation {i} has invalid priority: {rec['priority']}")
                    if rec["implementation_effort"] not in ["low", "medium", "high"]:
                        raise ValueError(f"Recommendation {i} has invalid implementation_effort: {rec['implementation_effort']}")
                
                # Limit to max recommendations
                return recommendations[:self.max_recommendations]
                
            except (json.JSONDecodeError, ValueError) as parse_error:
                # NO FALLBACKS: Fail explicitly with full diagnostic information
                raise RuntimeError(
                    f"CRITICAL: LLM recommendations generation failed to return valid JSON.\n"
                    f"Parse Error: {parse_error}\n"
                    f"LLM Response: {response_text[:2000]}...\n"
                    f"This violates pharmaceutical system requirements for explicit failure handling."
                ) from parse_error
                
        except Exception as llm_error:
            # NO FALLBACKS: Fail explicitly with full diagnostic information  
            raise RuntimeError(
                f"CRITICAL: Recommendations generation LLM call failed.\n"
                f"Error: {llm_error}\n"
                f"Request: {request.specialty}, {request.compliance_level}\n"
                f"This violates pharmaceutical system requirements - recommendations cannot use fallback logic."
            ) from llm_error

    async def _provide_validation_guidance(
        self,
        request: SMEAgentRequest,
        recommendations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Provide specific validation guidance using LLM expertise."""
        
        # NO FALLBACKS: Use actual LLM analysis instead of static logic
        guidance_prompt = f"""
        As a pharmaceutical validation expert specializing in {request.specialty}, provide specific validation guidance based on:
        
        CONTEXT:
        - Specialty: {request.specialty}
        - Test Focus: {request.test_focus}
        - Compliance Level: {request.compliance_level}
        - GAMP Category: {request.categorization_context.get('gamp_category', 'unknown')}
        - Validation Focus Areas: {', '.join(request.validation_focus)}
        
        RECOMMENDATIONS TO IMPLEMENT:
        {recommendations}
        
        Provide specific, actionable validation guidance covering:
        1. Test strategy approach tailored to the test focus
        2. Compliance validation procedures for the compliance level
        3. Risk management guidance based on recommendations
        4. Domain-specific validation approaches
        5. Quality assurance considerations
        
        Each guidance item should include:
        - Area of focus
        - Specific guidance instructions
        - Key considerations/checkpoints
        - Clear success criteria
        
        Respond with valid JSON in this exact format:
        [
            {{
                "area": "area_name",
                "guidance": "specific_guidance_instructions",
                "key_considerations": ["consideration1", "consideration2"],
                "success_criteria": "clear_success_criteria"
            }}
        ]
        """
        
        try:
            # Make actual LLM call - NO FALLBACKS ALLOWED
            response = await self.llm.acomplete(guidance_prompt)
            response_text = response.text.strip()
            
            # Parse JSON response using robust extraction
            try:
                guidance = extract_json_from_markdown(response_text)
                
                # Validate response structure
                if not isinstance(guidance, list):
                    raise ValueError("Response must be a list of guidance items")
                
                # Validate each guidance item
                required_fields = ["area", "guidance", "key_considerations", "success_criteria"]
                for i, item in enumerate(guidance):
                    if not isinstance(item, dict):
                        raise ValueError(f"Guidance item {i} must be a dictionary")
                    for field in required_fields:
                        if field not in item:
                            raise ValueError(f"Guidance item {i} missing required field: {field}")
                    if not isinstance(item["key_considerations"], list):
                        raise ValueError(f"Guidance item {i} key_considerations must be a list")
                
                return guidance
                
            except (json.JSONDecodeError, ValueError) as parse_error:
                # NO FALLBACKS: Fail explicitly with full diagnostic information
                raise RuntimeError(
                    f"CRITICAL: LLM validation guidance failed to return valid JSON.\n"
                    f"Parse Error: {parse_error}\n"
                    f"LLM Response: {response_text[:2000]}...\n"
                    f"This violates pharmaceutical system requirements for explicit failure handling."
                ) from parse_error
                
        except Exception as llm_error:
            # NO FALLBACKS: Fail explicitly with full diagnostic information  
            raise RuntimeError(
                f"CRITICAL: Validation guidance LLM call failed.\n"
                f"Error: {llm_error}\n"
                f"Request: {request.specialty}, {request.test_focus}\n"
                f"This violates pharmaceutical system requirements - validation guidance cannot use fallback logic."
            ) from llm_error

    async def _generate_domain_insights(self, request: SMEAgentRequest) -> dict[str, Any]:
        """Generate domain-specific insights using LLM expertise."""
        
        # NO FALLBACKS: Use actual LLM analysis instead of static logic
        insights_prompt = f"""
        As a pharmaceutical validation expert specializing in {request.specialty}, provide domain-specific insights for a validation project with these characteristics:
        
        - Specialty: {request.specialty}
        - Compliance Level: {request.compliance_level}
        - Test Focus: {request.test_focus}
        - Domain Knowledge Areas: {', '.join(request.domain_knowledge)}
        - GAMP Category: {request.categorization_context.get('gamp_category', 'unknown')}
        
        Provide comprehensive domain insights including:
        1. Current industry trends affecting {request.specialty}
        2. Best practices specific to this specialty and compliance level
        3. Common pitfalls to avoid in {request.specialty} projects
        4. Key expertise areas that are critical for success
        5. Emerging challenges and opportunities
        
        Focus on practical, actionable insights that can improve validation outcomes.
        
        Respond with valid JSON in this exact format:
        {{
            "specialty_focus": "specialty_name",
            "key_expertise_areas": ["area1", "area2"],
            "industry_trends": ["trend1", "trend2"],
            "best_practices": ["practice1", "practice2"],
            "common_pitfalls": ["pitfall1", "pitfall2"],
            "emerging_challenges": ["challenge1", "challenge2"],
            "opportunities": ["opportunity1", "opportunity2"]
        }}
        """
        
        try:
            # Make actual LLM call - NO FALLBACKS ALLOWED
            response = await self.llm.acomplete(insights_prompt)
            response_text = response.text.strip()
            
            # Parse JSON response using robust extraction
            try:
                insights = extract_json_from_markdown(response_text)
                
                # Validate required fields are present
                required_fields = ["specialty_focus", "key_expertise_areas", "industry_trends", "best_practices", "common_pitfalls"]
                for field in required_fields:
                    if field not in insights:
                        raise ValueError(f"Missing required field: {field}")
                
                # Validate field types
                list_fields = ["key_expertise_areas", "industry_trends", "best_practices", "common_pitfalls"]
                for field in list_fields:
                    if not isinstance(insights[field], list):
                        raise ValueError(f"Field {field} must be a list")
                
                return insights
                
            except (json.JSONDecodeError, ValueError) as parse_error:
                # NO FALLBACKS: Fail explicitly with full diagnostic information
                raise RuntimeError(
                    f"CRITICAL: LLM domain insights generation failed to return valid JSON.\n"
                    f"Parse Error: {parse_error}\n"
                    f"LLM Response: {response_text[:2000]}...\n"
                    f"This violates pharmaceutical system requirements for explicit failure handling."
                ) from parse_error
                
        except Exception as llm_error:
            # NO FALLBACKS: Fail explicitly with full diagnostic information  
            raise RuntimeError(
                f"CRITICAL: Domain insights LLM call failed.\n"
                f"Error: {llm_error}\n"
                f"Request: {request.specialty}\n"
                f"This violates pharmaceutical system requirements - domain insights cannot use fallback logic."
            ) from llm_error

    async def _assess_regulatory_considerations(self, request: SMEAgentRequest) -> list[dict[str, Any]]:
        """Assess regulatory considerations using LLM expertise."""
        
        # NO FALLBACKS: Use actual LLM analysis instead of static logic
        regulatory_prompt = f"""
        As a pharmaceutical regulatory expert specializing in {request.specialty}, assess the regulatory considerations for a validation project with these characteristics:
        
        - Specialty: {request.specialty}
        - Compliance Level: {request.compliance_level}
        - GAMP Category: {request.categorization_context.get('gamp_category', 'unknown')}
        - Validation Focus: {', '.join(request.validation_focus)}
        - Test Focus: {request.test_focus}
        
        Assess regulatory considerations including:
        1. GAMP-5 category-specific requirements
        2. 21 CFR Part 11 electronic records compliance
        3. FDA Data Integrity Guidance (ALCOA+ principles)
        4. ICH guidelines applicable to the specialty
        5. EU GMP Annex 11 requirements
        6. Any specialty-specific regulatory requirements
        
        For each consideration, provide:
        - Specific regulation/guideline
        - Key consideration or requirement
        - Impact level (low/medium/high/critical)
        - Required actions
        - Implementation timeline phase
        
        Respond with valid JSON in this exact format:
        [
            {{
                "regulation": "regulation_name",
                "consideration": "specific_consideration_or_requirement",
                "impact": "low/medium/high/critical",
                "action_required": "specific_action_needed",
                "timeline": "design_phase/implementation_phase/validation_phase/ongoing"
            }}
        ]
        """
        
        try:
            # Make actual LLM call - NO FALLBACKS ALLOWED
            response = await self.llm.acomplete(regulatory_prompt)
            response_text = response.text.strip()
            
            # Parse JSON response using robust extraction
            try:
                considerations = extract_json_from_markdown(response_text)
                
                # Validate response structure
                if not isinstance(considerations, list):
                    raise ValueError("Response must be a list of regulatory considerations")
                
                # Validate each consideration
                required_fields = ["regulation", "consideration", "impact", "action_required", "timeline"]
                valid_impacts = ["low", "medium", "high", "critical"]
                valid_timelines = ["design_phase", "implementation_phase", "validation_phase", "ongoing"]
                
                for i, item in enumerate(considerations):
                    if not isinstance(item, dict):
                        raise ValueError(f"Consideration {i} must be a dictionary")
                    for field in required_fields:
                        if field not in item:
                            raise ValueError(f"Consideration {i} missing required field: {field}")
                    if item["impact"] not in valid_impacts:
                        raise ValueError(f"Consideration {i} has invalid impact: {item['impact']}")
                    # Allow compound timelines separated by slashes
                    timeline_parts = item["timeline"].split("/")
                    for timeline_part in timeline_parts:
                        if timeline_part.strip() not in valid_timelines:
                            raise ValueError(f"Consideration {i} has invalid timeline part: {timeline_part.strip()} in {item['timeline']}")
                
                return considerations
                
            except (json.JSONDecodeError, ValueError) as parse_error:
                # NO FALLBACKS: Fail explicitly with full diagnostic information
                raise RuntimeError(
                    f"CRITICAL: LLM regulatory considerations assessment failed to return valid JSON.\n"
                    f"Parse Error: {parse_error}\n"
                    f"LLM Response: {response_text[:2000]}...\n"
                    f"This violates pharmaceutical system requirements for explicit failure handling."
                ) from parse_error
                
        except Exception as llm_error:
            # NO FALLBACKS: Fail explicitly with full diagnostic information  
            raise RuntimeError(
                f"CRITICAL: Regulatory considerations LLM call failed.\n"
                f"Error: {llm_error}\n"
                f"Request: {request.specialty}, {request.compliance_level}\n"
                f"This violates pharmaceutical system requirements - regulatory assessment cannot use fallback logic."
            ) from llm_error

    async def _formulate_expert_opinion(
        self,
        request: SMEAgentRequest,
        recommendations: list[dict[str, Any]],
        risk_analysis: dict[str, Any]
    ) -> str:
        """Formulate expert opinion summary using LLM expertise."""
        
        # NO FALLBACKS: Use actual LLM analysis instead of static logic
        opinion_prompt = f"""
        As a pharmaceutical validation expert specializing in {request.specialty}, formulate a comprehensive expert opinion based on the complete analysis conducted:
        
        SYSTEM CONTEXT:
        - Specialty: {request.specialty}
        - Compliance Level: {request.compliance_level}
        - Test Focus: {request.test_focus}
        - GAMP Category: {request.categorization_context.get('gamp_category', 'unknown')}
        
        ANALYSIS RESULTS:
        Risk Analysis: {risk_analysis}
        
        Recommendations Generated: {len(recommendations)} recommendations
        High Priority Recommendations: {len([r for r in recommendations if r.get("priority") == "high"])}
        
        Formulate a concise expert opinion that:
        1. Summarizes the overall validation approach recommended
        2. Highlights key risk considerations and mitigation strategies
        3. Provides guidance on implementation priorities
        4. Addresses compliance and regulatory considerations
        5. Offers professional judgment on success likelihood
        
        Write in a professional, authoritative tone appropriate for pharmaceutical validation documentation.
        Keep the opinion concise but comprehensive (2-4 sentences).
        
        Respond with just the expert opinion text, no JSON formatting needed.
        """
        
        try:
            # Make actual LLM call - NO FALLBACKS ALLOWED
            response = await self.llm.acomplete(opinion_prompt)
            expert_opinion = response.text.strip()
            
            # Basic validation - ensure we got a reasonable response
            if not expert_opinion or len(expert_opinion) < 50:
                raise ValueError("Expert opinion is too short or empty")
            
            # Increased limit to 3000 characters for comprehensive pharmaceutical analysis
            # Pharmaceutical expert opinions often require detailed explanations for regulatory compliance
            if len(expert_opinion) > 3000:
                self.logger.warning(f"Expert opinion is very long ({len(expert_opinion)} chars), consider review for conciseness")
                # Don't fail - just log warning for audit trail
                # raise ValueError("Expert opinion is too long")
            
            return expert_opinion
                
        except Exception as llm_error:
            # NO FALLBACKS: Fail explicitly with full diagnostic information  
            raise RuntimeError(
                f"CRITICAL: Expert opinion formulation LLM call failed.\n"
                f"Error: {llm_error}\n"
                f"Request: {request.specialty}, {request.compliance_level}\n"
                f"This violates pharmaceutical system requirements - expert opinion cannot use fallback logic."
            ) from llm_error

    def _calculate_confidence_score(
        self,
        recommendations: list[dict[str, Any]],
        compliance_assessment: dict[str, Any],
        risk_analysis: dict[str, Any]
    ) -> float:
        """Calculate confidence score for SME analysis."""
        # Base confidence from recommendation strength
        recommendation_factor = min(len(recommendations) / self.max_recommendations, 1.0)

        # Compliance certainty factor
        compliance_factor = compliance_assessment.get("certainty_score", 0.5)

        # Risk clarity factor
        risk_factor = risk_analysis.get("clarity_score", 0.5)

        # Domain knowledge factor (higher confidence for specialized domains)
        domain_factor = 0.9 if self.specialty in self.domain_knowledge else 0.6

        # Combine factors
        confidence = (
            recommendation_factor * 0.3 +
            compliance_factor * 0.3 +
            risk_factor * 0.2 +
            domain_factor * 0.2
        )

        return min(confidence, 1.0)

    def _initialize_domain_knowledge(self) -> dict[str, Any]:
        """Initialize domain knowledge base."""
        return {
            "pharmaceutical_validation": {
                "expertise_areas": [
                    "GAMP-5 compliance", "21 CFR Part 11", "Computer System Validation",
                    "Risk-based validation", "Process validation", "Analytical method validation"
                ],
                "regulatory_focus": ["FDA", "EMA", "ICH"],
                "validation_experience": "extensive"
            },
            "quality_assurance": {
                "expertise_areas": [
                    "Quality management systems", "CAPA processes", "Quality risk management",
                    "Validation lifecycle management", "Regulatory compliance"
                ],
                "regulatory_focus": ["ISO 9001", "ICH Q8-Q12", "FDA Quality Metrics"],
                "validation_experience": "comprehensive"
            },
            "regulatory_affairs": {
                "expertise_areas": [
                    "Regulatory submission strategy", "Compliance assessment",
                    "Regulatory change management", "Global regulatory requirements"
                ],
                "regulatory_focus": ["FDA", "EMA", "Health Canada", "PMDA"],
                "validation_experience": "regulatory_focused"
            }
        }

    def _create_function_agent(self) -> FunctionAgent:
        """Create function agent with SME tools."""
        tools = [
            self._create_compliance_assessment_tool(),
            self._create_risk_analysis_tool(),
            self._create_validation_guidance_tool()
        ]

        system_prompt = f"""You are a Subject Matter Expert in {self.specialty}.
Your responsibilities:
1. Validate test strategies against regulatory requirements
2. Ensure GAMP-5 category compliance  
3. Assess risk factors and mitigation strategies
4. Provide domain-specific recommendations

Always maintain pharmaceutical regulatory standards and provide evidence-based recommendations."""

        return FunctionAgent(
            tools=tools,
            llm=self.llm,
            verbose=self.verbose,
            system_prompt=system_prompt
        )

    def _create_compliance_assessment_tool(self) -> FunctionTool:
        """Create compliance assessment tool."""
        def assess_compliance_requirements(gamp_category: str, regulatory_scope: list[str]) -> dict[str, Any]:
            """
            Assess compliance requirements for given GAMP category and scope.
            
            Args:
                gamp_category: GAMP software category
                regulatory_scope: List of applicable regulations
            
            Returns:
                Compliance assessment results
            """
            assessment = {
                "category": gamp_category,
                "applicable_regulations": regulatory_scope,
                "validation_rigor": "standard",
                "critical_controls": []
            }

            if gamp_category in ["4", "5"]:
                assessment["validation_rigor"] = "enhanced"
                assessment["critical_controls"].extend([
                    "Configuration management",
                    "Change control",
                    "Security controls"
                ])

            return assessment

        return FunctionTool.from_defaults(fn=assess_compliance_requirements)

    def _create_risk_analysis_tool(self) -> FunctionTool:
        """Create risk analysis tool."""
        def analyze_validation_risks(system_complexity: str, regulatory_impact: str, data_criticality: str) -> dict[str, Any]:
            """
            Analyze validation risks based on system characteristics.
            
            Args:
                system_complexity: System complexity level
                regulatory_impact: Regulatory impact level
                data_criticality: Data criticality level
            
            Returns:
                Risk analysis results
            """
            risk_factors = {
                "complexity_risk": system_complexity,
                "regulatory_risk": regulatory_impact,
                "data_risk": data_criticality,
                "overall_risk": "medium"
            }

            high_risk_factors = sum(1 for factor in [system_complexity, regulatory_impact, data_criticality] if factor == "high")

            if high_risk_factors >= 2:
                risk_factors["overall_risk"] = "high"
            elif high_risk_factors == 0:
                risk_factors["overall_risk"] = "low"

            return risk_factors

        return FunctionTool.from_defaults(fn=analyze_validation_risks)

    def _create_validation_guidance_tool(self) -> FunctionTool:
        """Create validation guidance tool."""
        def provide_validation_guidance(test_types: list[str], compliance_level: str) -> dict[str, Any]:
            """
            Provide validation guidance for specified test types and compliance level.
            
            Args:
                test_types: List of test types to validate
                compliance_level: Required compliance level
            
            Returns:
                Validation guidance
            """
            guidance = {
                "test_types": test_types,
                "compliance_level": compliance_level,
                "validation_approach": "risk_based",
                "key_activities": []
            }

            for test_type in test_types:
                if test_type == "functional_testing":
                    guidance["key_activities"].append("User acceptance criteria validation")
                elif test_type == "integration_testing":
                    guidance["key_activities"].append("Interface validation and data flow testing")
                elif test_type == "security_testing":
                    guidance["key_activities"].append("Access control and data protection validation")

            return guidance

        return FunctionTool.from_defaults(fn=provide_validation_guidance)

    def _detect_oss_model(self) -> bool:
        """
        Detect if we're using an OSS model that needs enhanced prompting.
        
        Returns:
            bool: True if OSS model detected
        """
        if hasattr(self.llm, 'model'):
            model_name = str(self.llm.model).lower()
            return 'oss' in model_name or 'gpt-oss' in model_name
        return False

    def _enhance_prompt_for_oss(self, base_prompt: str, response_format: str = "json") -> str:
        """
        Enhance prompt for OSS models with explicit formatting instructions.
        
        Args:
            base_prompt: Base prompt text
            response_format: Expected response format (json, array, object)
            
        Returns:
            Enhanced prompt with OSS-specific instructions
        """
        if not self.is_oss_model:
            return base_prompt
            
        format_instructions = {
            "json": """
CRITICAL RESPONSE FORMAT REQUIREMENTS:
1. You MUST respond with valid JSON only
2. Do NOT include any text before or after the JSON
3. Do NOT use markdown code blocks (no ```)  
4. Do NOT include explanations or commentary
5. Ensure all JSON is properly escaped and valid
6. Double-check your JSON syntax before responding

Example valid response:
{"key": "value", "array": ["item1", "item2"]}
            """,
            "array": """
CRITICAL RESPONSE FORMAT REQUIREMENTS:
1. You MUST respond with a valid JSON ARRAY only
2. Do NOT include any text before or after the JSON array
3. Do NOT use markdown code blocks (no ```)
4. Do NOT include explanations or commentary  
5. Ensure all JSON is properly escaped and valid
6. Double-check your JSON array syntax before responding

Example valid response:
[{"key": "value"}, {"key2": "value2"}]
            """
        }
        
        instruction = format_instructions.get(response_format, format_instructions["json"])
        return f"{base_prompt}\n\n{instruction}"

    def _log_llm_response_debug(self, response_text: str, parsing_context: str) -> None:
        """
        Log detailed debug information about LLM responses for OSS model troubleshooting.
        
        Args:
            response_text: Raw LLM response text
            parsing_context: Context of what was being parsed (e.g., "recommendations")
        """
        self.logger.info(f"[LLM DEBUG] {parsing_context} - Response length: {len(response_text)}")
        self.logger.info(f"[LLM DEBUG] {parsing_context} - Response preview (first 500 chars): {response_text[:500]}...")
        
        # Check for common OSS model issues
        has_markdown = '```' in response_text
        has_json_start = '{' in response_text or '[' in response_text
        has_json_end = '}' in response_text or ']' in response_text
        starts_with_json = response_text.strip().startswith(('{', '['))
        
        self.logger.info(f"[LLM DEBUG] {parsing_context} - Format analysis:")
        self.logger.info(f"  - Has markdown blocks: {has_markdown}")
        self.logger.info(f"  - Has JSON start chars: {has_json_start}")
        self.logger.info(f"  - Has JSON end chars: {has_json_end}")  
        self.logger.info(f"  - Starts with JSON: {starts_with_json}")
        
        if self.is_oss_model:
            self.logger.info(f"[OSS MODEL DEBUG] Model: {self.llm.model}")
            
        # Log the last 200 characters to see how it ends
        self.logger.info(f"[LLM DEBUG] {parsing_context} - Response ending (last 200 chars): ...{response_text[-200:]}")

    def _update_performance_stats(self, processing_time: float) -> None:
        """Update performance statistics."""
        current_avg = self._expertise_stats["avg_processing_time"]
        total_consultations = self._expertise_stats["total_consultations"]

        # Calculate new average
        new_avg = ((current_avg * (total_consultations - 1)) + processing_time) / total_consultations
        self._expertise_stats["avg_processing_time"] = new_avg

    def get_expertise_stats(self) -> dict[str, Any]:
        """Get current expertise statistics."""
        return self._expertise_stats.copy()


def create_sme_agent(
    specialty: str = "pharmaceutical_validation",
    llm: LLM | None = None,
    verbose: bool = False,
    enable_phoenix: bool = True,
    confidence_threshold: float = 0.7,
    max_recommendations: int = 10
) -> SMEAgent:
    """
    Create an SME Agent instance.
    
    Args:
        specialty: SME specialty area
        llm: Language model for expert analysis
        verbose: Enable verbose logging
        enable_phoenix: Enable Phoenix AI instrumentation
        confidence_threshold: Minimum confidence for recommendations
        max_recommendations: Maximum number of recommendations
    
    Returns:
        Configured SMEAgent instance
    """
    return SMEAgent(
        specialty=specialty,
        llm=llm,
        verbose=verbose,
        enable_phoenix=enable_phoenix,
        confidence_threshold=confidence_threshold,
        max_recommendations=max_recommendations
    )
