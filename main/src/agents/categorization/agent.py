"""
GAMP-5 Categorization Agent - LlamaIndex Implementation

This module provides the GAMP-5 categorization agent following LlamaIndex patterns.
Uses FunctionAgent with LLM intelligence and categorization tools.

Key Features:
- Comprehensive error handling with automatic Category 5 fallback
- Confidence scoring with configurable thresholds
- Full audit trail for regulatory compliance (21 CFR Part 11)
- Multiple categorization approaches (LLM chat or structured output)
- Support for all GAMP categories (1, 3, 4, 5)

Error Handling:
- Automatic detection of parsing, logic, ambiguity, and confidence errors
- Conservative fallback to Category 5 on any uncertainty
- Complete audit trail with decision rationale
- Integration ready for Phoenix observability

Usage:
    # Create agent with error handling
    agent = create_gamp_categorization_agent(
        enable_error_handling=True,
        confidence_threshold=0.60
    )
    
    # Categorize with structured output (recommended)
    result = categorize_with_structured_output(
        agent, urs_content, "document.urs"
    )

Based on the synthesis document and following the project's established agent patterns.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.llms import LLM
from llama_index.core.tools import FunctionTool
from src.agents.categorization.error_handler import (
    CategorizationError,
    CategorizationErrorHandler,
    ErrorSeverity,
    ErrorType,
)
from src.core.events import GAMPCategorizationEvent, GAMPCategory


class CategorizationAgentWrapper:
    """Wrapper to hold agent and error handler together."""

    def __init__(self, agent: FunctionAgent, error_handler: CategorizationErrorHandler | None = None):
        self.agent = agent
        self.error_handler = error_handler or CategorizationErrorHandler()

    def chat(self, *args, **kwargs):
        """Delegate chat to agent."""
        return self.agent.chat(*args, **kwargs)

    def __getattr__(self, name):
        """Delegate other attributes to agent."""
        return getattr(self.agent, name)


def gamp_analysis_tool(urs_content: str) -> dict[str, Any]:
    """
    Analyze URS content for GAMP categorization indicators.
    
    This tool implements the rules-based categorization logic from the synthesis document,
    analyzing URS content to identify indicators for each GAMP category.
    
    Args:
        urs_content: The URS document content as text
        
    Returns:
        Dictionary with categorization analysis including predicted category and evidence
    """
    # Normalize content for analysis
    normalized_content = urs_content.lower()
    normalized_content = " ".join(normalized_content.split())  # Remove extra whitespace

    # Category 1: Infrastructure Software
    category_1_indicators = {
        "strong_indicators": [
            "operating system", "windows server", "linux", "unix", "macos",
            "database engine", "oracle", "sql server", "mysql", "postgresql",
            "programming language", "java", "python", "c++", ".net framework",
            "network protocol", "tcp/ip", "http", "https", "ftp", "smtp",
            "middleware", "web server", "application server"
        ],
        "weak_indicators": [
            "infrastructure", "platform", "system software", "foundation",
            "runtime environment", "virtual machine"
        ],
        "exclusions": [
            "custom configuration", "business logic", "gxp-critical",
            "modified", "extended", "customized"
        ]
    }

    # Category 3: Non-Configured Products
    category_3_indicators = {
        "strong_indicators": [
            "commercial software", "standard package", "off-the-shelf",
            "cots", "vendor standard", "default configuration",
            "standard installation", "unmodified", "as supplied"
        ],
        "weak_indicators": [
            "basic instrument", "balance", "ph meter", "spectrophotometer",
            "microsoft office", "adobe acrobat", "standard functionality",
            "backup software", "antivirus"
        ],
        "exclusions": [
            "configuration", "customization", "modification", "user-defined",
            "workflow", "setup", "parameters"
        ]
    }

    # Category 4: Configured Products
    category_4_indicators = {
        "strong_indicators": [
            "configure", "configuration", "configurable", "user-defined parameters",
            "workflow configuration", "business rules setup", "system parameters",
            "user preferences", "setup wizard", "approval workflows"
        ],
        "weak_indicators": [
            "lims", "sample management", "test protocols", "result workflows",
            "erp", "business processes", "mes", "production workflows",
            "qms", "document workflows", "change control"
        ],
        "exclusions": [
            "custom development", "proprietary code", "bespoke", "programming"
        ]
    }

    # Category 5: Custom Applications
    category_5_indicators = {
        "strong_indicators": [
            "custom development", "bespoke solution", "proprietary algorithm",
            "custom calculations", "tailored functionality", "purpose-built",
            "custom integration", "unique business logic", "custom code"
        ],
        "weak_indicators": [
            "algorithm development", "custom data models", "proprietary methods",
            "specialized calculations", "custom interfaces", "ai/ml implementation",
            "novel functionality", "custom reporting engine"
        ],
        "exclusions": []  # Category 5 has no exclusions
    }

    # Analyze each category
    categories_analysis = {}
    for category, indicators in [
        (GAMPCategory.CATEGORY_1, category_1_indicators),
        (GAMPCategory.CATEGORY_3, category_3_indicators),
        (GAMPCategory.CATEGORY_4, category_4_indicators),
        (GAMPCategory.CATEGORY_5, category_5_indicators)
    ]:
        strong_matches = [ind for ind in indicators["strong_indicators"] if ind in normalized_content]
        weak_matches = [ind for ind in indicators["weak_indicators"] if ind in normalized_content]
        exclusions = [exc for exc in indicators["exclusions"] if exc in normalized_content]

        categories_analysis[category.value] = {
            "strong_indicators": strong_matches,
            "weak_indicators": weak_matches,
            "exclusion_factors": exclusions,
            "strong_count": len(strong_matches),
            "weak_count": len(weak_matches),
            "exclusion_count": len(exclusions)
        }

    # Apply decision logic (following synthesis document decision tree)
    # 1. Infrastructure components only? → Category 1
    cat1_analysis = categories_analysis[1]
    if cat1_analysis["strong_count"] > 0 and cat1_analysis["exclusion_count"] == 0:
        predicted_category = GAMPCategory.CATEGORY_1
        evidence = cat1_analysis
    # 2. Custom development required? → Category 5
    elif categories_analysis[5]["strong_count"] > 0:
        predicted_category = GAMPCategory.CATEGORY_5
        evidence = categories_analysis[5]
    # 3. Configuration required? → Category 4
    elif categories_analysis[4]["strong_count"] > 0 and categories_analysis[4]["exclusion_count"] == 0:
        predicted_category = GAMPCategory.CATEGORY_4
        evidence = categories_analysis[4]
    # 4. Otherwise → Category 3
    else:
        predicted_category = GAMPCategory.CATEGORY_3
        evidence = categories_analysis[3]

    return {
        "predicted_category": predicted_category.value,
        "evidence": evidence,
        "all_categories_analysis": categories_analysis,
        "decision_rationale": f"Category {predicted_category.value} selected based on {evidence['strong_count']} strong indicators"
    }


def confidence_tool(category_data: dict[str, Any]) -> float:
    """
    Calculate confidence score for categorization decision.
    
    Based on the confidence scoring algorithm from the synthesis document.
    
    Args:
        category_data: Output from gamp_analysis_tool
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    evidence = category_data["evidence"]
    all_analysis = category_data["all_categories_analysis"]

    # Base scoring weights
    weights = {
        "strong_indicators": 0.4,
        "weak_indicators": 0.2,
        "exclusion_factors": -0.3,
        "ambiguity_penalty": -0.1
    }

    # Calculate base score
    base_score = (
        weights["strong_indicators"] * evidence["strong_count"] +
        weights["weak_indicators"] * evidence["weak_count"] +
        weights["exclusion_factors"] * evidence["exclusion_count"]
    )

    # Calculate ambiguity penalty (other categories with strong indicators)
    predicted_category = category_data["predicted_category"]
    competing_strong_indicators = sum(
        analysis["strong_count"] for cat_id, analysis in all_analysis.items()
        if cat_id != predicted_category and analysis["strong_count"] > 0
    )

    ambiguity_penalty = 0.0
    if competing_strong_indicators > 0:
        penalty_factor = min(competing_strong_indicators * 0.1, 0.3)
        ambiguity_penalty = weights["ambiguity_penalty"] * penalty_factor

    # Category-specific adjustments
    category_adjustment = 0.0
    if predicted_category == 1 and evidence["strong_count"] >= 2:  # Category 1
        category_adjustment = 0.1
    elif predicted_category == 5 and evidence["strong_count"] >= 2:  # Category 5
        category_adjustment = 0.15
    elif predicted_category in [3, 4] and evidence["strong_count"] >= 1:
        category_adjustment = 0.05

    # Final confidence calculation
    raw_confidence = base_score + ambiguity_penalty + category_adjustment
    final_confidence = max(0.0, min(1.0, 0.5 + raw_confidence))

    return final_confidence


