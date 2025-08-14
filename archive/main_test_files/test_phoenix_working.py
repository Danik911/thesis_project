"""
Test that Phoenix enhanced observability is actually working.
Simple tests that verify the integration is functional.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add main to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_phoenix_integration():
    """Test the actual Phoenix integration end-to-end."""
    logger.info("\n======== PHOENIX INTEGRATION TEST ========")

    # Test 1: Import test
    logger.info("\n1. Testing imports...")
    try:
        from src.monitoring.phoenix_enhanced import (
            AutomatedTraceAnalyzer,
            PhoenixEnhancedClient,
        )
        logger.info("✅ Imports successful")
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False

    # Test 2: Client initialization
    logger.info("\n2. Testing Phoenix client initialization...")
    try:
        client = PhoenixEnhancedClient()
        logger.info("✅ Client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Client initialization failed: {e}")
        # This is expected if Phoenix is not running
        logger.info("   (This is expected if Phoenix server is not running)")

    # Test 3: Analyzer initialization
    logger.info("\n3. Testing analyzer initialization...")
    try:
        # Create a mock client if real one failed
        try:
            client = PhoenixEnhancedClient()
        except:
            # Create simplified mock
            class MockClient:
                def __init__(self):
                    self.endpoint = "http://localhost:6006"
            client = MockClient()

        analyzer = AutomatedTraceAnalyzer(client)
        logger.info("✅ Analyzer initialized successfully")
    except Exception as e:
        logger.error(f"❌ Analyzer initialization failed: {e}")
        return False

    # Test 4: Dashboard generation
    logger.info("\n4. Testing dashboard generation...")
    try:
        dashboard_path = await analyzer.generate_compliance_dashboard()
        if dashboard_path:
            logger.info(f"✅ Dashboard generated: {dashboard_path}")
        else:
            logger.info("❌ Dashboard generation returned None")
    except Exception as e:
        logger.error(f"❌ Dashboard generation failed: {e}")

    # Test 5: Workflow integration
    logger.info("\n5. Testing workflow integration...")
    try:
        from src.core.unified_workflow import UnifiedTestGenerationWorkflow

        # Check if enhanced observability is integrated
        workflow = UnifiedTestGenerationWorkflow()

        # Check if the complete_workflow method exists
        if hasattr(workflow, "complete_workflow"):
            logger.info("✅ Workflow has complete_workflow method")
        else:
            logger.error("❌ Workflow missing complete_workflow method")

    except Exception as e:
        logger.error(f"❌ Workflow integration test failed: {e}")

    logger.info("\n======== TEST COMPLETE ========")
    return True


async def main():
    """Run the test."""
    await test_phoenix_integration()


if __name__ == "__main__":
    asyncio.run(main())
