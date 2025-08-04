#!/usr/bin/env python3
"""
Test Phoenix observability infrastructure only
Tests if Phoenix setup, instrumentation, and basic trace collection works
"""

import asyncio
import sys
from pathlib import Path
import time

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.monitoring.phoenix_config import setup_phoenix, shutdown_phoenix, get_phoenix_manager

def test_phoenix_basic_infrastructure():
    """Test basic Phoenix infrastructure without LLM calls"""
    
    print("Testing Phoenix infrastructure setup...")
    
    # Test Phoenix setup
    phoenix_manager = setup_phoenix()
    
    if not phoenix_manager:
        print("FAILED: Phoenix manager not created")
        return False
    
    print(f"SUCCESS: Phoenix manager created - initialized: {phoenix_manager._initialized}")
    
    # Test tracer creation
    try:
        tracer = phoenix_manager.get_tracer("test_tracer")
        if tracer:
            print("SUCCESS: Tracer created successfully")
        else:
            print("FAILED: Tracer not created")
            return False
    except Exception as e:
        print(f"FAILED: Tracer creation error: {e}")
        return False
    
    # Test basic span creation (without LLM calls)
    try:
        with tracer.start_as_current_span("test_span") as span:
            span.set_attribute("test.operation", "phoenix_infrastructure_test")
            span.set_attribute("test.type", "basic_trace")
            span.set_attribute("compliance.gamp5.test", True)
            
            # Simulate some work
            time.sleep(0.1)
            
            span.set_attribute("test.status", "success")
            print("SUCCESS: Basic span created and attributes set")
    except Exception as e:
        print(f"FAILED: Span creation error: {e}")
        return False
    
    return True

def test_phoenix_enhanced_features():
    """Test enhanced Phoenix features"""
    
    print("Testing Phoenix enhanced features...")
    
    phoenix_manager = get_phoenix_manager()
    if not phoenix_manager:
        print("FAILED: No Phoenix manager available")
        return False
    
    # Test enhanced compliance attributes
    try:
        tracer = phoenix_manager.get_tracer("pharmaceutical_test")
        with tracer.start_as_current_span("pharmaceutical_workflow") as span:
            # Test the enhanced workflow span functionality
            from src.monitoring.phoenix_config import enhance_workflow_span_with_compliance
            
            enhance_workflow_span_with_compliance(
                span,
                workflow_type="categorization_test",
                test_document="phoenix_test.urs",
                test_category="observability_validation"
            )
            
            span.set_attribute("test.enhanced.features", "success")
            print("SUCCESS: Enhanced compliance attributes applied")
            
    except Exception as e:
        print(f"FAILED: Enhanced features error: {e}")
        return False
    
    return True

def test_phoenix_instrumentation_status():
    """Test Phoenix instrumentation components"""
    
    print("Testing Phoenix instrumentation status...")
    
    phoenix_manager = get_phoenix_manager()
    if not phoenix_manager:
        print("FAILED: No Phoenix manager available")
        return False
    
    config = phoenix_manager.config
    print(f"  - Tracing enabled: {config.enable_tracing}")
    print(f"  - OpenAI instrumentation: {config.enable_openai_instrumentation}")
    print(f"  - ChromaDB instrumentation: {config.enable_chromadb_instrumentation}")
    print(f"  - Tool instrumentation: {config.enable_tool_instrumentation}")
    print(f"  - OTLP endpoint: {config.otlp_endpoint}")
    print(f"  - Service name: {config.service_name}")
    
    # Test if tracer provider is working
    if phoenix_manager.tracer_provider:
        print("SUCCESS: Tracer provider is active")
    else:
        print("FAILED: No tracer provider")
        return False
    
    return True

async def main():
    """Main test function"""
    print("Starting Phoenix observability infrastructure test")
    
    try:
        # Test 1: Basic infrastructure
        test1 = test_phoenix_basic_infrastructure()
        
        # Test 2: Enhanced features
        test2 = test_phoenix_enhanced_features()
        
        # Test 3: Instrumentation status
        test3 = test_phoenix_instrumentation_status()
        
        # Allow time for any spans to export
        print("Waiting for span export...")
        await asyncio.sleep(2)
        
        # Report results
        total_tests = 3
        passed_tests = sum([test1, test2, test3])
        
        print(f"\n=== PHOENIX OBSERVABILITY TEST RESULTS ===")
        print(f"Tests passed: {passed_tests}/{total_tests}")
        print(f"Basic infrastructure: {'PASS' if test1 else 'FAIL'}")
        print(f"Enhanced features: {'PASS' if test2 else 'FAIL'}")
        print(f"Instrumentation status: {'PASS' if test3 else 'FAIL'}")
        
        success = passed_tests == total_tests
        
        if success:
            print("Phoenix observability infrastructure is WORKING")
        else:
            print("Phoenix observability infrastructure has ISSUES")
        
        return success
        
    except Exception as e:
        print(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        print("Shutting down Phoenix...")
        shutdown_phoenix(timeout_seconds=3)
        print("Phoenix shutdown complete")

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)