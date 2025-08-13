#!/usr/bin/env python3
"""
Test script for ALCOA+ Compliance Enhancement (Task 23)

This script validates that the ALCOA+ compliance enhancements successfully
improve the Original and Accurate attribute scores from 0.40 to ≥0.80 each,
achieving an overall score of ≥9.0 from the current 8.11.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Add main/src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "main" / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_alcoa_enhancement():
    """Test the ALCOA+ enhancement implementation."""
    try:
        # Import required modules
        from compliance_validation.alcoa_scorer import ALCOAScorer
        from compliance_validation.evidence_collector import EvidenceCollector
        from compliance_validation.metadata_injector import get_metadata_injector
        from agents.oq_generator.models import OQTestSuite, OQTestCase, TestStep
        from core.events import GAMPCategory
        
        logger.info("Starting ALCOA+ enhancement validation test...")
        
        # Create test data (simulating generated OQ test suite)
        test_cases = [
            OQTestCase(
                test_id="OQ-001",
                test_name="System Installation Verification",
                test_category="installation",
                gamp_category=4,
                objective="Verify system installation meets requirements",
                test_steps=[
                    TestStep(
                        step_number=1,
                        action="Check system installation directory",
                        expected_result="Installation directory exists with correct permissions"
                    )
                ],
                acceptance_criteria=["Installation successful", "Directory permissions correct"]
            ),
            OQTestCase(
                test_id="OQ-002",
                test_name="Functional Testing",
                test_category="functional",
                gamp_category=4,
                objective="Test core functionality",
                test_steps=[
                    TestStep(
                        step_number=1,
                        action="Execute main function",
                        expected_result="Function executes without errors"
                    )
                ],
                acceptance_criteria=["Function executes", "No errors reported"]
            )
        ]
        
        # Create original test suite (without ALCOA+ metadata)
        original_suite = OQTestSuite(
            suite_id="OQ-SUITE-1234",
            gamp_category=4,
            document_name="Test URS Document",
            test_cases=test_cases,
            total_test_count=len(test_cases),
            estimated_execution_time=60
        )
        
        logger.info(f"Created original test suite: {original_suite.suite_id}")
        
        # Test original suite ALCOA+ score (should be low)
        evidence_collector = EvidenceCollector()
        alcoa_scorer = ALCOAScorer(evidence_collector)
        
        # Convert to dict for assessment
        original_data_samples = [original_suite.model_dump()]
        
        logger.info("Assessing original ALCOA+ score...")
        original_assessment = alcoa_scorer.assess_system_data_integrity(
            system_name="original_test_suite",
            data_samples=original_data_samples,
            target_score=9.0
        )
        
        logger.info(f"Original ALCOA+ Score: {original_assessment.overall_score:.2f}/10")
        logger.info(f"Original scores - Original: {original_assessment.attribute_scores.get('original', {}).score:.2f}, "
                   f"Accurate: {original_assessment.attribute_scores.get('accurate', {}).score:.2f}")
        
        # Apply ALCOA+ metadata enhancement
        logger.info("Applying ALCOA+ metadata enhancement...")
        metadata_injector = get_metadata_injector()
        
        # Convert to dict and enhance with metadata
        suite_dict = original_suite.model_dump()
        enhanced_dict = metadata_injector.inject_test_suite_metadata(
            test_suite_dict=suite_dict,
            llm_response={"confidence_score": 0.92},
            generation_context={
                "source_document_id": "Test_URS_Document",
                "gamp_category": 4,
                "pharmaceutical_validation": True,
                "generation_method": "LLMTextCompletionProgram"
            }
        )
        
        logger.info("Enhanced test suite with ALCOA+ metadata")
        
        # Test enhanced suite ALCOA+ score (should be high)
        enhanced_data_samples = [enhanced_dict]
        
        logger.info("Assessing enhanced ALCOA+ score...")
        enhanced_assessment = alcoa_scorer.assess_system_data_integrity(
            system_name="enhanced_test_suite",
            data_samples=enhanced_data_samples,
            target_score=9.0
        )
        
        logger.info(f"Enhanced ALCOA+ Score: {enhanced_assessment.overall_score:.2f}/10")
        logger.info(f"Enhanced scores - Original: {enhanced_assessment.attribute_scores.get('original', {}).score:.2f}, "
                   f"Accurate: {enhanced_assessment.attribute_scores.get('accurate', {}).score:.2f}")
        
        # Validate improvement
        score_improvement = enhanced_assessment.overall_score - original_assessment.overall_score
        original_original_score = original_assessment.attribute_scores.get('original', {}).score
        enhanced_original_score = enhanced_assessment.attribute_scores.get('original', {}).score
        original_accurate_score = original_assessment.attribute_scores.get('accurate', {}).score
        enhanced_accurate_score = enhanced_assessment.attribute_scores.get('accurate', {}).score
        
        logger.info("\n" + "="*60)
        logger.info("ALCOA+ ENHANCEMENT VALIDATION RESULTS")
        logger.info("="*60)
        logger.info(f"Overall Score Improvement: {original_assessment.overall_score:.2f} → {enhanced_assessment.overall_score:.2f} (+{score_improvement:.2f})")
        logger.info(f"Original Attribute: {original_original_score:.2f} → {enhanced_original_score:.2f} (+{enhanced_original_score - original_original_score:.2f})")
        logger.info(f"Accurate Attribute: {original_accurate_score:.2f} → {enhanced_accurate_score:.2f} (+{enhanced_accurate_score - original_accurate_score:.2f})")
        logger.info(f"Target Achievement: {'✓ SUCCESS' if enhanced_assessment.overall_score >= 9.0 else '✗ FAILED'} (≥9.0)")
        logger.info(f"Original Target: {'✓ SUCCESS' if enhanced_original_score >= 0.80 else '✗ FAILED'} (≥0.80)")
        logger.info(f"Accurate Target: {'✓ SUCCESS' if enhanced_accurate_score >= 0.80 else '✗ FAILED'} (≥0.80)")
        
        # Check specific metadata fields
        logger.info("\nMetadata Validation:")
        key_fields = [
            "is_original", "digital_signature", "validated", "confidence_score",
            "checksum", "hash", "accuracy_score", "reconciled", "cross_verified"
        ]
        
        for field in key_fields:
            value = enhanced_dict.get(field)
            status = "✓" if value is not None else "✗"
            logger.info(f"  {status} {field}: {value}")
        
        # Save results for documentation
        results = {
            "test_timestamp": datetime.now().isoformat(),
            "test_description": "ALCOA+ Compliance Enhancement Validation (Task 23)",
            "original_assessment": {
                "overall_score": original_assessment.overall_score,
                "original_score": original_original_score,
                "accurate_score": original_accurate_score,
                "meets_target": original_assessment.meets_target
            },
            "enhanced_assessment": {
                "overall_score": enhanced_assessment.overall_score,
                "original_score": enhanced_original_score,
                "accurate_score": enhanced_accurate_score,
                "meets_target": enhanced_assessment.meets_target
            },
            "improvements": {
                "overall_improvement": score_improvement,
                "original_improvement": enhanced_original_score - original_original_score,
                "accurate_improvement": enhanced_accurate_score - original_accurate_score
            },
            "target_achievement": {
                "overall_target_met": enhanced_assessment.overall_score >= 9.0,
                "original_target_met": enhanced_original_score >= 0.80,
                "accurate_target_met": enhanced_accurate_score >= 0.80,
                "all_targets_met": (
                    enhanced_assessment.overall_score >= 9.0 and
                    enhanced_original_score >= 0.80 and 
                    enhanced_accurate_score >= 0.80
                )
            },
            "metadata_fields_present": {field: enhanced_dict.get(field) is not None for field in key_fields}
        }
        
        # Save results file
        results_file = Path("ALCOA_ENHANCEMENT_VALIDATION_RESULTS.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\nValidation results saved to: {results_file}")
        
        # Final validation
        success = results["target_achievement"]["all_targets_met"]
        logger.info(f"\n{'='*60}")
        logger.info(f"TASK 23 VALIDATION: {'✓ COMPLETE SUCCESS' if success else '✗ NEEDS WORK'}")
        logger.info(f"{'='*60}")
        
        return success
        
    except Exception as e:
        logger.error(f"ALCOA+ enhancement test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_alcoa_enhancement())
    exit(0 if success else 1)