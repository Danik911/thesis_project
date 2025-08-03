#!/usr/bin/env python3
"""Debug workflow execution to find where it's stuck"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Disable Unicode in console
os.environ['PYTHONIOENCODING'] = 'utf-8'

from src.core.unified_workflow import run_unified_test_generation_workflow

async def debug_workflow():
    """Run workflow with debug output"""
    
    print("Starting workflow with DEBUG logging enabled...")
    print("This will show detailed execution flow")
    print("="*60)
    
    try:
        result = await run_unified_test_generation_workflow(
            document_path='tests/test_data/gamp5_test_data/testing_data.md',
            test_suite_type='oq'
        )
        
        print("\n" + "="*60)
        print("WORKFLOW COMPLETED SUCCESSFULLY!")
        print(f"Result: {result}")
        
        # Check for output files
        from pathlib import Path
        output_dir = Path("output/test_suites")
        json_files = list(output_dir.glob("*.json"))
        
        if json_files:
            print(f"\nFound {len(json_files)} output files:")
            for f in json_files:
                print(f"  - {f.name}")
        else:
            print("\nNO OUTPUT FILES FOUND!")
            
    except Exception as e:
        print(f"\nWORKFLOW FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run with asyncio debug mode
    asyncio.run(debug_workflow(), debug=True)