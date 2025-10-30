#!/usr/bin/env python3
"""Run workflow in background and poll for results"""
import subprocess
import time
from pathlib import Path

print("Starting workflow in background...")
print("This will run for up to 15 minutes")
print("Polling output/test_suites/ every 30 seconds")
print("="*60)

# Start the workflow in background
process = subprocess.Popen([
    "uv", "run", "python", "-c",
    """
import asyncio
import os
from dotenv import load_dotenv
load_dotenv('../.env')
from src.core.unified_workflow import run_unified_test_generation_workflow

asyncio.run(run_unified_test_generation_workflow(
    document_path='tests/test_data/gamp5_test_data/testing_data.md',
    test_suite_type='oq'
))
"""
], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

print(f"Process started with PID: {process.pid}")

# Poll for results
output_dir = Path("output/test_suites")
start_time = time.time()
check_count = 0

while True:
    check_count += 1
    elapsed = time.time() - start_time

    # Check if process is still running
    poll = process.poll()
    if poll is not None:
        print(f"\nProcess completed with return code: {poll}")
        stdout, stderr = process.communicate()
        if stdout:
            print("STDOUT:", stdout[-1000:])  # Last 1000 chars
        if stderr:
            print("STDERR:", stderr[-1000:])  # Last 1000 chars
        break

    # Check for output files
    json_files = list(output_dir.glob("*.json"))

    print(f"\r[{elapsed:.0f}s] Check #{check_count}: Found {len(json_files)} files", end="", flush=True)

    if json_files:
        print("\n\nSUCCESS! Test suite generated:")
        for f in json_files:
            print(f"  - {f.name} ({f.stat().st_size} bytes)")

            # Show content preview
            with open(f) as file:
                content = file.read()
                print("\nFirst 1000 characters:")
                print(content[:1000])
        break

    # Timeout after 15 minutes
    if elapsed > 900:
        print("\n\nTimeout reached (15 minutes)")
        process.terminate()
        break

    # Wait 30 seconds before next check
    time.sleep(30)

print("\n" + "="*60)
print("Monitoring complete")