def gamp_analysis_tool_with_error_handling(
    urs_content: str,
    error_handler: CategorizationErrorHandler | None = None
) -> dict[str, Any]:
    """
    Enhanced GAMP analysis tool with error handling.
    
    Wraps the original tool with comprehensive error detection and recovery.
    """
    if error_handler is None:
        # Use default error handler if none provided
        error_handler = CategorizationErrorHandler()

    try:
        # Validate input
        if not urs_content or not isinstance(urs_content, str):
            raise ValueError("Invalid URS content: must be non-empty string")

        if len(urs_content.strip()) < 10:
            raise ValueError("URS content too short for meaningful analysis")

        # Call original analysis tool
        result = gamp_analysis_tool(urs_content)

        # Validate result
        validation_error = error_handler.validate_categorization_result(result)
        if validation_error:
            raise RuntimeError(f"Validation failed: {validation_error.message}")

        return result

    except Exception as e:
        # Let error handler create appropriate response
        error_event = error_handler.handle_tool_error(
            tool_name="gamp_analysis_tool",
            exception=e,
            tool_input=urs_content[:200] if urs_content else "Empty",
            document_name="Analysis Input"
        )

        # Return error result that indicates fallback
        return {
            "predicted_category": 5,
            "evidence": {"error": str(e)},
            "all_categories_analysis": {},
            "decision_rationale": f"Error during analysis: {e!s}. Fallback to Category 5.",
            "error": True
        }


