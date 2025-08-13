#!/usr/bin/env python3
"""
Test ALCOA+ Integration with OQ Workflow (Task 23)
"""

import sys
from pathlib import Path
sys.path.insert(0, 'src')
import asyncio
import logging
from agents.oq_generator.workflow import OQTestGenerationWorkflow
from agents.oq_generator.events import OQTestGenerationEvent
from core.events import GAMPCategory
from compliance_validation.alcoa_scorer import ALCOAScorer
from compliance_validation.evidence_collector import EvidenceCollector

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_workflow_integration():
    """Test ALCOA+ metadata injection in real OQ workflow."""
    try:
        logger.info("Testing ALCOA+ integration with OQ workflow...")
        
        # Create OQ generation event
        generation_event = OQTestGenerationEvent(
            gamp_category=GAMPCategory.CATEGORY_4,
            urs_content="Test URS content for system validation requirements.",
            aggregated_context={"research_findings": "Test context", "sme_insights": "Expert input"},
            document_metadata={"name": "Test_URS_Document.docx"},
            required_test_count=3
        )
        
        # Create OQ workflow with metadata injection enabled
        workflow = OQTestGenerationWorkflow(
            verbose=True,
            enable_validation=True,
            oq_generation_event=generation_event
        )
        
        logger.info("Starting OQ workflow with ALCOA+ metadata injection...")
        
        # Run workflow
        result = await workflow.run()
        
        # Check if test suite was generated
        if hasattr(result, 'test_suite') and result.test_suite:
            test_suite = result.test_suite
            logger.info(f"Generated test suite: {test_suite.suite_id}")
            
            # Convert to dict for ALCOA+ assessment
            test_suite_dict = test_suite.model_dump()
            
            # Check for ALCOA+ metadata presence
            alcoa_fields = [
                'is_original', 'digital_signature', 'validated', 'confidence_score',
                'checksum', 'hash', 'accuracy_score', 'reconciled', 'cross_verified'
            ]
            
            metadata_present = sum(1 for field in alcoa_fields if field in test_suite_dict and test_suite_dict[field] is not None)
            
            print()
            print("="*60)
            print("WORKFLOW INTEGRATION TEST RESULTS")
            print("="*60)
            print(f"Test Suite Generated: [{'OK' if test_suite else 'FAILED'}]")
            print(f"Suite ID: {test_suite.suite_id if test_suite else 'N/A'}")
            print(f"Test Cases Count: {len(test_suite.test_cases) if test_suite else 0}")
            print(f"ALCOA+ Metadata Coverage: {metadata_present}/{len(alcoa_fields)} fields ({100*metadata_present/len(alcoa_fields):.1f}%)")
            
            # Test ALCOA+ scoring on generated suite
            if test_suite:
                output_dir = Path('output/workflow_test')
                output_dir.mkdir(parents=True, exist_ok=True)
                
                evidence_collector = EvidenceCollector(output_directory=output_dir)
                alcoa_scorer = ALCOAScorer(evidence_collector)
                
                assessment = alcoa_scorer.assess_system_data_integrity(
                    system_name="generated_test_suite",
                    data_samples=[test_suite_dict],
                    target_score=9.0
                )
                
                print(f"ALCOA+ Score: {assessment.overall_score:.2f}/10")
                print(f"Target Met: {'[SUCCESS]' if assessment.meets_target else '[FAILED]'} (>=9.0)")
                
                success = assessment.overall_score >= 9.0 and metadata_present >= 7
                print()
                print("="*60)
                print(f"INTEGRATION TEST: {'[SUCCESS]' if success else '[NEEDS WORK]'}")
                print("="*60)
                
                return success
            else:
                print("[ERROR] No test suite generated")
                return False
        else:
            print("[ERROR] Workflow did not return test suite")
            return False
            
    except Exception as e:
        logger.error(f"Workflow integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_workflow_integration())
    print(f"\nIntegration Test Result: {'PASSED' if result else 'FAILED'}")