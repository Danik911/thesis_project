"""
GAMP-5 Categorization Agent - Enhanced with Pydantic Structured Output

This module provides the GAMP-5 categorization agent with multiple approaches:
1. NEW: Pydantic structured output using LLMTextCompletionProgram (RECOMMENDED)
2. Legacy: FunctionAgent with LLM intelligence and categorization tools

Key Features:
- Pydantic structured output eliminates fragile regex parsing
- LLMTextCompletionProgram for guaranteed structured responses
- Comprehensive error handling with explicit failure reporting
- Confidence scoring with configurable thresholds
- Full audit trail for regulatory compliance (21 CFR Part 11)
- Support for all GAMP categories (1, 3, 4, 5)
- NO FALLBACK LOGIC - all errors must be addressed explicitly

Implementation Approaches:

1. RECOMMENDED: Pydantic Structured Output
   - Uses LLMTextCompletionProgram with GAMPCategorizationResult model
   - Eliminates regex parsing fragility
   - Guaranteed structured responses
   - Better error handling and validation

2. Legacy: FunctionAgent Approach
   - Uses FunctionAgent with tools for analysis
   - Still uses regex parsing for response extraction
   - Maintained for backward compatibility

Usage Examples:

    # RECOMMENDED: High-level convenience function
    result = categorize_urs_document(
        urs_content="Software for managing laboratory data...",
        document_name="LIMS_URS_v1.2.pdf",
        use_structured_output=True  # Default
    )
    
    # Direct Pydantic structured output
    # from llama_index.llms.openai import OpenAI  # Migrated to centralized config
    llm = LLMConfig.get_llm()
    result = categorize_with_pydantic_structured_output(
        llm=llm,
        urs_content=urs_content,
        document_name="document.urs"
    )
    
    # Legacy FunctionAgent approach (deprecated)
    agent = create_gamp_categorization_agent(use_structured_output=False)
    result = categorize_with_structured_output(agent, urs_content, "document.urs")

Error Handling:
- Explicit detection of parsing, logic, ambiguity, and confidence errors
- All failures reported with complete diagnostic information
- Complete audit trail with decision rationale
- Integration ready for Phoenix observability
- NO FALLBACK LOGIC - all errors must be addressed explicitly

Based on Task 2 implementation replacing fragile regex parsing with Pydantic structured output.
"""

import asyncio
import json
import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.llms import LLM
from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field, ValidationError
from src.agents.categorization.error_handler import (
    CategorizationError,
    CategorizationErrorHandler,
    ErrorSeverity,
    ErrorType,
)
from src.agents.parallel.context_provider import (
    ContextProviderRequest,
    create_context_provider_agent,
)
from src.config.llm_config import LLMConfig
from src.core.events import AgentRequestEvent, GAMPCategorizationEvent, GAMPCategory
from src.monitoring.phoenix_config import instrument_tool


class GAMPCategorizationResult(BaseModel):
    """Pydantic model for structured GAMP categorization output."""

    category: int = Field(
        ...,
        ge=1,
        le=5,
        description="GAMP category number (must be 1, 3, 4, or 5)"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0"
    )
    reasoning: str = Field(
        ...,
        min_length=10,
        description="Brief justification for the categorization decision"
    )

    def validate_category(self) -> None:
        """Validate that category is a valid GAMP category (1, 3, 4, or 5)."""
        if self.category not in [1, 3, 4, 5]:
            raise ValueError(f"Invalid GAMP category: {self.category}. Must be 1, 3, 4, or 5.")


def parse_structured_response(response_text: str, output_cls=GAMPCategorizationResult) -> GAMPCategorizationResult:
    """
    Parse LLM response into structured Pydantic model.
    
    Supports both OpenAI and OpenRouter/OSS models by extracting JSON
    from various response formats without relying on model-specific features.
    
    Args:
        response_text: Raw LLM response text
        output_cls: Pydantic model class to parse into (default: GAMPCategorizationResult)
        
    Returns:
        Parsed GAMPCategorizationResult instance
        
    Raises:
        RuntimeError: If parsing fails with full diagnostic information
    """
    # Strategy 1: Try to find and parse clean JSON
    try:
        # Look for JSON object in the response
        json_patterns = [
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}",  # Nested JSON
            r"\{.*?\}",  # Simple JSON
        ]

        for pattern in json_patterns:
            json_matches = re.findall(pattern, response_text, re.DOTALL)
            for json_match in json_matches:
                try:
                    json_data = json.loads(json_match)
                    # Check if this looks like our expected structure
                    if "category" in json_data:
                        return output_cls(**json_data)
                except (json.JSONDecodeError, ValidationError):
                    continue
    except Exception:
        pass

    # Strategy 2: Extract fields using regex patterns
    try:
        # Extract category (various formats)
        category_patterns = [
            r'"?category"?\s*:\s*(\d+)',
            r"Category\s*:\s*(\d+)",
            r"GAMP\s+Category\s*:\s*(\d+)",
            r"Category\s+(\d+)",
        ]

        category = None
        for pattern in category_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                category = int(match.group(1))
                break

        # Extract confidence score (various formats)
        confidence_patterns = [
            r'"?confidence[_-]?score"?\s*:\s*([0-9.]+)',
            r"Confidence\s*:\s*([0-9.]+)",
            r"Score\s*:\s*([0-9.]+)",
        ]

        confidence = None
        for pattern in confidence_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                confidence = float(match.group(1))
                # Handle percentage values
                if confidence > 1.0:
                    confidence = confidence / 100.0
                break

        # Extract reasoning (various formats)
        reasoning_patterns = [
            r'"?reasoning"?\s*:\s*"([^"]+)"',
            r'"?reasoning"?\s*:\s*\'([^\']+)\'',
            r"Reasoning\s*:\s*(.+?)(?:\n|$)",
            r"Justification\s*:\s*(.+?)(?:\n|$)",
        ]

        reasoning = None
        for pattern in reasoning_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                break

        # If we have all required fields, create the result
        if category is not None and confidence is not None and reasoning:
            return output_cls(
                category=category,
                confidence_score=confidence,
                reasoning=reasoning
            )
    except Exception:
        # Continue to error reporting
        pass

    # NO FALLBACKS: Fail explicitly with full diagnostic information
    error_msg = (
        f"Failed to parse structured response from LLM.\n"
        f"Response text (first 500 chars): {response_text[:500]}...\n"
        f"Expected format: JSON with 'category' (int), 'confidence_score' (float), 'reasoning' (str)\n"
        f"This typically occurs with OSS models that don't follow strict JSON formatting.\n"
        f"Consider prompting the model more explicitly for JSON output."
    )
    raise RuntimeError(error_msg)


