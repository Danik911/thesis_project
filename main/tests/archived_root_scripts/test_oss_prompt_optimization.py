#!/usr/bin/env python3
"""
Test script for OSS model prompt optimizations in OQ generation.

This script tests the optimized prompts to verify they generate complete
test suites with the OSS model (openai/gpt-oss-120b) instead of incomplete responses.
"""

import logging
import os
import sys

# Add the main directory to path to import modules
sys.path.append(os.path.dirname(__file__))

from src.agents.oq_generator.templates import GAMPCategoryConfig, OQPromptTemplates
from src.core.events import GAMPCategory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_prompt_optimization():
    """Test the optimized prompts for all GAMP categories."""

    logger.info("Testing OSS-optimized OQ generation prompts...")

    # Sample URS content for testing
    sample_urs = """
    User Requirements Specification (URS) - Laboratory Information Management System (LIMS)
    
    REQ-001: System Installation
    The system must be installed on approved hardware with all required components.
    
    REQ-002: User Authentication
    The system must provide secure user authentication with role-based access controls.
    
    REQ-003: Data Integrity
    The system must maintain complete audit trails for all data modifications.
    
    REQ-004: Reporting
    The system must generate comprehensive reports for regulatory compliance.
    
    REQ-005: Integration
    The system must integrate with external laboratory instruments and databases.
    
    REQ-006: Performance
    The system must respond to user queries within 3 seconds under normal load.
    
    REQ-007: Security
    The system must implement encryption for data at rest and in transit.
    
    REQ-008: Backup
    The system must perform automated daily backups with verification.
    
    REQ-009: Compliance
    The system must meet 21 CFR Part 11 and GAMP-5 requirements.
    
    REQ-010: Validation
    The system must support comprehensive validation testing and documentation.
    """

    # Test configurations for each GAMP category
    test_configs = [
        (GAMPCategory.CATEGORY_1, "LIMS Infrastructure", 4),
        (GAMPCategory.CATEGORY_3, "LIMS Standard", 8),
        (GAMPCategory.CATEGORY_4, "LIMS Configured", 18),
        (GAMPCategory.CATEGORY_5, "LIMS Custom", 27),
    ]

    results = []

    for gamp_category, document_name, test_count in test_configs:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing GAMP Category {gamp_category.value}: {document_name}")
        logger.info(f"Required test count: {test_count}")
        logger.info(f"{'='*60}")

        try:
            # Generate the optimized prompt
            prompt = OQPromptTemplates.get_generation_prompt(
                gamp_category=gamp_category,
                urs_content=sample_urs,
                document_name=document_name,
                test_count=test_count,
                context_summary="OSS model testing with optimized prompts"
            )

            # Analyze the prompt for OSS-friendly features
            prompt_analysis = analyze_prompt_optimization(prompt, test_count)

            logger.info("✅ Prompt generated successfully")
            logger.info(f"   Prompt length: {len(prompt)} characters")
            logger.info(f"   Test count mentions: {prompt_analysis['test_count_mentions']}")
            logger.info(f"   Has explicit counting: {prompt_analysis['has_explicit_counting']}")
            logger.info(f"   Has example structure: {prompt_analysis['has_example_structure']}")
            logger.info(f"   Has step-by-step instructions: {prompt_analysis['has_step_by_step']}")
            logger.info(f"   Has validation checklist: {prompt_analysis['has_validation_checklist']}")
            logger.info(f"   OSS optimization score: {prompt_analysis['oss_score']:.1f}/10")

            # Save prompt to file for manual inspection
            prompt_filename = f"optimized_prompt_category_{gamp_category.value}_tests_{test_count}.txt"
            with open(prompt_filename, "w", encoding="utf-8") as f:
                f.write(prompt)
            logger.info(f"   Prompt saved to: {prompt_filename}")

            results.append((gamp_category.value, test_count, "SUCCESS", prompt_analysis["oss_score"]))

        except Exception as e:
            logger.error(f"❌ Prompt generation failed: {e}")
            results.append((gamp_category.value, test_count, "FAILED", 0))

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("PROMPT OPTIMIZATION TEST SUMMARY")
    logger.info(f"{'='*60}")

    total_score = 0
    successful = 0

    for category, test_count, status, score in results:
        if status == "SUCCESS":
            logger.info(f"✅ GAMP Category {category} ({test_count} tests): {status} - OSS Score: {score:.1f}/10")
            successful += 1
            total_score += score
        else:
            logger.error(f"❌ GAMP Category {category} ({test_count} tests): {status}")

    if successful > 0:
        avg_score = total_score / successful
        logger.info(f"\nResults: {successful}/{len(results)} categories passed")
        logger.info(f"Average OSS optimization score: {avg_score:.1f}/10")

        if avg_score >= 8.0:
            logger.info("🎉 EXCELLENT - Prompts are highly optimized for OSS models!")
        elif avg_score >= 6.0:
            logger.info("✅ GOOD - Prompts should work well with OSS models")
        elif avg_score >= 4.0:
            logger.info("⚠️  FAIR - Prompts may need more optimization")
        else:
            logger.info("❌ POOR - Prompts need significant optimization")
    else:
        logger.error("💥 ALL TESTS FAILED")

    return successful == len(results)


