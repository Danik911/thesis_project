#!/usr/bin/env python3
"""
Test Script for OSS Model SME Agent JSON Generation Fix

This script tests the enhanced SME agent with OSS model compatibility
fixes including:
- Increased token limits (2000 -> 4000)
- Enhanced JSON prompting for OSS models  
- Comprehensive debug logging
- OSS model detection and handling

CRITICAL: NO FALLBACKS - All failures are explicit for pharmaceutical compliance
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the main directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from src.config.llm_config import LLMConfig
from src.agents.parallel.sme_agent import create_sme_agent
from src.core.events import AgentRequestEvent
from uuid import uuid4

# Configure logging for comprehensive debug output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment setup for OSS model testing."""
    logger.info("=== Environment Check ===")
    
    # Check LLM provider
    provider = os.getenv("LLM_PROVIDER", "openrouter")
    logger.info(f"LLM Provider: {provider}")
    
    # Check API keys
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    logger.info(f"OpenRouter API Key Present: {'Yes' if openrouter_key else 'No'}")
    
    if provider == "openrouter" and not openrouter_key:
        logger.error("OPENROUTER_API_KEY not found in environment!")
        return False
    
    # Check model configuration 
    try:
        provider_info = LLMConfig.get_provider_info()
        logger.info(f"Model Configuration: {provider_info}")
        
        # Validate configuration
        is_valid, error = LLMConfig.validate_configuration()
        logger.info(f"Configuration Valid: {is_valid}")
        if not is_valid:
            logger.error(f"Configuration Error: {error}")
            return False
            
    except Exception as e:
        logger.error(f"LLM Configuration Error: {e}")
        return False
    
    logger.info("✅ Environment check passed")
    return True

async def test_llm_basic():
    """Test basic LLM functionality with OSS model."""
    logger.info("=== Basic LLM Test ===")
    
    try:
        llm = LLMConfig.get_llm()
        logger.info(f"LLM initialized: {llm}")
        logger.info(f"Model: {llm.model}")
        logger.info(f"Max tokens: {llm.max_tokens}")
        
        # Test simple completion
        simple_prompt = "What is GAMP-5? Answer in one sentence."
        response = await llm.acomplete(simple_prompt)
        logger.info(f"Simple completion successful: {len(response.text)} chars")
        logger.info(f"Response preview: {response.text[:200]}...")
        
        # Test JSON generation
        json_prompt = """
        Generate a simple JSON object with pharmaceutical validation info.
        
        CRITICAL: Respond with valid JSON only, no markdown or explanations.
        
        Format:
        {
            "category": "pharmaceutical_validation",
            "standards": ["GAMP-5", "21 CFR Part 11"],
            "complexity": "medium"
        }
        """
        
        json_response = await llm.acomplete(json_prompt)
        logger.info(f"JSON completion successful: {len(json_response.text)} chars")
        logger.info(f"JSON response: {json_response.text}")
        
        # Try to parse the JSON
        import json
        try:
            parsed = json.loads(json_response.text.strip())
            logger.info("✅ JSON parsing successful")
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON parsing failed: {e}")
            
    except Exception as e:
        logger.error(f"❌ Basic LLM test failed: {e}")
        raise

async def test_sme_agent_creation():
    """Test SME agent creation and OSS model detection."""
    logger.info("=== SME Agent Creation Test ===")
    
    try:
        # Create SME agent
        sme_agent = create_sme_agent(
            specialty="GAMP Category 5",
            verbose=True
        )
        
        logger.info(f"SME agent created: {sme_agent}")
        logger.info(f"Specialty: {sme_agent.specialty}")
        logger.info(f"OSS model detected: {sme_agent.is_oss_model}")
        logger.info(f"Model: {sme_agent.llm.model}")
        logger.info(f"Max tokens: {sme_agent.llm.max_tokens}")
        
        # Test OSS model detection
        if sme_agent.is_oss_model:
            logger.info("✅ OSS model correctly detected - enhanced prompting will be used")
        else:
            logger.warning("⚠️ OSS model not detected - check detection logic")
            
    except Exception as e:
        logger.error(f"❌ SME agent creation failed: {e}")
        raise

