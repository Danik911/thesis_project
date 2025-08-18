#!/usr/bin/env python3
"""
Cross-Validation Test Script for GAMP-5 Pharmaceutical System

This script tests the fixes for:
1. LlamaIndex callback manager conflicts
2. GAMP categorization accuracy (URS-001 should be Category 3)
3. Phoenix observability integration

Usage:
    python test_cross_validation.py
"""

import asyncio
import logging
import sys
import traceback
from pathlib import Path

# Add main to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.agents.categorization.agent import categorize_urs_document, gamp_analysis_tool
from src.agents.parallel.context_provider import create_context_provider_agent
from src.core.events import AgentRequestEvent
from datetime import UTC, datetime
from uuid import uuid4


def setup_logging():
    """Setup detailed logging for test analysis."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def test_gamp_categorization_fix():
    """Test 1: Verify URS-001 categorizes correctly as Category 3."""
    logger = logging.getLogger("test_categorization")
    logger.info("🧪 Testing GAMP Categorization Fix")
    
    # URS-001 content from testing_data.md
    urs_001_content = """
Environmental Monitoring System (EMS)
Target Category: 3 (Clear)
System Type: Continuous Temperature and Humidity Monitoring

This URS defines the requirements for an Environmental Monitoring System to monitor critical storage areas for temperature-sensitive pharmaceutical products.

Functional Requirements:
- The system shall continuously monitor temperature in all GMP storage areas.
- Temperature readings shall be recorded at intervals not exceeding 5 minutes.
- The system shall use vendor-supplied software without modification.
- Temperature range: -80°C to +50°C with accuracy of ±0.5°C.
- The system shall generate alerts when temperature deviates ±2°C from setpoint.
- All data shall be stored in the vendor's standard database format.
- Standard reports provided by vendor shall be used for batch release.

