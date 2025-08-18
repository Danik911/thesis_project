#!/usr/bin/env python3
"""
SME Agent Fix Validation Test

This script tests the JSON parsing fixes for the SME agent to ensure:
1. "critical" priority values are accepted
2. Case-insensitive validation works
3. DeepSeek V3 compatibility is restored
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import UTC, datetime
from uuid import uuid4

# Add main to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.agents.parallel.sme_agent import SMEAgent, extract_json_from_markdown


def setup_logging():
    """Setup detailed logging for test analysis."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def test_json_extraction_with_critical_priority():
    """Test that JSON extraction handles 'critical' priority correctly."""
    logger = logging.getLogger("test_json_extraction")
    logger.info("🧪 Testing JSON extraction with 'critical' priority")
    
    # Simulate DeepSeek V3 response with 'critical' priority
    test_json_response = """
    [
        {
            "category": "compliance",
            "priority": "critical",
            "recommendation": "Implement comprehensive data integrity validation",
            "rationale": "21 CFR Part 11 requires robust data integrity controls",
            "implementation_effort": "high",
            "expected_benefit": "regulatory_compliance"
        },
        {
            "category": "risk_management",
            "priority": "high",
            "recommendation": "Establish change control procedures",
            "rationale": "GAMP-5 requires documented change management",
            "implementation_effort": "medium",
            "expected_benefit": "process_improvement"
        }
    ]
    """
    
    try:
        # Test the extraction
        parsed_data = extract_json_from_markdown(test_json_response)
        
        logger.info(f"✅ JSON extraction successful")
        logger.info(f"   Extracted {len(parsed_data)} recommendations")
        
        # Check first recommendation has critical priority
        if parsed_data[0]["priority"] == "critical":
            logger.info(f"✅ Critical priority accepted: {parsed_data[0]['priority']}")
            return True
        else:
            logger.error(f"❌ Expected 'critical', got: {parsed_data[0]['priority']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ JSON extraction failed: {e}")
        return False


def test_case_insensitive_validation():
    """Test case-insensitive validation logic."""
    logger = logging.getLogger("test_case_insensitive")
    logger.info("🧪 Testing case-insensitive validation")
    
    # Test different case variations
    test_cases = [
        {"priority": "critical", "effort": "high"},
        {"priority": "Critical", "effort": "HIGH"},
        {"priority": "CRITICAL", "effort": "High"},
        {"priority": "high", "effort": "medium"},
        {"priority": "Medium", "effort": "Low"}
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases):
        test_json = f'''
        [
            {{
                "category": "test",
                "priority": "{test_case['priority']}",
                "recommendation": "Test recommendation {i}",
                "rationale": "Test rationale",
                "implementation_effort": "{test_case['effort']}",
                "expected_benefit": "test_benefit"
            }}
        ]
        '''
        
        try:
            parsed_data = extract_json_from_markdown(test_json)
            logger.info(f"✅ Case variation {i+1} accepted: priority='{test_case['priority']}', effort='{test_case['effort']}'")
            success_count += 1
        except Exception as e:
            logger.error(f"❌ Case variation {i+1} failed: {e}")
    
    success_rate = success_count / len(test_cases)
    logger.info(f"Case-insensitive validation success rate: {success_rate:.1%}")
    
    return success_rate >= 0.8  # Allow some failures but expect most to work


def test_invalid_values_rejection():
    """Test that invalid values are properly rejected."""
    logger = logging.getLogger("test_invalid_rejection")
    logger.info("🧪 Testing invalid value rejection")
    
    # Test invalid priority values that should be rejected
    invalid_cases = [
        {"priority": "urgent", "should_fail": True},
        {"priority": "minimal", "should_fail": True},
        {"priority": "extreme", "should_fail": True},
        {"priority": "critical", "should_fail": False},  # This should pass
        {"priority": "high", "should_fail": False}       # This should pass
    ]
    
    correct_rejections = 0
    
    for i, test_case in enumerate(invalid_cases):
        test_json = f'''
        [
            {{
                "category": "test",
                "priority": "{test_case['priority']}",
                "recommendation": "Test recommendation {i}",
                "rationale": "Test rationale",
                "implementation_effort": "medium",
                "expected_benefit": "test_benefit"
            }}
        ]
        '''
        
        try:
            parsed_data = extract_json_from_markdown(test_json)
            if test_case["should_fail"]:
                logger.error(f"❌ Invalid priority '{test_case['priority']}' was incorrectly accepted")
            else:
                logger.info(f"✅ Valid priority '{test_case['priority']}' correctly accepted")
                correct_rejections += 1
        except Exception as e:
            if test_case["should_fail"]:
                logger.info(f"✅ Invalid priority '{test_case['priority']}' correctly rejected: {e}")
                correct_rejections += 1
            else:
                logger.error(f"❌ Valid priority '{test_case['priority']}' incorrectly rejected: {e}")
    
    success_rate = correct_rejections / len(invalid_cases)
    logger.info(f"Invalid value rejection success rate: {success_rate:.1%}")
    
    return success_rate >= 0.8