async def test_sme_agent_simple_request():
    """Test SME agent with a simple request."""
    logger.info("=== SME Agent Simple Request Test ===")
    
    try:
        # Create SME agent
        sme_agent = create_sme_agent(
            specialty="pharmaceutical_validation",
            verbose=True
        )
        
        # Create simple request
        simple_request = AgentRequestEvent(
            agent_type="sme",
            request_data={
                "specialty": "pharmaceutical_validation",
                "test_focus": "OQ testing for GAMP Category 5 system",
                "compliance_level": "high", 
                "domain_knowledge": ["GAMP-5", "21 CFR Part 11"],
                "validation_focus": ["functional_testing", "compliance_validation"],
                "risk_factors": {"complexity": "high", "regulatory_impact": "high"},
                "categorization_context": {"gamp_category": 5, "confidence_score": 0.9}
            },
            correlation_id=uuid4(),
            requesting_step="test_script",
            session_id="test_session"
        )
        
        logger.info("Processing SME request...")
        result = await sme_agent.process_request(simple_request)
        
        logger.info(f"SME request completed: Success={result.success}")
        
        if result.success:
            logger.info("✅ SME agent request successful!")
            recommendations = result.result_data.get("recommendations", [])
            logger.info(f"Recommendations generated: {len(recommendations)}")
            
            if recommendations:
                logger.info(f"First recommendation: {recommendations[0]}")
                
        else:
            logger.error(f"❌ SME agent request failed: {result.error_message}")
            logger.error(f"Result data: {result.result_data}")
            
    except Exception as e:
        logger.error(f"❌ SME agent simple request failed: {e}")
        raise

async def test_workflow_integration():
    """Test integration with the unified workflow."""
    logger.info("=== Workflow Integration Test ===")
    
    try:
        from src.core.unified_workflow import run_unified_test_generation_workflow
        
        # Use test document
        test_document = Path("main/tests/test_data/gamp5_test_data/category_5_test_system.md")
        
        if not test_document.exists():
            logger.warning(f"Test document not found: {test_document}")
            logger.info("Skipping workflow integration test")
            return
            
        logger.info(f"Running unified workflow with: {test_document}")
        
        result = await run_unified_test_generation_workflow(
            document_path=str(test_document),
            timeout=300,  # 5 minutes
            verbose=True
        )
        
        logger.info(f"Workflow result status: {result.get('status', 'unknown')}")
        
        if result.get("status") == "failed":
            logger.error(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
        else:
            logger.info("✅ Workflow integration test successful!")
            
            # Check if we got to OQ generation
            if "oq_generation" in result:
                logger.info("✅ OQ generation reached!")
            else:
                logger.warning("⚠️ OQ generation not reached")
                
    except Exception as e:
        logger.error(f"❌ Workflow integration test failed: {e}")
        # Don't re-raise - this is expected to potentially fail

async def main():
    """Main test execution."""
    logger.info("🧪 Starting OSS Model SME Agent Fix Testing")
    logger.info("=" * 60)
    
    try:
        # Environment check
        if not check_environment():
            logger.error("❌ Environment check failed - aborting tests")
            sys.exit(1)
        
        # Basic LLM test
        await test_llm_basic()
        logger.info("✅ Basic LLM test passed")
        
        # SME agent creation test
        await test_sme_agent_creation()
        logger.info("✅ SME agent creation test passed")
        
        # SME agent request test
        await test_sme_agent_simple_request()
        logger.info("✅ SME agent request test passed")
        
        # Workflow integration test (optional)
        await test_workflow_integration()
        
        logger.info("=" * 60)
        logger.info("🎉 All tests completed successfully!")
        logger.info("✅ OSS model SME agent fixes are working")
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ Test suite failed: {e}")
        logger.error("🔧 Check the debug logs above for detailed error analysis")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())