Regulatory Requirements:
- System shall maintain an audit trail per 21 CFR Part 11.
- Electronic signatures shall use vendor's built-in functionality.
- Data shall be retained for 7 years using vendor's archival feature.
"""
    
    try:
        # Test the rule-based analysis first
        logger.info("Testing rule-based GAMP analysis...")
        analysis_result = gamp_analysis_tool(urs_001_content)
        
        logger.info(f"Analysis result keys: {list(analysis_result.keys())}")
        logger.info(f"Predicted category: {analysis_result['predicted_category']}")
        logger.info(f"Evidence: {analysis_result['evidence']}")
        
        # Print debug scoring information
        if "debug_scoring" in analysis_result.get("evidence", {}):
            logger.info("Scoring breakdown:")
            for debug_line in analysis_result["evidence"]["debug_scoring"]:
                logger.info(f"  {debug_line}")
        
        # Test full categorization
        logger.info("Testing full categorization with LLM...")
        result = categorize_urs_document(
            urs_content=urs_001_content,
            document_name="URS-001-EMS-CrossValidation-Test",
            verbose=True
        )
        
        # Evaluate results
        category = result.gamp_category.value
        confidence = result.confidence_score
        
        logger.info(f"✅ GAMP Categorization Results:")
        logger.info(f"   Category: {category} (Expected: 3)")
        logger.info(f"   Confidence: {confidence:.1%}")
        
        success = category == 3 and confidence >= 0.85
        logger.info(f"   Status: {'✅ PASS' if success else '❌ FAIL'}")
        
        if not success:
            logger.error(f"❌ Categorization failed - Category {category} with {confidence:.1%} confidence")
            logger.error("This indicates pattern matching or scoring issues")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Categorization test failed with exception: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False


async def test_context_provider_callback_fix():
    """Test 2: Verify context provider works without callback conflicts."""
    logger = logging.getLogger("test_context_provider")
    logger.info("🧪 Testing Context Provider Callback Fix")
    
    try:
        # Create context provider agent
        logger.info("Creating context provider agent...")
        context_provider = create_context_provider_agent(
            verbose=True,
            enable_phoenix=True,
            max_documents=10
        )
        
        logger.info("✅ Context provider created successfully")
        
        # Test embedding operation (this would fail with callback conflicts)
        logger.info("Testing embedding operation...")
        
        # Create a simple request to test embedding
        test_request_data = {
            "gamp_category": "3",
            "test_strategy": {"test_types": ["operational_qualification"]},
            "document_sections": ["functional_requirements"],
            "search_scope": {"focus_areas": ["gamp_category_3"]},
            "correlation_id": uuid4(),
            "timeout_seconds": 60
        }
        
        request_event = AgentRequestEvent(
            agent_type="context_provider",
            request_data=test_request_data,
            correlation_id=test_request_data["correlation_id"],
            timestamp=datetime.now(UTC)
        )
        
        # This should not fail with callback conflicts
        result = await context_provider.process_request(request_event)
        
        logger.info(f"✅ Context provider request processed successfully")
        logger.info(f"   Success: {result.success}")
        logger.info(f"   Processing time: {result.processing_time:.2f}s")
        
        return result.success
        
    except Exception as e:
        logger.error(f"❌ Context provider test failed: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False


def test_phoenix_connectivity():
    """Test 3: Check Phoenix UI accessibility."""
    logger = logging.getLogger("test_phoenix")
    logger.info("🧪 Testing Phoenix Connectivity")
    
    try:
        import requests
        response = requests.get("http://localhost:6006", timeout=5)
        
        if response.status_code == 200:
            logger.info("✅ Phoenix UI accessible at http://localhost:6006")
            return True
        else:
            logger.error(f"❌ Phoenix UI returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ Phoenix UI not accessible at http://localhost:6006")
        logger.info("💡 Run 'launch_phoenix.bat' to start Phoenix server")
        return False
    except Exception as e:
        logger.error(f"❌ Phoenix connectivity test failed: {e}")
        return False


async def run_cross_validation_test():
    """Run comprehensive cross-validation test."""
    logger = setup_logging()
    logger.info("🚀 Starting Cross-Validation Fixes Test")
    logger.info("=" * 60)
    
    results = {}
    
    # Test 1: GAMP Categorization
    results["categorization"] = test_gamp_categorization_fix()
    
    # Test 2: Context Provider Callback Fix
    results["context_provider"] = await test_context_provider_callback_fix()
    
    # Test 3: Phoenix Connectivity
    results["phoenix"] = test_phoenix_connectivity()
    
    # Summary
    logger.info("=" * 60)
    logger.info("🔍 CROSS-VALIDATION TEST RESULTS")
    logger.info("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name.upper():20} {status}")
    
    all_passed = all(results.values())
    overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
    logger.info(f"\nOVERALL STATUS: {overall_status}")
    
    if all_passed:
        logger.info("\n🎉 Cross-validation fixes are working correctly!")
        logger.info("You can now run cross-validation tests with confidence.")
    else:
        logger.info("\n⚠️  Some issues remain. Check the logs above for details.")
        
        # Specific guidance
        if not results["categorization"]:
            logger.info("🔧 Categorization issue: Check pattern matching and scoring logic")
        if not results["context_provider"]:
            logger.info("🔧 Context provider issue: Check callback manager initialization")
        if not results["phoenix"]:
            logger.info("🔧 Phoenix issue: Run launch_phoenix.bat to start Phoenix server")
    
    return all_passed


def run_actual_cross_validation():
    """Run a simplified cross-validation test to verify fixes work in practice."""
    logger = logging.getLogger("cross_validation")
    logger.info("🧪 Running Actual Cross-Validation Test")
    
    # Simple test data for cross-validation
    test_documents = [
        {
            "name": "URS-001-EMS",
            "content": """Environmental Monitoring System using vendor-supplied software without modification.
                         All data stored in vendor's standard database format.
                         Standard reports provided by vendor for batch release.""",
            "expected_category": 3
        },
        {
            "name": "URS-002-Custom",
            "content": """Custom-developed system with proprietary algorithms.
                         Bespoke solution with custom code development.
                         Unique business logic implementation.""",
            "expected_category": 5
        }
    ]
    
    try:
        # Simulate cross-validation by processing multiple documents
        results = []
        for doc in test_documents:
            logger.info(f"Processing {doc['name']}...")
            
            result = categorize_urs_document(
                urs_content=doc["content"],
                document_name=doc["name"],
                verbose=False
            )
            
            success = result.gamp_category.value == doc["expected_category"]
            results.append(success)
            
            logger.info(f"  Expected: Category {doc['expected_category']}")
            logger.info(f"  Got: Category {result.gamp_category.value}")
            logger.info(f"  Confidence: {result.confidence_score:.1%}")
            logger.info(f"  Result: {'✅ PASS' if success else '❌ FAIL'}")
        
        overall_success = all(results)
        logger.info(f"\nCross-validation test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        return overall_success
        
    except Exception as e:
        logger.error(f"❌ Cross-validation test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 GAMP-5 Cross-Validation Fixes Test")
    print("=====================================")
    
    # Run comprehensive test
    success = asyncio.run(run_cross_validation_test())
    
    if success:
        print("\n🧪 Running actual cross-validation test...")
        cv_success = run_actual_cross_validation()
        if cv_success:
            print("\n🎉 ALL TESTS PASSED - Cross-validation fixes are working!")
        else:
            print("\n⚠️  Cross-validation test failed - check categorization logic")
    
    sys.exit(0 if success else 1)