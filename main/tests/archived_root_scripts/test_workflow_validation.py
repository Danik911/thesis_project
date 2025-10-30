#!/usr/bin/env python3
"""Test script to validate workflow with VALIDATION_MODE bypass."""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Set environment variables before imports
os.environ['VALIDATION_MODE'] = 'true'
# Ensure API keys are loaded
if not os.getenv('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = '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'
if not os.getenv('OPENROUTER_API_KEY'):
    os.environ['OPENROUTER_API_KEY'] = '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'

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('workflow_validation_test.log')
    ]
)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.unified_workflow import UnifiedTestGenerationWorkflow

async def test_workflow():
    """Test the workflow with validation bypass."""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Starting Workflow Validation Test")
    logger.info(f"VALIDATION_MODE: {os.getenv('VALIDATION_MODE')}")
    logger.info("=" * 60)
    
    # Test document path
    test_doc = Path("tests/test_data/gamp5_test_data/testing_data.md")
    if not test_doc.exists():
        logger.error(f"Test document not found: {test_doc}")
        return False
    
    try:
        # Initialize workflow
        logger.info("Initializing workflow...")
        workflow = UnifiedTestGenerationWorkflow(verbose=True)
        
        # Run with timeout
        logger.info(f"Running workflow with document: {test_doc}")
        logger.info("Expected behavior: Should bypass consultation and complete")
        
        result = await asyncio.wait_for(
            workflow.run(
                document_path=str(test_doc),
                test_type="OQ",
                compliance_level="high"
            ),
            timeout=300  # 5-minute timeout for testing
        )
        
        logger.info("=" * 60)
        logger.info("WORKFLOW COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        
        if result:
            logger.info(f"Result type: {type(result)}")
            if hasattr(result, 'test_cases'):
                logger.info(f"Generated {len(result.test_cases)} test cases")
            logger.info("Result preview:")
            logger.info(str(result)[:500])
        
        return True
        
    except asyncio.TimeoutError:
        logger.error("=" * 60)
        logger.error("WORKFLOW TIMEOUT - Still hanging after consultation bypass!")
        logger.error("Check if there's another blocking point after consultation")
        logger.error("=" * 60)
        return False
        
    except Exception as e:
        logger.error(f"Workflow failed with error: {e}")
        logger.exception("Full traceback:")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PHARMACEUTICAL TEST GENERATION WORKFLOW - VALIDATION TEST")
    print("=" * 60)
    print()
    print("This test validates that VALIDATION_MODE=true properly bypasses")
    print("human consultation and allows the workflow to complete.")
    print()
    
    success = asyncio.run(test_workflow())
    
    if success:
        print("\nTEST PASSED: Workflow completed with validation bypass")
        sys.exit(0)
    else:
        print("\nTEST FAILED: Workflow still has issues")
        print("Check workflow_validation_test.log for details")
        sys.exit(1)