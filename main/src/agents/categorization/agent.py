"""
GAMP-5 Categorization Agent - LlamaIndex Implementation

This module provides the GAMP-5 categorization agent following LlamaIndex patterns.
Uses FunctionAgent with LLM intelligence and categorization tools.

Based on the synthesis document and following the project's established agent patterns.
"""

from typing import Dict, Any, Optional
from datetime import datetime, UTC
from uuid import uuid4

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool
from llama_index.core.llms import LLM

from main.src.core.events import GAMPCategory, GAMPCategorizationEvent


def gamp_analysis_tool(urs_content: str) -> Dict[str, Any]:
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
    normalized_content = ' '.join(normalized_content.split())  # Remove extra whitespace
    
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


def confidence_tool(category_data: Dict[str, Any]) -> float:
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
        'strong_indicators': 0.4,
        'weak_indicators': 0.2,
        'exclusion_factors': -0.3,
        'ambiguity_penalty': -0.1
    }
    
    # Calculate base score
    base_score = (
        weights['strong_indicators'] * evidence['strong_count'] +
        weights['weak_indicators'] * evidence['weak_count'] +
        weights['exclusion_factors'] * evidence['exclusion_count']
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
        ambiguity_penalty = weights['ambiguity_penalty'] * penalty_factor
    
    # Category-specific adjustments
    category_adjustment = 0.0
    if predicted_category == 1 and evidence['strong_count'] >= 2:  # Category 1
        category_adjustment = 0.1
    elif predicted_category == 5 and evidence['strong_count'] >= 2:  # Category 5
        category_adjustment = 0.15
    elif predicted_category in [3, 4] and evidence['strong_count'] >= 1:
        category_adjustment = 0.05
    
    # Final confidence calculation
    raw_confidence = base_score + ambiguity_penalty + category_adjustment
    final_confidence = max(0.0, min(1.0, 0.5 + raw_confidence))
    
    return final_confidence


def create_gamp_categorization_agent(llm: LLM = None) -> FunctionAgent:
    """
    Create GAMP-5 categorization agent following project patterns.
    
    This factory function creates a FunctionAgent with LLM intelligence and GAMP
    categorization tools, following the established project architecture.
    
    Args:
        llm: Optional LLM instance. If not provided, uses default from project config
        
    Returns:
        FunctionAgent configured for GAMP-5 categorization
    """
    if llm is None:
        # Use OpenAI LLM without JSON mode for FunctionAgent compatibility
        from llama_index.llms.openai import OpenAI
        import os
        llm = OpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=2000
            # JSON mode NOT used - FunctionAgent requires natural language responses
        )
    
    # Create function tools
    gamp_analysis_function_tool = FunctionTool.from_defaults(
        fn=gamp_analysis_tool,
        name="gamp_analysis_tool", 
        description="Analyze URS content for GAMP categorization indicators based on synthesis document"
    )
    
    confidence_function_tool = FunctionTool.from_defaults(
        fn=confidence_tool,
        name="confidence_tool",
        description="Calculate confidence score for GAMP categorization decision"
    )
    
    return FunctionAgent(
        tools=[gamp_analysis_function_tool, confidence_function_tool],
        llm=llm,
        verbose=True,  # Enable verbose for debugging during development
        max_iterations=10,  # Reduced from default 20 to prevent timeouts
        system_prompt="""You are a GAMP-5 categorization expert. Analyze URS documents and determine the GAMP category.

Categories:
- Category 1: Infrastructure (OS, databases, middleware)
- Category 3: Non-configured COTS (used as supplied)
- Category 4: Configured products (user parameters)
- Category 5: Custom applications (bespoke code)

Process:
1. Use gamp_analysis_tool to analyze the content
2. Use confidence_tool to get confidence score
3. Provide clear categorization with justification

Provide the category number, confidence score, and brief explanation."""
    )


def create_categorization_event(
    categorization_result: Dict[str, Any],
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
        f"",
        f"CLASSIFICATION: Category {predicted_category.value}",
        f"CONFIDENCE: {confidence_score:.1%}",
        f"",
        f"EVIDENCE ANALYSIS:",
    ]
    
    if evidence["strong_indicators"]:
        justification_parts.append(f"✓ Strong Indicators ({evidence['strong_count']}): {', '.join(evidence['strong_indicators'][:5])}")
    
    if evidence["weak_indicators"]:
        justification_parts.append(f"○ Supporting Indicators ({evidence['weak_count']}): {', '.join(evidence['weak_indicators'][:3])}")
    
    if evidence["exclusion_factors"]:
        justification_parts.append(f"⚠ Exclusion Factors ({evidence['exclusion_count']}): {', '.join(evidence['exclusion_factors'])}")
    
    justification_parts.append(f"")
    justification_parts.append(f"DECISION RATIONALE: {categorization_result['decision_rationale']}")
    
    requires_review = confidence_score < 0.85
    if requires_review:
        justification_parts.extend([
            f"",
            f"⚠️ HUMAN REVIEW REQUIRED",
            f"Confidence below threshold (85%) - Expert review needed for regulatory compliance"
        ])
    
    # Build risk assessment
    risk_assessment = {
        'category': predicted_category.value,
        'category_description': _get_category_description(predicted_category),
        'validation_approach': _get_validation_approach(predicted_category),
        'confidence_score': confidence_score,
        'evidence_strength': _assess_evidence_strength(evidence),
        'requires_human_review': requires_review,
        'regulatory_impact': _assess_regulatory_impact(predicted_category),
        'validation_effort': _estimate_validation_effort(predicted_category)
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


def _assess_evidence_strength(evidence: Dict[str, Any]) -> str:
    """Assess overall strength of evidence."""
    strong_count = evidence["strong_count"]
    exclusion_count = evidence["exclusion_count"]
    
    if strong_count >= 3 and exclusion_count == 0:
        return "Strong"
    elif strong_count >= 2 and exclusion_count <= 1:
        return "Moderate"
    elif strong_count >= 1:
        return "Weak"
    else:
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