def confidence_tool_with_error_handling(
    category_data: dict[str, Any],
    error_handler: CategorizationErrorHandler | None = None
) -> float:
    """
    Enhanced confidence tool with error handling.
    
    Wraps the original tool with error detection and fallback.
    """
    if error_handler is None:
        error_handler = CategorizationErrorHandler()

    try:
        # Check if this is an error result
        if category_data.get("error", False):
            return 0.0

        # Validate input
        if not isinstance(category_data, dict):
            raise ValueError("Invalid category data: must be dictionary")

        required_fields = ["predicted_category", "evidence", "all_categories_analysis"]
        missing_fields = [f for f in required_fields if f not in category_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Call original confidence tool
        confidence = confidence_tool(category_data)

        # Check for ambiguity
        all_analysis = category_data.get("all_categories_analysis", {})
        confidence_scores = {}

        for cat_id, analysis in all_analysis.items():
            # Simple confidence calculation for each category
            cat_confidence = (
                0.4 * analysis.get("strong_count", 0) +
                0.2 * analysis.get("weak_count", 0) -
                0.3 * analysis.get("exclusion_count", 0)
            )
            confidence_scores[int(cat_id)] = max(0.0, min(1.0, 0.5 + cat_confidence))

        ambiguity_error = error_handler.check_ambiguity(category_data, confidence_scores)
        if ambiguity_error:
            # Log the ambiguity but don't fail - let low confidence handle it
            error_handler.logger.warning(f"Ambiguity detected: {ambiguity_error.message}")

        return confidence

    except Exception as e:
        error_handler.logger.error(f"Confidence calculation error: {e!s}")
        return 0.0  # Return zero confidence on error


def create_gamp_categorization_agent(
    llm: LLM = None,
    enable_error_handling: bool = True,
    confidence_threshold: float = 0.60,
    verbose: bool = False
) -> FunctionAgent:
    """
    Create GAMP-5 categorization agent with enhanced error handling.
    
    This factory function creates a FunctionAgent with LLM intelligence, GAMP
    categorization tools, and comprehensive error handling capabilities.
    
    Args:
        llm: Optional LLM instance. If not provided, uses default from project config
        enable_error_handling: Whether to enable comprehensive error handling
        confidence_threshold: Minimum confidence threshold for categorization
        verbose: Enable verbose logging
        
    Returns:
        FunctionAgent configured for GAMP-5 categorization with error handling
    """
    if llm is None:
        # Use OpenAI LLM without JSON mode for FunctionAgent compatibility

        from llama_index.llms.openai import OpenAI
        llm = OpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=2000
            # JSON mode NOT used - FunctionAgent requires natural language responses
        )

    # Create error handler if enabled
    error_handler = None
    if enable_error_handling:
        error_handler = CategorizationErrorHandler(
            confidence_threshold=confidence_threshold,
            verbose=verbose
        )

    # Create function tools with or without error handling
    if enable_error_handling and error_handler:
        # Create wrapped tools with error handling
        def gamp_tool_wrapper(urs_content: str) -> dict[str, Any]:
            return gamp_analysis_tool_with_error_handling(urs_content, error_handler)

        def confidence_tool_wrapper(category_data: dict[str, Any]) -> float:
            return confidence_tool_with_error_handling(category_data, error_handler)

        gamp_analysis_function_tool = FunctionTool.from_defaults(
            fn=gamp_tool_wrapper,
            name="gamp_analysis_tool",
            description="Analyze URS content for GAMP categorization with error handling"
        )

        confidence_function_tool = FunctionTool.from_defaults(
            fn=confidence_tool_wrapper,
            name="confidence_tool",
            description="Calculate confidence score with error detection"
        )
    else:
        # Use original tools without error handling
        gamp_analysis_function_tool = FunctionTool.from_defaults(
            fn=gamp_analysis_tool,
            name="gamp_analysis_tool",
            description="Analyze URS content for GAMP categorization indicators"
        )

        confidence_function_tool = FunctionTool.from_defaults(
            fn=confidence_tool,
            name="confidence_tool",
            description="Calculate confidence score for categorization decision"
        )

    # Enhanced system prompt with error handling guidance
    system_prompt = """You are a GAMP-5 categorization expert. Analyze URS documents and determine the GAMP category.

Categories:
- Category 1: Infrastructure (OS, databases, middleware)
- Category 3: Non-configured COTS (used as supplied)
- Category 4: Configured products (user parameters)
- Category 5: Custom applications (bespoke code)

Process:
1. Use gamp_analysis_tool to analyze the content
2. Use confidence_tool to get confidence score
3. Provide clear categorization with justification

Error Handling:
- If analysis fails or confidence is below 60%, Category 5 will be assigned
- All errors are logged for regulatory compliance
- Low confidence results require human review

Provide the category number, confidence score, and brief explanation."""

    agent = FunctionAgent(
        tools=[gamp_analysis_function_tool, confidence_function_tool],
        llm=llm,
        verbose=verbose,
        max_iterations=10,  # Reduced from default 20 to prevent timeouts
        system_prompt=system_prompt
    )

    # Return wrapper if error handling is enabled
    if enable_error_handling and error_handler:
        return CategorizationAgentWrapper(agent, error_handler)

    return agent


