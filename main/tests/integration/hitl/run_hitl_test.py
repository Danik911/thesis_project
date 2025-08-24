#!/usr/bin/env uv run python
"""
Run HITL Test Script
"""
import subprocess
import sys
from pathlib import Path

# Change to the main directory
main_dir = Path(__file__).parent
print(f"Working directory: {main_dir}")

# Run the HITL fix test
try:
    result = subprocess.run([
        sys.executable, "test_hitl_fix.py"
    ], check=False, cwd=main_dir, capture_output=True, text=True)

    print("STDOUT:")
    print(result.stdout)

    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    print(f"Exit code: {result.returncode}")

except Exception as e:
    print(f"Error running test: {e}")
