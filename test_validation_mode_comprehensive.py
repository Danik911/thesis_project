#!/usr/bin/env python3
"""
Comprehensive Validation Mode Cross-Validation Testing - Task 21

This script performs comprehensive testing of the validation mode implementation
with real API calls using the DeepSeek open-source model. It tests:
1. Category 5 document success rate improvement
2. Audit trail preservation
3. Performance impact
4. Edge cases and error handling
5. Compliance requirements

CRITICAL: Uses REAL API calls with DeepSeek model - NO MOCKED DATA
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Any
from uuid import uuid4

# Add the main source directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "main" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "main"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from src.config.llm_config import LLMConfig, ModelProvider
from src.core.unified_workflow import UnifiedTestGenerationWorkflow, run_unified_test_generation_workflow
from src.shared.config import get_config, Config
from src.core.events import GAMPCategorizationEvent, GAMPCategory, ConsultationBypassedEvent, ConsultationRequiredEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/validation_mode_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

class ValidationModeTestResults:
    """Container for test results with comprehensive metrics."""
    
    def __init__(self):
        self.test_start_time = datetime.now(UTC)
        self.production_mode_results: List[Dict[str, Any]] = []
        self.validation_mode_results: List[Dict[str, Any]] = []
        self.bypass_events: List[ConsultationBypassedEvent] = []
        self.api_calls_count = 0
        self.total_cost_estimate = 0.0
        self.performance_metrics: Dict[str, Any] = {}
        self.compliance_metrics: Dict[str, Any] = {}
        self.error_log: List[Dict[str, Any]] = []
        
    def add_production_result(self, document_id: str, category: int, confidence: float, 
                            required_consultation: bool, time_taken: float, error: str = None):
        """Add production mode test result."""
        result = {
            "document_id": document_id,
            "category": category,
            "confidence": confidence,
            "required_consultation": required_consultation,
            "time_taken": time_taken,
            "error": error,
            "timestamp": datetime.now(UTC).isoformat()
        }
        self.production_mode_results.append(result)
        
    def add_validation_result(self, document_id: str, category: int, confidence: float,
                            bypassed: bool, time_taken: float, error: str = None):
        """Add validation mode test result."""
        result = {
            "document_id": document_id,
            "category": category,
            "confidence": confidence,
            "bypassed": bypassed,
            "time_taken": time_taken,
            "error": error,
            "timestamp": datetime.now(UTC).isoformat()
        }
        self.validation_mode_results.append(result)
        
    def add_bypass_event(self, event: ConsultationBypassedEvent):
        """Add bypass event for audit trail validation."""
        self.bypass_events.append(event)
        
    def calculate_success_rates(self) -> Dict[str, float]:
        """Calculate success rates for both modes."""
        production_successful = len([r for r in self.production_mode_results if not r["error"]])
        validation_successful = len([r for r in self.validation_mode_results if not r["error"]])
        
        production_rate = (production_successful / len(self.production_mode_results) 
                         if self.production_mode_results else 0.0)
        validation_rate = (validation_successful / len(self.validation_mode_results)
                         if self.validation_mode_results else 0.0)
        
        return {
            "production_success_rate": production_rate,
            "validation_success_rate": validation_rate,
            "improvement": validation_rate - production_rate,
            "production_successful": production_successful,
            "validation_successful": validation_successful,
            "total_production_tests": len(self.production_mode_results),
            "total_validation_tests": len(self.validation_mode_results)
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        success_rates = self.calculate_success_rates()
        test_duration = (datetime.now(UTC) - self.test_start_time).total_seconds()
        
        return {
            "test_summary": {
                "start_time": self.test_start_time.isoformat(),
                "end_time": datetime.now(UTC).isoformat(),
                "duration_seconds": test_duration,
                "model_used": f"{LLMConfig.PROVIDER.value}/{LLMConfig.MODELS[LLMConfig.PROVIDER]['model']}",
                "api_calls_count": self.api_calls_count,
                "estimated_cost": self.total_cost_estimate
            },
            "success_rates": success_rates,
            "performance_metrics": self.performance_metrics,
            "compliance_validation": {
                "bypass_events_captured": len(self.bypass_events),
                "audit_trail_preserved": all(hasattr(e, 'audit_trail_preserved') and e.audit_trail_preserved 
                                           for e in self.bypass_events),
                "consultation_types_logged": list(set(e.original_consultation.consultation_type 
                                                    for e in self.bypass_events if e.original_consultation))
            },
            "detailed_results": {
                "production_mode": self.production_mode_results,
                "validation_mode": self.validation_mode_results
            },
            "errors": self.error_log,
            "recommendations": self._generate_recommendations(success_rates)
        }
    
    def _generate_recommendations(self, success_rates: Dict[str, float]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if success_rates["improvement"] > 0.5:  # 50%+ improvement
            recommendations.append("✅ Validation mode significantly improves Category 5 success rate")
        elif success_rates["improvement"] > 0.2:  # 20%+ improvement
            recommendations.append("✅ Validation mode provides moderate improvement for Category 5 documents")
        else:
            recommendations.append("⚠️ Validation mode improvement is minimal - investigate further")
            
        if success_rates["validation_success_rate"] > 0.9:
            recommendations.append("✅ Validation mode achieves >90% success rate target")
        else:
            recommendations.append("❌ Validation mode does not meet 90% success rate target")
            
        if len(self.bypass_events) == len([r for r in self.validation_mode_results if r.get("bypassed", False)]):
            recommendations.append("✅ All bypassed consultations properly logged for audit trail")
        else:
            recommendations.append("❌ Some bypassed consultations not properly logged")
            
        return recommendations


async def test_model_configuration():
    """Test that DeepSeek model is properly configured and accessible."""
    logger.info("🔧 Testing DeepSeek Model Configuration")
    
    # Verify environment configuration
    assert LLMConfig.PROVIDER == ModelProvider.OPENROUTER, f"Expected OpenRouter, got {LLMConfig.PROVIDER}"
    assert LLMConfig.MODELS[LLMConfig.PROVIDER]["model"] == "deepseek/deepseek-chat", \
        f"Expected deepseek/deepseek-chat, got {LLMConfig.MODELS[LLMConfig.PROVIDER]['model']}"
    
    # Test API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    assert api_key, "OPENROUTER_API_KEY not found in environment"
    logger.info(f"✅ API Key present: {api_key[:10]}...")
    
    # Test LLM initialization
    try:
        llm = LLMConfig.get_llm()
        logger.info(f"✅ LLM initialized: {type(llm).__name__}")
        
        # Test simple API call
        response = await llm.acomplete("API_TEST_SUCCESS")
        assert "API_TEST_SUCCESS" in str(response), "API test failed"
        logger.info(f"✅ API connection successful: {str(response)[:100]}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Model configuration test failed: {e}")
        return False


async def test_category_5_workflow_real(document_path: str, validation_mode: bool, 
                                      results: ValidationModeTestResults) -> Dict[str, Any]:
    """Test Category 5 document workflow with real API calls."""
    start_time = time.time()
    doc_id = f"test_{uuid4().hex[:8]}"
    
    logger.info(f"📄 Testing document workflow - Validation Mode: {validation_mode}")
    
    try:
        # Run the unified workflow with real API calls
        result = await run_unified_test_generation_workflow(
            document_path=document_path,
            validation_mode=validation_mode,
            enable_categorization=True,
            enable_planning=True,
            enable_parallel_coordination=True,
            enable_document_processing=True,
            verbose=True
        )
        
        time_taken = time.time() - start_time
        results.api_calls_count += 1  # Increment API call counter
        
        # Extract results
        categorization_result = result.get("categorization", {})
        category = categorization_result.get("gamp_category", {}).get("value", 0)
        confidence = categorization_result.get("confidence_score", 0.0)
        
        # Check for bypass events in workflow events
        workflow_events = result.get("workflow_events", [])
        bypass_events = [e for e in workflow_events if isinstance(e, ConsultationBypassedEvent)]
        consultation_events = [e for e in workflow_events if isinstance(e, ConsultationRequiredEvent)]
        
        if validation_mode:
            bypassed = len(bypass_events) > 0
            results.add_validation_result(doc_id, category, confidence, bypassed, time_taken)
            
            # Add bypass events for audit trail validation
            for event in bypass_events:
                results.add_bypass_event(event)
                
            logger.info(f"✅ Validation mode test completed - Bypassed: {bypassed}")
        else:
            required_consultation = len(consultation_events) > 0
            results.add_production_result(doc_id, category, confidence, required_consultation, time_taken)
            logger.info(f"✅ Production mode test completed - Consultation required: {required_consultation}")
        
        return result
        
    except Exception as e:
        time_taken = time.time() - start_time
        error_msg = f"Workflow failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        if validation_mode:
            results.add_validation_result(doc_id, 0, 0.0, False, time_taken, error_msg)
        else:
            results.add_production_result(doc_id, 0, 0.0, False, time_taken, error_msg)
        
        results.error_log.append({
            "document_id": doc_id,
            "validation_mode": validation_mode,
            "error": error_msg,
            "timestamp": datetime.now(UTC).isoformat()
        })
        
        return {"error": error_msg}


async def test_performance_impact(results: ValidationModeTestResults):
    """Test performance impact of validation mode."""
    logger.info("⚡ Testing Performance Impact")
    
    # Get average times for both modes
    prod_times = [r["time_taken"] for r in results.production_mode_results if not r["error"]]
    val_times = [r["time_taken"] for r in results.validation_mode_results if not r["error"]]
    
    if prod_times and val_times:
        avg_prod_time = sum(prod_times) / len(prod_times)
        avg_val_time = sum(val_times) / len(val_times)
        
        results.performance_metrics = {
            "average_production_time": avg_prod_time,
            "average_validation_time": avg_val_time,
            "time_improvement": avg_prod_time - avg_val_time,
            "speed_improvement_percentage": ((avg_prod_time - avg_val_time) / avg_prod_time) * 100
        }
        
        logger.info(f"📊 Performance Results:")
        logger.info(f"   Production mode average: {avg_prod_time:.2f}s")
        logger.info(f"   Validation mode average: {avg_val_time:.2f}s") 
        logger.info(f"   Speed improvement: {results.performance_metrics['speed_improvement_percentage']:.1f}%")
    else:
        logger.warning("⚠️ Insufficient data for performance comparison")


async def test_edge_cases(results: ValidationModeTestResults):
    """Test edge cases and error handling."""
    logger.info("🔬 Testing Edge Cases")
    
    # Test 1: Invalid confidence scores
    try:
        config = get_config()
        config.validation_mode.bypass_consultation_threshold = 1.5  # Invalid threshold
        logger.error("❌ Should have failed with invalid threshold")
    except ValueError as e:
        logger.info(f"✅ Correctly rejected invalid threshold: {e}")
        
    # Test 2: Invalid GAMP categories
    try:
        config.validation_mode.bypass_allowed_categories = [99]  # Invalid category
        logger.error("❌ Should have failed with invalid category")
    except ValueError as e:
        logger.info(f"✅ Correctly rejected invalid category: {e}")
    
    # Reset config to valid state
    config = get_config()


async def run_comprehensive_validation_test():
    """Run comprehensive validation mode testing with real API calls."""
    logger.info("🚀 Starting Comprehensive Validation Mode Testing")
    logger.info("=" * 80)
    logger.info("CRITICAL: This test uses REAL API calls with DeepSeek model")
    logger.info("NO MOCK DATA - Testing actual implementation behavior")
    logger.info("=" * 80)
    
    results = ValidationModeTestResults()
    
    # Step 1: Test model configuration
    logger.info("Phase 1: Model Configuration Testing")
    if not await test_model_configuration():
        logger.error("❌ Model configuration test failed - aborting")
        return False
    
    # Step 2: Find a Category 5 document for testing
    urs_manifest_path = Path(__file__).parent / "datasets" / "urs_corpus" / "urs_manifest.json"
    limited_manifest_path = Path(__file__).parent / "datasets" / "urs_corpus" / "limited_manifest.json"
    
    # Use limited manifest if available, otherwise full manifest
    manifest_path = limited_manifest_path if limited_manifest_path.exists() else urs_manifest_path
    
    if not manifest_path.exists():
        logger.error(f"❌ URS manifest not found at {manifest_path}")
        return False
        
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Find Category 5 documents
    category_5_docs = [doc for doc in manifest["documents"] 
                      if doc.get("expected_category") == 5]
    
    if not category_5_docs:
        logger.warning("⚠️ No Category 5 documents found, using first available document")
        test_doc = manifest["documents"][0]
    else:
        test_doc = category_5_docs[0]
        
    test_doc_path = Path(__file__).parent / "datasets" / "urs_corpus" / test_doc["filename"]
    
    logger.info(f"📄 Using test document: {test_doc['filename']}")
    logger.info(f"📋 Expected category: {test_doc.get('expected_category', 'Unknown')}")
    
    # Step 3: Test production mode (should require consultation for Category 5)
    logger.info("\nPhase 2: Production Mode Testing")
    await test_category_5_workflow_real(str(test_doc_path), validation_mode=False, results=results)
    
    # Step 4: Test validation mode (should bypass consultation)
    logger.info("\nPhase 3: Validation Mode Testing")
    await test_category_5_workflow_real(str(test_doc_path), validation_mode=True, results=results)
    
    # Step 5: Performance analysis
    logger.info("\nPhase 4: Performance Analysis")
    await test_performance_impact(results)
    
    # Step 6: Edge case testing
    logger.info("\nPhase 5: Edge Case Testing")
    await test_edge_cases(results)
    
    # Step 7: Generate comprehensive report
    logger.info("\nPhase 6: Report Generation")
    report = results.generate_report()
    
    # Save report to file
    report_path = Path(__file__).parent / "main" / "docs" / "TASK_21_VALIDATION_MODE_TEST_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, "w") as f:
        f.write("# Task 21 Validation Mode Comprehensive Test Report\n\n")
        f.write(f"**Generated:** {datetime.now(UTC).isoformat()}\n")
        f.write(f"**Model:** {report['test_summary']['model_used']}\n")
        f.write(f"**Test Duration:** {report['test_summary']['duration_seconds']:.2f} seconds\n\n")
        
        f.write("## Executive Summary\n\n")
        success_rates = report['success_rates']
        f.write(f"- **Production Mode Success Rate:** {success_rates['production_success_rate']:.1%}\n")
        f.write(f"- **Validation Mode Success Rate:** {success_rates['validation_success_rate']:.1%}\n")
        f.write(f"- **Success Rate Improvement:** {success_rates['improvement']:.1%}\n")
        f.write(f"- **API Calls Made:** {report['test_summary']['api_calls_count']}\n")
        f.write(f"- **Bypass Events Captured:** {report['compliance_validation']['bypass_events_captured']}\n\n")
        
        f.write("## Recommendations\n\n")
        for rec in report['recommendations']:
            f.write(f"- {rec}\n")
        
        f.write("\n## Detailed Test Results\n\n")
        f.write("```json\n")
        f.write(json.dumps(report, indent=2, default=str))
        f.write("\n```\n")
    
    # Display results
    logger.info("=" * 80)
    logger.info("📊 COMPREHENSIVE VALIDATION MODE TEST RESULTS")
    logger.info("=" * 80)
    
    success_rates = report['success_rates']
    logger.info(f"✅ Production Mode Success Rate: {success_rates['production_success_rate']:.1%} ({success_rates['production_successful']}/{success_rates['total_production_tests']})")
    logger.info(f"✅ Validation Mode Success Rate: {success_rates['validation_success_rate']:.1%} ({success_rates['validation_successful']}/{success_rates['total_validation_tests']})")
    logger.info(f"📈 Success Rate Improvement: {success_rates['improvement']:.1%}")
    
    # Check success criteria
    meets_target = success_rates['validation_success_rate'] >= 0.9
    has_improvement = success_rates['improvement'] > 0
    audit_compliant = report['compliance_validation']['audit_trail_preserved']
    
    logger.info(f"🎯 Meets 90% Success Target: {'✅' if meets_target else '❌'}")
    logger.info(f"📈 Shows Improvement: {'✅' if has_improvement else '❌'}")
    logger.info(f"📋 Audit Trail Preserved: {'✅' if audit_compliant else '❌'}")
    
    overall_success = meets_target and has_improvement and audit_compliant
    logger.info(f"🏆 Overall Test Success: {'✅ PASS' if overall_success else '❌ FAIL'}")
    
    logger.info("=" * 80)
    logger.info("📑 Recommendations:")
    for rec in report['recommendations']:
        logger.info(f"   {rec}")
    
    logger.info(f"\n📄 Detailed report saved to: {report_path}")
    
    return overall_success


if __name__ == "__main__":
    # Set environment for validation mode testing
    os.environ["VALIDATION_MODE"] = "false"  # Start with production default
    os.environ["VALIDATION_MODE_EXPLICIT"] = "true"  # Suppress warnings
    os.environ["LLM_PROVIDER"] = "openrouter"  # Ensure DeepSeek model
    
    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    
    # Run comprehensive test
    success = asyncio.run(run_comprehensive_validation_test())
    
    if success:
        logger.info("🎉 All validation mode tests passed!")
        sys.exit(0)
    else:
        logger.error("❌ Some validation mode tests failed - review report for details")
        sys.exit(1)