def create_categorization_event(
    categorization_result: dict[str, Any],
    confidence_score: float,
    document_name: str = "Unknown",
    categorized_by: str = "GAMPCategorizationAgent"
) -> GAMPCategorizationEvent:
    """
    Create GAMPCategorizationEvent from analysis results.
    
    Helper function to convert agent output into proper event format.
    
    Args:
        categorization_result: Output from gamp_analysis_tool
        confidence_score: Output from confidence_tool
        document_name: Name of analyzed document
        categorized_by: Identifier of categorizing agent
        
    Returns:
        GAMPCategorizationEvent for workflow integration
    """
    predicted_category = GAMPCategory(categorization_result["predicted_category"])
    evidence = categorization_result["evidence"]

    # Generate comprehensive justification
    justification_parts = [
        f"GAMP-5 Categorization Analysis for '{document_name}'",
        "",
        f"CLASSIFICATION: Category {predicted_category.value}",
        f"CONFIDENCE: {confidence_score:.1%}",
        "",
        "EVIDENCE ANALYSIS:",
    ]

    if evidence["strong_indicators"]:
        justification_parts.append(f"✓ Strong Indicators ({evidence['strong_count']}): {', '.join(evidence['strong_indicators'][:5])}")

    if evidence["weak_indicators"]:
        justification_parts.append(f"○ Supporting Indicators ({evidence['weak_count']}): {', '.join(evidence['weak_indicators'][:3])}")

    if evidence["exclusion_factors"]:
        justification_parts.append(f"⚠ Exclusion Factors ({evidence['exclusion_count']}): {', '.join(evidence['exclusion_factors'])}")

    justification_parts.append("")
    justification_parts.append(f"DECISION RATIONALE: {categorization_result['decision_rationale']}")

    requires_review = confidence_score < 0.85
    if requires_review:
        justification_parts.extend([
            "",
            "⚠️ HUMAN REVIEW REQUIRED",
            "Confidence below threshold (85%) - Expert review needed for regulatory compliance"
        ])

    # Build risk assessment
    risk_assessment = {
        "category": predicted_category.value,
        "category_description": _get_category_description(predicted_category),
        "validation_approach": _get_validation_approach(predicted_category),
        "confidence_score": confidence_score,
        "evidence_strength": _assess_evidence_strength(evidence),
        "requires_human_review": requires_review,
        "regulatory_impact": _assess_regulatory_impact(predicted_category),
        "validation_effort": _estimate_validation_effort(predicted_category)
    }

    return GAMPCategorizationEvent(
        gamp_category=predicted_category,
        confidence_score=confidence_score,
        justification="\n".join(justification_parts),
        risk_assessment=risk_assessment,
        event_id=uuid4(),
        timestamp=datetime.now(UTC),
        categorized_by=categorized_by,
        review_required=requires_review
    )


