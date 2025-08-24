#!/usr/bin/env python3
"""
Validation Mode Testing with OpenAI (temporary) - Task 21

This script tests the validation mode implementation using OpenAI model temporarily
while we debug the OpenRouter API key issue. The core validation logic should
work the same regardless of the underlying model.

CRITICAL: This is a temporary workaround to validate the bypass logic implementation
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "main" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "main"))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import src.config.llm_config as llm_config_module
from src.config.llm_config import LLMConfig, ModelProvider
from src.core.events import (
    ConsultationBypassedEvent,
    ConsultationRequiredEvent,
)
from src.core.unified_workflow import run_unified_test_generation_workflow
from src.shared.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_validation_mode_with_real_workflow():
    """Test validation mode with actual workflow execution."""
    logger.info("🧪 Testing Validation Mode with Real Workflow")
    logger.info(f"Using model: {LLMConfig.PROVIDER.value}/{LLMConfig.MODELS[LLMConfig.PROVIDER]['model']}")

    # Use a Category 5 document directly for testing
    category_5_docs = [
        "URS-003.md",  # First Category 5 document
        "URS-014.md",
        "URS-015.md",
        "URS-016.md",
        "URS-017.md"
    ]

    test_doc_name = category_5_docs[0]  # Use URS-003.md
    test_doc_path = Path(__file__).parent / "datasets" / "urs_corpus" / "category_5" / test_doc_name

    if not test_doc_path.exists():
        logger.error(f"❌ Test document not found: {test_doc_path}")
        return False

    logger.info(f"📄 Testing with document: {test_doc_name}")
    logger.info("📋 Expected category: 5 (Category 5 document)")

    results = {"production": None, "validation": None}

    # Test 1: Production mode (should require consultation for Category 5)
    logger.info("\n🔄 Test 1: Production Mode (validation_mode=False)")
    start_time = time.time()

    try:
        result_prod = await run_unified_test_generation_workflow(
            document_path=str(test_doc_path),
            validation_mode=False,  # Production mode
            enable_categorization=True,
            enable_planning=False,  # Skip planning to focus on categorization
            enable_parallel_coordination=False,
            enable_document_processing=False,
            verbose=True
        )

        results["production"] = result_prod
        prod_time = time.time() - start_time

        # Analyze results
        categorization = result_prod.get("categorization", {})
        category = categorization.get("gamp_category", {}).get("value", 0)
        confidence = categorization.get("confidence_score", 0.0)

        workflow_events = result_prod.get("workflow_events", [])
        consultation_events = [e for e in workflow_events if isinstance(e, ConsultationRequiredEvent)]

        logger.info(f"✅ Production mode completed in {prod_time:.2f}s")
        logger.info(f"   📊 Category: {category}, Confidence: {confidence:.3f}")
        logger.info(f"   🔍 Consultation events: {len(consultation_events)}")

        if consultation_events:
            logger.info(f"   ⚠️ Consultations required: {[e.consultation_type for e in consultation_events]}")
        else:
            logger.info("   ✅ No consultation required (high confidence)")

    except Exception as e:
        logger.error(f"❌ Production mode failed: {e}")
        results["production"] = {"error": str(e)}

    # Test 2: Validation mode (should bypass consultation)
    logger.info("\n🔄 Test 2: Validation Mode (validation_mode=True)")
    start_time = time.time()

    try:
        result_val = await run_unified_test_generation_workflow(
            document_path=str(test_doc_path),
            validation_mode=True,  # Validation mode
            enable_categorization=True,
            enable_planning=False,  # Skip planning to focus on categorization
            enable_parallel_coordination=False,
            enable_document_processing=False,
            verbose=True
        )

        results["validation"] = result_val
        val_time = time.time() - start_time

        # Analyze results
        categorization = result_val.get("categorization", {})
        category = categorization.get("gamp_category", {}).get("value", 0)
        confidence = categorization.get("confidence_score", 0.0)

        workflow_events = result_val.get("workflow_events", [])
        bypass_events = [e for e in workflow_events if isinstance(e, ConsultationBypassedEvent)]
        consultation_events = [e for e in workflow_events if isinstance(e, ConsultationRequiredEvent)]

        logger.info(f"✅ Validation mode completed in {val_time:.2f}s")
        logger.info(f"   📊 Category: {category}, Confidence: {confidence:.3f}")
        logger.info(f"   🔄 Bypass events: {len(bypass_events)}")
        logger.info(f"   🔍 Consultation events: {len(consultation_events)}")

        if bypass_events:
            for event in bypass_events:
                logger.info(f"   ✅ Bypassed: {event.original_consultation.consultation_type} (reason: {event.bypass_reason})")

    except Exception as e:
        logger.error(f"❌ Validation mode failed: {e}")
        results["validation"] = {"error": str(e)}

    # Analysis
    logger.info("\n" + "="*80)
    logger.info("📊 VALIDATION MODE TEST ANALYSIS")
    logger.info("="*80)

    success_criteria = []

    # Check if both modes completed
    prod_success = results["production"] and "error" not in results["production"]
    val_success = results["validation"] and "error" not in results["validation"]

    success_criteria.append(("Both modes completed", prod_success and val_success))

    if prod_success and val_success:
        # Compare workflow behavior
        prod_events = results["production"].get("workflow_events", [])
        val_events = results["validation"].get("workflow_events", [])

        prod_consultations = len([e for e in prod_events if isinstance(e, ConsultationRequiredEvent)])
        val_consultations = len([e for e in val_events if isinstance(e, ConsultationRequiredEvent)])
        val_bypasses = len([e for e in val_events if isinstance(e, ConsultationBypassedEvent)])

        # For Category 5 documents with low confidence, production should require consultation
        # but validation mode should bypass it
        expected_behavior = False

        # Get categorization results
        prod_cat = results["production"].get("categorization", {})
        val_cat = results["validation"].get("categorization", {})

        prod_category = prod_cat.get("gamp_category", {}).get("value", 0)
        val_category = val_cat.get("gamp_category", {}).get("value", 0)

        prod_confidence = prod_cat.get("confidence_score", 1.0)
        val_confidence = val_cat.get("confidence_score", 1.0)

        # Categories should be the same
        success_criteria.append(("Same categorization results", prod_category == val_category))

        # Check if Category 5 behavior is different between modes
        if prod_category == 5 or val_category == 5:
            # Category 5 with low confidence should behave differently
            config = get_config()
            threshold = config.validation_mode.bypass_consultation_threshold

            if prod_confidence < threshold or val_confidence < threshold:
                expected_behavior = True
                success_criteria.append(("Production mode required consultation", prod_consultations > 0))
                success_criteria.append(("Validation mode bypassed consultation", val_bypasses > 0))
                success_criteria.append(("Validation mode has fewer consultations", val_consultations < prod_consultations))
            else:
                # High confidence - should not require consultation in either mode
                success_criteria.append(("High confidence - no consultations needed", prod_consultations == 0 and val_consultations == 0))
        else:
            # Non-Category 5 should behave similarly
            success_criteria.append(("Non-Category 5 behavior similar", abs(prod_consultations - val_consultations) <= 1))

        # Audit trail validation
        if val_bypasses > 0:
            bypass_events = [e for e in val_events if isinstance(e, ConsultationBypassedEvent)]
            audit_preserved = all(hasattr(e, "audit_trail_preserved") and e.audit_trail_preserved for e in bypass_events)
            success_criteria.append(("Audit trail preserved for bypasses", audit_preserved))

    # Display results
    logger.info(f"📋 Production Mode: {'✅ Success' if prod_success else '❌ Failed'}")
    if prod_success:
        prod_cat = results["production"].get("categorization", {})
        logger.info(f"   Category: {prod_cat.get('gamp_category', {}).get('value', 'N/A')}")
        logger.info(f"   Confidence: {prod_cat.get('confidence_score', 'N/A')}")
        logger.info(f"   Consultations: {len([e for e in results['production'].get('workflow_events', []) if isinstance(e, ConsultationRequiredEvent)])}")

    logger.info(f"📋 Validation Mode: {'✅ Success' if val_success else '❌ Failed'}")
    if val_success:
        val_cat = results["validation"].get("categorization", {})
        logger.info(f"   Category: {val_cat.get('gamp_category', {}).get('value', 'N/A')}")
        logger.info(f"   Confidence: {val_cat.get('confidence_score', 'N/A')}")
        logger.info(f"   Consultations: {len([e for e in results['validation'].get('workflow_events', []) if isinstance(e, ConsultationRequiredEvent)])}")
        logger.info(f"   Bypasses: {len([e for e in results['validation'].get('workflow_events', []) if isinstance(e, ConsultationBypassedEvent)])}")

    logger.info("\n🎯 Success Criteria:")
    all_passed = True
    for criterion, passed in success_criteria:
        status = "✅" if passed else "❌"
        logger.info(f"   {status} {criterion}")
        if not passed:
            all_passed = False

    logger.info(f"\n🏆 Overall Result: {'✅ VALIDATION MODE WORKING CORRECTLY' if all_passed else '❌ VALIDATION MODE NEEDS FIXES'}")

    return all_passed


if __name__ == "__main__":
    # Temporarily use OpenAI for testing
    os.environ["LLM_PROVIDER"] = "openai"
    os.environ["VALIDATION_MODE"] = "false"  # Start with production default
    os.environ["VALIDATION_MODE_EXPLICIT"] = "true"  # Suppress warnings

    # Force reload the LLM config with OpenAI provider
    llm_config_module.LLMConfig.PROVIDER = ModelProvider.OPENAI

    success = asyncio.run(test_validation_mode_with_real_workflow())

    if success:
        logger.info("🎉 Task 21 validation mode implementation verified!")
        sys.exit(0)
    else:
        logger.error("❌ Task 21 validation mode implementation needs fixes")
        sys.exit(1)
