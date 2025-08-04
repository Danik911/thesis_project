#!/usr/bin/env python3
"""
Run Phoenix Enhanced Integration Test

This script runs the integration test and captures output for analysis.
"""

import subprocess
import sys
import os
from pathlib import Path

# Change to project directory
project_dir = Path(r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project")
os.chdir(project_dir)

print("🚀 Starting Phoenix Enhanced Integration Test...")
print(f"📁 Working directory: {project_dir}")

try:
    # Run the test using uv
    result = subprocess.run([
        "uv", "run", "python", "test_phoenix_enhanced_integration.py"
    ], capture_output=True, text=True, timeout=60)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
    
    print(f"\nReturn code: {result.returncode}")
    
except subprocess.TimeoutExpired:
    print("❌ Test timed out after 60 seconds")
except Exception as e:
    print(f"❌ Failed to run test: {e}")