def _get_category_description(category: GAMPCategory) -> str:
    """Get human-readable description of a GAMP category."""
    descriptions = {
        GAMPCategory.CATEGORY_1: "Infrastructure software - Operating systems, databases, middleware",
        GAMPCategory.CATEGORY_3: "Non-configured products - COTS software used as supplied",
        GAMPCategory.CATEGORY_4: "Configured products - Commercial software requiring configuration",
        GAMPCategory.CATEGORY_5: "Custom applications - Bespoke software development"
    }
    return descriptions.get(category, "Unknown category")


def _get_validation_approach(category: GAMPCategory) -> str:
    """Get recommended validation approach for a GAMP category."""
    approaches = {
        GAMPCategory.CATEGORY_1: "Installation Qualification (IQ) and operational procedures",
        GAMPCategory.CATEGORY_3: "Operational Qualification (OQ) of standard functions",
        GAMPCategory.CATEGORY_4: "Configuration verification and business process testing",
        GAMPCategory.CATEGORY_5: "Full software development lifecycle (GAMP V-model)"
    }
    return approaches.get(category, "Contact validation expert")


def _assess_evidence_strength(evidence: dict[str, Any]) -> str:
    """Assess overall strength of evidence."""
    strong_count = evidence["strong_count"]
    exclusion_count = evidence["exclusion_count"]

    if strong_count >= 3 and exclusion_count == 0:
        return "Strong"
    if strong_count >= 2 and exclusion_count <= 1:
        return "Moderate"
    if strong_count >= 1:
        return "Weak"
    return "Insufficient"


