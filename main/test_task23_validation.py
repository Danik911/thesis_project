#!/usr/bin/env python3
"""
Task 23 ALCOA+ Enhancement Validation Test

This script validates that the ALCOA+ compliance enhancements successfully
improve the Original and Accurate attribute scores from 0.40 to ≥0.80 each,
achieving an overall score of ≥9.0 from the current 8.11.
"""

import sys
from pathlib import Path

sys.path.insert(0, "src")
import asyncio
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

async def test_alcoa_enhancement():
    """Test the ALCOA+ enhancement implementation."""
    try:
        from compliance_validation.alcoa_scorer import ALCOAScorer
        from compliance_validation.evidence_collector import EvidenceCollector
        from compliance_validation.metadata_injector import get_metadata_injector

        logger.info("Starting ALCOA+ enhancement validation test...")

        # Create output directory for evidence collector
        output_dir = Path("output/test_alcoa")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create minimal test data (simulating generated OQ test suite)
        test_data = {
            "suite_id": "OQ-SUITE-1234",
            "document_name": "Test URS Document",
            "test_cases": [
                {
                    "test_id": "OQ-001",
                    "test_name": "System Installation Verification",
                    "objective": "Verify system installation meets requirements"
                }
            ],
            "total_test_count": 1,
            "estimated_execution_time": 60
        }

        logger.info(f"Created original test data: {test_data['suite_id']}")

        # Test original data ALCOA+ score
        evidence_collector = EvidenceCollector(output_directory=output_dir)
        alcoa_scorer = ALCOAScorer(evidence_collector)

        original_data_samples = [test_data]

        logger.info("Assessing original ALCOA+ score...")
        original_assessment = alcoa_scorer.assess_system_data_integrity(
            system_name="original_test_suite",
            data_samples=original_data_samples,
            target_score=9.0
        )

        logger.info(f"Original ALCOA+ Score: {original_assessment.overall_score:.2f}/10")
        original_scores = original_assessment.attribute_scores
        original_original_score = original_scores.get("original", type("", (), {"score": 0.0})()).score
        original_accurate_score = original_scores.get("accurate", type("", (), {"score": 0.0})()).score
        logger.info(f"Original scores - Original: {original_original_score:.2f}, Accurate: {original_accurate_score:.2f}")

        # Apply ALCOA+ metadata enhancement
        logger.info("Applying ALCOA+ metadata enhancement...")
        metadata_injector = get_metadata_injector()

        enhanced_dict = metadata_injector.inject_test_suite_metadata(
            test_suite_dict=test_data,
            llm_response={"confidence_score": 0.92},
            generation_context={
                "source_document_id": "Test_URS_Document",
                "gamp_category": 4,
                "pharmaceutical_validation": True,
                "generation_method": "LLMTextCompletionProgram"
            }
        )

        logger.info("Enhanced test suite with ALCOA+ metadata")

        # Test enhanced suite ALCOA+ score
        enhanced_data_samples = [enhanced_dict]

        logger.info("Assessing enhanced ALCOA+ score...")
        enhanced_assessment = alcoa_scorer.assess_system_data_integrity(
            system_name="enhanced_test_suite",
            data_samples=enhanced_data_samples,
            target_score=9.0
        )

        logger.info(f"Enhanced ALCOA+ Score: {enhanced_assessment.overall_score:.2f}/10")
        enhanced_scores = enhanced_assessment.attribute_scores
        enhanced_original_score = enhanced_scores.get("original", type("", (), {"score": 0.0})()).score
        enhanced_accurate_score = enhanced_scores.get("accurate", type("", (), {"score": 0.0})()).score
        logger.info(f"Enhanced scores - Original: {enhanced_original_score:.2f}, Accurate: {enhanced_accurate_score:.2f}")

        # Validate improvement
        score_improvement = enhanced_assessment.overall_score - original_assessment.overall_score

        print()
        print("="*60)
        print("ALCOA+ ENHANCEMENT VALIDATION RESULTS")
        print("="*60)
        print(f"Overall Score Improvement: {original_assessment.overall_score:.2f} -> {enhanced_assessment.overall_score:.2f} (+{score_improvement:.2f})")
        print(f"Original Attribute: {original_original_score:.2f} -> {enhanced_original_score:.2f} (+{enhanced_original_score - original_original_score:.2f})")
        print(f"Accurate Attribute: {original_accurate_score:.2f} -> {enhanced_accurate_score:.2f} (+{enhanced_accurate_score - original_accurate_score:.2f})")
        print(f"Target Achievement: {'[SUCCESS]' if enhanced_assessment.overall_score >= 9.0 else '[FAILED]'} (>=9.0)")
        print(f"Original Target: {'[SUCCESS]' if enhanced_original_score >= 0.80 else '[FAILED]'} (>=0.80)")
        print(f"Accurate Target: {'[SUCCESS]' if enhanced_accurate_score >= 0.80 else '[FAILED]'} (>=0.80)")

        # Check specific metadata fields
        print()
        print("Metadata Validation:")
        key_fields = [
            "is_original", "digital_signature", "validated", "confidence_score",
            "checksum", "hash", "accuracy_score", "reconciled", "cross_verified"
        ]

        fields_present = 0
        for field in key_fields:
            value = enhanced_dict.get(field)
            status = "[OK]" if value is not None else "[MISSING]"
            if value is not None:
                fields_present += 1
            print(f"  {status} {field}: {value}")

        print(f"\nMetadata Coverage: {fields_present}/{len(key_fields)} fields present ({100*fields_present/len(key_fields):.1f}%)")

        # Final validation
        success = (
            enhanced_assessment.overall_score >= 9.0 and
            enhanced_original_score >= 0.80 and
            enhanced_accurate_score >= 0.80
        )

        print()
        print("="*60)
        print(f"TASK 23 VALIDATION: {'[COMPLETE SUCCESS]' if success else '[NEEDS WORK]'}")
        print("="*60)

        # Save detailed results
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
                "all_targets_met": success
            },
            "metadata_coverage": {
                "fields_present": fields_present,
                "total_fields": len(key_fields),
                "coverage_percentage": 100 * fields_present / len(key_fields)
            }
        }

        # Save results
        results_file = Path("../TASK23_ALCOA_VALIDATION_RESULTS.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\nDetailed results saved to: {results_file}")

        return success

    except Exception as e:
        logger.error(f"ALCOA+ enhancement test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_alcoa_enhancement())
    print(f"\nTest Result: {'PASSED' if result else 'FAILED'}")
    sys.exit(0 if result else 1)
