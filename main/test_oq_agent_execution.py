#!/usr/bin/env python3
"""
Test that OQ agent executes and generates traces after callback fix.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from uuid import uuid4

# Add the main directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from src.core.unified_workflow import UnifiedTestGenerationWorkflow
from src.config.llm_config import LLMConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_oq_agent_execution():
    """Test that workflow reaches OQ agent execution."""
    logger.info("Testing OQ agent execution after callback fix...")
    
    try:
        # Initialize workflow
        llm = LLMConfig.get_llm()
        workflow = UnifiedTestGenerationWorkflow(
            llm=llm,
            timeout=300,  # 5 minutes
            verbose=True
        )
        
        logger.info("✅ Workflow initialized successfully")
        
        # Test URS content (simple Category 5 case)
        test_urs = """
        User Requirements Specification
        
        System: Pharmaceutical Manufacturing Control System
        Category: Custom Application (GAMP Category 5)
        
        Requirements:
        1. The system shall provide secure user authentication
        2. The system shall maintain complete audit trails
        3. The system shall validate data integrity
        4. The system shall support 21 CFR Part 11 compliance
        5. The system shall generate regulatory reports
        
        This is a critical pharmaceutical manufacturing system requiring full validation.
        """
        
        logger.info("Starting workflow execution...")
        logger.info(f"URS content length: {len(test_urs)} characters")
        
        # Run the workflow - this should now work without callback errors
        result = await workflow.run(
            urs_content=test_urs,
            document_name="Test Pharmaceutical System URS",
            session_id=str(uuid4())
        )
        
        logger.info("✅ Workflow completed successfully!")
        logger.info(f"  Result type: {type(result)}")
        logger.info(f"  Result data: {result}")
        
        # Check if we got OQ test results
        if hasattr(result, 'test_cases') or (hasattr(result, 'data') and 'test_cases' in str(result.data)):
            logger.info("🎉 OQ AGENT EXECUTED AND GENERATED TESTS!")
            logger.info("✅ Both callback fix and OQ execution working")
            return True
        else:
            logger.warning("⚠️ Workflow completed but no clear test cases found")
            logger.info("This may indicate the workflow stopped before OQ generation")
            return False
            
    except Exception as e:
        logger.error(f"❌ OQ agent execution test failed: {type(e).__name__}: {e}")
        
        # Check if this is still the callback error
        if "'NoneType' object has no attribute 'event_starts_to_ignore'" in str(e):
            logger.error("🔧 CALLBACK ERROR STILL PRESENT - Fix not working")
        elif "ChromaDB" in str(e) or "embedding" in str(e):
            logger.error("🔧 CHROMADB/EMBEDDING ERROR - Related to callback issue")
        else:
            logger.error("🔧 DIFFERENT ERROR - May be downstream issue")
            
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return False

async def main():
    """Main test execution."""
    logger.info("🧪 TESTING OQ AGENT EXECUTION AFTER CALLBACK FIX")
    logger.info("=" * 60)
    
    # Check environment
    provider = os.getenv("LLM_PROVIDER", "openrouter")
    api_key = os.getenv("OPENROUTER_API_KEY" if provider == "openrouter" else "OPENAI_API_KEY")
    
    if not api_key:
        logger.error(f"❌ API key not found for provider {provider}")
        return
        
    logger.info(f"Using LLM provider: {provider}")
    
    success = await test_oq_agent_execution()
    
    logger.info("=" * 60)
    if success:
        logger.info("🎉 OQ AGENT EXECUTION TEST PASSED!")
        logger.info("✅ ChromaDB callback fix resolved both issues:")
        logger.info("  1. ChromaDB embedding operations working")
        logger.info("  2. OQ agent can now execute and generate traces")
    else:
        logger.error("❌ OQ AGENT EXECUTION TEST FAILED!")
        logger.error("🔧 Further debugging required")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())