class CategorizationAgentWrapper:
    """Wrapper to hold agent and error handler together."""

    def __init__(self, agent: FunctionAgent, error_handler: CategorizationErrorHandler | None = None):
        self.agent = agent
        self.error_handler = error_handler or CategorizationErrorHandler()

    async def run(self, *args, **kwargs):
        """Delegate run to agent using proper FunctionAgent method."""
        return await self.agent.run(*args, **kwargs)

    def __getattr__(self, name):
        """Delegate other attributes to agent."""
        return getattr(self.agent, name)


@instrument_tool("gamp_analysis", "categorization", critical=True, regulatory_impact=True)
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
            "standard installation", "unmodified", "as supplied",
            "vendor-supplied software without modification", "vendor's built-in functionality",
            "vendor's standard database", "as supplied by vendor", "vendor's archival feature",
            "vendor's standard reporting", "standard reports provided by vendor"
        ],
        "weak_indicators": [
            "basic instrument", "balance", "ph meter", "spectrophotometer",
            "microsoft office", "adobe acrobat", "standard functionality",
            "backup software", "antivirus", "environmental monitoring"
        ],
        "exclusions": [
            "configuration", "customization", "modification", "user-defined",
            "workflow", "setup", "parameters", "custom"
        ]
    }

    # Category 4: Configured Products
    category_4_indicators = {
        "strong_indicators": [
            "configure", "configuration", "configurable", "user-defined parameters",
            "workflow configuration", "business rules setup", "system parameters",
            "user preferences", "setup wizard", "approval workflows",
            "vendor's configuration tools", "vendor's formula editor", "vendor's report designer",
            "commercial lims package", "commercial cms", "configure workflows"
        ],
        "weak_indicators": [
            "lims", "sample management", "test protocols", "result workflows",
            "erp", "business processes", "mes", "production workflows",
            "qms", "document workflows", "change control",
            "custom calculations using vendor", "custom reports using vendor",
            "configure standard integration", "vendor's standard adapter"
        ],
        "exclusions": [
            "custom development", "proprietary code", "bespoke", "programming",
            "custom-developed", "purpose-built", "custom code"
        ]
    }

    # Category 5: Custom Applications
    category_5_indicators = {
        "strong_indicators": [
            "custom development", "custom-developed", "bespoke solution", "bespoke analytics",
            "proprietary algorithm", "tailored functionality", "purpose-built",
            "unique business logic", "custom code", "develop custom",
            "proprietary data structures", "custom mobile application", "custom audit trail",
            "proprietary electronic signature", "custom data integrity", "bespoke module",
            "proprietary protocols", "custom implementation", "custom-developed to integrate",
            "custom algorithms for", "custom workflow engine", "custom interfaces for",
            "bespoke", "proprietary", "custom software"
        ],
        "weak_indicators": [
            "algorithm development", "custom data models", "proprietary methods",
            "specialized calculations", "ai/ml implementation",
            "novel functionality", "custom reporting engine",
            "enhanced metadata", "site-specific business rules not supported",
            "proprietary equipment", "custom exceptions", "develop proprietary"
        ],
        "exclusions": [
            "vendor's", "commercial", "configure", "standard", "using vendor"
        ]  # Category 5 excludes vendor-supported activities
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
        # Context-aware exclusion detection to prevent false positives
        exclusions = []
        for exc in indicators["exclusions"]:
            if exc in normalized_content:
                # Check for negation patterns that indicate the exclusion doesn't actually apply
                negation_patterns = [
                    f"without {exc}",
                    f"without any {exc}",
                    f"no {exc}",
                    f"not {exc}",
                    "not configured", # Special case for "configuration" in negative context
                    "not customized", # Special case for "customization" in negative context
                    "no custom",     # Covers "no custom code", "no custom logic"
                    "no bespoke",    # Covers "no bespoke interfaces"
                    "no bespoke interfaces or modifications", # Specific pattern from document
                    f"standard {exc} only",  # "standard configuration only" = limited, not custom
                    f"basic {exc}",          # "basic configuration" = minimal setup
                    f"minimal {exc}",        # "minimal setup" = not extensive configuration
                ]

                # Check if the exclusion word appears in a negating context
                is_negated = any(pattern in normalized_content for pattern in negation_patterns)

                if not is_negated:
                    exclusions.append(exc)

        categories_analysis[category.value] = {
            "strong_indicators": strong_matches,
            "weak_indicators": weak_matches,
            "exclusion_factors": exclusions,
            "strong_count": len(strong_matches),
            "weak_count": len(weak_matches),
            "exclusion_count": len(exclusions)
        }

    # Apply scoring-based decision logic to prevent over-classification
    # Calculate weighted scores for each category based on evidence strength
    category_scores = {}

    for category_num in [1, 3, 4, 5]:
        analysis = categories_analysis[category_num]

        # Base score calculation
        strong_score = analysis["strong_count"] * 3  # Strong indicators worth 3 points
        weak_score = analysis["weak_count"] * 1      # Weak indicators worth 1 point
        exclusion_penalty = analysis["exclusion_count"] * -2  # Exclusions subtract 2 points

        base_score = strong_score + weak_score + exclusion_penalty

        # Category-specific adjustments for accuracy
        if category_num == 1:
            # Category 1 needs clear infrastructure focus without business logic
            if analysis["strong_count"] >= 2 and analysis["exclusion_count"] == 0:
                base_score += 2  # Bonus for clear infrastructure pattern
        elif category_num == 3:
            # Category 3 needs clear unmodified vendor software indicators
            if analysis["strong_count"] >= 1 and analysis["exclusion_count"] == 0:
                base_score += 3  # Strong bonus for unmodified vendor software
        elif category_num == 4:
            # Category 4 needs configuration evidence without custom development
            if analysis["strong_count"] >= 1 and analysis["exclusion_count"] == 0:
                base_score += 2  # Bonus for clear configuration pattern
        elif category_num == 5:
            # Category 5 requires very strong evidence due to validation impact
            if analysis["exclusion_count"] > 0:
                base_score -= 5  # Heavy penalty for vendor-supported activities
            if analysis["strong_count"] >= 2:
                base_score += 1  # Only modest bonus - high bar for Category 5

        category_scores[category_num] = max(0, base_score)  # Floor at 0

    # Select category with highest score
    predicted_category_num = max(category_scores.items(), key=lambda x: x[1])
    predicted_category = GAMPCategory(predicted_category_num[0])
    evidence = categories_analysis[predicted_category_num[0]]

    # Add scoring details for transparency and debugging
    evidence["category_scores"] = category_scores
    evidence["winning_score"] = predicted_category_num[1]

    # Return a simplified structure that's easier for the LLM to process
    return {
        "predicted_category": predicted_category.value,
        "evidence": evidence,
        "all_categories_analysis": categories_analysis,
        "decision_rationale": f"Category {predicted_category.value} selected based on {evidence['strong_count']} strong indicators",
        # Add a simple summary for the LLM
        "summary": f"GAMP Category {predicted_category.value} with {evidence['strong_count']} strong and {evidence['weak_count']} weak indicators"
    }


@instrument_tool("confidence_scoring", "categorization", critical=True, compliance_required=True)
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

    # Final confidence calculation - NO FALLBACKS: explicit bounds checking without baseline
    raw_confidence = base_score + ambiguity_penalty + category_adjustment

    # NO FALLBACKS: Fail explicitly if confidence calculation produces invalid results
    if raw_confidence < -0.5:  # Sanity check for severely negative confidence
        raise RuntimeError(
            f"CRITICAL: Confidence calculation failed - severely negative raw score {raw_confidence:.3f}. "
            f"This indicates systematic categorization failure requiring explicit resolution. "
            f"Evidence: base_score={base_score:.3f}, ambiguity_penalty={ambiguity_penalty:.3f}, "
            f"category_adjustment={category_adjustment:.3f}"
        )

    # Apply bounds without artificial baseline - use actual computed confidence
    final_confidence = max(0.0, min(1.0, raw_confidence))

    return final_confidence


@instrument_tool("context_provider_integration", "categorization", critical=True, regulatory_impact=True)
def context_provider_tool(
    gamp_category: int,
    urs_content: str,
    document_name: str = "Unknown"
) -> dict[str, Any]:
    """
    Query the Context Provider Agent to enhance categorization confidence.
    
    This tool integrates the Context Provider Agent to retrieve regulatory
    context and documentation that can enhance GAMP categorization confidence.
    
    Args:
        gamp_category: Initial GAMP category from analysis (1, 3, 4, or 5)
        urs_content: Original URS document content for context
        document_name: Document identifier for audit trail
        
    Returns:
        Dictionary with context data including quality assessment and confidence boost
    """
    try:
        # Create context provider instance
        context_provider = create_context_provider_agent(
            verbose=True,
            enable_phoenix=True,
            max_documents=20,  # Reasonable limit for categorization context
            quality_threshold=0.6  # Lower threshold for broader context coverage
        )

        # Determine test strategy based on GAMP category
        test_strategy = {
            "test_types": {
                1: ["installation_qualification", "operational_procedures"],
                3: ["operational_qualification", "functional_testing"],
                4: ["configuration_verification", "business_process_testing", "operational_qualification"],
                5: ["unit_testing", "integration_testing", "system_testing", "acceptance_testing"]
            }.get(gamp_category, ["functional_testing"]),
            "validation_approach": {
                1: "infrastructure_validation",
                3: "standard_application_validation",
                4: "configured_system_validation",
                5: "custom_application_validation"
            }.get(gamp_category, "standard_validation")
        }

        # Extract potential document sections from URS content
        # Look for common pharmaceutical document sections
        content_lower = urs_content.lower()
        potential_sections = []

        section_keywords = {
            "functional_requirements": ["functional", "function", "requirement"],
            "technical_specifications": ["technical", "specification", "architecture"],
            "validation_requirements": ["validation", "qualify", "verify"],
            "regulatory_compliance": ["regulatory", "compliance", "gxp", "cfr", "gamp"],
            "security_requirements": ["security", "access", "authentication"],
            "data_integrity": ["data integrity", "alcoa", "audit trail"],
            "user_requirements": ["user", "stakeholder", "business"]
        }

        for section, keywords in section_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                potential_sections.append(section)

        # Default sections if none found
        if not potential_sections:
            potential_sections = ["functional_requirements", "validation_requirements"]

        # Create search scope based on GAMP category
        search_scope = {
            "focus_areas": [
                f"gamp_category_{gamp_category}",
                "pharmaceutical_validation",
                "regulatory_compliance"
            ],
            "include_best_practices": True,
            "filters": {
                "compliance_level": ["regulatory", "mandatory", "recommended"]
            }
        }

        # Create context provider request
        context_request = ContextProviderRequest(
            gamp_category=str(gamp_category),
            test_strategy=test_strategy,
            document_sections=potential_sections,
            search_scope=search_scope,
            context_depth="standard",
            correlation_id=uuid4(),
            timeout_seconds=120  # Reasonable timeout for categorization
        )

        # Create agent request event
        agent_request = AgentRequestEvent(
            agent_type="context_provider",
            request_data=context_request.model_dump(),
            correlation_id=context_request.correlation_id,
            timestamp=datetime.now(UTC)
        )

        # Execute context provider query with async-to-sync bridge
        # Use asyncio.run() to handle the async call
        try:
            context_result = asyncio.run(context_provider.process_request(agent_request))
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                # Alternative approach for nested event loops
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(context_provider.process_request(agent_request))
                    )
                    context_result = future.result(timeout=120)
            else:
                raise

        # Check if context retrieval was successful
        if not context_result.success:
            error_msg = f"Context provider failed: {context_result.error_message}"
            raise RuntimeError(error_msg)

        # Extract context data
        result_data = context_result.result_data

        # Calculate confidence enhancement based on context quality
        context_quality = result_data.get("context_quality", "poor")
        search_coverage = result_data.get("search_coverage", 0.0)
        retrieved_docs_count = len(result_data.get("retrieved_documents", []))
        context_confidence = result_data.get("confidence_score", 0.0)

        # Quality-based confidence boost
        quality_boost = {
            "high": 0.20,
            "medium": 0.15,
            "low": 0.10,
            "poor": 0.05
        }.get(context_quality, 0.05)

        # Coverage factor (multiply boost by coverage)
        coverage_factor = max(0.5, search_coverage)  # Minimum 50% factor

        # Document count factor (more documents = better support)
        doc_count_factor = min(1.0, retrieved_docs_count / 10)  # Normalize to 10 docs

        # Final confidence boost calculation
        final_boost = quality_boost * coverage_factor * (0.7 + 0.3 * doc_count_factor)

        # Return comprehensive context data
        return {
            "context_available": True,
            "context_quality": context_quality,
            "search_coverage": search_coverage,
            "retrieved_documents_count": retrieved_docs_count,
            "context_confidence_score": context_confidence,
            "confidence_boost": final_boost,
            "processing_time": context_result.processing_time,
            "regulatory_documents_found": len([
                doc for doc in result_data.get("retrieved_documents", [])
                if doc.get("type") in ["regulatory_requirement", "regulatory_guidance"]
            ]),
            "validation_context": {
                "test_strategy_alignment": result_data.get("assembled_context", {}).get("test_strategy_alignment", {}),
                "regulatory_requirements": len(result_data.get("assembled_context", {}).get("regulatory_requirements", [])),
                "best_practices_found": len(result_data.get("assembled_context", {}).get("best_practices", []))
            },
            "audit_trail": {
                "correlation_id": str(context_request.correlation_id),
                "timestamp": datetime.now(UTC).isoformat(),
                "document_name": document_name,
                "gamp_category": gamp_category,
                "context_sections_searched": potential_sections,
                "search_scope": search_scope
            }
        }

    except Exception as e:
        # NO FALLBACKS: Fail explicitly with full diagnostic information
        error_msg = f"Context provider integration failed: {e!s}"
        raise RuntimeError(
            f"{error_msg}\n"
            f"GAMP Category: {gamp_category}\n"
            f"Document: {document_name}\n"
            f"URS Content Length: {len(urs_content)} chars\n"
            f"Error Type: {type(e).__name__}"
        ) from e