def _assess_regulatory_impact(category: GAMPCategory) -> str:
    """Assess regulatory impact based on GAMP category."""
    impact_mapping = {
        GAMPCategory.CATEGORY_1: "Low - Infrastructure components with minimal GxP impact",
        GAMPCategory.CATEGORY_3: "Low-Medium - Standard applications with defined validation approach",
        GAMPCategory.CATEGORY_4: "Medium-High - Configured systems requiring thorough validation",
        GAMPCategory.CATEGORY_5: "High - Custom applications requiring comprehensive lifecycle validation"
    }
    return impact_mapping.get(category, "Unknown impact - review required")


def _estimate_validation_effort(category: GAMPCategory) -> str:
    """Estimate relative validation effort based on GAMP category."""
    effort_mapping = {
        GAMPCategory.CATEGORY_1: "5-10% of total project effort - Installation and operational focus",
        GAMPCategory.CATEGORY_3: "15-25% of total project effort - Functional verification",
        GAMPCategory.CATEGORY_4: "40-60% of total project effort - Configuration and business process testing",
        GAMPCategory.CATEGORY_5: "70-90% of total project effort - Full SDLC documentation and testing"
    }
    return effort_mapping.get(category, "Effort unknown - expert consultation required")


def categorize_with_structured_output(
    agent: FunctionAgent,
    urs_content: str,
    document_name: str = "Unknown"
) -> GAMPCategorizationEvent:
    """
    Categorize URS using tools directly for structured output.
    
    This approach bypasses LLM chat parsing by using tools directly,
    providing more reliable structured results.
    """
    error_handler = getattr(agent, "error_handler", None)
    if error_handler is None:
        error_handler = CategorizationErrorHandler()

    try:
        # Step 1: Run GAMP analysis tool
        analysis_result = gamp_analysis_tool_with_error_handling(
            urs_content, error_handler
        )

        # Check for tool error
        if analysis_result.get("error", False):
            return error_handler.handle_tool_error(
                "gamp_analysis_tool",
                Exception(analysis_result.get("decision_rationale", "Tool error")),
                urs_content[:200],
                document_name
            )

        # Step 2: Calculate confidence
        confidence = confidence_tool_with_error_handling(
            analysis_result, error_handler
        )

        # Step 3: Check confidence threshold
        if confidence < error_handler.confidence_threshold:
            error = CategorizationError(
                error_type=ErrorType.CONFIDENCE_ERROR,
                severity=ErrorSeverity.MEDIUM,
                message=f"Confidence {confidence:.2f} below threshold {error_handler.confidence_threshold}",
                details={
                    "confidence": confidence,
                    "threshold": error_handler.confidence_threshold,
                    "category": analysis_result["predicted_category"]
                }
            )
            return error_handler._create_fallback_event(error, document_name)

        # Step 4: Create successful event
        return create_categorization_event(
            analysis_result,
            confidence,
            document_name,
            "GAMPCategorizationAgent"
        )

    except Exception as e:
        # Handle any unexpected errors
        return error_handler.handle_llm_error(e, urs_content[:500], document_name)


