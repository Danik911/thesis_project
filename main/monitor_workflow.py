#!/usr/bin/env python3
"""Monitor workflow progress and output files"""
import time
from pathlib import Path

print("Monitoring workflow progress...")
print("Checking every 10 seconds for:")
print("1. Output files in output/test_suites/")
print("2. Latest log entries")
print("="*60)

output_dir = Path("output/test_suites")
log_file = Path("workflow_output.log")
last_size = 0

while True:
    # Check for output files
    json_files = list(output_dir.glob("*.json")) if output_dir.exists() else []
    
    # Check log file
    if log_file.exists():
        current_size = log_file.stat().st_size
        if current_size > last_size:
            # Read new content
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(last_size)
                new_content = f.read()
                
                # Show key events
                for line in new_content.split('\n'):
                    if any(keyword in line for keyword in ['OQ test generation', 'SUCCESS', 'ERROR', 'completed', 'saved to']):
                        print(f"[LOG] {line.strip()}")
                        
            last_size = current_size
    
    # Status update
    print(f"\r[{time.strftime('%H:%M:%S')}] Files: {len(json_files)}, Log size: {last_size:,} bytes", end="", flush=True)
    
    if json_files:
        print(f"\n\nSUCCESS! Found output files:")
        for f in json_files:
            print(f"  - {f.name} ({f.stat().st_size:,} bytes)")
        break
    
    # Check if workflow completed
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if "WORKFLOW EXECUTION COMPLETE" in content or "Traceback" in content:
                print("\n\nWorkflow completed or errored. Check logs.")
                break
    
    time.sleep(10)

print("\nMonitoring complete.")