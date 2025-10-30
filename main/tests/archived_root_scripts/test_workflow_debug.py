#!/usr/bin/env python3
"""Debug script to test workflow execution with detailed logging."""

import sys
import os
import logging
from pathlib import Path

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_workflow():
    """Test the workflow with debugging."""
    try:
        logger.info("Starting workflow debug test...")
        
        # Test imports
        logger.info("Testing imports...")
        from src.core.unified_workflow import UnifiedTestGenerationWorkflow
        logger.info("✓ UnifiedTestGenerationWorkflow imported")
        
        from src.config.llm_config import LLMConfig
        logger.info("✓ LLMConfig imported")
        
        # Test LLM initialization
        logger.info("Testing LLM initialization...")
        llm = LLMConfig.get_llm()
        logger.info(f"✓ LLM initialized: {llm}")
        
        # Test security imports
        logger.info("Testing security imports...")
        from src.security import SecureLLMWrapper
        logger.info("✓ SecureLLMWrapper imported")
        
        # Test compliance imports
        logger.info("Testing compliance imports...")
        from src.compliance import get_rbac_system
        rbac = get_rbac_system()
        logger.info(f"✓ RBAC system initialized: {rbac}")
        
        # Read test document
        test_file = Path("tests/test_data/gamp5_test_data/testing_data.md")
        if not test_file.exists():
            logger.error(f"Test file not found: {test_file}")
            return
        
        with open(test_file, 'r', encoding='utf-8') as f:
            urs_content = f.read()
        logger.info(f"✓ Test document loaded: {len(urs_content)} chars")
        
        # Create workflow
        logger.info("Creating workflow instance...")
        workflow = UnifiedTestGenerationWorkflow()
        logger.info("✓ Workflow created")
        
        # Run workflow with timeout
        logger.info("Starting workflow execution...")
        import asyncio
        
        async def run_with_timeout():
            try:
                result = await asyncio.wait_for(
                    workflow.run(
                        urs_content=urs_content,
                        document_name="testing_data.md",
                        document_path=str(test_file),  # Add document path
                        document_version="1.0",
                        author="test"
                    ),
                    timeout=60.0  # Increase timeout to 60 seconds
                )
                return result
            except asyncio.TimeoutError:
                logger.error("Workflow timed out after 60 seconds")
                return None
        
        result = asyncio.run(run_with_timeout())
        
        if result:
            logger.info(f"✓ Workflow completed: {result}")
        else:
            logger.error("Workflow failed or timed out")
            
    except Exception as e:
        logger.error(f"Error during workflow test: {e}", exc_info=True)

if __name__ == "__main__":
    test_workflow()