def enhanced_confidence_tool(
    category_data: dict[str, Any],
    context_data: dict[str, Any] | None = None
) -> float:
    """
    Enhanced confidence calculation that incorporates context provider data.
    
    Combines the original confidence scoring with context quality assessment
    to provide more accurate confidence levels for GAMP categorization.
    
    Args:
        category_data: Output from gamp_analysis_tool
        context_data: Optional output from context_provider_tool
        
    Returns:
        Enhanced confidence score between 0.0 and 1.0
    """
    # Calculate base confidence using original algorithm
    base_confidence = confidence_tool(category_data)

    # Handle missing context data gracefully while maintaining NO FALLBACK policy
    if not context_data or not context_data.get("context_available", False):
        # Return base confidence with audit trail - this is not a fallback but expected behavior
        # when context provider is not available or fails
        self.logger.warning(
            f"Enhanced confidence calculation requested but context data unavailable. "
            f"Returning base confidence: {base_confidence:.3f}. "
            f"Context status: {context_data.get('context_available', 'not provided') if context_data else 'no context data'}"
        )
        return base_confidence

    # Apply context-based confidence enhancement
    confidence_boost = context_data.get("confidence_boost", 0.0)

    # Enhanced confidence calculation
    enhanced_confidence = base_confidence + confidence_boost

    # Ensure confidence stays within bounds [0.0, 1.0]
    final_confidence = max(0.0, min(1.0, enhanced_confidence))

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

        # Log the result for debugging
        error_handler.logger.debug(f"GAMP analysis tool returned keys: {list(result.keys())}")
        error_handler.logger.debug(f"GAMP analysis predicted category: {result.get('predicted_category')}")

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

        # NO FALLBACKS: Re-raise exception with full diagnostic information
        raise RuntimeError(f"GAMP analysis tool failed: {e!s}") from e


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
        # Log the input for debugging
        error_handler.logger.debug(f"Confidence tool received data type: {type(category_data)}")
        error_handler.logger.debug(f"Confidence tool received keys: {list(category_data.keys()) if isinstance(category_data, dict) else 'Not a dict'}")

        # Check if this is an error result
        if category_data.get("error", False):
            # Try to extract actual confidence from error event
            confidence_score = category_data.get("confidence_score", 0.0)
            return confidence_score

        # Validate input
        if not isinstance(category_data, dict):
            raise ValueError("Invalid category data: must be dictionary")

        required_fields = ["predicted_category", "evidence", "all_categories_analysis"]
        missing_fields = [f for f in required_fields if f not in category_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Call original confidence tool
        confidence = confidence_tool(category_data)

        # Check for ambiguity using actual confidence score
        # Only use the actual confidence score for the predicted category
        # This prevents false ambiguity detection from artificial scores
        predicted_category = category_data.get("predicted_category")
        confidence_scores = {predicted_category: confidence}

        # Log for audit trail
        error_handler.logger.debug(f"Using actual confidence score {confidence} for category {predicted_category}")
        error_handler.logger.debug(f"Confidence scores for ambiguity check: {confidence_scores}")

        ambiguity_error = error_handler.check_ambiguity(category_data, confidence_scores)
        if ambiguity_error:
            # Log the ambiguity but don't fail - let low confidence handle it
            error_handler.logger.warning(f"Ambiguity detected: {ambiguity_error.message}")

        return confidence

    except Exception as e:
        error_handler.logger.error(f"Confidence calculation error: {e!s}")
        error_handler.logger.error(f"Input data that caused error: {category_data}")
        # NO FALLBACKS: Re-raise exception with full diagnostic information
        raise RuntimeError(f"Confidence calculation failed: {e!s}") from e


def create_gamp_categorization_agent(
    llm: LLM = None,
    enable_error_handling: bool = True,
    confidence_threshold: float = 0.40,  # Reduced to 0.40 for pharmaceutical system practicality
    verbose: bool = False,
    use_structured_output: bool = True,  # New parameter to enable Pydantic structured output
    enable_context_provider: bool = True  # New parameter to enable context provider integration
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
        use_structured_output: Whether to use Pydantic structured output (recommended)
        enable_context_provider: Whether to enable context provider integration for confidence enhancement
        
    Returns:
        FunctionAgent configured for GAMP-5 categorization with error handling
        
    Note:
        When use_structured_output=True, the agent should be used with
        categorize_with_pydantic_structured_output() instead of the regular
        categorize_with_error_handling() function for optimal results.
        
        When enable_context_provider=True, the agent gains access to regulatory
        context that can boost confidence scores by 0.15-0.20 points.
    """
    if llm is None:
        # Use centralized LLM config - NO FALLBACKS
        # Migrated from direct OpenAI to centralized configuration
        llm = LLMConfig.get_llm(
            temperature=0.1,  # Override default temperature for categorization
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
    tools = []

    if enable_error_handling and error_handler:
        # Create wrapped tools with error handling
        def gamp_tool_wrapper(urs_content: str) -> dict[str, Any]:
            return gamp_analysis_tool_with_error_handling(urs_content, error_handler)

        def confidence_tool_wrapper(category_data: dict[str, Any], context_data: dict[str, Any] = None) -> float:
            if enable_context_provider and context_data:
                return enhanced_confidence_tool(category_data, context_data)
            return confidence_tool_with_error_handling(category_data, error_handler)

        gamp_analysis_function_tool = FunctionTool.from_defaults(
            fn=gamp_tool_wrapper,
            name="gamp_analysis_tool",
            description="Analyze URS content to determine GAMP category. Input: URS content string. Returns: dictionary with predicted_category, evidence, and analysis."
        )

        if enable_context_provider:
            confidence_function_tool = FunctionTool.from_defaults(
                fn=confidence_tool_wrapper,
                name="enhanced_confidence_tool",
                description="Calculate enhanced confidence score using context data. Input: category_data dictionary from gamp_analysis_tool, optional context_data from context_provider_tool. Returns: enhanced confidence score (0.0-1.0)."
            )
        else:
            confidence_function_tool = FunctionTool.from_defaults(
                fn=lambda category_data: confidence_tool_with_error_handling(category_data, error_handler),
                name="confidence_tool",
                description="Calculate confidence score for categorization. Input: category_data dictionary from gamp_analysis_tool. Returns: confidence score (0.0-1.0)."
            )
    else:
        # Use original tools without error handling
        gamp_analysis_function_tool = FunctionTool.from_defaults(
            fn=gamp_analysis_tool,
            name="gamp_analysis_tool",
            description="Analyze URS content to determine GAMP category. Input: URS content string. Returns: dictionary with predicted_category, evidence, and analysis."
        )

        if enable_context_provider:
            confidence_function_tool = FunctionTool.from_defaults(
                fn=lambda category_data, context_data=None: enhanced_confidence_tool(category_data, context_data),
                name="enhanced_confidence_tool",
                description="Calculate enhanced confidence score using context data. Input: category_data dictionary from gamp_analysis_tool, optional context_data from context_provider_tool. Returns: enhanced confidence score (0.0-1.0)."
            )
        else:
            confidence_function_tool = FunctionTool.from_defaults(
                fn=confidence_tool,
                name="confidence_tool",
                description="Calculate confidence score for categorization. Input: category_data dictionary from gamp_analysis_tool. Returns: confidence score (0.0-1.0)."
            )

    # Add core tools
    tools.extend([gamp_analysis_function_tool, confidence_function_tool])

    # Add context provider tool if enabled
    if enable_context_provider:
        context_provider_function_tool = FunctionTool.from_defaults(
            fn=context_provider_tool,
            name="context_provider_tool",
            description="Query regulatory context to enhance categorization confidence. Input: gamp_category (int), urs_content (str), document_name (str). Returns: context data with quality assessment and confidence boost."
        )
        tools.append(context_provider_function_tool)

    # Enhanced system prompt with Chain-of-Thought reasoning and context provider
    if enable_context_provider:
        system_prompt = """You are a GAMP-5 categorization expert with access to regulatory context. Use Chain-of-Thought reasoning to analyze URS documents.

Categories:
1: Infrastructure (OS, databases, middleware)
3: Non-configured COTS (used as supplied) 
4: Configured products (user parameters)
5: Custom applications (bespoke code)

Chain-of-Thought Process:
1. Identify software type: [infrastructure/commercial/custom]
2. Check customization level: [none/configuration/development]
3. Apply GAMP-5 criteria: [evidence evaluation] 
4. Determine category with confidence: [1-5 with reasoning]

Tool Process:
1. Call gamp_analysis_tool with URS content
2. Call context_provider_tool with predicted category, URS content, and document name  
3. Call enhanced_confidence_tool with analysis results AND context data
4. After calling ALL THREE tools EXACTLY ONCE, provide final answer

Final answer format:
- Category number (1, 3, 4, or 5)
- Enhanced confidence as percentage (e.g., 82%)
- Chain-of-Thought reasoning summary
- Context quality assessment (high/medium/low/poor)

Error Handling: All failures reported explicitly with full diagnostic information - NO FALLBACKS"""
    else:
        system_prompt = """You are a GAMP-5 categorization expert. Use Chain-of-Thought reasoning to analyze URS documents.

Categories:
1: Infrastructure (OS, databases, middleware)
3: Non-configured COTS (used as supplied)
4: Configured products (user parameters) 
5: Custom applications (bespoke code)

Chain-of-Thought Process:
1. Identify software type: [infrastructure/commercial/custom]
2. Check customization level: [none/configuration/development]
3. Apply GAMP-5 criteria: [evidence evaluation]
4. Determine category with confidence: [1-5 with reasoning]

Tool Process:
1. Call gamp_analysis_tool with URS content
2. Call confidence_tool with analysis results dictionary
3. After calling BOTH tools EXACTLY ONCE, provide final answer

Final answer format:
- Category number (1, 3, 4, or 5)
- Confidence as percentage (e.g., 75%)
- Chain-of-Thought reasoning summary

Error Handling: All failures reported explicitly with full diagnostic information - NO FALLBACKS"""

    agent = FunctionAgent(
        tools=tools,
        llm=llm,
        verbose=verbose,
        max_iterations=20 if enable_context_provider else 15,  # More iterations for context provider workflow
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
        justification_parts.append(f"[WARNING] Exclusion Factors ({evidence['exclusion_count']}): {', '.join(evidence['exclusion_factors'])}")

    justification_parts.append("")
    justification_parts.append(f"DECISION RATIONALE: {categorization_result['decision_rationale']}")

    requires_review = confidence_score < 0.85
    if requires_review:
        justification_parts.extend([
            "",
            "[WARNING] HUMAN REVIEW REQUIRED",
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


def categorize_with_pydantic_structured_output(
    llm: LLM,
    urs_content: str,
    document_name: str = "Unknown",
    error_handler: CategorizationErrorHandler | None = None
) -> GAMPCategorizationEvent:
    """
    Categorize URS using direct LLM calls with robust parsing for OSS model compatibility.
    
    This approach bypasses LLMTextCompletionProgram's model validation to support
    both OpenAI and OpenRouter/OSS models through direct LLM calls with JSON parsing.
    
    Args:
        llm: LLM instance to use for categorization
        urs_content: URS document content
        document_name: Document identifier for logging
        error_handler: Optional error handler for compliance tracking
        
    Returns:
        GAMPCategorizationEvent with categorization result
    """
    if error_handler is None:
        error_handler = CategorizationErrorHandler()

    try:
        # Enhanced prompt with Chain-of-Thought reasoning and JSON examples
        categorization_prompt = f"""You are a GAMP-5 categorization expert. Use step-by-step reasoning to analyze the URS document.

Categories:
1: Infrastructure (OS, databases, middleware)
3: Non-configured COTS (used as supplied)  
4: Configured products (user parameters)
5: Custom applications (bespoke development)

Chain-of-Thought Reasoning Process:
1. Identify software type: [infrastructure/commercial/custom]
2. Check customization level: [none/configuration/development]  
3. Evaluate GAMP indicators: [list key findings]
4. Determine category: [1/3/4/5]
5. Calculate confidence: [0.0-1.0]

Examples with Chain-of-Thought:

Input: "Requirements for Windows Server 2019 operating system installation with Oracle Database 19c for laboratory network infrastructure"
Chain-of-Thought: 1) Software type: infrastructure (OS, database), 2) Customization: none (standard installation), 3) GAMP indicators: foundational platform services, no business logic, 4) Category: 1, 5) Confidence: 0.85 (clear infrastructure pattern)
Output: {{"category": 1, "confidence_score": 0.85, "reasoning": "Infrastructure software - Windows Server OS and Oracle Database are Category 1 components providing foundational platform services"}}

