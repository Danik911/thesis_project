#!/usr/bin/env python3
"""
Direct OSS Model Test - No Phoenix Instrumentation
Tests the core OSS migration functionality without observability interference.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

# Load environment
load_dotenv("../.env")
os.environ["LLM_PROVIDER"] = "openrouter"
os.environ["PHOENIX_ENABLE_TRACING"] = "false"

sys.path.append(".")

from src.core.categorization_workflow import GAMPCategorizationWorkflow
from src.core.events import URSIngestionEvent


async def test_oss_categorization():
    """Test OSS categorization without Phoenix interference."""
    print("=== OSS Direct Categorization Test ===")
    print(f"LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
    print(f"OPENROUTER_API_KEY: {os.getenv('OPENROUTER_API_KEY', 'NOT SET')[:20]}...")
    print(f"PHOENIX_ENABLE_TRACING: {os.getenv('PHOENIX_ENABLE_TRACING')}")

    # Create proper URSIngestionEvent
    test_content = """
# Test URS - Category 5 System
This is a test document for a Category 5 custom application system.

## Requirements
- URS-001: The system shall implement custom business logic
- URS-002: The system shall integrate with existing databases  
- URS-003: The system shall generate regulatory reports
"""

    try:
        # Create event with all required fields
        event = URSIngestionEvent(
            urs_content=test_content,
            document_name="OSS_Test_Document",
            document_version="1.0",
            author="Test_User",
            correlation_id="oss-test-123"
        )

        # Initialize workflow
        workflow = GAMPCategorizationWorkflow()
        print("Workflow initialized successfully")

        # Run categorization
        print("Starting categorization...")
        result = await workflow.run(ev=event)

        print("Categorization completed!")
        print(f"Result type: {type(result)}")
        print(f"Category: {getattr(result, 'category', 'NOT FOUND')}")
        print(f"Confidence: {getattr(result, 'confidence', 'NOT FOUND')}")
        print(f"Reasoning: {getattr(result, 'reasoning', 'NOT FOUND')[:200]}...")

        return True

    except Exception as e:
        print(f"ERROR: Categorization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_context_provider():
    """Test context provider without Phoenix interference."""
    print("\n=== OSS Context Provider Test ===")

    try:
        from src.agents.parallel.context_provider import (
            ContextProviderAgent,
            ContextProviderRequest,
        )

        agent = ContextProviderAgent()
        print("Context provider initialized")

        # Create test request
        request = ContextProviderRequest(
            gamp_category=5,
            search_scope={
                "documents": ["gamp5_documents", "best_practices"],
                "requirements": ["custom application", "validation"],
                "compliance": ["21 CFR Part 11", "GAMP-5"]
            },
            correlation_id="context-test-123"
        )

        print("Processing context request...")
        result = await agent.process_request(request)

        print("Context provider completed!")
        print(f"Documents found: {result.total_documents}")
        print(f"Context sections: {len(result.context_sections)}")

        return True

    except Exception as e:
        print(f"ERROR: Context provider failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all OSS tests without Phoenix."""
    print("OSS Migration Direct Test Suite")
    print("=" * 50)

    # Test 1: Categorization
    cat_success = await test_oss_categorization()

    # Test 2: Context Provider
    context_success = await test_context_provider()

    print("\n" + "=" * 50)
    print("OSS Migration Test Results:")
    print(f"Categorization: {'PASS' if cat_success else 'FAIL'}")
    print(f"Context Provider: {'PASS' if context_success else 'FAIL'}")
    print(f"Overall: {'PASS' if (cat_success and context_success) else 'FAIL'}")


if __name__ == "__main__":
    asyncio.run(main())
