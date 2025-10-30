#!/usr/bin/env python3
"""Direct test of OQ generation to isolate the issue."""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime, UTC
from uuid import uuid4

# Set environment
os.environ['VALIDATION_MODE'] = 'true'
os.environ['OPENAI_API_KEY'] = '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'
os.environ['OPENROUTER_API_KEY'] = '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'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path.cwd()))

from src.agents.oq_generator.workflow import OQGenerationWorkflow
from src.agents.oq_generator.events import OQTestGenerationEvent
from src.core.events import GAMPCategory

async def test_direct_oq():
    """Test OQ generation directly without the full workflow."""
    logger.info("=" * 60)
    logger.info("DIRECT OQ GENERATION TEST")
    logger.info("=" * 60)
    
    # Create minimal test event
    test_event = OQTestGenerationEvent(
        gamp_category=GAMPCategory.CATEGORY_3,
        urs_content="Simple test system with basic requirements",
        document_metadata={"name": "test.md"},
        required_test_count=3,  # Only 3 tests for speed
        test_strategy={"focus": "basic functionality"},
        aggregated_context={
            "context_provider": {"documents": []},
            "sme_agent": {"recommendations": []},
            "research_agent": {"findings": []}
        },
        categorization_confidence=0.8,
        event_id=uuid4(),
        timestamp=datetime.now(UTC),
        correlation_id=uuid4()
    )
    
    try:
        logger.info("Creating OQ workflow...")
        oq_workflow = OQGenerationWorkflow(timeout=60)
        
        logger.info("Starting OQ generation with minimal data...")
        start_time = asyncio.get_event_loop().time()
        
        # Run with direct event data
        result = await asyncio.wait_for(
            oq_workflow.run(data={
                "gamp_category": 3,
                "urs_content": "Simple test system",
                "document_metadata": {"name": "test.md"},
                "required_test_count": 3,
                "test_strategy": {},
                "agent_results": {},
                "categorization_confidence": 0.8,
                "correlation_id": str(uuid4())
            }),
            timeout=60
        )
        
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info(f"OQ generation completed in {elapsed:.2f} seconds")
        
        logger.info(f"Result type: {type(result)}")
        
        if hasattr(result, 'test_suite'):
            suite = result.test_suite
            if hasattr(suite, 'test_cases'):
                logger.info(f"✅ SUCCESS: Generated {len(suite.test_cases)} test cases")
                for i, test in enumerate(suite.test_cases[:2], 1):
                    logger.info(f"  Test {i}: {test.test_id}")
                return True
        
        logger.info("❌ FAILED: No test cases in result")
        return False
        
    except asyncio.TimeoutError:
        logger.error("❌ TIMEOUT: OQ generation took more than 60 seconds")
        return False
    except Exception as e:
        logger.error(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_direct_oq())
    sys.exit(0 if success else 1)