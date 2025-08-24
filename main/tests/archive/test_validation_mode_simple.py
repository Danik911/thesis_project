#!/usr/bin/env python3
"""
Simple test for validation mode bypass logic - Task 21

Tests the core bypass logic without running the full workflow.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the main source directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "main" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.core.events import (
    ConsultationBypassedEvent,
    GAMPCategorizationEvent,
    GAMPCategory,
)
from src.core.unified_workflow import UnifiedTestGenerationWorkflow
from src.shared.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_bypass_logic_directly():
    """Test the bypass logic directly by calling the check_consultation_required step."""
    logger.info("🧪 Testing Validation Mode Bypass Logic Directly")

    # Create a Category 5 event with high confidence (should still require consultation due to category)
    categorization_event = GAMPCategorizationEvent(
        gamp_category=GAMPCategory.CATEGORY_5,
        confidence_score=0.85,  # High confidence but Category 5 still needs consultation
        justification="Custom LIMS with proprietary algorithms",
        risk_assessment={"risk_level": "high", "custom_development": True},
        categorized_by="test_system"
    )

    logger.info(f"📋 Test Event: Category {categorization_event.gamp_category.value}, Confidence: {categorization_event.confidence_score}")

    # Test 1: Production mode (validation_mode=False)
    logger.info("🔄 Test 1: Production Mode (should require consultation)")
    config = get_config()
    config.validation_mode.validation_mode = False

    workflow = UnifiedTestGenerationWorkflow(verbose=True)

    # Create a mock context
    class MockContext:
        def __init__(self):
            self.store_data = {}
            self.events_sent = []

        async def store_get(self, key):
            return self.store_data.get(key)

        async def store_set(self, key, value):
            self.store_data[key] = value

        def send_event(self, event):
            self.events_sent.append(event)

    # Mock the safe_context_set and safe_context_get functions
    async def mock_safe_context_set(ctx, key, value):
        await ctx.store_set(key, value)

    # Replace the safe context functions temporarily
    import src.core.unified_workflow
    original_safe_context_set = src.core.unified_workflow.safe_context_set
    src.core.unified_workflow.safe_context_set = mock_safe_context_set

    try:
        # Mock context with store attribute
        mock_ctx = MockContext()
        mock_ctx.store = mock_ctx  # Make store point to self for get/set methods

        # Test production mode
        result = await workflow.check_consultation_required(mock_ctx, categorization_event)

        production_test_passed = hasattr(result, "consultation_type") and result.consultation_type == "categorization_review"
        logger.info(f"✅ Production mode result: {type(result).__name__} - Requires consultation: {production_test_passed}")

        # Test 2: Validation mode (validation_mode=True)
        logger.info("🔄 Test 2: Validation Mode (should bypass consultation)")
        config.validation_mode.validation_mode = True

        # Reset context
        mock_ctx = MockContext()
        mock_ctx.store = mock_ctx

        result = await workflow.check_consultation_required(mock_ctx, categorization_event)

        validation_test_passed = isinstance(result, ConsultationBypassedEvent)
        logger.info(f"✅ Validation mode result: {type(result).__name__} - Bypass used: {validation_test_passed}")

        if validation_test_passed:
            logger.info(f"   📊 Bypass details: {result.bypass_reason}")
            logger.info(f"   📊 Original consultation: {result.original_consultation.consultation_type}")
            logger.info(f"   📊 Audit trail: {result.audit_trail_preserved}")

        # Overall success
        overall_success = production_test_passed and validation_test_passed

        logger.info("=" * 60)
        logger.info("📋 BYPASS LOGIC TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Production mode (requires consultation): {production_test_passed}")
        logger.info(f"✅ Validation mode (bypasses consultation): {validation_test_passed}")
        logger.info(f"🎯 Overall success: {overall_success}")
        logger.info("=" * 60)

        return {
            "production_mode_passed": production_test_passed,
            "validation_mode_passed": validation_test_passed,
            "overall_success": overall_success
        }

    finally:
        # Restore original function
        src.core.unified_workflow.safe_context_set = original_safe_context_set
        # Reset config
        config.validation_mode.validation_mode = False


if __name__ == "__main__":
    # Set environment variables
    os.environ["VALIDATION_MODE"] = "false"
    os.environ["VALIDATION_MODE_EXPLICIT"] = "true"

    # Run the test
    result = asyncio.run(test_bypass_logic_directly())

    if result["overall_success"]:
        logger.info("🎉 Validation mode bypass logic working correctly!")
        sys.exit(0)
    else:
        logger.error("❌ Validation mode bypass logic needs fixes")
        sys.exit(1)
