#!/usr/bin/env python3
"""
Task 42: Simple Cross-Validation Test
Tests a single document to verify the workflow is working.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run simple test of the workflow."""
    print("=" * 60)
    print("TASK 42: SIMPLE WORKFLOW TEST")
    print("=" * 60)
    
    # Check environment
    print("\n[1] Checking environment...")
    
    # Check API keys
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("[ERROR] OPENROUTER_API_KEY not set")
        return
    if not os.getenv("OPENAI_API_KEY"):
        print("[ERROR] OPENAI_API_KEY not set")
        return
    print("[OK] API keys configured")
    
    # Check Phoenix
    import requests
    try:
        response = requests.get("http://localhost:6006", timeout=5)
        if response.status_code == 200:
            print("[OK] Phoenix monitoring accessible")
    except:
        print("[WARNING] Phoenix not running (optional)")
    
    # Run workflow
    print("\n[2] Running workflow test...")
    print("-" * 40)
    
    test_doc = "main/tests/test_data/gamp5_test_data/testing_data.md"
    
    # Change to main directory
    os.chdir("C:/Users/anteb/Desktop/Courses/Projects/thesis_project/main")
    
    # Run the main workflow with a timeout
    cmd = [
        sys.executable,  # Use current Python interpreter
        "main.py",
        test_doc,
        "--verbose"
    ]
    
    print(f"[CMD] {' '.join(cmd)}")
    print("\n[3] Workflow output:")
    print("-" * 40)
    
    try:
        # Run with timeout of 5 minutes
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show output in real-time
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print("\n[SUCCESS] Workflow completed successfully!")
        else:
            print(f"\n[ERROR] Workflow failed with code: {result.returncode}")
            
    except subprocess.TimeoutExpired:
        print("\n[TIMEOUT] Workflow exceeded 5 minute timeout")
        print("[INFO] This may indicate an issue with the DeepSeek V3 API")
    except Exception as e:
        print(f"\n[ERROR] Failed to run workflow: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()