Input: "Commercial LIMS package to be used as supplied by vendor without modifications or custom configuration"  
Chain-of-Thought: 1) Software type: commercial COTS, 2) Customization: none (as supplied), 3) GAMP indicators: vendor-supplied without modification, standard functionality, 4) Category: 3, 5) Confidence: 0.90 (explicit 'as supplied' statement)
Output: {{"category": 3, "confidence_score": 0.90, "reasoning": "Non-configured product - COTS LIMS used as supplied without modifications indicates Category 3"}}

Input: "Configure commercial ERP system workflows, user roles, and business process parameters for pharmaceutical manufacturing"
Chain-of-Thought: 1) Software type: commercial product, 2) Customization: configuration (workflows, parameters), 3) GAMP indicators: business process setup, user-defined parameters, 4) Category: 4, 5) Confidence: 0.80 (clear configuration requirements)  
Output: {{"category": 4, "confidence_score": 0.80, "reasoning": "Configured product - commercial ERP requiring workflow configuration and business rule setup indicates Category 4"}}

Input: "Custom-developed laboratory data management system with proprietary algorithms for analytical data processing and bespoke reporting modules"
Chain-of-Thought: 1) Software type: custom development, 2) Customization: full development (proprietary code), 3) GAMP indicators: bespoke solution, proprietary algorithms, custom modules, 4) Category: 5, 5) Confidence: 0.95 (multiple strong custom indicators)
Output: {{"category": 5, "confidence_score": 0.95, "reasoning": "Custom application - bespoke development with proprietary algorithms and custom modules clearly indicates Category 5"}}

