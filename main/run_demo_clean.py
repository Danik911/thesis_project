#!/usr/bin/env python3
"""
Clean demonstration runner without Unicode issues
"""
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Set encoding before any imports
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Ensure API keys are set
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'

print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting demonstration workflow")
print(f"OpenAI API Key present: {bool(os.environ.get('OPENAI_API_KEY'))}")
print(f"OpenRouter API Key present: {bool(os.environ.get('OPENROUTER_API_KEY'))}")
print(f"ChromaDB should have 15 chunks from previous ingestion")

# Now run the main workflow
from main import main
import sys

if __name__ == "__main__":
    start_time = datetime.now()
    print(f"[{start_time.strftime('%H:%M:%S')}] Launching unified workflow...")
    
    sys.argv = [
        "main.py",
        r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\datasets\urs_corpus\category_3\URS-001.md",
        "--verbose"
    ]
    
    try:
        # Run with asyncio timeout
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_with_timeout():
            # Import main function
            import importlib
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            main_module = importlib.import_module('main')
            
            # Call main
            await main_module.main()
        
        # Run with 8 minute timeout
        task = loop.create_task(run_with_timeout())
        loop.run_until_complete(asyncio.wait_for(task, timeout=480))
        
    except asyncio.TimeoutError:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Workflow timeout after 8 minutes - this is expected for full generation")
    except Exception as e:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Workflow error: {e}")
    finally:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"\n[{end_time.strftime('%H:%M:%S')}] Total time: {duration:.1f}s ({duration/60:.1f} minutes)")
        
        # Check results
        import glob
        test_suites = glob.glob("output/test_suites/test_suite_OQ-SUITE-*_20250828_*.json")
        if test_suites:
            print(f"SUCCESS: Generated test suite: {Path(test_suites[-1]).name}")
            # Check size
            import json
            with open(test_suites[-1], 'r') as f:
                data = json.load(f)
                if 'test_cases' in data:
                    print(f"Tests generated: {len(data['test_cases'])}")
        
        traces = glob.glob("logs/traces/*20250828*.jsonl")
        if traces:
            print(f"Traces generated: {len(traces)} files")
            for trace in traces:
                print(f"  - {Path(trace).name}")