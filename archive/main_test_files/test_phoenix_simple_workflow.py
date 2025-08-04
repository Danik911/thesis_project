#!/usr/bin/env python3
"""
Simple Phoenix observability test with minimal workflow
Tests if traces are being captured and stored properly
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.monitoring.phoenix_config import setup_phoenix, shutdown_phoenix
from src.agents.categorization.agent import categorize_urs_document

async def test_simple_phoenix_workflow():
    """Test basic Phoenix trace collection with categorization"""
    
    print("Setting up Phoenix observability...")
    phoenix_manager = setup_phoenix()
    
    try:
        print("Testing basic categorization with Phoenix tracing...")
        
        # Create simple test URS (Category 3 - clear case)
        test_urs = """
        URS-TEST-001: Temperature monitoring system for pharmaceutical storage
        
        The system shall monitor temperature continuously in cold storage areas.
        System uses vendor-supplied software without modifications.
        Temperature range: 2-8°C with accuracy ±0.5°C.
        System generates alerts when temperature exceeds limits.
        All data shall be stored in vendor's standard database format.
        Standard reports provided by vendor shall be used for batch release.
        """
        
        # Run categorization using the high-level function
        result = categorize_urs_document(
            urs_content=test_urs,
            document_name="test_phoenix_urs.txt",
            use_structured_output=True
        )
        
        print(f"Categorization result: Category {result.category}, Confidence: {result.confidence:.2f}")
        print(f"Reasoning: {result.reasoning[:100]}...")
        
        print("Phoenix traces should now be available")
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print("Waiting for Phoenix span export...")
        await asyncio.sleep(3)  # Allow time for spans to export
        
        shutdown_phoenix(timeout_seconds=5)
        print("Phoenix observability shutdown complete")

async def main():
    """Main test function"""
    print("Starting simple Phoenix workflow test")
    success = await test_simple_phoenix_workflow()
    
    if success:
        print("Phoenix workflow test completed successfully")
    else:
        print("Phoenix workflow test failed")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)