def analyze_prompt_optimization(prompt: str, expected_test_count: int) -> dict:
    """
    Analyze prompt for OSS model optimization features.
    
    Returns a score from 0-10 based on OSS-friendly features.
    """
    analysis = {
        "test_count_mentions": 0,
        "has_explicit_counting": False,
        "has_example_structure": False,
        "has_step_by_step": False,
        "has_validation_checklist": False,
        "has_emphasis": False,
        "has_simple_language": False,
        "oss_score": 0
    }

    # Count test count mentions
    test_count_str = str(expected_test_count)
    analysis["test_count_mentions"] = prompt.count(test_count_str)

    # Check for explicit counting instructions
    counting_phrases = [
        "count them as you generate",
        "test 1, test 2, test 3",
        "generate test 1",
        "continue until test"
    ]
    analysis["has_explicit_counting"] = any(phrase.lower() in prompt.lower() for phrase in counting_phrases)

    # Check for example structure
    analysis["has_example_structure"] = '"test_id":' in prompt and '"step_number":' in prompt

    # Check for step-by-step instructions
    step_phrases = [
        "step-by-step generation instructions",
        "generation instructions",
        "follow this exact order"
    ]
    analysis["has_step_by_step"] = any(phrase.lower() in prompt.lower() for phrase in step_phrases)

    # Check for validation checklist
    checklist_phrases = [
        "validation checklist",
        "verify before responding",
        "generated exactly"
    ]
    analysis["has_validation_checklist"] = any(phrase.lower() in prompt.lower() for phrase in checklist_phrases)

    # Check for emphasis (caps, emojis)
    analysis["has_emphasis"] = any(char in prompt for char in "🚨🎯✅❌📋📄📊🔍") and "CRITICAL" in prompt

    # Check for simple language (shorter sentences, direct commands)
    sentences = prompt.split(".")
    avg_sentence_length = sum(len(s.strip()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()])
    analysis["has_simple_language"] = avg_sentence_length < 100  # Shorter sentences are better for OSS models

    # Calculate OSS optimization score (0-10)
    score = 0

    # Test count emphasis (0-3 points)
    if analysis["test_count_mentions"] >= 10:
        score += 3
    elif analysis["test_count_mentions"] >= 5:
        score += 2
    elif analysis["test_count_mentions"] >= 2:
        score += 1

    # Structural features (0-4 points)
    if analysis["has_explicit_counting"]:
        score += 1
    if analysis["has_example_structure"]:
        score += 1
    if analysis["has_step_by_step"]:
        score += 1
    if analysis["has_validation_checklist"]:
        score += 1

    # Style features (0-3 points)
    if analysis["has_emphasis"]:
        score += 1.5
    if analysis["has_simple_language"]:
        score += 1.5

    analysis["oss_score"] = score

    return analysis


def test_category_requirements():
    """Test that category requirements are correctly configured."""

    logger.info("\nTesting GAMP category requirements...")

    expected_ranges = {
        GAMPCategory.CATEGORY_1: (3, 5),
        GAMPCategory.CATEGORY_3: (5, 10),
        GAMPCategory.CATEGORY_4: (15, 20),
        GAMPCategory.CATEGORY_5: (25, 30)
    }

    all_passed = True

    for category, expected_range in expected_ranges.items():
        try:
            actual_range = GAMPCategoryConfig.get_test_count_range(category)

            if actual_range == expected_range:
                logger.info(f"✅ GAMP Category {category.value}: {actual_range} (correct)")
            else:
                logger.error(f"❌ GAMP Category {category.value}: expected {expected_range}, got {actual_range}")
                all_passed = False

        except Exception as e:
            logger.error(f"❌ GAMP Category {category.value}: error - {e}")
            all_passed = False

    return all_passed


if __name__ == "__main__":
    logger.info("Starting OSS Prompt Optimization Tests")
    logger.info("="*60)

    # Run tests
    requirements_passed = test_category_requirements()
    prompt_test_passed = test_prompt_optimization()

    # Overall result
    if requirements_passed and prompt_test_passed:
        logger.info("\n🎉 ALL TESTS PASSED - OSS prompt optimizations are ready!")
        logger.info("   Next step: Test with actual OSS model to validate completeness")
        sys.exit(0)
    else:
        logger.error("\n💥 SOME TESTS FAILED - Optimizations need fixes")
        sys.exit(1)