def categorize_with_error_handling(
    agent: FunctionAgent,
    urs_content: str,
    document_name: str = "Unknown",
    max_retries: int = 1
) -> GAMPCategorizationEvent:
    """
    Categorize URS content with comprehensive error handling.
    
    This wrapper function provides end-to-end error handling for the categorization
    process, ensuring fallback to Category 5 on any failure.
    
    Args:
        agent: The GAMP categorization agent
        urs_content: URS document content
        document_name: Document identifier for logging
        max_retries: Maximum retry attempts on failure
        
    Returns:
        GAMPCategorizationEvent with categorization or fallback result
    """
    # Get error handler from agent or create default
    error_handler = getattr(agent, "error_handler", None)
    if error_handler is None:
        error_handler = CategorizationErrorHandler()

    retry_count = 0
    last_error = None

    while retry_count <= max_retries:
        try:
            # Validate input
            if not urs_content or not isinstance(urs_content, str):
                raise ValueError("Invalid URS content: must be non-empty string")

            # Run agent query
            response = agent.chat(f"Analyze this URS document and categorize it:\n\n{urs_content}")

            # Parse response to extract category and confidence
            response_text = str(response)

            # Extract category number (look for patterns like "Category 1", "Category: 1", etc.)
            import re
            category_match = re.search(r"[Cc]ategory[\s:]*(\d)", response_text)
            if not category_match:
                raise ValueError("Could not extract category from agent response")

            category_num = int(category_match.group(1))
            if category_num not in [1, 3, 4, 5]:
                raise ValueError(f"Invalid category number: {category_num}")

            # Extract confidence (look for patterns like "85%", "0.85", "confidence: 0.85")
            confidence_match = re.search(r"(\d+(?:\.\d+)?)\s*%|confidence[\s:]*(\d+(?:\.\d+)?)", response_text, re.IGNORECASE)
            if confidence_match:
                if confidence_match.group(1):  # Percentage format
                    confidence = float(confidence_match.group(1)) / 100
                else:  # Decimal format
                    confidence = float(confidence_match.group(2))
            else:
                # If no confidence found, use a default based on response
                confidence = 0.7  # Default moderate confidence

            # Check confidence threshold
            if confidence < error_handler.confidence_threshold:
                error = CategorizationError(
                    error_type=ErrorType.CONFIDENCE_ERROR,
                    severity=ErrorSeverity.MEDIUM,
                    message=f"Confidence {confidence:.2f} below threshold {error_handler.confidence_threshold}",
                    details={
                        "confidence": confidence,
                        "threshold": error_handler.confidence_threshold,
                        "category": category_num
                    }
                )
                return error_handler._create_fallback_event(error, document_name)

            # Create successful event
            return GAMPCategorizationEvent(
                gamp_category=GAMPCategory(category_num),
                confidence_score=confidence,
                justification=response_text,
                risk_assessment={
                    "category": category_num,
                    "category_description": _get_category_description(GAMPCategory(category_num)),
                    "validation_approach": _get_validation_approach(GAMPCategory(category_num)),
                    "confidence_score": confidence,
                    "evidence_strength": "Agent-based analysis",
                    "requires_human_review": confidence < 0.85,
                    "regulatory_impact": _assess_regulatory_impact(GAMPCategory(category_num)),
                    "validation_effort": _estimate_validation_effort(GAMPCategory(category_num))
                },
                event_id=uuid4(),
                timestamp=datetime.now(UTC),
                categorized_by="GAMPCategorizationAgent",
                review_required=confidence < 0.85
            )

        except Exception as e:
            last_error = e
            retry_count += 1

            if retry_count <= max_retries:
                error_handler.logger.warning(f"Categorization attempt {retry_count} failed: {e!s}. Retrying...")
                continue
            # Max retries exceeded, create fallback
            if isinstance(e, ValueError) and "URS content" in str(e):
                return error_handler.handle_parsing_error(e, urs_content, document_name)
            return error_handler.handle_llm_error(e, urs_content[:500], document_name)

    # Should not reach here, but if it does, create fallback
    return error_handler.handle_logic_error(
        {"message": "Unexpected error in categorization loop", "last_error": str(last_error)},
        document_name
    )