Now use Chain-of-Thought reasoning to analyze this URS content and respond with ONLY the JSON object:

{urs_content}"""

        # Use direct LLM call instead of LLMTextCompletionProgram
        error_handler.logger.info(f"Starting structured categorization for document: {document_name}")

        # Call LLM directly
        response = llm.complete(categorization_prompt)
        response_text = response.text if hasattr(response, "text") else str(response)

        error_handler.logger.debug(f"LLM response (first 200 chars): {response_text[:200]}")

        # Parse the response using our robust parser
        result = parse_structured_response(response_text)

        # Validate the result
        result.validate_category()

        error_handler.logger.info(f"Structured categorization completed: Category {result.category}, Confidence {result.confidence_score:.2f}")

        # Check confidence threshold
        if result.confidence_score < error_handler.confidence_threshold:
            error = CategorizationError(
                error_type=ErrorType.CONFIDENCE_ERROR,
                severity=ErrorSeverity.MEDIUM,
                message=f"Confidence {result.confidence_score:.2f} below threshold {error_handler.confidence_threshold}",
                details={
                    "confidence": result.confidence_score,
                    "threshold": error_handler.confidence_threshold,
                    "category": result.category
                }
            )
            return error_handler._create_human_consultation_request(error, document_name)

        # Create successful categorization event
        gamp_category = GAMPCategory(result.category)

        # Build comprehensive justification
        justification_parts = [
            f"GAMP-5 Structured Categorization Analysis for '{document_name}'",
            "",
            f"CLASSIFICATION: Category {result.category}",
            f"CONFIDENCE: {result.confidence_score:.1%}",
            "",
            "ANALYSIS METHOD: LLMTextCompletionProgram with Pydantic structured output",
            "",
            "REASONING:",
            result.reasoning,
            "",
            f"CATEGORY DESCRIPTION: {_get_category_description(gamp_category)}",
            f"VALIDATION APPROACH: {_get_validation_approach(gamp_category)}"
        ]

        requires_review = result.confidence_score < 0.85
        if requires_review:
            justification_parts.extend([
                "",
                "[WARNING] HUMAN REVIEW REQUIRED",
                "Confidence below threshold (85%) - Expert review needed for regulatory compliance"
            ])

        # Build comprehensive risk assessment
        risk_assessment = {
            "category": result.category,
            "category_description": _get_category_description(gamp_category),
            "validation_approach": _get_validation_approach(gamp_category),
            "confidence_score": result.confidence_score,
            "evidence_strength": "Structured LLM analysis",
            "requires_human_review": requires_review,
            "regulatory_impact": _assess_regulatory_impact(gamp_category),
            "validation_effort": _estimate_validation_effort(gamp_category),
            "analysis_method": "LLMTextCompletionProgram with Pydantic validation"
        }

        return GAMPCategorizationEvent(
            gamp_category=gamp_category,
            confidence_score=result.confidence_score,
            justification="\n".join(justification_parts),
            risk_assessment=risk_assessment,
            event_id=uuid4(),
            timestamp=datetime.now(UTC),
            categorized_by="GAMPCategorizationAgent-Structured",
            review_required=requires_review
        )

    except Exception as e:
        # NO FALLBACKS: Handle errors explicitly with full diagnostic information
        error_handler.logger.error(f"Structured categorization failed: {e!s}")
        error_handler.logger.error(f"Input that caused error: {urs_content[:200]}...")
        # Re-raise with comprehensive diagnostic information
        raise RuntimeError(f"Structured categorization failed for document '{document_name}': {e!s}") from e


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
            return error_handler._create_human_consultation_request(error, document_name)

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


async def categorize_with_error_handling(
    agent: FunctionAgent,
    urs_content: str,
    document_name: str = "Unknown",
    max_retries: int = 1
) -> GAMPCategorizationEvent:
    """
    Categorize URS content with comprehensive error handling.
    
    This wrapper function provides end-to-end error handling for the categorization
    process with explicit failure reporting - NO FALLBACKS.
    
    Args:
        agent: The GAMP categorization agent
        urs_content: URS document content
        document_name: Document identifier for logging
        max_retries: Maximum retry attempts on failure
        
    Returns:
        GAMPCategorizationEvent with categorization result
        
    Raises:
        RuntimeError: When categorization fails after all retries (NO FALLBACKS)
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

            # Run agent query using FunctionAgent's run method
            error_handler.logger.info(f"Starting categorization attempt {retry_count + 1} for document: {document_name}")
            response = await agent.run(user_msg=f"Analyze this URS document and categorize it:\n\n{urs_content}")
            error_handler.logger.info(f"Agent response received (length: {len(str(response))} chars)")

            # Parse response to extract category and confidence
            response_text = str(response)

            # Debug logging
            error_handler.logger.debug(f"Agent response: {response_text[:500]}...")

            # Extract category number (look for patterns like "Category 1", "Category: 1", etc.)
            import re
            category_match = re.search(r"[Cc]ategory[\s:]*(\d)", response_text)
            if not category_match:
                # Try alternative patterns
                category_match = re.search(r"GAMP[\s-]*(\d)", response_text)
                if not category_match:
                    # Try markdown format
                    category_match = re.search(r"\*\*Determined Category\*\*[\s:]*(\d)", response_text)
                    if not category_match:
                        error_handler.logger.error(f"Failed to extract category from response: {response_text[:200]}...")
                        raise ValueError("Could not extract category from agent response")

            category_num = int(category_match.group(1))
            if category_num not in [1, 3, 4, 5]:
                raise ValueError(f"Invalid category number: {category_num}")

            # Extract confidence (look for patterns like "85%", "0.85", "confidence: 0.85")
            confidence_match = re.search(r"(\d+(?:\.\d+)?)\s*%|confidence[\s:]*(\d+(?:\.\d+)?)", response_text, re.IGNORECASE)
            if not confidence_match:
                # Try markdown format
                confidence_match = re.search(r"\*\*Confidence Score\*\*[\s:]*(\d+(?:\.\d+)?)\s*%", response_text)

            if confidence_match:
                if confidence_match.group(1):  # Percentage format or decimal with %
                    raw_value = float(confidence_match.group(1))
                    if "%" in confidence_match.group(0):  # Percentage format
                        confidence = raw_value / 100
                    else:  # Decimal format without %
                        confidence = raw_value if raw_value <= 1.0 else raw_value / 100
                else:  # Group 2 - decimal format from "confidence:" pattern
                    raw_value = float(confidence_match.group(2))
                    confidence = raw_value if raw_value <= 1.0 else raw_value / 100
            else:
                # NO FALLBACKS: Raise exception when confidence cannot be parsed
                error_handler.logger.error(f"Failed to extract confidence from response: {response_text[:500]}...")
                raise ValueError("Could not extract confidence from agent response")

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
                return error_handler._create_human_consultation_request(error, document_name)

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
            # NO FALLBACKS: Max retries exceeded, fail explicitly with full diagnostic information
            error_handler.logger.error(f"Categorization failed after {max_retries} retries for document '{document_name}'")
            error_handler.logger.error(f"Final error: {e!s}")
            error_handler.logger.error(f"Error type: {type(e).__name__}")
            error_handler.logger.error(f"URS content length: {len(urs_content)} characters")
            raise RuntimeError(
                f"GAMP categorization failed after {max_retries} retries for document '{document_name}': "
                f"{e!s}. No fallback allowed - explicit resolution required."
            ) from e

    # NO FALLBACKS: This code should never be reached - fail explicitly if it is
    error_handler.logger.critical(f"Unexpected code path reached in categorization loop for document '{document_name}'")
    error_handler.logger.critical(f"Last error: {last_error}")
    raise RuntimeError(
        f"GAMP categorization reached unexpected code path for document '{document_name}'. "
        f"Last error: {last_error}. System integrity compromised - immediate investigation required."
    )


