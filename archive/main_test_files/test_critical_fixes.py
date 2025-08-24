#!/usr/bin/env python3
"""
Test script to validate critical workflow failure fixes.
This script tests each fix incrementally to ensure they work correctly.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the main directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from uuid import uuid4

from src.agents.parallel.context_provider import ContextProviderRequest
from src.core.events import AgentRequestEvent, GAMPCategory

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_context_provider_type_conversion():
    """Test Fix 1: Context Provider Type Conversion"""
    logger.info("🧪 Testing Fix 1: Context Provider Type Conversion")

    try:
        # Test with integer (old broken behavior)
        gamp_category_int = 5

        # Test with direct ContextProviderRequest creation (what was failing)
        request_data = {
            "gamp_category": gamp_category_int,  # Integer
            "test_strategy": {"approach": "test"},
            "document_sections": ["requirements"],
            "search_scope": {},
            "correlation_id": uuid4()
        }

        # This should now work with our Pydantic validator
        request = ContextProviderRequest(**request_data)

        # Verify conversion worked
        assert isinstance(request.gamp_category, str)
        assert request.gamp_category == "5"

        logger.info("✅ Fix 1 PASSED: Integer to string conversion works")

        # Test with string (should also work)
        request_data["gamp_category"] = "3"
        request2 = ContextProviderRequest(**request_data)
        assert request2.gamp_category == "3"

        logger.info("✅ Fix 1 PASSED: String input also works")

        # Test with GAMPCategory enum value
        request_data["gamp_category"] = GAMPCategory.CATEGORY_4.value
        request3 = ContextProviderRequest(**request_data)
        assert request3.gamp_category == "4"

        logger.info("✅ Fix 1 PASSED: GAMPCategory enum value conversion works")

        return True

    except Exception as e:
        logger.error(f"❌ Fix 1 FAILED: {e}")
        return False

def test_unified_workflow_request_creation():
    """Test the unified workflow request creation fix"""
    logger.info("🧪 Testing Unified Workflow Request Creation")

    try:
        # Simulate the fixed unified workflow request creation
        gamp_category = GAMPCategory.CATEGORY_5

        # This is the fixed code from unified_workflow.py
        agent_request = {
            "agent_type": "context_provider",
            "request_data": {
                "gamp_category": str(gamp_category.value),  # Explicit string conversion
                "test_strategy": {"approach": "category_based"},
                "document_sections": ["functional_requirements", "validation_requirements"],
                "search_scope": {}  # Added required field
            },
            "correlation_id": "ctx_test_session"
        }

        # Create AgentRequestEvent (simulating workflow)
        request_event = AgentRequestEvent(
            agent_type=agent_request["agent_type"],
            request_data=agent_request["request_data"],
            correlation_id=uuid4(),
            requesting_step="test",
            session_id="test_session"
        )

        # Test creating ContextProviderRequest from this event
        request = ContextProviderRequest(
            **request_event.request_data,
            correlation_id=request_event.correlation_id
        )

        assert request.gamp_category == "5"
        assert "search_scope" in request_event.request_data

        logger.info("✅ Unified Workflow Request Creation PASSED")
        return True

    except Exception as e:
        logger.error(f"❌ Unified Workflow Request Creation FAILED: {e}")
        return False

def test_phoenix_config_improvements():
    """Test Phoenix configuration improvements"""
    logger.info("🧪 Testing Phoenix Configuration Improvements")

    try:
        from src.monitoring.phoenix_config import PhoenixConfig, PhoenixManager

        # Test configuration creation
        config = PhoenixConfig()
        assert config.enable_tracing
        assert config.enable_openai_instrumentation
        assert config.enable_chromadb_instrumentation

        logger.info("✅ Phoenix Config Creation PASSED")

        # Test manager creation (without actual setup to avoid dependencies)
        manager = PhoenixManager(config)
        assert manager.config == config
        assert not manager._initialized  # Should not be initialized yet

        logger.info("✅ Phoenix Manager Creation PASSED")
        return True

    except Exception as e:
        logger.error(f"❌ Phoenix Configuration Test FAILED: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🚀 Starting Critical Fixes Validation")

    results = []

    # Test each fix
    results.append(test_context_provider_type_conversion())
    results.append(test_unified_workflow_request_creation())
    results.append(test_phoenix_config_improvements())

    # Summary
    passed = sum(results)
    total = len(results)

    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 ALL CRITICAL FIXES VALIDATED SUCCESSFULLY!")
        return True
    logger.error("❌ Some critical fixes failed validation")
    return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
