#!/usr/bin/env python3
"""
Final demonstration runner with 8-minute execution
"""
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Ensure API keys are set
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')
os.environ['OPENROUTER_API_KEY'] = os.getenv('OPENROUTER_API_KEY', '')

print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting demonstration workflow")
print(f"OpenAI API Key present: {bool(os.environ.get('OPENAI_API_KEY'))}")
print(f"OpenRouter API Key present: {bool(os.environ.get('OPENROUTER_API_KEY'))}")

async def run_demo():
    # Import after env is loaded
    from main import run_with_event_logging
    from pathlib import Path
    
    # Setup args
    class Args:
        def __init__(self):
            self.verbose = True
            self.categorization_only = False  # Run FULL workflow
            self.disable_parallel_coordination = False
            self.confidence_threshold = 0.60
            self.enable_document_processing = False
            self.no_logging = False
            self.log_dir = "logs"
            self.consult = False
            self.list_consultations = False
            self.respond_to = None
    
    args = Args()
    document_path = Path(r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\datasets\urs_corpus\category_3\URS-001.md")
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Loading document: {document_path.name}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Running FULL unified workflow (not categorization-only)")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Expected duration: 5-8 minutes")
    
    start_time = datetime.now()
    
    try:
        await run_with_event_logging(document_path, args)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Workflow completed successfully!")
        print(f"Total execution time: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        
        # Check for generated files
        import glob
        test_suites = glob.glob("output/test_suites/test_suite_OQ-SUITE-*_20250828_*.json")
        if test_suites:
            print(f"Generated test suite: {Path(test_suites[-1]).name}")
        
        traces = glob.glob("logs/traces/*20250828*.jsonl")
        print(f"Generated {len(traces)} trace files")
        
    except asyncio.TimeoutError:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Workflow timeout after 8 minutes")
    except Exception as e:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Set 8 minute timeout
    try:
        asyncio.wait_for(
            asyncio.run(run_demo()),
            timeout=480.0  # 8 minutes
        )
    except asyncio.TimeoutError:
        print("\n[TIMEOUT] Workflow exceeded 8 minute limit")
        sys.exit(1)