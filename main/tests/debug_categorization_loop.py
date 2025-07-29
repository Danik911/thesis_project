"""
Debug script for GAMP-5 categorization iteration loop issue.

This script isolates the categorization agent to debug why it's getting
stuck in an iteration loop.
"""

import asyncio
import logging
from datetime import datetime

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from src.agents.categorization.agent import create_gamp_categorization_agent, categorize_with_error_handling
from src.core.events import GAMPCategory


# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create specific loggers
categorization_logger = logging.getLogger('src.agents.categorization')
categorization_logger.setLevel(logging.DEBUG)

workflow_logger = logging.getLogger('llama_index.core.workflow')
workflow_logger.setLevel(logging.DEBUG)

agent_logger = logging.getLogger('llama_index.core.agent')
agent_logger.setLevel(logging.DEBUG)


async def test_categorization_agent():
    """Test the categorization agent with a simple URS."""
    
    print("\n" + "="*80)
    print("GAMP-5 CATEGORIZATION AGENT DEBUG TEST")
    print("="*80 + "\n")
    
    # Simple test URS content
    test_urs = """
    # Pharmaceutical System URS
    
    ## System Overview
    This document describes requirements for a Laboratory Information Management System (LIMS).
    The LIMS will be used to manage laboratory test results and ensure compliance with 21 CFR Part 11.
    
    ## Key Requirements
    1. The system shall manage laboratory test results
    2. The system shall provide audit trails for all data changes
    3. The system shall support electronic signatures
    4. The system requires configuration of workflows and user roles
    5. Standard reports shall be configurable by authorized users
    """
    
    print("Test URS Content:")
    print("-" * 40)
    print(test_urs)
    print("-" * 40 + "\n")
    
    try:
        # Create agent with verbose logging
        print("Creating GAMP-5 categorization agent...")
        agent = create_gamp_categorization_agent(
            enable_error_handling=True,
            confidence_threshold=0.60,
            verbose=True
        )
        print("✓ Agent created successfully\n")
        
        # Track timing
        start_time = datetime.now()
        
        # Run categorization
        print("Starting categorization (this may take a moment)...")
        print("Monitoring for iteration loops...\n")
        
        result = await categorize_with_error_handling(
            agent=agent,
            urs_content=test_urs,
            document_name="debug_test.urs",
            max_retries=0  # No retries for debugging
        )
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Display results
        print("\n" + "="*80)
        print("CATEGORIZATION RESULTS")
        print("="*80)
        print(f"✓ Categorization completed in {duration:.2f} seconds")
        print(f"  Category: {result.gamp_category.value}")
        print(f"  Confidence: {result.confidence_score:.2%}")
        print(f"  Review Required: {result.review_required}")
        print(f"\nJustification:")
        print("-" * 40)
        print(result.justification[:500] + "..." if len(result.justification) > 500 else result.justification)
        
        # Check for issues
        print("\n" + "="*80)
        print("ISSUE ANALYSIS")
        print("="*80)
        
        if duration > 30:
            print("⚠️  WARNING: Categorization took longer than 30 seconds")
            print("   This suggests the agent may be stuck in iteration loops")
        else:
            print("✓ Categorization completed within reasonable time")
            
        if result.confidence_score == 0.0 and result.gamp_category == GAMPCategory.CATEGORY_5:
            print("⚠️  WARNING: Fallback to Category 5 with 0% confidence detected")
            print("   This indicates categorization failed and fell back to default")
        else:
            print("✓ Valid categorization with non-zero confidence")
            
    except Exception as e:
        print(f"\n❌ ERROR: Categorization failed with exception:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        
        import traceback
        print("\nFull traceback:")
        print("-" * 40)
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")


async def test_tools_directly():
    """Test the tools directly to ensure they work properly."""
    
    print("\n" + "="*80)
    print("DIRECT TOOL TESTING")
    print("="*80 + "\n")
    
    from src.agents.categorization.agent import gamp_analysis_tool, confidence_tool
    
    test_urs = "This is a LIMS system with configuration requirements."
    
    try:
        # Test GAMP analysis tool
        print("Testing gamp_analysis_tool...")
        analysis_result = gamp_analysis_tool(test_urs)
        print(f"✓ Analysis tool returned: {list(analysis_result.keys())}")
        print(f"  Predicted category: {analysis_result['predicted_category']}")
        print(f"  Decision rationale: {analysis_result['decision_rationale']}")
        
        # Test confidence tool
        print("\nTesting confidence_tool...")
        confidence = confidence_tool(analysis_result)
        print(f"✓ Confidence tool returned: {confidence:.2%}")
        
    except Exception as e:
        print(f"❌ Tool testing failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all debug tests."""
    # Test tools directly first
    await test_tools_directly()
    
    # Then test the full agent
    await test_categorization_agent()


if __name__ == "__main__":
    asyncio.run(main())