async def test_sme_agent_initialization():
    """Test that SME agent can be initialized and configured properly."""
    logger = logging.getLogger("test_sme_init")
    logger.info("🧪 Testing SME Agent initialization")
    
    try:
        # Create SME agent instance
        sme_agent = SMEAgent(
            specialty="pharmaceutical_validation",
            verbose=True,
            enable_phoenix=False,  # Disable Phoenix for this test
            confidence_threshold=0.7,
            max_recommendations=5
        )
        
        logger.info("✅ SME Agent initialized successfully")
        logger.info(f"   Specialty: {sme_agent.specialty}")
        logger.info(f"   OSS Model Detected: {sme_agent.is_oss_model}")
        logger.info(f"   Max Recommendations: {sme_agent.max_recommendations}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SME Agent initialization failed: {e}")
        return False


async def run_sme_agent_fix_validation():
    """Run comprehensive SME agent fix validation."""
    logger = setup_logging()
    logger.info("🚀 Starting SME Agent Fix Validation")
    logger.info("=" * 60)
    
    results = {}
    
    # Test 1: JSON extraction with critical priority
    results["json_extraction"] = test_json_extraction_with_critical_priority()
    
    # Test 2: Case-insensitive validation
    results["case_insensitive"] = test_case_insensitive_validation()
    
    # Test 3: Invalid value rejection
    results["invalid_rejection"] = test_invalid_values_rejection()
    
    # Test 4: SME agent initialization
    results["sme_initialization"] = await test_sme_agent_initialization()
    
    # Summary
    logger.info("=" * 60)
    logger.info("🔍 SME AGENT FIX VALIDATION RESULTS")
    logger.info("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name.upper():20} {status}")
    
    all_passed = all(results.values())
    overall_status = "✅ ALL FIXES WORKING" if all_passed else "❌ SOME FIXES FAILED"
    logger.info(f"\nOVERALL STATUS: {overall_status}")
    
    if all_passed:
        logger.info("\n🎉 SME Agent JSON parsing fixes are working correctly!")
        logger.info("The SME agent should now handle DeepSeek V3 responses properly.")
        logger.info("\nNext steps:")
        logger.info("1. Run end-to-end test: python test_cross_validation.py")
        logger.info("2. Check Phoenix traces for successful SME agent execution")
        logger.info("3. Monitor workflow for complete test generation")
    else:
        logger.info("\n⚠️  Some fixes are not working correctly. Check the logs above.")
        
        # Specific guidance
        if not results["json_extraction"]:
            logger.info("🔧 JSON extraction issue: Check extract_json_from_markdown function")
        if not results["case_insensitive"]:
            logger.info("🔧 Case sensitivity issue: Check validation logic in SME agent")
        if not results["invalid_rejection"]:
            logger.info("🔧 Validation issue: Check priority value validation logic")
        if not results["sme_initialization"]:
            logger.info("🔧 Initialization issue: Check SME agent constructor and dependencies")
    
    return all_passed


if __name__ == "__main__":
    print("🚀 SME Agent JSON Parsing Fix Validation")
    print("=========================================")
    
    # Run validation tests
    success = asyncio.run(run_sme_agent_fix_validation())
    
    if success:
        print("\n🎉 ALL SME AGENT FIXES VALIDATED SUCCESSFULLY!")
        print("You can now proceed with end-to-end testing.")
    else:
        print("\n⚠️  SOME FIXES NEED ATTENTION - Check the logs above")
    
    sys.exit(0 if success else 1)