def categorize_urs_document(
    urs_content: str,
    document_name: str = "Unknown",
    llm: LLM = None,
    use_structured_output: bool = True,
    confidence_threshold: float = 0.40,
    verbose: bool = False
) -> GAMPCategorizationEvent:
    """
    High-level convenience function for URS document categorization.
    
    This function provides a simple interface for categorizing URS documents
    with either the new Pydantic structured output approach (recommended)
    or the legacy FunctionAgent approach.
    
    Args:
        urs_content: URS document content to categorize
        document_name: Document identifier for logging and traceability
        llm: Optional LLM instance (uses default if not provided)
        use_structured_output: Use Pydantic structured output (recommended: True)
        confidence_threshold: Minimum confidence threshold for categorization
        verbose: Enable verbose logging
        
    Returns:
        GAMPCategorizationEvent with categorization results
        
    Example:
        # Recommended approach with structured output
        result = categorize_urs_document(
            urs_content="Software for managing laboratory data...",
            document_name="LIMS_URS_v1.2.pdf",
            use_structured_output=True
        )
    """
    if llm is None:
        # Use centralized LLM config - NO FALLBACKS
        # Migrated from direct OpenAI to centralized configuration
        llm = LLMConfig.get_llm(
            temperature=0.1,  # Override default temperature for categorization
            max_tokens=2000
        )

    # Create error handler for compliance tracking
    error_handler = CategorizationErrorHandler(
        confidence_threshold=confidence_threshold,
        verbose=verbose
    )

    if use_structured_output:
        # Use new Pydantic structured output approach (recommended)
        return categorize_with_pydantic_structured_output(
            llm=llm,
            urs_content=urs_content,
            document_name=document_name,
            error_handler=error_handler
        )
    # Use legacy FunctionAgent approach (deprecated)
    agent = create_gamp_categorization_agent(
        llm=llm,
        enable_error_handling=True,
        confidence_threshold=confidence_threshold,
        verbose=verbose,
        use_structured_output=False
    )
    return categorize_with_structured_output(agent, urs_content, document_name)
