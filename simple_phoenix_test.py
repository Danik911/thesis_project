#!/usr/bin/env python3
"""
Simple Phoenix test script to generate traces without Unicode issues
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the main directory to Python path
main_dir = Path(__file__).parent / "main"
sys.path.insert(0, str(main_dir))

async def test_phoenix_traces():
    """Test Phoenix trace generation with minimal setup"""
    try:
        print("=== Phoenix Trace Generation Test ===")
        
        # Import Phoenix setup
        from src.monitoring.phoenix_config import setup_phoenix, PhoenixConfig
        
        # Setup Phoenix
        config = PhoenixConfig(
            phoenix_host="localhost",
            phoenix_port=6006,
            enable_tracing=True,
            service_name="simple_test",
            project_name="test_generation_thesis"
        )
        
        phoenix_manager = setup_phoenix(config)
        print("Phoenix manager initialized:", phoenix_manager._initialized if phoenix_manager else False)
        
        # Import categorization workflow
        from src.core.categorization_workflow import GAMPCategorizationWorkflow
        
        # Create test document content
        test_content = """
PHARMACEUTICAL SYSTEM REQUIREMENTS

GAMP Category: Category 5 (Custom Application)
Risk Level: High

Functional Requirements:
1. User authentication required
2. Data integrity (ALCOA+ compliance)
3. Audit trail logging
4. Electronic signatures

Testing Requirements:
- Validation testing required
- Performance testing required
- Security testing required
"""
        
        print("Creating categorization workflow...")
        workflow = GAMPCategorizationWorkflow(timeout=30.0, verbose=True)
        
        print("Starting categorization...")
        result = await workflow.run(content=test_content)
        
        print("Categorization completed!")
        print(f"Category: {result.get('category', 'Unknown')}")
        print(f"Confidence: {result.get('confidence', 'Unknown')}")
        
        # Give traces time to be sent
        await asyncio.sleep(2)
        
        if phoenix_manager:
            phoenix_manager.shutdown()
            print("Phoenix manager shut down")
        
        print("=== Test completed successfully ===")
        return True
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phoenix_traces())
    sys.exit(0 if success else 1)